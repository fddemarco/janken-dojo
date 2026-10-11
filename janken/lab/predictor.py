"""A bot as a predictor of the opponent's next move.

A bot's move implies a prediction: the opponent move it beats. Read through its
core only, the signals, rotations, scorer and selector of its blueprint, that is
the bot's best guess at the opponent's next move from the moves so far. Its
guards and overlays (noise, openings, stalling, team play, invalid moves) are
about playing the game, not about predicting, so a predictor leaves them out,
along with the parameters only they read: tuning those can't change a
prediction.

Every bot shares the predictor kernel (predict_kernel.py), which takes the
compiled blueprint as arrays, so a new parameter set or a new bot never
recompiles anything.
"""

import dataclasses
from collections.abc import Mapping

import numpy as np

from .. import botfile
from ..engine.registry import pack_params
from ..kit import declare
from ..kit.blueprint import Blueprint, Compiled, Knob
from ..spec import BotSpec


class PredictorError(ValueError):
    """A bot that can't be read as a predictor."""


@dataclasses.dataclass(frozen=True)
class Predictor:
    """A bot's core, compiled, with its parameter vector."""

    label: str
    stem: str
    compiled: Compiled
    prm: np.ndarray  # float64[P_MAX]
    params: tuple[str, ...]  # the parameters the core reads, in `prm` order

    @property
    def state(self) -> np.ndarray:
        """(f size, fixed i size, per-round i slots), as the kernel takes them."""
        return np.array(self.compiled.state, np.int64)


def knob_names(node: object) -> set[str]:
    """The parameter names read by every Knob in a blueprint (or any part of it)."""
    if isinstance(node, Knob):
        return {node.name}
    if isinstance(node, tuple):
        return set().union(*(knob_names(x) for x in node))
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        return set().union(
            *(knob_names(getattr(node, f.name)) for f in dataclasses.fields(node))
        )
    return set()


def core_of(blueprint: Blueprint) -> Blueprint:
    """The blueprint without its guards and overlays."""
    return dataclasses.replace(blueprint, guards=(), overlays=())


def predictor_params(path: str) -> tuple[str, ...]:
    """The bot's parameters its core reads, in `defaults` order.

    Raises:
        PredictorError: the file isn't a YAML bot.
    """
    used = knob_names(core_of(_blueprint(path)))
    return tuple(name for name in botfile.defaults(path) if name in used)


def make_predictor(spec: BotSpec) -> Predictor:
    """The predictor of a bot spec.

    Raises:
        PredictorError: the bot isn't a YAML bot, or an override sets a parameter
            only its guards or overlays read.
    """
    names = predictor_params(spec.path)
    ignored = sorted(set(spec.params) - set(names))
    if ignored:
        raise PredictorError(
            f"{spec.label}: {', '.join(ignored)} feed(s) only the bot's guards or"
            " overlays, which a predictor leaves out"
        )
    defaults = botfile.defaults(spec.path)
    kept: Mapping[str, float | int] = {n: defaults[n] for n in names}
    try:
        compiled = core_of(_blueprint(spec.path)).compile(kept)
    except ValueError as exc:
        raise PredictorError(f"{spec.path}: {exc}") from exc
    return Predictor(
        label=spec.label,
        stem=spec.stem,
        compiled=compiled,
        prm=pack_params(spec.path, names, {**kept, **spec.params}),
        params=names,
    )


def _blueprint(path: str) -> Blueprint:
    if botfile.is_kernel_module(path):
        raise PredictorError(f"{path} is a kernel module; a predictor is a YAML bot")
    try:
        return declare.blueprint_from_data(botfile.read(path).blueprint)
    except ValueError as exc:
        raise PredictorError(f"{path}: {exc}") from exc
