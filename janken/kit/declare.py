"""Blueprints declared as data: what a bot's YAML file says, turned into a Blueprint.

A bot file (bots/<level>/<name>.yaml) holds plain data; its `blueprint` section is read here.
It has guards, a core predictor (a Bandit or a Gate) and overlays:

    blueprint:
      guards: [{Noise: {p: $NOISE}}, {Opening: {rounds: 1, move: ROCK}}]
      core:
        Bandit: {predictors: [{LastMove: {of: OPP}}], rotations: [BEAT]}

or with a ready-made core from presets.py:

    blueprint:
      core: {smartbot_sims: {n: 10, arm_decay: $ARM_DECAY, ...}}
      overlays: [{Team: {role: CHAMPION}}]

The grammar:

* a call is `Name` (no arguments), `{Name: {field: value, ...}}` (keywords) or
  `{Name: [value, ...]}` (positional). `Name` is a stage or predictor class of
  janken/kit/blueprint/ (CamelCase) or a preset function of presets.py (lower_case).
* `$NAME` is `Knob("NAME")`, a knob read from the bot's defaults.
* an UPPER_CASE word is a constant of codes.py / moves.py (`OPP`, `BEAT`, `ROCK`, ...).
* a list is a tuple; a call inside a list that returns a tuple (a preset such as
  `metabot_signals`) is spliced into it.

Nothing here touches numba: this module only builds the Blueprint dataclasses.
"""

import dataclasses
import inspect
from collections.abc import Callable, Mapping, Sequence

from . import blueprint as bp
from . import codes as c
from . import presets
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
        bp.Sim,
        bp.Rotated,
        bp.Bandit,
        bp.Gate,
        bp.ChooseSelector,
    )
}

PRESETS: Mapping[str, Callable[..., object]] = {
    fn.__name__: fn
    for fn in (
        presets.metabot_signals,
        presets.metabot,
        presets.iocaine,
        presets.rps4,
        presets.staller,
        presets.sims,
        presets.smartbot_sims,
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
    "EDGE": c.EDGE,
    "ILIAD": c.ILIAD,
    "ILIAD_V2": c.ILIAD_V2,
    "ILIAD_V3": c.ILIAD_V3,
    "IMPOSTOR": c.IMPOSTOR,
    "JOINT": c.JOINT,
    "LAST": c.LAST,
    "LEADER": c.LEADER,
    "LEADER_PRIORITY": c.LEADER_PRIORITY,
    "MAIN_FIRST": c.MAIN_FIRST,
    "MY": c.MY,
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


def blueprint_from_data(data: object, where: str = "blueprint") -> bp.Blueprint:
    """The Blueprint a bot file's `blueprint` section declares.

    Args:
        data: the section, as parsed from YAML.
        where: the section's path, for error messages.

    Returns:
        The (not yet compiled) Blueprint.

    Raises:
        BlueprintError: the section doesn't follow the grammar.
    """
    if data is None:
        return bp.Blueprint()
    section = _mapping(data, where)
    _check_keys(section, BLUEPRINT_KEYS, where)
    args = {k: value(v, f"{where}.{k}") for k, v in section.items()}
    _check(
        isinstance(args.get("core", bp.Bandit()), bp.Predictor),
        f"{where}.core: a core is a predictor (a Bandit or a Gate)",
    )
    built = _call(bp.Blueprint, "Blueprint", (), args, where)
    if not isinstance(built, bp.Blueprint):
        raise bp.BlueprintError(f"{where}: does not declare a blueprint")
    return built


def value(data: object, where: str) -> object:
    """A YAML value as a blueprint value: a literal, a knob, a constant or a call."""
    if isinstance(data, bool | int | float):
        return data
    if isinstance(data, str):
        return _word(data, where)
    if isinstance(data, list):
        return _sequence(data, where)
    if isinstance(data, dict):
        _check(
            len(data) == 1, f"{where}: a call is one `Name: arguments` pair, got {data}"
        )
        ((name, args),) = data.items()
        return _invoke(str(name), args, f"{where}.{name}")
    raise bp.BlueprintError(f"{where}: unexpected value {data!r}")


def _word(text: str, where: str) -> object:
    if text.startswith(KNOB_PREFIX):
        name = text[len(KNOB_PREFIX) :]
        _check(name.isidentifier(), f"{where}: bad knob {text!r}")
        return bp.Knob(name)
    if text in SYMBOLS:
        return SYMBOLS[text]
    if text in CLASSES or text in PRESETS:
        return _invoke(text, {}, where)
    raise bp.BlueprintError(
        f"{where}: unknown name {text!r} (a $KNOB, a constant, a stage or a preset)"
    )


def _sequence(items: Sequence[object], where: str) -> tuple[object, ...]:
    """A list as a tuple; a call returning a tuple is spliced in."""
    out: list[object] = []
    for k, item in enumerate(items):
        parsed = value(item, f"{where}[{k}]")
        if isinstance(item, dict | str) and isinstance(parsed, tuple):
            out.extend(parsed)
        else:
            out.append(parsed)
    return tuple(out)


def _invoke(name: str, args: object, where: str) -> object:
    target = CLASSES.get(name) or PRESETS.get(name)
    if target is None:
        raise bp.BlueprintError(f"{where}: unknown stage or preset {name!r}")
    if args is None:
        args = {}
    if isinstance(args, list):
        positional = tuple(value(v, f"{where}[{k}]") for k, v in enumerate(args))
        return _call(target, name, positional, {}, where)
    keywords = {
        str(k): value(v, f"{where}.{k}") for k, v in _mapping(args, where).items()
    }
    return _call(target, name, (), keywords, where)


def _call(
    target: Callable[..., object],
    name: str,
    positional: tuple[object, ...],
    keywords: Mapping[str, object],
    where: str,
) -> object:
    """`target(*positional, **keywords)`, with argument errors reported at `where`."""
    try:
        inspect.signature(target).bind(*positional, **keywords)
    except TypeError as exc:
        raise bp.BlueprintError(f"{where}: {name}: {exc}") from exc
    return target(*positional, **keywords)


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
