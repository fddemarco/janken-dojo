"""The move dataset: metrics, predictors, the prediction kernel, storage, tuning, CLI."""

import contextlib
import io
import os
import pathlib
import shutil
from collections.abc import Callable
from typing import TypeVar

import numpy as np
import optuna
import pytest
from typer.testing import CliRunner

from janken.cli import app
from janken.engine import registry
from janken.kit import bot
from janken.kit.moves import INVALID, PAPER, ROCK, SCISSORS
from janken.lab import collect, dataset, metrics, predict, predict_tune, space
from janken.lab.predict_kernel import NO_PREDICTION, implied_prediction
from janken.lab.predictor import (
    PredictorError,
    core_of,
    knob_names,
    make_predictor,
    predictor_params,
)
from janken.lab.runs_db import RunStore
from janken.lab.tune import Search
from janken.match import MatchResult
from janken.spec import make_spec

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
BOTS_DIR = os.path.join(ROOT, "bots")
SPACES_DIR = os.path.join(ROOT, "spaces")
LIGHT_BOTS = ("rock", "cycler", "copycat", "frequency")
ROUNDS = 6
HOLDOUT = 0.3
T = TypeVar("T")


def bot_path(stem: str) -> str:
    return registry.find(BOTS_DIR, stem)


def quietly(fn: Callable[..., T], *args: object, **kwargs: object) -> T:
    with (
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        return fn(*args, **kwargs)


def sequences(p1: list[int], p2: list[int], seed: int = 1) -> dataset.Sequences:
    """One match between two hand-written move sequences."""
    return dataset.Sequences(
        match_ids=np.array([0], np.int64),
        seeds=np.array([seed], np.int64),
        starts=np.array([0, len(p1)], np.int64),
        p1=np.array(p1, np.int64),
        p2=np.array(p2, np.int64),
        p1_index=np.array([0], np.int64),
        p2_index=np.array([1], np.int64),
        labels=["a", "b"],
    )


class TestMetrics:
    def test_perfect_predictions(self) -> None:
        y = np.array([ROCK, PAPER, SCISSORS, ROCK])
        got = metrics.scores(y, y.copy())
        assert (got.n, got.abstained) == (4, 0)
        assert got.accuracy == pytest.approx(1.0, rel=0, abs=0.5e-7)
        assert got.macro_f1 == pytest.approx(1.0, rel=0, abs=0.5e-7)
        assert got.kappa == pytest.approx(1.0, rel=0, abs=0.5e-7)
        assert got.edge == pytest.approx(1.0, rel=0, abs=0.5e-7)

    def test_predicting_the_losing_side_has_negative_edge(self) -> None:
        y = np.array([ROCK, PAPER, SCISSORS])
        got = metrics.scores(y, (y + 1) % 3)  # we'd play (y + 2): it loses to y
        assert got.accuracy == pytest.approx(0.0, rel=0, abs=0.5e-7)
        assert got.edge == pytest.approx(-1.0, rel=0, abs=0.5e-7)
        assert got.kappa < 0.0

    def test_abstentions_are_misses_in_no_column(self) -> None:
        y = np.array([ROCK, ROCK, PAPER, PAPER])
        pred = np.array([ROCK, metrics.ABSTAIN, PAPER, metrics.ABSTAIN])
        got = metrics.scores(y, pred)
        assert got.abstained == 2
        assert got.accuracy == pytest.approx(0.5, rel=0, abs=0.5e-7)
        assert int(metrics.confusion(y, pred).sum()) == 2
        # rock and paper: precision 1, recall 1/2, F1 2/3; scissors never shows up
        assert got.macro_f1 == pytest.approx(2 / 3, rel=0, abs=0.5e-7)
        # true marginals (2, 2, 0) count the abstentions: chance agreement 1/4
        assert got.kappa == pytest.approx((0.5 - 0.25) / (1 - 0.25), rel=0, abs=0.5e-7)

    def test_a_perfect_guess_of_a_constant_player(self) -> None:
        got = metrics.scores(np.full(4, ROCK), np.full(4, ROCK))
        assert got.macro_f1 == pytest.approx(1.0, rel=0, abs=0.5e-7)
        assert got.kappa == pytest.approx(
            0.0, rel=0, abs=0.5e-7
        )  # nothing beyond the marginals

    def test_kappa_is_zero_for_a_constant_guess(self) -> None:
        y = np.array([ROCK, PAPER, SCISSORS, ROCK, PAPER, SCISSORS])
        got = metrics.scores(y, np.full(6, PAPER))
        assert got.accuracy == pytest.approx(1 / 3, rel=0, abs=0.5e-7)
        assert got.kappa == pytest.approx(0.0, rel=0, abs=0.5e-7)

    def test_metric_by_name_and_groups(self) -> None:
        y = np.array([ROCK, ROCK, PAPER])
        pred = np.array([ROCK, PAPER, PAPER])
        got = metrics.scores(y, pred)
        assert got.metric("accuracy") == got.accuracy
        with pytest.raises(ValueError):
            got.metric("auc")
        groups = metrics.by_group(y, pred, np.array([0, 0, 2]), ["x", "y", "z"])
        assert [name for name, _ in groups] == ["x", "z"]
        assert groups[0][1].accuracy == pytest.approx(0.5, rel=0, abs=0.5e-7)

    def test_bad_inputs_are_refused(self) -> None:
        with pytest.raises(ValueError):
            metrics.scores(np.array([ROCK]), np.array([ROCK, PAPER]))
        with pytest.raises(ValueError):
            metrics.scores(np.array([INVALID]), np.array([ROCK]))


class TestPredictor:
    def test_knob_names_walk_the_whole_blueprint(self) -> None:
        blueprint = bot.Blueprint(
            guards=(bot.Noise(bot.Knob("NOISE")),),
            core=bot.Bandit(predictors=(bot.Frequency(bot.OPP, bot.Knob("DECAY")),)),
        )
        assert knob_names(blueprint) == {"NOISE", "DECAY"}
        assert knob_names(core_of(blueprint)) == {"DECAY"}

    def test_guards_and_overlays_are_left_out(self) -> None:
        assert predictor_params(bot_path("frequency")) == ("DECAY",)
        assert predictor_params(bot_path("rock")) == ()
        predictor = make_predictor(make_spec(bot_path("frequency"), {"DECAY": 0.5}))
        assert predictor.params == ("DECAY",)
        assert predictor.prm[0] == 0.5

    def test_a_parameter_only_guards_read_is_refused(self) -> None:
        with pytest.raises(PredictorError, match="NOISE"):
            make_predictor(make_spec(bot_path("frequency"), {"NOISE": 0.1}))

    def test_a_kernel_module_is_not_a_predictor(self, tmp_path: pathlib.Path) -> None:
        d = str(tmp_path)
        path = os.path.join(d, "fixture.py")
        with open(path, "w") as f:
            f.write("STATE = (0, 0)\n")
        with pytest.raises(PredictorError):
            predictor_params(path)


class TestPredictionKernel:
    def test_a_move_implies_the_move_it_beats(self) -> None:
        assert implied_prediction(PAPER) == ROCK
        assert implied_prediction(ROCK) == SCISSORS
        assert implied_prediction(INVALID) == NO_PREDICTION

    def test_both_sides_are_predicted_from_the_past_only(self) -> None:
        seqs = sequences([ROCK] * 5, [SCISSORS] * 5)
        out = predict.predictions(
            make_predictor(make_spec(bot_path("frequency"))), seqs
        )
        assert out.shape == (2, 5)
        # From round 1 on, the most frequent move so far is the only one.
        assert out[0, 1:].tolist() == [ROCK] * 4
        assert out[1, 1:].tolist() == [SCISSORS] * 4

    def test_invalid_targets_are_not_scored(self) -> None:
        seqs = sequences([ROCK, INVALID, ROCK], [PAPER, PAPER, PAPER])
        truth = predict.targets(seqs)
        assert truth.y_true.tolist() == [ROCK, ROCK, PAPER, PAPER, PAPER]
        assert truth.player.tolist() == [0, 0, 1, 1, 1]

    def test_predictions_are_reproducible(self) -> None:
        seqs = sequences([ROCK, PAPER, SCISSORS] * 3, [PAPER] * 9, seed=5)
        nash = make_predictor(make_spec(bot_path("nash")))
        first = predict.predictions(nash, seqs)
        assert np.array_equal(first, predict.predictions(nash, seqs))

    def test_evaluate_scores_overall_and_per_player(self) -> None:
        seqs = sequences([ROCK] * 6, [PAPER] * 6)
        got = predict.evaluate(make_predictor(make_spec(bot_path("frequency"))), seqs)
        assert got.scores.n == 12
        assert got.scores.accuracy >= 10 / 12
        assert [name for name, _ in got.by_player] == ["a", "b"]
        assert "frequency" in predict.render([got], players=True)


class StoredDataset:
    """A dataset of round robins of LIGHT_BOTS in a temporary directory."""

    @pytest.fixture(autouse=True)
    def _dataset(self, tmp_path: pathlib.Path) -> None:
        self.dir = str(tmp_path)
        self.db = os.path.join(self.dir, "moves.duckdb")
        self.specs = [make_spec(bot_path(stem)) for stem in LIGHT_BOTS]

    def grow(self, seed: int, matches: int = 1) -> range:
        return quietly(collect.grow, self.db, self.specs, ROUNDS, matches, seed, 0)

    def read(self) -> dataset.Sequences:
        con = dataset.connect(self.db, read_only=True)
        try:
            return dataset.load(con, "all", HOLDOUT, dataset.last_match_id(con))
        finally:
            con.close()


class TestDataset(StoredDataset):
    def test_a_batch_stores_every_match_and_round(self) -> None:
        ids = self.grow(seed=3, matches=2)
        assert ids == range(12)  # 6 pairs x 2
        con = dataset.connect(self.db, read_only=True)
        try:
            info = dataset.summary(con, HOLDOUT)
            row = con.execute(
                "SELECT rounds, p1_stem, p2_stem, p1_params FROM matches"
                " WHERE match_id = 0"
            ).fetchone()
        finally:
            con.close()
        assert (info["matches"], info["rounds"]) == (12, 12 * ROUNDS)
        assert row == (ROUNDS, "rock", "cycler", '{"NOISE": 0.0}')

    def test_a_chunked_batch_equals_one_transaction(self) -> None:
        chunked = os.path.join(self.dir, "chunked.duckdb")
        args = (self.specs, ROUNDS, 2, 3, 0)
        assert quietly(collect.grow, chunked, *args, chunk=5) == range(12)
        assert quietly(collect.grow, self.db, *args, chunk=1000) == range(12)
        query = (
            "SELECT match_id, batch_id, seed, holdout_key, p1_label, p2_label,"
            " p1_wins, p2_wins FROM matches ORDER BY match_id"
        )
        rows = []
        for path in (chunked, self.db):
            con = dataset.connect(path, read_only=True)
            try:
                rows.append(con.execute(query).fetchall())
            finally:
                con.close()
        assert rows[0] == rows[1]
        assert {r[1] for r in rows[0]} == {0}  # one batch id

    def test_appending_never_changes_stored_matches(self) -> None:
        self.grow(seed=3)
        before = self.read()
        assert self.grow(seed=4) == range(6, 12)
        after = self.read()
        assert after.n_matches == 12
        stored = after.take(0, before.n_matches)
        assert np.array_equal(stored.p1, before.p1)
        assert np.array_equal(stored.p2, before.p2)
        assert np.array_equal(stored.starts, before.starts)

    def test_stored_moves_are_the_played_moves(self) -> None:
        batch = quietly(collect.play_batch, self.specs[:2], ROUNDS, 1, 9, 0, ["t"])
        con = dataset.connect(self.db, read_only=False)
        try:
            dataset.append(con, batch)
        finally:
            con.close()
        moves = dataset.decode_moves(batch.matches[0].result.moves)
        seqs = self.read()
        assert seqs.p1.tolist() == moves[:, 0].tolist()
        assert seqs.p2.tolist() == moves[:, 1].tolist()

    def test_splits_partition_the_matches(self) -> None:
        self.grow(seed=3, matches=3)
        con = dataset.connect(self.db, read_only=True)
        try:
            upto = dataset.last_match_id(con)
            sizes = {
                s: dataset.load(con, s, HOLDOUT, upto).n_matches
                for s in ("train", "test", "all")
            }
        finally:
            con.close()
        assert sizes["train"] + sizes["test"] == sizes["all"]

    def test_a_snapshot_ignores_newer_matches(self) -> None:
        self.grow(seed=3)
        self.grow(seed=4)
        con = dataset.connect(self.db, read_only=True)
        try:
            assert dataset.load(con, "all", HOLDOUT, 5).n_matches == 6
        finally:
            con.close()

    def test_a_failed_append_stores_nothing(self) -> None:
        self.grow(seed=3)
        batch = quietly(collect.play_batch, self.specs[:2], ROUNDS, 1, 9, 0, ["t"])
        broken = MatchResult(bot_a="a", bot_b="b", moves="rq")
        bad = dataset.Batch(
            matches=[
                batch.matches[0],
                dataset.PlayedMatch(self.specs[0], self.specs[1], 1, 0.5, broken),
            ],
            rounds=ROUNDS,
            seed=9,
            library="x",
            git=dataset.GitInfo("", False),
            command=["t"],
            played_at=batch.played_at,
        )
        con = dataset.connect(self.db, read_only=False)
        try:
            with pytest.raises(ValueError):
                dataset.append(con, bad)
            assert dataset.last_match_id(con) == 5
        finally:
            con.close()

    def test_players_and_a_missing_dataset(self) -> None:
        self.grow(seed=3)
        con = dataset.connect(self.db, read_only=True)
        try:
            rows = dataset.players(con)
        finally:
            con.close()
        assert sorted(r[0] for r in rows) == sorted(LIGHT_BOTS)
        assert all(r[1] == 3 and r[2] == 3 * ROUNDS for r in rows)
        with pytest.raises(SystemExit):
            dataset.connect(os.path.join(self.dir, "none.duckdb"), read_only=True)

    def test_expand_reads_directories_and_specs(self, tmp_path: pathlib.Path) -> None:
        d = str(tmp_path)
        for stem in ("rock", "cycler"):
            shutil.copy(bot_path(stem), d)
        specs = collect.expand([d, os.path.join(d, "cycler.yaml") + ":STEP=2"])
        assert [s.stem for s in specs] == ["cycler", "rock", "cycler"]
        assert specs[2].params == {"STEP": 2}


class TestPredictTune(StoredDataset):
    @pytest.fixture(autouse=True)
    def _grown(self, _dataset: None) -> None:
        self.grow(seed=3, matches=3)
        self.spaces = [
            space.load(os.path.join(SPACES_DIR, f"{stem}.yaml"))
            for stem in ("frequency", "transition_matrix")
        ]
        self.setup = predict_tune.Setup(
            db=self.db, metric="accuracy", holdout=HOLDOUT, chunks=2, root=self.dir
        )

    def tune(self, name: str, setup: predict_tune.Setup) -> optuna.Study:
        search = Search(trials=3, sampler_seed=1, validate_top=1)
        return quietly(predict_tune.run_predict_tune, self.spaces, name, setup, search)

    def test_automl_picks_a_predictor_then_its_params(self) -> None:
        study = self.tune("automl", self.setup)
        assert len(study.trials) == 3
        first = study.trials[0].params  # the baselines run first
        assert first[predict_tune.PREDICTOR] == "frequency"
        assert "frequency.NOISE" not in first  # a guard's param is dropped
        assert predict_tune.spec_of(first, self.spaces).label == "frequency"
        assert all(t.value is not None for t in study.trials)

    def test_a_study_resumes_only_under_its_setup(self) -> None:
        self.tune("resume", self.setup)
        self.grow(seed=4)  # newer matches stay out of the study's snapshot
        study = self.tune("resume", self.setup)
        assert study.user_attrs["upto_match_id"] == 17
        kappa = predict_tune.Setup(
            db=self.db, metric="kappa", holdout=HOLDOUT, chunks=2, root=self.dir
        )
        with pytest.raises(SystemExit):
            self.tune("resume", kappa)

    def test_validation_scores_are_recorded(self) -> None:
        study = self.tune("validated", self.setup)
        rows = RunStore.at(self.dir).validations("predict_validations", "validated")
        defaults = rows.filter(rows["trial"] == -1)
        assert sorted(defaults["config"]) == ["frequency", "transition_matrix"]
        assert (rows["split"] == "test").all()
        assert ((rows["accuracy"] >= 0) & (rows["accuracy"] <= 1)).all()
        assert len(study.user_attrs["validations"]) == 1

    def test_chunks_cover_every_match_once(self) -> None:
        seqs = self.read()
        parts = predict_tune.chunks_of(seqs, 4)
        assert sum(c.seqs.n_matches for c in parts) == seqs.n_matches
        assert sum(c.seqs.n_rounds for c in parts) == seqs.n_rounds


class TestCli(StoredDataset):
    def test_dataset_add_info_and_predict(self) -> None:
        runner = CliRunner()
        args = ["--workspace", self.dir, "--cache", "off"]
        outputs = []
        for command in (
            ["lab", "dataset", "add", bot_path("rock"), bot_path("cycler")]
            + ["--rounds", "5", "--seed", "1"],
            ["lab", "dataset", "info", "--players"],
            ["lab", "predict", bot_path("frequency"), "--split", "all"],
        ):
            result = runner.invoke(app, [*command, *args])
            assert result.exit_code == 0, result.output
            outputs.append(result.output)
        text = "".join(outputs)
        assert "appended 1 matches" in text
        assert "| cycler | 1 | 5 | 0 |" in text
        assert "| frequency | 10 |" in text
