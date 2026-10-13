"""`janken lab gauntlet ...`: candidates vs every opponent of a list, one by one.

How it works is in janken/lab/gauntlet.py: `variations` writes the opponents (the
field's bots and their parameter variants), `nash` finds the Nash-like ones to
leave out, `run` plays the candidates against the rest. Matches are logged in the
workspace's `gauntlet.dir` as they are played, so every command resumes.
"""

import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated

import typer

from .options import CFG, Lab, about, fail, lab_command

if TYPE_CHECKING:
    from ..lab.gauntlet import Job, Log
    from ..lab.match_cache import MatchCache

app = typer.Typer(
    help="Gauntlets: candidates vs every opponent of a list, variations included.",
    no_args_is_help=True,
)

LIST_HELP = "a file of bot specs, one per line (bots/l1/x.yaml:NAME=value,...)"
LOG_HELP = "the log's name in the workspace's gauntlet folder (resumed if it exists)"


def read_list(path: str) -> list[str]:
    if not os.path.isfile(path):
        raise fail(f"no list file {path}")
    with open(path) as lines:
        found = [line.split("#")[0].strip() for line in lines]
    return [f for f in found if f]


def _log(lab: Lab, name: str) -> str:
    return os.path.join(lab.workspace, CFG.gauntlet.dir, name + ".jsonl")


def report(
    lab: Lab,
    done: "Log",
    cand: list[str],
    opps: list[str],
    ladder: list[int],
    threshold: float,
) -> None:
    """Each candidate's mean share won, and the opponents it falls under the
    threshold against."""
    from ..lab import gauntlet

    data, text = {}, []
    for c in cand:
        rows = gauntlet.shares(done, c, opps, ladder)
        under = sorted((r for r in rows if r.won < threshold), key=lambda r: r.won)
        mean = sum(r.won for r in rows) / max(1, len(rows))
        data[c] = {"mean": mean, "under": [r.__dict__ for r in under], "met": len(rows)}
        text.append(
            f"{c}: {len(under)} of {len(rows)} opponents under {threshold:.0%},"
            f" mean {mean:.1%}"
        )
        text += [
            f"  {r.won:.1%} [{r.won - r.half_width:.1%}, {r.won + r.half_width:.1%}]"
            f" lost {r.lost:.1%} n={r.matches}  {r.opponent}"
            for r in under
        ]
    lab.emit(data, "\n".join(text))


def _done(lab: Lab, log: str) -> "Log":
    from ..lab import gauntlet

    return gauntlet.load(log, lab.rounds)


def _play(lab: Lab, jobs: "list[Job]", log: str) -> None:
    """Play the jobs into the log: streamed, read back from the match cache."""
    from ..lab import gauntlet

    gauntlet.play(
        jobs,
        lab.rounds,
        CFG.gauntlet.batch,
        log,
        lab.workers,
        CFG.execution.flush_s,
        _progress(lab),
        _matches(lab),
    )


def _matches(lab: Lab) -> "MatchCache":
    """The workspace's match cache (on unless runs.match_cache is off)."""
    from ..lab.match_cache import MatchCache
    from ..lab.runs_db import RunStore

    return MatchCache(RunStore.at(lab.workspace), CFG.runs.match_cache)


def _progress(lab: Lab) -> Callable[[int, int], None]:
    def show(done: int, total: int) -> None:
        lab.say(f"{done}/{total} matches")

    return show


@app.command("variations")
@lab_command("lab gauntlet variations")
def variations(
    lab: Lab,
    out: Annotated[str, typer.Argument(help="the list file to write")],
    per_bot: Annotated[
        int, typer.Option(help=about("gauntlet.per_bot"))
    ] = CFG.gauntlet.per_bot,
    only: Annotated[
        str, typer.Option(help="only these bots: stems, comma-separated (all: empty)")
    ] = "",
) -> None:
    """Write the field's bots and their parameter variants, one spec per line."""
    from ..engine.registry import discover
    from ..lab import gauntlet
    from ..lab import space as spaces
    from ..match import bot_name

    cfg = CFG.gauntlet
    lines: list[str] = []
    for path in sorted(discover(lab.bots_dir)):
        stem = bot_name(path)
        level = os.path.basename(os.path.dirname(path))
        wanted = not only or stem in only.split(",")
        if stem in cfg.exclude or level not in cfg.levels or not wanted:
            continue
        space_file = os.path.join(lab.spaces_dir, stem + ".yaml")
        found: list[str] = []
        if os.path.isfile(space_file):
            drawn = gauntlet.candidates(
                path, spaces.load(space_file), per_bot, cfg.draws, cfg.seed
            )
            kept = gauntlet.changing(
                path, drawn, cfg.variation_probes, cfg.probe_rounds, _matches(lab)
            )
            found = kept[:per_bot]
        lab.say(f"{stem}: {len(found)} variants")
        lines += [os.path.relpath(path), *found]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w") as sink:
        sink.write("\n".join(lines) + "\n")
    lab.emit({"file": out, "bots": len(lines)}, f"wrote {len(lines)} bots to {out}")


@app.command("nash")
@lab_command("lab gauntlet nash")
def nash(
    lab: Lab,
    bots: Annotated[str, typer.Argument(help=LIST_HELP)],
    out: Annotated[str, typer.Argument(help="the markdown table to write")],
    name: Annotated[str, typer.Option(help=LOG_HELP)],
    seeds: Annotated[
        int, typer.Option(help=about("gauntlet.nash_seeds"))
    ] = CFG.gauntlet.nash_seeds,
    skew: Annotated[
        float, typer.Option(help=about("gauntlet.nash_skew"))
    ] = CFG.gauntlet.nash_skew,
    sequential: Annotated[
        bool, typer.Option(help=about("gauntlet.sequential"))
    ] = CFG.gauntlet.sequential,
) -> None:
    """Which bots are Nash-like: no probe bot skews their results either way.

    With --sequential, a bot that one probe already skews decisively in its first
    match (gauntlet.nash_decisive) is settled without the other seeds."""
    from ..lab import gauntlet

    cfg = CFG.gauntlet
    checked = read_list(bots)
    probes = list(cfg.nash_probes)
    ladder = list(range(1, seeds + 1))
    log = _log(lab, name)
    _play(lab, gauntlet.missing(checked, probes, ladder[:1], _done(lab, log)), log)
    done = _done(lab, log)
    rest = [
        b
        for b in checked
        if not (sequential and gauntlet.decisive(done, b, probes, cfg.nash_decisive))
    ]
    _play(lab, gauntlet.missing(rest, probes, ladder[1:], done), log)
    verdicts = gauntlet.nash_verdicts(
        gauntlet.load(log, lab.rounds), checked, probes, ladder, skew
    )
    like = [v for v in verdicts if v.nash_like]
    header = (
        f"Each bot vs {len(probes)} probes ({seeds} seeds x {lab.rounds} rounds):"
        f" {', '.join(os.path.basename(p)[:-5] for p in probes)}. Nash-like: rounds"
        f" won - lost under {skew:.0%} in size vs every probe."
    )
    rows = [
        header,
        "",
        f"{len(like)} of {len(verdicts)} bots are Nash-like.",
        "",
        "| bot | most skewed probe | won | lost | Nash-like |",
        "|---|---|---|---|---|",
    ]
    rows += [
        f"| `{v.bot}` | `{os.path.basename(v.probe)[:-5]}` | {v.won:.1%} | {v.lost:.1%}"
        f" | {'yes' if v.nash_like else 'no'} |"
        for v in verdicts
    ]
    with open(out, "w") as sink:
        sink.write("\n".join(rows) + "\n")
    lab.emit(
        {"nash_like": [v.bot for v in like], "checked": len(verdicts)},
        f"{len(like)} of {len(verdicts)} bots are Nash-like (table: {out})\n"
        + "\n".join(f"  {v.bot}" for v in like),
    )


@app.command("run")
@lab_command("lab gauntlet run")
def run(
    lab: Lab,
    opponents: Annotated[str, typer.Argument(help=LIST_HELP)],
    cand: Annotated[list[str], typer.Option(help="a candidate bot spec (repeatable)")],
    name: Annotated[str, typer.Option(help=LOG_HELP)],
    seeds: Annotated[
        int, typer.Option(help=about("gauntlet.seeds"))
    ] = CFG.gauntlet.seeds,
    threshold: Annotated[
        float, typer.Option(help=about("gauntlet.threshold"))
    ] = CFG.gauntlet.threshold,
    sequential: Annotated[
        bool, typer.Option(help=about("gauntlet.sequential"))
    ] = CFG.gauntlet.sequential,
) -> None:
    """Play candidates vs every opponent; list those under the threshold.

    With --sequential, every pairing plays gauntlet.min_seeds seeds, then one
    more at a time while its share won isn't yet clear of the threshold
    (janken/lab/sequential.py): only the close ones play every seed."""
    from ..lab import gauntlet
    from ..lab import sequential as seq

    cfg = CFG.gauntlet
    opps = read_list(opponents)
    ladder = list(range(1, seeds + 1))
    log = _log(lab, name)
    open_ = [(c, o) for c in cand for o in opps]
    looked: list[int] = []
    first = cfg.min_seeds if sequential else len(ladder)
    for stage in gauntlet.stages(ladder, first):
        looked += stage
        done = _done(lab, log)
        jobs = [
            gauntlet.Job(a, b, s)
            for s in stage
            for a, b in open_
            if gauntlet.Job(a, b, s) not in done
        ]
        _play(lab, jobs, log)
        if len(looked) < len(ladder):
            alpha = seq.look_alpha(len(looked), len(ladder), cfg.stop_alpha)
            open_ = gauntlet.still_open(
                _done(lab, log), open_, looked, threshold, alpha
            )
            lab.say(f"after {len(looked)} seeds: {len(open_)} pairings still close")
    report(lab, _done(lab, log), cand, opps, ladder, threshold)


@app.command("fingerprint")
@lab_command("lab gauntlet fingerprint")
def fingerprint(
    lab: Lab,
    exports: Annotated[
        list[str], typer.Argument(help="tournament exports (CSV), one or more")
    ],
    name: Annotated[
        str,
        typer.Option(
            help="the gauntlet log in which the probes played the lab's bots, as"
            " candidates (janken lab gauntlet run LIST --cand PROBE ...)"
        ),
    ],
    probes: Annotated[
        list[str],
        typer.Option(
            "--probe",
            help=about("gauntlet.fingerprint_probes") + " (repeatable)",
            default_factory=lambda: list(CFG.gauntlet.fingerprint_probes),
        ),
    ],
    nearest: Annotated[
        int, typer.Option(help=about("gauntlet.fingerprint_nearest"))
    ] = CFG.gauntlet.fingerprint_nearest,
) -> None:
    """Fingerprint tournament bots by their margins over scripted probes.

    Reads every match of the exports, takes each bot's mean margin over each
    probe it met ((rounds won - lost) / rounds played), and names the lab bots
    whose margins over the same probes, in the gauntlet log, are closest
    (research/probes.md)."""
    from ..lab import fingerprint as fp

    for path in exports:
        if not os.path.isfile(path):
            raise fail(f"no export file {path}")
    matches = [m for path in exports for m in fp.read_export(path)]
    seen = fp.competition(matches, probes)
    library = fp.lab(_done(lab, _log(lab, name)), probes)
    if not library:
        raise fail(f"the gauntlet log {name} holds no match of these probes")
    data, text = {}, []
    for bot, prints in sorted(seen.items()):
        close = fp.nearest(prints, library, nearest)
        data[bot] = {"fingerprint": prints, "nearest": close}
        margins = ", ".join(f"{fp.stem(p)} {v:+.0%}" for p, v in sorted(prints.items()))
        text.append(f"{bot}: {margins}")
        text += [f"  {d:.0%} from {other}" for other, d in close]
    lab.emit(data, "\n".join(text) or "no bot of the exports met a probe")
