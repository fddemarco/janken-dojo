"""Guards (stage 1): answer the round before any model does."""

import dataclasses
from typing import ClassVar

from .. import codes as c
from .base import MOVES, Stage, Value, check, check_side


@dataclasses.dataclass(frozen=True)
class Opening(Stage):
    """For the first `rounds` rounds, play `move` (RANDOM_MOVE: a random one)."""

    kind: ClassVar[int] = c.G_OPENING
    rounds: int = 1
    move: int = c.RANDOM_MOVE

    def params(self) -> tuple[int, ...]:
        return self.rounds, self.move

    def validate(self) -> None:
        check(self.rounds >= 1, "Opening needs rounds >= 1")
        check_side(self.move, MOVES + (c.RANDOM_MOVE,), "Opening move")


@dataclasses.dataclass(frozen=True)
class Noise(Stage):
    """With probability `p`, a uniformly random move (always draws once)."""

    kind: ClassVar[int] = c.G_NOISE
    p: Value = 0.0

    def knobs(self) -> tuple[Value, ...]:
        return (self.p,)


@dataclasses.dataclass(frozen=True)
class OnInvalid(Stage):
    """Once an invalid move is in the history (the `LAST` round or `ANY` round, of
    the opponent or of `BOTH`), CRASH (forfeit) or play at random. Without this
    guard the bot simply ignores invalid rounds, which is the robust choice."""

    kind: ClassVar[int] = c.G_ON_INVALID
    action: int = c.RANDOM_ACTION
    scope: int = c.ANY
    side: int = c.BOTH

    def params(self) -> tuple[int, ...]:
        return self.action, self.scope, self.side

    def validate(self) -> None:
        check_side(self.action, (c.CRASH_ACTION, c.RANDOM_ACTION), "OnInvalid action")
        check_side(self.scope, (c.LAST, c.ANY), "OnInvalid scope")
        check_side(self.side, (c.OPP, c.BOTH), "OnInvalid side")


Guard = Opening | Noise | OnInvalid
