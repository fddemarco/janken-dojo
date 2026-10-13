"""The referee, compiled: whole matches inside one numba kernel.

`play_batch` spreads a schedule across cores with `prange`, flagging each match
done as it ends (janken/engine/__init__.py reads them while it plays). Each bot draws from
its own stream: before a side moves, the kernel reseeds numba's generator from
(match seed, side, round), so a match depends only on its seed, never on the
thread that played it, and neither bot's draws depend on how many the other
made (one shared stream would let a bot replay its opponent's randomness).

The kernel reaches the bots through `new_state(code, rounds)` (fresh state for
every match, sized for its rounds) and
`step(code, f, i, prm, my, opp, n)`, defined at the end of this module. Here they
are a stand-in with no bots. build.py compiles a copy of this module whose
dispatch section is generated for the bots being played (numba can only cache a
kernel whose callees are fixed globals), and every set of bots gets its own copy.
"""

import random

import numpy as np
from numba import prange

from janken.kit.codes import ORACLE_ARM, ORACLE_PURE
from janken.kit.jit import kernel, parallel_kernel
from janken.kit.moves import CRASH, INVALID, PAPER
from janken.match import INVALID_MOVE_LIMIT

# Why a bot forfeited, per side, in a match's status row.
FF_NONE, FF_CRASHED, FF_INVALID = 0, 1, 2

# The sides, as they name their random streams.
SIDE_A, SIDE_B = 0, 1
MASK32 = 0xFFFFFFFF
HASH_MUL = 0x45D9F3B  # a 32-bit integer hash's multiplier (products fit int64)


@kernel
def _mix32(x):
    """A bijective 32-bit integer hash of x's low 32 bits."""
    x &= MASK32
    x = (((x >> 16) ^ x) * HASH_MUL) & MASK32
    x = (((x >> 16) ^ x) * HASH_MUL) & MASK32
    return (x >> 16) ^ x


@kernel
def _seed_side(seed, side, r):
    """Seed the generator with side's stream for round r of the match `seed`:
    distinct for every (side, round) of a match."""
    match = _mix32(seed ^ _mix32(seed >> 32))
    random.seed(_mix32(match ^ (2 * r + side)))


@kernel
def _crashed(move):
    return FF_CRASHED if move == CRASH else FF_NONE


@kernel
def _over_limit(invalid):
    return FF_INVALID if invalid >= INVALID_MOVE_LIMIT else FF_NONE


@kernel
def _reveal(i, at, r, move, opp_level):
    """Tell an Oracle arm (janken/mocks.py) the opponent's move in round r and its
    level."""
    i[at] = r + 1
    i[at + 1] = move
    i[at + 2] = opp_level


@kernel
def play_into(code_a, code_b, prm_a, prm_b, rounds, seed, out):
    """Play one match into out[rounds, 2] (bot a's move, bot b's move).
    Returns (rounds played, forfeit a, forfeit b), forfeits as FF_* codes.

    Both bots move every round, a first, unless one holds an Oracle
    (janken/mocks.py): a pure Oracle never runs, it plays an outcome drawn vs the
    other's move and level (vs another pure Oracle, a random move); an Oracle arm
    is told the other's move and level before it moves; two arms both play PAPER.
    A crash forfeits at once, and its round
    is not played. An invalid move loses its round; the one that reaches
    INVALID_MOVE_LIMIT forfeits after its round is scored. Each side draws from
    its own stream of the match `seed` (_seed_side)."""
    fa, ia = new_state(code_a, rounds)
    fb, ib = new_state(code_b, rounds)
    ha = np.empty(rounds, np.int64)
    hb = np.empty(rounds, np.int64)
    kind_a = oracle_kind(code_a)
    kind_b = oracle_kind(code_b)
    level_a = level(code_a)
    level_b = level(code_b)
    cell_a = oracle_cell(code_a)
    cell_b = oracle_cell(code_b)
    invalid_a = 0
    invalid_b = 0
    for r in range(rounds):
        if kind_a == ORACLE_PURE and kind_b == ORACLE_PURE:
            _seed_side(seed, SIDE_B, r)
            mb = random.randrange(3)
            _seed_side(seed, SIDE_A, r)
            ma = oracle_move(code_a, fa, prm_a, mb, level_b)
        elif kind_a == ORACLE_PURE:  # b moves first (an ARM untold), a plays it
            _seed_side(seed, SIDE_B, r)
            mb = step(code_b, fb, ib, prm_b, hb, ha, r)
            _seed_side(seed, SIDE_A, r)
            ma = oracle_move(code_a, fa, prm_a, mb, level_b)
        elif kind_b == ORACLE_PURE:
            _seed_side(seed, SIDE_A, r)
            ma = step(code_a, fa, ia, prm_a, ha, hb, r)
            _seed_side(seed, SIDE_B, r)
            mb = oracle_move(code_b, fb, prm_b, ma, level_a)
        elif kind_a == ORACLE_ARM and kind_b == ORACLE_ARM:  # neither can be told
            ma = PAPER
            mb = PAPER
        elif kind_a == ORACLE_ARM:
            _seed_side(seed, SIDE_B, r)
            mb = step(code_b, fb, ib, prm_b, hb, ha, r)
            _reveal(ia, cell_a, r, mb, level_b)
            _seed_side(seed, SIDE_A, r)
            ma = step(code_a, fa, ia, prm_a, ha, hb, r)
        elif kind_b == ORACLE_ARM:
            _seed_side(seed, SIDE_A, r)
            ma = step(code_a, fa, ia, prm_a, ha, hb, r)
            _reveal(ib, cell_b, r, ma, level_a)
            _seed_side(seed, SIDE_B, r)
            mb = step(code_b, fb, ib, prm_b, hb, ha, r)
        else:
            _seed_side(seed, SIDE_A, r)
            ma = step(code_a, fa, ia, prm_a, ha, hb, r)
            _seed_side(seed, SIDE_B, r)
            mb = step(code_b, fb, ib, prm_b, hb, ha, r)
        if ma == CRASH or mb == CRASH:
            return r, _crashed(ma), _crashed(mb)
        ha[r] = ma
        hb[r] = mb
        out[r, 0] = ma
        out[r, 1] = mb
        if ma == INVALID:
            invalid_a += 1
        if mb == INVALID:
            invalid_b += 1
        if invalid_a >= INVALID_MOVE_LIMIT or invalid_b >= INVALID_MOVE_LIMIT:
            return r + 1, _over_limit(invalid_a), _over_limit(invalid_b)
    return rounds, FF_NONE, FF_NONE


@parallel_kernel
def play_batch(codes_a, codes_b, prm_a, prm_b, rounds, seeds, out, status, done):
    """Play every (codes_a[k], codes_b[k]) match into the caller's arrays: its
    moves into out[k] (int8[rounds, 2]), its (rounds played, forfeit a, forfeit b)
    into status[k], then done[k] = 1. Compiled without the GIL, so the caller can
    read finished matches while the batch is still playing."""
    for k in prange(codes_a.size):
        played, ff_a, ff_b = play_into(
            codes_a[k], codes_b[k], prm_a[k], prm_b[k], rounds, int(seeds[k]), out[k]
        )
        status[k, 0] = played
        status[k, 1] = ff_a
        status[k, 2] = ff_b
        done[k] = 1


# --- dispatch (build.py replaces everything below) ---------------------------


@kernel
def new_state(code, rounds):
    return np.zeros(0, np.float64), np.zeros(0, np.int64)


@kernel
def step(code, f, i, prm, my, opp, n):
    return CRASH


@kernel
def oracle_kind(code):
    """ORACLE_NONE (0), ORACLE_PURE or ORACLE_ARM (janken/mocks.py)."""
    return 0


@kernel
def oracle_cell(code):
    """The i offset of an Oracle arm's state, or -1."""
    return -1


@kernel
def level(code):
    """The bot's level (janken/kit/levels.py)."""
    return 1


@kernel
def oracle_move(code, f, prm, opp, opp_level):
    """A pure Oracle's move vs `opp`, an opponent of `opp_level`."""
    return CRASH
