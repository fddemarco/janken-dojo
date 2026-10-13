"""`janken lab gauntlet ...`: candidates vs every opponent of a list, one by one.

How it works is in janken/lab/gauntlet.py: `variations` writes the opponents (the
field's bots and their parameter variants), `nash` finds the Nash-like ones to
leave out, `run` plays the candidates against the rest. Matches are logged in the
workspace's `gauntlet.dir` as they are played, so every command resumes.
"""

import os
from collections.abc import Callable
from typing import Annotated

import typer

from .options import CFG, Lab, about, fail, lab_command

app = typer.Typer(
    help="Gauntlets: candidates vs every opponent of a list, variations included.",
    no_args_is_help=True,
)

LIST_HELP = "a file of bot specs, one per line (bots/l1/x.yaml:NAME=value,...)"
LOG_HELP = "the log's name in the workspace's gauntlet folder (resumed if it exists)"


def _read_list(path: str) -> list[str]:
    if not os.path.isfile(path):
        raise fail(f"no list file {path}")
    with open(path) as lines:
        found = [line.split("#")[0].strip() for line in lines]
    return [f for f in found if f]


def _log(lab: Lab, name: str) -> str:
    return os.path.join(lab.workspace, CFG.gauntlet.dir, name + ".jsonl")


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
                path, drawn, cfg.variation_probes, cfg.probe_rounds
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
) -> None:
    """Which bots are Nash-like: no probe bot skews their results either way."""
    from ..lab import gauntlet

    cfg = CFG.gauntlet
    checked = _read_list(bots)
    probes = list(cfg.nash_probes)
    ladder = list(range(1, seeds + 1))
    log = _log(lab, name)
    jobs = gauntlet.missing(checked, probes, ladder, gauntlet.load(log, lab.rounds))
    gauntlet.play(
        jobs,
        lab.rounds,
        cfg.batch,
        log,
        lab.workers,
        CFG.execution.flush_s,
        _progress(lab),
    )
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
) -> None:
    """Play candidates vs every opponent; list those under the threshold."""
    from ..lab import gauntlet

    opps = _read_list(opponents)
    ladder = list(range(1, seeds + 1))
    log = _log(lab, name)
    jobs = gauntlet.missing(cand, opps, ladder, gauntlet.load(log, lab.rounds))
    gauntlet.play(
        jobs,
        lab.rounds,
        CFG.gauntlet.batch,
        log,
        lab.workers,
        CFG.execution.flush_s,
        _progress(lab),
    )
    done = gauntlet.load(log, lab.rounds)
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
