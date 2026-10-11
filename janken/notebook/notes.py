"""Experiment notes, `experiments/NNNN-<slug>.md`: one per experiment or study.

A note is created `planned` with its hypothesis, becomes `run` when its results are
written in, and `analyzed` when it gets a verdict. Its header is a list of
`- **Key:** value` fields; its body is `## ` sections. The CLI rewrites single fields
and whole sections, and leaves everything else as written:

    # NNNN: <title>

    - **Date:** YYYY-MM-DD
    - **Status:** planned | run | analyzed
    - **Kind:** evaluation | tuning
    - **Idea:** #N
    - **Candidates:** `a`, `b`
    - **Baselines:** `c`
    - **Run:** `<run id>`            (an evaluation)
    - **Study:** `<study>`           (a tuning study)
    - **Verdict:** keep | drop | iterate

    ## Hypothesis / ## Command / ## Results / ## Analysis / ## Verdict

Notes written before the CLI kept their run id on a `Run id: `...`` line; they are
read the same way.
"""

import dataclasses
import datetime
import os
import re

DIR = "experiments"
PLANNED, RUN, ANALYZED = "planned", "run", "analyzed"
STATUSES = (PLANNED, RUN, ANALYZED)
EVALUATION, TUNING = "evaluation", "tuning"
KINDS = (EVALUATION, TUNING)
VERDICTS = ("keep", "drop", "iterate")
SECTIONS = ("Hypothesis", "Command", "Results", "Analysis", "Verdict")
_NAME = re.compile(r"^(\d{4})-([a-z0-9][a-z0-9_-]*)\.md$")
_FIELD = re.compile(r"^- \*\*([A-Za-z ]+):\*\* ?(.*)$")
_LEGACY_RUN = re.compile(r"^Run id: `([^`]+)`")
_TICKED = re.compile(r"`([^`]+)`")


class NoteError(ValueError):
    """A note that doesn't exist or can't take the change."""


@dataclasses.dataclass(frozen=True)
class Note:
    """A note on disk: where it is, and what it says."""

    number: int
    slug: str
    path: str
    text: str

    @property
    def title(self) -> str:
        first = self.text.splitlines()[0] if self.text else ""
        return first.split(":", 1)[1].strip() if ":" in first else first.lstrip("# ")

    def field(self, key: str) -> str:
        """A header field's value ("" when the note doesn't have it)."""
        for line in self.text.splitlines():
            found = _FIELD.match(line)
            if found and found.group(1) == key:
                return found.group(2).strip()
        return ""

    @property
    def status(self) -> str:
        return self.field("Status").split()[0] if self.field("Status") else PLANNED

    @property
    def kind(self) -> str:
        return self.field("Kind") or EVALUATION

    @property
    def run_ids(self) -> list[str]:
        """The note's run id(s), from its Run field or a legacy `Run id:` line."""
        found = _TICKED.findall(self.field("Run"))
        for line in self.text.splitlines():
            legacy = _LEGACY_RUN.match(line)
            if legacy:
                found.append(legacy.group(1))
        return found

    @property
    def study(self) -> str:
        ticked = _TICKED.findall(self.field("Study"))
        return ticked[0] if ticked else ""

    @property
    def idea(self) -> int:
        """The idea number it tests (0: none)."""
        found = re.search(r"#(\d+)", self.field("Idea"))
        return int(found.group(1)) if found else 0

    @property
    def candidates(self) -> list[str]:
        return _TICKED.findall(self.field("Candidates"))

    @property
    def baselines(self) -> list[str]:
        return _TICKED.findall(self.field("Baselines"))

    @property
    def supports(self) -> list[str]:
        """A tuning note's fleet supports."""
        return _TICKED.findall(self.field("Supports"))

    @property
    def verdict(self) -> str:
        return self.field("Verdict").split()[0] if self.field("Verdict") else ""

    def section(self, heading: str) -> str:
        """A section's body, without its heading ("" when absent)."""
        lines = self.text.splitlines()
        start, end = _section_range(lines, heading)
        return "\n".join(lines[start + 1 : end]).strip() if start >= 0 else ""


def notes_dir(notebook: str) -> str:
    return os.path.join(notebook, DIR)


def all_notes(notebook: str) -> list[Note]:
    """Every note, by number (the template is not a note)."""
    folder = notes_dir(notebook)
    if not os.path.isdir(folder):
        return []
    out = []
    for name in sorted(os.listdir(folder)):
        found = _NAME.match(name)
        if found:
            path = os.path.join(folder, name)
            with open(path, encoding="utf-8") as f:
                out.append(Note(int(found.group(1)), found.group(2), path, f.read()))
    return out


def find(notebook: str, ref: str) -> Note:
    """The note `ref` names: its number (`7`, `0007`) or its file stem.

    Raises:
        NoteError: no such note.
    """
    for note in all_notes(notebook):
        stem = f"{note.number:04d}-{note.slug}"
        if ref in (stem, f"{note.number:04d}") or (
            ref.isdigit() and int(ref) == note.number
        ):
            return note
    raise NoteError(f"no note {ref!r} in {notes_dir(notebook)}")


def next_number(notebook: str) -> int:
    return max((n.number for n in all_notes(notebook)), default=0) + 1


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48].strip("-")
    if not slug:
        raise NoteError(f"can't make a note name out of {text!r}")
    return slug


def ticked(text: str) -> list[str]:
    """The `backticked` names in a field's value."""
    return _TICKED.findall(text)


def ticks(names: list[str]) -> str:
    return ", ".join(f"`{n}`" for n in names) or "—"


@dataclasses.dataclass(frozen=True)
class Draft:
    """What a new note starts with."""

    kind: str
    title: str
    slug: str
    hypothesis: str
    candidates: list[str]
    baselines: list[str]
    idea: int  # 0: none


def render_new(number: int, draft: Draft, today: datetime.date) -> str:
    """A planned note's text."""
    if draft.kind not in KINDS:
        raise NoteError(f"a note is one of {', '.join(KINDS)}")
    if not draft.hypothesis.strip():
        raise NoteError("a note needs its hypothesis before it runs")
    fields = [
        ("Date", today.isoformat()),
        ("Status", PLANNED),
        ("Kind", draft.kind),
        ("Idea", f"#{draft.idea}" if draft.idea else "—"),
        ("Candidates", ticks(draft.candidates)),
        ("Baselines", ticks(draft.baselines)),
        ("Run" if draft.kind == EVALUATION else "Study", "—"),
        ("Verdict", "—"),
    ]
    out = [f"# {number:04d}: {draft.title}", ""]
    out += [f"- **{k}:** {v}" for k, v in fields]
    for heading in SECTIONS:
        body = draft.hypothesis.strip() if heading == "Hypothesis" else "—"
        out += ["", f"## {heading}", "", body]
    return "\n".join(out) + "\n"


def create(notebook: str, draft: Draft, today: datetime.date) -> Note:
    """Write a new planned note, numbered after the last one."""
    number = next_number(notebook)
    os.makedirs(notes_dir(notebook), exist_ok=True)
    path = os.path.join(notes_dir(notebook), f"{number:04d}-{draft.slug}.md")
    text = render_new(number, draft, today)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return Note(number, draft.slug, path, text)


def with_field(text: str, key: str, value: str) -> str:
    """`text` with the header field `key` set (added after the last field if new)."""
    lines = text.splitlines()
    last = -1
    for i, line in enumerate(lines):
        found = _FIELD.match(line)
        if found:
            last = i
            if found.group(1) == key:
                lines[i] = f"- **{key}:** {value}"
                return "\n".join(lines) + "\n"
    if last < 0:
        raise NoteError("the note has no header fields")
    lines.insert(last + 1, f"- **{key}:** {value}")
    return "\n".join(lines) + "\n"


def _section_range(lines: list[str], heading: str) -> tuple[int, int]:
    start = -1
    for i, line in enumerate(lines):
        if line.startswith("## "):
            if start >= 0:
                return start, i
            if line[3:].strip() == heading:
                start = i
    return (start, len(lines)) if start >= 0 else (-1, -1)


def with_section(text: str, heading: str, body: str) -> str:
    """`text` with the section `heading` holding `body` (appended if new)."""
    lines = text.splitlines()
    start, end = _section_range(lines, heading)
    block = [f"## {heading}", "", body.strip()]
    if start < 0:
        lines += ["", *block]
    else:
        lines[start:end] = [*block, ""] if end < len(lines) else block
    return "\n".join(lines).rstrip("\n") + "\n"


def save(note: Note, text: str) -> Note:
    with open(note.path, "w", encoding="utf-8") as f:
        f.write(text)
    return dataclasses.replace(note, text=text)


def record_command(note: Note, command: str) -> Note:
    return save(note, with_section(note.text, "Command", f"```bash\n{command}\n```"))


def record_results(note: Note, ref_key: str, ref: str, results: str) -> Note:
    """Write a finished run's (or study's) results in; the note becomes `run`."""
    text = with_field(note.text, ref_key, f"`{ref}`")
    text = with_field(text, "Status", RUN)
    return save(note, with_section(text, "Results", results))


def record_verdict(note: Note, verdict: str, summary: str, analysis: str) -> Note:
    """Close the note with its verdict; it becomes `analyzed`.

    Raises:
        NoteError: an unknown verdict, an empty summary, or a note without results.
    """
    if verdict not in VERDICTS:
        raise NoteError(f"a verdict is one of {', '.join(VERDICTS)}")
    if not summary.strip():
        raise NoteError("a verdict needs its summary")
    if note.status == PLANNED:
        raise NoteError(f"note {note.number:04d} has no results yet: evaluate it first")
    text = with_field(note.text, "Verdict", verdict)
    text = with_field(text, "Status", ANALYZED)
    if analysis.strip():
        text = with_section(text, "Analysis", analysis)
    return save(
        note, with_section(text, "Verdict", f"**{verdict}**. {summary.strip()}")
    )
