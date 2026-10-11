"""Bot blueprints: what a bot is made of, declared as data and compiled for the pipeline.

Every bot has the same anatomy (janken/kit/pipeline.py runs it, in this order):

1. guards     answer the round before any model does: an opening, a noise floor,
              what to do once the history holds an invalid move.
2. view       the models only ever see rounds where both moves are valid.
3. track      every stateful stage folds in the rounds it hasn't seen, and the
              arms proposed last round are scored against what really happened.
4. signals    each proposes a symbol (usually the opponent's predicted move), or
              none: opponent models, generators, sims of the opponent's model of us.
5. move choice  each signal's symbol becomes one arm per rotation: COPY it, BEAT it,
              or BEAT_BEAT it (beat the move that beats it). An optional random arm
              is the defence when nothing works.
6. select     a scorer keeps each arm's record and a selector picks the arm to play.
7. overlays   transform the chosen move: stalling, a team handshake, spending the
              invalid moves the rules allow.

A bot file (bots/<name>.yaml) declares a blueprint plus its defaults; declare.py
turns its YAML into these dataclasses. A stage knob is either a literal or a
`Knob("NAME")` (`$NAME` in YAML) read from the bot's parameters, so tuning and
variants work on any stage:

    blueprint = Blueprint(
        guards=(Noise(Knob("NOISE")), Opening(1, ROCK), OnInvalid(CRASH_ACTION, LAST, OPP)),
        signals=(LastMove(OPP),),
        rotations=(BEAT,),
    )
    state, spec, knobs = blueprint.compile({"NOISE": 0.05})

`compile` validates the blueprint, lays out the state every stage needs in the
bot's `f` / `i` arrays and encodes it all as the arrays the pipeline reads (see
codes.py). A new idea is a new stage class here plus its compiled half.
"""

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import ClassVar, NamedTuple

import numpy as np

from . import codes as c
from .moves import PAPER, ROCK, SCISSORS


@dataclasses.dataclass(frozen=True)
class Knob:
    """A stage knob read from the bot's parameter of this name (its defaults key)."""

    name: str


Value = float | int | Knob

MOVES = (ROCK, PAPER, SCISSORS)
ROTATIONS = (c.COPY, c.BEAT, c.BEAT_BEAT)
ALL_ROTATIONS = (c.BEAT, c.BEAT_BEAT, c.COPY)  # Iocaine's P0, P1, P2
MAX_NGRAM_ORDER = 4
MAX_REPLAY_DEPTH = 2  # a replay may contain replays, which may not


class BlueprintError(ValueError):
    """A blueprint that can't be compiled."""


@dataclasses.dataclass(frozen=True)
class Stage:
    """A pipeline stage: its kind code, knobs, literal parameters and state sizes."""

    kind: ClassVar[int] = -1

    def knobs(self) -> tuple[Value, ...]:
        return ()

    def params(self) -> tuple[int, ...]:
        return ()

    def state(self) -> tuple[int, int]:
        return 0, 0

    def validate(self) -> None:
        """Raise BlueprintError when the stage's literals make no sense."""


def _check(ok: bool, message: str) -> None:
    if not ok:
        raise BlueprintError(message)


def _check_side(side: int, allowed: Sequence[int], what: str) -> None:
    _check(side in allowed, f"{what} must be one of {allowed}, got {side!r}")


# --- 1. guards ---------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Opening(Stage):
    """For the first `rounds` rounds, play `move` (RANDOM_MOVE: a random one)."""

    kind: ClassVar[int] = c.G_OPENING
    rounds: int = 1
    move: int = c.RANDOM_MOVE

    def params(self) -> tuple[int, ...]:
        return self.rounds, self.move

    def validate(self) -> None:
        _check(self.rounds >= 1, "Opening needs rounds >= 1")
        _check_side(self.move, MOVES + (c.RANDOM_MOVE,), "Opening move")


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
        _check_side(self.action, (c.CRASH_ACTION, c.RANDOM_ACTION), "OnInvalid action")
        _check_side(self.scope, (c.LAST, c.ANY), "OnInvalid scope")
        _check_side(self.side, (c.OPP, c.BOTH), "OnInvalid side")


Guard = Opening | Noise | OnInvalid


# --- 4. signals --------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Signal(Stage):
    """A signal: proposes a symbol each round, or none."""


@dataclasses.dataclass(frozen=True)
class LastMove(Signal):
    """The last move of `of` (OPP: the opponent, MY: ours)."""

    kind: ClassVar[int] = c.S_LAST
    of: int = c.OPP

    def params(self) -> tuple[int, ...]:
        return (self.of,)

    def validate(self) -> None:
        _check_side(self.of, (c.OPP, c.MY), "LastMove of")


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
        _check_side(self.of, (c.OPP, c.MY), "Frequency of")


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
        _check_side(self.of, (c.OPP, c.MY), "NGram of")
        _check_side(self.ctx, (c.OPP, c.MY, c.JOINT), "NGram ctx")
        _check(0 <= self.order <= MAX_NGRAM_ORDER, "NGram order must be 0..4")
        _check(
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
        _check_side(self.of, (c.OPP, c.MY), "Backoff of")
        _check_side(self.ctx, (c.OPP, c.MY, c.JOINT), "Backoff ctx")
        _check(0 <= self.max_order <= 3, "Backoff max_order must be 0..3")


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
        _check_side(self.of, (c.OPP, c.MY), "LongestMatch of")
        _check_side(self.ctx, (c.OPP, c.MY, c.JOINT), "LongestMatch ctx")


@dataclasses.dataclass(frozen=True)
class SecondMatch(LongestMatch):
    """Second-order history matching (rps_kaggle §4.2): find the longest earlier
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
        _check_side(self.ref, (c.OPP, c.MY), "Relative ref")


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
        _check_side(self.move, MOVES, "Constant move")


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
class Sim:
    """A model of us: `signal` run from the opponent's side of the board (histories
    swapped). The opponent plays what beats its prediction of us, so the symbol is
    that move."""

    signal: Signal


@dataclasses.dataclass(frozen=True)
class Rotated:
    """`signal` with its own rotations instead of the ensemble's."""

    signal: "Signal | Sim | Replay"
    rotations: tuple[int, ...]


@dataclasses.dataclass(frozen=True)
class Replay(Signal):
    """A model of us: a whole bot core (`ensemble`) replayed from the opponent's
    side. The symbol is its most likely move: the arm with the best score, or,
    with `draws` > 0, the move its Thompson sampling picks most often in that many
    draws of every arm's Dirichlet (a scored random arm counts for each move)."""

    kind: ClassVar[int] = c.S_REPLAY
    ensemble: "Ensemble"
    draws: int = 0

    def params(self) -> tuple[int, ...]:
        return (self.draws,)

    def validate(self) -> None:
        _check(self.draws >= 0, "Replay draws must be >= 0")
        _check(
            self.draws == 0 or isinstance(self.ensemble.scorer, Dirichlet),
            "Replay draws sample a Dirichlet: use the Dirichlet scorer",
        )


@dataclasses.dataclass(frozen=True)
class NaiveBayes(Signal):
    """TPI-lite (rps_kaggle §6): a naive-Bayes combiner of the ensemble's other
    signals (other NaiveBayes ones excluded). Per input it keeps counts, decayed
    by `decay`, of its symbol (NO_MOVE included) against the opponent's real move;
    the posterior over the opponent's next move multiplies those likelihoods with
    a decayed prior. The symbol is the opponent move that our expected-score-best
    move beats, so play it with BEAT."""

    kind: ClassVar[int] = c.S_BAYES
    decay: Value = 0.95

    def knobs(self) -> tuple[Value, ...]:
        return (self.decay,)


def bayes_size(inputs: int) -> int:
    """NaiveBayes's f block over an ensemble of `inputs` signals: the prior, then
    per signal a (symbol or NO_MOVE) x (opponent move) count table."""
    return 3 + inputs * 4 * 3


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
        _check(len(self.wins) >= 1, "an Oracle needs a win chance per level")
        _check(len(self.oracle) == 2, "an Oracle's `oracle` is (win, tie)")


SignalLike = Signal | Sim | Rotated


# --- 6. scorers and selectors ------------------------------------------------


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
        _check_side(self.fallback, MOVES + (c.RANDOM_MOVE,), "First fallback")


@dataclasses.dataclass(frozen=True)
class Greedy(Selector):
    """The best-scored arm; ties go to the FIRST one or a RANDOM one."""

    kind: ClassVar[int] = c.SEL_GREEDY
    ties: int = c.TIES_RANDOM

    def params(self) -> tuple[int, ...]:
        return (self.ties,)

    def validate(self) -> None:
        _check_side(self.ties, (c.TIES_FIRST, c.TIES_RANDOM), "Greedy ties")


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
    """Two experts in one ensemble: its last arm (the gated expert, e.g. a replay)
    and the main expert, Thompson sampling (counts times `sharp`) over every other
    arm. The gatekeeper keeps the gated arm's own Dirichlet record, decayed by
    `decay`, every round, played or not, and with `rule`:

    EDGE        from round `warmup` on, the gated arm plays while its posterior
                mean P(win) - P(loss) is above `edge`, else the main expert;
    ANTI_FIRST  the gated arm plays unless, from round `warmup` on, the main
                expert's record (its proposal, kept every round too) beats it
                by more than `edge`;
    BANDIT      Thompson sampling (`sharp`) between the two experts' records;
    ANTI_FIRST_HOLD  ANTI_FIRST, but once on the main expert it stays there
                until the gated arm leads it by more than `edge` (hysteresis);
    MAIN_FIRST  the main expert first; from round `warmup` on, the gated arm
                once it leads the main expert by more than `edge`, kept until
                the main expert leads it by more than `edge` (hysteresis);
    LEADER      MAIN_FIRST over the main expert and the last `experts` arms: the
                best-scored expert takes over once it leads the current one by
                more than `edge`;
    LEADER_PRIORITY  LEADER, but from a gated expert only the main expert or
                the last gated one (e.g. the anti expert) can take over.
    """

    kind: ClassVar[int] = c.SEL_KEEPER
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
        _check_side(
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
        _check(self.experts >= 1, "a Gatekeeper gates one expert or more")
        _check(
            self.experts == 1 or self.rule in (c.LEADER, c.LEADER_PRIORITY),
            "only the LEADER rules gate more than one expert",
        )


@dataclasses.dataclass(frozen=True)
class ChooseSelector:
    """One of `options`, picked by the integer value of `index` (for tuning)."""

    index: Value
    options: tuple[Selector, ...]


# --- 7. overlays -------------------------------------------------------------


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
        _check_side(self.role, (c.CHAMPION, c.SUPPORT, c.IMPOSTOR), "Team role")
        _check_side(self.fleet, (c.ILIAD, c.ILIAD_V2, c.ILIAD_V3), "Team fleet")


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


# --- the blueprint -----------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Ensemble:
    """Signals x rotations = arms, plus an optional random arm, with a scorer."""

    signals: tuple[SignalLike, ...] = ()
    rotations: tuple[int, ...] = (c.BEAT,)
    scorer: Scorer = NoScore()
    random_arm: int = c.RA_NONE


@dataclasses.dataclass(frozen=True)
class Blueprint:
    """A whole bot: guards, a core ensemble with its selector, overlays."""

    guards: tuple[Guard, ...] = ()
    signals: tuple[SignalLike, ...] = ()
    rotations: tuple[int, ...] = (c.BEAT,)
    scorer: Scorer = NoScore()
    random_arm: int = c.RA_NONE
    selector: Selector | ChooseSelector = First()
    overlays: tuple[Overlay, ...] = ()

    @classmethod
    def around(
        cls,
        core: Ensemble,
        selector: "Selector | ChooseSelector",
        guards: tuple[Guard, ...] = (),
        overlays: tuple[Overlay, ...] = (),
    ) -> "Blueprint":
        """A blueprint built around a ready-made core (see presets.py)."""
        return cls(
            guards=guards,
            signals=core.signals,
            rotations=core.rotations,
            scorer=core.scorer,
            random_arm=core.random_arm,
            selector=selector,
            overlays=overlays,
        )

    @property
    def core(self) -> Ensemble:
        return Ensemble(self.signals, self.rotations, self.scorer, self.random_arm)

    def compile(self, defaults: Mapping[str, float | int]) -> "Compiled":
        """Validate and encode the blueprint for a bot with these defaults."""
        return _Encoder(defaults).encode(self)


class Compiled(NamedTuple):
    """A compiled blueprint: `state, spec, knobs = blueprint.compile(defaults)`.

    `state` is (f size, fixed i size, per-round i slots): every match, the bot gets
    fresh arrays, its i grown by one slot of rounds + 1 cells per per-round slot
    (the per-match workspace: the valid-only history and the match indexes).
    """

    state: tuple[int, int, int]
    spec: np.ndarray
    knobs: np.ndarray

    def new_state(self, rounds: int) -> tuple[np.ndarray, np.ndarray]:
        """Fresh (f, i) for a match of `rounds` rounds (the engine generates the
        same allocation, compiled; see janken/engine/build.py)."""
        f_size, i_size, per_round = self.state
        stride = rounds + 1
        i = np.zeros(i_size + per_round * stride, np.int64)
        at = int(self.spec[c.H_ROUNDS_I])
        i[at] = stride
        i[at + 1] = i_size
        return np.zeros(f_size, np.float64), i


def _unwrap(signal: SignalLike) -> tuple[Signal, bool, tuple[int, ...]]:
    """(the signal, whether it's a sim, its own rotations or ())."""
    rotations: tuple[int, ...] = ()
    if isinstance(signal, Rotated):
        rotations = signal.rotations
        signal = signal.signal
    if isinstance(signal, Sim):
        return signal.signal, True, rotations
    return signal, False, rotations


def _stream(signal: Signal, swapped: bool) -> int:
    """The history stream a matcher reads (STREAM_*), or -1 for other signals.

    A swapped view (a sim, a replay) reads OPP as MY and back; JOINT's repeats are
    the same rounds either way."""
    if isinstance(signal, Geometry):
        return c.STREAM_JOINT
    if not isinstance(signal, LongestMatch):
        return -1
    if signal.ctx == c.JOINT:
        return c.STREAM_JOINT
    mine = (signal.ctx == c.MY) != swapped
    return c.STREAM_MY if mine else c.STREAM_OPP


def _selector_options(selector: Selector | ChooseSelector) -> tuple[Selector, ...]:
    if isinstance(selector, ChooseSelector):
        return selector.options
    return (selector,)


class _Encoder:
    """Lays out state and writes the spec, one stage at a time."""

    def __init__(self, defaults: Mapping[str, float | int]) -> None:
        self.names = list(defaults)
        self.defaults = dict(defaults)
        self.used: set[str] = set()
        self.spec: list[int] = [0] * c.HEADER
        self.knob_values: list[float] = []
        self.knob_binds: list[int] = []
        self.f_size = 0
        self.i_size = 0
        self.per_round = 0
        self.streams: dict[int, int] = {}  # stream -> its match index's number

    def alloc(self, f_size: int, i_size: int) -> tuple[int, int]:
        at = self.f_size, self.i_size
        self.f_size += f_size
        self.i_size += i_size
        return at

    def alloc_rounds(self, slots: int) -> int:
        """`slots` per-round slots of the workspace; returns the first one."""
        at = self.per_round
        self.per_round += slots
        return at

    def index_for(self, stream: int) -> int:
        """The number of the bot's match index over `stream` (one per stream)."""
        return self.streams.setdefault(stream, len(self.streams))

    def knob(self, value: Value) -> int:
        """A new knob slot holding `value` (a literal, or a bound parameter)."""
        if isinstance(value, Knob):
            _check(
                value.name in self.defaults,
                "Knob({!r}) is not in the defaults ({})".format(
                    value.name, ", ".join(self.names) or "none"
                ),
            )
            self.used.add(value.name)
            self.knob_values.append(float(self.defaults[value.name]))
            self.knob_binds.append(self.names.index(value.name))
        else:
            _check(math.isfinite(float(value)), "knob values must be finite")
            self.knob_values.append(float(value))
            self.knob_binds.append(-1)
        return len(self.knob_values) - 1

    def record(self, stage: Stage) -> list[int]:
        """A stage's record, with its state allocated and its knobs slotted."""
        stage.validate()
        rec = [0] * c.REC
        rec[c.R_KIND] = stage.kind
        rec[c.R_F], rec[c.R_I] = self.alloc(*stage.state())
        slots = [self.knob(v) for v in stage.knobs()]
        rec[c.R_K] = slots[0] if slots else -1
        for k, p in enumerate(stage.params()):
            rec[c.R_A + k] = p
        return rec

    def encode(self, blueprint: Blueprint) -> Compiled:
        _check(
            not (
                any(isinstance(o, EmitInvalid) for o in blueprint.overlays)
                and any(
                    isinstance(g, OnInvalid) and g.side == c.BOTH
                    for g in blueprint.guards
                )
            ),
            "EmitInvalid would trip the bot's own OnInvalid(side=BOTH)",
        )
        cursor_i = self.alloc(0, 1)[1]
        view_i = self.alloc(0, c.VIEW_CELLS)[1]
        self.alloc_rounds(2)  # VIEW_MY_SLOT, VIEW_OPP_SLOT
        guards = [self.record(g) for g in blueprint.guards]
        overlays = [self.record(o) for o in blueprint.overlays]
        options = _selector_options(blueprint.selector)
        self._check_selectors(blueprint, options)
        choice = (
            self.knob(blueprint.selector.index)
            if isinstance(blueprint.selector, ChooseSelector)
            else -1
        )
        selectors = [self.record(s) for s in options]
        core_records, core_header, replays = self.ensemble(blueprint.core, depth=0)
        _check(
            core_header[c.E_NARMS] >= 2
            or not any(isinstance(s, Gatekeeper) for s in options),
            "Gatekeeper needs two arms or more: the gated last arm and the rest",
        )
        _check(
            all(
                core_header[c.E_NARMS] > s.experts
                for s in options
                if isinstance(s, Gatekeeper)
            ),
            "a Gatekeeper needs a main arm besides its gated experts",
        )

        header = self.spec
        header[c.H_CURSOR_I] = cursor_i
        header[c.H_VIEW_I] = view_i
        header[c.H_NGUARD] = len(guards)
        header[c.H_GUARD_AT] = self.append(guards)
        header[c.H_NOVER] = len(overlays)
        header[c.H_OVER_AT] = self.append(overlays)
        header[c.H_NSEL] = len(selectors)
        header[c.H_SEL_AT] = self.append(selectors)
        header[c.H_SEL_K] = choice
        header[c.H_CORE], sig_at = self.place(core_records, core_header)
        self.place_replays(sig_at, replays, depth=1)

        header[c.H_NIDX] = len(self.streams)
        header[c.H_IDX_AT] = len(self.spec)
        for stream in self.streams:  # in index order
            fixed = self.alloc(0, c.X_FIXED)[1]
            slot = self.alloc_rounds(c.X_SLOTS)
            self.spec.extend([stream, fixed, slot, 0])
        header[c.H_ROUNDS_I] = self.alloc(0, 2)[1]

        unused = [n for n in self.names if n not in self.used]
        _check(
            not unused, "defaults not used by any Knob: {}".format(", ".join(unused))
        )
        knob_f = self.alloc(len(self.knob_values), 0)[0]
        header[c.H_KNOB_F] = knob_f
        header[c.H_NKNOB] = len(self.knob_values)
        header[c.H_BIND_AT] = len(self.spec)
        self.spec.extend(self.knob_binds)
        return Compiled(
            state=(self.f_size, self.i_size, self.per_round),
            spec=np.array(self.spec, np.int64),
            knobs=np.array(self.knob_values, np.float64),
        )

    def _check_selectors(
        self, blueprint: Blueprint, options: tuple[Selector, ...]
    ) -> None:
        _check(len(options) >= 1, "ChooseSelector needs at least one option")
        scored = not isinstance(blueprint.scorer, NoScore)
        for s in options:
            if isinstance(s, First):
                _check(
                    not scored and blueprint.random_arm == c.RA_NONE,
                    "First reads no scores: use NoScore and no random arm",
                )
            else:
                _check(scored, f"{type(s).__name__} needs a scorer")
            if isinstance(s, Thompson | Gatekeeper):
                _check(
                    isinstance(blueprint.scorer, Dirichlet),
                    "Thompson samples a Dirichlet: use the Dirichlet scorer",
                )
                _check(
                    blueprint.random_arm != c.RA_PINNED,
                    "Thompson needs a scored random arm, not a pinned one",
                )

    def place_replays(
        self, sig_at: int, replays: list[tuple[int, Ensemble]], depth: int
    ) -> None:
        """Encode each replayed ensemble (at `depth`, 1: replayed from the top
        ensemble) and its own replays, and point its record at it."""
        for k, sub in replays:
            sub_records, sub_header, inner = self.ensemble(sub, depth)
            at, sub_sig_at = self.place(sub_records, sub_header)
            self.spec[sig_at + k * c.REC + c.R_SUB] = at
            self.place_replays(sub_sig_at, inner, depth + 1)

    def ensemble(
        self, ens: Ensemble, depth: int
    ) -> tuple[list[list[int]], list[int], list[tuple[int, Ensemble]]]:
        """An ensemble's signal records, its header, and its replays as (index of
        the replay's record, the replayed ensemble). `depth` counts the replays
        it is nested in: an odd depth sees the history swapped."""
        self._check_rotations(ens.rotations)
        records: list[list[int]] = []
        replays: list[tuple[int, Ensemble]] = []
        bayes: list[list[int]] = []
        oracles = 0
        arm = 0
        for item in ens.signals:
            signal, swap, rotations = _unwrap(item)
            rotations = rotations or ens.rotations
            self._check_rotations(rotations)
            rec = self.record(signal)
            rec[c.R_SWAP] = int(swap)
            stream = _stream(signal, swap != (depth % 2 == 1))
            if stream >= 0:
                rec[c.R_IDX] = self.index_for(stream)
            rec[c.R_ARM] = arm
            rec[c.R_NROT] = len(rotations)
            for k, r in enumerate(rotations):
                rec[c.R_ROT + k] = r
            arm += len(rotations)
            if isinstance(signal, SecondMatch):
                rec[c.R_C] = self.alloc_rounds(1)
            if isinstance(signal, Oracle):
                _check(
                    depth == 0 and not swap,
                    "an Oracle mocks the bot's own expert: not in a Sim or a Replay",
                )
                oracles += 1
                _check(oracles <= 1, "a bot holds at most one Oracle")
            if isinstance(signal, NaiveBayes):
                _check(not swap, "a NaiveBayes combines its ensemble: no Sim of it")
                bayes.append(rec)
            if isinstance(signal, Replay):
                _check(
                    depth < MAX_REPLAY_DEPTH,
                    f"replays nest at most {MAX_REPLAY_DEPTH} deep",
                )
                _check(not swap, "a Replay already plays from the opponent's side")
                _check(
                    not isinstance(signal.ensemble.scorer, NoScore),
                    "a Replay's ensemble needs a scorer to pick its best arm",
                )
                replays.append((len(records), signal.ensemble))
            records.append(rec)
        for rec in bayes:
            rec[c.R_F] = self.alloc(bayes_size(len(records)), 0)[0]
        header = [0] * c.ENS
        header[c.E_NSIG] = len(records)
        header[c.E_NARMS] = arm
        header[c.E_RANDOM] = ens.random_arm
        scorer = self.record(ens.scorer)
        header[c.E_SCORER] = scorer[c.R_KIND]
        header[c.E_SCORER_K] = scorer[c.R_K]
        header[c.E_SCORE_F] = self.alloc((arm + 1) * 3, 0)[0]
        header[c.E_PEND_I] = self.alloc(0, arm + 2)[1]
        header[c.E_SYM_I] = self.alloc(0, len(records))[1]
        return records, header, replays

    def place(self, records: list[list[int]], header: list[int]) -> tuple[int, int]:
        """Append an ensemble's signal records, then its header.
        Returns (the header's offset, the first record's offset)."""
        sig_at = self.append(records)
        header[c.E_SIG_AT] = sig_at
        at = len(self.spec)
        self.spec.extend(header)
        return at, sig_at

    def append(self, records: list[list[int]]) -> int:
        at = len(self.spec)
        for rec in records:
            self.spec.extend(rec)
        return at

    @staticmethod
    def _check_rotations(rotations: tuple[int, ...]) -> None:
        _check(1 <= len(rotations) <= 3, "1 to 3 rotations")
        _check(len(set(rotations)) == len(rotations), "rotations must be distinct")
        for r in rotations:
            _check_side(r, ROTATIONS, "a rotation")
