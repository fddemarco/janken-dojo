"""Overlays (stage 7): transform the chosen move."""

import dataclasses
from typing import ClassVar

from .. import codes as c
from .base import Stage, Value, check_side


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
    """An Iliad fleet's handshake: a fixed opening, then a role move. Once a
    teammate is recognised, a SUPPORT throws the match to the CHAMPION. An
    IMPOSTOR plays a support's handshake, then beats the champion's throw move.
    `fleet` picks the handshake (ILIAD, ILIAD_V2, ILIAD_V3: fleets don't recognise each
    other). `vigilant` keeps checking the teammate after the role move: at the
    first round it doesn't throw (a support's ROCK, the champion's PAPER) the bot
    plays its own move for the rest of the match, so an impostor wins one round."""

    kind: ClassVar[int] = c.O_TEAM
    role: int = c.SUPPORT
    fleet: int = c.ILIAD
    vigilant: bool = False

    def params(self) -> tuple[int, ...]:
        return self.role, self.fleet, int(self.vigilant)

    def validate(self) -> None:
        check_side(self.role, (c.CHAMPION, c.SUPPORT, c.IMPOSTOR), "Team role")
        check_side(self.fleet, (c.ILIAD, c.ILIAD_V2, c.ILIAD_V3), "Team fleet")


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
