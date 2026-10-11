"""The lab's lifecycle steps, each one functional iteration end to end.

They compose the lab (experiments, tuning, the runs database) with the notebook
(notes, ideas, insights), so the CLI's high-level commands stay thin:

    plan          a new note, with its hypothesis (and its idea marked in progress)
    evaluate      a note's experiment: run (or resume) it, analyze it, write the
                  results into the note
    tune          a note's study: spaces, trials, validation, results into the note
    close         a note's verdict, and its idea's status
    learn         an insight from a note, only if the note's evidence meets the bar

Nothing here prints except the lab code it calls; every input is passed in.
"""

import dataclasses
import datetime
import os
from collections.abc import Sequence

import polars as pl

from .. import settings
from ..notebook import ideas, insights, notes
from ..spec import BotSpec, format_spec, make_spec, parse_spec
from . import analyze, space
from .runs_db import COMPLETE, RunStore


class WorkflowError(ValueError):
    """A lifecycle step that can't be taken as asked."""


@dataclasses.dataclass(frozen=True)
class Plan:
    """How an experiment is played, and how much evidence it gathers."""

    workspace: str
    bots_dir: str
    rounds: int
    pool_size: int
    round_robins: int
    seed: int
    allow_small: bool
    use_mocks: bool
    workers: int
    mode: str


@dataclasses.dataclass(frozen=True)
class TuneBudget:
    """How a study searches and validates."""

    trials: int
    round_robins: int  # per trial
    validate_top: int
    validate_round_robins: int
    sampler: str
    sampler_seed: int
    prune: bool
    seed: int  # the pools and match seeds every trial plays
    timeout: float


def specs(texts: Sequence[str]) -> list[BotSpec]:
    """Bot specs from `bots/x.yaml[:NAME=value,...]` texts.

    Raises:
        WorkflowError: a spec that doesn't name a bot or its parameters.
    """
    try:
        return [parse_spec(t) for t in texts]
    except ValueError as exc:
        raise WorkflowError(str(exc)) from exc


def plan(
    notebook: str, draft: notes.Draft, supports: Sequence[str], today: datetime.date
) -> notes.Note:
    """A new planned note; its idea (if any) goes in progress."""
    if draft.idea:
        backlog = ideas.load(notebook)
        if backlog.get(draft.idea).state == ideas.OPEN:
            ideas.save(notebook, backlog.set_status(draft.idea, ideas.IN_PROGRESS))
    note = notes.create(notebook, draft, today)
    if supports:
        note = notes.save(
            note, notes.with_field(note.text, "Supports", notes.ticks(list(supports)))
        )
    return note


def evaluate(notebook: str, ref: str, how: Plan) -> tuple[notes.Note, dict]:
    """Run note `ref`'s experiment (or finish its interrupted run), analyze it, and
    write the results into the note; returns the note and the run's summary."""
    from .experiment import resume_experiment, run_experiment

    note = notes.find(notebook, ref)
    if note.kind != notes.EVALUATION:
        raise WorkflowError(
            f"note {note.number:04d} is a {note.kind}: use `janken tune`"
        )
    runs = RunStore.at(how.workspace)
    stem = f"{note.number:04d}-{note.slug}"
    known = [r for r in note.run_ids if r in runs.run_ids()]
    if known and runs.status(known[-1]) != COMPLETE:
        run_id = resume_experiment(known[-1], how.workspace, how.workers or None)
    elif known:
        run_id = known[-1]
    else:
        candidates = specs(note.candidates + note.baselines)
        if not candidates:
            raise WorkflowError(f"note {note.number:04d} names no candidate")
        started: list[notes.Note] = [note]

        def remember(run_id: str) -> None:
            """Put the run id in the note before it plays, so a cut run resumes."""
            started[0] = notes.save(
                started[0], notes.with_field(started[0].text, "Run", f"`{run_id}`")
            )

        run_id = run_experiment(
            candidates,
            bots_dir=how.bots_dir,
            pool_size=how.pool_size,
            rounds=how.rounds,
            round_robins=how.round_robins,
            seed=how.seed,
            mode=how.mode,
            name=stem,
            workers=how.workers or None,
            allow_small=how.allow_small,
            use_mocks=how.use_mocks,
            root=how.workspace,
            on_start=remember,
        )
        note = started[0]
    summary = analyze.analyze_run(run_id, how.workspace)
    note = notes.record_command(note, _command(note, run_id, runs))
    return notes.record_results(
        note, "Run", run_id, analyze.render_brief(summary)
    ), summary


def _command(note: notes.Note, run_id: str, runs: RunStore) -> str:
    """The reproducible low-level command of a stored run."""
    manifest = runs.manifest(run_id)
    cfg = manifest["config"]
    cands = " ".join(
        format_spec(make_spec(c["path"], c["params"])) for c in manifest["candidates"]
    )
    return (
        f"uv run janken lab experiment {cands} --rounds {cfg['rounds']}"
        f" --round-robins {cfg['round_robins']} --pool-size {cfg['pool_size']}"
        f" --seed {cfg['seed']} --name {note.number:04d}-{note.slug}"
    )


def _space_for(
    bot: str, weight: float, spaces_dir: str, config: settings.SpaceConfig
) -> space.Space:
    """The bot's space file (scaffolded and written if missing), at `weight`."""
    from ..match import bot_name

    path = os.path.join(spaces_dir, bot_name(bot) + ".yaml")
    if os.path.isfile(path):
        found = space.load(path)
    else:
        found = space.scaffold(bot, weight, config)
        space.write(found, spaces_dir)
    return dataclasses.replace(found, weight=weight)


def tune(
    notebook: str,
    ref: str,
    how: Plan,
    budget: TuneBudget,
    spaces_dir: str,
    space_config: settings.SpaceConfig,
    champion_weight: float,
) -> notes.Note:
    """Run note `ref`'s study (resuming it if it exists), validate its best trials,
    and write the recorded validations into the note."""
    from .tune import Search, Setup, run_tune

    note = notes.find(notebook, ref)
    if note.kind != notes.TUNING:
        raise WorkflowError(
            f"note {note.number:04d} is an {note.kind}: use `janken evaluate`"
        )
    supports = note.supports
    tuned = [
        _space_for(b, champion_weight, spaces_dir, space_config)
        for b in note.candidates
    ]
    tuned += [_space_for(b, 0.0, spaces_dir, space_config) for b in supports]
    study = f"{note.number:04d}-{note.slug}"
    note = notes.save(note, notes.with_field(note.text, "Study", f"`{study}`"))
    run_tune(
        tuned,
        study,
        Setup(
            rounds=how.rounds,
            round_robins=budget.round_robins,
            pool_size=how.pool_size,
            seed=budget.seed,
            bots_dir=how.bots_dir,
            workers=how.workers,
            allow_small=how.allow_small,
            use_mocks=how.use_mocks,
            root=how.workspace,
        ),
        Search(
            sampler=budget.sampler,
            sampler_seed=budget.sampler_seed,
            trials=budget.trials,
            timeout=budget.timeout,
            prune=budget.prune,
            validate_top=budget.validate_top,
            validate_round_robins=budget.validate_round_robins,
        ),
    )
    command = (
        "uv run janken lab study run "
        + " ".join(
            os.path.relpath(os.path.join(spaces_dir, s.stem + ".yaml")) for s in tuned
        )
        + f" --study {study} --rounds {how.rounds} --round-robins {budget.round_robins}"
        f" --pool-size {how.pool_size} --seed {budget.seed}"
    )
    note = notes.record_command(note, command)
    results = analyze.render_validations(study, how.workspace)
    return notes.record_results(note, "Study", study, results)


def close(
    notebook: str, ref: str, verdict: str, summary: str, analysis: str
) -> notes.Note:
    """Give note `ref` its verdict, and set its idea's status to match."""
    note = notes.record_verdict(notes.find(notebook, ref), verdict, summary, analysis)
    if note.idea:
        backlog = ideas.load(notebook)
        if verdict == "iterate":
            status = ideas.IN_PROGRESS
        else:
            state = ideas.DONE if verdict == "keep" else ideas.DROPPED
            status = ideas.linked(state, note.number, note.slug)
        ideas.save(notebook, backlog.set_status(note.idea, status))
    return note


def evidence(note: notes.Note, workspace: str) -> list[str]:
    """The note's results that meet the insight bar: a paired comparison (or a
    validated difference from the defaults) whose 95% CI excludes 0."""
    runs = RunStore.at(workspace)
    if note.kind == notes.TUNING:
        rows = runs.validations("tune_validations", note.study)
        if not rows.height:
            return []
        found = rows.filter(
            (pl.col("trial") >= 0)
            & ((pl.col("vs_defaults_lo") > 0) | (pl.col("vs_defaults_hi") < 0))
        )
        return [
            "{} vs defaults {:+.1f} pts [{:+.1f}, {:+.1f}] (validation run {})".format(
                r["champion"],
                100 * r["vs_defaults"],
                100 * r["vs_defaults_lo"],
                100 * r["vs_defaults_hi"],
                r["run_id"],
            )
            for r in found.iter_rows(named=True)
        ]
    known = [r for r in note.run_ids if r in runs.run_ids()]
    if not known:
        return []
    summary = analyze.analyze_run(known[-1], workspace, write=False)
    return [analyze.comparison_text(c) for c in analyze.significant(summary)]


def learn(
    notebook: str,
    ref: str,
    finding: str,
    mechanism: str,
    implication: str,
    workspace: str,
    today: datetime.date,
) -> insights.Insight:
    """Add an insight from note `ref`, if its evidence meets the bar.

    Raises:
        WorkflowError: the note has no result whose CI excludes 0.
    """
    note = notes.find(notebook, ref)
    found = evidence(note, workspace)
    if not found:
        raise WorkflowError(
            f"note {note.number:04d} has no paired comparison or validated difference"
            " whose 95% CI excludes 0: that's a result, not an insight. Add an idea"
            " to confirm it instead (`janken idea add`)."
        )
    where = f"run {note.run_ids[-1]}" if note.run_ids else f"study {note.study}"
    insight = insights.Insight(
        today,
        finding,
        f"experiments/{note.number:04d}-{note.slug}.md ({where}): " + "; ".join(found),
        mechanism,
        implication,
    )
    file = insights.path(notebook)
    with open(file, encoding="utf-8") as f:
        text = f.read()
    with open(file, "w", encoding="utf-8") as f:
        f.write(insights.add(text, insight))
    return insight
