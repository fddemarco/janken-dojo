"""`janken lab profile ...`: where a command's time goes, and whether a fix worked.

The command profiled or benchmarked comes after `--`, with its own flags (give it a
scratch `--workspace`); the flags before `--` are the profile command's own, and its
`--workspace` is where profiles are stored. The budget rule and the bucket names are
in janken/lab/profiling.py and docs/development.md (Performance); the `/profile`
skill drives these commands.
"""

from typing import Annotated

import typer

from .options import CFG, Lab, about, fail, lab_command

app = typer.Typer(
    help="Profiles, benchmarks and timing spans: find hotspots, measure fixes.",
    no_args_is_help=True,
)

TARGET_HELP = "the janken command, after `--`: -- lab experiment bots/l1/x.yaml ..."


def _target(argv: list[str]) -> list[str]:
    words = [w for w in argv if w != "--"]
    if not words:
        raise fail("name the command after `--`: -- lab experiment ...")
    if words[0] == "janken":
        words = words[1:]
    return words


@app.command("run")
@lab_command("lab profile run")
def run(
    lab: Lab,
    target: Annotated[list[str], typer.Argument(help=TARGET_HELP)],
    jit: Annotated[bool, typer.Option(help=about("profile.jit"))] = CFG.profile.jit,
    warmup: Annotated[
        bool, typer.Option(help=about("profile.warmup"))
    ] = CFG.profile.warmup,
    top: Annotated[int, typer.Option(help=about("profile.top"))] = CFG.profile.top,
    force: Annotated[
        bool, typer.Option(help="profile again even if this code was profiled")
    ] = False,
) -> None:
    """Profile a janken command: its hotspots, and whether fixing them pays."""
    from .. import telemetry
    from ..lab import profiling

    argv = _target(target)
    done = profiling.same_code(
        profiling.records(lab.workspace), argv, jit, telemetry.code_fingerprint()
    )
    if done and not force:
        last = done[-1]
        lab.say(
            f"{last.id} already profiled this command on this code; nothing changed"
            " since, so it would only measure noise (--force to profile again)\n"
        )
        lab.emit(
            {"record": last.to_dict(), "reused": True},
            profiling.render(last, profiling.folder_of(lab.workspace, last)),
        )
        return
    try:
        taken = profiling.run_profiled(
            lab.workspace, argv, jit, warmup, CFG.profile.interval_s, top
        )
    except profiling.ProfileError as exc:
        raise fail(str(exc)) from None
    stats = profiling.span_stats(
        lab.workspace, CFG.profile.window_days, CFG.telemetry.slow_factor
    )
    verdict = profiling.worth(taken.record, stats, CFG.profile)
    lab.emit(
        {"record": taken.record.to_dict(), "worth": verdict.__dict__},
        profiling.render(taken.record, taken.folder)
        + "\n\n"
        + profiling.render_worth(verdict),
    )


@app.command("bench")
@lab_command("lab profile bench")
def bench(
    lab: Lab,
    target: Annotated[list[str], typer.Argument(help=TARGET_HELP)],
    jit: Annotated[bool, typer.Option(help=about("profile.jit"))] = CFG.profile.jit,
    warmup: Annotated[
        bool, typer.Option(help=about("profile.warmup"))
    ] = CFG.profile.warmup,
    repeats: Annotated[
        int, typer.Option(help=about("profile.repeats"))
    ] = CFG.profile.repeats,
    baseline: Annotated[
        str,
        typer.Option(help="a benchmark of the same command to compare with (an id)"),
    ] = "",
) -> None:
    """Time a janken command (no profiler); with --baseline, keep or revert a fix."""
    from ..lab import profiling

    argv = _target(target)
    try:
        timed = profiling.bench(lab.workspace, argv, jit, warmup, repeats)
        text = profiling.render(timed.record, timed.folder)
        data: dict[str, object] = {"record": timed.record.to_dict()}
        if baseline:
            before = profiling.find(lab.workspace, baseline)
            change = profiling.gain(before, timed.record)
            kept = profiling.keep(change, CFG.profile)
            text += (
                f"\n\nvs {before.id} ({before.wall_s:.2f}s): {change:+.1%} wall time"
                f" cut; **{'keep' if kept else 'revert'}** the change"
                f" (min_gain {CFG.profile.min_gain:.0%})"
            )
            data |= {"baseline": before.id, "gain": change, "keep": kept}
    except profiling.ProfileError as exc:
        raise fail(str(exc)) from None
    lab.emit(data, text)


@app.command("list")
@lab_command("lab profile list")
def list_profiles(lab: Lab) -> None:
    """The stored profiles and benchmarks; `stale` ones ran on other code."""
    from .. import telemetry
    from ..lab import profiling

    stored = profiling.records(lab.workspace)
    lab.emit(
        [r.to_dict() for r in stored],
        profiling.render_list(stored, telemetry.code_fingerprint()),
    )


@app.command("show")
@lab_command("lab profile show")
def show(
    lab: Lab,
    ref: Annotated[
        str, typer.Argument(help="a profile's id, a unique part, or latest")
    ],
) -> None:
    """A stored profile or benchmark, and where its flame graph is."""
    from ..lab import profiling

    try:
        record = profiling.find(lab.workspace, ref)
    except profiling.ProfileError as exc:
        raise fail(str(exc)) from None
    lab.emit(
        record.to_dict(),
        profiling.render(record, profiling.folder_of(lab.workspace, record)),
    )


@app.command("spans")
@lab_command("lab profile spans")
def spans(
    lab: Lab,
    days: Annotated[
        int, typer.Option(help=about("profile.window_days"))
    ] = CFG.profile.window_days,
    op: Annotated[
        str, typer.Option(help="only this operation (command, engine.play, ...)")
    ] = "",
) -> None:
    """Where the lab's time went: each timed operation per command, slow ones flagged.

    A command is slow when its last run took telemetry.slow_factor times its median.
    """
    from ..lab import analyze, profiling

    frame = profiling.span_stats(lab.workspace, days, CFG.telemetry.slow_factor, op)
    if not frame.height:
        lab.emit([], f"(no spans in the last {days} days)")
        return
    lab.emit(frame.to_dicts(), analyze.render_frame(frame))
