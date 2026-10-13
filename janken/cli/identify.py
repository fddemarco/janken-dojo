"""`janken lab identify`: can an opponent bandit's parameters be told in time?

Research only: janken/experimental/identify.py, imported inside the command. Every
opponent of a gauntlet list is played on seeds 1..n; each match logs the posterior's
checkpoints and the rounds after the commit of three branches (exploit the
posterior, keep the probe, the oracle), one JSON line per match in the
workspace's `identify.dir`, so the command resumes. The report averages the
checkpoints round by round and pairs each branch with keep.
"""

import concurrent.futures
import dataclasses
import json
import math
import os
from collections.abc import Mapping, Sequence
from typing import Annotated

import typer

from .gauntlet import LIST_HELP, LOG_HELP, read_list
from .options import CFG, Lab, about, bot_path, fail, lab_command


def _rows(log: str, key: str) -> list[dict]:
    """The log's matches played with this setup (its hash, `key`)."""
    if not os.path.isfile(log):
        return []
    with open(log) as lines:
        found = [json.loads(line) for line in lines if line.strip()]
    return [row for row in found if row["setup"] == key]


def _append(log: str, row: Mapping) -> None:
    os.makedirs(os.path.dirname(log) or ".", exist_ok=True)
    with open(log, "a") as sink:
        sink.write(json.dumps(row) + "\n")


def _percent(value: float) -> str:
    return "-" if math.isnan(value) else f"{value:.1%}"


def _report(lab: Lab, rows: Sequence[Mapping], condition: str) -> None:
    from ..experimental import identify

    points = identify.curve(rows)
    gains = identify.gains(rows)
    species = sorted({str(r["species"]) for r in rows})
    by_species = {
        s: identify.gains([r for r in rows if r["species"] == s]) for s in species
    }
    text = [
        f"{len(rows)} matches ({condition}); the posterior, averaged per checkpoint:",
        "",
        (
            "| round | MAP species right | mass on species | mass near truth"
            " | param error (MAP right) | vote hit | particles |"
        ),
        "|---|---|---|---|---|---|---|",
        *(
            f"| {p.round} | {_percent(p.correct)} | {_percent(p.species_mass)}"
            f" | {_percent(p.near_mass)} | {_percent(p.param_error)}"
            f" | {_percent(p.hit)} | {p.alive:.0f} |"
            for p in points
        ),
        "",
        "Rounds after the commit, won minus lost (vs keep: paired, 95% CI):",
        "",
        "| branch | net | vs keep |",
        "|---|---|---|",
        *(
            f"| {g.branch} | {g.mean:+.1%} | {g.vs_keep:+.1%} +- {g.half_width:.1%} |"
            for g in gains
        ),
        "",
        "| opponent species | exploit vs keep | oracle vs keep | matches |",
        "|---|---|---|---|",
        *(
            f"| {s} | {g[0].vs_keep:+.1%} +- {g[0].half_width:.1%}"
            f" | {g[2].vs_keep:+.1%} | {g[0].matches} |"
            for s, g in by_species.items()
        ),
    ]
    if not all(r["prefix_agrees"] for r in rows):
        text.append("\nwarning: some branches disagree before the commit round")
    lab.emit(
        {
            "condition": condition,
            "matches": len(rows),
            "curve": [dataclasses.asdict(p) for p in points],
            "gains": [dataclasses.asdict(g) for g in gains],
            "by_species": {
                s: [dataclasses.asdict(x) for x in g] for s, g in by_species.items()
            },
        },
        "\n".join(text),
    )


@lab_command("lab identify")
def identify(
    lab: Lab,
    opponents: Annotated[str, typer.Argument(help=LIST_HELP)],
    name: Annotated[str, typer.Option(help=LOG_HELP)],
    hypothesis: Annotated[
        list[str],
        typer.Option(
            help=about("identify.hypotheses") + " (repeatable)",
            default_factory=lambda: list(CFG.identify.hypotheses),
        ),
    ],
    seeds: Annotated[
        int, typer.Option(help=about("identify.seeds"))
    ] = CFG.identify.seeds,
    particles: Annotated[
        int, typer.Option(help=about("identify.particles"))
    ] = CFG.identify.particles,
    eps: Annotated[float, typer.Option(help=about("identify.eps"))] = CFG.identify.eps,
    commit_round: Annotated[
        int, typer.Option(help=about("identify.commit_round"))
    ] = CFG.identify.commit_round,
    checkpoint_every: Annotated[
        int, typer.Option(help=about("identify.checkpoint_every"))
    ] = CFG.identify.checkpoint_every,
    prune_ratio: Annotated[
        float, typer.Option(help=about("identify.prune_ratio"))
    ] = CFG.identify.prune_ratio,
    near: Annotated[
        float, typer.Option(help=about("identify.near"))
    ] = CFG.identify.near,
    probe: Annotated[
        str, typer.Option(help=about("identify.probe"))
    ] = CFG.identify.probe,
    leave_one_out: Annotated[
        bool, typer.Option(help=about("identify.leave_one_out"))
    ] = CFG.identify.leave_one_out,
    sampler_seed: Annotated[
        int, typer.Option(help=about("identify.seed"))
    ] = CFG.identify.seed,
) -> None:
    """Can an opponent bandit's parameters be told from its moves in time to pay?
    A particle posterior per match, and the rounds after the commit played three
    ways: exploit it, keep the probe, or the oracle (research only)."""
    from ..experimental import identify as study
    from ..spec import params_hash

    if commit_round >= lab.rounds:
        raise fail(f"the commit round {commit_round} must come before {lab.rounds}")
    setup = study.Setup(
        hypotheses=tuple(bot_path(lab, h) for h in hypothesis),
        spaces_dir=lab.spaces_dir,
        particles=particles,
        sampler_seed=sampler_seed,
        eps=eps,
        commit=commit_round,
        every=checkpoint_every,
        prune_ratio=prune_ratio,
        near=near,
        probe=bot_path(lab, probe),
        rounds=lab.rounds,
        leave_one_out=leave_one_out,
    )
    key = params_hash(dataclasses.asdict(setup))
    log = os.path.join(lab.workspace, CFG.identify.dir, name + ".jsonl")
    opps = read_list(opponents)
    done = {(r["opponent"], r["seed"]) for r in _rows(log, key)}
    jobs = [(o, s) for s in range(1, seeds + 1) for o in opps if (o, s) not in done]
    condition = "leave-one-out" if leave_one_out else "in library"
    lab.say(f"setup {key} ({condition}): {len(jobs)} matches to play")
    workers = lab.workers or os.cpu_count() or 1
    try:
        with concurrent.futures.ProcessPoolExecutor(workers) as pool:
            futures = [pool.submit(study.study, setup, o, s) for o, s in jobs]
            for k, future in enumerate(concurrent.futures.as_completed(futures), 1):
                _append(log, {"setup": key, **future.result()})
                lab.say(f"{k}/{len(jobs)} matches")
    except ValueError as exc:
        raise fail(str(exc)) from exc
    rows = [r for r in _rows(log, key) if r["opponent"] in set(opps)]
    if not rows:
        raise fail("no match played")
    _report(lab, rows, condition)
