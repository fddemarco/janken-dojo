"""The bot library: bots read by stem, so an aggregator can name its arms.

An aggregator's arms are other bots, named by stem (janken/kit/blueprint/refs.py).
They are looked up under the bots dir the referring bot lives in: the nearest
folder above it that holds a `blocks/` folder (bots/), else its field root. Every
bot file below it counts, the field's level folders, `blocks/` (L1 heuristics
that exist to be arms, never in a pool) and `inactive/` alike, so a retired
version stays readable by the bots that name it. Stems are unique there.

    read_blueprint(path)   a bot file's blueprint, its references resolved
    structural_parameters(path)  its parameters fixed at compile time
    source_hash(path)      its file's hash and those of every bot it names
    references(path)       the stems a bot file names
"""

import hashlib
import os
from collections.abc import Iterator

from . import botfile
from .kit import blueprint as bp
from .kit import declare, levels
from .kit.blueprint import refs
from .kit.blueprint.binding import structural_names
from .match import bot_name

BLOCKS = "blocks"


def library_root(path: str) -> str:
    """The folder whose bots `path` may name: the nearest above it holding a
    blocks folder, else its field root (its folder, or the parent of its level
    folder)."""
    folder = os.path.dirname(os.path.abspath(path))
    probe = folder
    while True:
        if os.path.isdir(os.path.join(probe, BLOCKS)):
            return probe
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    if (
        levels.is_level_folder(os.path.basename(folder))
        or os.path.basename(folder) == BLOCKS
    ):
        return os.path.dirname(folder)
    return folder


class Library:
    """The bots under one root, read by stem (a refs.Library)."""

    def __init__(self, root: str) -> None:
        self.root = root
        self._index: dict[str, list[str]] = {}
        self._reading: list[str] = []

    def paths(self, stem: str) -> list[str]:
        """Every bot file named `stem` (one, when the library is sound)."""
        if not self._index:
            self._index = _index(self.root)
        return list(self._index.get(stem, []))

    def stems(self) -> list[str]:
        """Every stem under the root, sorted."""
        if not self._index:
            self._index = _index(self.root)
        return sorted(self._index)

    def path(self, stem: str) -> str:
        """The bot file named `stem`.

        Raises:
            BlueprintError: no bot has that stem, or more than one has.
        """
        found = self.paths(stem)
        if len(found) != 1:
            raise bp.BlueprintError(
                f"{len(found)} bots named {stem!r} under {self.root}"
                + (f": {', '.join(found)}" if found else "")
            )
        return found[0]

    def bot(self, stem: str) -> refs.Referenced:
        path = self.path(stem)
        try:
            defaults = botfile.read(path).defaults
        except botfile.BotFileError as exc:
            raise bp.BlueprintError(str(exc)) from exc
        return refs.Referenced(
            name=stem, blueprint=self.blueprint(path), defaults=defaults
        )

    def blueprint(self, path: str) -> bp.Blueprint:
        """The blueprint of the bot file at `path`, its references resolved here.

        Raises:
            BlueprintError: bots name each other in a cycle, or one can't be read.
        """
        stem = bot_name(path)
        if stem in self._reading:
            cycle = " -> ".join([*self._reading, stem])
            raise bp.BlueprintError(f"bots name each other in a cycle: {cycle}")
        self._reading.append(stem)
        try:
            return declare.blueprint_from_data(
                botfile.read(path).blueprint, self, f"{stem}.blueprint"
            )
        finally:
            self._reading.pop()


def read_blueprint(path: str) -> bp.Blueprint:
    """A bot file's blueprint (a kernel module has an empty one).

    Raises:
        BlueprintError: the blueprint, or a bot it names, can't be read.
        BotFileError: the file can't be read.
    """
    if botfile.is_kernel_module(path):
        return bp.Blueprint()
    return Library(library_root(path)).blueprint(path)


def structural_parameters(path: str) -> set[str]:
    """The bot's parameters that shape its compiled form (an n-gram's order, a
    matcher's history): fixed at compile time, never tuned (binding.py)."""
    return structural_names(read_blueprint(path))


def references(path: str) -> list[str]:
    """The stems the bot file at `path` names, in order, each once."""
    if botfile.is_kernel_module(path):
        return []
    return list(dict.fromkeys(_named(botfile.read(path).blueprint)))


def source_hash(path: str) -> str:
    """The bot's identity: its file's hash, and those of the bots it names (so
    editing a bot changes the hash of every bot built on it)."""
    own = botfile.source_hash(path)
    named = references(path)
    if not named:
        return own
    library = Library(library_root(path))
    seen = {bot_name(path)}
    digest = hashlib.sha256(own.encode())
    for stem in _closure(library, named, seen):
        digest.update(f"{stem}:{botfile.source_hash(library.path(stem))}".encode())
    return digest.hexdigest()


def _closure(library: Library, stems: list[str], seen: set[str]) -> Iterator[str]:
    """Every stem named, directly or not, depth first, each once."""
    for stem in stems:
        if stem in seen:
            continue
        seen.add(stem)
        yield stem
        yield from _closure(library, references(library.path(stem)), seen)


def _named(data: object) -> Iterator[str]:
    """The stems of every bot reference in a raw blueprint section."""
    if isinstance(data, dict):
        stem = data.get("bot")
        if isinstance(stem, str):
            yield stem
        for v in data.values():
            yield from _named(v)
    elif isinstance(data, list):
        for v in data:
            yield from _named(v)


def _index(root: str) -> dict[str, list[str]]:
    """Every YAML bot file under `root`, by stem."""
    index: dict[str, list[str]] = {}
    for folder, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith((".", "_")))
        for name in sorted(files):
            if botfile.is_bot_file(name) and name.endswith(botfile.BOT_SUFFIX):
                path = os.path.normpath(os.path.join(folder, name))
                index.setdefault(bot_name(path), []).append(path)
    return index
