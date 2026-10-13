"""The blueprint's foundations: knobs, the stage base class, validation, shared constants."""

import dataclasses
from collections.abc import Sequence
from typing import ClassVar

from .. import codes as c
from ..moves import PAPER, ROCK, SCISSORS


@dataclasses.dataclass(frozen=True)
class Knob:
    """A stage knob read from the bot's parameter of this name (its defaults key)."""

    name: str


Value = float | int | Knob


MOVES = (ROCK, PAPER, SCISSORS)


ROTATIONS = (c.COPY, c.BEAT, c.BEAT_BEAT)

ALL_ROTATIONS = (c.BEAT, c.BEAT_BEAT, c.COPY)  # Iocaine's P0, P1, P2


MAX_NGRAM_ORDER = 4


MAX_REPLAY_DEPTH = 3  # replays nest three deep (an L5 replaying an L4)


class BlueprintError(ValueError):
    """A blueprint that can't be compiled."""


@dataclasses.dataclass(frozen=True)
class Stage:
    """A pipeline stage: its kind code, knobs, literal parameters and state sizes.

    `declarable` is False for a stage only the compiler builds (bot files don't
    name it: janken/kit/declare.py)."""

    kind: ClassVar[int] = -1
    declarable: ClassVar[bool] = True

    def knobs(self) -> tuple[Value, ...]:
        return ()

    def params(self) -> tuple[int, ...]:
        return ()

    def state(self) -> tuple[int, int]:
        return 0, 0

    def validate(self) -> None:
        """Raise BlueprintError when the stage's literals make no sense."""


def check(ok: bool, message: str) -> None:
    """Raise BlueprintError with `message` unless `ok`."""
    if not ok:
        raise BlueprintError(message)


def check_side(side: int, allowed: Sequence[int], what: str) -> None:
    """Raise BlueprintError unless `side` is one of `allowed`."""
    check(side in allowed, f"{what} must be one of {allowed}, got {side!r}")
