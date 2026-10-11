"""The research state, and the next step of the lab's loop.

`next_step` is the loop's decision list, as pure logic over what the notebook and the
workspace hold: finish what's started before starting something new.

1. A note whose run was interrupted → finish it (`janken evaluate --note`).
1. A note with results but no verdict → decide (`janken verdict`).
1. A planned note → run it (`janken evaluate --note` / `janken tune --note`).
1. A `keep` note no insight cites yet → consider an insight (`janken insight add`).
1. Otherwise → build the top open idea (in-progress first, then by priority).
1. No open idea → ideate.
"""

import dataclasses
from collections.abc import Mapping, Sequence

from . import ideas, insights, notes


@dataclasses.dataclass(frozen=True)
class Step:
    """What to do next, why, and the command (or skill) that does it."""

    action: str  # resume | verdict | run | learn | build | ideate
    reason: str
    command: str


def next_step(
    all_notes: Sequence[notes.Note],
    backlog: ideas.Backlog,
    run_status: Mapping[str, str],
    insights_text: str,
) -> Step:
    """The loop's next step (see the module docstring).

    Args:
        all_notes: every note, by number.
        backlog: the ideas backlog.
        run_status: {run id: status} of the stored runs.
        insights_text: insights.md's text.
    """
    for note in all_notes:
        if any(run_status.get(r) in ("running", "interrupted") for r in note.run_ids):
            return Step(
                "resume",
                f"note {note.number:04d}'s run was interrupted",
                f"janken evaluate --note {note.number:04d}",
            )
    for note in all_notes:
        if note.status == notes.RUN:
            return Step(
                "verdict",
                f"note {note.number:04d} has results but no verdict",
                f"janken verdict {note.number:04d} keep|drop|iterate --summary ...",
            )
    for note in all_notes:
        if note.status == notes.PLANNED:
            verb = "tune" if note.kind == notes.TUNING else "evaluate"
            return Step(
                "run",
                f"note {note.number:04d} is planned",
                f"janken {verb} --note {note.number:04d}",
            )
    for note in reversed(all_notes):
        stem = f"{note.number:04d}-{note.slug}"
        if note.verdict == "keep" and not insights.cites(insights_text, stem):
            return Step(
                "learn",
                f"note {note.number:04d} was kept and no insight cites it",
                f"janken insight add --note {note.number:04d} ...",
            )
    top = ideas.ranked(backlog)
    if top:
        idea = top[0]
        return Step(
            "build",
            f"idea #{idea.number} ({idea.priority}, {idea.state}) is the top open idea",
            f"janken bot new <name> --from <bot> --idea {idea.number}",
        )
    return Step("ideate", "the backlog has no open idea", "janken idea add ...")
