"""janken/kit/declare.py: blueprints declared as YAML data, their arms named as bots."""

import dataclasses
import textwrap
from collections.abc import Mapping

import pytest
import yaml

from janken.kit import bot
from janken.kit.blueprint import Blueprint, BlueprintError, Gatekeeper, refs
from janken.kit.declare import blueprint_from_data, symbol

# The bots the declarations below name, by stem: L1 heuristics, an L2 bandit, a
# gate, a silent bot.
SHELF = {
    "last": """
        defaults: {OF: OPP}
        blueprint:
          guards: [{Noise: {p: 0.5}}]
          core: {Heuristic: {signal: {LastMove: {of: $OF}}, rotation: BEAT}}
    """,
    "coin": """
        defaults: {P_ROCK: 0.5, P_PAPER: 0.3}
        blueprint:
          core:
            Heuristic: {signal: {Biased: {p_rock: $P_ROCK, p_paper: $P_PAPER}}}
    """,
    "gram": """
        defaults: {ORDER: 1, CTX: 0, DECAY: 1.0}
        blueprint:
          core:
            Heuristic:
              signal: {NGram: {order: $ORDER, ctx: $CTX, decay: $DECAY}}
              rotation: BEAT
    """,
    "board": """
        defaults: {DECAY: 0.9}
        blueprint:
          core:
            Bandit:
              predictors: [{bot: last, rotations: [COPY, BEAT]}]
              scorer: {Dirichlet: {decay: $DECAY}}
              random_arm: RA_SCORED
              selector: Thompson
    """,
    "gated": """
        blueprint:
          core:
            Gate: {main: {bot: board}, experts: [{bot: last}]}
    """,
    "nash": "blueprint: {}",
    "loop_a": "blueprint: {core: {Bandit: {predictors: [{bot: loop_b}]}}}",
    "loop_b": "blueprint: {core: {Bandit: {predictors: [{bot: loop_a}]}}}",
}


class Shelf:
    """A library of the bots in SHELF, read from memory."""

    def __init__(self, files: Mapping[str, str]) -> None:
        self.files = {k: yaml.safe_load(textwrap.dedent(v)) for k, v in files.items()}
        self.reading: list[str] = []

    def bot(self, stem: str) -> refs.Referenced:
        if stem not in self.files:
            raise BlueprintError(f"no bot {stem!r}")
        if stem in self.reading:
            raise BlueprintError(f"a cycle through {stem}")
        self.reading.append(stem)
        try:
            data = self.files[stem]
            blueprint = blueprint_from_data(data.get("blueprint"), self)
        finally:
            self.reading.pop()
        defaults = {
            name: symbol(v) if isinstance(v, str) else v
            for name, v in (data.get("defaults") or {}).items()
        }
        return refs.Referenced(stem, blueprint, defaults)


def declared(text: str) -> Blueprint:
    return blueprint_from_data(yaml.safe_load(textwrap.dedent(text)), Shelf(SHELF))


def bandit(text: str) -> bot.Bandit:
    """The core of a blueprint section, which must be a Bandit."""
    core = declared(text).core
    assert isinstance(core, bot.Bandit)
    return core


def arms(text: str) -> tuple[bot.SignalLike, ...]:
    """The arms of `core: {Bandit: {predictors: <text>}}`."""
    return bandit(f"core: {{Bandit: {{predictors: {text}}}}}").predictors


BOARD = bot.Bandit(
    (bot.Rotated(bot.LastMove(bot.OPP), (bot.BEAT, bot.BEAT_BEAT)),),
    scorer=bot.Dirichlet(0.9),
    random_arm=bot.RA_SCORED,
    selector=bot.Thompson(),
)


class TestGrammar:
    def test_keywords_positional_and_bare_calls(self) -> None:
        expected = bot.Blueprint(
            guards=(bot.Noise(bot.Knob("NOISE")), bot.Opening(1, bot.ROCK)),
            core=bot.Heuristic(bot.React(), bot.BEAT),
        )
        assert (
            declared("""
                guards: [{Noise: {p: $NOISE}}, {Opening: [1, ROCK]}]
                core: {Heuristic: {signal: React, rotation: BEAT}}
            """)
            == expected
        )

    def test_an_empty_section_is_the_default_blueprint(self) -> None:
        assert blueprint_from_data(None) == Blueprint()
        assert blueprint_from_data({}) == Blueprint()
        assert Blueprint().core == bot.Heuristic(bot.Silent())

    def test_a_vigilant_team_with_its_handshake(self) -> None:
        assert declared("""
                overlays:
                  - Team: {role: CHAMPION, handshake: [ROCK, PAPER], vigilant: true}
            """).overlays == (
            bot.Team(bot.CHAMPION, (bot.ROCK, bot.PAPER), vigilant=True),
        )


class TestReference:
    def test_an_l1_arm_is_its_signal_with_its_rotation_plus_the_arms(self) -> None:
        # last plays BEAT: COPY'd, its move; BEAT, the move that beats it.
        assert arms("[{bot: last, rotations: [COPY, BEAT]}]") == (
            bot.Rotated(bot.LastMove(bot.OPP), (bot.BEAT, bot.BEAT_BEAT)),
        )
        assert arms("[{bot: coin}]") == (  # by default, its move as it is
            bot.Rotated(bot.Biased(0.5, 0.3), (bot.COPY,)),
        )

    def test_arms_take_one_value_each_or_share_one(self) -> None:
        assert arms(
            "[{bot: gram, arms: 3, space: {ORDER: [1, 2, 3], CTX: JOINT}}]"
        ) == tuple(
            bot.Rotated(bot.NGram(o, ctx=bot.JOINT), (bot.BEAT,)) for o in (1, 2, 3)
        )

    def test_parameters_are_named_in_any_case_and_may_be_knobs(self) -> None:
        (arm,) = arms("[{bot: coin, space: {p_rock: $ROCKY}}]")
        assert arm == bot.Rotated(bot.Biased(bot.Knob("ROCKY"), 0.3), (bot.COPY,))

    def test_arms_are_spliced_in_order(self) -> None:
        assert arms("[{bot: coin}, {bot: last, space: {OF: MY}}]") == (
            bot.Rotated(bot.Biased(0.5, 0.3), (bot.COPY,)),
            bot.Rotated(bot.LastMove(bot.MY), (bot.BEAT,)),
        )

    def test_an_l1_from_the_opponents_side_is_a_sim(self) -> None:
        # A Sim's symbol is their move when they play BEAT; BEAT beats it.
        assert arms("[{bot: last, side: OPP}]") == (
            bot.Rotated(bot.Sim(bot.LastMove(bot.OPP)), (bot.BEAT,)),
        )
        # coin plays COPY: their move is the Sim's symbol turned back by one.
        assert arms("[{bot: coin, side: OPP, rotations: [COPY]}]") == (
            bot.Rotated(bot.Sim(bot.Biased(0.5, 0.3)), (bot.BEAT_BEAT,)),
        )

    def test_a_bandit_arm_is_a_replay_from_either_side(self) -> None:
        assert arms("[{bot: board}]") == (
            bot.Rotated(bot.Replay(BOARD, side=bot.MY), (bot.COPY,)),
        )
        (anti,) = arms(
            "[{bot: board, side: OPP, draws: 64, random_arm: RA_NONE,"
            " rotations: [BEAT]}]"
        )
        replayed = bot.Replay(dataclasses.replace(BOARD, random_arm=bot.RA_NONE), 64)
        assert anti == bot.Rotated(replayed, (bot.BEAT,))

    def test_a_heuristic_over_a_named_bot(self) -> None:
        core = declared("core: {Heuristic: {signal: {bot: board, side: OPP}}}").core
        assert core == bot.Heuristic(
            bot.Rotated(bot.Replay(BOARD), (bot.BEAT,)), bot.COPY
        )
        assert core.level() == 2

    def test_a_gate_names_its_main_bandit_and_experts(self) -> None:
        core = declared(
            "core: {Gate: {main: {bot: board}, experts: [{bot: last}]}}"
        ).core
        assert core == bot.Gate(
            BOARD, (bot.Rotated(bot.LastMove(bot.OPP), (bot.BEAT,)),)
        )

    def test_a_core_is_another_bot_bound_without_its_guards(self) -> None:
        blueprint = declared("""
            core: {bot: board, space: {DECAY: $DECAY}}
            overlays: [{Team: {role: SUPPORT}}]
        """)
        assert blueprint.guards == ()
        assert blueprint.core == dataclasses.replace(
            BOARD, scorer=bot.Dirichlet(bot.Knob("DECAY"))
        )

    def test_a_naive_bayes_combines_the_other_arms(self) -> None:
        core = bandit("""
            core:
              Bandit:
                predictors: [{bot: last}, {NaiveBayes: {decay: 0.9}}, {bot: coin}]
        """)
        last, coin = core.predictors[0], core.predictors[2]
        assert core.predictors[1] == bot.NaiveBayes((last, coin), 0.9)

    def test_the_same_predictor_twice_is_refused(self) -> None:
        # The same bot, parameters and side: its rotations belong in one entry.
        with pytest.raises(BlueprintError, match="last repeats an arm"):
            arms("[{bot: last}, {bot: coin}, {bot: last, rotations: [BEAT]}]")
        with pytest.raises(BlueprintError, match="gram repeats an arm"):
            arms("[{bot: gram, arms: 2, space: {ORDER: [2, 2]}}]")
        with pytest.raises(BlueprintError, match="board repeats an arm"):
            declared("""
                core:
                  Gate:
                    main: {bot: board}
                    experts: [{bot: board, side: OPP}, {bot: board, side: OPP}]
            """)

    def test_a_bot_may_repeat_with_other_parameters_or_from_the_other_side(
        self,
    ) -> None:
        assert len(arms("[{bot: last}, {bot: last, side: OPP}]")) == 2
        assert len(arms("[{bot: gram}, {bot: gram, space: {ORDER: 2}}]")) == 2
        assert len(arms("[{bot: last}, {bot: last, space: {OF: MY}}]")) == 2

    def test_two_bots_sharing_a_signal_are_two_arms(self) -> None:
        shelf = Shelf({**SHELF, "echo": SHELF["last"]})  # last, under another stem
        text = "core: {Bandit: {predictors: [{bot: last}, {bot: echo}]}}"
        core = blueprint_from_data(yaml.safe_load(text), shelf).core
        assert isinstance(core, bot.Bandit)
        assert len(core.predictors) == 2

    def test_a_gate_bot_is_an_arm_replayed_with_its_gatekeeper(self) -> None:
        (arm,) = arms("[{bot: gated, side: OPP}]")
        assert isinstance(arm, bot.Rotated)
        replay = arm.signal
        assert isinstance(replay, bot.Replay)
        assert isinstance(replay.bandit.selector, Gatekeeper)
        assert len(replay.bandit.predictors) == 2  # the main arm, the gated expert

    def test_inner_draws_cap_the_replays_a_replayed_bot_holds(self) -> None:
        shelf = Shelf(
            {
                **SHELF,
                "deep": """
                    blueprint:
                      core:
                        Bandit:
                          predictors: [{bot: board, side: OPP, draws: 256}]
                          scorer: {Dirichlet: {decay: 0.9}}
                          selector: Thompson
                """,
            }
        )

        def inner(text: str) -> int:
            core = blueprint_from_data(yaml.safe_load(text), shelf).core
            assert isinstance(core, bot.Bandit)
            (arm,) = core.predictors
            assert isinstance(arm, bot.Rotated)
            replay = arm.signal
            assert isinstance(replay, bot.Replay)
            (held,) = replay.bandit.predictors
            assert isinstance(held, bot.Rotated)
            assert isinstance(held.signal, bot.Replay)
            return held.signal.draws

        bandit_of = "core: {{Bandit: {{predictors: [{{bot: deep, draws: 8{}}}]}}}}"
        assert inner(bandit_of.format("")) == 256
        assert inner(bandit_of.format(", inner_draws: 32")) == 32
        assert inner(bandit_of.format(", inner_draws: 1000")) == 256

    def test_estimate_and_inner_estimate_set_how_replays_name_a_move(self) -> None:
        shelf = Shelf(
            {
                **SHELF,
                "deep": """
                    blueprint:
                      core:
                        Bandit:
                          predictors:
                            - {bot: board, side: OPP, draws: 256}
                            - {bot: board, side: OPP}
                          scorer: {Dirichlet: {decay: 0.9}}
                          selector: Thompson
                """,
            }
        )

        def estimates(ref: str) -> tuple[int, int, int]:
            text = f"core: {{Bandit: {{predictors: [{{bot: deep{ref}}}]}}}}"
            core = blueprint_from_data(yaml.safe_load(text), shelf).core
            assert isinstance(core, bot.Bandit)
            (arm,) = core.predictors
            assert isinstance(arm, bot.Rotated) and isinstance(arm.signal, bot.Replay)
            held = []
            for p in arm.signal.bandit.predictors:
                assert isinstance(p, bot.Rotated) and isinstance(p.signal, bot.Replay)
                held.append(p.signal.estimate)
            drawn, best = held
            return arm.signal.estimate, drawn, best

        assert estimates("") == (bot.EST_DRAWS,) * 3
        assert estimates(", estimate: NORMAL") == (
            bot.EST_NORMAL,
            bot.EST_DRAWS,
            bot.EST_DRAWS,
        )
        # a replay that names its best arm keeps doing so
        assert estimates(", inner_estimate: NORMAL") == (
            bot.EST_DRAWS,
            bot.EST_NORMAL,
            bot.EST_DRAWS,
        )

    def test_choose_selector(self) -> None:
        assert bandit("""
                core:
                  Bandit:
                    predictors: [{bot: last}]
                    selector:
                      ChooseSelector:
                        index: $SELECT
                        options: [Thompson, {Greedy: {ties: TIES_FIRST}}]
            """).selector == bot.ChooseSelector(
            bot.Knob("SELECT"), (bot.Thompson(), bot.Greedy(bot.TIES_FIRST))
        )


def assert_refused(text: str, where: str) -> None:
    with pytest.raises(BlueprintError, match=where):
        declared(text)


class TestError:
    def test_unknown_names_are_refused_with_their_path(self) -> None:
        assert_refused(
            "core: {Heuristic: {signal: NGrm}}", r"blueprint\.core\.Heuristic\.signal"
        )
        assert_refused("core: {Heuristic: {signal: {LastMove: {of: THEM}}}}", "THEM")
        assert_refused("guards: [{Noise: {q: 0.1}}]", r"guards\[0\]\.Noise")
        assert_refused("signals: [React]", "unknown key")

    def test_malformed_calls_are_refused(self) -> None:
        assert_refused("core: {React: {}, LastMove: {}}", "one `Name")
        assert_refused("guards: [{Opening: [1, 2, 3, 4]}]", "Opening")
        assert_refused("core: {Heuristic: {signal: {LastMove: {of: $}}}}", "bad knob")

    def test_the_old_grammars_are_gone(self) -> None:
        assert_refused("around: staller\nselector: First", "unknown key")
        assert_refused("selector: Thompson", "unknown key")
        assert_refused("core: {metabot: [0.9, 0.9, 12]}", "unknown stage 'metabot'")
        assert_refused("core: {Bandit: {predictors: [{Sim: {}}]}}", "unknown stage")

    def test_an_aggregators_arms_are_bots(self) -> None:
        assert_refused("core: {Bandit: {predictors: [React]}}", "arms are bots")
        assert_refused(
            "core: {Gate: {main: {bot: board}, experts: [React]}}", "arms are bots"
        )

    def test_a_reference_names_the_bots_parameters(self) -> None:
        assert_refused("core: {bot: coin, space: {P_SCISSORS: 0.2}}", "P_ROCK, P_PAPER")
        assert_refused("core: {bot: coin, typo: 1}", "unknown key")
        assert_refused(
            "core: {Bandit: {predictors: [{bot: gram, arms: 2, space: {ORDER: [1, 2, 3]}}]}}",
            "3 values for 2 arms",
        )

    def test_a_structural_parameter_takes_literals(self) -> None:
        assert_refused(
            "core: {Bandit: {predictors: [{bot: gram, space: {ORDER: $ORDER}}]}}",
            "ORDER",
        )

    def test_what_cannot_be_an_arm(self) -> None:
        assert_refused("core: {Bandit: {predictors: [{bot: nash}]}}", "at random")
        assert_refused("core: {Bandit: {predictors: [{bot: nobody}]}}", "nobody")
        assert_refused("core: {Bandit: {predictors: [{bot: loop_a}]}}", "cycle")
        assert_refused("guards: [{bot: last}]", "an arm of a Bandit or a Gate")

    def test_a_reference_needs_a_library(self) -> None:
        with pytest.raises(BlueprintError, match="no bot library"):
            blueprint_from_data({"core": {"bot": "board"}})

    def test_a_core_is_a_predictor(self) -> None:
        assert_refused("core: Thompson", "a core is a predictor")

    def test_a_gatekeeper_and_a_replay_are_built_by_the_compiler_only(self) -> None:
        assert_refused("core: {Bandit: {selector: Gatekeeper}}", "'Gatekeeper'")
        assert_refused("core: {Heuristic: {signal: Replay}}", "'Replay'")
