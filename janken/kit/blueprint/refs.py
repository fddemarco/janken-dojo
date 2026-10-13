"""Bot references: an aggregator's arms, named as bots.

An aggregator (a Bandit, a Gate) combines bots. A bot file names each one, with
the parameters of every arm it makes of it (declare.py reads the mapping):

    {bot: ngram, arms: 4, space: {ORDER: [1, 2, 3, 4], CTX: OPP, DECAY: $TABLE_DECAY},
     rotations: [COPY, BEAT, BEAT_BEAT]}

    bot         the referenced bot's stem (versions are frozen, so the reference is)
    arms        how many instances of it (1)
    space       per parameter (a key of the referenced bot's defaults, its
                parameter interface; any case), one value per instance, or one
                value they all share: a literal, a constant or a `$KNOB` of the
                referring bot. Unset parameters keep the referenced bot's defaults.
    rotations   the arms each instance makes: its move COPY'd, BEAT or BEAT_BEAT
                (default: [COPY] from our side, [BEAT] from the opponent's)
    side        MY (default): the bot plays for us; OPP: the bot as the opponent
                would play it (a model of us), so BEAT beats its move
    draws       a replayed bot of level 2+: its move by that many Thompson draws
    random_arm  a replayed bot of level 2+: its random arm replaced (RA_NONE, ...)
    inner_draws a replayed bot of level 3+: the draws of the replays it holds
                capped (theirs kept when fewer, a best arm's left as is); Thompson
                draws are what a replay costs, so a model of an L4 is cheaper

An instance is the referenced bot's core, its knobs bound (binding.py), its guards
and overlays left out (they are about playing the game, not about predicting):

* an L1 bot (a Heuristic) becomes its signal, rotated (wrapped in a Sim from the
  opponent's side);
* a bot of level 2 or more (a Bandit) becomes a Replay of its bandit, from `side`.

A reference may also stand for a whole core (a Blueprint's `core`, a Gate's
`main`): the referenced bot's core, bound, at its own level.

A reference is resolved against a Library, which reads bots by stem (janken/
library.py reads them from the bots dir).
"""

import dataclasses
import typing
from collections.abc import Mapping

from .. import codes as c
from . import lowering
from .anatomy import Blueprint
from .base import ROTATIONS, BlueprintError, Value, check, check_side
from .binding import bind, structural_names
from .composites import Bandit, Gate, NaiveBayes, Replay
from .heuristic import Heuristic, Silent
from .predictor import Predictor
from .signals import Rotated, Signal, Sim

KEEP = -1  # random_arm, inner_draws: the referenced bot's own

P = typing.TypeVar("P", bound=Predictor)

KEYS = (
    "bot",
    "arms",
    "space",
    "rotations",
    "side",
    "draws",
    "random_arm",
    "inner_draws",
)


@dataclasses.dataclass(frozen=True)
class Reference:
    """A named bot as arms of an aggregator (see the module docstring)."""

    bot: str
    arms: int = 1
    space: tuple[tuple[str, tuple[Value, ...]], ...] = ()  # (name, per-arm values)
    rotations: tuple[int, ...] = ()  # () : the side's default
    side: int = c.MY
    draws: int = 0
    random_arm: int = KEEP
    inner_draws: int = KEEP


@dataclasses.dataclass(frozen=True)
class Referenced:
    """A bot as a library hands it over: its blueprint, knobs unbound, and defaults."""

    name: str
    blueprint: Blueprint
    defaults: Mapping[str, float | int]


class Library(typing.Protocol):
    """Reads bots by stem."""

    def bot(self, stem: str) -> Referenced:
        """The bot named `stem`.

        Raises:
            BlueprintError: no such bot, or it can't be read.
        """
        ...


class NoLibrary:
    """A library with no bots: blueprints declared on their own name none."""

    def bot(self, stem: str) -> Referenced:
        raise BlueprintError(f"no bot library to find {stem!r} in")


def arms(ref: Reference, library: Library) -> tuple[Rotated, ...]:
    """The arms `ref` makes: one per instance, each with its rotations."""
    target = library.bot(ref.bot)
    check(ref.arms >= 1, f"{ref.bot}: arms must be >= 1")
    return tuple(_arm(ref, core) for core in _instances(ref, target))


def core(ref: Reference, library: Library) -> Predictor:
    """A bot's core, named: the referenced bot's core, bound (a bot that is
    another plus its own guards and overlays, at the same level)."""
    target = library.bot(ref.bot)
    check(ref.arms == 1, f"{ref.bot}: a core is one instance")
    check(
        not ref.rotations
        and ref.side == c.MY
        and ref.draws == 0
        and ref.inner_draws == KEEP,
        f"{ref.bot}: a core plays as it is: no rotations, side or draws",
    )
    (bound,) = _instances(ref, target)
    if isinstance(bound, Bandit):
        return _with_random_arm(bound, ref.random_arm)
    check(ref.random_arm == KEEP, f"{ref.bot}: random_arm is a bandit's")
    return bound


def main_bandit(ref: Reference, library: Library) -> Bandit:
    """A Gate's main bandit, named: the referenced bot's bandit, bound."""
    bound = core(ref, library)
    check(isinstance(bound, Bandit), f"{ref.bot}: a gate's main bot is a Bandit")
    assert isinstance(bound, Bandit)
    return bound


def _instances(ref: Reference, target: Referenced) -> list[Predictor]:
    """The referenced core once per arm, its knobs bound to that arm's values."""
    names = _interface(ref, target)
    for name, values in ref.space:
        check(
            len(values) in (1, ref.arms),
            f"{ref.bot}: {name} has {len(values)} values for {ref.arms} arms",
        )
    cores = []
    for k in range(ref.arms):
        values: dict[str, Value] = dict(target.defaults)
        for name, given in ref.space:
            values[names[name]] = given[k] if len(given) > 1 else given[0]
        core = bind(target.blueprint.core, values)
        _check_literal(ref.bot, core, values)
        cores.append(core)
    return cores


def _interface(ref: Reference, target: Referenced) -> dict[str, str]:
    """Each `space` key as the referenced bot's parameter it names (any case)."""
    by_upper = {name.upper(): name for name in target.defaults}
    out: dict[str, str] = {}
    for name, _ in ref.space:
        check(
            name.upper() in by_upper,
            "{}: unknown parameter {!r} (its parameters: {})".format(
                ref.bot, name, ", ".join(target.defaults) or "none"
            ),
        )
        out[name] = by_upper[name.upper()]
    return out


def _check_literal(stem: str, core: Predictor, values: Mapping[str, Value]) -> None:
    """A structural parameter (binding.py) can't be the referring bot's knob."""
    bad = sorted(structural_names(core))
    check(
        not bad,
        "{}: {} shape(s) the compiled bot: give literal values, not a $KNOB".format(
            stem, ", ".join(f"{n} (as {values.get(n, n)})" for n in bad)
        ),
    )


def _arm(ref: Reference, core: Predictor) -> Rotated:
    if isinstance(core, Heuristic):
        return _heuristic_arm(ref, core)
    if isinstance(core, Gate):  # replayed as it plays: its gatekeeper runs
        core = lowering.lower(core)
    if isinstance(core, Bandit):
        replayed = _with_random_arm(core, ref.random_arm)
        if ref.inner_draws != KEEP:
            check(ref.inner_draws >= 0, f"{ref.bot}: inner_draws must be >= 0")
            replayed = _capped(replayed, ref.inner_draws)
        rotations = _rotations(ref, 0)
        return Rotated(Replay(replayed, ref.draws, ref.side), rotations)
    raise BlueprintError(
        f"{ref.bot}: its core is {type(core).__name__}, which can't be an arm"
    )


def _heuristic_arm(ref: Reference, core: Heuristic) -> Rotated:
    """An L1 bot's arm: its predictor with its own rotation plus the arm's."""
    signal, rotation = core.played()
    if isinstance(signal, Silent):
        raise BlueprintError(f"{ref.bot} plays at random: not an arm")
    check(ref.random_arm == KEEP, f"{ref.bot}: random_arm is a bandit's")
    if isinstance(signal, Replay):
        if ref.side == c.OPP:
            flipped = c.MY if signal.side == c.OPP else c.OPP
            signal = dataclasses.replace(signal, side=flipped)
        signal = dataclasses.replace(signal, draws=ref.draws or signal.draws)
        return Rotated(signal, _rotations(ref, rotation))
    check(ref.draws == 0, f"{ref.bot}: draws sample a replayed bandit")
    if ref.side == c.MY:
        return Rotated(signal, _rotations(ref, rotation))
    check(isinstance(signal, Signal), f"{ref.bot}: already plays a model of us")
    assert isinstance(signal, Signal)
    # A Sim's symbol beats its prediction of us (rotation BEAT): their move is it,
    # turned by what their rotation adds to BEAT.
    return Rotated(Sim(signal), _rotations(ref, rotation - c.BEAT))


def _capped(node: P, cap: int) -> P:
    """`node` with the draws of every replay below it capped at `cap`."""
    if isinstance(node, Replay):
        draws = min(node.draws, cap) if node.draws > 0 else 0
        return dataclasses.replace(node, bandit=_capped(node.bandit, cap), draws=draws)
    if isinstance(node, Bandit):
        return dataclasses.replace(
            node, predictors=tuple(_capped(p, cap) for p in node.predictors)
        )
    if isinstance(node, Rotated | Sim):
        return dataclasses.replace(node, signal=_capped(node.signal, cap))
    if isinstance(node, NaiveBayes):
        return dataclasses.replace(
            node, inputs=tuple(_capped(p, cap) for p in node.inputs)
        )
    return node


def _rotations(ref: Reference, base: int) -> tuple[int, ...]:
    """The arm's rotations relative to the referenced bot's move, made absolute."""
    default = (c.COPY,) if ref.side == c.MY else (c.BEAT,)
    relative = ref.rotations or default
    for r in relative:
        check_side(r, ROTATIONS, f"{ref.bot}: a rotation")
    check_side(ref.side, (c.MY, c.OPP), f"{ref.bot}: side")
    return tuple((base + r) % 3 for r in relative)


def _with_random_arm(core: Bandit, random_arm: int) -> Bandit:
    if random_arm == KEEP:
        return core
    return dataclasses.replace(core, random_arm=random_arm)
