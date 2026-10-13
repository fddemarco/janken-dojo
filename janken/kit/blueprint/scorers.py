"""Scorers (stage 6): every arm's record, counterfactually."""

import dataclasses
from typing import ClassVar

from .. import codes as c
from .base import Stage, Value


@dataclasses.dataclass(frozen=True)
class Scorer(Stage):
    """Keeps each arm's record, counterfactually: every arm, every round."""


@dataclasses.dataclass(frozen=True)
class NoScore(Scorer):
    """No records (for the First selector)."""

    kind: ClassVar[int] = c.SC_NONE


@dataclasses.dataclass(frozen=True)
class Dirichlet(Scorer):
    """Decayed win / tie / loss counts: a Dirichlet posterior per arm."""

    kind: ClassVar[int] = c.SC_DIRICHLET
    decay: Value = 0.95

    def knobs(self) -> tuple[Value, ...]:
        return (self.decay,)


@dataclasses.dataclass(frozen=True)
class DecayedNet(Scorer):
    """A decayed net score: `decay * score + result` (result +1 / 0 / -1)."""

    kind: ClassVar[int] = c.SC_DECAYED
    decay: Value = 0.9

    def knobs(self) -> tuple[Value, ...]:
        return (self.decay,)


@dataclasses.dataclass(frozen=True)
class DropSwitch(Scorer):
    """A net score that drops to 0 on a loss with probability `p_reset` (1: always,
    no draw): re-adapts within a round to an opponent that switches."""

    kind: ClassVar[int] = c.SC_DROP_SWITCH
    p_reset: Value = 1.0

    def knobs(self) -> tuple[Value, ...]:
        return (self.p_reset,)
