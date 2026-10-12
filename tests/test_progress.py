"""janken/progress.py and batched play: bars follow the settings, batches don't
change results."""

import contextlib
import io
import os

import pytest

from janken import progress, settings
from janken.engine import play_in_batches, play_pairs, registry
from janken.spec import make_spec

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def bot(stem: str) -> str:
    return registry.find(os.path.join(ROOT, "bots"), stem)


class TestProgress:
    def test_bars_are_off_off_a_terminal(self, monkeypatch: pytest.MonkeyPatch) -> None:
        err = io.StringIO()
        monkeypatch.delenv(settings.PROGRESS_ENV, raising=False)
        with contextlib.redirect_stderr(err):
            assert not progress.enabled()
            with progress.bar(3, "x", "step") as bar:
                bar.update(3)
        assert err.getvalue() == ""

    def test_bars_show_when_turned_on(self, monkeypatch: pytest.MonkeyPatch) -> None:
        err = io.StringIO()
        monkeypatch.setenv(settings.PROGRESS_ENV, "on")
        with contextlib.redirect_stderr(err):
            with progress.bar(2, "steps", "step") as bar:
                bar.update(2)
            progress.log("a line")
        assert "steps" in err.getvalue()
        assert "a line" in err.getvalue()


class TestInterrupted:
    def test_ctrl_c_is_told_apart_from_errors(self) -> None:
        assert progress.interrupted(KeyboardInterrupt())
        try:
            try:
                raise KeyboardInterrupt
            except KeyboardInterrupt as cause:
                raise SystemError("returned a result with an exception set") from cause
        except SystemError as wrapped:
            assert progress.interrupted(wrapped)
        assert not progress.interrupted(SystemError("a real one"))


class TestBatches:
    def test_batches_cover_every_match_and_change_nothing(self) -> None:
        pairs = [(make_spec(bot("cycler_v1")), make_spec(bot("wsls_v1")))] * 5
        seeds = [1, 2, 3, 4, 5]
        whole = play_pairs(pairs, 8, seeds)
        spans = []
        batched = []
        for span, results in play_in_batches(pairs, 8, seeds, 2):
            spans.append(span)
            batched += results
        assert spans == [range(2), range(2, 4), range(4, 5)]
        assert [m.moves for m in batched] == [m.moves for m in whole]
