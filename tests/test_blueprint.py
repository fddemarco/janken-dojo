"""janken/kit/blueprint/: validation, lowering, state layout and knob binding."""

import dataclasses
import itertools
import types
from collections.abc import Mapping

import pytest
import yaml

from janken.kit import bot, declare
from janken.kit import codes as c
from janken.kit.blueprint import BlueprintError, Gatekeeper, encoder, lowering

SIMPLE = bot.Blueprint(
    guards=(bot.Noise(bot.Knob("NOISE")),),
    core=bot.Bandit(predictors=(bot.LastMove(bot.OPP),)),
)

NO_DEFAULTS: Mapping[str, float] = types.MappingProxyType({})


def records(spec, at: int, count: int, width: int = c.REC) -> list[list[int]]:
    return [list(spec[at + k * width : at + (k + 1) * width]) for k in range(count)]


def assert_refused(
    blueprint: bot.Blueprint, defaults: Mapping[str, float] = NO_DEFAULTS
) -> None:
    with pytest.raises(BlueprintError):
        blueprint.compile(defaults)


class TestValidation:
    def test_knobs_must_name_defaults_and_defaults_must_be_used(self) -> None:
        assert_refused(SIMPLE, {"NOSE": 0.1})
        assert_refused(SIMPLE, {"NOISE": 0.1, "SPARE": 1})
        SIMPLE.compile({"NOISE": 0.1})

    def test_first_reads_no_scores(self) -> None:
        assert_refused(
            bot.Blueprint(
                core=bot.Bandit(
                    predictors=(bot.LastMove(),), scorer=bot.DecayedNet(0.9)
                )
            )
        )
        assert_refused(
            bot.Blueprint(
                core=bot.Bandit(predictors=(bot.LastMove(),), random_arm=bot.RA_SCORED)
            )
        )

    def test_team_fleet_must_exist(self) -> None:
        assert_refused(bot.Blueprint(overlays=(bot.Team(bot.SUPPORT, fleet=7),)))

    def test_naive_bayes_combines_its_own_side_only(self) -> None:
        last = bot.LastMove()
        sim = bot.Sim(bot.NaiveBayes((last,)))
        assert_refused(bot.Blueprint(core=bot.Bandit(predictors=(last, sim))))

    def test_scored_selectors_need_a_scorer(self) -> None:
        assert_refused(
            bot.Blueprint(
                core=bot.Bandit(predictors=(bot.LastMove(),), selector=bot.Greedy())
            )
        )

    def test_thompson_needs_a_dirichlet_and_no_pinned_random_arm(self) -> None:
        def thompson(scorer: bot.Scorer, random_arm: int) -> bot.Blueprint:
            return bot.Blueprint(
                core=bot.Bandit(
                    predictors=(bot.LastMove(),),
                    scorer=scorer,
                    random_arm=random_arm,
                    selector=bot.Thompson(),
                )
            )

        assert_refused(thompson(bot.DecayedNet(0.9), bot.RA_NONE))
        assert_refused(thompson(bot.Dirichlet(0.9), bot.RA_PINNED))
        thompson(bot.Dirichlet(0.9), bot.RA_SCORED).compile({})

    def test_replays_nest_two_deep_and_need_a_scorer(self) -> None:
        inner = bot.Bandit((bot.LastMove(),), scorer=bot.DecayedNet(0.9))
        nested = bot.Bandit((bot.Replay(inner),), scorer=bot.DecayedNet(0.9))
        too_deep = bot.Bandit((bot.Replay(nested),), scorer=bot.DecayedNet(0.9))
        unscored = bot.Bandit((bot.LastMove(),))

        def replaying(ensemble: bot.Bandit) -> bot.Blueprint:
            return bot.Blueprint(
                core=bot.Bandit(
                    predictors=(bot.Replay(ensemble),),
                    scorer=bot.DecayedNet(0.9),
                    selector=bot.Greedy(),
                )
            )

        assert_refused(replaying(too_deep))
        assert_refused(
            bot.Blueprint(
                core=bot.Bandit(
                    predictors=(bot.Replay(inner, draws=8),),
                    scorer=bot.DecayedNet(0.9),
                    selector=bot.Greedy(),
                )
            )
        )
        assert_refused(replaying(unscored))
        replaying(inner).compile({})
        replaying(nested).compile({})

    def test_emitting_invalid_moves_must_not_trip_our_own_guard(self) -> None:
        assert_refused(
            bot.Blueprint(
                guards=(bot.OnInvalid(bot.CRASH_ACTION, bot.ANY, bot.BOTH),),
                core=bot.Bandit(predictors=(bot.LastMove(),)),
                overlays=(bot.EmitInvalid(5, 9),),
            )
        )

    def test_literals_are_checked(self) -> None:
        assert_refused(
            bot.Blueprint(core=bot.Bandit(predictors=(bot.LastMove(),), rotations=()))
        )
        assert_refused(
            bot.Blueprint(
                core=bot.Bandit(predictors=(bot.LastMove(),), rotations=(1, 1))
            )
        )
        assert_refused(
            bot.Blueprint(core=bot.Bandit(predictors=(bot.NGram(4, ctx=bot.JOINT),)))
        )
        assert_refused(bot.Blueprint(guards=(bot.Opening(0),)))
        assert_refused(bot.Blueprint(core=bot.Bandit(predictors=(bot.Constant(5),))))


MAIN = bot.Bandit(
    (bot.LastMove(), bot.Constant(bot.ROCK)),
    bot.ALL_ROTATIONS,
    bot.Dirichlet(0.9),
    bot.RA_SCORED,
    bot.Thompson(sharp=2.0),
)
EXPERT = bot.Rotated(bot.React(), (bot.BEAT,))


class TestLowering:
    """janken/kit/blueprint/lowering.py: the tree as the flat bandit it plays."""

    def test_a_bandit_is_played_as_it_is(self) -> None:
        assert lowering.lower(MAIN) is MAIN

    def test_a_gate_is_its_main_bandit_with_the_experts_last(self) -> None:
        gate = bot.Gate(
            MAIN, (EXPERT,), rule=bot.MAIN_FIRST, edge=0.1, decay=0.9, warmup=5
        )
        keeper = Gatekeeper(
            edge=0.1, decay=0.9, warmup=5, sharp=2.0, rule=bot.MAIN_FIRST, experts=1
        )
        flat = dataclasses.replace(
            MAIN, predictors=(*MAIN.predictors, EXPERT), selector=keeper
        )
        assert lowering.lower(gate) == flat
        assert (
            bot.Blueprint(core=gate).compile({}).spec.tolist()
            == encoder.Encoder({}).encode((), flat, ()).spec.tolist()
        )

    def test_a_gate_needs_a_thompson_main_bandit(self) -> None:
        greedy = dataclasses.replace(MAIN, selector=bot.Greedy())
        with pytest.raises(BlueprintError, match="Thompson"):
            lowering.lower(bot.Gate(greedy, (EXPERT,)))

    def test_a_gated_expert_is_one_arm(self) -> None:
        with pytest.raises(BlueprintError, match="one arm"):
            lowering.lower(bot.Gate(MAIN, (bot.React(),)))  # three rotations

    def test_a_gate_needs_a_main_arm_and_an_expert(self) -> None:
        empty = dataclasses.replace(MAIN, predictors=())
        with pytest.raises(BlueprintError, match="main arm"):
            lowering.lower(bot.Gate(empty, (EXPERT,)))
        assert_refused(bot.Blueprint(core=bot.Gate(MAIN, ())))

    def test_only_the_leader_rules_gate_more_than_one_expert(self) -> None:
        two = (EXPERT, EXPERT)
        assert_refused(bot.Blueprint(core=bot.Gate(MAIN, two, rule=bot.MAIN_FIRST)))
        bot.Blueprint(core=bot.Gate(MAIN, two, rule=bot.LEADER)).compile({})

    def test_a_gate_compiles_only_as_the_core(self) -> None:
        replayed_gate = declare.blueprint_from_data(
            yaml.safe_load("""
                core:
                  Bandit:
                    predictors:
                      - Replay:
                          bandit:
                            Gate:
                              main: {metabot: [0.9, 0.9, 12]}
                              experts: [{Rotated: {signal: React, rotations: [BEAT]}}]
                    scorer: {DecayedNet: {decay: 0.9}}
                    selector: Greedy
            """)
        )
        with pytest.raises(BlueprintError, match="only as the bot's core"):
            replayed_gate.compile({})
        with pytest.raises(BlueprintError, match="a Bandit or a Gate"):
            lowering.lower(bot.LastMove())

    def test_a_naive_bayes_combines_exactly_its_bandits_other_predictors(
        self,
    ) -> None:
        last, react = bot.LastMove(), bot.React()

        def core(*inputs: bot.SignalLike) -> bot.Bandit:
            combiner = bot.Rotated(bot.NaiveBayes(inputs), (bot.BEAT,))
            return bot.Bandit((last, react, combiner), scorer=bot.DecayedNet(0.9))

        assert lowering.lower(core(last, react)) == core(last, react)
        for inputs in ((last,), (react, last), (last, react, react)):
            with pytest.raises(BlueprintError, match="NaiveBayes combines"):
                lowering.lower(core(*inputs))


class TestLayout:
    def test_state_blocks_do_not_overlap(self) -> None:
        core = bot.presets.smartbot_sims(10, 0.95, 0.9, 12)
        compiled = bot.Blueprint(core=core).compile({})
        spec = compiled.spec
        f_size, i_size, _ = compiled.state
        f_blocks = []
        stack = [spec[c.H_CORE]]
        while stack:
            e = stack.pop()
            n_arms = spec[e + c.E_NARMS]
            f_blocks.append((spec[e + c.E_SCORE_F], (n_arms + 1) * 3))
            for rec in records(spec, spec[e + c.E_SIG_AT], spec[e + c.E_NSIG]):
                if rec[c.R_KIND] == c.S_REPLAY:
                    stack.append(rec[c.R_SUB])
        f_blocks.append((spec[c.H_KNOB_F], spec[c.H_NKNOB]))
        f_blocks.sort()
        for (at, size), (nxt, _) in itertools.pairwise(f_blocks):
            assert at + size <= nxt
        last_at, last_size = f_blocks[-1]
        assert last_at + last_size <= f_size
        assert spec[c.H_CURSOR_I] < i_size

    def test_matchers_share_one_index_per_stream(self) -> None:
        compiled = bot.Blueprint(
            core=bot.presets.smartbot_sims(10, 0.95, 0.9, 12)
        ).compile({})
        spec = compiled.spec
        assert spec[c.H_NIDX] == 3  # OPP, MY, JOINT, whoever reads them
        streams = sorted(
            spec[spec[c.H_IDX_AT] + x * c.IDX + c.X_STREAM]
            for x in range(spec[c.H_NIDX])
        )
        assert streams == [c.STREAM_OPP, c.STREAM_MY, c.STREAM_JOINT]
        per_round = compiled.state[2]
        assert per_round == 2 + 3 * c.X_SLOTS  # valid history + indexes

    def test_a_swapped_view_reads_the_other_side(self) -> None:
        def stream_of(signal: bot.SignalLike) -> int:
            spec = bot.Blueprint(core=bot.Bandit(predictors=(signal,))).compile({}).spec
            return spec[spec[c.H_IDX_AT] + c.X_STREAM]

        assert stream_of(bot.LongestMatch(4, ctx=bot.OPP)) == c.STREAM_OPP
        assert stream_of(bot.Sim(bot.LongestMatch(4, ctx=bot.OPP))) == c.STREAM_MY
        assert stream_of(bot.Sim(bot.LongestMatch(4, ctx=bot.MY))) == c.STREAM_OPP
        assert stream_of(bot.Sim(bot.Geometry())) == c.STREAM_JOINT
        replayed = bot.Replay(
            bot.Bandit((bot.LongestMatch(4, ctx=bot.OPP),), scorer=bot.DecayedNet(0.9))
        )
        assert stream_of(replayed) == c.STREAM_MY
        no_matcher = bot.Blueprint(
            core=bot.Bandit(predictors=(bot.LastMove(),))
        ).compile({})
        assert no_matcher.spec[c.H_NIDX] == 0
        assert no_matcher.state[2] == 2  # the valid history only

    def test_new_state_sizes_the_workspace_by_rounds(self) -> None:
        compiled = bot.Blueprint(
            core=bot.Bandit(predictors=(bot.LongestMatch(4),))
        ).compile({})
        f_size, i_size, per_round = compiled.state
        for rounds in (1, 10, 200):
            f, i = compiled.new_state(rounds)
            assert f.size == f_size
            assert i.size == i_size + per_round * (rounds + 1)
            at = compiled.spec[c.H_ROUNDS_I]
            assert (i[at], i[at + 1]) == (rounds + 1, i_size)

    def test_knobs_bind_to_defaults_by_position(self) -> None:
        blueprint = bot.Blueprint(
            guards=(bot.Noise(bot.Knob("NOISE")),),
            core=bot.Bandit(
                predictors=(
                    bot.Frequency(bot.OPP, 0.5),
                    bot.Frequency(bot.MY, bot.Knob("DECAY")),
                )
            ),
        )
        compiled = blueprint.compile({"DECAY": 0.8, "NOISE": 0.1})
        spec = compiled.spec
        binds = list(spec[spec[c.H_BIND_AT] : spec[c.H_BIND_AT] + spec[c.H_NKNOB]])
        assert binds == [1, -1, 0]  # NOISE, a literal 0.5, DECAY
        assert list(compiled.knobs) == [0.1, 0.5, 0.8]

    def test_choose_selector_binds_its_index(self) -> None:
        blueprint = bot.Blueprint(
            core=bot.Bandit(
                predictors=(bot.LastMove(),),
                scorer=bot.Dirichlet(0.9),
                selector=bot.ChooseSelector(
                    bot.Knob("SELECT"), (bot.Thompson(), bot.Greedy())
                ),
            )
        )
        spec = blueprint.compile({"SELECT": 1}).spec
        assert spec[c.H_NSEL] == 2
        assert spec[c.H_SEL_K] >= 0
