"""An ensemble, compiled: signals x rotations = arms, their records, the best arm.

Each round, `predictions` asks every signal for its symbol (a sim is asked with
the histories swapped, and its symbol is the move that beats its prediction of
us), and `set_arms` turns each symbol into one pending move per rotation, plus
the random arm. When the round is folded in, `fold` scores every pending arm
counterfactually against the opponent's real move (rps_kaggle section 4.5: unchosen arms
must learn too) and lets the signals observe it.

Replay signals are filled in by the caller (janken/kit/replay.py), which is how a
replayed ensemble can reuse all of this without recursion.

State: f[score_f + 3a : +3] is arm a's record (random arm last); i[pend] is the
raw round + 1 the pending moves were made for, then one move per arm (-1: none,
RANDOM_MOVE: the pinned random arm, drawn only if it is picked).
"""

import random

import numpy as np

from . import bayes, signals
from . import codes as c
from .jit import kernel


@kernel
def predictions(
    spec: np.ndarray,
    e: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    n: int,
    rn: int,
    my: np.ndarray,
    opp: np.ndarray,
) -> np.ndarray:
    """Every signal's symbol for round n (replays: NO_MOVE, filled by the caller),
    in the ensemble's scratch block of i (no allocation)."""
    n_sig = spec[e + c.E_NSIG]
    at = spec[e + c.E_SYM_I]
    out = i[at : at + n_sig]
    for s in range(n_sig):
        out[s] = c.NO_MOVE
        r = spec[e + c.E_SIG_AT] + s * c.REC
        if spec[r + c.R_KIND] == c.S_REPLAY:
            continue
        if spec[r + c.R_SWAP]:
            guess = signals.predict(spec, r, f, i, kn, n, rn, opp, my)
            out[s] = (guess + 1) % 3 if guess >= 0 else c.NO_MOVE
        else:
            out[s] = signals.predict(spec, r, f, i, kn, n, rn, my, opp)
    return out


@kernel
def set_arms(
    spec: np.ndarray, e: int, i: np.ndarray, symbols: np.ndarray, rn: int
) -> None:
    """Each symbol rotated into its arms' pending moves for raw round rn."""
    pend = spec[e + c.E_PEND_I]
    n_arms = spec[e + c.E_NARMS]
    i[pend] = rn + 1
    for s in range(spec[e + c.E_NSIG]):
        r = spec[e + c.E_SIG_AT] + s * c.REC
        arm = spec[r + c.R_ARM]
        for q in range(spec[r + c.R_NROT]):
            sym = symbols[s]
            i[pend + 1 + arm + q] = (
                (sym + spec[r + c.R_ROT + q]) % 3 if sym >= 0 else c.NO_MOVE
            )
    mode = spec[e + c.E_RANDOM]
    if mode == c.RA_SCORED:
        i[pend + 1 + n_arms] = random.randrange(3)
    elif mode == c.RA_PINNED:
        i[pend + 1 + n_arms] = c.RANDOM_MOVE
    else:
        i[pend + 1 + n_arms] = c.NO_MOVE


@kernel
def score_arm(
    scorer: int, f: np.ndarray, at: int, move: int, o: int, kn: np.ndarray, kk: int
) -> None:
    """Update one arm's record with how `move` would have fared against `o`."""
    r = (move - o) % 3  # 0 tie, 1 win, 2 loss
    result = 0.0 if r == 0 else (1.0 if r == 1 else -1.0)
    if scorer == c.SC_DIRICHLET:
        for j in range(3):
            f[at + j] *= kn[kk]
        f[at + (0 if r == 1 else (1 if r == 0 else 2))] += 1.0
    elif scorer == c.SC_DECAYED:
        f[at] = kn[kk] * f[at] + result
    elif scorer == c.SC_DROP_SWITCH:
        f[at] += result
        p_reset = kn[kk]
        if r == 2 and (p_reset >= 1.0 or (p_reset > 0.0 and random.random() < p_reset)):
            f[at] = 0.0


@kernel
def value(scorer: int, f: np.ndarray, at: int) -> float:
    """An arm's score: the posterior mean P(win) - P(loss), or its net score."""
    if scorer == c.SC_DIRICHLET:
        w = f[at]
        t = f[at + 1]
        lo = f[at + 2]
        return (w - lo) / (w + t + lo + 3.0)
    return f[at]


@kernel
def fold(
    spec: np.ndarray,
    e: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    k: int,
    rk: int,
    my: np.ndarray,
    opp: np.ndarray,
) -> None:
    """Fold valid round k (raw index rk): score the arms proposed for it, let the
    NaiveBayes combiners learn from the symbols behind them, then let every signal
    but the replays observe it."""
    scorer = spec[e + c.E_SCORER]
    pend = spec[e + c.E_PEND_I]
    if i[pend] == rk + 1:
        at = spec[e + c.E_SYM_I]
        bayes.observe(spec, e, f, kn, i[at : at + spec[e + c.E_NSIG]], opp[k])
    if scorer != c.SC_NONE and i[pend] == rk + 1:
        score_f = spec[e + c.E_SCORE_F]
        kk = spec[e + c.E_SCORER_K]
        for a in range(spec[e + c.E_NARMS] + 1):
            move = i[pend + 1 + a]
            if move >= 0:
                score_arm(scorer, f, score_f + 3 * a, move, opp[k], kn, kk)
    i[pend] = 0
    for s in range(spec[e + c.E_NSIG]):
        r = spec[e + c.E_SIG_AT] + s * c.REC
        if spec[r + c.R_KIND] == c.S_REPLAY:
            continue
        if spec[r + c.R_SWAP]:
            signals.observe(spec, r, f, i, kn, k, rk, opp, my)
        else:
            signals.observe(spec, r, f, i, kn, k, rk, my, opp)


@kernel
def best_arm(spec: np.ndarray, e: int, f: np.ndarray, i: np.ndarray) -> int:
    """The move of the best-scored pending arm (first maximum, no draw), or NO_MOVE.
    With a pinned random arm, a best score <= 0 means random play: NO_MOVE."""
    pend = spec[e + c.E_PEND_I]
    scorer = spec[e + c.E_SCORER]
    score_f = spec[e + c.E_SCORE_F]
    pick = c.NO_MOVE
    best = 0.0
    for a in range(spec[e + c.E_NARMS]):
        move = i[pend + 1 + a]
        if move < 0:
            continue
        v = value(scorer, f, score_f + 3 * a)
        if pick < 0 or v > best:
            pick = move
            best = v
    if spec[e + c.E_RANDOM] == c.RA_PINNED and best <= 0.0:
        return c.NO_MOVE
    return pick
