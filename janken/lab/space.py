"""Space files: what one bot's parameters are tuned over, one file per bot.

    # spaces/smartbot_sims_v1.yaml
    bot: bots/l3/smartbot_sims_v1.yaml
    weight: 1.0     # its share of a multi-bot study's objective (0: tuned only
                    # for what it does to the others, e.g. a fleet's support)
    params:         # a subset of the bot's defaults; the rest stay at their defaults
      ARM_DECAY: {type: float, low: 0.5, high: 0.99, grid: [0.6, 0.8, 0.9, 0.95]}
      MAX_MATCH: {type: int, low: 2, high: 20, step: 2}
      SELECT: {type: categorical, choices: [0, 1]}

A param is `float` or `int` (`low`, `high`, optional `step`, `log`) or `categorical`
(`choices`); `grid` lists the values `--sampler grid` tries. `scaffold` writes a
starting point from a bot's defaults (`janken lab space`), meant to be edited.
"""

import dataclasses
import math
import os
from collections.abc import Mapping, Sequence

import yaml

from .. import botfile, settings
from ..match import bot_name

PARAM_TYPES = ("float", "int", "categorical")
KEYS = ("bot", "weight", "params")
PARAM_KEYS = ("type", "low", "high", "step", "log", "choices", "grid")

Number = int | float


class SpaceError(ValueError):
    """A space file that can't be used."""


@dataclasses.dataclass(frozen=True)
class Param:
    """One tunable parameter. `step` 0 means a continuous range."""

    type: str
    low: Number = 0
    high: Number = 0
    step: Number = 0
    log: bool = False
    choices: tuple[Number, ...] = ()
    grid: tuple[Number, ...] = ()

    def contains(self, value: Number) -> bool:
        if self.type == "categorical":
            return value in self.choices
        return self.low <= value <= self.high

    def grid_values(self) -> tuple[Number, ...]:
        """The values a grid search tries: `grid`, else every choice, else every
        value of a small int range."""
        if self.grid:
            return self.grid
        if self.type == "categorical":
            return self.choices
        if self.type == "int" and self.high - self.low <= 10:
            return tuple(range(int(self.low), int(self.high) + 1, int(self.step or 1)))
        return ()

    def to_data(self) -> dict[str, object]:
        """The YAML mapping, without keys at their defaults."""
        out: dict[str, object] = {"type": self.type}
        if self.type == "categorical":
            out["choices"] = list(self.choices)
        else:
            out.update(low=self.low, high=self.high)
            if self.step:
                out["step"] = self.step
            if self.log:
                out["log"] = True
        if self.grid:
            out["grid"] = list(self.grid)
        return out


@dataclasses.dataclass(frozen=True)
class Space:
    """A bot file, its tunable params and its weight in a study's objective."""

    bot: str
    weight: float
    params: Mapping[str, Param]

    @property
    def stem(self) -> str:
        return bot_name(self.bot)

    def defaults(self) -> dict[str, Number]:
        """The bot's defaults for the tuned params: a study's baseline."""
        known = botfile.defaults(self.bot)
        return {name: known[name] for name in self.params}

    def to_data(self) -> dict[str, object]:
        return {
            "bot": self.bot,
            "weight": self.weight,
            "params": {name: p.to_data() for name, p in self.params.items()},
        }


def load(path: str) -> Space:
    """The space file at `path`, validated against its bot.

    Raises:
        SpaceError: the file is malformed or doesn't match its bot.
    """
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "bot" not in data:
        raise SpaceError(
            f"{path} is not a space file (no `bot:`); write one with"
            " `janken lab space <bot file>`"
        )
    return from_data(data, path)


def from_data(data: Mapping[object, object], where: str) -> Space:
    """A validated Space from its YAML mapping; `where` names it in errors."""
    unknown = sorted(set(map(str, data)) - set(KEYS))
    _check(not unknown, f"{where}: unknown key(s) {', '.join(unknown)}")
    bot = data["bot"]
    if not isinstance(bot, str):
        raise SpaceError(f"{where}: `bot` must be a bot file path")
    bot = os.path.normpath(bot)
    _check(os.path.isfile(bot), f"{where}: no bot file {bot!r}")
    weight = _number(data.get("weight", 1.0), f"{where}: weight")
    _check(weight >= 0, f"{where}: weight must be >= 0")
    raw = _mapping(data.get("params") or {}, f"{where}: params")
    known = botfile.defaults(bot)
    params: dict[str, Param] = {}
    for name, spec in raw.items():
        at = f"{where}: params[{name!r}]"
        _check(name in known, f"{at} is not a parameter of {bot}")
        params[name] = _param(_mapping(spec, at), at)
        _check(
            params[name].contains(known[name]),
            f"{at} doesn't contain the bot's default {known[name]!r}",
        )
    return Space(bot=bot, weight=float(weight), params=params)


def _param(spec: Mapping[str, object], at: str) -> Param:
    unknown = sorted(set(spec) - set(PARAM_KEYS))
    _check(not unknown, f"{at}: unknown key(s) {', '.join(unknown)}")
    kind = spec.get("type")
    if kind not in PARAM_TYPES or not isinstance(kind, str):
        raise SpaceError(f"{at} type must be one of {', '.join(PARAM_TYPES)}")
    grid = _numbers(spec.get("grid", []), f"{at} grid")
    if kind == "categorical":
        choices = _numbers(spec.get("choices", []), f"{at} choices")
        _check(bool(choices), f"{at} needs 'choices'")
        return Param(type=kind, choices=choices, grid=grid)
    _check("low" in spec and "high" in spec, f"{at} needs 'low' and 'high'")
    low = _number(spec["low"], f"{at} low")
    high = _number(spec["high"], f"{at} high")
    step = _number(spec.get("step", 0), f"{at} step")
    _check(low <= high, f"{at}: low must be <= high")
    if kind == "int":
        _check(
            all(float(v).is_integer() for v in (low, high, step)),
            f"{at}: an int range needs int low/high/step",
        )
    return Param(
        type=kind,
        low=low,
        high=high,
        step=step,
        log=bool(spec.get("log", False)),
        grid=grid,
    )


def scaffold(bot: str, weight: float, config: settings.SpaceConfig) -> Space:
    """A starting space for every default of `bot`, ranged around its value.

    Raises:
        SpaceError: the bot has no parameters to tune.
    """
    known = botfile.defaults(bot)
    _check(bool(known), f"{bot} declares no defaults; nothing to tune")
    return Space(
        bot=os.path.normpath(bot),
        weight=weight,
        params={name: scaffold_param(v, config) for name, v in known.items()},
    )


def scaffold_param(default: Number, config: settings.SpaceConfig) -> Param:
    """A range around `default` (see settings.SpaceConfig) with an even grid."""
    spread = config.spread
    if default == 0:
        low, high = 0.0, 1.0
    elif default > 0:
        low, high = default / spread, default * spread
        if isinstance(default, float) and default <= 1:
            high = min(high, 1.0)
    else:
        low, high = default * spread, default / spread
    points = config.grid_points
    even = [low + (high - low) * k / (points - 1) for k in range(points)]
    if isinstance(default, int):
        low, high = math.floor(low), math.ceil(high)
        grid = sorted({round(v) for v in even} | {default})
        return Param(type="int", low=low, high=high, grid=tuple(grid))
    grid = sorted({round(v, 4) for v in even} | {default})
    return Param(type="float", low=round(low, 4), high=round(high, 4), grid=tuple(grid))


def dump(space: Space) -> str:
    """The space file's text: one flow mapping per param."""
    data = space.to_data()
    head = yaml.safe_dump(
        {k: data[k] for k in ("bot", "weight")}, sort_keys=False, width=88
    )
    lines = ["params:"]
    for name, param in space.params.items():
        flow = yaml.safe_dump(
            param.to_data(), default_flow_style=True, sort_keys=False, width=10**6
        ).strip()
        lines.append(f"  {name}: {flow}")
    return head + "\n".join(lines) + "\n"


def write(space: Space, out_dir: str, force: bool = False) -> str:
    """Write `space` to `<out_dir>/<stem>.yaml`; returns the path.

    Raises:
        SpaceError: the file exists and `force` is off.
    """
    path = os.path.join(out_dir, space.stem + ".yaml")
    _check(force or not os.path.exists(path), f"{path} exists (use --force)")
    os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump(space))
    return path


def _numbers(values: object, at: str) -> tuple[Number, ...]:
    if not isinstance(values, list):
        raise SpaceError(f"{at} must be a list")
    return tuple(_number(v, at) for v in values)


def _number(value: object, at: str) -> Number:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise SpaceError(f"{at} must be a number, got {value!r}")
    return value


def _mapping(value: object, at: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise SpaceError(f"{at} must be a mapping")
    return {str(k): v for k, v in value.items()}


def _check(ok: bool, message: str) -> None:
    if not ok:
        raise SpaceError(message)


def check_unique_stems(spaces: Sequence[Space]) -> None:
    """Raise unless every space is for a different bot."""
    stems = [s.stem for s in spaces]
    dupes = sorted({s for s in stems if stems.count(s) > 1})
    _check(not dupes, f"one space file per bot: {', '.join(dupes)} given twice")
