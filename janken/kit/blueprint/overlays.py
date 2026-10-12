"""Overlays (stage 7): transform the chosen move."""

import dataclasses
from typing import ClassVar

from .. import codes as c
from .base import MOVES, Stage, Value, check, check_side


@dataclasses.dataclass(frozen=True)
class Stall(Stage):
    """Pure random play on two triggers. Drawdown: the last `dd_window` rounds net
    `-dd_trigger` or worse, so stall `stall_rounds` rounds. Lead lock: the lead is
    safe by `lock_z` standard deviations of a random walk over the rounds left of
    `assumed_rounds`."""

    kind: ClassVar[int] = c.O_STALL
    dd_window: Value = 20
    dd_trigger: Value = 5
    stall_rounds: Value = 15
    lock_z: Value = 4.0
    assumed_rounds: Value = 200

    def knobs(self) -> tuple[Value, ...]:
        return (
            self.dd_window,
            self.dd_trigger,
            self.stall_rounds,
            self.lock_z,
            self.assumed_rounds,
        )

    def state(self) -> tuple[int, int]:
        return 0, 3


@dataclasses.dataclass(frozen=True)
class Team(Stage):
    """A fleet's handshake: a fixed opening (`handshake`, the fleet's own moves),
    then a role move. Once a teammate is recognised, a SUPPORT throws the match to
    the CHAMPION. An IMPOSTOR plays a support's handshake, then beats the
    champion's throw move. Fleets with different handshakes don't recognise each
    other. `vigilant` keeps checking the teammate after the role move: at the
    first round it doesn't throw (a support's ROCK, the champion's PAPER) the bot
    plays its own move for the rest of the match, so an impostor wins one round.

    A fleet's champion is usually declared by its bot file's `fleet` section
    (janken/botfile.py), which adds this overlay; its supports are the same bot
    with role SUPPORT."""

    kind: ClassVar[int] = c.O_TEAM
    role: int = c.SUPPORT
    handshake: tuple[int, ...] = ()
    vigilant: bool = False

    def knobs(self) -> tuple[Value, ...]:
        return self.handshake

    def params(self) -> tuple[int, ...]:
        return self.role, len(self.handshake), int(self.vigilant)

    def validate(self) -> None:
        check_side(self.role, (c.CHAMPION, c.SUPPORT, c.IMPOSTOR), "Team role")
        check(bool(self.handshake), "a Team's handshake needs at least one move")
        for move in self.handshake:
            check_side(move, MOVES, "a Team handshake's move")


@dataclasses.dataclass(frozen=True)
class EmitInvalid(Stage):
    """Returns INVALID in rounds `first_at` and `second_at` (-1: never), at most
    INVALID_MOVE_LIMIT - 1 times a match, so it never forfeits."""

    kind: ClassVar[int] = c.O_EMIT_INVALID
    first_at: Value = -1
    second_at: Value = -1

    def knobs(self) -> tuple[Value, ...]:
        return self.first_at, self.second_at


Overlay = Stall | Team | EmitInvalid
