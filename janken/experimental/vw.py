"""An online Vowpal Wabbit learner as an arena player.

Each round it learns, from the round just played, what each move would have
scored given the features it chose on (cost-sensitive, one cost per move: 0 a
win, 1 a draw, 2 a loss), then picks the move its model expects to cost least
on the next round's features (janken/experimental/features.py). Every match
starts from an empty model, as a bot starts from an empty history: what is
learned is how to adapt within a match, never the opponents themselves.

    vw_args   Vowpal Wabbit's arguments: a cost-sensitive reduction over the
              three moves (`--csoaa 3`), and how it learns
    history   rounds of history the features read
    explore   the chance of a uniformly random move (unpredictability)
"""

import dataclasses
import random

import numpy as np
import vowpalwabbit

from ..kit.moves import INVALID
from .arena import score
from .features import Experts, history_tokens

COST_OF = {1: 0, 0: 1, -1: 2}  # a move's cost by its outcome: win, draw, loss
NO_EXPERTS = Experts((), ())


@dataclasses.dataclass(frozen=True)
class Settings:
    """The learner's settings (janken.toml's [arena])."""

    vw_args: str
    history: int
    explore: float


def label(theirs: int) -> str:
    """The costs of each move (VW's classes 1..3 = R, P, S) vs `theirs`."""
    return " ".join(f"{m + 1}:{COST_OF[score(m, theirs)]}" for m in range(3))


class VWPlayer:
    """Vowpal Wabbit, learning online which move pays from the match so far."""

    def __init__(self, settings: Settings, experts: Experts = NO_EXPERTS) -> None:
        self.settings: Settings = settings
        self.experts: Experts = experts
        self.model: vowpalwabbit.Workspace = vowpalwabbit.Workspace(settings.vw_args)
        self.rng: random.Random = random.Random()
        self.chosen_on: str = ""  # the features of the move last played

    def reset(self, seed: int, rounds: int) -> None:
        self.model.finish()
        self.model = vowpalwabbit.Workspace(self.settings.vw_args)
        self.rng = random.Random(seed)
        self.experts.reset(seed, rounds)
        self.chosen_on = ""

    def features(self, my: np.ndarray, opp: np.ndarray, n: int) -> str:
        """Round n's features, in VW's format."""
        history = history_tokens(my, opp, n, self.settings.history)
        line = " |h " + " ".join(history)
        if len(self.experts):
            line += " |e " + " ".join(self.experts.tokens(my, opp, n))
        return line

    def move(self, my: np.ndarray, opp: np.ndarray, n: int) -> int:
        if n > 0 and opp[n - 1] != INVALID:
            self.model.learn(label(int(opp[n - 1])) + self.chosen_on)
        self.chosen_on = self.features(my, opp, n)
        predicted = int(self.model.predict(self.chosen_on)) - 1
        if self.rng.random() < self.settings.explore:
            return self.rng.randrange(3)
        return predicted
