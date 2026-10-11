"""History matching, compiled: one incremental match index per history stream.

A history matcher (LongestMatch, Geometry) wants, for the history s[0:n], the most
recent earlier repeat of the longest suffix of s (at most max_len symbols): the
largest end e < n with s[e - L : e] == s[n - L : n], for the largest such L. Scanning
the history for it every round costs O(max_len * n) a round; this index answers it
in O(1) and pays, per folded round, only for the earlier ends whose last symbol
equals the new one.

For every end e < n it keeps M(e), the length of the common suffix of s[0:e] and
s[0:n]. Appending x = s[n] (n -> n + 1) makes M(e + 1) = M(e) + 1 where s[e] == x and
0 elsewhere, so only the ends whose last symbol is x (a linked list per symbol)
are touched; a stamp tells a fresh M from a stale one, which is 0. Walking that
list newest first, best[L] records the first (most recent) end with M >= L.

Every matcher of a bot shares the index of the stream it reads. A sim or a replay
sees the history swapped, which turns OPP into MY and back and leaves JOINT's
repeats where they are (my * 3 + opp and opp * 3 + my name the same rounds), so a
bot has at most three indexes (blueprint.py assigns them). They live in the bot's
own state, fresh every match: fixed cells [head per symbol, filled] and four
per-round slots [mval, stamp, prev, best] (codes.py, the per-match workspace).
"""

import numpy as np

from . import codes as c
from .jit import kernel

SYMBOLS = 9  # the widest stream: JOINT


@kernel
def slot_at(spec: np.ndarray, i: np.ndarray, slot: int) -> int:
    """Offset in i of per-round slot `slot`."""
    rounds_i = spec[c.H_ROUNDS_I]
    return i[rounds_i + 1] + slot * i[rounds_i]


@kernel
def record(spec: np.ndarray, r: int) -> int:
    """Offset of the match index record that signal record r reads."""
    return spec[c.H_IDX_AT] + spec[r + c.R_IDX] * c.IDX


@kernel
def stream_symbol(stream: int, k: int, my: np.ndarray, opp: np.ndarray) -> int:
    """Symbol k of a stream (of the unswapped valid history)."""
    if stream == c.STREAM_OPP:
        return opp[k]
    if stream == c.STREAM_MY:
        return my[k]
    return my[k] * 3 + opp[k]


@kernel
def fold(
    spec: np.ndarray, x: int, i: np.ndarray, k: int, my: np.ndarray, opp: np.ndarray
) -> None:
    """Append valid round k to index record x; it then describes s[0:k + 1]."""
    n = k + 1
    sym = stream_symbol(spec[x + c.X_STREAM], k, my, opp)
    fixed = spec[x + c.X_FIXED_I]
    mval = slot_at(spec, i, spec[x + c.X_SLOT])
    stamp = slot_at(spec, i, spec[x + c.X_SLOT] + 1)
    prev = slot_at(spec, i, spec[x + c.X_SLOT] + 2)
    best = slot_at(spec, i, spec[x + c.X_SLOT] + 3)
    filled = 0
    e = i[fixed + sym]  # the newest earlier end whose last symbol is sym (0: none)
    while e > 0:
        m = i[mval + e - 1] + 1 if i[stamp + e - 1] == n - 1 else 1
        i[mval + e] = m
        i[stamp + e] = n
        while filled < m:
            filled += 1
            i[best + filled] = e
        e = i[prev + e]
    i[prev + n] = i[fixed + sym]
    i[fixed + sym] = n
    i[fixed + SYMBOLS] = filled


@kernel
def query(spec: np.ndarray, x: int, i: np.ndarray, max_len: int, n: int) -> int:
    """The end just after the most recent earlier repeat of the longest suffix (up
    to max_len symbols) of the n symbols folded into index record x, or -1."""
    length = min(max_len, n - 1, i[spec[x + c.X_FIXED_I] + SYMBOLS])
    if length < 1:
        return -1
    return i[slot_at(spec, i, spec[x + c.X_SLOT] + 3) + length]
