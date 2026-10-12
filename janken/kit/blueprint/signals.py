"""Signals (stage 4): the predictor tree's leaves, and the decorators that wrap one.

A signal proposes a symbol each round (usually the opponent's predicted move), or
none. Sim and Rotated decorate one (see predictor.py)."""

import dataclasses
from typing import ClassVar

from .. import codes as c
from ..moves import ROCK
from .base import MAX_NGRAM_ORDER, MOVES, Stage, Value, check, check_side
from .predictor import Decorator, Leaf, Predictor


@dataclasses.dataclass(frozen=True)
class Signal(Leaf, Stage):
    """A signal: proposes a symbol each round, or none."""


@dataclasses.dataclass(frozen=True)
class LastMove(Signal):
    """The last move of `of` (OPP: the opponent, MY: ours)."""

    kind: ClassVar[int] = c.S_LAST
    of: int = c.OPP

    def params(self) -> tuple[int, ...]:
        return (self.of,)

    def validate(self) -> None:
        check_side(self.of, (c.OPP, c.MY), "LastMove of")


@dataclasses.dataclass(frozen=True)
class Frequency(Signal):
    """The most frequent move of `of`, over counts decayed by `decay` per round."""

    kind: ClassVar[int] = c.S_FREQ
    of: int = c.OPP
    decay: Value = 1.0

    def knobs(self) -> tuple[Value, ...]:
        return (self.decay,)

    def params(self) -> tuple[int, ...]:
        return (self.of,)

    def state(self) -> tuple[int, int]:
        return 3, 0

    def validate(self) -> None:
        check_side(self.of, (c.OPP, c.MY), "Frequency of")


def _rows(ctx: int, order: int) -> int:
    return (9 if ctx == c.JOINT else 3) ** order


@dataclasses.dataclass(frozen=True)
class NGram(Signal):
    """The next move of `of` after the last `order` symbols of `ctx`: a decayed
    count table per context, read by argmax (or sampled, with `sample`)."""

    kind: ClassVar[int] = c.S_NGRAM
    order: int = 1
    ctx: int = c.OPP
    of: int = c.OPP
    decay: Value = 1.0
    sample: bool = False

    def knobs(self) -> tuple[Value, ...]:
        return (self.decay,)

    def params(self) -> tuple[int, ...]:
        return self.of, self.ctx, self.order, int(self.sample)

    def state(self) -> tuple[int, int]:
        return _rows(self.ctx, self.order) * 3, 0

    def validate(self) -> None:
        check_side(self.of, (c.OPP, c.MY), "NGram of")
        check_side(self.ctx, (c.OPP, c.MY, c.JOINT), "NGram ctx")
        check(0 <= self.order <= MAX_NGRAM_ORDER, "NGram order must be 0..4")
        check(
            not (self.ctx == c.JOINT and self.order > 3),
            "joint NGram order must be <= 3",
        )


@dataclasses.dataclass(frozen=True)
class Backoff(Signal):
    """word2janken's predictor: the next move of `of` after the longest context of
    `ctx` (max_order down to 0) seen before, by plain counts, first maximum."""

    kind: ClassVar[int] = c.S_BACKOFF
    max_order: int = 3
    ctx: int = c.JOINT
    of: int = c.OPP

    def params(self) -> tuple[int, ...]:
        return self.of, self.ctx, self.max_order

    def state(self) -> tuple[int, int]:
        return sum(_rows(self.ctx, o) for o in range(self.max_order + 1)) * 3, 0

    def validate(self) -> None:
        check_side(self.of, (c.OPP, c.MY), "Backoff of")
        check_side(self.ctx, (c.OPP, c.MY, c.JOINT), "Backoff ctx")
        check(0 <= self.max_order <= 3, "Backoff max_order must be 0..3")


@dataclasses.dataclass(frozen=True)
class LongestMatch(Signal):
    """History matching: the move of `of` that followed the most recent earlier
    repeat of the longest suffix (up to `max_len`) of `ctx`."""

    kind: ClassVar[int] = c.S_MATCH
    max_len: Value = 12
    ctx: int = c.JOINT
    of: int = c.OPP

    def knobs(self) -> tuple[Value, ...]:
        return (self.max_len,)

    def params(self) -> tuple[int, ...]:
        return self.of, self.ctx

    def validate(self) -> None:
        check_side(self.of, (c.OPP, c.MY), "LongestMatch of")
        check_side(self.ctx, (c.OPP, c.MY, c.JOINT), "LongestMatch ctx")


@dataclasses.dataclass(frozen=True)
class SecondMatch(LongestMatch):
    """Second-order history matching (rps_kaggle section 4.2): find the longest earlier
    repeat of `ctx`'s suffix, as LongestMatch does, then that matched point's own
    longest earlier repeat, and read the move of `of` that followed it: an older
    witness of the same pattern. Keeps each round's match end (one per-round slot)."""

    kind: ClassVar[int] = c.S_MATCH2


@dataclasses.dataclass(frozen=True)
class Relative(Signal):
    """Rotation model: the opponent's move relative to `ref`'s last move (OPP or
    MY), by decayed counts, optionally per outcome of the last round."""

    kind: ClassVar[int] = c.S_RELATIVE
    ref: int = c.OPP
    by_outcome: bool = False
    decay: Value = 1.0

    def knobs(self) -> tuple[Value, ...]:
        return (self.decay,)

    def params(self) -> tuple[int, ...]:
        return self.ref, int(self.by_outcome)

    def state(self) -> tuple[int, int]:
        return (9 if self.by_outcome else 3), 0

    def validate(self) -> None:
        check_side(self.ref, (c.OPP, c.MY), "Relative ref")


@dataclasses.dataclass(frozen=True)
class React(Signal):
    """After we win, the opponent beats our last move; otherwise it repeats its own."""

    kind: ClassVar[int] = c.S_REACT


@dataclasses.dataclass(frozen=True)
class Constant(Signal):
    """Always `move`."""

    kind: ClassVar[int] = c.S_CONSTANT
    move: int = ROCK

    def params(self) -> tuple[int, ...]:
        return (self.move,)

    def validate(self) -> None:
        check_side(self.move, MOVES, "Constant move")


@dataclasses.dataclass(frozen=True)
class Cycle(Signal):
    """rock, paper, scissors (`step` 1) or the reverse (`step` 2), by round."""

    kind: ClassVar[int] = c.S_CYCLE
    step: Value = 1

    def knobs(self) -> tuple[Value, ...]:
        return (self.step,)


@dataclasses.dataclass(frozen=True)
class Biased(Signal):
    """A weighted coin: rock `p_rock`, paper `p_paper`, scissors the rest."""

    kind: ClassVar[int] = c.S_BIASED
    p_rock: Value = 1.0 / 3.0
    p_paper: Value = 1.0 / 3.0

    def knobs(self) -> tuple[Value, ...]:
        return self.p_rock, self.p_paper


@dataclasses.dataclass(frozen=True)
class WinStay(Signal):
    """Our last move, shifted by `shift` after a loss (win-stay, lose-shift)."""

    kind: ClassVar[int] = c.S_WIN_STAY
    shift: Value = 1

    def knobs(self) -> tuple[Value, ...]:
        return (self.shift,)


@dataclasses.dataclass(frozen=True)
class Rarest(Signal):
    """The least frequent move of `of`, over counts decayed by `decay` per round:
    what a player who evens out their counts plays next."""

    kind: ClassVar[int] = c.S_RAREST
    of: int = c.OPP
    decay: Value = 1.0

    def knobs(self) -> tuple[Value, ...]:
        return (self.decay,)

    def params(self) -> tuple[int, ...]:
        return (self.of,)

    def state(self) -> tuple[int, int]:
        return 3, 0

    def validate(self) -> None:
        check_side(self.of, (c.OPP, c.MY), "Rarest of")


MAX_PERIOD = 24


@dataclasses.dataclass(frozen=True)
class Period(Signal):
    """Period detection: for every period p in 1..`max_period`, a score of how
    often `of`'s move repeated the one p rounds before (decayed by `decay`); the
    move p rounds ago of the best-scored p (the shortest among ties)."""

    kind: ClassVar[int] = c.S_PERIOD
    of: int = c.OPP
    max_period: int = 12
    decay: Value = 0.95

    def knobs(self) -> tuple[Value, ...]:
        return (self.decay,)

    def params(self) -> tuple[int, ...]:
        return self.of, self.max_period

    def state(self) -> tuple[int, int]:
        return self.max_period, 0

    def validate(self) -> None:
        check_side(self.of, (c.OPP, c.MY), "Period of")
        check(
            1 <= self.max_period <= MAX_PERIOD,
            f"Period max_period must be 1..{MAX_PERIOD}",
        )


@dataclasses.dataclass(frozen=True)
class ScoreState(Signal):
    """The most frequent move of `of` given the match score so far (behind, level
    or ahead, from our side of the history), over counts decayed by `decay`."""

    kind: ClassVar[int] = c.S_SCORE_STATE
    of: int = c.OPP
    decay: Value = 1.0

    def knobs(self) -> tuple[Value, ...]:
        return (self.decay,)

    def params(self) -> tuple[int, ...]:
        return (self.of,)

    def state(self) -> tuple[int, int]:
        return 10, 0  # f: a count row per score state (9), the running score (1)

    def validate(self) -> None:
        check_side(self.of, (c.OPP, c.MY), "ScoreState of")


@dataclasses.dataclass(frozen=True)
class Geometry(Signal):
    """superant's geometry: a learned complex offset (rate `alpha`) rotates the
    longest joint match's next opponent move into a distribution over our moves,
    which is sampled (or read by argmax). The symbol is the opponent move our
    chosen move beats, so play it with BEAT."""

    kind: ClassVar[int] = c.S_GEOMETRY
    alpha: Value = 0.05
    max_len: Value = 20
    sample: bool = True

    def knobs(self) -> tuple[Value, ...]:
        return self.alpha, self.max_len

    def params(self) -> tuple[int, ...]:
        return (int(self.sample),)

    def state(self) -> tuple[int, int]:
        return 5, 2  # f: the learned offset (2), the move distribution (scratch, 3)


@dataclasses.dataclass(frozen=True)
class Oracle(Signal):
    """Research only, never submitted: a mock of a bot of any level
    (janken/mocks.py). The referee reveals the opponent's move and level; the
    Oracle wins with chance `wins[k]` vs a level-(k + 1) opponent (the last entry
    for higher levels; ties and losses split the rest), and with (win, tie)
    `oracle` vs another Oracle (by default a draw). A bot that is only an Oracle
    never runs its pipeline: the referee plays the drawn outcome. As an arm, its
    symbol is the one whose BEAT has the outcome. Without the referee (tests,
    exports) it has no symbol."""

    kind: ClassVar[int] = c.S_ORACLE
    wins: tuple[Value, ...] = (1.0 / 3.0,)
    oracle: tuple[Value, ...] = (0.0, 1.0)

    def knobs(self) -> tuple[Value, ...]:
        return (*self.wins, *self.oracle)

    def params(self) -> tuple[int, ...]:
        return (len(self.wins),)

    def state(self) -> tuple[int, int]:
        return 0, 3  # i: the revealed round + 1, the opponent's move and level

    def validate(self) -> None:
        check(len(self.wins) >= 1, "an Oracle needs a win chance per level")
        check(len(self.oracle) == 2, "an Oracle's `oracle` is (win, tie)")


@dataclasses.dataclass(frozen=True)
class Sim(Decorator):
    """A model of us: `signal` run from the opponent's side of the board (histories
    swapped). The opponent plays what beats its prediction of us, so the symbol is
    that move."""

    signal: Signal

    def child(self) -> Predictor:
        return self.signal


@dataclasses.dataclass(frozen=True)
class Rotated(Decorator):
    """`signal` with its own rotations instead of its bandit's."""

    signal: Signal | Sim  # a Replay or a NaiveBayes is a Signal too
    rotations: tuple[int, ...]

    def child(self) -> Predictor:
        return self.signal
