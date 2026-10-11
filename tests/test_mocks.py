"""Oracles: the stage, the referee's pure and arm Oracles, pools, calibration."""

import os
import random
import tempfile
import unittest

import numpy as np

from janken import export, mocks
from janken.engine import play_pairs
from janken.kit import blueprint, bot, levels, pipeline
from janken.kit import codes as c
from janken.kit.moves import PAPER, ROCK, SCISSORS
from janken.lab import calibrate
from janken.lab.pool import eligible
from janken.match import bot_name
from janken.spec import make_spec
from janken.tournament import discover_bots
from tests.test_stages import Runner

R, P, S = ROCK, PAPER, SCISSORS
ROCK_BOT = """description: always rock (L1).
blueprint:
  signals: [{Constant: [ROCK]}]
  rotations: [COPY]
"""
SCORED_BOT = """description: a bandit over two arms (L2).
blueprint:
  signals: [{LastMove: {of: OPP}}]
  rotations: [BEAT, COPY]
  scorer: {DecayedNet: {decay: 0.9}}
  selector: Greedy
"""
PURE = """description: a pure Oracle.
mocks: {mocked}
blueprint:
  signals: [{{Oracle: {{wins: {wins}}}}}]
"""
ARM = """description: an Oracle arm before a rock arm.
blueprint:
  signals: [{Oracle: {wins: [1.0]}}, {Constant: [ROCK]}]
  rotations: [BEAT]
"""


def arm_symbol(stage: bot.Oracle, opp: int, opp_level: int) -> int:
    """An Oracle arm's move in round 0 after a hand-written reveal."""
    runner = Runner(
        bot.Blueprint(signals=(stage,), rotations=(bot.BEAT,), selector=bot.First())
    )
    at = mocks.oracle_cell(
        bot.Blueprint(signals=(stage,), rotations=(bot.BEAT,)).compile({})
    )
    runner.i[at : at + 3] = (1, opp, opp_level)
    empty = np.zeros(0, np.int64)
    return int(
        pipeline.play(
            runner.f, runner.i, runner.prm, empty, empty, 0, runner.spec, runner.knobs
        )
    )


class OracleStageTest(unittest.TestCase):
    def setUp(self) -> None:
        random.seed(2)

    def test_it_wins_with_the_chance_of_the_opponents_level(self) -> None:
        stage = bot.Oracle(wins=(0.0, 1.0))
        self.assertEqual(arm_symbol(stage, S, 2), R)  # L2: always wins
        self.assertEqual(arm_symbol(stage, S, 7), R)  # above: the last entry
        lost_or_tied = {arm_symbol(stage, S, 1) for _ in range(30)}
        self.assertEqual(lost_or_tied, {S, P})  # L1: never wins, ties and losses

    def test_oracles_draw_each_other_by_default(self) -> None:
        moves = {arm_symbol(bot.Oracle(), S, c.LEVEL_ORACLE) for _ in range(20)}
        self.assertEqual(moves, {S})

    def test_without_a_reveal_it_has_no_symbol(self) -> None:
        runner = Runner(
            bot.Blueprint(
                signals=(bot.Oracle(),),
                rotations=(bot.BEAT,),
                selector=bot.First(fallback=ROCK),
            )
        )
        self.assertEqual(runner.moves([P, S], [S, P]), [R, R, R])

    def test_it_mocks_only_the_bots_own_expert(self) -> None:
        with self.assertRaises(blueprint.BlueprintError):
            bot.Blueprint(signals=(bot.Sim(bot.Oracle()),)).compile({})
        with self.assertRaises(blueprint.BlueprintError):
            bot.Blueprint(signals=(bot.Oracle(), bot.Oracle())).compile({})


class BotsDir(unittest.TestCase):
    """A temporary bots dir: rock (L1), a scored bot (L2), a pure Oracle of rock."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.write("rock", ROCK_BOT)
        self.write("scored", SCORED_BOT)
        self.pure = self.write("pure", PURE.format(mocked="rock", wins="[1.0]"))

    def write(self, stem: str, text: str) -> str:
        path = os.path.join(self.tmp.name, stem + ".yaml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def path(self, stem: str) -> str:
        return os.path.join(self.tmp.name, stem + ".yaml")

    def play(self, a: str, b: str, rounds: int = 6) -> str:
        (result,) = play_pairs([(make_spec(a), make_spec(b))], rounds, [1])
        return result.moves


class RefereeTest(BotsDir):
    def test_a_pure_oracle_plays_the_drawn_outcome_without_its_pipeline(
        self,
    ) -> None:
        # Its own pipeline has no reveal: it would play First's random fallback.
        self.assertEqual(self.play(self.pure, self.path("rock")), "pr" * 6)
        self.assertEqual(self.play(self.path("rock"), self.pure), "rp" * 6)

    def test_a_pure_oracle_reads_the_opponents_level(self) -> None:
        by_level = self.write("by_level", PURE.format(mocked="", wins="[0.0, 1.0]"))
        moves = self.play(by_level, self.path("scored"), 20)
        mine, theirs = moves[0::2], moves[1::2]
        beats = {"r": "p", "p": "s", "s": "r"}
        self.assertTrue(all(beats[o] == m for m, o in zip(mine, theirs)))

    def test_two_pure_oracles_draw(self) -> None:
        other = self.write("pure2", PURE.format(mocked="scored", wins="[1.0]"))
        moves = self.play(self.pure, other, 10)
        self.assertEqual(moves[0::2], moves[1::2])

    def test_an_arm_is_told_the_move_and_level(self) -> None:
        arm = self.write("arm", ARM)
        self.assertEqual(self.play(arm, self.path("rock")), "pr" * 6)

    def test_an_arm_vs_a_pure_oracle_is_untold_and_drawn(self) -> None:
        arm = self.write("arm", ARM)
        # The arm moves first, untold: its rock arm's BEAT, PAPER; the pure
        # Oracle draws vs an Oracle.
        self.assertEqual(self.play(arm, self.pure), "pp" * 6)

    def test_two_arms_play_paper(self) -> None:
        arm = self.write("arm", ARM)
        arm2 = self.write("arm2", ARM)
        self.assertEqual(self.play(arm, arm2), "pp" * 6)


class KindTest(BotsDir):
    def test_kinds_and_levels(self) -> None:
        arm = self.write("arm", ARM)
        self.assertEqual(mocks.path_kind(self.path("rock")), c.ORACLE_NONE)
        self.assertEqual(mocks.path_kind(self.pure), c.ORACLE_PURE)
        self.assertEqual(mocks.path_kind(arm), c.ORACLE_ARM)
        self.assertEqual(mocks.path_level(arm), levels.ORACLE)
        self.assertEqual(mocks.path_level(self.path("scored")), 2)


class PoolTest(BotsDir):
    def stems(self, use_mocks: bool) -> set[str]:
        return {bot_name(p) for p in eligible(self.tmp.name, (), use_mocks)}

    def test_pools_draw_pure_oracles_for_the_bots_they_mock_never_arms(
        self,
    ) -> None:
        self.write("arm", ARM)
        self.assertEqual(self.stems(False), {"rock", "scored"})
        self.assertEqual(self.stems(True), {"pure", "scored"})


class CalibrateTest(unittest.TestCase):
    def test_win_chances_are_the_mean_per_level(self) -> None:
        rows = {
            "a": calibrate.Row(0.5, 0.25, 0.25, 2),
            "b": calibrate.Row(0.3, 0.35, 0.35, 2),
            "z": calibrate.Row(0.9, 0.05, 0.05, 1),
        }
        means = calibrate.level_wins(rows)
        self.assertEqual(list(means), [1, 2])
        self.assertAlmostEqual(means[1], 0.9)
        self.assertAlmostEqual(means[2], 0.4)


class GuardTest(BotsDir):
    def test_an_oracle_is_never_exported_nor_in_a_tournament(self) -> None:
        with self.assertRaises(export.ExportError):
            export.scripts(self.pure, self.tmp.name, 10)
        names = {bot_name(p) for p in discover_bots(self.tmp.name)}
        self.assertEqual(names, {"rock", "scored"})
