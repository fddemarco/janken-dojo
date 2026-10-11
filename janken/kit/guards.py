"""Guards, compiled: answer the round before any model runs, or PASS.

They see the raw history, invalid moves included, and run in blueprint order;
the first to answer plays.
"""

import random

import numpy as np

from . import codes as c
from .jit import kernel
from .moves import CRASH, INVALID, invalid_seen


@kernel
def _invalid_seen(
    spec: np.ndarray,
    i: np.ndarray,
    scope: int,
    side: int,
    my: np.ndarray,
    opp: np.ndarray,
    n: int,
) -> bool:
    if scope == c.LAST:
        if n == 0:
            return False
        return opp[n - 1] == INVALID or (side == c.BOTH and my[n - 1] == INVALID)
    return invalid_seen(spec[c.H_VIEW_I], i, side)


@kernel
def apply(
    spec: np.ndarray,
    g: int,
    i: np.ndarray,
    kn: np.ndarray,
    my: np.ndarray,
    opp: np.ndarray,
    n: int,
) -> int:
    """Guard record g's move for round n, or PASS."""
    kind = spec[g + c.R_KIND]
    if kind == c.G_OPENING:
        if n < spec[g + c.R_A]:
            move = spec[g + c.R_B]
            return random.randrange(3) if move == c.RANDOM_MOVE else move
        return c.PASS
    if kind == c.G_NOISE:
        if random.random() < kn[spec[g + c.R_K]]:
            return random.randrange(3)
        return c.PASS
    if _invalid_seen(spec, i, spec[g + c.R_B], spec[g + c.R_C], my, opp, n):
        return CRASH if spec[g + c.R_A] == c.CRASH_ACTION else random.randrange(3)
    return c.PASS
