"""The lab: bot specs and parameters, pools, experiments, storage, analysis, tuning."""

import contextlib
import dataclasses
import io
import math
import os
import pathlib
import random
import re
import shutil
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import optuna

from janken import mocks
from janken.engine import play_pairs, registry
from janken.lab import analyze, space
from janken.lab.experiment import build_schedule, resume_experiment, run_experiment
from janken.lab.pool import sample_pool
from janken.lab.runs_db import COMPLETE, INTERRUPTED, RunStore
from janken.lab.tune import (
    Search,
    Setup,
    baseline,
    grid_space,
    run_tune,
    split_params,
)
from janken.spec import format_spec, make_spec, parse_spec

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
BOTS_DIR = os.path.join(ROOT, "bots")
SPACES_DIR = os.path.join(ROOT, "spaces")


# Cheap bots: experiments and tuning in these tests play pools of them only.
LIGHT_BOTS = (
    "rock_v1",
    "nash_v1",
    "cycler_v1",
    "wsls_v1",
    "copycat_v1",
    "reactionary_v1",
    "biased_v1",
)
POOL = 4


def bot(stem: str) -> str:
    return registry.find(BOTS_DIR, stem)


@pytest.fixture(scope="class")
def light_bots_dir(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> None:
    request.cls.bots_dir = str(tmp_path_factory.mktemp("light_bots"))
    for stem in LIGHT_BOTS:
        shutil.copy(bot(stem), request.cls.bots_dir)


@pytest.mark.usefixtures("light_bots_dir")
class LightBots:
    """A bots directory holding copies of LIGHT_BOTS only."""

    bots_dir: str

    @classmethod
    def light(cls, stem: str) -> str:
        return os.path.join(cls.bots_dir, stem + ".yaml")


def quietly(fn, *args, **kwargs):
    with (
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        return fn(*args, **kwargs)


class TestSpec:
    def test_default_and_variant_labels(self) -> None:
        assert parse_spec(bot("geometry_v1")).label == "geometry_v1"
        v = parse_spec(bot("geometry_v1") + ":ALPHA=0.1,MAX_LEN=12")
        assert v.params == {"ALPHA": 0.1, "MAX_LEN": 12}
        assert re.search(r"^geometry_v1@[0-9a-f]{6}$", v.label)
        assert parse_spec(format_spec(v)) == v
        assert (
            v.label
            == make_spec(bot("geometry_v1"), {"MAX_LEN": 12, "ALPHA": 0.1}).label
        )

    def test_unknown_parameter_is_an_error(self) -> None:
        with pytest.raises(ValueError):
            parse_spec(bot("geometry_v1") + ":ALHPA=0.1")
        with pytest.raises(ValueError):
            parse_spec(bot("nash_v1") + ":X=1")

    def test_params_reach_the_bot(self) -> None:
        cycler = make_spec(bot("cycler_v1"), {"STEP": 2, "NOISE": 0.0})
        (m,) = play_pairs([(cycler, make_spec(bot("rock_v1")))], 4, [1])
        assert m.moves[0::2] == "rspr"


class TestPool:
    def test_pools_exclude_candidates_and_are_reproducible(self) -> None:
        cand = make_spec(bot("geometry_v1"))
        a = build_schedule([cand], BOTS_DIR, 20, 3, seed=5)
        b = build_schedule(
            [make_spec(bot("geometry_v1"), {"ALPHA": 0.2})], BOTS_DIR, 20, 3, seed=5
        )
        for rr_a, rr_b in zip(a, b):
            labels = [p.label for p in rr_a["pool"]]
            assert len(labels) == 20
            assert "geometry_v1" not in labels
            # same pools and seeds for every variant: common random numbers
            assert labels == [p.label for p in rr_b["pool"]]
            assert rr_a["seeds"] == rr_b["seeds"]
        assert len(a[0]["pairs"]) == 21 * 20 // 2
        assert [p.label for p in a[0]["pool"]] != [p.label for p in a[1]["pool"]]

    def test_candidates_mode(self) -> None:
        cands = [make_spec(bot("geometry_v1")), make_spec(bot("rps4_lite_v1"))]
        rr = build_schedule(cands, BOTS_DIR, 20, 1, seed=1, mode="candidates")[0]
        assert len(rr["pairs"]) == 1 + 2 * 20

    def test_small_pool(self) -> None:
        with pytest.raises(SystemExit):
            sample_pool(BOTS_DIR, 500, random.Random(1))
        regular = [p for p in registry.discover(BOTS_DIR) if not mocks.is_mock(p)]
        assert len(
            sample_pool(BOTS_DIR, 500, random.Random(1), allow_small=True)
        ) == len(regular)


class TestExperiment(LightBots):
    @pytest.fixture(autouse=True)
    def _workspace(self, tmp_path: pathlib.Path) -> None:
        self.root = str(tmp_path)
        self.runs = RunStore.at(self.root)

    def run_exp(self, cands, **kw):
        kw.setdefault("round_robins", 2)
        kw.setdefault("rounds", 20)
        kw.setdefault("pool_size", POOL)
        return quietly(
            run_experiment,
            cands,
            self.bots_dir,
            seed=kw.pop("seed", 3),
            root=self.root,
            **kw,
        )

    def test_store_round_trip_and_reproducibility(self) -> None:
        cands = [
            make_spec(self.light("cycler_v1")),
            make_spec(self.light("wsls_v1"), {"NOISE": 0.1}),
        ]
        p1 = self.run_exp(cands, name="one")
        p2 = self.run_exp(cands, name="two")
        _, _, df = self.runs.load_run(p1)
        _, _, df2 = self.runs.load_run(p2)
        players = POOL + len(cands)
        assert df.height == 2 * (players * (players - 1) // 2)
        assert df.drop("run_id").equals(df2.drop("run_id"))
        assert "engine" not in df.columns
        assert self.runs.resolve("latest") == p2
        assert self.runs.resolve("one") == p1
        assert self.runs.status(p1) == COMPLETE

        summary = analyze.analyze_run(p1, self.root)
        assert p1 in self.runs.summaries()
        by_bot = {r["bot"]: r for r in summary["candidates_vs_pool"]}
        assert set(by_bot) == {c.label for c in cands}
        for r in by_bot.values():
            assert r["n"] == 2 * POOL
            assert r["W"] + r["D"] + r["L"] == 2 * POOL
            assert r["ci_lo"] <= r["score"]
            assert r["score"] <= r["ci_hi"]
        assert len(summary["comparisons"]) == 1
        assert summary["head_to_head"][0]["n"] == 2

        board = analyze.leaderboard(self.root)
        assert set(board["bot"]) == {c.label for c in cands}
        history = analyze.history("cycler_v1", self.root)
        assert history.height == 2
        assert history["library"].n_unique() == 1

    def test_identical_behaviour_has_zero_paired_difference(self) -> None:
        same = [
            make_spec(self.light("cycler_v1")),
            make_spec(self.light("cycler_v1"), {"NOISE": 0.05}),
        ]
        summary = analyze.analyze_run(self.run_exp(same), self.root)
        cmp = summary["comparisons"][0]
        assert (cmp["mean"], cmp["ci_lo"], cmp["ci_hi"]) == (0.0, 0.0, 0.0)

    def test_a_candidate_outside_the_bots_dir_plays_the_pool(self) -> None:
        path = os.path.join(self.root, "mystery.yaml")
        with open(path, "w") as f:
            f.write("description: uniform random play\nblueprint: {}\n")
        run = self.run_exp([make_spec(path)], round_robins=1, rounds=30)
        _, manifest, df = self.runs.load_run(run)
        assert manifest["n_matches"] == (POOL + 1) * POOL // 2
        mystery = df.filter((df["bot_a"] == "mystery") | (df["bot_b"] == "mystery"))
        assert mystery.height == POOL

    def test_an_interrupted_run_keeps_its_round_robins_and_resumes(self) -> None:
        cands = [make_spec(self.light("cycler_v1")), make_spec(self.light("wsls_v1"))]

        def stop_after_the_first(rr: int) -> None:
            if rr == 0:
                raise KeyboardInterrupt

        with pytest.raises(KeyboardInterrupt):
            self.run_exp(
                cands, round_robins=3, name="cut", on_batch=stop_after_the_first
            )
        cut = self.runs.resolve("cut")
        assert self.runs.status(cut) == INTERRUPTED
        assert self.runs.played_round_robins(cut) == {0}
        partial = analyze.analyze_run(cut, self.root)
        assert partial["round_robins_played"] == 1
        assert "Partial: 1 of 3" in analyze.render(partial)

        quietly(resume_experiment, cut, self.root)
        assert self.runs.status(cut) == COMPLETE
        whole = self.run_exp(cands, round_robins=3, name="whole")
        resumed = self.runs.matches(cut).drop("run_id")
        assert resumed.equals(self.runs.matches(whole).drop("run_id"))

    def test_a_resume_refuses_a_changed_bot(self) -> None:
        path = os.path.join(self.root, "mystery.yaml")
        with open(path, "w") as f:
            f.write("description: uniform random play\nblueprint: {}\n")

        def stop(rr: int) -> None:
            raise KeyboardInterrupt

        with pytest.raises(KeyboardInterrupt):
            self.run_exp([make_spec(path)], name="m", on_batch=stop)
        with open(path, "w") as f:
            f.write("description: something else now\nblueprint: {}\n")
        with pytest.raises(SystemExit):
            quietly(resume_experiment, "m", self.root)


class TestWilson:
    def test_bounds(self) -> None:
        lo, hi = analyze.wilson(0.5, 100)
        assert lo == pytest.approx(0.4038, rel=0, abs=0.5e-3)
        assert hi == pytest.approx(0.5962, rel=0, abs=0.5e-3)
        assert analyze.wilson(1.0, 10)[1] == pytest.approx(1.0, rel=0, abs=0.5e-7)


class TestTune(LightBots):
    def space_for(self, stem: str, weight: float = 1.0) -> space.Space:
        """The project's space file for `stem`, pointed at the light copy."""
        found = space.load(os.path.join(SPACES_DIR, stem + ".yaml"))
        return dataclasses.replace(found, bot=self.light(stem), weight=weight)

    @pytest.fixture(autouse=True)
    def _workspace(self, tmp_path: pathlib.Path) -> None:
        self.dir = str(tmp_path)
        self.setup = Setup(
            rounds=20,
            round_robins=1,
            pool_size=POOL,
            seed=1,
            bots_dir=self.bots_dir,
            root=self.dir,
        )

    def tune(self, spaces: list[space.Space], name: str, **search) -> optuna.Study:
        search.setdefault("sampler_seed", 1)
        return quietly(run_tune, spaces, name, self.setup, Search(**search))

    def test_tiny_study_runs_and_resumes(self) -> None:
        study = self.tune([self.space_for("rock_v1")], "t", trials=3)
        assert len(study.trials) == 3
        assert study.trials[0].params == {"rock_v1.NOISE": 0.0}  # baseline
        study = self.tune([self.space_for("rock_v1")], "t", trials=1)
        assert len(study.trials) == 4
        assert os.path.exists(os.path.join(self.dir, "tuning", "t", "trials.parquet"))
        grid = self.tune([self.space_for("wsls_v1")], "g", sampler="grid")
        assert len(grid.trials) == 4  # SHIFT 2 x NOISE 2
        self.setup = dataclasses.replace(self.setup, rounds=50)
        with pytest.raises(SystemExit):  # different setup
            self.tune([self.space_for("rock_v1")], "t", trials=1)

    def test_bots_tune_together_on_a_weighted_objective(self) -> None:
        spaces = [self.space_for("cycler_v1"), self.space_for("wsls_v1", weight=0.0)]
        study = self.tune(spaces, "fleet", trials=2)
        first = study.trials[0]
        assert first.params == {
            "cycler_v1.STEP": 1,
            "cycler_v1.NOISE": 0.05,
            "wsls_v1.SHIFT": 1,
            "wsls_v1.NOISE": 0.0,
        }
        bots = first.user_attrs["bots"]
        assert set(bots) == {"cycler_v1", "wsls_v1"}
        assert bots["cycler_v1"]["n"] == POOL + 1  # the pool and wsls
        assert first.value == bots["cycler_v1"]["score"]  # wsls weighs 0
        grid = self.tune(spaces, "fleet-grid", sampler="grid")
        sizes = [len(v) for v in grid_space(spaces).values()]
        assert len(sizes) == 4
        assert len(grid.trials) == math.prod(sizes)  # every combination

    def test_split_params_and_baseline(self) -> None:
        spaces = [self.space_for("cycler_v1"), self.space_for("wsls_v1")]
        assert split_params({"cycler_v1.STEP": 2, "wsls_v1.NOISE": 0.1}, spaces) == {
            "cycler_v1": {"STEP": 2},
            "wsls_v1": {"NOISE": 0.1},
        }
        assert baseline(spaces)["wsls_v1.SHIFT"] == 1

    def test_a_study_needs_weight_and_distinct_bots(self) -> None:
        with pytest.raises(SystemExit):
            self.tune([self.space_for("rock_v1", weight=0.0)], "zero", trials=1)
        with pytest.raises(ValueError):
            self.tune(
                [self.space_for("rock_v1"), self.space_for("rock_v1")],
                "twice",
                trials=1,
            )

    def test_validation_replays_each_fleet_on_its_own(self) -> None:
        spaces = [self.space_for("cycler_v1"), self.space_for("wsls_v1", weight=0.0)]
        self.tune(spaces, "v", trials=2)
        study = self.tune(
            spaces, "v", trials=0, validate_top=1, validate_round_robins=1
        )
        assert len(study.trials) == 2  # validation only: no new trials
        stored = RunStore.at(self.dir)
        runs = stored.run_ids()
        assert len(runs) == 2  # the defaults, then the best trial
        for run in runs:
            _, manifest, _ = stored.load_run(run)
            assert len(manifest["candidates"]) == 2
            assert manifest["tuning"]["study"] == "v"
        assert sorted(study.user_attrs["validations"][-1]["runs"]) == runs

    def test_validation_results_are_recorded(self) -> None:
        spaces = [self.space_for("cycler_v1"), self.space_for("wsls_v1", weight=0.0)]
        self.tune(spaces, "rec", trials=3, validate_top=2, validate_round_robins=1)
        rows = RunStore.at(self.dir).validations("tune_validations", "rec")
        assert rows.height >= 2
        first = rows.row(0, named=True)
        assert first["trial"] == -1  # the defaults come first
        assert first["champion"].startswith("cycler_v1")
        assert first["vs_defaults"] == 0.0
        assert first["n"] == POOL
        assert len(set(rows["run_id"])) == rows.height  # one run each
        text = analyze.render_validations("rec", self.dir)
        assert "vs defaults" in text
