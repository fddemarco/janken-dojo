"""The high-level lifecycle commands: status, evaluate, tune, verdict, tournament.

Each is one functional iteration of the lab's loop, and keeps the notebook's books
(janken/lab/workflows.py does the work).
"""

import datetime
from typing import Annotated

import typer

from .. import settings
from .options import (
    CFG,
    LEAGUE,
    MODE,
    SAMPLER,
    Lab,
    League,
    Mode,
    Sampler,
    Verdict,
    about,
    budget_help,
    fail,
    lab_command,
    shown,
)

HYPOTHESIS_HELP = (
    "what you expect, and the effect size that would matter (written before the run)"
)
TITLE_HELP = "the note's title (default: built from the bots)"
NAME_HELP = "the note's file name, NNNN-<name>.md (default: from the title)"
IDEA_HELP = "the ideas.md number it tests (it goes in progress); 0: none"
NOTE_HELP = (
    "an existing note (number or NNNN-name) to run or resume, instead of a new one"
)


def plan_for(lab: Lab, mode: str):
    from ..lab.workflows import Plan

    return Plan(
        workspace=lab.workspace,
        bots_dir=lab.bots_dir,
        rounds=lab.rounds,
        pool_size=lab.pool_size,
        round_robins=lab.round_robins,
        seed=lab.seed,
        allow_small=lab.allow_small,
        use_mocks=lab.use_mocks,
        workers=lab.workers,
        mode=mode,
    )


def _stems(texts: list[str]) -> str:
    from ..match import bot_name

    return ", ".join(bot_name(t.split(":")[0]) for t in texts)


def _draft(
    kind: str,
    candidates: list[str],
    baselines: list[str],
    hypothesis: str,
    title: str,
    name: str,
    idea: int,
):
    from ..notebook import notes

    if not candidates:
        raise fail("name the candidate bot(s), or run an existing note with --note")
    title = title or (
        f"{_stems(candidates)} vs {_stems(baselines)}"
        if baselines
        else f"{kind} of {_stems(candidates)}"
    )
    return notes.Draft(
        kind=kind,
        title=title,
        slug=notes.slugify(name or title),
        hypothesis=hypothesis,
        candidates=list(candidates),
        baselines=list(baselines),
        idea=idea,
    )


@lab_command("status")
def status(lab: Lab) -> None:
    """The research state and the next step: notes, runs, ideas, leaderboard."""
    from ..engine.registry import discover
    from ..lab import analyze
    from ..lab.runs_db import RunStore
    from ..match import bot_name
    from ..notebook import ideas, insights, notes, state

    all_notes = notes.all_notes(lab.notebook)
    backlog = ideas.load(lab.notebook)
    runs = RunStore.at(lab.workspace)
    frame = runs.runs()
    run_status = (
        dict(zip(frame["run_id"], frame["status"], strict=True)) if frame.height else {}
    )
    with open(insights.path(lab.notebook), encoding="utf-8") as f:
        insight_text = f.read()
    field = {bot_name(p) for p in discover(lab.bots_dir)}
    step = state.next_step(all_notes, backlog, run_status, insight_text, field)
    open_notes = [n for n in all_notes if n.status != notes.ANALYZED]
    top = ideas.ranked(backlog)[: CFG.status.ideas]
    board = (
        analyze.leaderboard(lab.workspace, lab.given("rounds", 0)).head(
            CFG.status.leaderboard
        )
        if frame.height
        else frame
    )
    recent = frame.tail(CFG.status.recent_runs) if frame.height else frame
    data = {
        "next": step.__dict__,
        "open_notes": [
            {"note": f"{n.number:04d}-{n.slug}", "status": n.status} for n in open_notes
        ],
        "ideas": [i.__dict__ for i in top],
        "recent_runs": recent.to_dicts(),
        "leaderboard": board.to_dicts(),
        "insights": insights.titles(insight_text)[:3],
    }
    text = [
        f"## Next step: {step.action}",
        "",
        f"{step.reason}: `{step.command}`",
        "",
        "## Open notes",
        "",
        "\n".join(f"- {n.number:04d}-{n.slug}: {n.status}" for n in open_notes)
        or "(none)",
        "",
        "## Top open ideas",
        "",
        "\n".join(
            f"- #{i.number} [{i.priority}, {i.state}] {i.text[:110]}" for i in top
        )
        or "(none)",
        "",
        "## Recent runs",
        "",
        analyze.render_runs(recent),
        "",
        "## Leaderboard (candidates vs pool, pooled over runs)",
        "",
        analyze.render_frame(board) if board.height else "(no runs yet)",
    ]
    lab.emit(data, "\n".join(text))


@lab_command("evaluate")
def evaluate(
    lab: Lab,
    candidates: Annotated[
        list[str],
        typer.Argument(
            help="the bot(s) under test: bots/l1/x.yaml[:NAME=value,...]",
            default_factory=list,
            show_default=False,
        ),
    ],
    baseline: Annotated[
        list[str],
        typer.Option(
            help="a bot to beat, played in the same run (paired); repeatable",
            default_factory=list,
            show_default=False,
        ),
    ],
    hypothesis: Annotated[str, typer.Option(help=HYPOTHESIS_HELP)] = "",
    title: Annotated[str, typer.Option(help=TITLE_HELP)] = "",
    name: Annotated[str, typer.Option(help=NAME_HELP)] = "",
    idea: Annotated[int, typer.Option(help=IDEA_HELP)] = 0,
    note: Annotated[str, typer.Option(help=NOTE_HELP)] = "",
    mode: Annotated[Mode, typer.Option(help=about("evaluation.mode"))] = MODE,
) -> None:
    """Test candidates against random pools, with a note: hypothesis → results.

    Writes research/experiments/NNNN-<name>.md (planned), plays the experiment, analyzes
    it, and writes its results in (status run). Close it with `janken verdict`.
    """
    from ..lab import workflows

    if not note:
        draft = _draft(
            "evaluation", candidates, baseline, hypothesis, title, name, idea
        )
        created = workflows.plan(lab.notebook, draft, [], datetime.date.today())
        note = f"{created.number:04d}"
        lab.say(f"note {shown(created.path)} (planned)")
    done, summary = workflows.evaluate(lab.notebook, note, plan_for(lab, str(mode)))
    lab.emit(
        {
            "note": shown(done.path),
            "run": done.run_ids[-1],
            "summary": summary,
        },
        done.section("Results")
        + f"\n\nnote: {shown(done.path)} (status {done.status}); next:"
        f" janken verdict {done.number:04d} keep|drop|iterate --summary ...",
    )


@lab_command("tune")
def tune(
    lab: Lab,
    bots: Annotated[
        list[str],
        typer.Argument(
            help="the bot(s) to tune (the champion first)",
            default_factory=list,
            show_default=False,
        ),
    ],
    support: Annotated[
        list[str],
        typer.Option(
            help="a fleet support, tuned at weight 0 for the champion; repeatable",
            default_factory=list,
            show_default=False,
        ),
    ],
    hypothesis: Annotated[str, typer.Option(help=HYPOTHESIS_HELP)] = "",
    title: Annotated[str, typer.Option(help=TITLE_HELP)] = "",
    name: Annotated[str, typer.Option(help=NAME_HELP)] = "",
    idea: Annotated[int, typer.Option(help=IDEA_HELP)] = 0,
    note: Annotated[str, typer.Option(help=NOTE_HELP)] = "",
    trials: Annotated[
        int, typer.Option(help=budget_help("trials this session", "trials"))
    ] = CFG.effort.budget(CFG.effort.default).trials,
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
    sampler_seed: Annotated[
        int, typer.Option(help=about("tuning.sampler_seed"))
    ] = CFG.tuning.sampler_seed,
    prune: Annotated[bool, typer.Option(help=about("tuning.prune"))] = CFG.tuning.prune,
    timeout: Annotated[
        float, typer.Option(help=about("tuning.timeout_s"))
    ] = CFG.tuning.timeout_s,
) -> None:
    """Tune a bot (or a fleet) and validate its best trials, with a note.

    Scaffolds missing space files, runs the study (resuming it with --note), replays
    the best trials on fresh pools, and writes the recorded validations into the note.
    """
    from ..lab import workflows

    if not note:
        draft = _draft("tuning", bots, [], hypothesis, title, name, idea)
        created = workflows.plan(lab.notebook, draft, support, datetime.date.today())
        note = f"{created.number:04d}"
        lab.say(f"note {shown(created.path)} (planned)")
    budget = workflows.TuneBudget(
        trials=-1
        if sampler == "grid" and "trials" not in lab.passed
        else lab.pick("trials", trials, "trials"),
        round_robins=lab.pick(
            "round_robins", lab.raw["round_robins"], "tune_round_robins"
        ),
        validate_top=lab.pick("validate_top", validate_top, "validate_top"),
        validate_round_robins=lab.pick(
            "validate_round_robins", validate_round_robins, "validate_round_robins"
        ),
        sampler=str(sampler),
        sampler_seed=sampler_seed,
        prune=prune,
        seed=lab.given("seed", CFG.tuning.seed),
        timeout=timeout,
    )
    done = workflows.tune(
        lab.notebook,
        note,
        plan_for(lab, CFG.evaluation.mode),
        budget,
        lab.spaces_dir,
        CFG.space,
        CFG.space.weight,
    )
    lab.emit(
        {"note": shown(done.path), "study": done.study},
        done.section("Results")
        + f"\n\nnote: {shown(done.path)} (status {done.status}); next:"
        f" janken verdict {done.number:04d} keep|drop|iterate --summary ...",
    )


@lab_command("verdict")
def verdict(
    lab: Lab,
    note: Annotated[str, typer.Argument(help="the note: its number or NNNN-name")],
    decision: Annotated[
        Verdict, typer.Argument(help="keep, drop or iterate", metavar="VERDICT")
    ],
    summary: Annotated[
        str,
        typer.Option(help="one paragraph: what was learned (the paired result and CI)"),
    ],
    analysis: Annotated[
        str, typer.Option(help="the longer reading of the results, for ## Analysis")
    ] = "",
) -> None:
    """Close a note with its verdict; its idea becomes done, dropped or stays open."""
    from ..lab import workflows

    done = workflows.close(lab.notebook, note, str(decision), summary, analysis)
    lab.emit(
        {"note": shown(done.path), "verdict": done.verdict},
        f"note {shown(done.path)}: {done.verdict} (status {done.status})",
    )


@lab_command("tournament")
def tournament(
    lab: Lab,
    matches: Annotated[
        int, typer.Option(help=about("tournament.matches"))
    ] = CFG.tournament.matches,
    games: Annotated[
        int, typer.Option(help=about("tournament.games"))
    ] = CFG.tournament.games,
    league: Annotated[League, typer.Option(help=about("tournament.league"))] = LEAGUE,
    json_out: Annotated[
        str,
        typer.Option(
            "--json-out", help="also write standings, ratings and transcripts here"
        ),
    ] = "",
    verbose: Annotated[bool, typer.Option(help="print every match")] = False,
) -> None:
    """Play the whole field: standings, Glicko-2 ratings and titles (nothing stored)."""
    import json
    import time

    from .. import rating, report
    from ..tournament import discover_bots, run_tournament

    paths = discover_bots(lab.bots_dir)
    seed = lab.given("seed", CFG.tournament.seed)
    lab.say(
        f"Tournament: {len(paths)} bots, "
        + (
            f"~{games} games each"
            if games
            else f"round robin, {matches} match(es)/pair"
        )
        + f", {lab.rounds} rounds/match"
    )
    started = time.perf_counter()
    result = run_tournament(
        paths,
        rounds=lab.rounds,
        matches_per_pair=matches,
        on_match=(lambda m: print("  " + report.describe_match(m)))
        if verbose
        else None,
        workers=lab.workers or None,
        games_per_bot=games or None,
        seed=None if seed == settings.RANDOM_SEED else seed,
    )
    ratings, titles = rating.rate_tournament(
        result.matches, [s.name for s in result.standings]
    )
    data = report.result_to_dict(result, titles, ratings)
    lab.emit(
        data,
        report.standings_table(result, titles, ratings, league=str(league))
        + f"\n\n{len(result.matches)} matches in {time.perf_counter() - started:.2f}s",
    )
    if json_out:
        with open(json_out, "w") as f:
            json.dump(data, f, indent=2)
        lab.say(f"JSON results written to {json_out}")
