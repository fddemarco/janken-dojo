"""Compile a set of bot files into one engine module.

A YAML bot's blueprint is compiled here into its `spec` / `knobs` arrays, which
the generated module holds as globals (numba freezes them as constants), and its
move is `pipeline.play(..., spec, knobs)`. Its state is allocated fresh for every
match, with the per-match workspace sized for the match's rounds. A Python kernel module (the referee's
test fixtures) brings its own `@kernel step`.

numba can't call "whichever bot this code names" by itself, so for each set of
bots this builds a copy of kernel.py whose dispatch section is generated,

    new_state(code, rounds) -> (f, i)      the bot's fresh state arrays
    step(code, f, i, prm, my, opp, n)      the bot's move
    oracle_kind / oracle_cell / level      Oracles (janken/mocks.py) and levels
    oracle_move(code, f, prm, opp, level)  a pure Oracle's move, no pipeline

and imports it. The copy's file name hashes the bots' sources. With numba's
on-disk cache on (janken/settings.py), it is written to the cache directory, so
numba caches it like any module and a changed bot means a new file: a cached
kernel can never replay a bot's old code. Without the cache, it goes to a
temporary directory that lasts as long as the process.
"""

import atexit
import dataclasses
import functools
import hashlib
import importlib.util
import inspect
import os
import shutil
import sys
import tempfile
import types
from collections.abc import Callable, Iterable

from .. import _numba_cache, botfile, mocks, settings
from ..kit import codes as c
from ..kit import declare, levels
from ..kit.blueprint import Blueprint, Compiled
from ..match import bot_name
from . import kernel
from .registry import discover, module_name, param_names

DISPATCH_MARKER = "# --- dispatch"


class BotContractError(ValueError):
    """A bot file that doesn't honour the bot contract."""


@dataclasses.dataclass(frozen=True)
class BlueprintBot:
    """A YAML bot: its blueprint, compiled into the arrays `pipeline.play` reads."""

    path: str
    blueprint: Blueprint
    compiled: Compiled

    @property
    def key(self) -> str:
        return f"{bot_name(self.path)}:{botfile.source_hash(self.path)}"

    def new_state_source(self) -> list[str]:
        """The body of its `new_state(code, rounds)` branch: Compiled.new_state."""
        f_size, i_size, per_round = self.compiled.state
        at = int(self.compiled.spec[c.H_ROUNDS_I])
        return [
            f"i = np.zeros({i_size} + {per_round} * (rounds + 1), np.int64)",
            f"i[{at}] = rounds + 1",
            f"i[{at + 1}] = {i_size}",
            f"return np.zeros({f_size}, np.float64), i",
        ]

    def globals_source(self, k: int) -> list[str]:
        return [
            f"S{k} = np.array({self.compiled.spec.tolist()!r}, np.int64)",
            f"K{k} = np.array({self.compiled.knobs.tolist()!r}, np.float64)",
        ]

    def call_source(self, k: int) -> str:
        return f"play(f, i, prm, my, opp, n, S{k}, K{k})"


@dataclasses.dataclass(frozen=True)
class KernelModule:
    """A Python module with its own `@kernel step`: the referee's test fixtures."""

    path: str
    module: types.ModuleType

    @property
    def key(self) -> str:
        return self.module.__name__

    @property
    def state(self) -> tuple[int, int]:
        f_size, i_size = getattr(self.module, "STATE", (0, 0))
        return int(f_size), int(i_size)

    def new_state_source(self) -> list[str]:
        """The body of its `new_state(code, rounds)` branch: its fixed STATE."""
        return [
            "return np.zeros({}, np.float64), np.zeros({}, np.int64)".format(
                *self.state
            )
        ]

    def globals_source(self, k: int) -> list[str]:
        return [f"b{k} = sys.modules[{self.module.__name__!r}]"]

    def call_source(self, k: int) -> str:
        return f"b{k}.step(f, i, prm, my, opp, n)"


EngineBot = BlueprintBot | KernelModule


@dataclasses.dataclass(frozen=True)
class CompiledBots:
    codes: dict[str, int]  # bot path -> its code in the dispatcher
    play_batch: Callable[..., tuple]  # kernel.play_batch, compiled against these bots


_engines: dict[str, types.ModuleType] = {}  # generated module name -> module


def compile_bots(paths: Iterable[str]) -> CompiledBots:
    """The engine for these bot files and every other bot in their directories.

    Compiling whole directories keeps the bot set, and so the cached kernel, the
    same from run to run, whichever pool an experiment happens to draw. The engine
    module is built once per process and bot set."""
    every = with_neighbours(paths)
    bots = [load_bot(p) for p in every]
    name = engine_name(bots)
    if name not in _engines:
        _engines[name] = _import_generated(name, engine_source(bots))
    return CompiledBots(
        codes={p: k for k, p in enumerate(every)},
        play_batch=_engines[name].play_batch,
    )


def with_neighbours(paths: Iterable[str]) -> list[str]:
    """`paths` plus every bot file in their directories, normalised and sorted."""
    normal = {os.path.normpath(p) for p in paths}
    folders = {os.path.dirname(p) or "." for p in normal}
    return sorted(normal | {p for folder in folders for p in discover(folder)})


def engine_name(bots: list[EngineBot]) -> str:
    """The generated module's name: a hash of the bots' keys, which themselves hash
    each bot's source."""
    keys = "\n".join(b.key for b in bots).encode()
    return "janken_engine_" + hashlib.sha256(keys).hexdigest()[:16]


def _kind(bot: EngineBot) -> int:
    if isinstance(bot, BlueprintBot):
        return mocks.kind(bot.blueprint)
    return c.ORACLE_NONE


def _level(bot: EngineBot) -> int:
    return levels.level(bot.blueprint) if isinstance(bot, BlueprintBot) else 1


def load_bot(path: str) -> EngineBot:
    """A bot file, read (once per content) and checked against the bot contract.

    Raises:
        BotContractError: the file isn't a valid bot.
    """
    if botfile.is_kernel_module(path):
        return _load_kernel_module(path)
    return _load_blueprint_bot(path, botfile.source_hash(path))


@functools.cache
def _load_blueprint_bot(path: str, sha256: str) -> BlueprintBot:
    del sha256  # keys the cache: an edited file is read again
    try:
        param_names(path)
        bot = botfile.read(path)
        blueprint = declare.blueprint_from_data(bot.blueprint)
        compiled = blueprint.compile(bot.defaults)
    except (ValueError, TypeError) as exc:
        raise BotContractError(f"{path}: {exc}") from exc
    return BlueprintBot(path=path, blueprint=blueprint, compiled=compiled)


def _load_kernel_module(path: str) -> KernelModule:
    name = module_name(path)
    module = sys.modules.get(name) or _import_file(name, path)
    if not callable(getattr(module, "step", 0)):
        raise BotContractError(
            f"{path} must define a @kernel `step(f, i, prm, my, opp, n)`"
        )
    bot = KernelModule(path=path, module=module)
    if min(bot.state) < 0:
        raise BotContractError(
            f"{path}: STATE sizes must be >= 0, got {module.STATE!r}"
        )
    return bot


def engine_source(bots: list[EngineBot]) -> str:
    """kernel.py with its dispatch section generated for these bots."""
    head = inspect.getsource(kernel).split(DISPATCH_MARKER)[0]
    return head + dispatch_source(bots)


def _oracle_source_lines(bots: list[EngineBot]) -> list[str]:
    """`oracle_kind`, `oracle_cell`, `level` and `oracle_move` for these bots."""
    kinds = [_kind(b) for b in bots]
    lines = ["", "", f"KINDS = np.array({kinds!r}, np.int64)"]
    lines += [f"LEVELS = np.array({[_level(b) for b in bots]!r}, np.int64)"]
    lines += ["", "", "@kernel", "def oracle_kind(code):", "    return KINDS[code]"]
    lines += ["", "", "@kernel", "def level(code):", "    return LEVELS[code]"]
    lines += ["", "", "@kernel", "def oracle_cell(code):"]
    for k, b in enumerate(bots):
        if kinds[k] == c.ORACLE_ARM and isinstance(b, BlueprintBot):
            lines += [
                f"    if code == {k}:",
                f"        return {mocks.oracle_cell(b.compiled)}",
            ]
    lines += [
        "    return -1",
        "",
        "",
        "@kernel",
        "def oracle_move(code, f, prm, opp, opp_level):",
    ]
    for k, b in enumerate(bots):
        if kinds[k] == c.ORACLE_PURE:
            lines += [
                f"    if code == {k}:",
                f"        return oracle_play(f, prm, opp, opp_level, S{k}, K{k})",
            ]
    lines += ["    return CRASH", ""]
    return lines


def dispatch_source(bots: list[EngineBot]) -> str:
    names = ", ".join(bot_name(b.path) for b in bots)
    lines = [
        DISPATCH_MARKER + ": generated by janken/engine/build.py for " + names,
        "",
        "import sys  # noqa: E402",
        "",
        "from janken.kit.pipeline import oracle_play, play  # noqa: E402",
        "",
    ]
    for k, b in enumerate(bots):
        lines += b.globals_source(k)
    lines += ["", "", "@kernel", "def new_state(code, rounds):"]
    for k, b in enumerate(bots):
        lines += [f"    if code == {k}:"]
        lines += ["        " + line for line in b.new_state_source()]
    lines += [
        "    return np.zeros(0, np.float64), np.zeros(0, np.int64)",
        "",
        "",
        "@kernel",
        "def step(code, f, i, prm, my, opp, n):",
    ]
    for k, b in enumerate(bots):
        lines += [f"    if code == {k}:", f"        return {b.call_source(k)}"]
    lines += ["    return CRASH", ""]
    lines += _oracle_source_lines(bots)
    return "\n".join(lines)


def _generated_dir() -> str:
    """Where generated engines are written: the cache directory when numba caches
    (it can only cache functions that live in a file), else this process's own
    temporary directory."""
    if settings.load(os.environ).cache:
        return os.path.join(_numba_cache.cache_dir(), "generated")
    if not _scratch:
        _scratch.append(tempfile.mkdtemp(prefix="janken-engine-"))
        atexit.register(shutil.rmtree, _scratch[0], ignore_errors=True)
    return _scratch[0]


_scratch: list[str] = []  # this process's temporary directory, once made


def _import_generated(name: str, source: str) -> types.ModuleType:
    """Write the generated engine `source` to a file (once) and import it."""
    folder = _generated_dir()
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name + ".py")
    if not os.path.exists(path):
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "w") as f:
            f.write(source)
        os.replace(tmp, path)  # atomic: parallel processes may race here
    return _import_file(name, path)


def _import_file(name: str, path: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[name]
        raise
    return module
