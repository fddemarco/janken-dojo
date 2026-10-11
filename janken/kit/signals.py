"""Signals, compiled: each proposes a symbol for the next round, or NO_MOVE.

A signal reads the valid-only history (`my`, `opp`, `n`). A sim evaluates the
same signal with the histories swapped (janken/kit/ensemble.py does that), so
"OPP" is then us. Stateful signals keep their tables in their own block of `f`
(and `i`), laid out by janken/kit/blueprint.py; `observe` folds round `k` into
them, with `rk` the round's index in the raw history (for pending predictions).

Tables are decayed count rows; an all-zero row means "never seen", so readers
return NO_MOVE for it rather than guess. History matchers (LongestMatch, SecondMatch,
Geometry) read the bot's shared match index of their stream (janken/kit/matching.py).
"""

import math
import random

import numpy as np

from . import codes as c
from . import matching, oracle
from .jit import kernel

S3 = math.sqrt(3.0) / 2.0
B_RE = np.array([1.0, -0.5, -0.5])  # moves as the cube roots of unity
B_IM = np.array([0.0, S3, -S3])


@kernel
def seq(src: int, t: int, my: np.ndarray, opp: np.ndarray) -> int:
    """Symbol t of a sequence: OPP's move, MY move, or the JOINT pair (0..8)."""
    if src == c.OPP:
        return opp[t]
    if src == c.MY:
        return my[t]
    return my[t] * 3 + opp[t]


@kernel
def rows(ctx: int, order: int) -> int:
    """Context rows of an order-`order` table over `ctx`."""
    return (9 if ctx == c.JOINT else 3) ** order


@kernel
def context(ctx: int, order: int, end: int, my: np.ndarray, opp: np.ndarray) -> int:
    """Row index of the context ctx[end - order : end]."""
    base = 9 if ctx == c.JOINT else 3
    key = 0
    for t in range(end - order, end):
        key = key * base + seq(ctx, t, my, opp)
    return key


@kernel
def bump(f: np.ndarray, at: int, k: int, decay: float) -> None:
    """Decay the row f[at:at+3], then count symbol k."""
    for j in range(3):
        f[at + j] *= decay
    f[at + k] += 1.0


@kernel
def argmax_random(f: np.ndarray, at: int) -> int:
    """The max of f[at:at+3] (a random one among ties), or NO_MOVE when max <= 0.
    Draws only to break a tie."""
    m = max(f[at], max(f[at + 1], f[at + 2]))
    if m <= 0:
        return c.NO_MOVE
    ties = 0
    for j in range(3):
        if f[at + j] >= m - 1e-9:
            ties += 1
    skip = random.randrange(ties) if ties > 1 else 0  # the tie's rank, in order
    for j in range(3):
        if f[at + j] >= m - 1e-9:
            if skip == 0:
                return j
            skip -= 1
    return c.NO_MOVE


@kernel
def first_max(f: np.ndarray, at: int) -> int:
    """The first max of f[at:at+3], or NO_MOVE when max <= 0. Never draws."""
    m = max(f[at], max(f[at + 1], f[at + 2]))
    if m <= 0:
        return c.NO_MOVE
    for j in range(3):
        if f[at + j] >= m:
            return j
    return c.NO_MOVE


@kernel
def sample_row(f: np.ndarray, at: int) -> int:
    """A symbol drawn in proportion to f[at:at+3], or NO_MOVE for an empty row."""
    total = f[at] + f[at + 1] + f[at + 2]
    if total <= 0:
        return c.NO_MOVE
    u = random.random() * total
    if u < f[at]:
        return 0
    if u < f[at] + f[at + 1]:
        return 1
    return 2


@kernel
def _geometry_learn(f: np.ndarray, at: int, x: int, o: int, alpha: float) -> None:
    """a <- (1 - alpha) a + alpha y conj(x), y the move that beat the opponent."""
    y = (o + 1) % 3
    t_re = B_RE[y] * B_RE[x] + B_IM[y] * B_IM[x]
    t_im = B_IM[y] * B_RE[x] - B_RE[y] * B_IM[x]
    f[at] = (1.0 - alpha) * f[at] + alpha * t_re
    f[at + 1] = (1.0 - alpha) * f[at + 1] + alpha * t_im


@kernel
def _geometry_move(f: np.ndarray, at: int, x: int, sample: bool) -> int:
    """Our move from the feature x rotated by the learned offset: sampled from
    p_k = max(0, (2 Re(z conj B_k) + 1) / 3), or its first maximum. p is written
    to the stage's scratch row f[at + 2 : at + 5]."""
    z_re = B_RE[x] * f[at] - B_IM[x] * f[at + 1]
    z_im = B_RE[x] * f[at + 1] + B_IM[x] * f[at]
    for k in range(3):
        f[at + 2 + k] = max((2.0 * (z_re * B_RE[k] + z_im * B_IM[k]) + 1.0) / 3.0, 0.0)
    if sample:
        return sample_row(f, at + 2)
    return first_max(f, at + 2)


@kernel
def observe(
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
    """Fold round k (my[k], opp[k]) into signal record r's state; the history
    before it is [0, k), and rk is the round's raw index."""
    kind = spec[r + c.R_KIND]
    at = spec[r + c.R_F]
    kk = spec[r + c.R_K]
    a = spec[r + c.R_A]
    b = spec[r + c.R_B]
    order = spec[r + c.R_C]
    if kind == c.S_FREQ:
        bump(f, at, seq(a, k, my, opp), kn[kk])
    elif kind == c.S_NGRAM:
        if k >= order:
            bump(f, at + 3 * context(b, order, k, my, opp), seq(a, k, my, opp), kn[kk])
    elif kind == c.S_BACKOFF:
        sym = seq(a, k, my, opp)
        for o in range(order + 1):
            if k >= o:
                f[at + 3 * context(b, o, k, my, opp) + sym] += 1.0
            at += rows(b, o) * 3
    elif kind == c.S_RELATIVE:
        if k > 0:
            row = (opp[k - 1] - my[k - 1]) % 3 if b else 0
            bump(f, at + 3 * row, (opp[k] - seq(a, k - 1, my, opp)) % 3, kn[kk])
    elif kind == c.S_MATCH2:
        j = matching.query(spec, matching.record(spec, r), i, int(kn[kk]), k + 1)
        i[matching.slot_at(spec, i, order) + k + 1] = j + 1
    elif kind == c.S_GEOMETRY:
        ia = spec[r + c.R_I]
        if i[ia] == rk + 1:
            _geometry_learn(f, at, i[ia + 1], opp[k], kn[kk])
        i[ia] = 0


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
    """Signal record r's symbol for round n (raw index rn), or NO_MOVE."""
    kind = spec[r + c.R_KIND]
    at = spec[r + c.R_F]
    kk = spec[r + c.R_K]
    a = spec[r + c.R_A]
    b = spec[r + c.R_B]
    order = spec[r + c.R_C]
    if kind == c.S_LAST:
        return seq(a, n - 1, my, opp) if n > 0 else c.NO_MOVE
    if kind == c.S_FREQ:
        return argmax_random(f, at)
    if kind == c.S_NGRAM:
        if n < order:
            return c.NO_MOVE
        row = at + 3 * context(b, order, n, my, opp)
        return sample_row(f, row) if spec[r + c.R_D] else argmax_random(f, row)
    if kind == c.S_BACKOFF:
        for o in range(order, -1, -1):
            if n >= o:
                start = at  # the order-o table follows the lower orders' tables
                for q in range(o):
                    start += rows(b, q) * 3
                guess = first_max(f, start + 3 * context(b, o, n, my, opp))
                if guess >= 0:
                    return guess
        return c.NO_MOVE
    if kind == c.S_MATCH:
        j = matching.query(spec, matching.record(spec, r), i, int(kn[kk]), n)
        return seq(a, j, my, opp) if j >= 0 else c.NO_MOVE
    if kind == c.S_MATCH2:
        j = matching.query(spec, matching.record(spec, r), i, int(kn[kk]), n)
        if j < 0:
            return c.NO_MOVE
        j2 = i[matching.slot_at(spec, i, order) + j] - 1
        return seq(a, j2, my, opp) if j2 >= 0 else c.NO_MOVE
    if kind == c.S_RELATIVE:
        if n == 0:
            return c.NO_MOVE
        row = (opp[n - 1] - my[n - 1]) % 3 if b else 0
        d = argmax_random(f, at + 3 * row)
        return (seq(a, n - 1, my, opp) + d) % 3 if d >= 0 else c.NO_MOVE
    if kind == c.S_REACT:
        if n == 0:
            return c.NO_MOVE
        if (my[n - 1] - opp[n - 1]) % 3 == 1:
            return (my[n - 1] + 1) % 3
        return opp[n - 1]
    if kind == c.S_CONSTANT:
        return a
    if kind == c.S_CYCLE:
        return (n * int(kn[kk])) % 3
    if kind == c.S_BIASED:
        u = random.random()
        if u < kn[kk]:
            return 0
        return 1 if u < kn[kk] + kn[kk + 1] else 2
    if kind == c.S_WIN_STAY:
        if n == 0:
            return c.NO_MOVE
        m = my[n - 1]
        return (m + int(kn[kk])) % 3 if (m - opp[n - 1]) % 3 == 2 else m
    if kind == c.S_GEOMETRY:
        j = matching.query(spec, matching.record(spec, r), i, int(kn[kk + 1]), n)
        if j < 0:
            return c.NO_MOVE
        ia = spec[r + c.R_I]
        i[ia] = rn + 1
        i[ia + 1] = opp[j]
        move = _geometry_move(f, at, opp[j], a == 1)
        return (move + 2) % 3
    if kind == c.S_ORACLE:
        return oracle.symbol(spec, r, i, kn, rn)
    return c.NO_MOVE
