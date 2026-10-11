"""`janken idea ...` and `janken insight ...`: the backlog and the confirmed findings."""

import datetime
import os
from typing import Annotated

import typer

from .options import Lab, Priority, lab_command, shown

idea_app = typer.Typer(
    help="The ideas backlog (research/ideas.md).", no_args_is_help=True
)
insight_app = typer.Typer(
    help="Confirmed findings (research/insights.md).", no_args_is_help=True
)

NUMBER_HELP = "the idea's number in ideas.md"


def _show(idea) -> str:
    return (
        f"#{idea.number} [{idea.priority}, {idea.status}]\n{idea.text}\n\n"
        f"motivation: {idea.motivation}"
    )


@idea_app.command("add")
@lab_command("idea add")
def idea_add(
    lab: Lab,
    text: Annotated[
        str, typer.Argument(help="the idea, one line (markdown allowed, no '|')")
    ],
    priority: Annotated[
        Priority, typer.Option(help="P1 (likely big win) … P3 (curiosity)")
    ],
    motivation: Annotated[
        str,
        typer.Option(help="the evidence or source behind it (a note, insight, card)"),
    ],
) -> None:
    """Add an open idea to the backlog."""
    from ..notebook import ideas

    backlog, idea = ideas.load(lab.notebook).add(text, str(priority), motivation)
    ideas.save(lab.notebook, backlog)
    lab.emit(idea.__dict__, f"added idea #{idea.number}")


@idea_app.command("list")
@lab_command("idea list")
def idea_list(
    lab: Lab,
    every: Annotated[
        bool, typer.Option("--all", help="also list done and dropped ideas")
    ] = False,
) -> None:
    """The open ideas, in progress first, then by priority (--all: every idea)."""
    from ..notebook import ideas

    backlog = ideas.load(lab.notebook)
    shown = backlog.ideas if every else ideas.ranked(backlog)
    lab.emit(
        [i.__dict__ for i in shown],
        "\n".join(f"#{i.number} [{i.priority}, {i.state}] {i.text}" for i in shown)
        or "(no open ideas)",
    )


@idea_app.command("show")
@lab_command("idea show")
def idea_show(
    lab: Lab, number: Annotated[int, typer.Argument(help=NUMBER_HELP)]
) -> None:
    """One idea in full."""
    from ..notebook import ideas

    idea = ideas.load(lab.notebook).get(number)
    lab.emit(idea.__dict__, _show(idea))


@idea_app.command("start")
@lab_command("idea start")
def idea_start(
    lab: Lab, number: Annotated[int, typer.Argument(help=NUMBER_HELP)]
) -> None:
    """Mark an idea in progress."""
    from ..notebook import ideas

    backlog = ideas.load(lab.notebook).set_status(number, ideas.IN_PROGRESS)
    ideas.save(lab.notebook, backlog)
    lab.emit({"number": number, "status": ideas.IN_PROGRESS}, f"#{number}: in-progress")


@idea_app.command("drop")
@lab_command("idea drop")
def idea_drop(
    lab: Lab,
    number: Annotated[int, typer.Argument(help=NUMBER_HELP)],
    reason: Annotated[
        str, typer.Option(help="why, with a link to the note or insight that shows it")
    ],
) -> None:
    """Drop an idea without a note of its own (a note's verdict drops its idea)."""
    from ..notebook import ideas

    status = f"{ideas.DROPPED} ({reason})"
    ideas.save(lab.notebook, ideas.load(lab.notebook).set_status(number, status))
    lab.emit({"number": number, "status": status}, f"#{number}: {status}")


@insight_app.command("add")
@lab_command("insight add")
def insight_add(
    lab: Lab,
    note: Annotated[
        str, typer.Option(help="the note whose evidence backs it (number or NNNN-name)")
    ],
    finding: Annotated[
        str, typer.Option(help="the one-line finding, general enough to steer bots")
    ],
    mechanism: Annotated[
        str, typer.Option(help="why it works (say so if it's a hypothesis)")
    ],
    implication: Annotated[
        str, typer.Option(help="what to build or try next (add it as an idea too)")
    ],
) -> None:
    """Record an insight, if the note's evidence meets the bar.

    The bar: a paired comparison (or a validated difference from a tuned bot's
    defaults) whose 95% CI excludes 0. The evidence line is written from the note's
    stored numbers.
    """
    from ..lab import workflows

    insight = workflows.learn(
        lab.notebook,
        note,
        finding,
        mechanism,
        implication,
        lab.workspace,
        datetime.date.today(),
    )
    lab.emit(
        {"title": f"{insight.date}: {insight.finding}", "evidence": insight.evidence},
        f"recorded in {shown(os.path.join(lab.notebook, 'insights.md'))}:\n"
        f"{insight.render()}",
    )


@insight_app.command("list")
@lab_command("insight list")
def insight_list(lab: Lab) -> None:
    """Every insight's title, newest first."""
    from ..notebook import insights

    with open(insights.path(lab.notebook), encoding="utf-8") as f:
        found = insights.titles(f.read())
    lab.emit(found, "\n".join(found) or "(no insights yet)")


@insight_app.command("supersede")
@lab_command("insight supersede")
def insight_supersede(
    lab: Lab,
    match: Annotated[str, typer.Argument(help="a unique part of the insight's title")],
    by: Annotated[str, typer.Option(help="the newer evidence: a note or insight link")],
) -> None:
    """Strike an insight a later result contradicts (it is never deleted)."""
    from ..notebook import insights

    path = insights.path(lab.notebook)
    with open(path, encoding="utf-8") as f:
        text = insights.supersede(f.read(), match, by)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    lab.emit({"superseded": match, "by": by}, f"superseded: {match}")
