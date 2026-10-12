"""The lab's lifecycle steps, each one functional iteration end to end.

They compose the lab (experiments, tuning, the runs database) with the notebook
(notes, ideas, insights), so the CLI's high-level commands stay thin:

    plan          a new note, with its hypothesis (and its idea marked in progress)
    evaluate      a note's experiment: run (or resume) it, analyze it, write the
                  results into the note
    tune          a note's study: spaces, trials, validation, results into the note
    close         a note's verdict, and its idea's status
    learn         an insight from a note, only if the note's evidence meets the bar
    classify      a kept candidate's species: a new one, the next version, or a
                  variant (janken/lab/classify.py decides; this moves the files)

Nothing here prints except the lab code it calls; every input is passed in.
"""

import dataclasses
import datetime
import math
import os
import re
import typing
from collections.abc import Collection, Sequence

import numpy as np
import polars as pl

from .. import settings
from ..notebook import ideas, insights, notes
from ..notebook import species as registry
from ..spec import BotSpec, format_spec, make_spec, parse_spec
from . import analyze, classify, space
from .dataset import Sequences
from .runs_db import COMPLETE, RunStore

if typing.TYPE_CHECKING:
    from . import cores


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
    """Bot specs from `bots/l1/x.yaml[:NAME=value,...]` texts.

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


def evaluate(
    notebook: str, ref: str, how: Plan, grow_to: int = 0
) -> tuple[notes.Note, dict]:
    """Run note `ref`'s experiment (or finish its interrupted run), analyze it, and
    write the results into the note; returns the note and the run's summary.

    `grow_to` above the note's run's round robins grows that run to as many (the
    1 --> 3 --> 5 --> 7 --> 10 ladder: stop as soon as the comparison is clear);
    0 leaves it as planned."""
    from .experiment import resume_experiment, run_experiment

    note = notes.find(notebook, ref)
    if note.kind != notes.EVALUATION:
        raise WorkflowError(
            f"note {note.number:04d} is a {note.kind}: use `janken tune`"
        )
    runs = RunStore.at(how.workspace)
    stem = f"{note.number:04d}-{note.slug}"
    known = [r for r in note.run_ids if r in runs.run_ids()]
    if known and (runs.status(known[-1]) != COMPLETE or grow_to):
        run_id = resume_experiment(
            known[-1], how.workspace, how.workers or None, round_robins=grow_to
        )
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
    small = "--allow-small-pool" if cfg.get("allow_small") else "--no-allow-small-pool"
    mocks = "--mocks" if cfg.get("mocks") else "--no-mocks"
    return (
        f"uv run janken lab experiment {cands} --rounds {cfg['rounds']}"
        f" --round-robins {cfg['round_robins']} --pool-size {cfg['pool_size']}"
        f" --mode {cfg.get('mode', 'full')} {small} {mocks}"
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


# --- species ---------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Field:
    """The field's species, each by its current version, read as cores."""

    paths: dict[str, str]  # {stem: bot file}
    levels: dict[str, str]  # {stem: "L1", ...}
    cores: dict[str, np.ndarray]  # {stem: its core's predictions on the histories}


@dataclasses.dataclass(frozen=True)
class Classification:
    """What a kept candidate turned out to be, and the evidence."""

    note: notes.Note
    decision: classify.Decision
    kin: tuple[classify.Kin, ...]
    incumbent: str  # its level's closest species ("" when there is none)
    correlation: float  # nan when no paired run was needed
    matchups: tuple[classify.Matchup, ...]
    speedup: float  # the incumbent's time over the candidate's (1 when not timed)
    run_id: str  # "" when no paired run was needed
    stem: str  # the bot's stem now
    path: str  # its file now


def bot_level(path: str) -> str:
    """The level name of the bot at `path` ("L1", "L2", ...)."""
    from .. import mocks
    from ..kit import levels

    return levels.name(mocks.path_level(path))


def species_paths(bots_dir: str) -> dict[str, str]:
    """{stem: path} of every species' current version: the versioned field bots
    (Oracles are not species)."""
    from .. import mocks
    from ..engine.registry import discover
    from ..match import bot_name

    return {
        bot_name(p): p
        for p in discover(bots_dir)
        if registry.is_versioned(bot_name(p)) and not mocks.is_mock(p)
    }


def histories(dataset_file: str, split: str, holdout: float, matches: int) -> Sequences:
    """`matches` matches of the dataset's `split`, evenly spread: the histories
    cores are compared on.

    Raises:
        WorkflowError: the dataset is missing or the split is empty.
    """
    from . import dataset

    if not os.path.isfile(dataset_file):
        raise WorkflowError(
            f"no move dataset at {dataset_file}: grow one with `janken lab dataset add`"
        )
    con = dataset.connect(dataset_file, read_only=True)
    try:
        seqs = dataset.load(con, split, holdout, dataset.last_match_id(con))
    finally:
        con.close()
    if not seqs.n_matches:
        raise WorkflowError(
            f"the dataset's {split} split holds no matches: `janken lab dataset add`"
        )
    return seqs.spread(matches)


def core(path: str, seqs: Sequences) -> np.ndarray:
    """The predictions of the bot's core (defaults) on `seqs`."""
    from .predict import predictions
    from .predictor import make_predictor

    return predictions(make_predictor(make_spec(path)), seqs)


def core_cache(workspace: str, config: settings.SpeciesConfig) -> "cores.CoreCache":
    """The workspace's kept cores, computing a missing one with `core`."""
    from . import cores

    return cores.CoreCache(os.path.join(workspace, config.cores_dir), core)


def read_field(
    paths: dict[str, str], seqs: Sequences, cache: "cores.CoreCache"
) -> Field:
    """Species (`{stem: path}` of their current versions) read as cores on `seqs`."""
    return Field(
        paths=paths,
        levels={s: bot_level(p) for s, p in paths.items()},
        cores={s: cache.core(p, seqs) for s, p in paths.items()},
    )


def compare(
    path: str, field: Field, seqs: Sequences, cache: "cores.CoreCache"
) -> list[classify.Kin]:
    """The field's species by how close their cores are to the bot's, closest first
    (the bot itself left out)."""
    from ..match import bot_name

    others = {s: c for s, c in field.cores.items() if s != bot_name(path)}
    return classify.ranked(cache.core(path, seqs), others, field.levels)


def _species_run(
    note: notes.Note, specs_: list[BotSpec], how: Plan
) -> tuple[str, notes.Note]:
    """The paired run of the candidate and the incumbent: played, resumed, or the
    stored one (`species-NNNN`); its id goes in the note before it plays."""
    from .experiment import resume_experiment, run_experiment

    runs = RunStore.at(how.workspace)
    name = f"species-{note.number:04d}"
    frame = runs.runs()
    stored = frame.filter(pl.col("name") == name) if frame.height else frame
    if stored.height:
        run_id = str(stored["run_id"][-1])
        if runs.status(run_id) != COMPLETE:
            run_id = resume_experiment(run_id, how.workspace, how.workers or None)
        return run_id, note
    started: list[notes.Note] = [note]

    def remember(run_id: str) -> None:
        started[0] = notes.save(
            started[0], notes.with_field(started[0].text, "Species run", f"`{run_id}`")
        )

    run_id = run_experiment(
        specs_,
        bots_dir=how.bots_dir,
        pool_size=how.pool_size,
        rounds=how.rounds,
        round_robins=how.round_robins,
        seed=how.seed,
        mode=how.mode,
        name=name,
        workers=how.workers or None,
        allow_small=how.allow_small,
        use_mocks=how.use_mocks,
        root=how.workspace,
        on_start=remember,
    )
    return run_id, started[0]


def _candidate(note: notes.Note, bots_dir: str) -> BotSpec:
    """The kept note's one candidate, still in the field without a version.

    Raises:
        WorkflowError: the note can't be classified.
    """
    from ..match import bot_name

    if note.kind != notes.EVALUATION or note.verdict != "keep":
        raise WorkflowError(
            f"note {note.number:04d} is not a kept evaluation: only a keep is"
            " classified"
        )
    if note.species:
        raise WorkflowError(f"note {note.number:04d} is classified: {note.species}")
    stems = [bot_name(c.split(":")[0]) for c in note.candidates]
    field = {bot_name(p) for p in _discover(bots_dir)}
    open_stems = classifiable(stems, field)
    if len(open_stems) != 1:
        raise WorkflowError(
            f"note {note.number:04d} has {len(open_stems)} candidate(s) in the field"
            f" ({bots_dir}) without a version, {open_stems}: classify one bot at a"
            " time (retire the others to bots/inactive/legacy/, or make each a note"
            " of its own)"
        )
    (spec,) = specs([note.candidates[stems.index(open_stems[0])]])
    if spec.params:
        raise WorkflowError(
            f"{spec.label} is a variant with parameters: make it a bot first"
            " (`janken bot new`), evaluate it, then classify it"
        )
    return spec


def classifiable(stems: Sequence[str], field: Collection[str]) -> list[str]:
    """The stems still to classify: in the field, without a version."""
    return [s for s in stems if s in field and not registry.is_versioned(s)]


def _discover(bots_dir: str) -> list[str]:
    from ..engine.registry import discover

    return discover(bots_dir)


def classify_note(
    notebook: str,
    ref: str,
    name: str,
    how: Plan,
    spaces_dir: str,
    config: settings.SpeciesConfig,
    seqs: Sequences,
) -> Classification:
    """Classify note `ref`'s kept candidate, and act on it.

    - New species (no species of its level is alike): it becomes `<name>_v1`.
    - Next version (alike its level's nearest species, and dominates it): it becomes
      `<species>_v{N+1}`; the current version retires to the legacy folder.
    - Variant (alike, without dominating): it retires to the legacy folder.

    The note gets a Species field and section, and `species.md` the lineage.

    Raises:
        WorkflowError: the note can't be classified, or a new species has no name.
    """
    note = notes.find(notebook, ref)
    spec = _candidate(note, how.bots_dir)
    level = bot_level(spec.path)
    paths = {  # versions never cross levels: only its level's species are read
        s: p for s, p in species_paths(how.bots_dir).items() if bot_level(p) == level
    }
    cache = core_cache(how.workspace, config)
    field = read_field(paths, seqs, cache)
    same = kin = compare(spec.path, field, seqs, cache)
    correlation, compared, run_id, speedup = math.nan, (), "", 1.0
    if same and classify.needs_run(same[0], level, config):
        nearest = same[0]
        run_id, note = _species_run(
            note, [spec, make_spec(field.paths[nearest.stem])], how
        )
        _, _, df = RunStore.at(how.workspace).load_run(run_id)
        lf = analyze.long_form(df)
        correlation = classify.profile_correlation(lf, spec.label, nearest.stem)
        compared = tuple(classify.matchups(lf, spec.label, nearest.stem, config))
        if correlation >= config.profile_correlation and classify.as_good(compared):
            speedup = _speedup(spec, make_spec(field.paths[nearest.stem]), how, config)
    decision = (
        classify.decide(same[0], level, correlation, compared, config, speedup)
        if same
        else classify.Decision(classify.NEW, (f"the field has no {level} species",))
    )
    found = Classification(
        note=note,
        decision=decision,
        kin=tuple(kin),
        incumbent=same[0].stem if same else "",
        correlation=correlation,
        matchups=compared,
        speedup=speedup,
        run_id=run_id,
        stem=spec.stem,
        path=spec.path,
    )
    if decision.outcome == classify.NEW and not name:
        raise WorkflowError(
            f"{spec.stem} is a new species ({'; '.join(decision.reasons)}): name it"
            f" with --name\n\n{render_kin(found.kin)}"
        )
    if decision.outcome != classify.NEW and name:
        raise WorkflowError(
            f"{spec.stem} is a {decision.outcome} of {same[0].stem}, not a new"
            " species: leave out --name"
        )
    return _apply(notebook, found, name, how.bots_dir, spaces_dir, config, level)


def _apply(
    notebook: str,
    found: Classification,
    name: str,
    bots_dir: str,
    spaces_dir: str,
    config: settings.SpeciesConfig,
    level: str,
) -> Classification:
    """Move the files, record the lineage and write the note."""
    note = found.note
    link = f"[{note.number:04d}](experiments/{note.number:04d}-{note.slug}.md)"
    book = registry.load(notebook)
    legacy = os.path.join(bots_dir, config.legacy_dir)
    outcome = found.decision.outcome
    if outcome == classify.NEW:
        book = book.add(registry.check_name(name), level, found.stem, link)
        stem = registry.Version(name, 1).stem
        path = _rename(found.path, stem, bots_dir, spaces_dir)
        label = f"`{stem}` (new species)"
    elif outcome == classify.PROMOTE:
        incumbent = found.incumbent
        book, stem = book.promote(
            registry.parse_stem(incumbent).species, found.stem, link
        )
        _retire(_find(bots_dir, incumbent), legacy, spaces_dir)
        path = _rename(found.path, stem, bots_dir, spaces_dir)
        label = f"`{stem}` (promoted over `{incumbent}`)"
    else:
        incumbent = found.incumbent
        book = book.add_variant(
            registry.parse_stem(incumbent).species, found.stem, link
        )
        path = _retire(found.path, legacy, spaces_dir)
        stem = found.stem
        label = f"`{stem}` (variant of `{incumbent}`)"
    registry.save(notebook, book)
    done = dataclasses.replace(found, stem=stem, path=path)
    note = notes.record_species(note, label, render_classification(done))
    return dataclasses.replace(done, note=note)


def play_time(spec: BotSpec, how: Plan, config: settings.SpeciesConfig) -> float:
    """Seconds the bot takes to play `config.speed_matches` self-play matches on one
    thread: the fastest of `config.speed_repeats` timings, after a warm-up (the
    engine compiles once per process)."""
    import time

    from ..engine import play_pairs

    pairs = [(spec, spec)] * config.speed_matches
    seeds = list(range(config.speed_matches))
    play_pairs(pairs[:1], how.rounds, seeds[:1], workers=1)
    times = []
    for _ in range(config.speed_repeats):
        started = time.perf_counter()
        play_pairs(pairs, how.rounds, seeds, workers=1)
        times.append(time.perf_counter() - started)
    return min(times)


def _speedup(
    challenger: BotSpec,
    incumbent: BotSpec,
    how: Plan,
    config: settings.SpeciesConfig,
) -> float:
    """The incumbent's playing time over the challenger's."""
    return play_time(incumbent, how, config) / play_time(challenger, how, config)


def _find(bots_dir: str, stem: str) -> str:
    from ..engine.registry import find

    return find(bots_dir, stem)


def _rename(path: str, stem: str, bots_dir: str, spaces_dir: str) -> str:
    """Rename a bot file (and its space file) to `stem`, in the same folder."""
    from ..match import bot_name

    old = bot_name(path)
    taken = {bot_name(p) for p in _discover(bots_dir)}
    if stem in taken:
        raise WorkflowError(f"a bot named {stem} exists already")
    target = os.path.join(os.path.dirname(path), stem + ".yaml")
    os.replace(path, target)
    old_space = os.path.join(spaces_dir, old + ".yaml")
    if os.path.isfile(old_space):
        with open(old_space, encoding="utf-8") as f:
            text = f.read()
        text = re.sub(
            rf"^(bot: .*){re.escape(old)}\.yaml$",
            rf"\g<1>{stem}.yaml",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        with open(os.path.join(spaces_dir, stem + ".yaml"), "w", encoding="utf-8") as f:
            f.write(text)
        os.remove(old_space)
    return target


def _retire(path: str, legacy: str, spaces_dir: str) -> str:
    """Move a bot out of the field, into the legacy folder; its space goes too
    (git keeps it)."""
    from ..match import bot_name

    os.makedirs(legacy, exist_ok=True)
    target = os.path.join(legacy, os.path.basename(path))
    if os.path.exists(target):
        raise WorkflowError(f"{target} exists already")
    os.replace(path, target)
    space_file = os.path.join(spaces_dir, bot_name(path) + ".yaml")
    if os.path.isfile(space_file):
        os.remove(space_file)
    return target


def render_kin(kin: Sequence[classify.Kin], top: int = 0) -> str:
    """The field ranked by agreement, as a markdown table (`top` rows; 0: all)."""
    rows = kin[:top] if top else kin
    return "\n".join(
        ["| species (current version) | level | core agreement |", "|---|---|---|"]
        + [f"| `{k.stem}` | {k.level} | {k.agreement:.1%} |" for k in rows]
    )


def render_matchups(compared: Sequence[classify.Matchup]) -> str:
    """The challenger minus the incumbent per matchup, as a markdown table."""
    lines = [
        "| opponent | n | diff | 95% CI | strict lower bound | |",
        "|---|---|---|---|---|---|",
    ]
    for m in compared:
        mark = "worse" if m.worse else ("better" if m.better else "")
        lines.append(
            f"| {m.opponent} | {m.n} | {100 * m.mean:+.1f} |"
            f" [{100 * m.lo:+.1f}, {100 * m.hi:+.1f}] | {100 * m.strict_lo:+.1f}"
            f" | {mark} |"
        )
    return "\n".join(lines)


def render_classification(found: Classification) -> str:
    """The note's Species section."""
    out = [
        f"**{found.decision.outcome}**: " + "; ".join(found.decision.reasons) + ".",
        "",
        "Closest species by core agreement (the dataset's histories):",
        "",
        render_kin(found.kin, top=5),
    ]
    if found.run_id:
        timed = (
            f" Self-play speed: {found.speedup:.2f}x the incumbent's."
            if found.speedup != 1.0
            else ""
        )
        run = (
            f"Paired run `{found.run_id}`: profile correlation"
            f" {found.correlation:+.2f}.{timed} Challenger minus incumbent, per"
            " matchup (points; the strict bound is the Bonferroni test for 'better'):"
        )
        out += [
            "",
            run,
            "",
            render_matchups(found.matchups),
        ]
    return "\n".join(out)
