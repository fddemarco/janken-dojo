"""janken/kit/declare.py: blueprints declared as YAML data."""

import pytest
import yaml

from janken.kit import bot, presets
from janken.kit.blueprint import Blueprint, BlueprintError
from janken.kit.declare import blueprint_from_data


def declared(text: str) -> Blueprint:
    return blueprint_from_data(yaml.safe_load(text))


def bandit(text: str) -> bot.Bandit:
    """The core of a blueprint section, which must be a Bandit."""
    core = declared(text).core
    assert isinstance(core, bot.Bandit)
    return core


class TestGrammar:
    def test_keywords_positional_and_bare_calls(self) -> None:
        expected = bot.Blueprint(
            guards=(bot.Noise(bot.Knob("NOISE")), bot.Opening(1, bot.ROCK)),
            core=bot.Bandit(
                predictors=(bot.React(), bot.LastMove(bot.MY)),
                rotations=(bot.BEAT, bot.COPY),
            ),
        )
        assert (
            declared("""
                guards: [{Noise: {p: $NOISE}}, {Opening: [1, ROCK]}]
                core:
                  Bandit:
                    predictors: [React, {LastMove: {of: MY}}]
                    rotations: [BEAT, COPY]
            """)
            == expected
        )

    def test_an_empty_section_is_the_default_blueprint(self) -> None:
        assert blueprint_from_data(None) == Blueprint()
        assert blueprint_from_data({}) == Blueprint()

    def test_wrappers_nest(self) -> None:
        assert bandit("""
                core:
                  Bandit:
                    predictors:
                      - Sim: {signal: {NGram: {order: 2, ctx: JOINT}}}
                      - Rotated: {signal: {Geometry: {alpha: 0.1}}, rotations: [BEAT]}
                      - Replay: {bandit: {staller: {}}}
                    rotations: ALL_ROTATIONS
            """).predictors == (
            bot.Sim(bot.NGram(2, ctx=bot.JOINT)),
            bot.Rotated(bot.Geometry(0.1), (bot.BEAT,)),
            bot.Replay(presets.staller()),
        )

    def test_a_preset_core(self) -> None:
        assert declared("""
                core: {iocaine: {decay: $DECAY, max_len: 12, selector: Thompson}}
                overlays: [{Team: {role: SUPPORT}}]
            """) == bot.Blueprint(
            core=presets.iocaine(bot.Knob("DECAY"), 12, bot.Thompson()),
            overlays=(bot.Team(bot.SUPPORT),),
        )

    def test_a_gate_over_a_main_bandit_and_its_experts(self) -> None:
        main = bot.Bandit(
            (bot.LastMove(),), scorer=bot.Dirichlet(), selector=bot.Thompson()
        )
        assert declared("""
                core:
                  Gate:
                    main:
                      Bandit:
                        predictors: [LastMove]
                        scorer: Dirichlet
                        selector: Thompson
                    experts: [{Rotated: {signal: React, rotations: [COPY]}}]
                    rule: MAIN_FIRST
                    edge: $EDGE
            """).core == bot.Gate(
            main,
            (bot.Rotated(bot.React(), (bot.COPY,)),),
            rule=bot.MAIN_FIRST,
            edge=bot.Knob("EDGE"),
        )

    def test_a_naive_bayes_lists_its_inputs(self) -> None:
        core = bandit("""
                core:
                  Bandit:
                    predictors:
                      - React
                      - NaiveBayes: {inputs: [React], decay: 0.9}
            """)
        assert core.predictors == (bot.React(), bot.NaiveBayes((bot.React(),), 0.9))

    def test_a_vigilant_team_of_a_named_fleet(self) -> None:
        assert declared("""
                overlays: [{Team: {role: CHAMPION, fleet: ILIAD_V2, vigilant: true}}]
            """).overlays == (bot.Team(bot.CHAMPION, bot.ILIAD_V2, vigilant=True),)

    def test_a_preset_returning_signals_is_spliced(self) -> None:
        predictors = bandit("""
            core: {Bandit: {predictors: [{metabot_signals: [0.9, 12]}, React]}}
        """).predictors
        assert predictors == (*presets.metabot_signals(0.9, 12), bot.React())

    def test_choose_selector(self) -> None:
        assert bandit("""
                core:
                  Bandit:
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
            "core: {Bandit: {predictors: [React, NGrm]}}",
            r"blueprint\.core\.Bandit\.predictors\[1\]",
        )
        assert_refused("core: {Bandit: {predictors: [{LastMove: {of: THEM}}]}}", "THEM")
        assert_refused("guards: [{Noise: {q: 0.1}}]", r"guards\[0\]\.Noise")
        assert_refused("signals: [React]", "unknown key")

    def test_malformed_calls_are_refused(self) -> None:
        assert_refused("core: {React: {}, LastMove: {}}", "one `Name")
        assert_refused("guards: [{Opening: [1, 2, 3, 4]}]", "Opening")
        assert_refused(
            "core: {Bandit: {predictors: [{LastMove: {of: $}}]}}", "bad knob"
        )

    def test_the_old_flat_grammar_is_gone(self) -> None:
        assert_refused("around: staller\nselector: First", "unknown key")
        assert_refused("selector: Thompson", "unknown key")

    def test_a_core_is_a_predictor(self) -> None:
        assert_refused("core: Thompson", "a core is a predictor")

    def test_a_gatekeeper_is_built_by_the_compiler_only(self) -> None:
        assert_refused(
            "core: {Bandit: {selector: Gatekeeper}}", "unknown name 'Gatekeeper'"
        )
