"""NaiveBayes, compiled: TPI-lite, one signal that combines its ensemble's others.

Testing Please Ignore (rps_kaggle §6) multiplies the evidence of every predictor
into one distribution over the opponent's next move and plays the move with the
best expected score. Here each input is one of the ensemble's signals, read as a
symbol (0..2, or NO_MOVE as a fourth value), so the combiner learns what any
signal's symbol says about the opponent's move, whatever the signal means by it.

The combiner runs once the ensemble's symbols are all in (replays included), and
learns when a round is folded from the symbols proposed for it (the ensemble's
scratch row, still holding them while the round's arms are pending).

State: f[at : at + 3] is the decayed prior over the opponent's move; then per
input signal s a 4 x 3 table at f[at + 3 + 12 s]: row = its symbol (3: NO_MOVE),
column = the opponent's move.
"""

import math

import numpy as np

from . import codes as c
from .jit import kernel

NONE_ROW = 3  # the table row of a NO_MOVE symbol
TABLE = 12  # 4 rows x 3 opponent moves per input


@kernel
def _row(symbol: int) -> int:
    return symbol if symbol >= 0 else NONE_ROW


@kernel
def _is_input(spec: np.ndarray, r: int, me: int) -> bool:
    return r != me and spec[r + c.R_KIND] != c.S_BAYES


@kernel
def predict(
    spec: np.ndarray, e: int, me: int, f: np.ndarray, symbols: np.ndarray
) -> int:
    """NaiveBayes record `me` of ensemble e: the opponent move that the move with
    the best expected score beats (first maximum), or NO_MOVE before any evidence."""
    at = spec[me + c.R_F]
    if f[at] + f[at + 1] + f[at + 2] <= 0.0:
        return c.NO_MOVE
    logp = np.empty(3)
    for m in range(3):
        logp[m] = math.log(f[at + m] + 1.0)
    for s in range(spec[e + c.E_NSIG]):
        r = spec[e + c.E_SIG_AT] + s * c.REC
        if not _is_input(spec, r, me):
            continue
        row = at + 3 + s * TABLE + 3 * _row(symbols[s])
        for m in range(3):  # P(symbol | m), Laplace-smoothed over the 4 rows
            logp[m] += math.log((f[row + m] + 1.0) / (f[at + m] + 4.0))
    top = max(logp[0], max(logp[1], logp[2]))
    p = np.empty(3)
    for m in range(3):
        p[m] = math.exp(logp[m] - top)
    best = -1
    best_ev = 0.0
    for h in range(3):  # h beats h + 2 and loses to h + 1
        ev = p[(h + 2) % 3] - p[(h + 1) % 3]
        if best < 0 or ev > best_ev:
            best = h
            best_ev = ev
    return (best + 2) % 3


@kernel
def combine(spec: np.ndarray, e: int, f: np.ndarray, symbols: np.ndarray) -> None:
    """Fill in every NaiveBayes symbol of ensemble e from the others."""
    for s in range(spec[e + c.E_NSIG]):
        r = spec[e + c.E_SIG_AT] + s * c.REC
        if spec[r + c.R_KIND] == c.S_BAYES:
            symbols[s] = predict(spec, e, r, f, symbols)


@kernel
def observe(
    spec: np.ndarray,
    e: int,
    f: np.ndarray,
    kn: np.ndarray,
    symbols: np.ndarray,
    o: int,
) -> None:
    """Every NaiveBayes record of ensemble e learns the opponent's move o against
    the symbols proposed for that round."""
    for s in range(spec[e + c.E_NSIG]):
        me = spec[e + c.E_SIG_AT] + s * c.REC
        if spec[me + c.R_KIND] != c.S_BAYES:
            continue
        at = spec[me + c.R_F]
        decay = kn[spec[me + c.R_K]]
        for j in range(3 + spec[e + c.E_NSIG] * TABLE):
            f[at + j] *= decay
        f[at + o] += 1.0
        for q in range(spec[e + c.E_NSIG]):
            r = spec[e + c.E_SIG_AT] + q * c.REC
            if _is_input(spec, r, me):
                f[at + 3 + q * TABLE + 3 * _row(symbols[q]) + o] += 1.0
