"""The ideas backlog, `ideas.md`: one markdown table row per idea.

    | # | idea | priority | status | motivation |

A status is `open`, `in-progress`, `done (→ link)` or `dropped (→ link)`. Rows are
parsed from and rendered back to the table; every other line of the file, and every
row nobody changed, is kept byte for byte.
"""

import dataclasses
import os
import re

FILE = "ideas.md"
PRIORITIES = ("P1", "P2", "P3")
OPEN, IN_PROGRESS, DONE, DROPPED = "open", "in-progress", "done", "dropped"
STATUSES = (OPEN, IN_PROGRESS, DONE, DROPPED)
_ROW = re.compile(r"^\|\s*(\d+)\s*\|")


class IdeaError(ValueError):
    """A backlog operation that can't be done."""


@dataclasses.dataclass(frozen=True)
class Idea:
    """One backlog row."""

    number: int
    text: str
    priority: str
    status: str  # the whole cell, e.g. "done (→ [0003](experiments/0003-x.md))"
    motivation: str

    @property
    def state(self) -> str:
        """The status's first word: open, in-progress, done or dropped."""
        return self.status.split()[0] if self.status.split() else OPEN

    @property
    def is_open(self) -> bool:
        return self.state in (OPEN, IN_PROGRESS)

    def row(self) -> str:
        cells = [
            str(self.number),
            self.text,
            self.priority,
            self.status,
            self.motivation,
        ]
        return "| " + " | ".join(cells) + " |"


def parse_row(line: str) -> Idea:
    """An idea from its table row.

    Raises:
        IdeaError: the row doesn't have the backlog's five cells.
    """
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) != 5:
        raise IdeaError(f"an idea row has 5 cells, got {len(cells)}: {line[:60]}")
    number, text, priority, status, motivation = cells
    return Idea(int(number), text, priority, status, motivation)


@dataclasses.dataclass(frozen=True)
class Backlog:
    """ideas.md: its lines, and which of them are idea rows."""

    lines: tuple[str, ...]

    @property
    def ideas(self) -> list[Idea]:
        return [parse_row(line) for line in self.lines if _ROW.match(line)]

    def get(self, number: int) -> Idea:
        for idea in self.ideas:
            if idea.number == number:
                return idea
        raise IdeaError(f"no idea #{number} in the backlog")

    def replace(self, idea: Idea) -> "Backlog":
        """The backlog with idea `idea.number`'s row rewritten."""
        self.get(idea.number)
        lines = [
            idea.row()
            if _ROW.match(line) and parse_row(line).number == idea.number
            else line
            for line in self.lines
        ]
        return Backlog(tuple(lines))

    def add(self, text: str, priority: str, motivation: str) -> tuple["Backlog", Idea]:
        """The backlog with a new open idea after the last row, and that idea."""
        if priority not in PRIORITIES:
            raise IdeaError(f"priority must be one of {', '.join(PRIORITIES)}")
        for name, value in (("idea", text), ("motivation", motivation)):
            if not value.strip() or "|" in value or "\n" in value:
                raise IdeaError(f"an idea's {name} is one line of text without '|'")
        rows = [i for i, line in enumerate(self.lines) if _ROW.match(line)]
        if not rows:
            raise IdeaError("the backlog has no table to add to")
        idea = Idea(
            max(i.number for i in self.ideas) + 1, text, priority, OPEN, motivation
        )
        lines = list(self.lines)
        lines.insert(rows[-1] + 1, idea.row())
        return Backlog(tuple(lines)), idea

    def set_status(self, number: int, status: str) -> "Backlog":
        idea = self.get(number)
        return self.replace(dataclasses.replace(idea, status=status))

    def render(self) -> str:
        return "\n".join(self.lines) + "\n"


def path(notebook: str) -> str:
    return os.path.join(notebook, FILE)


def load(notebook: str) -> Backlog:
    with open(path(notebook), encoding="utf-8") as f:
        return parse(f.read())


def parse(text: str) -> Backlog:
    return Backlog(tuple(text.splitlines()))


def save(notebook: str, backlog: Backlog) -> None:
    with open(path(notebook), "w", encoding="utf-8") as f:
        f.write(backlog.render())


def linked(state: str, number: int, slug: str) -> str:
    """A closed status pointing at its note: `done (→ [0007](experiments/0007-x.md))`."""
    if state not in (DONE, DROPPED):
        raise IdeaError(f"only done or dropped link a note, not {state!r}")
    return f"{state} (→ [{number:04d}](experiments/{number:04d}-{slug}.md))"


def ranked(backlog: Backlog) -> list[Idea]:
    """The open ideas, in-progress first, then by priority and number."""
    return sorted(
        (i for i in backlog.ideas if i.is_open),
        key=lambda i: (i.state != IN_PROGRESS, i.priority, i.number),
    )
