"""Heuristics: one predictor played straight, the core of every L1 bot.

    Heuristic   one predictor (a signal, or a Replay of a whole bot) played with
                one rotation: copycat is LastMove(OPP) played COPY, frequency is
                Frequency(OPP) played BEAT. No aggregator, so it adds no level: a
                heuristic over a signal is L1, over a replay of an L3 bot L3.
    Silent      no prediction at all: the bot plays uniformly at random (nash).

lowering.py plays a Heuristic as a one-arm bandit with no scorer.
"""

import dataclasses

from .. import codes as c
from .base import ROTATIONS, check_side
from .predictor import Decorator, Leaf, Predictor
from .signals import Rotated, Signal, Sim


@dataclasses.dataclass(frozen=True)
class Silent(Leaf):
    """No proposal, ever: a heuristic over it plays at random. Not a stage: lowering
    leaves it out."""


@dataclasses.dataclass(frozen=True)
class Heuristic(Decorator):
    """`signal` played with `rotation`. A Rotated signal of one rotation (a named
    bot's arm, refs.py) adds its rotation to this one."""

    signal: Signal | Sim | Rotated | Silent = Silent()
    rotation: int = c.COPY

    def child(self) -> Predictor:
        return self.signal

    def played(self) -> tuple[Signal | Sim | Silent, int]:
        """The predictor it plays and the rotation it plays it with, a Rotated
        signal unwrapped."""
        check_side(self.rotation, ROTATIONS, "a rotation")
        if isinstance(self.signal, Rotated):
            check_side(len(self.signal.rotations), (1,), "a heuristic's rotations")
            return self.signal.signal, (self.signal.rotations[0] + self.rotation) % 3
        return self.signal, self.rotation
