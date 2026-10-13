"""`janken lab ...`: the low level, for ad hoc runs, queries and reports.

None of these touch the research notebook; the high-level commands do that. The lab
modules are imported inside each command, after the common flags settled caching
(numba reads it when the engine is first imported).
"""

import dataclasses
import os
import random
from typing import Annotated

import typer

from .. import settings
from . import gauntlet, profile
from .options import (
    CFG,
    METRIC,
    MODE,
    SAMPLER,
    SPLIT,
    TUNE_SPLIT,
    Db,
    Lab,
    Metric,
    Mode,
    Sampler,
    Split,
    about,
    bot_path,
    budget_help,
    fail,
    lab_command,
    shown,
)

app = typer.Typer(
    help="Low level: ad hoc experiments, studies, queries and reports (no notebook).",
    no_args_is_help=True,
)
study_app = typer.Typer(
    help="Tuning studies (Optuna), without a note.", no_args_is_help=True
)
dataset_app = typer.Typer(
    help="The move dataset (DuckDB, append-only).", no_args_is_help=True
)
app.add_typer(study_app, name="study")
app.add_typer(dataset_app, name="dataset")
app.add_typer(profile.app, name="profile")
app.add_typer(gauntlet.app, name="gauntlet")

QUERY_DB = Db(CFG.query.db)
SPEC_HELP = "bot files, optionally with overrides: bots/l1/x.yaml:NAME=value,NAME=value"


def _seed(seed: int) -> int:
    return (
        random.SystemRandom().getrandbits(32) if seed == settings.RANDOM_SEED else seed
    )


def _specs(texts: list[str]) -> list:
    from ..lab.workflows import specs

    return specs(texts)


def _dataset_file(lab: Lab) -> str:
    return os.path.join(lab.workspace, CFG.dataset.file)


# --- experiments and reports -------------------------------------------------


@app.command()
@lab_command("lab experiment")
def experiment(
    lab: Lab,
    candidates: Annotated[list[str], typer.Argument(help=SPEC_HELP)],
    mode: Annotated[Mode, typer.Option(help=about("evaluation.mode"))] = MODE,
    name: Annotated[
        str,
        typer.Option(help="the run's name, appended to its id (default: the labels)"),
    ] = "",
) -> None:
    """Play candidates against fresh random pools and store the run."""
    from ..lab import analyze
    from ..lab.experiment import run_experiment

    run_id = run_experiment(
        _specs(candidates),
        bots_dir=lab.bots_dir,
        pool_size=lab.pool_size,
        rounds=lab.rounds,
        round_robins=lab.round_robins,
        seed=lab.seed,
        mode=str(mode),
        name=name or None,
        workers=lab.workers or None,
        allow_small=lab.allow_small,
        use_mocks=lab.use_mocks,
        root=lab.workspace,
    )
    summary = analyze.analyze_run(run_id, lab.workspace)
    lab.emit(summary, analyze.render(summary))
    print(f"run id: {run_id}")


@app.command()
@lab_command("lab resume")
def resume(
    lab: Lab,
    run: Annotated[
        str, typer.Argument(help="a run id, a unique part of one, or latest")
    ],
) -> None:
    """Play the round robins an interrupted run is missing."""
    from ..lab import analyze
    from ..lab.experiment import resume_experiment

    try:
        run_id = resume_experiment(run, lab.workspace, lab.workers or None)
    except ValueError as exc:  # a candidate's bot file is gone
        raise fail(str(exc)) from None
    summary = analyze.analyze_run(run_id, lab.workspace)
    lab.emit(summary, analyze.render(summary))
    print(f"run id: {run_id}")


@app.command()
@lab_command("lab report")
def report(
    lab: Lab,
    runs: Annotated[
        list[str], typer.Argument(help="run ids, unique parts of them, or latest")
    ],
) -> None:
    """Analyze stored runs (finished or not) and print their reports."""
    from ..lab import analyze

    for ref in runs:
        summary = analyze.analyze_run(ref, lab.workspace)
        lab.emit(summary, analyze.render(summary))


@app.command("runs")
@lab_command("lab runs")
def list_runs(lab: Lab) -> None:
    """List every stored run, with its status."""
    from ..lab import analyze

    frame = analyze.list_runs(lab.workspace)
    lab.emit(frame.to_dicts(), analyze.render_runs(frame))


@app.command()
@lab_command("lab history")
def history(
    lab: Lab,
    stem: Annotated[str, typer.Argument(help="a bot's stem; its variants count too")],
) -> None:
    """A bot's score vs the pool in every stored run."""
    from ..lab import analyze

    frame = analyze.history(stem, lab.workspace)
    lab.emit(frame.to_dicts(), analyze.render_frame(frame))


@app.command()
@lab_command("lab leaderboard")
def leaderboard(lab: Lab) -> None:
    """Every candidate ever tested, pooled over runs (only runs of --rounds, if given)."""
    from ..lab import analyze

    frame = analyze.leaderboard(lab.workspace, lab.given("rounds", 0))
    lab.emit(frame.to_dicts(), analyze.render_frame(frame))


@app.command()
@lab_command("lab match")
def match(
    lab: Lab,
    a: Annotated[str, typer.Argument(help="the first bot: " + SPEC_HELP)],
    b: Annotated[str, typer.Argument(help="the second bot")],
) -> None:
    """Play one match and print its transcript (nothing is stored)."""
    from ..engine import play_pairs
    from ..report import describe_match

    first, second = _specs([a, b])
    seed = _seed(lab.seed)
    (result,) = play_pairs([(first, second)], lab.rounds, [seed], lab.workers or None)
    data = {"seed": seed, **result.__dict__}
    lab.emit(data, f"{describe_match(result)}  (seed {seed})\n{result.moves}")


@app.command()
@lab_command("lab calibrate")
def calibrate(
    lab: Lab,
    bot: Annotated[
        str,
        typer.Argument(help="the bot a pure Oracle stands in for: a stem or a path"),
    ],
    seeds: Annotated[
        int, typer.Option(help=about("calibration.seeds"))
    ] = CFG.calibration.seeds,
) -> None:
    """Measure a bot's win chance per opponent level: its pure Oracle's `wins`."""
    from ..kit import levels
    from ..lab.calibrate import calibrate as measure
    from ..lab.calibrate import level_wins

    path = bot_path(lab, bot)
    if not os.path.isfile(path):
        raise fail(f"no bot file {path}")
    rows = measure(path, lab.bots_dir, lab.rounds, seeds, _seed(lab.seed), lab.workers)
    means = level_wins(rows)
    lines = ["| opponent | level | win | tie | loss |", "|---|---|---|---|---|"]
    lines += [
        f"| {stem} | {levels.name(r.level)} | {r.win:.1%} | {r.tie:.1%} | {r.loss:.1%} |"
        for stem, r in sorted(rows.items(), key=lambda kv: (kv[1].level, kv[0]))
    ]
    wins = ", ".join(f"{levels.name(lv)} {w:.4f}" for lv, w in means.items())
    lab.emit(
        {
            "wins": {levels.name(lv): w for lv, w in means.items()},
            "opponents": {k: dataclasses.asdict(v) for k, v in rows.items()},
        },
        "\n".join([*lines, "", f"win chance per level: {wins}"]),
    )


@app.command()
@lab_command("lab query")
def query(
    lab: Lab,
    sql: Annotated[
        str, typer.Argument(help="a read-only SELECT over the database's tables")
    ],
    db: Annotated[Db, typer.Option(help=about("query.db"))] = QUERY_DB,
    limit: Annotated[int, typer.Option(help=about("query.limit"))] = CFG.query.limit,
) -> None:
    """Run read-only SQL against the runs database or the move dataset.

    Tables: runs, matches, reports, tune_validations, predict_validations (runs);
    matches, rounds (dataset).
    """
    import duckdb

    from ..lab import analyze, duck
    from ..lab.runs_db import RunStore

    path = RunStore.at(lab.workspace).path if db == "runs" else _dataset_file(lab)
    if not os.path.isfile(path):
        raise fail(f"no database at {path}")
    con = duckdb.connect(path, read_only=True)
    try:
        frame = duck.fetch_frame(con, sql)
    except duckdb.Error as exc:
        raise fail(str(exc)) from None
    finally:
        con.close()
    lab.emit(frame.head(limit).to_dicts(), analyze.render_frame(frame.head(limit)))
    if frame.height > limit:
        lab.say(f"({frame.height - limit} more rows; raise --limit)")


@app.command()
@lab_command("lab space")
def space(
    lab: Lab,
    bots: Annotated[
        list[str], typer.Argument(help="bot files (bots/l1/x.yaml) to tune")
    ],
    weight: Annotated[float, typer.Option(help=about("space.weight"))] = (
        CFG.space.weight
    ),
    force: Annotated[bool, typer.Option(help="overwrite existing space files")] = False,
) -> None:
    """Scaffold a space file for each bot from its defaults, to edit before tuning."""
    from ..lab import space as spaces

    written = [
        spaces.write(spaces.scaffold(path, weight, CFG.space), lab.spaces_dir, force)
        for path in bots
    ]
    for path in written:
        lab.say(f"wrote {shown(path)}")


# --- studies -------------------------------------------------------------------

STUDY_HELP = "the study's name (an existing one resumes)"


def search_options(
    lab: Lab, trials: int, validate_top: int, validate_round_robins: int
):
    """The budget flags of a study, resolved against the effort."""
    return (
        lab.pick("trials", trials, "trials"),
        lab.pick("validate_top", validate_top, "validate_top"),
        lab.pick(
            "validate_round_robins", validate_round_robins, "validate_round_robins"
        ),
    )


@study_app.command("run")
@lab_command("lab study run")
def study_run(
    lab: Lab,
    spaces: Annotated[
        list[str],
        typer.Argument(help="space files (spaces/x.yaml); several tune together"),
    ],
    study: Annotated[str, typer.Option(help=STUDY_HELP)],
    trials: Annotated[
        int, typer.Option(help=budget_help("trials this session", "trials"))
    ] = (CFG.effort.budget(CFG.effort.default).trials),
    validate_top: Annotated[
        int,
        typer.Option(
            help=budget_help("best trials replayed on fresh pools", "validate_top")
        ),
    ] = CFG.effort.budget(CFG.effort.default).validate_top,
    validate_round_robins: Annotated[
        int,
        typer.Option(
            help=budget_help("pools each validation plays", "validate_round_robins")
        ),
    ] = CFG.effort.budget(CFG.effort.default).validate_round_robins,
    sampler: Annotated[Sampler, typer.Option(help=about("tuning.sampler"))] = SAMPLER,
    sampler_seed: Annotated[int, typer.Option(help=about("tuning.sampler_seed"))] = (
        CFG.tuning.sampler_seed
    ),
    prune: Annotated[bool, typer.Option(help=about("tuning.prune"))] = CFG.tuning.prune,
    timeout: Annotated[float, typer.Option(help=about("tuning.timeout_s"))] = (
        CFG.tuning.timeout_s
    ),
) -> None:
    """Tune one or more bots' spaces with Optuna (a fleet: weights 1 and 0)."""
    from ..lab import space as spaces_mod
    from ..lab.tune import Search, Setup, run_tune

    n_trials, top, validate_rr = search_options(
        lab, trials, validate_top, validate_round_robins
    )
    run_tune(
        [spaces_mod.load(p) for p in spaces],
        study,
        Setup(
            rounds=lab.rounds,
            round_robins=lab.pick(
                "round_robins", lab.raw["round_robins"], "tune_round_robins"
            ),
            pool_size=lab.pool_size,
            seed=lab.given("seed", CFG.tuning.seed),
            bots_dir=lab.bots_dir,
            workers=lab.workers,
            allow_small=lab.allow_small,
            use_mocks=lab.use_mocks,
            root=lab.workspace,
        ),
        Search(
            sampler=str(sampler),
            sampler_seed=sampler_seed,
            trials=-1 if sampler == "grid" and "trials" not in lab.passed else n_trials,
            timeout=timeout,
            prune=prune,
            validate_top=top,
            validate_round_robins=validate_rr,
        ),
    )


@study_app.command("show")
@lab_command("lab study show")
def study_show(
    lab: Lab, study: Annotated[str, typer.Argument(help="a study's name")]
) -> None:
    """A study's recorded validation results (tune and predict-tune)."""
    from ..lab import analyze
    from ..lab.runs_db import RunStore

    runs = RunStore.at(lab.workspace)
    data = {
        t: runs.validations(t, study).to_dicts()
        for t in ("tune_validations", "predict_validations")
    }
    lab.emit(data, analyze.render_validations(study, lab.workspace))


@study_app.command("list")
@lab_command("lab study list")
def study_list(lab: Lab) -> None:
    """The tuning studies in the workspace."""
    found = []
    for sub in ("", "predict"):
        folder = os.path.join(lab.workspace, "tuning", sub)
        if os.path.isdir(folder):
            found += [
                (sub or "tune") + ": " + f[:-3]
                for f in sorted(os.listdir(folder))
                if f.endswith(".db")
            ]
    lab.emit(found, "\n".join(found) or "(no studies yet)")


# --- the move dataset ---------------------------------------------------------------


@dataset_app.command("add")
@lab_command("lab dataset add")
def dataset_add(
    lab: Lab,
    bots: Annotated[
        list[str], typer.Argument(help="bot directories and/or " + SPEC_HELP)
    ],
    matches: Annotated[int, typer.Option(help=about("dataset.matches"))] = (
        CFG.dataset.matches
    ),
) -> None:
    """Play a round robin of the bots and append every round to the dataset."""
    from ..lab.collect import expand, grow

    try:
        found = expand(bots)
    except ValueError as exc:
        raise fail(str(exc)) from None
    if len(found) < 2:
        raise fail(f"a round robin needs at least 2 bots, got {len(found)}")
    seed = _seed(lab.given("seed", CFG.dataset.seed))
    ids = grow(_dataset_file(lab), found, lab.rounds, matches, seed, lab.workers)
    lab.emit(
        {"first": ids.start, "stop": ids.stop},
        f"appended {len(ids)} matches (ids {ids.start}..{ids.stop - 1})",
    )
    _print_dataset(lab, players=False)


@dataset_app.command("info")
@lab_command("lab dataset info")
def dataset_info(
    lab: Lab,
    players: Annotated[bool, typer.Option(help="also list every player")] = False,
) -> None:
    """Summarise the dataset: matches, rounds, batches, the test split."""
    _print_dataset(lab, players)


def _print_dataset(lab: Lab, players: bool) -> None:
    from ..lab import dataset
    from ..lab.predict import table

    path = _dataset_file(lab)
    con = dataset.connect(path, read_only=True)
    try:
        info = dataset.summary(con, CFG.dataset.holdout)
        rows = dataset.players(con) if players else []
    finally:
        con.close()
    text = (
        f"{path}: {info['matches']} matches, {info['rounds']} rounds,"
        f" {info['batches']} batch(es); test split {info['test_matches']} matches"
        f" (holdout {CFG.dataset.holdout}); played {info['first']} .. {info['last']}"
    )
    if rows:
        text += "\n\n" + table(
            ["player", "matches", "rounds", "invalid moves"],
            [[str(x) for x in r] for r in rows],
        )
    lab.emit({**info, "players": rows}, text)


@app.command()
@lab_command("lab predict")
def predict(
    lab: Lab,
    bots: Annotated[list[str], typer.Argument(help=SPEC_HELP)],
    split: Annotated[Split, typer.Option(help=about("dataset.split"))] = SPLIT,
    players: Annotated[
        bool, typer.Option(help="also score per predicted player")
    ] = False,
) -> None:
    """Score bots as predictors of the next move, on the stored dataset."""
    from .. import progress
    from ..lab import dataset
    from ..lab.predict import evaluate, render
    from ..lab.predictor import make_predictor

    try:
        predictors = [make_predictor(s) for s in _specs(bots)]
    except ValueError as exc:  # a PredictorError
        raise fail(str(exc)) from None
    con = dataset.connect(_dataset_file(lab), read_only=True)
    try:
        seqs = dataset.load(
            con, str(split), CFG.dataset.holdout, dataset.last_match_id(con)
        )
    finally:
        con.close()
    if not seqs.n_matches:
        raise fail(f"the {split} split holds no matches")
    with progress.bar(len(predictors), "predictors", "bot") as bar:
        evaluations = []
        for p in predictors:
            evaluations.append(evaluate(p, seqs))
            bar.update(1)
    lab.say(
        f"## Predictors on the {split} split: {seqs.n_matches} matches,"
        f" {2 * seqs.n_rounds} predictions\n"
    )
    lab.emit(
        [{"label": e.label, **e.scores.__dict__} for e in evaluations],
        render(evaluations, players=players),
    )


@app.command("predict-tune")
@lab_command("lab predict-tune")
def predict_tune(
    lab: Lab,
    spaces: Annotated[list[str], typer.Argument(help="space files; several: AutoML")],
    study: Annotated[str, typer.Option(help=STUDY_HELP)],
    trials: Annotated[
        int, typer.Option(help=budget_help("trials this session", "predict_trials"))
    ] = (CFG.effort.budget(CFG.effort.default).predict_trials),
    validate_top: Annotated[
        int,
        typer.Option(
            help=budget_help("best trials scored on the test split", "validate_top")
        ),
    ] = CFG.effort.budget(CFG.effort.default).validate_top,
    split: Annotated[
        Split, typer.Option(help=about("dataset.tune_split"))
    ] = TUNE_SPLIT,
    metric: Annotated[Metric, typer.Option(help=about("dataset.metric"))] = METRIC,
    sampler: Annotated[Sampler, typer.Option(help=about("tuning.sampler"))] = SAMPLER,
    sampler_seed: Annotated[int, typer.Option(help=about("tuning.sampler_seed"))] = (
        CFG.tuning.sampler_seed
    ),
    prune: Annotated[bool, typer.Option(help=about("tuning.prune"))] = CFG.tuning.prune,
    timeout: Annotated[float, typer.Option(help=about("tuning.timeout_s"))] = (
        CFG.tuning.timeout_s
    ),
) -> None:
    """Tune predictors on the move dataset (several space files: AutoML)."""
    from ..lab import space as spaces_mod
    from ..lab.predict_tune import Setup, run_predict_tune
    from ..lab.tune import Search

    n_trials = lab.pick("trials", trials, "predict_trials")
    run_predict_tune(
        [spaces_mod.load(p) for p in spaces],
        study,
        Setup(
            db=_dataset_file(lab),
            metric=str(metric),
            holdout=CFG.dataset.holdout,
            chunks=CFG.dataset.chunks,
            split=str(split),
            root=lab.workspace,
        ),
        Search(
            sampler=str(sampler),
            sampler_seed=sampler_seed,
            trials=-1 if sampler == "grid" and "trials" not in lab.passed else n_trials,
            timeout=timeout,
            prune=prune,
            validate_top=lab.pick("validate_top", validate_top, "validate_top"),
        ),
    )
