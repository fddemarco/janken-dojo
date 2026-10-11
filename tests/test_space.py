"""janken/lab/space.py and `uv run janken space`: one space file per bot."""

import dataclasses
import os
import tempfile
import unittest

import yaml
from typer.testing import CliRunner

from janken import settings
from janken.cli import app
from janken.lab import space

BOT = """\
description: a test bot
defaults: {DECAY: 0.9, MAX_LEN: 12, OFFSET: -1, SELECT: 0, LOCK_Z: 4.0}
blueprint:
  signals:
    - LongestMatch: {max_len: $MAX_LEN}
    - Frequency: {decay: $DECAY}
  overlays: [{EmitInvalid: {first_at: $OFFSET}}]
  selector:
    ChooseSelector: {index: $SELECT, options: [Greedy]}
  scorer: {Dirichlet: {decay: $LOCK_Z}}
"""


class SpaceFileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        os.mkdir(os.path.join(self.dir.name, "bots"))
        self.bot = os.path.join(self.dir.name, "bots", "probe.yaml")
        with open(self.bot, "w") as f:
            f.write(BOT)

    def load(self, data: dict[str, object]) -> space.Space:
        return space.from_data({"bot": self.bot, **data}, "test")

    def test_a_space_loads_and_round_trips(self) -> None:
        found = self.load(
            {
                "weight": 0,
                "params": {
                    "DECAY": {"type": "float", "low": 0.5, "high": 1.0, "grid": [0.9]},
                    "SELECT": {"type": "categorical", "choices": [0, 1]},
                },
            }
        )
        self.assertEqual(found.stem, "probe")
        self.assertEqual(found.weight, 0.0)
        self.assertEqual(found.defaults(), {"DECAY": 0.9, "SELECT": 0})
        path = space.write(found, self.dir.name)
        self.assertEqual(space.load(path), found)

    def test_malformed_spaces_are_refused(self) -> None:
        bad: list[dict[str, object]] = [
            {"params": {"NOPE": {"type": "int", "low": 0, "high": 2}}},
            {"params": {"DECAY": {"type": "real", "low": 0, "high": 1}}},
            {"params": {"DECAY": {"type": "float", "low": 0.5}}},
            {"params": {"DECAY": {"type": "float", "low": 0.95, "high": 1.0}}},
            {"params": {"DECAY": {"type": "float", "low": 1.0, "high": 0.5}}},
            {"params": {"MAX_LEN": {"type": "int", "low": 1.5, "high": 20}}},
            {"params": {"SELECT": {"type": "categorical"}}},
            {"params": {"DECAY": {"type": "float", "low": 0, "high": 1, "lo": 0}}},
            {"weight": -1},
            {"extra": 1},
        ]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(space.SpaceError):
                self.load(data)
        with self.assertRaises(space.SpaceError):
            space.from_data({"bot": "no/such/bot.yaml"}, "test")

    def test_a_bot_file_is_not_a_space_file(self) -> None:
        with self.assertRaisesRegex(space.SpaceError, "janken lab space"):
            space.load(self.bot)

    def test_scaffold_ranges_around_every_default(self) -> None:
        found = space.scaffold(
            self.bot, 0.5, dataclasses.replace(settings.config().space, spread=2.0)
        )
        self.assertEqual(found.weight, 0.5)
        self.assertEqual(
            list(found.params), ["DECAY", "MAX_LEN", "OFFSET", "SELECT", "LOCK_Z"]
        )
        p = found.params
        self.assertEqual(
            (p["DECAY"].type, p["DECAY"].low, p["DECAY"].high), ("float", 0.45, 1.0)
        )
        self.assertEqual(
            (p["MAX_LEN"].type, p["MAX_LEN"].low, p["MAX_LEN"].high), ("int", 6, 24)
        )
        self.assertEqual((p["OFFSET"].low, p["OFFSET"].high), (-2, 0))
        self.assertEqual((p["SELECT"].low, p["SELECT"].high), (0, 1))
        self.assertEqual((p["LOCK_Z"].low, p["LOCK_Z"].high), (2.0, 8.0))
        for name, param in p.items():
            self.assertIn(found.defaults()[name], param.grid)
            self.assertTrue(all(param.contains(v) for v in param.grid))
        # what scaffold writes, load accepts
        self.assertEqual(space.load(space.write(found, self.dir.name)), found)

    def test_scaffold_needs_defaults(self) -> None:
        empty = os.path.join(self.dir.name, "empty.yaml")
        with open(empty, "w") as f:
            f.write("blueprint: {}\n")
        with self.assertRaises(space.SpaceError):
            space.scaffold(empty, 1.0, settings.config().space)

    def test_cli_writes_one_file_per_bot_and_keeps_existing_ones(self) -> None:
        out = os.path.join(self.dir.name, "spaces")
        argv = ["lab", "space", self.bot, "--spaces-dir", out, "--weight", "0"]
        runner = CliRunner()
        first = runner.invoke(app, argv)
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertIn("wrote", first.output)
        with open(os.path.join(out, "probe.yaml")) as f:
            self.assertEqual(yaml.safe_load(f)["weight"], 0.0)
        self.assertEqual(runner.invoke(app, argv).exit_code, 2)  # it exists
        self.assertEqual(runner.invoke(app, [*argv, "--force"]).exit_code, 0)


if __name__ == "__main__":
    unittest.main()
