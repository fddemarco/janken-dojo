"""janken/lab/gauntlet.py: the log, the per-opponent shares, the Nash verdict and
the variants' sampling, on synthetic data (no engine)."""

import pathlib
import random

import pytest

from janken.lab import gauntlet
from janken.lab import space as spaces
from janken.lab.gauntlet import Job, Played

A, B, C = "bots/l9/a.yaml", "bots/l9/b.yaml", "bots/l9/c.yaml"


class TestLog:
    def test_appended_matches_load_back(self, tmp_path: pathlib.Path) -> None:
        log = str(tmp_path / "g" / "log.jsonl")
        gauntlet.append(log, 250, {Job(A, B, 1): Played(0.4, 0.3)})
        gauntlet.append(log, 250, {Job(A, B, 2): Played(0.5, 0.2)})
        assert gauntlet.load(log, 250) == {
            Job(A, B, 1): Played(0.4, 0.3),
            Job(A, B, 2): Played(0.5, 0.2),
        }

    def test_matches_of_other_lengths_are_left_out(
        self, tmp_path: pathlib.Path
    ) -> None:
        log = str(tmp_path / "log.jsonl")
        gauntlet.append(log, 200, {Job(A, B, 1): Played(0.4, 0.3)})
        assert gauntlet.load(log, 250) == {}

    def test_no_log_is_an_empty_one(self, tmp_path: pathlib.Path) -> None:
        assert gauntlet.load(str(tmp_path / "none.jsonl"), 250) == {}

    def test_missing_skips_what_was_played_and_goes_seed_by_seed(self) -> None:
        done = {Job(A, B, 1): Played(0.4, 0.3)}
        assert gauntlet.missing([A], [B, C], [1, 2], done) == [
            Job(A, C, 1),
            Job(A, B, 2),
            Job(A, C, 2),
        ]


class TestShares:
    def test_a_share_is_the_mean_with_its_confidence_interval(self) -> None:
        got = gauntlet.share(B, [Played(0.3, 0.3), Played(0.5, 0.2)])
        assert got.won == pytest.approx(0.4)
        assert got.lost == pytest.approx(0.25)
        # sd of (0.3, 0.5) is 0.1414; half width 1.96 * 0.1414 / sqrt(2)
        assert got.half_width == pytest.approx(0.196, abs=1e-3)
        assert got.matches == 2

    def test_one_match_has_no_spread(self) -> None:
        assert gauntlet.share(B, [Played(0.4, 0.3)]).half_width == 0.0

    def test_shares_cover_the_opponents_met_in_list_order(self) -> None:
        done = {Job(A, C, 1): Played(0.4, 0.3), Job(A, B, 1): Played(0.5, 0.2)}
        rows = gauntlet.shares(done, A, [B, C, "never/met.yaml"], [1])
        assert [r.opponent for r in rows] == [B, C]


class TestNash:
    def test_a_bot_no_probe_skews_is_nash_like(self) -> None:
        verdict = gauntlet.nash_verdict(
            A, {B: [Played(0.34, 0.33)], C: [Played(0.31, 0.36)]}, skew=0.1
        )
        assert verdict.nash_like
        assert verdict.probe == C  # the most skewed one is reported

    def test_one_skewed_probe_makes_a_real_bot(self) -> None:
        verdict = gauntlet.nash_verdict(
            A, {B: [Played(0.34, 0.33)], C: [Played(0.10, 0.80)]}, skew=0.1
        )
        assert not verdict.nash_like
        assert (verdict.probe, verdict.won, verdict.lost) == (C, 0.10, 0.80)

    def test_verdicts_read_the_log(self) -> None:
        done = {Job(A, B, s): Played(0.9, 0.05) for s in (1, 2)}
        done |= {Job(C, B, s): Played(0.33, 0.33) for s in (1, 2)}
        verdicts = gauntlet.nash_verdicts(done, [A, C], [B], [1, 2], skew=0.1)
        assert [v.nash_like for v in verdicts] == [False, True]


class TestVariants:
    def test_float_values_fill_every_stratum_of_the_range(self) -> None:
        values = gauntlet.quantiles(
            spaces.Param("float", 0.0, 1.0), 10, random.Random(0)
        )
        assert sorted(int(float(v) * 10) for v in values) == list(range(10))

    def test_log_ranges_are_spread_on_the_log_scale(self) -> None:
        values = gauntlet.quantiles(
            spaces.Param("float", 0.01, 100.0, log=True), 4, random.Random(0)
        )
        assert sum(float(v) < 1.0 for v in values) == 2

    def test_int_and_categorical_values_stay_in_their_kind(self) -> None:
        ints = gauntlet.quantiles(spaces.Param("int", 1, 2), 6, random.Random(0))
        assert set(ints) <= {1, 2}
        assert all(isinstance(v, int) for v in ints)
        picked = gauntlet.quantiles(
            spaces.Param("categorical", choices=(3, 5)), 4, random.Random(0)
        )
        assert sorted(picked) == [3, 3, 5, 5]

    def test_a_spec_names_its_overrides_sorted(self) -> None:
        assert gauntlet.spec_text(A, {"Z": 1, "B": 0.5}) == A + ":B=0.5,Z=1"

    def test_move_probabilities_must_fit_in_one(self) -> None:
        assert gauntlet.is_valid({"P_ROCK": 0.5, "P_PAPER": 0.4})
        assert not gauntlet.is_valid({"P_ROCK": 0.7, "P_PAPER": 0.4})
        assert gauntlet.is_valid({"DECAY": 0.9})

    def test_candidates_are_distinct_valid_and_seeded(self) -> None:
        space = spaces.Space(
            A,
            1.0,
            {
                "P_ROCK": spaces.Param("float", 0.3, 0.9),
                "P_PAPER": spaces.Param("float", 0.0, 0.5),
            },
        )
        first = gauntlet.candidates(A, space, per_bot=5, draws=3, seed=7)
        assert first == gauntlet.candidates(A, space, per_bot=5, draws=3, seed=7)
        assert len(first) == len(set(first)) <= 15
        assert all(t.startswith(A + ":P_PAPER=") for t in first)
        for text in first:
            values = dict(kv.split("=") for kv in text.split(":", 1)[1].split(","))
            assert float(values["P_ROCK"]) + float(values["P_PAPER"]) <= 1.0
        assert first != gauntlet.candidates(A, space, per_bot=5, draws=3, seed=8)
