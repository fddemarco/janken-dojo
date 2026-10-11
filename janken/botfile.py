"""Bot files: a bot declared as YAML, read without compiling anything.

    description: plays what beats the opponent's last move.
    defaults: {NOISE: 0.05}            # the bot as submitted
    blueprint:                          # janken/kit/declare.py reads this section
      guards: [{Noise: {p: $NOISE}}]
      signals: [{LastMove: {of: OPP}}]
      rotations: [BEAT]
    mocks: gate_edge                    # a pure Oracle only: the bot it stands in for

The engine passes a bot its parameters at run time, as the `prm` vector in
`defaults` order (engine/registry.py), so a variant needs no new file. What a
bot's parameters may be tuned over is not the bot's business: it lives in a space
file (janken/lab/space.py).

A test fixture may instead be a Python kernel module (`*.py` with a `@kernel step`,
see engine/build.py); it has no parameters.
"""

import dataclasses
import functools
import hashlib
from collections.abc import Mapping

import yaml

BOT_SUFFIX = ".yaml"
KERNEL_SUFFIX = ".py"
SUFFIXES = (BOT_SUFFIX, KERNEL_SUFFIX)
KEYS = ("description", "defaults", "blueprint", "mocks")

Number = int | float


class BotFileError(ValueError):
    """A bot file that can't be read."""


@dataclasses.dataclass(frozen=True)
class BotFile:
    """A bot file's contents: its description, defaults and blueprint section."""

    path: str
    description: str
    defaults: Mapping[str, Number]
    blueprint: object  # the raw section; janken/kit/declare.py builds it
    mocks: str = ""  # a mock's: the stem of the bot it stands in for (janken/mocks.py)


def is_kernel_module(path: str) -> bool:
    """Whether `path` is a Python kernel module rather than a YAML bot."""
    return path.endswith(KERNEL_SUFFIX)


def read(path: str) -> BotFile:
    """The bot file at `path` (a kernel module reads as having no parameters)."""
    if is_kernel_module(path):
        return BotFile(path=path, description="", defaults={}, blueprint=None)
    return _read_yaml(path, source_hash(path))


@functools.cache
def _read_yaml(path: str, sha256: str) -> BotFile:
    """Parsed once per content (`sha256` keys the cache)."""
    del sha256
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise BotFileError(f"{path}: a bot file is a mapping of {', '.join(KEYS)}")
    unknown = sorted(set(map(str, data)) - set(KEYS))
    if unknown:
        raise BotFileError(
            f"{path}: unknown key(s) {', '.join(unknown)} (allowed: {', '.join(KEYS)})"
        )
    description = data.get("description") or ""
    if not isinstance(description, str):
        raise BotFileError(f"{path}: description must be text")
    mocks = data.get("mocks") or ""
    if not isinstance(mocks, str):
        raise BotFileError(f"{path}: mocks must be a bot's stem")
    return BotFile(
        path=path,
        description=description.strip(),
        defaults=_defaults(path, data.get("defaults") or {}),
        blueprint=data.get("blueprint"),
        mocks=mocks,
    )


def _defaults(path: str, data: object) -> dict[str, Number]:
    if not isinstance(data, dict):
        raise BotFileError(f"{path}: defaults must be a mapping of NAME: number")
    out: dict[str, Number] = {}
    for name, value in data.items():
        if not (isinstance(name, str) and name.isidentifier()):
            raise BotFileError(f"{path}: bad parameter name {name!r}")
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise BotFileError(f"{path}: parameter {name} must be a number")
        out[name] = value
    return out


def defaults(path: str) -> dict[str, Number]:
    """The bot's defaults ({} if it declares none), in declaration order."""
    return dict(read(path).defaults)


def check_params(path: str, params: Mapping[str, object]) -> None:
    """Raise if `params` names a parameter the bot doesn't declare."""
    known = defaults(path)
    unknown = sorted(set(params) - set(known))
    if unknown:
        raise ValueError(
            "{} has no parameter(s) {} (defaults: {})".format(
                path, ", ".join(unknown), ", ".join(sorted(known)) or "none"
            )
        )


def is_bot_file(name: str) -> bool:
    """Whether a directory entry named `name` is a bot ('_'-prefixed files skipped)."""
    return name.endswith(SUFFIXES) and not name.startswith("_")


def source_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
