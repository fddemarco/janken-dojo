"""Every bot in bots/ honours the bot contract, and every space in spaces/ fits it."""

import os
import unittest

from janken import botfile
from janken.engine.build import BlueprintBot, load_bot
from janken.engine.registry import P_MAX, discover
from janken.lab import space
from janken.match import bot_name

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
BOTS_DIR = os.path.join(ROOT, "bots")
SPACES_DIR = os.path.join(ROOT, "spaces")
BOT_PATHS = discover(BOTS_DIR)


class ContractTest(unittest.TestCase):
    def test_bots_are_yaml_only(self) -> None:
        self.assertTrue(BOT_PATHS)
        for path in BOT_PATHS:
            self.assertFalse(botfile.is_kernel_module(path), path)

    def test_every_bot_loads_and_compiles(self) -> None:
        for path in BOT_PATHS:
            with self.subTest(bot=bot_name(path)):
                bot = load_bot(path)
                self.assertIsInstance(bot, BlueprintBot)
                self.assertLessEqual(len(botfile.defaults(path)), P_MAX)
                self.assertTrue(botfile.read(path).description)

    def test_every_space_fits_a_bot_in_bots(self) -> None:
        stems = {bot_name(p) for p in BOT_PATHS}
        for name in sorted(os.listdir(SPACES_DIR)):
            with self.subTest(space=name):
                found = space.load(os.path.join(SPACES_DIR, name))
                self.assertEqual(found.stem, os.path.splitext(name)[0])
                self.assertIn(found.stem, stems)
                self.assertTrue(found.params)


if __name__ == "__main__":
    unittest.main()
