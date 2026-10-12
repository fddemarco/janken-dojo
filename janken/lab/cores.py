"""Species cores kept on disk: a bot's predictions on a set of histories.

A core (janken/lab/workflows.py `core`) depends only on the bot, the code that
replays it and the histories, so it is computed once and read back by every later
`species census`, `compare` and `classify`. Its file is named after a hash of all
three:

    the bot's transitive source hash (janken/library.py: editing a bot, or a bot
        it names, changes it)
    the replay code: janken/kit, janken/engine (janken/_numba_cache.py `digest`)
        and the predictor modules
    the histories' moves and seeds

so a stale core is never read; it is just never asked for again.
"""

import functools
import hashlib
import inspect
import os
import tempfile
from collections.abc import Callable

import numpy as np

from .. import _numba_cache, library
from . import predict, predict_kernel, predictor
from .dataset import Sequences

Compute = Callable[[str, Sequences], np.ndarray]


@functools.cache
def code_digest() -> str:
    """A hash of the code a core depends on: the kit, the engine and the predictor."""
    h = hashlib.sha256(_numba_cache.digest().encode())
    for module in (predict, predict_kernel, predictor):
        h.update(inspect.getsource(module).encode())
    return h.hexdigest()


def histories_digest(seqs: Sequences) -> str:
    """A hash of the histories a core is computed on: their moves and seeds."""
    h = hashlib.sha256()
    for array in (seqs.starts, seqs.seeds, seqs.p1, seqs.p2):
        h.update(np.ascontiguousarray(array, np.int64).tobytes())
    return h.hexdigest()


def key(path: str, seqs: Sequences) -> str:
    """The name of the bot's core on `seqs`."""
    parts = (library.source_hash(path), code_digest(), histories_digest(seqs))
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:32]


class CoreCache:
    """Cores in `directory`, computed by `compute` when missing."""

    def __init__(self, directory: str, compute: Compute) -> None:
        self.directory: str = directory
        self._compute: Compute = compute

    def file(self, path: str, seqs: Sequences) -> str:
        """Where the bot's core on `seqs` is kept."""
        return os.path.join(self.directory, key(path, seqs) + ".npy")

    def core(self, path: str, seqs: Sequences) -> np.ndarray:
        """The bot's core on `seqs`: read back, or computed and kept."""
        target = self.file(path, seqs)
        if os.path.isfile(target):
            return np.load(target)
        found = self._compute(path, seqs)
        os.makedirs(self.directory, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=self.directory, suffix=".npy", delete=False
        ) as tmp:
            np.save(tmp, found)
        os.replace(tmp.name, target)  # atomic: a reader never sees half a file
        return found
