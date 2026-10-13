"""Selectors (stage 6): pick the arm to play."""

import dataclasses
from typing import ClassVar

from .. import codes as c
from .base import MOVES, Stage, Value, check, check_side


@dataclasses.dataclass(frozen=True)
class Selector(Stage):
    """Picks the arm to play."""


@dataclasses.dataclass(frozen=True)
class First(Selector):
    """The first arm with a move, else `fallback` (RANDOM_MOVE: a random move)."""

    kind: ClassVar[int] = c.SEL_FIRST
    fallback: int = c.RANDOM_MOVE

    def params(self) -> tuple[int, ...]:
        return (self.fallback,)

    def validate(self) -> None:
        check_side(self.fallback, MOVES + (c.RANDOM_MOVE,), "First fallback")


@dataclasses.dataclass(frozen=True)
class Greedy(Selector):
    """The best-scored arm; ties go to the FIRST one or a RANDOM one."""

    kind: ClassVar[int] = c.SEL_GREEDY
    ties: int = c.TIES_RANDOM

    def params(self) -> tuple[int, ...]:
        return (self.ties,)

    def validate(self) -> None:
        check_side(self.ties, (c.TIES_FIRST, c.TIES_RANDOM), "Greedy ties")


@dataclasses.dataclass(frozen=True)
class Thompson(Selector):
    """Thompson sampling of each arm's Dirichlet, counts times `sharp`; the arm
    with the best sampled P(win) - P(loss) plays."""

    kind: ClassVar[int] = c.SEL_THOMPSON
    sharp: Value = 1.0

    def knobs(self) -> tuple[Value, ...]:
        return (self.sharp,)


@dataclasses.dataclass(frozen=True)
class SampledVote(Selector):
    """Plays a move sampled from the arms' vote: each arm weighs exp(score /
    `temperature`) for its move (the random arm for all three)."""

    kind: ClassVar[int] = c.SEL_VOTE
    temperature: Value = 0.2

    def knobs(self) -> tuple[Value, ...]:
        return (self.temperature,)


@dataclasses.dataclass(frozen=True)
class Gatekeeper(Selector):
    """A Gate, compiled (lowering.py): the selector over a flat bandit whose last
    `experts` arms are the gated experts and the rest the main bandit, sampled by
    Thompson (counts times `sharp`). See composites.Gate for the rules. Bot files
    declare the Gate, never this."""

    kind: ClassVar[int] = c.SEL_KEEPER
    declarable: ClassVar[bool] = False
    edge: Value = 0.05
    decay: Value = 1.0
    warmup: Value = 20
    sharp: Value = 1.0
    rule: int = c.EDGE
    experts: int = 1  # gated experts, the last arms (more than one: LEADER only)

    def knobs(self) -> tuple[Value, ...]:
        return self.edge, self.decay, self.warmup, self.sharp

    def params(self) -> tuple[int, ...]:
        return self.rule, self.experts

    def state(self) -> tuple[int, int]:
        # f: the gated arm's record, the main expert's; i: the gated arm's move,
        # its round + 1, k, the main expert's move, which expert the hold keeps
        n = self.experts + 1  # LEADER: a record and a move per expert
        return max(6, 3 * n), max(5, 3 + n)

    def validate(self) -> None:
        check_side(
            self.rule,
            (
                c.EDGE,
                c.ANTI_FIRST,
                c.BANDIT,
                c.ANTI_FIRST_HOLD,
                c.MAIN_FIRST,
                c.LEADER,
                c.LEADER_PRIORITY,
            ),
            "Gatekeeper rule",
        )
        check(self.experts >= 1, "a Gate gates one expert or more")
        check(
            self.experts == 1 or self.rule in (c.LEADER, c.LEADER_PRIORITY),
            "only the LEADER rules gate more than one arm (one expert, one rotation)",
        )


@dataclasses.dataclass(frozen=True)
class ChooseSelector:
    """One of `options`, picked by the integer value of `index` (for tuning)."""

    index: Value
    options: tuple[Selector, ...]
