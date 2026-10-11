"""The predictor kernel: a bot's core replayed over stored matches, compiled.

`predict_batch` replays every match from both sides, in parallel: from p1's side
the bot sees p1's moves as its own and predicts p2's next move, and the other way
round, so one match gives two prediction sequences. At round n the bot sees
rounds 0..n-1 only, exactly as in a match, and its move m implies the prediction
"the opponent plays the move m beats".

Unlike the referee (janken/engine/kernel.py), the bot's compiled blueprint comes
in as arguments, not as generated globals, so one compiled kernel serves every
bot and every parameter set.
"""

import random

import numpy as np
from numba import prange

from ..kit import codes as c
from ..kit.jit import kernel, parallel_kernel
from ..kit.pipeline import play

NO_PREDICTION = -1


@kernel
def implied_prediction(move: int) -> int:
    """The opponent move that `move` beats, or NO_PREDICTION for a non-move."""
    if 0 <= move <= 2:
        return (move + 2) % 3
    return NO_PREDICTION


@kernel
def predict_side(
    spec: np.ndarray,
    knobs: np.ndarray,
    state: np.ndarray,
    prm: np.ndarray,
    my: np.ndarray,
    opp: np.ndarray,
    out: np.ndarray,
) -> None:
    """Predict opp[n] from my[:n] and opp[:n], for every round n, into out[n].

    The bot's fresh state is allocated as Compiled.new_state does."""
    n = my.size
    f = np.zeros(state[0], np.float64)
    i = np.zeros(state[1] + state[2] * (n + 1), np.int64)
    at = spec[c.H_ROUNDS_I]
    i[at] = n + 1
    i[at + 1] = state[1]
    for r in range(n):
        out[r] = implied_prediction(play(f, i, prm, my, opp, r, spec, knobs))


@parallel_kernel
def predict_batch(
    spec: np.ndarray,
    knobs: np.ndarray,
    state: np.ndarray,
    prm: np.ndarray,
    p1: np.ndarray,
    p2: np.ndarray,
    starts: np.ndarray,
    seeds: np.ndarray,
) -> np.ndarray:
    """Predictions of every stored move: int64[2, rounds], row 0 for p1's moves
    (made from p2's side), row 1 for p2's. Match k's rounds are
    starts[k]:starts[k + 1]; its side s (0: p1's) is seeded with seeds[2k + s]."""
    out = np.empty((2, p1.size), np.int64)
    for t in prange(2 * (starts.size - 1)):
        k = t // 2
        a = starts[k]
        b = starts[k + 1]
        random.seed(int(seeds[t]))
        if t % 2 == 0:
            predict_side(spec, knobs, state, prm, p1[a:b], p2[a:b], out[1, a:b])
        else:
            predict_side(spec, knobs, state, prm, p2[a:b], p1[a:b], out[0, a:b])
    return out
