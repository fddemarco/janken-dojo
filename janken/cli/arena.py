"""`janken lab arena`: an experimental learner vs every opponent of a list.

The learner lives in janken/experimental/ (third-party libraries allowed, research
only, never exported), imported inside the command. It plays the opponents of a
gauntlet list (`janken lab gauntlet variations`: the field's bots and their
parameter variants) on seeds 1..n, every match appended to a gauntlet log as it
ends (so the command resumes), and is reported like `janken lab gauntlet run`: a
kit bot run through the gauntlet on the same list compares directly.
"""

import os
from typing import Annotated

import typer

from .gauntlet import LIST_HELP, LOG_HELP, read_list, report
from .options import CFG, Lab, about, bot_path, fail, lab_command

LABEL = "exp:vw@{}"  # a learner's name in the log: its settings' hash
SAY_EVERY = 50  # matches between progress lines


@lab_command("lab arena")
def arena(
    lab: Lab,
    opponents: Annotated[str, typer.Argument(help=LIST_HELP)],
    name: Annotated[str, typer.Option(help=LOG_HELP)],
    seeds: Annotated[int, typer.Option(help=about("arena.seeds"))] = CFG.arena.seeds,
    vw_args: Annotated[
        str, typer.Option(help=about("arena.vw_args"))
    ] = CFG.arena.vw_args,
    history: Annotated[
        int, typer.Option(help=about("arena.history"))
    ] = CFG.arena.history,
    explore: Annotated[
        float, typer.Option(help=about("arena.explore"))
    ] = CFG.arena.explore,
    expert: Annotated[
        list[str], typer.Option(help=about("arena.experts") + " (repeatable)")
    ] = list(CFG.arena.experts),
    no_experts: Annotated[
        bool, typer.Option(help="play without experts: history features only")
    ] = False,
    threshold: Annotated[
        float, typer.Option(help=about("gauntlet.threshold"))
    ] = CFG.gauntlet.threshold,
) -> None:
    """Play an experimental Vowpal Wabbit learner vs every opponent of a list,
    and report it like a gauntlet (research only: it can never be exported)."""
    from ..experimental import arena as played
    from ..experimental import features, vw
    from ..lab import gauntlet
    from ..spec import make_spec, params_hash

    stems = [] if no_experts else list(expert)
    settings = vw.Settings(vw_args, history, explore)
    label = LABEL.format(
        params_hash({"vw_args": vw_args, "history": history, "explore": explore})
        + (params_hash({"experts": stems}) if stems else "")
    )
    opps = read_list(opponents)
    ladder = list(range(1, seeds + 1))
    log = os.path.join(lab.workspace, CFG.arena.dir, name + ".jsonl")
    count = 0

    def logged(job: gauntlet.Job, result: gauntlet.Played) -> None:
        nonlocal count
        gauntlet.append(log, lab.rounds, {job: result})
        count += 1
        if count % SAY_EVERY == 0:
            lab.say(f"{count} matches")

    try:
        player = vw.VWPlayer(
            settings,
            features.Experts.of([make_spec(bot_path(lab, s)) for s in stems]),
        )
        lab.say(f"{label}: {vw_args}, history {history}, explore {explore}")
        played.run(
            player,
            opps,
            ladder,
            lab.rounds,
            label,
            gauntlet.load(log, lab.rounds),
            logged,
        )
    except ValueError as exc:
        raise fail(str(exc)) from exc
    report(lab, gauntlet.load(log, lab.rounds), [label], opps, ladder, threshold)
