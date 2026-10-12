"""Overlays, compiled: transform the chosen move, after the core has run.

    Stall        random play while being read (drawdown) or while the lead is safe
                 (lead lock): any margin wins a match here (rps_kaggle section 5)
    Team         an Iliad fleet's handshake; supports throw matches to the champion,
                 and an impostor fakes a support's to beat the champion's throw move;
                 a vigilant teammate stops throwing once the other one doesn't
    EmitInvalid  spends the invalid moves the rules allow (idea #20): the opponent
                 sees INVALID, and several zoo bots crash or go random on it

They see the raw history, invalid moves included.
"""

import math
import random

import numpy as np

from ..match import INVALID_MOVE_LIMIT
from . import codes as c
from .jit import kernel
from .moves import INVALID, PAPER, ROCK, SCISSORS

HANDSHAKES = (
    np.array(  # by fleet: ILIAD, ILIAD_V2, ILIAD_V3 (each differs from round 0)
        [
            [SCISSORS, SCISSORS, ROCK, ROCK, PAPER, SCISSORS, SCISSORS, PAPER],
            [PAPER, ROCK, ROCK, SCISSORS, PAPER, PAPER, ROCK, SCISSORS],
            [ROCK, SCISSORS, PAPER, PAPER, ROCK, SCISSORS, ROCK, PAPER],
        ],
        np.int64,
    )
)
HANDSHAKE = HANDSHAKES[c.ILIAD]
ROLE_MOVE = np.array([ROCK, PAPER], np.int64)  # by role: CHAMPION, SUPPORT
INVALID_BUDGET = INVALID_MOVE_LIMIT - 1  # invalid moves a bot may spend and not forfeit


@kernel
def round_result(m: int, o: int) -> int:
    """+1 / 0 / -1 for us; an invalid move loses the round (both invalid: tie)."""
    if m == INVALID or o == INVALID:
        return 0 if m == o else (1 if o == INVALID else -1)
    r = (m - o) % 3
    return 0 if r == 0 else (1 if r == 1 else -1)


@kernel
def _stall(
    spec: np.ndarray,
    o: int,
    i: np.ndarray,
    kn: np.ndarray,
    move: int,
    my: np.ndarray,
    opp: np.ndarray,
    n: int,
) -> int:
    ia = spec[o + c.R_I]  # [rounds scored, score, stall rounds left]
    kk = spec[o + c.R_K]
    for k in range(i[ia], n):
        i[ia + 1] += round_result(my[k], opp[k])
    i[ia] = n
    if i[ia + 2] > 0:
        i[ia + 2] -= 1
        return random.randrange(3)
    window = int(kn[kk])
    if n >= window // 2:
        total = 0
        for k in range(max(0, n - window), n):
            total += round_result(my[k], opp[k])
        if total <= -int(kn[kk + 1]):
            i[ia + 2] = int(kn[kk + 2]) - 1
            return random.randrange(3)
    remaining = int(kn[kk + 4]) - n
    if remaining > 0 and i[ia + 1] >= kn[kk + 3] * math.sqrt(2.0 / 3.0 * remaining) + 1:
        return random.randrange(3)
    return move


@kernel
def _kept_faith(opp: np.ndarray, start: int, n: int, expected: int) -> bool:
    """Whether the opponent played `expected` in every round from `start` to n."""
    for t in range(start, n):
        if opp[t] != expected:
            return False
    return True


@kernel
def team_move(role: int, fleet: int, vigilant: int, opp: np.ndarray, n: int) -> int:
    """The handshake / throw move for round n, or NO_MOVE to play on."""
    hand = HANDSHAKES[fleet]
    k = hand.size
    for t in range(min(n, k)):
        if opp[t] != hand[t]:
            return c.NO_MOVE
    if n < k:
        return hand[n]
    if n == k:
        return ROLE_MOVE[c.SUPPORT] if role == c.IMPOSTOR else ROLE_MOVE[role]
    if role == c.IMPOSTOR and opp[k] == ROLE_MOVE[c.CHAMPION]:
        return SCISSORS  # the champion now plays PAPER, expecting a support's ROCK
    if role == c.CHAMPION and opp[k] == ROLE_MOVE[c.SUPPORT]:
        throw, expected = PAPER, ROCK
    elif role == c.SUPPORT and opp[k] == ROLE_MOVE[c.CHAMPION]:
        throw, expected = ROCK, PAPER
    else:
        return c.NO_MOVE
    if vigilant and not _kept_faith(opp, k + 1, n, expected):
        return c.NO_MOVE  # not a teammate: an impostor, or a broken alliance
    return throw


@kernel
def _emit_invalid(
    spec: np.ndarray, o: int, kn: np.ndarray, move: int, my: np.ndarray, n: int
) -> int:
    kk = spec[o + c.R_K]
    if n != int(kn[kk]) and n != int(kn[kk + 1]):
        return move
    spent = 0
    for t in range(n):
        if my[t] == INVALID:
            spent += 1
    return INVALID if spent < INVALID_BUDGET else move


@kernel
def apply(
    spec: np.ndarray,
    o: int,
    i: np.ndarray,
    kn: np.ndarray,
    move: int,
    my: np.ndarray,
    opp: np.ndarray,
    n: int,
) -> int:
    """Overlay record o applied to this round's move."""
    kind = spec[o + c.R_KIND]
    if kind == c.O_STALL:
        return _stall(spec, o, i, kn, move, my, opp, n)
    if kind == c.O_TEAM:
        team = team_move(spec[o + c.R_A], spec[o + c.R_B], spec[o + c.R_C], opp, n)
        return move if team < 0 else team
    return _emit_invalid(spec, o, kn, move, my, n)
