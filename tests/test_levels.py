"""Bot levels, computed from blueprints."""

import unittest

from janken.kit import bot, levels, presets

ROCKY = bot.Constant(bot.ROCK)
LAST = bot.LastMove(bot.OPP)


def bandit(*signals: bot.SignalLike) -> bot.Ensemble:
    return bot.Ensemble(signals, bot.ALL_ROTATIONS, bot.Dirichlet(0.9))


class LevelTest(unittest.TestCase):
    def level(self, blueprint: bot.Blueprint) -> int:
        return levels.level(blueprint)

    def test_heuristics_are_level_one(self) -> None:
        self.assertEqual(self.level(bot.Blueprint(signals=(LAST,))), 1)
        sim = bot.Blueprint(signals=(bot.Sim(LAST), ROCKY), rotations=(bot.BEAT,))
        self.assertEqual(self.level(sim), 1)  # no scorer: no bandit

    def test_a_bandit_over_heuristics_is_level_two(self) -> None:
        self.assertEqual(
            self.level(bot.Blueprint.around(bandit(LAST), bot.Thompson())), 2
        )

    def test_a_single_scored_arm_is_no_bandit(self) -> None:
        one = bot.Blueprint(
            signals=(LAST,), scorer=bot.DecayedNet(0.9), selector=bot.Greedy()
        )
        self.assertEqual(self.level(one), 1)

    def test_a_replay_counts_at_its_own_level(self) -> None:
        l2 = bandit(LAST, ROCKY)
        self.assertEqual(levels.ensemble_level(l2), 2)
        l3 = bandit(LAST, bot.Replay(l2))
        self.assertEqual(levels.ensemble_level(l3), 3)
        l4 = bandit(LAST, bot.Replay(l3))
        self.assertEqual(levels.ensemble_level(l4), 4)
        lone = bot.Blueprint(
            signals=(bot.Replay(l3),), scorer=bot.DecayedNet(0.9), selector=bot.Greedy()
        )
        self.assertEqual(self.level(lone), 3)  # one replay arm: no extra layer

    def test_advanced_bots_core_is_level_three(self) -> None:
        core = presets.smartbot_sims(10, 0.95, 0.9, 12)
        self.assertEqual(levels.ensemble_level(core), 3)
        self.assertEqual(levels.ensemble_level(presets.metabot(0.95, 0.9, 12)), 2)

    def test_a_naive_bayes_combiner_is_one_above_its_inputs(self) -> None:
        self.assertEqual(levels.ensemble_level(bandit(LAST, bot.NaiveBayes())), 3)

    def test_any_oracle_makes_an_oracle(self) -> None:
        armed = bot.Blueprint.around(bandit(LAST, bot.Oracle()), bot.Thompson())
        self.assertEqual(self.level(armed), levels.ORACLE)
        self.assertEqual(levels.name(levels.ORACLE), "Oracle")
        self.assertEqual(levels.name(3), "L3")
