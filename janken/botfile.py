"""Bot files: a bot declared as YAML, read without compiling anything.

    description: plays what beats the opponent's last move.
    defaults: {NOISE: 0.05}            # the bot as submitted: its parameters
    blueprint:                          # janken/kit/declare.py reads this section
      guards: [{Noise: {p: $NOISE}}]
      core:
        Heuristic: {signal: {LastMove: {of: OPP}}, rotation: BEAT}
    mocks: gate_edge                    # a pure Oracle only: the bot it stands in for
    fleet:                              # a fleet's champion only: its fleet
      size: 3                           # bots in the fleet, the champion included
      supports: [first, second]         # their names (default: <stem>_support_K)
      handshake: [ROCK, PAPER, PAPER]   # the fleet's own opening
      vigilant: true                    # stop throwing at a teammate's first miss
    experimental: true                  # research only: never exported (default false)

An experimental bot is research only: `janken bot export` refuses it, and every
bot that names it, directly or not (janken/export.py). It marks a bot that
exists to test an idea, e.g. against a learner of janken/experimental/.

A fleet is one file, its champion's: the `fleet` section adds a Team overlay
(role CHAMPION) to the blueprint, and each support is the same bot with role
SUPPORT, never a file of its own (janken bot export writes one script per bot).

A bot's defaults are its parameter interface: what a variant, a space file or an
aggregator naming it as an arm may set. A default is a number, or a constant of
janken/kit/declare.py (`CTX: OPP`). The engine passes a bot its parameters at run time, as the `prm` vector in
`defaults` order (engine/registry.py), so a variant needs no new file. What a
bot's parameters may be tuned over is not the bot's business: it lives in a space
file (janken/lab/space.py).

A test fixture may instead be a Python kernel module (`*.py` with a `@kernel step`,
see engine/build.py); it has no parameters.
"""

import dataclasses
import functools
import hashlib
import os
from collections.abc import Mapping

import yaml

from .kit import blueprint as bp
from .kit import codes as c
from .kit import declare

BOT_SUFFIX = ".yaml"
KERNEL_SUFFIX = ".py"
SUFFIXES = (BOT_SUFFIX, KERNEL_SUFFIX)
KEYS = ("description", "defaults", "blueprint", "mocks", "fleet", "experimental")
FLEET_KEYS = ("size", "supports", "handshake", "vigilant")
MOVE_NAMES = ("ROCK", "PAPER", "SCISSORS")  # a handshake's words
SUPPORT_NAME = "{champion}_support_{k}"  # a support's name when the fleet names none

Number = int | float


class BotFileError(ValueError):
    """A bot file that can't be read."""


@dataclasses.dataclass(frozen=True)
class Fleet:
    """A champion's fleet: its supports' names, its handshake, and whether its
    bots are vigilant (blueprint.Team). No handshake: the bot leads no fleet."""

    supports: tuple[str, ...] = ()
    handshake: tuple[int, ...] = ()
    vigilant: bool = False

    @property
    def declared(self) -> bool:
        return bool(self.handshake)

    @property
    def size(self) -> int:
        """Bots in the fleet, the champion included."""
        return 1 + len(self.supports)

    def team(self) -> bp.Team:
        """The champion's Team overlay."""
        return bp.Team(c.CHAMPION, self.handshake, self.vigilant)


NO_FLEET = Fleet()


@dataclasses.dataclass(frozen=True)
class BotFile:
    """A bot file's contents: its description, defaults and blueprint section."""

    path: str
    description: str
    defaults: Mapping[str, Number]
    blueprint: object  # the raw section; janken/kit/declare.py builds it
    mocks: str = ""  # a mock's: the stem of the bot it stands in for (janken/mocks.py)
    fleet: Fleet = NO_FLEET  # a champion's: the fleet it leads
    experimental: bool = False  # research only: never exported


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
    experimental = data.get("experimental", False)
    if not isinstance(experimental, bool):
        raise BotFileError(f"{path}: experimental must be true or false")
    return BotFile(
        path=path,
        description=description.strip(),
        defaults=_defaults(path, data.get("defaults") or {}),
        blueprint=data.get("blueprint"),
        mocks=mocks,
        fleet=_fleet(path, data.get("fleet")),
        experimental=experimental,
    )


def _fleet(path: str, data: object) -> Fleet:
    """A `fleet` section: size, supports (optional), handshake, vigilant."""
    if data is None:
        return NO_FLEET
    where = f"{path}: fleet"
    if not isinstance(data, dict):
        raise BotFileError(f"{where} must be a mapping of {', '.join(FLEET_KEYS)}")
    unknown = sorted(set(map(str, data)) - set(FLEET_KEYS))
    if unknown:
        raise BotFileError(f"{where}: unknown key(s) {', '.join(unknown)}")
    size = data.get("size")
    if isinstance(size, bool) or not isinstance(size, int) or size < 2:
        raise BotFileError(f"{where}.size must be a whole number of bots, 2 or more")
    vigilant = data.get("vigilant", False)
    if not isinstance(vigilant, bool):
        raise BotFileError(f"{where}.vigilant must be true or false")
    return Fleet(
        supports=_supports(where, path, size, data.get("supports")),
        handshake=_handshake(where, data.get("handshake")),
        vigilant=vigilant,
    )


def _supports(where: str, path: str, size: int, data: object) -> tuple[str, ...]:
    """The supports' names: as listed (size - 1 of them), else numbered."""
    champion = os.path.splitext(os.path.basename(path))[0]
    if data is None:
        return support_names(champion, size)
    if not isinstance(data, list) or len(data) != size - 1:
        raise BotFileError(f"{where}.supports must list size - 1 = {size - 1} names")
    names = tuple(str(name) for name in data)
    if not all(name.isidentifier() for name in names):
        raise BotFileError(f"{where}.supports: a name is a bot stem, got {names}")
    if len(set(names)) != len(names) or champion in names:
        raise BotFileError(f"{where}.supports: every bot of a fleet has its own name")
    return names


def support_names(champion: str, size: int) -> tuple[str, ...]:
    """A fleet's supports when it names none: <champion>_support_1 .. size - 1."""
    return tuple(SUPPORT_NAME.format(champion=champion, k=k) for k in range(1, size))


def _handshake(where: str, data: object) -> tuple[int, ...]:
    """The handshake: a list of ROCK / PAPER / SCISSORS."""
    if not isinstance(data, list) or not data:
        raise BotFileError(f"{where}.handshake must list one move or more")
    moves = []
    for move in data:
        if move not in MOVE_NAMES:
            raise BotFileError(f"{where}.handshake: {move!r} is not a move")
        moves.append(declare.symbol(move))
    return tuple(moves)


def _defaults(path: str, data: object) -> dict[str, Number]:
    if not isinstance(data, dict):
        raise BotFileError(f"{path}: defaults must be a mapping of NAME: number")
    out: dict[str, Number] = {}
    for name, value in data.items():
        if not (isinstance(name, str) and name.isidentifier()):
            raise BotFileError(f"{path}: bad parameter name {name!r}")
        out[name] = _number(path, name, value)
    return out


def _number(path: str, name: str, value: object) -> Number:
    """A default's value: a number, or the constant an UPPER_CASE word names."""
    if isinstance(value, str):
        try:
            return declare.symbol(value)
        except bp.BlueprintError as exc:
            raise BotFileError(f"{path}: parameter {name}: {exc}") from exc
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise BotFileError(f"{path}: parameter {name} must be a number")
    return value


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
