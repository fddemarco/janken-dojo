"""Blueprints declared as data: what a bot's YAML file says, turned into a Blueprint.

A bot file (bots/<level>/<name>.yaml) holds plain data; its `blueprint` section is
read here. It has guards, a core predictor and overlays. An L1 bot's core is a
Heuristic, one signal played with one rotation:

    blueprint:
      guards: [{Noise: {p: $NOISE}}, {Opening: {rounds: 1, move: ROCK}}]
      core:
        Heuristic: {signal: {LastMove: {of: OPP}}, rotation: BEAT}

Any other core is an aggregator, a Bandit or a Gate, whose arms are bots, named
(blueprint/refs.py):

    blueprint:
      core:
        Bandit:
          predictors:
            - {bot: frequency, arms: 2, space: {DECAY: [1.0, 0.9]},
               rotations: [COPY, BEAT, BEAT_BEAT]}
            - {bot: smartbot_v1, side: OPP, random_arm: RA_NONE}
          scorer: {Dirichlet: {decay: $ARM_DECAY}}
          random_arm: RA_SCORED
          selector: Thompson
      overlays: [{Team: {role: IMPOSTOR, handshake: [ROCK, PAPER, PAPER]}}]

The grammar:

* a call is `Name` (no arguments), `{Name: {field: value, ...}}` (keywords) or
  `{Name: [value, ...]}` (positional). `Name` is a stage or predictor class of
  janken/kit/blueprint/ (CamelCase).
* a mapping with a `bot` key is a bot reference: the arms of a Bandit's
  `predictors` or a Gate's `experts`, a Gate's `main` bandit, a blueprint's
  `core` (the bot is another, plus its own guards and overlays), or (one arm,
  one rotation) a Heuristic's `signal`. Those take nothing else, but a NaiveBayes
  among a Bandit's predictors, which combines the others.
* `$NAME` is `Knob("NAME")`, a knob read from the bot's defaults.
* an UPPER_CASE word is a constant of codes.py / moves.py (`OPP`, `BEAT`, `ROCK`, ...).
* a list is a tuple; the arms a reference makes are spliced into it.

Nothing here touches numba or files: references are read through a Library
(janken/library.py); this module only builds the Blueprint dataclasses.
"""

import dataclasses
import inspect
from collections.abc import Callable, Mapping, Sequence

from . import blueprint as bp
from . import codes as c
from .blueprint import refs
from .moves import PAPER, ROCK, SCISSORS

KNOB_PREFIX = "$"


def _stage_classes(base: type) -> list[type]:
    """`base` and its subclasses that declare their own kind code (but those only
    the compiler builds, such as the Gatekeeper a Gate lowers to)."""
    declarable = "kind" in vars(base) and getattr(base, "declarable", True)
    found = [base] if declarable else []
    for sub in base.__subclasses__():
        found += _stage_classes(sub)
    return found


CLASSES: Mapping[str, type] = {
    cls.__name__: cls
    for cls in (
        *_stage_classes(bp.Stage),
        bp.Heuristic,
        bp.Bandit,
        bp.Gate,
        bp.ChooseSelector,
    )
}

SYMBOLS: Mapping[str, int | tuple[int, ...]] = {
    "ALL_ROTATIONS": bp.ALL_ROTATIONS,
    "ANTI_FIRST": c.ANTI_FIRST,
    "ANTI_FIRST_HOLD": c.ANTI_FIRST_HOLD,
    "ANY": c.ANY,
    "BANDIT": c.BANDIT,
    "BEAT": c.BEAT,
    "BEAT_BEAT": c.BEAT_BEAT,
    "BOTH": c.BOTH,
    "CHAMPION": c.CHAMPION,
    "COPY": c.COPY,
    "CRASH_ACTION": c.CRASH_ACTION,
    "DRAWS": c.EST_DRAWS,
    "EDGE": c.EDGE,
    "IMPOSTOR": c.IMPOSTOR,
    "JOINT": c.JOINT,
    "LAST": c.LAST,
    "LEADER": c.LEADER,
    "LEADER_PRIORITY": c.LEADER_PRIORITY,
    "MAIN_FIRST": c.MAIN_FIRST,
    "MY": c.MY,
    "NORMAL": c.EST_NORMAL,
    "OPP": c.OPP,
    "PAPER": PAPER,
    "RANDOM_ACTION": c.RANDOM_ACTION,
    "RANDOM_MOVE": c.RANDOM_MOVE,
    "RA_NONE": c.RA_NONE,
    "RA_PINNED": c.RA_PINNED,
    "RA_SCORED": c.RA_SCORED,
    "ROCK": ROCK,
    "SCISSORS": SCISSORS,
    "SUPPORT": c.SUPPORT,
    "TIES_FIRST": c.TIES_FIRST,
    "TIES_RANDOM": c.TIES_RANDOM,
}

# The keys of a blueprint section.
BLUEPRINT_KEYS = tuple(f.name for f in dataclasses.fields(bp.Blueprint))

# Where a bot reference may stand: (class, field) -> what it becomes there.
ARMS, CORE, MAIN, SIGNAL = "arms", "core", "main", "signal"
REFERENCE_SLOTS: Mapping[tuple[object, str], str] = {
    (bp.Blueprint, "core"): CORE,
    (bp.Bandit, "predictors"): ARMS,
    (bp.Gate, "experts"): ARMS,
    (bp.Gate, "main"): MAIN,
    (bp.Heuristic, "signal"): SIGNAL,
}


NO_LIBRARY = refs.NoLibrary()


def blueprint_from_data(
    data: object,
    library: refs.Library = NO_LIBRARY,
    where: str = "blueprint",
) -> bp.Blueprint:
    """The Blueprint a bot file's `blueprint` section declares.

    Args:
        data: the section, as parsed from YAML.
        library: where the bots it names are read.
        where: the section's path, for error messages.

    Returns:
        The (not yet compiled) Blueprint.

    Raises:
        BlueprintError: the section doesn't follow the grammar.
    """
    return _Reader(library).blueprint(data, where)


def symbol(text: str) -> int:
    """The constant an UPPER_CASE word names (a bot's defaults may use them).

    Raises:
        BlueprintError: no such constant, or it names several values.
    """
    found = SYMBOLS.get(text)
    if not isinstance(found, int):
        raise bp.BlueprintError(f"unknown constant {text!r}")
    return found


class _Reader:
    """Reads a blueprint section, resolving its bot references in `library`."""

    def __init__(self, library: refs.Library) -> None:
        self.library = library

    def blueprint(self, data: object, where: str) -> bp.Blueprint:
        if data is None:
            return bp.Blueprint()
        section = _mapping(data, where)
        _check_keys(section, BLUEPRINT_KEYS, where)
        args = {k: self.value(v, f"{where}.{k}") for k, v in section.items()}
        built = self.call(bp.Blueprint, "Blueprint", (), args, where)
        if not isinstance(built, bp.Blueprint):
            raise bp.BlueprintError(f"{where}: does not declare a blueprint")
        _check(
            isinstance(built.core, bp.Predictor),
            f"{where}.core: a core is a predictor (a Heuristic, a Bandit or a Gate)"
            " or a bot, named",
        )
        return built

    def value(self, data: object, where: str) -> object:
        """A YAML value: a literal, a knob, a constant, a call or a bot reference."""
        if isinstance(data, bool | int | float):
            return data
        if isinstance(data, str):
            return self.word(data, where)
        if isinstance(data, list):
            return tuple(self.value(v, f"{where}[{k}]") for k, v in enumerate(data))
        if isinstance(data, dict) and "bot" in data:
            return self.reference(data, where)
        if isinstance(data, dict):
            _check(
                len(data) == 1,
                f"{where}: a call is one `Name: arguments` pair, got {data}",
            )
            ((name, args),) = data.items()
            return self.invoke(str(name), args, f"{where}.{name}")
        raise bp.BlueprintError(f"{where}: unexpected value {data!r}")

    def word(self, text: str, where: str) -> object:
        if text.startswith(KNOB_PREFIX):
            name = text[len(KNOB_PREFIX) :]
            _check(name.isidentifier(), f"{where}: bad knob {text!r}")
            return bp.Knob(name)
        if text in SYMBOLS:
            return SYMBOLS[text]
        if text in CLASSES:
            return self.invoke(text, {}, where)
        raise bp.BlueprintError(
            f"{where}: unknown name {text!r} (a $KNOB, a constant or a stage)"
        )

    def reference(self, data: Mapping[object, object], where: str) -> refs.Reference:
        """A `{bot: stem, ...}` mapping as a Reference (resolved where it stands)."""
        section = {str(k): v for k, v in data.items()}
        _check_keys(section, refs.KEYS, where)
        stem = section["bot"]
        _check(isinstance(stem, str), f"{where}: bot is a bot's stem")
        args = {
            k: self.value(v, f"{where}.{k}")
            for k, v in section.items()
            if k not in ("bot", "space")
        }
        space = _mapping(section.get("space") or {}, f"{where}.space")
        per_arm = tuple(
            (name, self.arm_values(v, f"{where}.space.{name}"))
            for name, v in space.items()
        )
        reference = self.call(
            refs.Reference, "bot", (stem,), {**args, "space": per_arm}, where
        )
        assert isinstance(reference, refs.Reference)
        return reference

    def arm_values(self, data: object, where: str) -> tuple[bp.Value, ...]:
        """One value per arm (a list), or one they share."""
        parsed = self.value(data, where)
        out: list[bp.Value] = []
        for v in parsed if isinstance(parsed, tuple) else (parsed,):
            if isinstance(v, bool) or not isinstance(v, int | float | bp.Knob):
                raise bp.BlueprintError(
                    f"{where}: a parameter value is a number, a constant or a $KNOB"
                )
            out.append(v)
        return tuple(out)

    def invoke(self, name: str, args: object, where: str) -> object:
        target = CLASSES.get(name)
        if target is None:
            raise bp.BlueprintError(f"{where}: unknown stage {name!r}")
        if args is None:
            args = {}
        if isinstance(args, list):
            positional = tuple(
                self.value(v, f"{where}[{k}]") for k, v in enumerate(args)
            )
            return self.call(target, name, positional, {}, where)
        keywords = {
            str(k): self.value(v, f"{where}.{k}")
            for k, v in _mapping(args, where).items()
        }
        return self.call(target, name, (), keywords, where)

    def call(
        self,
        target: Callable[..., object],
        name: str,
        positional: tuple[object, ...],
        keywords: Mapping[str, object],
        where: str,
    ) -> object:
        """`target(*positional, **keywords)`, its bot references resolved, with
        argument errors reported at `where`."""
        try:
            bound = inspect.signature(target).bind(*positional, **keywords)
        except TypeError as exc:
            raise bp.BlueprintError(f"{where}: {name}: {exc}") from exc
        arguments = {
            field: self.resolve(target, field, v, f"{where}.{field}")
            for field, v in bound.arguments.items()
        }
        try:
            built = target(**arguments)
        except TypeError as exc:
            raise bp.BlueprintError(f"{where}: {name}: {exc}") from exc
        if isinstance(built, bp.Bandit):
            return _with_combiners(built)
        return built

    def resolve(self, target: object, field: str, value: object, where: str) -> object:
        """A field's value with the bot references it holds resolved."""
        slot = REFERENCE_SLOTS.get((target, field), "")
        try:
            if slot == ARMS:
                return self.arms(value, where)
            if slot == CORE and isinstance(value, refs.Reference):
                return refs.core(value, self.library)
            if slot == MAIN and isinstance(value, refs.Reference):
                return refs.main_bandit(value, self.library)
            if slot == SIGNAL and isinstance(value, refs.Reference):
                (arm,) = refs.arms(value, self.library)
                _check(len(arm.rotations) == 1, "a heuristic plays one rotation")
                return arm
        except bp.BlueprintError as exc:
            raise bp.BlueprintError(f"{where}: {exc}") from exc
        _check(
            not _holds_reference(value),
            f"{where}: a bot reference is an arm of a Bandit or a Gate",
        )
        return value

    def arms(self, value: object, where: str) -> tuple[object, ...]:
        """An aggregator's arms: its bot references' arms, spliced in order (and
        the NaiveBayes combiners, which combine the others).

        No bot is named twice with the same parameters and side: it would be the
        same predictor, computed twice; its rotations go in one entry. (Two bots
        that happen to share a signal are different arms.)"""
        _check(isinstance(value, tuple), f"{where}: a list of bot references")
        assert isinstance(value, tuple)
        out: list[object] = []
        named: list[tuple[str, object]] = []  # (bot, its arm's predictor)
        for k, item in enumerate(value):
            if isinstance(item, refs.Reference):
                for arm in refs.arms(item, self.library):
                    key = (item.bot, _unrotated(arm))
                    _check(
                        key not in named,
                        f"{where}[{k}]: {item.bot} repeats an arm of this aggregator"
                        " (the same bot, parameters and side): one entry, with all"
                        " its rotations",
                    )
                    named.append(key)
                    out.append(arm)
            elif isinstance(item, bp.NaiveBayes):
                out.append(item)
            else:
                raise bp.BlueprintError(
                    f"{where}[{k}]: an aggregator's arms are bots: name one as"
                    f" {{bot: <stem>, ...}}, got {type(item).__name__}"
                )
        return tuple(out)


def _with_combiners(bandit: bp.Bandit) -> bp.Bandit:
    """Each NaiveBayes declared with no inputs combines its bandit's other arms."""
    others = tuple(
        p for p in bandit.predictors if not isinstance(_unrotated(p), bp.NaiveBayes)
    )
    predictors = tuple(
        dataclasses.replace(p, inputs=others)
        if isinstance(p, bp.NaiveBayes) and not p.inputs
        else p
        for p in bandit.predictors
    )
    return dataclasses.replace(bandit, predictors=predictors)


def _unrotated(predictor: object) -> object:
    return predictor.signal if isinstance(predictor, bp.Rotated) else predictor


def _holds_reference(value: object) -> bool:
    if isinstance(value, refs.Reference):
        return True
    return isinstance(value, tuple) and any(_holds_reference(v) for v in value)


def _mapping(data: object, where: str) -> dict[str, object]:
    if not isinstance(data, dict):
        raise bp.BlueprintError(f"{where}: expected a mapping, got {data!r}")
    return {str(k): v for k, v in data.items()}


def _check_keys(
    section: Mapping[str, object], allowed: Sequence[str], where: str
) -> None:
    unknown = sorted(set(section) - set(allowed))
    _check(
        not unknown,
        "{}: unknown key(s) {} (allowed: {})".format(
            where, ", ".join(unknown), ", ".join(allowed)
        ),
    )


def _check(ok: bool, message: str) -> None:
    if not ok:
        raise bp.BlueprintError(message)
