"""Replays, compiled: a whole bot core run on the shared history, from either side.

Many bots predict our next move and play what beats it. Replaying their machinery
on the shared history, with the roles swapped (R_SWAP: the opponent's side),
predicts their move outright (experiment 0003: +9.1 pts over smartbot), and a
replay of a Thompson metabot's arm scores names its move often enough to tip close
matches (experiment 0005). Replayed from our side, a whole bot (an L2 or above)
is an arm of a higher-level bot: its symbol is its own move.

The replayed ensemble lives in its own blocks of f / i; its symbol is its
best-scored arm's move (janken/kit/ensemble.py `best_arm`). A replayed ensemble
may hold replays of its own (a replay of a bot that replays others), each from
its own side relative to the one holding it, and so on three deep, so an L5 can
replay an L4 that replays an L3 holding replays (numba compiles no recursion, so
each depth has its own functions: `fold` / `predict`, `_fold_inner` /
`_predict_inner` and `_fold_deepest` / `_predict_deepest`).
"""

import random

import numpy as np

from . import bayes, ensemble, selectors
from . import codes as c
from .jit import kernel


@kernel
def likely_move(
    spec: np.ndarray, e: int, f: np.ndarray, i: np.ndarray, draws: int
) -> int:
    """The move ensemble e's Thompson sampling (sharpness 1) picks most often over
    `draws` draws, first maximum; a draw won by the random arm counts a third for
    each move. NO_MOVE when no arm has a move. It stops drawing once the rest of
    the draws can't change the leader: the same move as all of them, from fewer
    random numbers."""
    return likely_move_among(spec, e, f, i, draws, spec[e + c.E_NARMS])


@kernel
def _decided(votes: np.ndarray, left: int) -> bool:
    """Whether `left` more draws (a vote of at most 1 each) can no longer change
    which move leads the vote: the leader is ahead of every other move by more."""
    top = max(votes[0], max(votes[1], votes[2]))
    lead = 0
    for m in range(3):
        if votes[m] == top:
            lead += 1
    if lead > 1:
        return False
    runner_up = -1.0
    for m in range(3):
        if votes[m] < top:
            runner_up = max(runner_up, votes[m])
    return top - runner_up > left


@kernel
def likely_move_among(
    spec: np.ndarray, e: int, f: np.ndarray, i: np.ndarray, draws: int, n_arms: int
) -> int:
    """likely_move over the ensemble's first `n_arms` arms (and its random arm)."""
    pend = spec[e + c.E_PEND_I]
    score_f = spec[e + c.E_SCORE_F]
    has_random = spec[e + c.E_RANDOM] == c.RA_SCORED
    votes = np.zeros(3)
    for d in range(draws):
        if _decided(votes, draws - d):
            break
        best = -2.0
        pick = -1
        for a in range(n_arms + 1):
            if a == n_arms and not has_random:
                break
            if a < n_arms and i[pend + 1 + a] < 0:
                continue
            at = score_f + 3 * (spec[e + c.E_NARMS] if a == n_arms else a)
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
def _likely(
    spec: np.ndarray, r: int, sub: int, f: np.ndarray, i: np.ndarray, n_arms: int
) -> int:
    """The likely move of the replayed ensemble's first n_arms arms: by draws, or
    its best arm's."""
    draws = spec[r + c.R_A]
    if draws > 0:
        return likely_move_among(spec, sub, f, i, draws, n_arms)
    return ensemble.best_arm_among(spec, sub, f, i, n_arms)


@kernel
def _guess(
    spec: np.ndarray,
    r: int,
    sub: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    n: int,
    rn: int,
    opp: np.ndarray,
) -> int:
    """Replay record r's symbol: its likely move by draws, or its best arm's. A
    replayed Gate (R_B: its Gatekeeper's record) runs its gatekeeper, records
    kept every round as the real one keeps them (`opp`: the history of the
    replayed bot's opponent), and names the gated expert's move when the gate
    plays one, else the main bandit's likely move."""
    sel = spec[r + c.R_B]
    n_arms = spec[sub + c.E_NARMS]
    if sel <= 0:
        return _likely(spec, r, sub, f, i, n_arms)
    move = selectors.choose(spec, sel, sub, f, i, kn, n, rn, opp)
    if selectors.played_gated(spec, sel, f, i, kn, rn):
        return move
    return _likely(spec, r, sub, f, i, n_arms - selectors.gated_arms(spec, sel))


@kernel
def _fold_deepest(
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
    if spec[r + c.R_SWAP]:
        ensemble.fold(spec, spec[r + c.R_SUB], f, i, kn, k, rk, opp, my)
    else:
        ensemble.fold(spec, spec[r + c.R_SUB], f, i, kn, k, rk, my, opp)


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
    sub = spec[r + c.R_SUB]
    a, b = (opp, my) if spec[r + c.R_SWAP] else (my, opp)
    ensemble.fold(spec, sub, f, i, kn, k, rk, a, b)
    for s in range(spec[sub + c.E_NSIG]):
        r2 = spec[sub + c.E_SIG_AT] + s * c.REC
        if spec[r2 + c.R_KIND] == c.S_REPLAY:
            _fold_deepest(spec, r2, f, i, kn, k, rk, a, b)


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
    the replays it holds. `my` / `opp` are the history as the bandit holding r
    sees it."""
    sub = spec[r + c.R_SUB]
    a, b = (opp, my) if spec[r + c.R_SWAP] else (my, opp)
    ensemble.fold(spec, sub, f, i, kn, k, rk, a, b)
    for s in range(spec[sub + c.E_NSIG]):
        r2 = spec[sub + c.E_SIG_AT] + s * c.REC
        if spec[r2 + c.R_KIND] == c.S_REPLAY:
            _fold_inner(spec, r2, f, i, kn, k, rk, a, b)


@kernel
def _predict_deepest(
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
    a, b = (opp, my) if spec[r + c.R_SWAP] else (my, opp)
    symbols = ensemble.predictions(spec, sub, f, i, kn, n, rn, a, b)
    bayes.combine(spec, sub, f, symbols)
    ensemble.set_arms(spec, sub, i, symbols, rn)
    return _guess(spec, r, sub, f, i, kn, n, rn, b)


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
    a, b = (opp, my) if spec[r + c.R_SWAP] else (my, opp)
    symbols = ensemble.predictions(spec, sub, f, i, kn, n, rn, a, b)
    for s in range(spec[sub + c.E_NSIG]):
        r2 = spec[sub + c.E_SIG_AT] + s * c.REC
        if spec[r2 + c.R_KIND] == c.S_REPLAY:
            symbols[s] = _predict_deepest(spec, r2, f, i, kn, n, rn, a, b)
    bayes.combine(spec, sub, f, symbols)
    ensemble.set_arms(spec, sub, i, symbols, rn)
    return _guess(spec, r, sub, f, i, kn, n, rn, b)


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
    """The replayed bot's most likely move this round, or NO_MOVE. `my` / `opp`
    are the history as the bandit holding r sees it."""
    sub = spec[r + c.R_SUB]
    a, b = (opp, my) if spec[r + c.R_SWAP] else (my, opp)
    symbols = ensemble.predictions(spec, sub, f, i, kn, n, rn, a, b)
    for s in range(spec[sub + c.E_NSIG]):
        r2 = spec[sub + c.E_SIG_AT] + s * c.REC
        if spec[r2 + c.R_KIND] == c.S_REPLAY:
            symbols[s] = _predict_inner(spec, r2, f, i, kn, n, rn, a, b)
    bayes.combine(spec, sub, f, symbols)
    ensemble.set_arms(spec, sub, i, symbols, rn)
    return _guess(spec, r, sub, f, i, kn, n, rn, b)
