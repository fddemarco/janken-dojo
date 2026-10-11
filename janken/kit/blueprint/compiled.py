"""A compiled blueprint: its state sizes and the arrays the pipeline reads."""

from typing import NamedTuple

import numpy as np

from .. import codes as c


class Compiled(NamedTuple):
    """A compiled blueprint: `state, spec, knobs = blueprint.compile(defaults)`.

    `state` is (f size, fixed i size, per-round i slots): every match, the bot gets
    fresh arrays, its i grown by one slot of rounds + 1 cells per per-round slot
    (the per-match workspace: the valid-only history and the match indexes).
    """

    state: tuple[int, int, int]
    spec: np.ndarray
    knobs: np.ndarray

    def new_state(self, rounds: int) -> tuple[np.ndarray, np.ndarray]:
        """Fresh (f, i) for a match of `rounds` rounds (the engine generates the
        same allocation, compiled; see janken/engine/build.py)."""
        f_size, i_size, per_round = self.state
        stride = rounds + 1
        i = np.zeros(i_size + per_round * stride, np.int64)
        at = int(self.spec[c.H_ROUNDS_I])
        i[at] = stride
        i[at + 1] = i_size
        return np.zeros(f_size, np.float64), i
