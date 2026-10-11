"""janken/notebook: the backlog, notes, insights and the lab's next step."""

import dataclasses
import datetime
import os
import shutil
import tempfile
import unittest

from janken.notebook import ideas, insights, notes, state

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
RESEARCH = os.path.join(ROOT, "research")
TODAY = datetime.date(2026, 10, 10)


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class Notebook(unittest.TestCase):
    """A copy of the real ideas.md and insights.md, and no notes."""

    def setUp(self) -> None:
        self.dir = tempfile.mkdtemp()
        for name in (ideas.FILE, insights.FILE):
            shutil.copy(os.path.join(RESEARCH, name), self.dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.dir)

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


class IdeasTest(Notebook):
    def test_the_real_backlog_round_trips_byte_for_byte(self) -> None:
        text = read(os.path.join(RESEARCH, ideas.FILE))
        backlog = ideas.parse(text)
        self.assertEqual(backlog.render(), text)
        self.assertGreaterEqual(len(backlog.ideas), 20)
        self.assertEqual(backlog.get(2).priority, "P1")

    def test_add_start_and_close(self) -> None:
        # The real backlog may hold ideas in progress; start from one without any.
        backlog = ideas.load(self.dir)
        for i in backlog.ideas:
            if i.state == ideas.IN_PROGRESS:
                backlog = backlog.set_status(i.number, ideas.OPEN)
        before: list[ideas.Idea] = list(backlog.ideas)
        last = max(i.number for i in backlog.ideas)
        backlog, idea = backlog.add("**New**: try it", "P2", "a hunch")
        self.assertEqual(idea.number, last + 1)
        self.assertEqual(backlog.ideas[-1], idea)
        backlog = backlog.set_status(idea.number, ideas.IN_PROGRESS)
        self.assertEqual(
            ideas.ranked(backlog)[0].number, idea.number
        )  # in progress first
        closed = backlog.set_status(idea.number, ideas.linked(ideas.DONE, 7, "x"))
        self.assertEqual(closed.get(idea.number).state, ideas.DONE)
        self.assertIn("experiments/0007-x.md", closed.get(idea.number).status)
        untouched = [i for i in closed.ideas if i.number != idea.number]
        self.assertEqual(untouched, before)

    def test_bad_ideas_are_refused(self) -> None:
        backlog = ideas.load(self.dir)
        with self.assertRaises(ideas.IdeaError):
            backlog.add("x", "P9", "y")
        with self.assertRaises(ideas.IdeaError):
            backlog.add("a | b", "P1", "y")
        with self.assertRaises(ideas.IdeaError):
            backlog.get(999)


class NotesTest(Notebook):
    def test_a_note_goes_planned_run_analyzed(self) -> None:
        note = notes.create(self.dir, self.draft(), TODAY)
        self.assertEqual(
            (note.number, note.status, note.kind), (1, notes.PLANNED, "evaluation")
        )
        self.assertEqual(note.candidates, ["bots/a.yaml"])
        self.assertEqual(note.baselines, ["bots/b.yaml"])
        self.assertEqual(note.idea, 2)
        self.assertEqual(note.section("Hypothesis"), "a beats b by 3 pts")
        with self.assertRaises(notes.NoteError):
            notes.record_verdict(note, "keep", "too soon", "")
        note = notes.record_results(note, "Run", "run-1", "| table |")
        self.assertEqual((note.status, note.run_ids), (notes.RUN, ["run-1"]))
        self.assertEqual(note.section("Results"), "| table |")
        note = notes.record_verdict(note, "keep", "it won", "the long story")
        self.assertEqual((note.status, note.verdict), (notes.ANALYZED, "keep"))
        self.assertEqual(note.section("Analysis"), "the long story")
        self.assertEqual(notes.find(self.dir, "1").text, note.text)
        self.assertEqual(notes.find(self.dir, "0001-a-vs-b").number, 1)
        self.assertEqual(notes.next_number(self.dir), 2)

    def test_sections_and_fields_are_rewritten_in_place(self) -> None:
        text = notes.render_new(3, self.draft(), TODAY)
        once = notes.with_section(text, "Results", "first")
        twice = notes.with_section(once, "Results", "second")
        self.assertEqual(twice, once.replace("first", "second"))
        self.assertIn("## Verdict", twice)
        added = notes.with_field(twice, "Supports", "`bots/c.yaml`")
        self.assertIn("- **Supports:** `bots/c.yaml`", added)

    def test_the_real_notes_read_back(self) -> None:
        found = notes.all_notes(RESEARCH)
        self.assertGreaterEqual(len(found), 6)
        self.assertTrue(all(n.status == notes.ANALYZED for n in found[:6]))
        sims3 = next(n for n in found if n.slug == "smartbot-sims3")
        self.assertEqual(sims3.run_ids, ["20261010-001100_0005-smartbot-sims3"])

    def test_bad_notes_are_refused(self) -> None:
        with self.assertRaises(notes.NoteError):
            notes.render_new(1, self.draft(hypothesis=" "), TODAY)
        with self.assertRaises(notes.NoteError):
            notes.find(self.dir, "42")
        note = notes.record_results(
            notes.create(self.dir, self.draft(), TODAY), "Run", "r", "x"
        )
        with self.assertRaises(notes.NoteError):
            notes.record_verdict(note, "maybe", "s", "")


class InsightsTest(Notebook):
    def test_add_goes_first_and_supersede_strikes(self) -> None:
        text = read(insights.path(self.dir))
        before = insights.titles(text)
        entry = insights.Insight(
            TODAY, "Sampling beats argmax", "experiments/0009-x.md", "m", "i"
        )
        added = insights.add(text, entry)
        self.assertEqual(
            insights.titles(added), [f"{TODAY}: Sampling beats argmax", *before]
        )
        self.assertTrue(insights.cites(added, "0009-x"))
        struck = insights.supersede(
            added, "Sampling beats", "[0010](experiments/0010-y.md)"
        )
        self.assertIn("~~Sampling beats argmax~~ (superseded by", struck)
        with self.assertRaises(insights.InsightError):
            insights.supersede(added, "no such finding", "x")
        with self.assertRaises(insights.InsightError):
            insights.Insight(TODAY, "two\nlines", "e", "m", "i").render()


class NextStepTest(Notebook):
    def test_finish_what_is_started_before_starting_anything(self) -> None:
        backlog = ideas.load(self.dir)
        text = read(insights.path(self.dir))
        planned = notes.create(self.dir, self.draft(), TODAY)
        self.assertEqual(state.next_step([planned], backlog, {}, text).action, "run")
        ran = notes.record_results(planned, "Run", "r1", "x")
        self.assertEqual(
            state.next_step([ran], backlog, {"r1": "complete"}, text).action, "verdict"
        )
        self.assertEqual(
            state.next_step([ran], backlog, {"r1": "interrupted"}, text).action,
            "resume",
        )
        kept = notes.record_verdict(ran, "keep", "won", "")
        self.assertEqual(state.next_step([kept], backlog, {}, text).action, "learn")
        dropped = notes.record_verdict(ran, "drop", "lost", "")
        step = state.next_step([dropped], backlog, {}, text)
        self.assertEqual(step.action, "build")
        self.assertIn(f"--idea {ideas.ranked(backlog)[0].number}", step.command)
        empty = ideas.parse(
            "| # | idea | priority | status | motivation |\n|---|---|---|---|---|\n"
        )
        self.assertEqual(state.next_step([], empty, {}, text).action, "ideate")


if __name__ == "__main__":
    unittest.main()
