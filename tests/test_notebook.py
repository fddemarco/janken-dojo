"""janken/notebook: the backlog, notes, insights and the lab's next step."""

import dataclasses
import datetime
import os
import pathlib
import shutil

import pytest

from janken.notebook import ideas, insights, notes, state

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
RESEARCH = os.path.join(ROOT, "research")
TODAY = datetime.date(2026, 10, 10)
FIELD = frozenset({"a_v1", "b_v1"})  # the drafts' bots are not in it


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class Notebook:
    """A copy of the real ideas.md and insights.md, and no notes."""

    @pytest.fixture(autouse=True)
    def _notebook(self, tmp_path: pathlib.Path) -> None:
        self.dir = str(tmp_path)
        for name in (ideas.FILE, insights.FILE):
            shutil.copy(os.path.join(RESEARCH, name), self.dir)

    def draft(self, **changes: object) -> notes.Draft:
        base = notes.Draft(
            kind=notes.EVALUATION,
            title="a vs b",
            slug="a-vs-b",
            hypothesis="a beats b by 3 pts",
            candidates=["bots/a.yaml"],
            baselines=["bots/b.yaml"],
            idea=2,
        )
        return dataclasses.replace(base, **changes)


class TestIdeas(Notebook):
    def test_the_real_backlog_round_trips_byte_for_byte(self) -> None:
        text = read(os.path.join(RESEARCH, ideas.FILE))
        backlog = ideas.parse(text)
        assert backlog.render() == text
        assert len(backlog.ideas) >= 20
        assert backlog.get(2).priority == "P1"

    def test_add_start_and_close(self) -> None:
        # The real backlog may hold ideas in progress; start from one without any.
        backlog = ideas.load(self.dir)
        for i in backlog.ideas:
            if i.state == ideas.IN_PROGRESS:
                backlog = backlog.set_status(i.number, ideas.OPEN)
        before: list[ideas.Idea] = list(backlog.ideas)
        last = max(i.number for i in backlog.ideas)
        backlog, idea = backlog.add("**New**: try it", "P2", "a hunch")
        assert idea.number == last + 1
        assert backlog.ideas[-1] == idea
        backlog = backlog.set_status(idea.number, ideas.IN_PROGRESS)
        assert ideas.ranked(backlog)[0].number == idea.number  # in progress first
        closed = backlog.set_status(idea.number, ideas.linked(ideas.DONE, 7, "x"))
        assert closed.get(idea.number).state == ideas.DONE
        assert "experiments/0007-x.md" in closed.get(idea.number).status
        untouched = [i for i in closed.ideas if i.number != idea.number]
        assert untouched == before

    def test_bad_ideas_are_refused(self) -> None:
        backlog = ideas.load(self.dir)
        with pytest.raises(ideas.IdeaError):
            backlog.add("x", "P9", "y")
        with pytest.raises(ideas.IdeaError):
            backlog.add("a | b", "P1", "y")
        with pytest.raises(ideas.IdeaError):
            backlog.get(999)


class TestNotes(Notebook):
    def test_a_note_goes_planned_run_analyzed(self) -> None:
        note = notes.create(self.dir, self.draft(), TODAY)
        assert (note.number, note.status, note.kind) == (1, notes.PLANNED, "evaluation")
        assert note.candidates == ["bots/a.yaml"]
        assert note.baselines == ["bots/b.yaml"]
        assert note.idea == 2
        assert note.section("Hypothesis") == "a beats b by 3 pts"
        with pytest.raises(notes.NoteError):
            notes.record_verdict(note, "keep", "too soon", "")
        note = notes.record_results(note, "Run", "run-1", "| table |")
        assert (note.status, note.run_ids) == (notes.RUN, ["run-1"])
        assert note.section("Results") == "| table |"
        note = notes.record_verdict(note, "keep", "it won", "the long story")
        assert (note.status, note.verdict) == (notes.ANALYZED, "keep")
        assert note.section("Analysis") == "the long story"
        assert notes.find(self.dir, "1").text == note.text
        assert notes.find(self.dir, "0001-a-vs-b").number == 1
        assert notes.next_number(self.dir) == 2

    def test_sections_and_fields_are_rewritten_in_place(self) -> None:
        text = notes.render_new(3, self.draft(), TODAY)
        once = notes.with_section(text, "Results", "first")
        twice = notes.with_section(once, "Results", "second")
        assert twice == once.replace("first", "second")
        assert "## Verdict" in twice
        added = notes.with_field(twice, "Supports", "`bots/c.yaml`")
        assert "- **Supports:** `bots/c.yaml`" in added

    def test_the_real_notes_read_back(self) -> None:
        found = notes.all_notes(RESEARCH)
        assert len(found) >= 6
        assert all(n.status == notes.ANALYZED for n in found[:6])
        sims3 = next(n for n in found if n.slug == "smartbot-sims3")
        assert sims3.run_ids == ["20261010-001100_0005-smartbot-sims3"]

    def test_bad_notes_are_refused(self) -> None:
        with pytest.raises(notes.NoteError):
            notes.render_new(1, self.draft(hypothesis=" "), TODAY)
        with pytest.raises(notes.NoteError):
            notes.find(self.dir, "42")
        note = notes.record_results(
            notes.create(self.dir, self.draft(), TODAY), "Run", "r", "x"
        )
        with pytest.raises(notes.NoteError):
            notes.record_verdict(note, "maybe", "s", "")


class TestInsights(Notebook):
    def test_add_goes_first_and_supersede_strikes(self) -> None:
        text = read(insights.path(self.dir))
        before = insights.titles(text)
        entry = insights.Insight(
            TODAY, "Sampling beats argmax", "experiments/0009-x.md", "m", "i"
        )
        added = insights.add(text, entry)
        assert insights.titles(added) == [f"{TODAY}: Sampling beats argmax", *before]
        assert insights.cites(added, "0009-x")
        struck = insights.supersede(
            added, "Sampling beats", "[0010](experiments/0010-y.md)"
        )
        assert "~~Sampling beats argmax~~ (superseded by" in struck
        with pytest.raises(insights.InsightError):
            insights.supersede(added, "no such finding", "x")
        with pytest.raises(insights.InsightError):
            insights.Insight(TODAY, "two\nlines", "e", "m", "i").render()


class TestNextStep(Notebook):
    def test_finish_what_is_started_before_starting_anything(self) -> None:
        backlog = ideas.load(self.dir)
        text = read(insights.path(self.dir))
        planned = notes.create(self.dir, self.draft(), TODAY)
        assert state.next_step([planned], backlog, {}, text, FIELD).action == "run"
        ran = notes.record_results(planned, "Run", "r1", "x")
        assert (
            state.next_step([ran], backlog, {"r1": "complete"}, text, FIELD).action
            == "verdict"
        )
        assert (
            state.next_step([ran], backlog, {"r1": "interrupted"}, text, FIELD).action
            == "resume"
        )
        kept = notes.record_verdict(ran, "keep", "won", "")
        assert state.next_step([kept], backlog, {}, text, FIELD).action == "learn"
        dropped = notes.record_verdict(ran, "drop", "lost", "")
        step = state.next_step([dropped], backlog, {}, text, FIELD)
        assert step.action == "build"
        assert f"--idea {ideas.ranked(backlog)[0].number}" in step.command
        empty = ideas.parse(
            "| # | idea | priority | status | motivation |\n|---|---|---|---|---|\n"
        )
        assert state.next_step([], empty, {}, text, FIELD).action == "ideate"

    def test_a_kept_bot_without_a_version_is_classified_before_learning(
        self,
    ) -> None:
        backlog = ideas.load(self.dir)
        text = read(insights.path(self.dir))
        ran = notes.record_results(
            notes.create(self.dir, self.draft(), TODAY), "Run", "r1", "x"
        )
        kept = notes.record_verdict(ran, "keep", "won", "")
        field = {"a", "b_v1"}
        step = state.next_step([kept], backlog, {}, text, field)
        assert (step.action, step.command) == (
            "classify",
            "janken species classify 0001",
        )
        done = notes.record_species(kept, "`a_v1` (new species)", "**new**.")
        assert done.species == "`a_v1` (new species)"
        assert state.next_step([done], backlog, {}, text, field).action == "learn"
        dropped = notes.record_verdict(ran, "drop", "lost", "")
        assert state.next_step([dropped], backlog, {}, text, field).action == "build"
