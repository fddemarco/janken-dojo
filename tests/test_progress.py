"""janken/progress.py and batched play: bars follow the settings, batches don't
change results."""

import contextlib
import io
import os
import unittest
from unittest import mock

from janken import progress, settings
from janken.engine import play_in_batches, play_pairs
from janken.spec import make_spec

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def bot(stem: str) -> str:
    return os.path.join(ROOT, "bots", stem + ".yaml")


class ProgressTest(unittest.TestCase):
    def test_bars_are_off_off_a_terminal(self) -> None:
        err = io.StringIO()
        with (
            contextlib.redirect_stderr(err),
            mock.patch.dict(os.environ, {}, clear=False),
        ):
            os.environ.pop(settings.PROGRESS_ENV, None)
            self.assertFalse(progress.enabled())
            with progress.bar(3, "x", "step") as bar:
                bar.update(3)
        self.assertEqual(err.getvalue(), "")

    def test_bars_show_when_turned_on(self) -> None:
        err = io.StringIO()
        with (
            contextlib.redirect_stderr(err),
            mock.patch.dict(os.environ, {settings.PROGRESS_ENV: "on"}),
        ):
            with progress.bar(2, "steps", "step") as bar:
                bar.update(2)
            progress.log("a line")
        self.assertIn("steps", err.getvalue())
        self.assertIn("a line", err.getvalue())


class InterruptedTest(unittest.TestCase):
    def test_ctrl_c_is_told_apart_from_errors(self) -> None:
        self.assertTrue(progress.interrupted(KeyboardInterrupt()))
        try:
            try:
                raise KeyboardInterrupt
            except KeyboardInterrupt as cause:
                raise SystemError("returned a result with an exception set") from cause
        except SystemError as wrapped:
            self.assertTrue(progress.interrupted(wrapped))
        self.assertFalse(progress.interrupted(SystemError("a real one")))


class BatchesTest(unittest.TestCase):
    def test_batches_cover_every_match_and_change_nothing(self) -> None:
        pairs = [(make_spec(bot("cycler")), make_spec(bot("wsls")))] * 5
        seeds = [1, 2, 3, 4, 5]
        whole = play_pairs(pairs, 8, seeds)
        spans = []
        batched = []
        for span, results in play_in_batches(pairs, 8, seeds, 2):
            spans.append(span)
            batched += results
        self.assertEqual(spans, [range(2), range(2, 4), range(4, 5)])
        self.assertEqual([m.moves for m in batched], [m.moves for m in whole])


if __name__ == "__main__":
    unittest.main()
