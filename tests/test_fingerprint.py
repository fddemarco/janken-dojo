"""Fingerprints from scripted probes: tournament exports and lab gauntlet logs."""

import math
import pathlib

import pytest

from janken.lab import fingerprint as fp
from janken.lab import gauntlet

CYCLE = "bots/inactive/probes/probe_cycle3.yaml"
BLOCKS = "bots/inactive/probes/probe_blocks50.yaml"
PROBES = (CYCLE, BLOCKS)
EXPORT = """﻿When,Kind,Bot A,Bot B,Score,Draws,Forfeit
2026-10-13 22:22,tournament,Learner,Probe_Cycle3,200–10,40,
2026-10-13 22:22,tournament,⏸ Probe Blocks50,Learner,50–150,50,
2026-10-13 22:22,tournament,Learner,Probe_Cycle3,190–20,40,
2026-10-13 22:22,tournament,Learner,Stranger,90–80,80,
2026-10-13 22:22,tournament,Probe_Cycle3,Probe Blocks50,100–100,50,
"""


@pytest.fixture
def export(tmp_path: pathlib.Path) -> str:
    path = tmp_path / "export.csv"
    path.write_text(EXPORT, encoding="utf-8")
    return str(path)


class TestReadExport:
    def test_reads_names_scores_and_draws(self, export: str) -> None:
        first, second = fp.read_export(export)[:2]
        assert first == fp.Match("Learner", "Probe_Cycle3", 200, 10, 40)
        assert second.a == "Probe Blocks50"  # the pause sign is dropped
        assert second.rounds == 250


class TestProbeOf:
    def test_a_name_containing_a_probes_stem_is_that_probe(self) -> None:
        assert fp.probe_of("Probe_Cycle3", PROBES) == CYCLE
        assert fp.probe_of("my probe-blocks50 bot", PROBES) == BLOCKS

    def test_other_names_are_no_probe(self) -> None:
        assert fp.probe_of("Learner", PROBES) == ""


class TestCompetition:
    def test_averages_each_bots_margin_per_round_over_each_probe(
        self, export: str
    ) -> None:
        seen = fp.competition(fp.read_export(export), PROBES)
        assert set(seen) == {"Learner"}  # probes and probe-less bots are left out
        assert seen["Learner"][CYCLE] == pytest.approx((190 / 250 + 170 / 250) / 2)
        assert seen["Learner"][BLOCKS] == pytest.approx(100 / 250)

    def test_skips_matches_with_no_round(self) -> None:
        empty = fp.Match("Learner", "Probe_Cycle3", 0, 0, 0)
        assert fp.competition([empty], PROBES) == {}


class TestLab:
    def test_a_probes_share_lost_is_its_opponents_margin(self) -> None:
        done: gauntlet.Log = {
            gauntlet.Job(CYCLE, "bots/l1/x.yaml", 1): gauntlet.Played(0.1, 0.7),
            gauntlet.Job(CYCLE, "bots/l1/x.yaml", 2): gauntlet.Played(0.1, 0.5),
            gauntlet.Job("bots/l1/other.yaml", "bots/l1/x.yaml", 1): gauntlet.Played(
                0.9, 0.0
            ),
        }
        assert fp.lab(done, PROBES) == {"bots/l1/x.yaml": {CYCLE: pytest.approx(0.5)}}


class TestNearest:
    def test_ranks_by_root_mean_square_difference_over_shared_probes(self) -> None:
        library = {
            "far": {CYCLE: 0.0, BLOCKS: 0.0},
            "near": {CYCLE: 0.7, BLOCKS: 0.4},
            "elsewhere": {"bots/inactive/probes/probe_other.yaml": 0.9},
        }
        ranked = fp.nearest({CYCLE: 0.8, BLOCKS: 0.4}, library, 3)
        assert [bot for bot, _ in ranked] == ["near", "far"]  # nothing shared: out
        assert ranked[0][1] == pytest.approx(math.sqrt(0.01 / 2))

    def test_keeps_only_k(self) -> None:
        library = {f"b{i}": {CYCLE: i / 10} for i in range(5)}
        assert len(fp.nearest({CYCLE: 0.0}, library, 2)) == 2
