"""Tournament A/B: two groups of bots compared on the opponents both met."""

import math

import pytest

from janken.lab import fingerprint as fp
from janken.lab import tournament

Match = fp.Match


def match(a: str, b: str, wins_a: int, wins_b: int, when: str) -> Match:
    return Match(a, b, wins_a, wins_b, 250 - wins_a - wins_b, when)


class TestWindow:
    def test_is_the_overlap_of_the_two_groups_spans(self) -> None:
        matches = [
            match("New", "X", 90, 80, "2026-10-14 10:00"),
            match("New", "X", 90, 80, "2026-10-16 10:00"),
            match("Old", "X", 90, 80, "2026-10-12 10:00"),
            match("Old", "X", 90, 80, "2026-10-15 10:00"),
        ]
        assert tournament.window(matches, ["New"], ["Old"]) == (
            "2026-10-14 10:00",
            "2026-10-15 10:00",
        )

    def test_is_empty_when_a_group_never_played(self) -> None:
        span = tournament.window([match("Old", "X", 1, 0, "t1")], ["New"], ["Old"])
        assert span[0] > span[1]


class TestRecords:
    def test_counts_wins_draws_and_margins_per_opponent(self) -> None:
        matches = [
            match("New", "X", 100, 50, "t1"),  # won, +50
            match("X", "New", 80, 80, "t2"),  # drawn, 0
        ]
        rec = tournament.records(matches, ["New"], [], ("t0", "t9"))
        assert (rec["X"].matches, rec["X"].won) == (2, 0.75)
        assert rec["X"].margin == pytest.approx(0.1)

    def test_skips_teammates_excluded_names_and_matches_outside_the_span(
        self,
    ) -> None:
        matches = [
            match("New", "Mate", 250, 0, "t1"),
            match("New", "Fleet", 250, 0, "t1"),
            match("New", "X", 250, 0, "t9"),
            Match("New", "X", 0, 0, 0, "t1"),  # no round played
        ]
        span = ("t0", "t5")
        assert tournament.records(matches, ["New", "Mate"], ["Fleet"], span) == {}


class TestCompare:
    def test_averages_differences_over_common_opponents(self) -> None:
        matches = [
            match("New", "X", 100, 50, "t1"),
            match("Old", "X", 50, 100, "t1"),
            match("New", "Y", 100, 50, "t2"),
            match("Old", "Y", 100, 50, "t2"),
            match("New", "OnlyNew", 100, 50, "t2"),
        ]
        result = tournament.compare(matches, ["New"], ["Old"], [])
        assert [d.opponent for d in result.differences] == ["X", "Y"]
        assert result.won == pytest.approx(0.5)  # +1 vs X, 0 vs Y
        assert result.won_half_width == pytest.approx(1.96 * math.sqrt(0.5 / 2))

    def test_a_single_opponent_has_an_infinite_interval(self) -> None:
        matches = [match("New", "X", 100, 50, "t1"), match("Old", "X", 50, 100, "t1")]
        assert math.isinf(tournament.compare(matches, ["New"], ["Old"], []).won_half_width)

    def test_refuses_groups_with_no_common_opponent(self) -> None:
        matches = [match("New", "X", 100, 50, "t1"), match("Old", "Y", 50, 100, "t1")]
        with pytest.raises(ValueError, match="no common opponent"):
            tournament.compare(matches, ["New"], ["Old"], [])
