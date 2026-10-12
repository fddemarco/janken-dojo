"""Tune predictors on the move dataset with Optuna: hyperparameters, or AutoML.

    uv run janken lab predict-tune spaces/x.yaml --study x-pred-v1
    uv run janken lab predict-tune spaces/x.yaml spaces/y.yaml ... --study automl-v1

* One space file: its bot's core is tuned over the space's params.
* Several: AutoML. Each trial first picks the predictor (Optuna's `predictor`
  parameter, one of the bots' stems), then that bot's params (`<stem>.<NAME>`):
  a conditional search space, which TPE's grouped multivariate mode handles.
* A space param that only feeds the bot's guards or overlays can't change a
  prediction (predictor.py), so it is dropped, with a note.
* Objective: the configured metric (`[tool.janken.dataset] metric`) on the train
  split. A trial is scored in `chunks` steps, each a slice of the matches, and
  reports its running value after each, so the median pruner can stop it early.
* Common random numbers: every trial replays the same matches, each match side
  seeded from the match's seed.
* Snapshot: the dataset only ever grows, so a study pins the newest match id it
  saw when it was created and never reads past it: a resumed study keeps scoring
  the same matches. Start a new study to use newer data.
* Overfitting check: `--validate-top K` scores the K best trials and every
  predictor's defaults on the test split (the same snapshot), and records the
  scores in the runs database's `predict_validations` table.
* Storage: SQLite under experiments/tuning/predict/, so a study resumes and
  takes parallel workers.
"""

import dataclasses
import datetime
import itertools
import json
import math
import os
import sys
import time
from collections.abc import Mapping, Sequence

import numpy as np
import optuna

from .. import botfile, progress
from ..spec import BotSpec, format_spec, make_spec
from . import dataset, metrics, store
from .predict import SCORE_HEADERS, Targets, predictions, score_row, table, targets
from .predictor import make_predictor, predictor_params
from .runs_db import RunStore
from .space import Number, Space, check_unique_stems
from .tune import (
    Search,
    TrialProgress,
    make_sampler,
    param_key,
    params_text,
    suggest_param,
    timed_trial,
)

PREDICTOR = "predictor"  # Optuna's name for the AutoML choice of predictor


@dataclasses.dataclass(frozen=True)
class Setup:
    """What every trial of a study is scored on."""

    db: str
    metric: str
    holdout: float
    chunks: int
    split: str = "train"
    root: str = ""  # "": the default experiments directory


@dataclasses.dataclass(frozen=True)
class Chunk:
    """A slice of the matches, with its true moves."""

    seqs: dataset.Sequences
    truth: Targets


def predictor_space(space: Space) -> Space:
    """`space` with only the params the bot's core reads (the rest noted)."""
    used = set(predictor_params(space.bot))
    dropped = [name for name in space.params if name not in used]
    if dropped:
        print(
            f"note: {space.stem}: {', '.join(dropped)} only feed guards or overlays;"
            " a predictor ignores them",
            file=sys.stderr,
        )
    params = {k: v for k, v in space.params.items() if k in used}
    return dataclasses.replace(space, params=params)


def suggest(trial: optuna.Trial, spaces: Sequence[Space]) -> BotSpec:
    """The trial's predictor (picked among `spaces` when there are several) and
    its parameters."""
    chosen = spaces[0]
    if len(spaces) > 1:
        stem = trial.suggest_categorical(PREDICTOR, [s.stem for s in spaces])
        chosen = next(s for s in spaces if s.stem == stem)
    params = {
        name: suggest_param(trial, param_key(chosen.stem, name), p)
        for name, p in chosen.params.items()
    }
    return spec_at(chosen, params)


def spec_at(space: Space, params: Mapping[str, Number]) -> BotSpec:
    """The bot of `space` at `params`; a value equal to the bot's default is no
    override, so a configuration has one label however it was reached."""
    defaults = botfile.defaults(space.bot)
    return make_spec(
        space.bot, {k: v for k, v in params.items() if v != defaults.get(k)}
    )


def spec_of(params: Mapping[str, object], spaces: Sequence[Space]) -> BotSpec:
    """The predictor a finished trial's `params` describe."""
    stem = params.get(PREDICTOR, spaces[0].stem)
    chosen = next(s for s in spaces if s.stem == stem)
    prefix = param_key(chosen.stem, "")
    values = {
        key[len(prefix) :]: value
        for key, value in params.items()
        if key.startswith(prefix) and isinstance(value, int | float)
    }
    return spec_at(chosen, values)


def baselines(spaces: Sequence[Space]) -> list[dict[str, object]]:
    """Every predictor at its defaults, one trial each."""
    out: list[dict[str, object]] = []
    for s in spaces:
        trial: dict[str, object] = {PREDICTOR: s.stem} if len(spaces) > 1 else {}
        trial.update({param_key(s.stem, k): v for k, v in s.defaults().items()})
        out.append(trial)
    return out


def chunks_of(seqs: dataset.Sequences, count: int) -> list[Chunk]:
    """The matches in `count` (or fewer) near-equal, non-empty slices."""
    steps = min(count, seqs.n_matches)
    edges = [seqs.n_matches * k // steps for k in range(steps + 1)]
    parts = [seqs.take(a, b) for a, b in itertools.pairwise(edges)]
    return [Chunk(seqs=p, truth=targets(p)) for p in parts]


def scores_on(spec: BotSpec, chunks: Sequence[Chunk]) -> metrics.Scores:
    """A predictor's scores over every chunk."""
    predictor = make_predictor(spec)
    y_true = [c.truth.y_true for c in chunks]
    y_pred = [predictions(predictor, c.seqs).reshape(-1)[c.truth.keep] for c in chunks]
    return metrics.scores(np.concatenate(y_true), np.concatenate(y_pred))


def study_config(spaces: Sequence[Space], setup: Setup) -> dict[str, object]:
    return {
        "spaces": [s.to_data() for s in spaces],
        "dataset": os.path.abspath(setup.db),
        "split": setup.split,
        "holdout": setup.holdout,
        "metric": setup.metric,
        "chunks": setup.chunks,
    }


def _open_study(
    spaces: Sequence[Space], setup: Setup, search: Search, study_name: str
) -> tuple[optuna.Study, int]:
    """Create or resume the study; returns it and its dataset snapshot (the last
    match id it reads)."""
    folder = os.path.join(store.tuning_dir(setup.root or None), "predict")
    os.makedirs(folder, exist_ok=True)
    storage = "sqlite:///{}".format(os.path.join(folder, f"{study_name}.db"))
    if search.sampler == "grid" and len(spaces) > 1:
        raise SystemExit("--sampler grid tunes one predictor; give one space file")
    study = optuna.create_study(
        study_name=study_name,
        storage=storage,
        direction="maximize",
        load_if_exists=True,
        sampler=make_sampler(search.sampler, spaces, search.sampler_seed),
        pruner=(
            optuna.pruners.MedianPruner(n_startup_trials=8, n_warmup_steps=1)
            if search.prune and setup.chunks >= 2
            else optuna.pruners.NopPruner()
        ),
    )
    config = study_config(spaces, setup)
    stored = study.user_attrs.get("config")
    if stored is None:
        con = dataset.connect(setup.db, read_only=True)
        try:
            upto = dataset.last_match_id(con)
        finally:
            con.close()
        study.set_user_attr("config", config)
        study.set_user_attr("upto_match_id", upto)
        if search.sampler != "grid":
            for trial in baselines(spaces):
                study.enqueue_trial(trial)
    elif stored != json.loads(json.dumps(config)):
        raise SystemExit(
            f"study {study_name!r} was created with a different setup:\n"
            f"  stored  {json.dumps(stored)}\n  now     {json.dumps(config)}\n"
            "use a new --study name"
        )
    return study, int(study.user_attrs["upto_match_id"])


def load_chunks(setup: Setup, split: str, upto: int) -> list[Chunk]:
    con = dataset.connect(setup.db, read_only=True)
    try:
        seqs = dataset.load(con, split, setup.holdout, upto)
    finally:
        con.close()
    if not seqs.n_matches:
        raise SystemExit(f"the {split} split of {setup.db} holds no matches")
    return chunks_of(seqs, setup.chunks)


def run_predict_tune(
    spaces: Sequence[Space], study_name: str, setup: Setup, search: Search
) -> optuna.Study:
    """Tune the predictors of `spaces` (AutoML across them when several)."""
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    check_unique_stems(spaces)
    spaces = [predictor_space(s) for s in spaces]
    if len(spaces) == 1 and not spaces[0].params:
        raise SystemExit("the space declares no param a predictor reads")
    study, upto = _open_study(spaces, setup, search, study_name)
    chunks = load_chunks(setup, setup.split, upto)
    n = sum(c.seqs.n_matches for c in chunks)
    print(
        f"tuning {' | '.join(s.stem for s in spaces)} on {setup.metric}: {n}"
        f" {setup.split} matches (ids <= {upto}), {len(chunks)} step(s) per trial;"
        f" study {study_name}",
        file=sys.stderr,
    )

    def objective(trial: optuna.Trial) -> float:
        spec = suggest(trial, spaces)
        predictor = make_predictor(spec)
        y_true: list[np.ndarray] = []
        y_pred: list[np.ndarray] = []
        got = metrics.scores(np.zeros(0, np.int64), np.zeros(0, np.int64))
        for step, chunk in enumerate(chunks):
            y_true.append(chunk.truth.y_true)
            y_pred.append(
                predictions(predictor, chunk.seqs).reshape(-1)[chunk.truth.keep]
            )
            got = metrics.scores(np.concatenate(y_true), np.concatenate(y_pred))
            trial.report(got.metric(setup.metric), step)
            if trial.should_prune():
                raise optuna.TrialPruned()
        trial.set_user_attr("scores", dataclasses.asdict(got))
        trial.set_user_attr("label", spec.label)
        return got.metric(setup.metric)

    n_trials = search.trials if search.trials >= 0 else None
    started = time.perf_counter()
    with progress.bar(n_trials or 0, "trials", "trial") as bar:
        try:
            study.optimize(
                timed_trial("predict_tune.trial", objective),
                n_trials=n_trials,
                timeout=search.timeout or None,
                callbacks=[TrialProgress(bar, lambda v: f"{v:.4f}")],
                gc_after_trial=False,
            )
        except (KeyboardInterrupt, SystemError) as exc:
            if not progress.interrupted(exc):
                raise
            progress.log("interrupted; the study keeps every finished trial")
    print(
        f"\n{len(study.trials)} trials in {time.perf_counter() - started:.0f}s"
        " this session"
    )
    report(study, spaces, setup.metric)
    if search.validate_top:
        validate(study, spaces, setup, search.validate_top, upto)
    return study


def top_trials(study: optuna.Study, k: int) -> list[optuna.trial.FrozenTrial]:
    done = [
        t
        for t in study.trials
        if t.state == optuna.trial.TrialState.COMPLETE and t.value is not None
    ]
    return sorted(done, key=lambda t: t.value or 0.0, reverse=True)[:k]


def report(study: optuna.Study, spaces: Sequence[Space], metric: str) -> None:
    best = top_trials(study, 10)
    if not best:
        print("no completed trials yet")
        return
    rows = [
        [str(t.number), f"{t.value or 0.0:.4f}", params_text(t.params)] for t in best
    ]
    print(table(["trial", metric, "params"], rows))
    spec = spec_of(best[0].params, spaces)
    print(
        f"\nbest: {spec.label}\n"
        f"  uv run janken lab predict {json.dumps(format_spec(spec))} --split test"
    )


def validate(
    study: optuna.Study,
    spaces: Sequence[Space],
    setup: Setup,
    k: int,
    upto: int,
) -> None:
    """Score the defaults and the `k` best trials on the test split, and record
    the scores (`predict_validations`)."""
    chunks = load_chunks(setup, "test", upto)
    configs: dict[str, tuple[str, BotSpec]] = {}
    origins: dict[str, tuple[int, float]] = {}  # label -> (trial, train value)
    for s in spaces:
        spec = make_spec(s.bot)
        configs.setdefault(spec.label, ("defaults", spec))
        origins.setdefault(spec.label, (-1, math.nan))
    for t in top_trials(study, k):
        spec = spec_of(t.params, spaces)
        configs.setdefault(spec.label, (f"#{t.number} ({t.value or 0.0:.4f})", spec))
        origins.setdefault(spec.label, (t.number, t.value or 0.0))
    print(
        f"\nvalidating on the test split"
        f" ({sum(c.seqs.n_matches for c in chunks)} matches):\n"
    )
    scored = [
        (origin, spec, scores_on(spec, chunks)) for origin, spec in configs.values()
    ]
    scored.sort(key=lambda x: x[2].metric(setup.metric), reverse=True)
    rows = [[origin] + score_row(spec.label, got) for origin, spec, got in scored]
    print(table(["trial (train)"] + SCORE_HEADERS, rows))
    study_name = study.study_name
    RunStore.at(setup.root).add_validations(
        "predict_validations",
        [
            {
                "study": study_name,
                "config": spec.label,
                "trial": origins[spec.label][0],
                "train_value": float(origins[spec.label][1]),
                "metric": setup.metric,
                "split": "test",
                "upto_match_id": upto,
                "n": got.n,
                "accuracy": got.accuracy,
                "macro_f1": got.macro_f1,
                "kappa": got.kappa,
                "edge": got.edge,
            }
            for _, spec, got in scored
        ],
    )
    history = list(study.user_attrs.get("validations", []))
    history.append({"at": datetime.datetime.now().isoformat(timespec="seconds")})
    study.set_user_attr("validations", history)
    print("\n(recorded in predict_validations)")
