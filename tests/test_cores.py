"""janken/lab/cores.py: species cores computed once, kept on disk."""

import dataclasses
import os
import pathlib

import numpy as np
import pytest

from janken.lab import cores
from janken.lab.dataset import Sequences

LAST = """\
defaults: {OF: OPP}
blueprint:
  core: {Heuristic: {signal: {LastMove: {of: $OF}}, rotation: BEAT}}
"""
BOARD = """\
blueprint:
  core:
    Bandit:
      predictors: [{bot: last, rotations: [COPY, BEAT]}]
      scorer: {DecayedNet: {decay: 0.9}}
      selector: Greedy
"""
SEQS = Sequences(
    match_ids=np.arange(2, dtype=np.int64),
    seeds=np.array([3, 4], np.int64),
    starts=np.array([0, 3, 5], np.int64),
    p1=np.array([0, 1, 2, 0, 1], np.int64),
    p2=np.array([2, 2, 1, 0, 0], np.int64),
    p1_index=np.zeros(2, np.int64),
    p2_index=np.ones(2, np.int64),
    labels=["a", "b"],
)


class Counting:
    """A core computer that records every bot it computes."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def __call__(self, path: str, seqs: Sequences) -> np.ndarray:
        self.calls.append(path)
        return np.vstack([seqs.p1, seqs.p2]) + len(self.calls)


class TestCoreCache:
    @pytest.fixture(autouse=True)
    def _bots(self, tmp_path: pathlib.Path) -> None:
        self.root: str = str(tmp_path / "bots")
        self.last: str = self.write("blocks/last", LAST)
        self.board: str = self.write("l2/board", BOARD)
        self.computed: Counting = Counting()
        self.cache: cores.CoreCache = cores.CoreCache(
            str(tmp_path / "cores"), self.computed
        )

    def write(self, name: str, text: str) -> str:
        path = os.path.join(self.root, name + ".yaml")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_a_core_is_computed_once_and_read_back(self) -> None:
        first = self.cache.core(self.board, SEQS)
        again = self.cache.core(self.board, SEQS)
        assert self.computed.calls == [self.board]
        assert np.array_equal(first, again)
        assert again.dtype == first.dtype

    def test_editing_a_named_bot_recomputes(self) -> None:
        before = self.cache.file(self.board, SEQS)
        self.write("blocks/last", LAST.replace("BEAT", "COPY"))
        assert self.cache.file(self.board, SEQS) != before

    def test_other_histories_get_their_own_core(self) -> None:
        reseeded = dataclasses.replace(SEQS, seeds=np.array([3, 5], np.int64))
        replayed = dataclasses.replace(SEQS, p2=np.array([2, 2, 1, 0, 1], np.int64))
        files = {self.cache.file(self.board, s) for s in (SEQS, reseeded, replayed)}
        assert len(files) == 3

    def test_each_bot_has_its_own_core(self) -> None:
        assert self.cache.file(self.last, SEQS) != self.cache.file(self.board, SEQS)
