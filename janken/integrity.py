"""The field's integrity: the bots, their space files and research/species.md agree.

Each check takes what was already read (a bot's facts, a parsed space file, the
species book) and returns the problems it finds, one sentence each, so the rules
are tested on hand-made data. `field_problems` reads a lab's directories and runs
them all: `janken bot audit`, which pre-commit runs on the real field.

    every field bot is a YAML file with a description and at most P_MAX defaults,
        loads and compiles, and sits in its level's folder
    every block is an L1 heuristic (or an Oracle's stand-in) that compiles
    stems are unique across the whole library (levels, blocks, inactive)
    every space file names a field bot by its own stem and file, and has params
    species.md and the field agree: every versioned bot is its species' current
        version, of the level of its folder, and every species' current version
        is in the field
"""

import dataclasses
import os
from collections.abc import Mapping, Sequence

from . import botfile, library, mocks
from .engine import registry
from .kit import levels
from .lab import space
from .match import bot_name
from .notebook import species


@dataclasses.dataclass(frozen=True)
class BotFacts:
    """What the checks need to know of one bot file, read once."""

    path: str
    is_yaml: bool
    description: str
    n_defaults: int
    folder: str  # where it sits
    expected_folder: str  # where its level puts it ("" when it can't be read)
    level: int  # 0 when it can't be read
    error: str  # why it doesn't load or compile, "" when it does


def read_bot(path: str) -> BotFacts:
    """The facts of the bot at `path`: read, its level computed and compiled."""
    from .engine.build import load_bot

    is_yaml = not botfile.is_kernel_module(path)
    description, n_defaults, expected, level, error = "", 0, "", 0, ""
    try:
        if is_yaml:
            found = botfile.read(path)
            description, n_defaults = found.description, len(found.defaults)
        level = mocks.path_level(path)
        expected = registry.expected_folder(path)
        load_bot(path)
    except ValueError as exc:  # every bot-file, blueprint and contract error
        error = str(exc)
    return BotFacts(
        path=path,
        is_yaml=is_yaml,
        description=description,
        n_defaults=n_defaults,
        folder=os.path.dirname(os.path.normpath(path)),
        expected_folder=expected,
        level=level,
        error=error,
    )


def _file_problems(bot: BotFacts) -> list[str]:
    """What every bot file, field or block, must honour."""
    if bot.error:
        return [f"{bot.path}: {bot.error}"]
    found = []
    if not bot.is_yaml:
        found.append(f"{bot.path}: a bot is a YAML file, not a kernel module")
    if not bot.description:
        found.append(f"{bot.path}: a bot needs a description")
    if bot.n_defaults > registry.P_MAX:
        found.append(f"{bot.path}: {bot.n_defaults} defaults, at most {registry.P_MAX}")
    return found


def contract_problems(bot: BotFacts) -> list[str]:
    """A field bot's problems: its file, and the folder its level puts it in."""
    found = _file_problems(bot)
    if not bot.error and bot.folder != bot.expected_folder:
        found.append(
            f"{bot.path}: an L{bot.level} bot belongs in {bot.expected_folder}"
        )
    return found


def block_problems(block: BotFacts) -> list[str]:
    """A block's problems: its file, and that it is an L1 (or an Oracle's stand-in)."""
    found = _file_problems(block)
    if not block.error and block.level not in (1, levels.ORACLE):
        found.append(f"{block.path}: a block is an L1 heuristic, not L{block.level}")
    return found


def stem_problems(paths_by_stem: Mapping[str, Sequence[str]]) -> list[str]:
    """Stems held by more than one file (`{stem: its files}` of the whole library)."""
    return [
        f"{len(paths)} bots named {stem!r}: {', '.join(paths)}"
        for stem, paths in sorted(paths_by_stem.items())
        if len(paths) > 1
    ]


def space_problems(
    name: str, found: space.Space, field: Mapping[str, str]
) -> list[str]:
    """Problems of the space file `name`, read as `found`, given the field
    (`{stem: bot file}`)."""
    stem = os.path.splitext(name)[0]
    if found.stem != stem:
        return [f"{name}: names {found.bot}, not a bot named {stem!r}"]
    if stem not in field:
        return [f"{name}: no field bot is named {stem!r}"]
    problems = []
    if os.path.normpath(found.bot) != os.path.normpath(field[stem]):
        problems.append(f"{name}: names {found.bot}, but {stem} is {field[stem]}")
    if not found.params:
        problems.append(f"{name}: no params to tune")
    return problems


def species_problems(
    book: Sequence[species.Species], field: Mapping[str, str]
) -> list[str]:
    """Where species.md and the field (`{stem: its level folder name}`) disagree."""
    current = {s.current: s for s in book}
    found = []
    for stem, folder in sorted(field.items()):
        if not species.is_versioned(stem):
            continue
        if stem not in current:
            found.append(f"{stem}: not a species' current version in species.md")
        elif current[stem].level.lower() != folder:
            found.append(
                f"{stem}: species.md says {current[stem].level}, its folder is {folder}"
            )
    for row in book:
        if row.current not in field:
            found.append(
                f"species {row.name}: its current version {row.current}"
                " is not in the field"
            )
        elif species.parse_stem(row.current).species != row.name:
            found.append(
                f"species {row.name}: {row.current} is not one of its versions"
            )
    return found


def field_problems(bots_dir: str, spaces_dir: str, notebook: str) -> list[str]:
    """Every problem of the field in `bots_dir`, its space files and its notebook."""
    field = {bot_name(p): p for p in registry.discover(bots_dir)}
    found = [p for path in field.values() for p in contract_problems(read_bot(path))]
    blocks = os.path.join(bots_dir, library.BLOCKS)
    if os.path.isdir(blocks):
        for name in sorted(os.listdir(blocks)):
            if botfile.is_bot_file(name):
                found += block_problems(read_bot(os.path.join(blocks, name)))
    shelf = library.Library(bots_dir)
    found += stem_problems({s: shelf.paths(s) for s in shelf.stems()})
    if os.path.isdir(spaces_dir):
        for name in sorted(os.listdir(spaces_dir)):
            try:
                read = space.load(os.path.join(spaces_dir, name))
            except ValueError as exc:
                found.append(str(exc))
                continue
            found += space_problems(name, read, field)
    folders = {s: os.path.basename(os.path.dirname(p)) for s, p in field.items()}
    return found + species_problems(species.load(notebook).species, folders)
