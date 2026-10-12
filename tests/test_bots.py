"""Every bot in bots/ honours the bot contract, sits in its level's folder, and every space in spaces/ fits it."""

import os

import pytest

from janken import botfile
from janken.engine import registry
from janken.engine.build import BlueprintBot, load_bot
from janken.engine.registry import P_MAX, discover
from janken.lab import space
from janken.match import bot_name
from janken.notebook import species

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
BOTS_DIR = os.path.join(ROOT, "bots")
SPACES_DIR = os.path.join(ROOT, "spaces")
BOT_PATHS = discover(BOTS_DIR)
SPACE_FILES = sorted(os.listdir(SPACES_DIR))


class TestContract:
    def test_bots_are_yaml_only(self) -> None:
        assert BOT_PATHS
        for path in BOT_PATHS:
            assert not botfile.is_kernel_module(path), path

    @pytest.mark.parametrize("path", BOT_PATHS, ids=bot_name)
    def test_every_bot_loads_and_compiles(self, path: str) -> None:
        bot = load_bot(path)
        assert isinstance(bot, BlueprintBot)
        assert len(botfile.defaults(path)) <= P_MAX
        assert botfile.read(path).description

    @pytest.mark.parametrize("name", SPACE_FILES)
    def test_every_space_fits_a_bot_in_bots(self, name: str) -> None:
        stems = {bot_name(p) for p in BOT_PATHS}
        found = space.load(os.path.join(SPACES_DIR, name))
        assert found.stem == os.path.splitext(name)[0]
        assert found.stem in stems
        assert found.params


class TestLayout:
    @pytest.mark.parametrize("path", BOT_PATHS, ids=bot_name)
    def test_every_bot_sits_in_its_level_folder(self, path: str) -> None:
        assert os.path.dirname(path) == registry.expected_folder(path)

    def test_stems_are_unique_across_levels(self) -> None:
        stems = [bot_name(p) for p in BOT_PATHS]
        assert len(stems) == len(set(stems))

    @pytest.mark.parametrize("name", SPACE_FILES)
    def test_every_space_names_its_bots_file(self, name: str) -> None:
        found = space.load(os.path.join(SPACES_DIR, name))
        assert os.path.normpath(os.path.join(ROOT, found.bot)) == registry.find(
            BOTS_DIR, found.stem
        )


class TestSpecies:
    """research/species.md and the field agree: one current version per species."""

    def test_every_versioned_bot_is_its_species_current_version(self) -> None:
        book = species.load(os.path.join(ROOT, "research"))
        current = {s.current: s for s in book.species}
        versioned = [p for p in BOT_PATHS if species.is_versioned(bot_name(p))]
        assert versioned
        for path in versioned:
            stem = bot_name(path)
            assert stem in current, f"{stem} is not a current version in species.md"
            folder = os.path.basename(os.path.dirname(path))
            assert current[stem].level.lower() == folder, stem

    def test_every_species_has_its_current_version_in_the_field(self) -> None:
        stems = {bot_name(p) for p in BOT_PATHS}
        for found in species.load(os.path.join(ROOT, "research")).species:
            assert found.current in stems, found.name
            assert species.parse_stem(found.current).species == found.name
