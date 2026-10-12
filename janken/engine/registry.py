"""Bot files: finding them, and turning parameters into the vector a bot reads."""

import os
from collections.abc import Mapping, Sequence

import numpy as np

from .. import botfile, mocks
from ..kit import levels
from ..match import bot_name

# Longest parameter vector a bot may take.
P_MAX = 8


def discover(directory: str) -> list[str]:
    """Every bot file in `directory` and in its level folders (l1, l2, ..., oracle),
    '_'-prefixed files skipped. Other subfolders (bots/inactive) are never searched."""
    folders = [directory] + [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if levels.is_level_folder(f) and os.path.isdir(os.path.join(directory, f))
    ]
    return sorted(
        os.path.normpath(os.path.join(folder, f))
        for folder in folders
        for f in os.listdir(folder)
        if botfile.is_bot_file(f)
    )


def field_root(path: str) -> str:
    """The directory whose discovery finds the bot at `path`: its folder, or that
    folder's parent when it is a level folder."""
    folder = os.path.dirname(os.path.normpath(path)) or "."
    if levels.is_level_folder(os.path.basename(folder)):
        return os.path.dirname(folder) or "."
    return folder


def find(directory: str, stem: str) -> str:
    """The bot file named `stem` that `discover(directory)` finds.

    Raises:
        FileNotFoundError: no bot has that stem, or more than one has.
    """
    found = [p for p in discover(directory) if bot_name(p) == stem]
    if len(found) != 1:
        raise FileNotFoundError(
            f"{len(found)} bots named {stem!r} in {directory}: {', '.join(found)}"
            if found
            else f"no bot {stem!r} in {directory}"
        )
    return found[0]


def expected_folder(path: str) -> str:
    """The level folder the bot at `path` belongs in, under its field root."""
    return os.path.normpath(
        os.path.join(field_root(path), levels.folder(mocks.path_level(path)))
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
