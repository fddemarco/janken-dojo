"""Replays, compiled: a whole bot core run from the opponent's side.

Many bots predict our next move and play what beats it. Replaying their machinery
on the shared history, with the roles swapped, predicts their move outright
(experiment 0003: +9.1 pts over smartbot), and a replay of a Thompson metabot's
arm scores names its move often enough to tip close matches (experiment 0005).

The replayed ensemble lives in its own blocks of f / i; its symbol is its
best-scored arm's move (janken/kit/ensemble.py `best_arm`). A replayed ensemble
may hold replays of its own (a replay of a bot that replays others), which see
the history swapped back; those may not (numba compiles no recursion, so each
depth has its own functions: `fold` / `predict` and `_fold_inner` /
`_predict_inner`).
"""

import random

import numpy as np

from . import bayes, ensemble
from . import codes as c
from .jit import kernel


@kernel
def likely_move(
    spec: np.ndarray, e: int, f: np.ndarray, i: np.ndarray, draws: int
) -> int:
    """The move ensemble e's Thompson sampling (sharpness 1) picks most often over
    `draws` draws, first maximum; a draw won by the random arm counts a third for
    each move. NO_MOVE when no arm has a move."""
    pend = spec[e + c.E_PEND_I]
    score_f = spec[e + c.E_SCORE_F]
    n_arms = spec[e + c.E_NARMS]
    has_random = spec[e + c.E_RANDOM] == c.RA_SCORED
    votes = np.zeros(3)
    for _ in range(draws):
        best = -2.0
        pick = -1
        for a in range(n_arms + 1):
            if a == n_arms and not has_random:
                break
            if a < n_arms and i[pend + 1 + a] < 0:
                continue
            at = score_f + 3 * a
            gw = random.gammavariate(1.0 + f[at], 1.0)
            gt = random.gammavariate(1.0 + f[at + 1], 1.0)
            gl = random.gammavariate(1.0 + f[at + 2], 1.0)
            sampled = (gw - gl) / (gw + gt + gl)
            if sampled > best:
                best = sampled
                pick = a
        if pick < 0:
            return c.NO_MOVE
        if pick == n_arms:
            for m in range(3):
                votes[m] += 1.0 / 3.0
        else:
            votes[i[pend + 1 + pick]] += 1.0
    top = 0
    for m in range(1, 3):
        if votes[m] > votes[top]:
            top = m
    return top


@kernel
def _guess(spec: np.ndarray, r: int, sub: int, f: np.ndarray, i: np.ndarray) -> int:
    """Replay record r's symbol: its likely move by draws, or its best arm's."""
    draws = spec[r + c.R_A]
    if draws > 0:
        return likely_move(spec, sub, f, i, draws)
    return ensemble.best_arm(spec, sub, f, i)


@kernel
def _fold_inner(
    spec: np.ndarray,
    r: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    k: int,
    rk: int,
    my: np.ndarray,
    opp: np.ndarray,
) -> None:
    ensemble.fold(spec, spec[r + c.R_SUB], f, i, kn, k, rk, opp, my)


@kernel
def fold(
    spec: np.ndarray,
    r: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    k: int,
    rk: int,
    my: np.ndarray,
    opp: np.ndarray,
) -> None:
    """Fold valid round k into replay record r's ensemble, from its side, and into
    the replays it holds."""
    sub = spec[r + c.R_SUB]
    ensemble.fold(spec, sub, f, i, kn, k, rk, opp, my)
    for s in range(spec[sub + c.E_NSIG]):
        r2 = spec[sub + c.E_SIG_AT] + s * c.REC
        if spec[r2 + c.R_KIND] == c.S_REPLAY:
            _fold_inner(spec, r2, f, i, kn, k, rk, opp, my)


@kernel
def _predict_inner(
    spec: np.ndarray,
    r: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    n: int,
    rn: int,
    my: np.ndarray,
    opp: np.ndarray,
) -> int:
    sub = spec[r + c.R_SUB]
    symbols = ensemble.predictions(spec, sub, f, i, kn, n, rn, opp, my)
    bayes.combine(spec, sub, f, symbols)
    ensemble.set_arms(spec, sub, i, symbols, rn)
    return _guess(spec, r, sub, f, i)


@kernel
def predict(
    spec: np.ndarray,
    r: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    n: int,
    rn: int,
    my: np.ndarray,
    opp: np.ndarray,
) -> int:
    """The replayed bot's most likely move this round, or NO_MOVE."""
    sub = spec[r + c.R_SUB]
    symbols = ensemble.predictions(spec, sub, f, i, kn, n, rn, opp, my)
    for s in range(spec[sub + c.E_NSIG]):
        r2 = spec[sub + c.E_SIG_AT] + s * c.REC
        if spec[r2 + c.R_KIND] == c.S_REPLAY:
            symbols[s] = _predict_inner(spec, r2, f, i, kn, n, rn, opp, my)
    bayes.combine(spec, sub, f, symbols)
    ensemble.set_arms(spec, sub, i, symbols, rn)
    return _guess(spec, r, sub, f, i)
