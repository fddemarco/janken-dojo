"""What a learner sees of a match before it moves, as words.

A feature is a word with no spaces, `|` or `:` (Vowpal Wabbit's input format,
which hashes it), so any learner that takes sparse binary features can read it.
Moves are written R, P, S, and X for an invalid one.

    history  for each of the last `history` rounds (lag 1 is the last): each
             side's move and the pair (o1=R, m1=P, j1=PR), and from lag 2 the
             runs they end (os2=RP, js2=PRSR: the opponent's and both sides'
             last moves, newest first)
    experts  what each expert would play now, from our seat and from theirs
             (e0m=P, e0o=S): a kit bot's view of the match, which the learner
             learns how far to trust, and how to turn
"""

from collections.abc import Sequence

import numpy as np

from ..kit.moves import CRASH, INVALID
from ..spec import BotSpec
from .arena import SIDE_A, KitBot

LETTERS = "RPSX"
SEED_SHIFT = 32  # experts draw from streams of the match seed shifted past its bits


def history_tokens(my: np.ndarray, opp: np.ndarray, n: int, history: int) -> list[str]:
    """The words of the last `history` rounds before round n."""
    out: list[str] = []
    opp_run = joint_run = ""
    for lag in range(1, min(history, n) + 1):
        o, m = LETTERS[opp[n - lag]], LETTERS[my[n - lag]]
        opp_run += o
        joint_run += m + o
        out += [f"o{lag}={o}", f"m{lag}={m}", f"j{lag}={m}{o}"]
        if lag > 1:
            out += [f"os{lag}={opp_run}", f"js{lag}={joint_run}"]
    return out


def letter(move: int) -> str:
    """A move's letter (a crash reads as an invalid move)."""
    return LETTERS[INVALID if move == CRASH else move]


class Experts:
    """Kit bots played from both seats of a match, as features: each sees the
    match as it is (ours) and as the opponent sees it (theirs)."""

    def __init__(self, bots: Sequence[KitBot], theirs: Sequence[KitBot]) -> None:
        if len(bots) != len(theirs):
            raise ValueError("every expert sits in both seats")
        self.ours: tuple[KitBot, ...] = tuple(bots)
        self.theirs: tuple[KitBot, ...] = tuple(theirs)

    @classmethod
    def of(cls, specs: Sequence[BotSpec]) -> "Experts":
        """These bots as experts, each sitting in both seats."""
        return cls(
            [KitBot.of(s, SIDE_A) for s in specs], [KitBot.of(s, SIDE_A) for s in specs]
        )

    def __len__(self) -> int:
        return len(self.ours)

    def reset(self, seed: int, rounds: int) -> None:
        """A new match: every expert draws from its own stream of `seed`."""
        for k, (ours, theirs) in enumerate(zip(self.ours, self.theirs, strict=True)):
            ours.reset(seed ^ ((2 * k + 1) << SEED_SHIFT), rounds)
            theirs.reset(seed ^ ((2 * k + 2) << SEED_SHIFT), rounds)

    def tokens(self, my: np.ndarray, opp: np.ndarray, n: int) -> list[str]:
        """Each expert's move for round n, from our seat and from theirs."""
        out: list[str] = []
        for k, (ours, theirs) in enumerate(zip(self.ours, self.theirs, strict=True)):
            out.append(f"e{k}m={letter(ours.move(my, opp, n))}")
            out.append(f"e{k}o={letter(theirs.move(opp, my, n))}")
        return out
