"""The Oracle, compiled: an outcome drawn from per-level win chances.

Research only (janken/mocks.py). The referee reveals the opponent's move and
level; the Oracle's knobs are its win chance vs each level (ties and losses
split the rest evenly), then its (win, tie) vs another Oracle (by default a
draw). A pure Oracle bot plays the move with the drawn outcome; an Oracle arm
proposes the symbol whose BEAT has it.
"""

import random

import numpy as np

from . import codes as c
from .jit import kernel

WIN, TIE, LOSS = 0, 1, 2


@kernel
def outcome(kn: np.ndarray, kk: int, n_wins: int, level: int) -> int:
    """WIN, TIE or LOSS vs an opponent of `level`, from the knobs at kk."""
    if level == c.LEVEL_ORACLE:
        win = kn[kk + n_wins]
        tie = kn[kk + n_wins + 1]
    else:
        win = kn[kk + min(max(level, 1), n_wins) - 1]
        tie = (1.0 - win) / 2.0
    u = random.random()
    if u < win:
        return WIN
    return TIE if u < win + tie else LOSS


@kernel
def move_for(result: int, opp: int) -> int:
    """The move with `result` vs the opponent's move `opp`."""
    if result == WIN:
        return (opp + 1) % 3
    return opp if result == TIE else (opp + 2) % 3


@kernel
def symbol(spec: np.ndarray, r: int, i: np.ndarray, kn: np.ndarray, rn: int) -> int:
    """An Oracle arm's symbol for raw round rn: the move whose BEAT has the drawn
    outcome vs the revealed move; NO_MOVE when nothing was revealed."""
    ia = spec[r + c.R_I]
    opp = i[ia + 1]
    if i[ia] != rn + 1 or opp < 0 or opp > 2:
        return c.NO_MOVE
    result = outcome(kn, spec[r + c.R_K], spec[r + c.R_A], i[ia + 2])
    return (move_for(result, opp) + 2) % 3  # BEAT of the symbol plays it


@kernel
def pure_move(spec: np.ndarray, kn: np.ndarray, opp: int, level: int) -> int:
    """A pure Oracle bot's move vs `opp` (an opponent of `level`); a random move
    vs a crash or an invalid move."""
    if opp < 0 or opp > 2:
        return random.randrange(3)
    r = spec[spec[c.H_CORE] + c.E_SIG_AT]
    return move_for(outcome(kn, spec[r + c.R_K], spec[r + c.R_A], level), opp)
