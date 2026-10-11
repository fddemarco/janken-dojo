"""Bot files: finding them, and turning parameters into the vector a bot reads."""

import os
from collections.abc import Mapping, Sequence

import numpy as np

from .. import botfile
from ..match import bot_name

# Longest parameter vector a bot may take.
P_MAX = 8


def discover(directory: str) -> list[str]:
    """Every bot file in `directory` (non-recursive; '_'-prefixed files skipped)."""
    return sorted(
        os.path.normpath(os.path.join(directory, f))
        for f in os.listdir(directory)
        if botfile.is_bot_file(f)
    )


def param_names(path: str) -> list[str]:
    """The bot's parameters, in the order its `prm` vector holds them."""
    names = list(botfile.defaults(path))
    if len(names) > P_MAX:
        raise ValueError(
            f"{path} declares {len(names)} parameters; a bot may have at most {P_MAX}"
        )
    return names


def param_vector(path: str, params: dict[str, object] | None = None) -> np.ndarray:
    """The bot's `prm`: its defaults overlaid with `params`, as float64[P_MAX]."""
    values: dict[str, object] = {**botfile.defaults(path), **(params or {})}
    return pack_params(path, param_names(path), values)


def pack_params(
    where: str, names: Sequence[str], values: Mapping[str, object]
) -> np.ndarray:
    """`values` of `names`, in that order, as a float64[P_MAX] `prm` vector.

    Raises:
        TypeError: a value is not a number (`where` names its bot).
    """
    vec = np.zeros(P_MAX, np.float64)
    for k, name in enumerate(names):
        value = values[name]
        if not isinstance(value, int | float):
            raise TypeError(
                f"{where}: parameter {name} must be a number, got {value!r}"
            )
        vec[k] = float(value)
    return vec


def module_name(path: str) -> str:
    """The name a kernel module is imported under: unique per file content, so two
    files with one stem (or one file before and after an edit) never collide."""
    return f"janken_bot_{bot_name(path)}_{botfile.source_hash(path)[:12]}"
