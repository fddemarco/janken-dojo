"""Confirmed findings, `insights.md`: newest first, below the `___` rule.

    ## YYYY-MM-DD: <one-line finding>
    - **Evidence:** experiments/NNNN-slug.md (run <run id>): <effect, CI, n>
    - **Mechanism:** why we think it works
    - **Implication:** what to build or try next

An insight a later result contradicts is never deleted: its title is struck through
and points at the new evidence.
"""

import dataclasses
import datetime
import os
import re

FILE = "insights.md"
_RULE = re.compile(r"^_{3,}\s*$")
_TITLE = re.compile(r"^## (\d{4}-\d{2}-\d{2}): (.*)$")


class InsightError(ValueError):
    """An insight that can't be written."""


@dataclasses.dataclass(frozen=True)
class Insight:
    date: datetime.date
    finding: str
    evidence: str
    mechanism: str
    implication: str

    def render(self) -> str:
        for name, value in dataclasses.asdict(self).items():
            if name != "date" and (not str(value).strip() or "\n" in str(value)):
                raise InsightError(f"an insight's {name} is one non-empty line")
        return "\n".join(
            [
                f"## {self.date.isoformat()}: {self.finding}",
                "",
                f"- **Evidence:** {self.evidence}",
                f"- **Mechanism:** {self.mechanism}",
                f"- **Implication:** {self.implication}",
            ]
        )


def path(notebook: str) -> str:
    return os.path.join(notebook, FILE)


def titles(text: str) -> list[str]:
    """Every insight's `date: finding` line, newest first."""
    return [
        f"{m.group(1)}: {m.group(2)}" for m in map(_TITLE.match, text.splitlines()) if m
    ]


def cites(text: str, note_stem: str) -> bool:
    """Whether some insight's evidence cites the note `NNNN-slug`."""
    return f"experiments/{note_stem}.md" in text


def add(text: str, insight: Insight) -> str:
    """`text` with `insight` first below the rule.

    Raises:
        InsightError: the file has no `___` rule to add below.
    """
    lines = text.splitlines()
    rule = next((i for i, line in enumerate(lines) if _RULE.match(line)), -1)
    if rule < 0:
        raise InsightError("insights.md has no ___ rule above its entries")
    body = [line for line in lines[rule + 1 :] if not line.startswith("(no insights")]
    lines = lines[: rule + 1] + ["", insight.render(), ""] + _trim(body)
    return "\n".join(lines).rstrip("\n") + "\n"


def _trim(lines: list[str]) -> list[str]:
    while lines and not lines[0].strip():
        lines = lines[1:]
    return lines


def supersede(text: str, match: str, by: str) -> str:
    """`text` with the one insight whose title contains `match` struck through.

    Raises:
        InsightError: no insight, or several, match.
    """
    lines = text.splitlines()
    hits = [i for i, line in enumerate(lines) if _TITLE.match(line) and match in line]
    if len(hits) != 1:
        raise InsightError(f"{len(hits)} insights match {match!r}; give a unique part")
    found = _TITLE.match(lines[hits[0]])
    if found is None:  # re.match's API: None when it doesn't match (it does here)
        raise InsightError("unreachable: the title stopped matching")
    lines[hits[0]] = f"## {found.group(1)}: ~~{found.group(2)}~~ (superseded by {by})"
    return "\n".join(lines) + "\n"
