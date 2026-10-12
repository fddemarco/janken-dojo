"""Oracles: the stage, the referee's pure and arm Oracles, pools, calibration."""

import os
import pathlib
import random

import numpy as np
import pytest

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
  core:
    Heuristic: {signal: {Constant: [ROCK]}, rotation: COPY}
"""
SCORED_BOT = """description: a bandit over two arms of an L1 (L2).
blueprint:
  core:
    Bandit:
      predictors: [{bot: copy_last, rotations: [BEAT, COPY]}]
      scorer: {DecayedNet: {decay: 0.9}}
      selector: Greedy
"""
PURE = """description: a pure Oracle.
mocks: {mocked}
blueprint:
  core:
    Heuristic: {{signal: {{Oracle: {{wins: {wins}}}}}, rotation: BEAT}}
"""
ARM = """description: an Oracle arm before a rock arm.
blueprint:
  core:
    Bandit:
      predictors: [{bot: sure_win}, {bot: rock, rotations: [BEAT]}]
"""
# The L1 blocks the bots above name as arms (blocks/: never in a pool).
BLOCKS = {
    "copy_last": """blueprint:
  core:
    Heuristic: {signal: {LastMove: {of: OPP}}, rotation: COPY}
""",
    "sure_win": """blueprint:
  core:
    Heuristic: {signal: {Oracle: {wins: [1.0]}}, rotation: BEAT}
""",
}


def arm_symbol(stage: bot.Oracle, opp: int, opp_level: int) -> int:
    """An Oracle arm's move in round 0 after a hand-written reveal."""
    runner = Runner(
        bot.Blueprint(
            core=bot.Bandit(
                predictors=(stage,), rotations=(bot.BEAT,), selector=bot.First()
            )
        )
    )
    at = mocks.oracle_cell(
        bot.Blueprint(
            core=bot.Bandit(predictors=(stage,), rotations=(bot.BEAT,))
        ).compile({})
    )
    runner.i[at : at + 3] = (1, opp, opp_level)
    empty = np.zeros(0, np.int64)
    return int(
        pipeline.play(
            runner.f, runner.i, runner.prm, empty, empty, 0, runner.spec, runner.knobs
        )
    )


class TestOracleStage:
    def setup_method(self) -> None:
        random.seed(2)

    def test_it_wins_with_the_chance_of_the_opponents_level(self) -> None:
        stage = bot.Oracle(wins=(0.0, 1.0))
        assert arm_symbol(stage, S, 2) == R  # L2: always wins
        assert arm_symbol(stage, S, 7) == R  # above: the last entry
        lost_or_tied = {arm_symbol(stage, S, 1) for _ in range(30)}
        assert lost_or_tied == {S, P}  # L1: never wins, ties and losses

    def test_oracles_draw_each_other_by_default(self) -> None:
        moves = {arm_symbol(bot.Oracle(), S, c.LEVEL_ORACLE) for _ in range(20)}
        assert moves == {S}

    def test_without_a_reveal_it_has_no_symbol(self) -> None:
        runner = Runner(
            bot.Blueprint(
                core=bot.Bandit(
                    predictors=(bot.Oracle(),),
                    rotations=(bot.BEAT,),
                    selector=bot.First(fallback=ROCK),
                )
            )
        )
        assert runner.moves([P, S], [S, P]) == [R, R, R]

    def test_it_mocks_only_the_bots_own_expert(self) -> None:
        with pytest.raises(blueprint.BlueprintError):
            bot.Blueprint(core=bot.Bandit(predictors=(bot.Sim(bot.Oracle()),))).compile(
                {}
            )
        with pytest.raises(blueprint.BlueprintError):
            bot.Blueprint(
                core=bot.Bandit(predictors=(bot.Oracle(), bot.Oracle()))
            ).compile({})


class BotsDir:
    """A temporary bots dir: rock (L1), a scored bot (L2), a pure Oracle of rock."""

    @pytest.fixture(autouse=True)
    def _bots_dir(self, tmp_path: pathlib.Path) -> None:
        self.tmp = str(tmp_path)
        os.makedirs(os.path.join(self.tmp, "blocks"))
        for stem, text in BLOCKS.items():
            self.write(os.path.join("blocks", stem), text)
        self.write("rock", ROCK_BOT)
        self.write("scored", SCORED_BOT)
        self.pure = self.write("pure", PURE.format(mocked="rock", wins="[1.0]"))

    def write(self, stem: str, text: str) -> str:
        path = os.path.join(self.tmp, stem + ".yaml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def path(self, stem: str) -> str:
        return os.path.join(self.tmp, stem + ".yaml")

    def play(self, a: str, b: str, rounds: int = 6) -> str:
        (result,) = play_pairs([(make_spec(a), make_spec(b))], rounds, [1])
        return result.moves


class TestReferee(BotsDir):
    def test_a_pure_oracle_plays_the_drawn_outcome_without_its_pipeline(
        self,
    ) -> None:
        # Its own pipeline has no reveal: it would play First's random fallback.
        assert self.play(self.pure, self.path("rock")) == "pr" * 6
        assert self.play(self.path("rock"), self.pure) == "rp" * 6

    def test_a_pure_oracle_reads_the_opponents_level(self) -> None:
        by_level = self.write("by_level", PURE.format(mocked="", wins="[0.0, 1.0]"))
        moves = self.play(by_level, self.path("scored"), 20)
        mine, theirs = moves[0::2], moves[1::2]
        beats = {"r": "p", "p": "s", "s": "r"}
        assert all(beats[o] == m for m, o in zip(mine, theirs))

    def test_two_pure_oracles_draw(self) -> None:
        other = self.write("pure2", PURE.format(mocked="scored", wins="[1.0]"))
        moves = self.play(self.pure, other, 10)
        assert moves[0::2] == moves[1::2]

    def test_an_arm_is_told_the_move_and_level(self) -> None:
        arm = self.write("arm", ARM)
        assert self.play(arm, self.path("rock")) == "pr" * 6

    def test_an_arm_vs_a_pure_oracle_is_untold_and_drawn(self) -> None:
        arm = self.write("arm", ARM)
        # The arm moves first, untold: its rock arm's BEAT, PAPER; the pure
        # Oracle draws vs an Oracle.
        assert self.play(arm, self.pure) == "pp" * 6

    def test_two_arms_play_paper(self) -> None:
        arm = self.write("arm", ARM)
        arm2 = self.write("arm2", ARM)
        assert self.play(arm, arm2) == "pp" * 6


class TestKind(BotsDir):
    def test_kinds_and_levels(self) -> None:
        arm = self.write("arm", ARM)
        assert mocks.path_kind(self.path("rock")) == c.ORACLE_NONE
        assert mocks.path_kind(self.pure) == c.ORACLE_PURE
        assert mocks.path_kind(arm) == c.ORACLE_ARM
        assert mocks.path_level(arm) == levels.ORACLE
        assert mocks.path_level(self.path("scored")) == 2


class TestPool(BotsDir):
    def stems(self, use_mocks: bool) -> set[str]:
        return {bot_name(p) for p in eligible(self.tmp, (), use_mocks)}

    def test_pools_draw_pure_oracles_for_the_bots_they_mock_never_arms(
        self,
    ) -> None:
        self.write("arm", ARM)
        assert self.stems(False) == {"rock", "scored"}
        assert self.stems(True) == {"pure", "scored"}


class TestCalibrate:
    def test_win_chances_are_the_mean_per_level(self) -> None:
        rows = {
            "a": calibrate.Row(0.5, 0.25, 0.25, 2),
            "b": calibrate.Row(0.3, 0.35, 0.35, 2),
            "z": calibrate.Row(0.9, 0.05, 0.05, 1),
        }
        means = calibrate.level_wins(rows)
        assert list(means) == [1, 2]
        assert means[1] == pytest.approx(0.9, rel=0, abs=0.5e-7)
        assert means[2] == pytest.approx(0.4, rel=0, abs=0.5e-7)


class TestGuard(BotsDir):
    def test_an_oracle_is_never_exported_nor_in_a_tournament(self) -> None:
        with pytest.raises(export.ExportError):
            export.scripts(self.pure, 10)
        names = {bot_name(p) for p in discover_bots(self.tmp)}
        assert names == {"rock", "scored"}
