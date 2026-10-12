"""Species and versions: stems, research/species.md, and how a kept bot is classified."""

import dataclasses
import pathlib

import numpy as np
import polars as pl
import pytest

from janken import settings
from janken.lab import classify, workflows
from janken.lab.dataset import Sequences
from janken.notebook import species
from tests import data

CONFIG: settings.SpeciesConfig = dataclasses.replace(
    settings.config().species,
    agreement=0.8,
    profile_correlation=0.7,
    min_matchup_matches=10,
    alpha=0.05,
    speed_factor=2.0,
)
ROUND_ROBINS = 20


class TestStems:
    @pytest.mark.parametrize(
        ("stem", "name", "number"),
        [("smartbot_v1", "smartbot", 1), ("gate_v2_v12", "gate_v2", 12)],
    )
    def test_a_version_names_its_species_and_number(
        self, stem: str, name: str, number: int
    ) -> None:
        version = species.parse_stem(stem)
        assert (version.species, version.number) == (name, number)
        assert version.stem == stem
        assert species.is_versioned(stem)

    @pytest.mark.parametrize("stem", ["smartbot", "smartbot_v0", "v1", "x_v1a"])
    def test_a_plain_stem_is_no_version(self, stem: str) -> None:
        assert not species.is_versioned(stem)
        with pytest.raises(species.SpeciesError):
            species.parse_stem(stem)

    @pytest.mark.parametrize("name", ["Smart", "smart_v3", "9lives", ""])
    def test_a_species_name_is_plain_snake_case(self, name: str) -> None:
        with pytest.raises(species.SpeciesError):
            species.check_name(name)


TABLE = """# Species

Some prose | with a pipe.

| species | level | current | versions | variants |
|---|---|---|---|---|
| `smartbot` | L2 | `smartbot_v1` | v1 ← `smartbot` | |
| `rock` | L1 | `rock_v1` | v1 ← `rock` | |

Trailing prose.
"""


class TestRegistry:
    def test_the_sample_file_round_trips_byte_for_byte(self) -> None:
        with open(species.path(data.RESEARCH), encoding="utf-8") as f:
            text = f.read()
        assert species.parse(text).render() == text

    def test_promote_appends_the_lineage_and_moves_current(self) -> None:
        book, stem = species.parse(TABLE).promote(
            "smartbot", "smartbot_decay", "[0031](experiments/0031-x.md)"
        )
        assert stem == "smartbot_v2"
        row = book.get("smartbot")
        assert row.current == "smartbot_v2"
        assert row.versions.endswith(
            "; v2 ← `smartbot_decay` ([0031](experiments/0031-x.md))"
        )
        assert book.of_stem("smartbot_v2") == row
        untouched = [line for line in book.lines if "smartbot" not in line]
        assert untouched == [
            line for line in TABLE.splitlines() if "smartbot" not in line
        ]

    def test_add_and_variant(self) -> None:
        book = species.parse(TABLE).add("bayes", "L2", "bayes_combiner", "[0040](x)")
        assert book.species[-1] == species.Species(
            "bayes", "L2", "bayes_v1", "v1 ← `bayes_combiner` ([0040](x))", ""
        )
        assert book.lines[-3].startswith("| `bayes` |")  # after the last row
        book = book.add_variant("rock", "rock_noisy", "[0041](y)")
        assert book.get("rock").variants == "`rock_noisy` ([0041](y))"
        with pytest.raises(species.SpeciesError):
            book.add("bayes", "L1", "z", "")
        with pytest.raises(species.SpeciesError):
            book.get("paper")


class TestAgreement:
    def test_abstentions_are_left_out(self) -> None:
        a = np.array([[0, 1, 2, -1], [1, 1, 3, 2]])
        b = np.array([[0, 2, 2, 0], [-1, 1, 0, 2]])
        assert classify.agreement(a, b) == pytest.approx(4 / 5)
        assert classify.agreement(np.array([-1]), np.array([0])) == 0.0

    def test_ranked_and_pairs_put_the_closest_first(self) -> None:
        cand = np.array([0, 1, 2, 0])
        field = {"x_v1": np.array([0, 1, 2, 1]), "y_v1": np.array([0, 1, 2, 0])}
        kin = classify.ranked(cand, field, {"x_v1": "L1", "y_v1": "L2"})
        assert [(k.stem, k.agreement) for k in kin] == [("y_v1", 1.0), ("x_v1", 0.75)]
        assert classify.pairs(field) == [("x_v1", "y_v1", 0.75)]


def test_spread_keeps_whole_matches_evenly() -> None:
    seqs = Sequences(
        match_ids=np.arange(5, dtype=np.int64),
        seeds=np.arange(5, dtype=np.int64) * 10,
        starts=np.array([0, 2, 5, 6, 8, 11], np.int64),
        p1=np.arange(11, dtype=np.int64),
        p2=np.arange(11, dtype=np.int64) + 100,
        p1_index=np.zeros(5, np.int64),
        p2_index=np.ones(5, np.int64),
        labels=["a", "b"],
    )
    got = seqs.spread(3)
    assert got.match_ids.tolist() == [0, 2, 4]
    assert got.starts.tolist() == [0, 2, 3, 6]
    assert got.p1.tolist() == [0, 1, 5, 8, 9, 10]
    assert got.p2.tolist() == [100, 101, 105, 108, 109, 110]
    assert seqs.spread(9) is seqs


def run(
    profile: dict[str, tuple[float, float]], h2h: float = 0.5, rrs: int = ROUND_ROBINS
) -> pl.DataFrame:
    """A paired run in long form: candidates a (challenger) and b (incumbent) meet
    each pool opponent once per round robin; `profile` gives {opponent: (a's
    result, b's result)}; they meet each other with a's result `h2h`."""
    rows = []
    for rr in range(rrs):
        for opp, (ra, rb) in profile.items():
            for bot, result in (("a", ra), ("b", rb)):
                rows.append((rr, bot, opp, opp, False, result))
        rows.append((rr, "a", "b", "b", True, h2h))
        rows.append((rr, "b", "a", "a", True, 1 - h2h))
    return pl.DataFrame(
        rows,
        schema=["rr", "bot", "opp", "opp_stem", "opp_cand", "result"],
        orient="row",
    )


EVEN = {"o1": (1.0, 1.0), "o2": (0.5, 0.5), "o3": (0.0, 0.0)}


class TestMatchups:
    def test_a_clear_gain_is_better_and_nothing_is_worse(self) -> None:
        found = classify.matchups(run({**EVEN, "o4": (1.0, 0.0)}), "a", "b", CONFIG)
        by = {m.opponent: m for m in found}
        assert by["o4"].better and not by["o4"].worse
        assert not any(m.worse for m in found)
        assert classify.HEAD_TO_HEAD in by
        assert not classify.as_good(found)

    def test_too_few_matches_leave_a_matchup_out(self) -> None:
        found = classify.matchups(run(EVEN, rrs=5), "a", "b", CONFIG)
        assert found == []

    def test_a_lost_head_to_head_is_worse(self) -> None:
        found = classify.matchups(run(EVEN, h2h=0.0), "a", "b", CONFIG)
        assert [m.opponent for m in found if m.worse] == [classify.HEAD_TO_HEAD]

    def test_flat_profiles_correlate_only_when_equal(self) -> None:
        flat = {"o1": (0.5, 0.5), "o2": (0.5, 0.5)}
        assert classify.profile_correlation(run(flat), "a", "b") == 1.0
        apart = {"o1": (1.0, 0.5), "o2": (1.0, 0.5)}
        assert classify.profile_correlation(run(apart), "a", "b") == 0.0
        assert classify.profile_correlation(run(EVEN), "a", "b") == pytest.approx(1.0)


def matchup(mean: float, lo: float, hi: float, strict_lo: float) -> classify.Matchup:
    return classify.Matchup("o", 20, mean, lo, hi, strict_lo)


NEAR = classify.Kin("smartbot_v1", "L2", 0.9)
SAME = matchup(0.0, -0.05, 0.05, -0.1)
BETTER = matchup(0.2, 0.1, 0.3, 0.02)
MARGINAL = matchup(0.1, 0.01, 0.2, -0.03)  # above 0 at 95%, not at Bonferroni
WORSE = matchup(-0.2, -0.3, -0.1, -0.35)


class TestDecide:
    @pytest.mark.parametrize(
        ("nearest", "level", "correlation"),
        [
            (NEAR, "L3", 0.9),  # versions never cross levels
            (dataclasses.replace(NEAR, agreement=0.5), "L2", 0.9),
            (NEAR, "L2", 0.2),
        ],
        ids=["other level", "low agreement", "low correlation"],
    )
    def test_new_species(
        self, nearest: classify.Kin, level: str, correlation: float
    ) -> None:
        decided = classify.decide(nearest, level, correlation, [BETTER], CONFIG)
        assert decided.outcome == classify.NEW

    @pytest.mark.parametrize(
        ("compared", "speedup", "outcome"),
        [
            ([SAME, BETTER], 1.0, classify.PROMOTE),
            ([SAME, BETTER, WORSE], 9.0, classify.VARIANT),
            ([SAME, MARGINAL], 1.0, classify.VARIANT),
            ([SAME, SAME], 2.5, classify.PROMOTE),  # as good, and much faster
            ([SAME, SAME], 2.0, classify.VARIANT),  # not more than 2x
            ([SAME, WORSE], 3.0, classify.VARIANT),  # faster but worse somewhere
        ],
        ids=[
            "better",
            "worse somewhere",
            "only a marginal gain",
            "faster",
            "exactly twice as fast",
            "faster but worse",
        ],
    )
    def test_version_or_variant(
        self, compared: list[classify.Matchup], speedup: float, outcome: str
    ) -> None:
        decided = classify.decide(NEAR, "L2", 0.9, compared, CONFIG, speedup)
        assert decided.outcome == outcome
        assert decided.reasons

    def test_a_run_is_needed_only_for_an_alike_species_of_the_level(self) -> None:
        assert classify.needs_run(NEAR, "L2", CONFIG)
        assert not classify.needs_run(NEAR, "L1", CONFIG)
        assert not classify.needs_run(
            dataclasses.replace(NEAR, agreement=0.79), "L2", CONFIG
        )


class TestFiles:
    """Renaming a bot to its version, and retiring one, move its space file too."""

    def test_a_rename_carries_and_repoints_the_space(
        self, tmp_path: pathlib.Path
    ) -> None:
        bots, spaces = tmp_path / "bots", tmp_path / "spaces"
        (bots / "l1").mkdir(parents=True)
        spaces.mkdir()
        bot = bots / "l1" / "twin.yaml"
        bot.write_text("description: x\n")
        (spaces / "twin.yaml").write_text("bot: bots/l1/twin.yaml\nweight: 1.0\n")
        moved = workflows._rename(str(bot), "twin_v1", str(bots), str(spaces))
        assert moved == str(bots / "l1" / "twin_v1.yaml")
        assert not bot.exists() and not (spaces / "twin.yaml").exists()
        assert (spaces / "twin_v1.yaml").read_text() == (
            "bot: bots/l1/twin_v1.yaml\nweight: 1.0\n"
        )

    def test_retiring_moves_the_bot_and_drops_its_space(
        self, tmp_path: pathlib.Path
    ) -> None:
        bot, spaces = tmp_path / "old_v1.yaml", tmp_path / "spaces"
        spaces.mkdir()
        bot.write_text("description: x\n")
        (spaces / "old_v1.yaml").write_text("bot: old_v1.yaml\n")
        legacy = tmp_path / "inactive" / "legacy"
        moved = workflows._retire(str(bot), str(legacy), str(spaces))
        assert moved == str(legacy / "old_v1.yaml")
        assert not (spaces / "old_v1.yaml").exists()
        bot.write_text("description: y\n")
        with pytest.raises(workflows.WorkflowError):
            workflows._retire(str(bot), str(legacy), str(spaces))
