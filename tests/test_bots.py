"""Every bot in bots/ honours the bot contract, and every space in spaces/ fits it."""

import os

import pytest

from janken import botfile
from janken.engine.build import BlueprintBot, load_bot
from janken.engine.registry import P_MAX, discover
from janken.lab import space
from janken.match import bot_name

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
