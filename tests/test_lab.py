"""The lab: bot specs and parameters, pools, experiments, storage, analysis, tuning."""

import contextlib
import dataclasses
import io
import math
import os
import random
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import optuna

from janken import mocks
from janken.engine import play_pairs
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
LIGHT_BOTS = ("rock", "nash", "cycler", "wsls", "copycat", "reactionary", "biased")
POOL = 4


def bot(stem):
    return os.path.join(BOTS_DIR, stem + ".yaml")


class LightBots(unittest.TestCase):
    """A bots directory holding copies of LIGHT_BOTS only."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bots_dir = tempfile.mkdtemp()
        for stem in LIGHT_BOTS:
            shutil.copy(bot(stem), cls.bots_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.bots_dir)

    @classmethod
    def light(cls, stem: str) -> str:
        return os.path.join(cls.bots_dir, stem + ".yaml")


def quietly(fn, *args, **kwargs):
    with (
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        return fn(*args, **kwargs)


class SpecTest(unittest.TestCase):
    def test_default_and_variant_labels(self):
        self.assertEqual(parse_spec(bot("geometry")).label, "geometry")
        v = parse_spec(bot("geometry") + ":ALPHA=0.1,MAX_LEN=12")
        self.assertEqual(v.params, {"ALPHA": 0.1, "MAX_LEN": 12})
        self.assertRegex(v.label, r"^geometry@[0-9a-f]{6}$")
        self.assertEqual(parse_spec(format_spec(v)), v)
        self.assertEqual(
            v.label, make_spec(bot("geometry"), {"MAX_LEN": 12, "ALPHA": 0.1}).label
        )

    def test_unknown_parameter_is_an_error(self):
        with self.assertRaises(ValueError):
            parse_spec(bot("geometry") + ":ALHPA=0.1")
        with self.assertRaises(ValueError):
            parse_spec(bot("nash") + ":X=1")

    def test_params_reach_the_bot(self):
        cycler = make_spec(bot("cycler"), {"STEP": 2, "NOISE": 0.0})
        (m,) = play_pairs([(cycler, make_spec(bot("rock")))], 4, [1])
        self.assertEqual(m.moves[0::2], "rspr")


class PoolTest(unittest.TestCase):
    def test_pools_exclude_candidates_and_are_reproducible(self):
        cand = make_spec(bot("geometry"))
        a = build_schedule([cand], BOTS_DIR, 20, 3, seed=5)
        b = build_schedule(
            [make_spec(bot("geometry"), {"ALPHA": 0.2})], BOTS_DIR, 20, 3, seed=5
        )
        for rr_a, rr_b in zip(a, b):
            labels = [p.label for p in rr_a["pool"]]
            self.assertEqual(len(labels), 20)
            self.assertNotIn("geometry", labels)
            # same pools and seeds for every variant: common random numbers
            self.assertEqual(labels, [p.label for p in rr_b["pool"]])
            self.assertEqual(rr_a["seeds"], rr_b["seeds"])
        self.assertEqual(len(a[0]["pairs"]), 21 * 20 // 2)
        self.assertNotEqual(
            [p.label for p in a[0]["pool"]], [p.label for p in a[1]["pool"]]
        )

    def test_candidates_mode(self):
        cands = [make_spec(bot("geometry")), make_spec(bot("rps4_lite"))]
        rr = build_schedule(cands, BOTS_DIR, 20, 1, seed=1, mode="candidates")[0]
        self.assertEqual(len(rr["pairs"]), 1 + 2 * 20)

    def test_small_pool(self):
        with self.assertRaises(SystemExit):
            sample_pool(BOTS_DIR, 500, random.Random(1))
        every = [os.path.join(BOTS_DIR, f) for f in os.listdir(BOTS_DIR)]
        regular = [p for p in every if p.endswith(".yaml") and not mocks.is_mock(p)]
        self.assertEqual(
            len(sample_pool(BOTS_DIR, 500, random.Random(1), allow_small=True)),
            len(regular),  # mocks only enter pools with use_mocks
        )


class ExperimentTest(LightBots):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = self.dir.name
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

    def test_store_round_trip_and_reproducibility(self):
        cands = [
            make_spec(self.light("cycler")),
            make_spec(self.light("wsls"), {"NOISE": 0.1}),
        ]
        p1 = self.run_exp(cands, name="one")
        p2 = self.run_exp(cands, name="two")
        _, _, df = self.runs.load_run(p1)
        _, _, df2 = self.runs.load_run(p2)
        players = POOL + len(cands)
        self.assertEqual(df.height, 2 * (players * (players - 1) // 2))
        self.assertTrue(df.drop("run_id").equals(df2.drop("run_id")))
        self.assertNotIn("engine", df.columns)
        self.assertEqual(self.runs.resolve("latest"), p2)
        self.assertEqual(self.runs.resolve("one"), p1)
        self.assertEqual(self.runs.status(p1), COMPLETE)

        summary = analyze.analyze_run(p1, self.root)
        self.assertIn(p1, self.runs.summaries())
        by_bot = {r["bot"]: r for r in summary["candidates_vs_pool"]}
        self.assertEqual(set(by_bot), {c.label for c in cands})
        for r in by_bot.values():
            self.assertEqual(r["n"], 2 * POOL)
            self.assertEqual(r["W"] + r["D"] + r["L"], 2 * POOL)
            self.assertLessEqual(r["ci_lo"], r["score"])
            self.assertLessEqual(r["score"], r["ci_hi"])
        self.assertEqual(len(summary["comparisons"]), 1)
        self.assertEqual(summary["head_to_head"][0]["n"], 2)

        board = analyze.leaderboard(self.root)
        self.assertEqual(set(board["bot"]), {c.label for c in cands})
        history = analyze.history("cycler", self.root)
        self.assertEqual(history.height, 2)
        self.assertEqual(history["library"].n_unique(), 1)

    def test_identical_behaviour_has_zero_paired_difference(self):
        same = [
            make_spec(self.light("cycler")),
            make_spec(self.light("cycler"), {"NOISE": 0.05}),
        ]
        summary = analyze.analyze_run(self.run_exp(same), self.root)
        cmp = summary["comparisons"][0]
        self.assertEqual((cmp["mean"], cmp["ci_lo"], cmp["ci_hi"]), (0.0, 0.0, 0.0))

    def test_a_candidate_outside_the_bots_dir_plays_the_pool(self):
        path = os.path.join(self.root, "mystery.yaml")
        with open(path, "w") as f:
            f.write("description: uniform random play\nblueprint: {}\n")
        run = self.run_exp([make_spec(path)], round_robins=1, rounds=30)
        _, manifest, df = self.runs.load_run(run)
        self.assertEqual(manifest["n_matches"], (POOL + 1) * POOL // 2)
        mystery = df.filter((df["bot_a"] == "mystery") | (df["bot_b"] == "mystery"))
        self.assertEqual(mystery.height, POOL)

    def test_an_interrupted_run_keeps_its_round_robins_and_resumes(self) -> None:
        cands = [make_spec(self.light("cycler")), make_spec(self.light("wsls"))]

        def stop_after_the_first(rr: int) -> None:
            if rr == 0:
                raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            self.run_exp(
                cands, round_robins=3, name="cut", on_batch=stop_after_the_first
            )
        cut = self.runs.resolve("cut")
        self.assertEqual(self.runs.status(cut), INTERRUPTED)
        self.assertEqual(self.runs.played_round_robins(cut), {0})
        partial = analyze.analyze_run(cut, self.root)
        self.assertEqual(partial["round_robins_played"], 1)
        self.assertIn("Partial: 1 of 3", analyze.render(partial))

        quietly(resume_experiment, cut, self.root)
        self.assertEqual(self.runs.status(cut), COMPLETE)
        whole = self.run_exp(cands, round_robins=3, name="whole")
        resumed = self.runs.matches(cut).drop("run_id")
        self.assertTrue(resumed.equals(self.runs.matches(whole).drop("run_id")))

    def test_a_resume_refuses_a_changed_bot(self) -> None:
        path = os.path.join(self.root, "mystery.yaml")
        with open(path, "w") as f:
            f.write("description: uniform random play\nblueprint: {}\n")

        def stop(rr: int) -> None:
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            self.run_exp([make_spec(path)], name="m", on_batch=stop)
        with open(path, "w") as f:
            f.write("description: something else now\nblueprint: {}\n")
        with self.assertRaises(SystemExit):
            quietly(resume_experiment, "m", self.root)


class WilsonTest(unittest.TestCase):
    def test_bounds(self):
        lo, hi = analyze.wilson(0.5, 100)
        self.assertAlmostEqual(lo, 0.4038, places=3)
        self.assertAlmostEqual(hi, 0.5962, places=3)
        self.assertAlmostEqual(analyze.wilson(1.0, 10)[1], 1.0)


class TuneTest(LightBots):
    def space_for(self, stem: str, weight: float = 1.0) -> space.Space:
        """The project's space file for `stem`, pointed at the light copy."""
        found = space.load(os.path.join(SPACES_DIR, stem + ".yaml"))
        return dataclasses.replace(found, bot=self.light(stem), weight=weight)

    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.setup = Setup(
            rounds=20,
            round_robins=1,
            pool_size=POOL,
            seed=1,
            bots_dir=self.bots_dir,
            root=self.dir.name,
        )

    def tune(self, spaces: list[space.Space], name: str, **search) -> optuna.Study:
        search.setdefault("sampler_seed", 1)
        return quietly(run_tune, spaces, name, self.setup, Search(**search))

    def test_tiny_study_runs_and_resumes(self) -> None:
        study = self.tune([self.space_for("rock")], "t", trials=3)
        self.assertEqual(len(study.trials), 3)
        self.assertEqual(study.trials[0].params, {"rock.NOISE": 0.0})  # baseline
        study = self.tune([self.space_for("rock")], "t", trials=1)
        self.assertEqual(len(study.trials), 4)
        self.assertTrue(
            os.path.exists(os.path.join(self.dir.name, "tuning", "t", "trials.parquet"))
        )
        grid = self.tune([self.space_for("wsls")], "g", sampler="grid")
        self.assertEqual(len(grid.trials), 4)  # SHIFT 2 x NOISE 2
        self.setup = dataclasses.replace(self.setup, rounds=50)
        with self.assertRaises(SystemExit):  # different setup
            self.tune([self.space_for("rock")], "t", trials=1)

    def test_bots_tune_together_on_a_weighted_objective(self) -> None:
        spaces = [self.space_for("cycler"), self.space_for("wsls", weight=0.0)]
        study = self.tune(spaces, "fleet", trials=2)
        first = study.trials[0]
        self.assertEqual(
            first.params,
            {
                "cycler.STEP": 1,
                "cycler.NOISE": 0.05,
                "wsls.SHIFT": 1,
                "wsls.NOISE": 0.0,
            },
        )
        bots = first.user_attrs["bots"]
        self.assertEqual(set(bots), {"cycler", "wsls"})
        self.assertEqual(bots["cycler"]["n"], POOL + 1)  # the pool and wsls
        self.assertEqual(first.value, bots["cycler"]["score"])  # wsls weighs 0
        grid = self.tune(spaces, "fleet-grid", sampler="grid")
        sizes = [len(v) for v in grid_space(spaces).values()]
        self.assertEqual(len(sizes), 4)
        self.assertEqual(len(grid.trials), math.prod(sizes))  # every combination

    def test_split_params_and_baseline(self) -> None:
        spaces = [self.space_for("cycler"), self.space_for("wsls")]
        self.assertEqual(
            split_params({"cycler.STEP": 2, "wsls.NOISE": 0.1}, spaces),
            {"cycler": {"STEP": 2}, "wsls": {"NOISE": 0.1}},
        )
        self.assertEqual(baseline(spaces)["wsls.SHIFT"], 1)

    def test_a_study_needs_weight_and_distinct_bots(self) -> None:
        with self.assertRaises(SystemExit):
            self.tune([self.space_for("rock", weight=0.0)], "zero", trials=1)
        with self.assertRaises(ValueError):
            self.tune(
                [self.space_for("rock"), self.space_for("rock")], "twice", trials=1
            )

    def test_validation_replays_each_fleet_on_its_own(self) -> None:
        spaces = [self.space_for("cycler"), self.space_for("wsls", weight=0.0)]
        self.tune(spaces, "v", trials=2)
        study = self.tune(
            spaces, "v", trials=0, validate_top=1, validate_round_robins=1
        )
        self.assertEqual(len(study.trials), 2)  # validation only: no new trials
        stored = RunStore.at(self.dir.name)
        runs = stored.run_ids()
        self.assertEqual(len(runs), 2)  # the defaults, then the best trial
        for run in runs:
            _, manifest, _ = stored.load_run(run)
            self.assertEqual(len(manifest["candidates"]), 2)
            self.assertEqual(manifest["tuning"]["study"], "v")
        self.assertEqual(sorted(study.user_attrs["validations"][-1]["runs"]), runs)

    def test_validation_results_are_recorded(self) -> None:
        spaces = [self.space_for("cycler"), self.space_for("wsls", weight=0.0)]
        self.tune(spaces, "rec", trials=3, validate_top=2, validate_round_robins=1)
        rows = RunStore.at(self.dir.name).validations("tune_validations", "rec")
        self.assertGreaterEqual(rows.height, 2)
        first = rows.row(0, named=True)
        self.assertEqual(first["trial"], -1)  # the defaults come first
        self.assertTrue(first["champion"].startswith("cycler"))
        self.assertEqual(first["vs_defaults"], 0.0)
        self.assertEqual(first["n"], POOL)
        self.assertEqual(len(set(rows["run_id"])), rows.height)  # one run each
        text = analyze.render_validations("rec", self.dir.name)
        self.assertIn("vs defaults", text)


if __name__ == "__main__":
    unittest.main()
