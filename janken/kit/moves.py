"""Move codes, and helpers for histories that may hold invalid moves.

A move is 0/1/2 = rock/paper/scissors, so the move that beats x is `beats(x)`.
A bot may also return `INVALID` (it loses that round; the third one forfeits the
match) or `CRASH` (it forfeits at once). Opponents see an invalid move as
`INVALID` in their history.

Never index a table with `INVALID`: numba does not bounds-check, so every read
of a history entry that may be invalid is guarded first.

The models only see the valid rounds. The pipeline keeps that valid-only history,
and the count of each side's invalid moves, in the bot's state as rounds arrive
(janken/kit/pipeline.py), so no round is scanned twice in a match.
"""

import numpy as np

from . import codes as c
from .jit import kernel

ROCK, PAPER, SCISSORS = 0, 1, 2
INVALID = 3
CRASH = -1


@kernel
def beats(x):
    """The move that beats x."""
    return (x + 1) % 3


@kernel
def scan_invalid(
    at: int, i: np.ndarray, my: np.ndarray, opp: np.ndarray, n: int
) -> None:
    """Count the invalid moves of the rounds not yet scanned, up to n, into the
    history cells i[at:at + VIEW_CELLS] (each round is scanned once a match)."""
    for t in range(i[at + 1], n):
        if opp[t] == INVALID:
            i[at + 2] += 1
        if my[t] == INVALID:
            i[at + 3] += 1
    i[at + 1] = max(i[at + 1], n)


@kernel
def invalid_seen(at: int, i: np.ndarray, side: int) -> bool:
    """Whether the scanned history holds an invalid move of the opponent (or of
    either side, with BOTH)."""
    return i[at + 2] > 0 or (side == c.BOTH and i[at + 3] > 0)
