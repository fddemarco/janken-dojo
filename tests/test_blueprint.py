"""janken/kit/blueprint.py: validation, state layout and knob binding."""

import itertools
import unittest

from janken.kit import bot
from janken.kit import codes as c
from janken.kit.blueprint import BlueprintError

SIMPLE = bot.Blueprint(
    guards=(bot.Noise(bot.Knob("NOISE")),),
    signals=(bot.LastMove(bot.OPP),),
)


def records(spec, at: int, count: int, width: int = c.REC) -> list[list[int]]:
    return [list(spec[at + k * width : at + (k + 1) * width]) for k in range(count)]


class ValidationTest(unittest.TestCase):
    def assertRefused(self, blueprint: bot.Blueprint, defaults=None) -> None:
        with self.assertRaises(BlueprintError):
            blueprint.compile(defaults or {})

    def test_knobs_must_name_defaults_and_defaults_must_be_used(self) -> None:
        self.assertRefused(SIMPLE, {"NOSE": 0.1})
        self.assertRefused(SIMPLE, {"NOISE": 0.1, "SPARE": 1})
        SIMPLE.compile({"NOISE": 0.1})

    def test_first_reads_no_scores(self) -> None:
        self.assertRefused(
            bot.Blueprint(signals=(bot.LastMove(),), scorer=bot.DecayedNet(0.9))
        )
        self.assertRefused(
            bot.Blueprint(signals=(bot.LastMove(),), random_arm=bot.RA_SCORED)
        )

    def test_team_fleet_must_exist(self) -> None:
        self.assertRefused(bot.Blueprint(overlays=(bot.Team(bot.SUPPORT, fleet=7),)))

    def test_naive_bayes_combines_its_own_side_only(self) -> None:
        self.assertRefused(bot.Blueprint(signals=(bot.Sim(bot.NaiveBayes()),)))

    def test_scored_selectors_need_a_scorer(self) -> None:
        self.assertRefused(
            bot.Blueprint(signals=(bot.LastMove(),), selector=bot.Greedy())
        )

    def test_thompson_needs_a_dirichlet_and_no_pinned_random_arm(self) -> None:
        def thompson(scorer: bot.Scorer, random_arm: int) -> bot.Blueprint:
            return bot.Blueprint(
                signals=(bot.LastMove(),),
                scorer=scorer,
                random_arm=random_arm,
                selector=bot.Thompson(),
            )

        self.assertRefused(thompson(bot.DecayedNet(0.9), bot.RA_NONE))
        self.assertRefused(thompson(bot.Dirichlet(0.9), bot.RA_PINNED))
        thompson(bot.Dirichlet(0.9), bot.RA_SCORED).compile({})

    def test_replays_nest_two_deep_and_need_a_scorer(self) -> None:
        inner = bot.Ensemble((bot.LastMove(),), scorer=bot.DecayedNet(0.9))
        nested = bot.Ensemble((bot.Replay(inner),), scorer=bot.DecayedNet(0.9))
        too_deep = bot.Ensemble((bot.Replay(nested),), scorer=bot.DecayedNet(0.9))
        unscored = bot.Ensemble((bot.LastMove(),))

        def replaying(ensemble: bot.Ensemble) -> bot.Blueprint:
            return bot.Blueprint(
                signals=(bot.Replay(ensemble),),
                scorer=bot.DecayedNet(0.9),
                selector=bot.Greedy(),
            )

        self.assertRefused(replaying(too_deep))
        self.assertRefused(
            bot.Blueprint(
                signals=(bot.Replay(inner, draws=8),),  # draws need a Dirichlet
                scorer=bot.DecayedNet(0.9),
                selector=bot.Greedy(),
            )
        )
        self.assertRefused(replaying(unscored))
        replaying(inner).compile({})
        replaying(nested).compile({})

    def test_emitting_invalid_moves_must_not_trip_our_own_guard(self) -> None:
        self.assertRefused(
            bot.Blueprint(
                guards=(bot.OnInvalid(bot.CRASH_ACTION, bot.ANY, bot.BOTH),),
                signals=(bot.LastMove(),),
                overlays=(bot.EmitInvalid(5, 9),),
            )
        )

    def test_literals_are_checked(self) -> None:
        self.assertRefused(bot.Blueprint(signals=(bot.LastMove(),), rotations=()))
        self.assertRefused(bot.Blueprint(signals=(bot.LastMove(),), rotations=(1, 1)))
        self.assertRefused(bot.Blueprint(signals=(bot.NGram(4, ctx=bot.JOINT),)))
        self.assertRefused(bot.Blueprint(guards=(bot.Opening(0),)))
        self.assertRefused(bot.Blueprint(signals=(bot.Constant(5),)))


class LayoutTest(unittest.TestCase):
    def test_state_blocks_do_not_overlap(self) -> None:
        core = bot.presets.smartbot_sims(10, 0.95, 0.9, 12)
        compiled = bot.Blueprint.around(core, bot.Thompson()).compile({})
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
            self.assertLessEqual(at + size, nxt)
        last_at, last_size = f_blocks[-1]
        self.assertLessEqual(last_at + last_size, f_size)
        self.assertLess(spec[c.H_CURSOR_I], i_size)

    def test_matchers_share_one_index_per_stream(self) -> None:
        compiled = bot.Blueprint.around(
            bot.presets.smartbot_sims(10, 0.95, 0.9, 12), bot.Thompson()
        ).compile({})
        spec = compiled.spec
        self.assertEqual(spec[c.H_NIDX], 3)  # OPP, MY, JOINT, whoever reads them
        streams = sorted(
            spec[spec[c.H_IDX_AT] + x * c.IDX + c.X_STREAM]
            for x in range(spec[c.H_NIDX])
        )
        self.assertEqual(streams, [c.STREAM_OPP, c.STREAM_MY, c.STREAM_JOINT])
        per_round = compiled.state[2]
        self.assertEqual(per_round, 2 + 3 * c.X_SLOTS)  # valid history + indexes

    def test_a_swapped_view_reads_the_other_side(self) -> None:
        def stream_of(signal: bot.SignalLike) -> int:
            spec = bot.Blueprint(signals=(signal,)).compile({}).spec
            return spec[spec[c.H_IDX_AT] + c.X_STREAM]

        self.assertEqual(stream_of(bot.LongestMatch(4, ctx=bot.OPP)), c.STREAM_OPP)
        self.assertEqual(
            stream_of(bot.Sim(bot.LongestMatch(4, ctx=bot.OPP))), c.STREAM_MY
        )
        self.assertEqual(
            stream_of(bot.Sim(bot.LongestMatch(4, ctx=bot.MY))), c.STREAM_OPP
        )
        self.assertEqual(stream_of(bot.Sim(bot.Geometry())), c.STREAM_JOINT)
        replayed = bot.Replay(
            bot.Ensemble(
                (bot.LongestMatch(4, ctx=bot.OPP),), scorer=bot.DecayedNet(0.9)
            )
        )
        self.assertEqual(stream_of(replayed), c.STREAM_MY)
        no_matcher = bot.Blueprint(signals=(bot.LastMove(),)).compile({})
        self.assertEqual(no_matcher.spec[c.H_NIDX], 0)
        self.assertEqual(no_matcher.state[2], 2)  # the valid history only

    def test_new_state_sizes_the_workspace_by_rounds(self) -> None:
        compiled = bot.Blueprint(signals=(bot.LongestMatch(4),)).compile({})
        f_size, i_size, per_round = compiled.state
        for rounds in (1, 10, 200):
            f, i = compiled.new_state(rounds)
            self.assertEqual(f.size, f_size)
            self.assertEqual(i.size, i_size + per_round * (rounds + 1))
            at = compiled.spec[c.H_ROUNDS_I]
            self.assertEqual((i[at], i[at + 1]), (rounds + 1, i_size))

    def test_knobs_bind_to_defaults_by_position(self) -> None:
        blueprint = bot.Blueprint(
            guards=(bot.Noise(bot.Knob("NOISE")),),
            signals=(
                bot.Frequency(bot.OPP, 0.5),
                bot.Frequency(bot.MY, bot.Knob("DECAY")),
            ),
        )
        compiled = blueprint.compile({"DECAY": 0.8, "NOISE": 0.1})
        spec = compiled.spec
        binds = list(spec[spec[c.H_BIND_AT] : spec[c.H_BIND_AT] + spec[c.H_NKNOB]])
        self.assertEqual(binds, [1, -1, 0])  # NOISE, a literal 0.5, DECAY
        self.assertEqual(list(compiled.knobs), [0.1, 0.5, 0.8])

    def test_choose_selector_binds_its_index(self) -> None:
        blueprint = bot.Blueprint(
            signals=(bot.LastMove(),),
            scorer=bot.Dirichlet(0.9),
            selector=bot.ChooseSelector(
                bot.Knob("SELECT"), (bot.Thompson(), bot.Greedy())
            ),
        )
        spec = blueprint.compile({"SELECT": 1}).spec
        self.assertEqual(spec[c.H_NSEL], 2)
        self.assertGreaterEqual(spec[c.H_SEL_K], 0)


if __name__ == "__main__":
    unittest.main()
