"""Turn a kernel's raw moves and status row into a MatchResult."""

import numpy as np

from ..kit.moves import INVALID
from ..match import INVALID_MOVE_LIMIT, MatchResult
from .kernel import FF_CRASHED, FF_INVALID, FF_NONE

# Transcript characters by move code.
MOVE_CHARS = np.array([ord("r"), ord("p"), ord("s"), ord("x")], dtype=np.uint8)

FORFEIT_REASONS = {
    FF_CRASHED: "crashed",
    FF_INVALID: f"returned {INVALID_MOVE_LIMIT} invalid moves",
}


def match_result(name_a, name_b, moves, status=None) -> MatchResult:
    """A MatchResult from one match's int8[rounds, 2] moves and its
    (rounds played, forfeit a, forfeit b) status (default: all played, no forfeit).
    An invalid move loses its round; both invalid is a draw."""
    played, ff_a, ff_b = (len(moves), FF_NONE, FF_NONE) if status is None else status
    moves = moves[:played]
    a = moves[:, 0].astype(np.int64)
    b = moves[:, 1].astype(np.int64)
    bad_a = a == INVALID
    bad_b = b == INVALID
    valid = ~bad_a & ~bad_b
    diff = (a - b) % 3  # 1: a wins, 2: b wins, 0: draw
    return MatchResult(
        bot_a=name_a,
        bot_b=name_b,
        wins_a=int((valid & (diff == 1)).sum() + (bad_b & ~bad_a).sum()),
        wins_b=int((valid & (diff == 2)).sum() + (bad_a & ~bad_b).sum()),
        draws=int((valid & (diff == 0)).sum() + (bad_a & bad_b).sum()),
        forfeit_a=FORFEIT_REASONS.get(int(ff_a)),
        forfeit_b=FORFEIT_REASONS.get(int(ff_b)),
        moves=MOVE_CHARS[moves].reshape(-1).tobytes().decode("ascii"),
    )
