"""janken/lab/space.py and `uv run janken space`: one space file per bot."""

import dataclasses
import os
import pathlib

import pytest
import yaml
from typer.testing import CliRunner

from janken import settings
from janken.cli import app
from janken.lab import space

BOT = """\
description: a test bot
defaults: {DECAY: 0.9, MAX_LEN: 12, OFFSET: -1, SELECT: 0, LOCK_Z: 4.0}
blueprint:
  core:
    Bandit:
      predictors:
        - LongestMatch: {max_len: $MAX_LEN}
        - Frequency: {decay: $DECAY}
      selector:
        ChooseSelector: {index: $SELECT, options: [Greedy]}
      scorer: {Dirichlet: {decay: $LOCK_Z}}
  overlays: [{EmitInvalid: {first_at: $OFFSET}}]
"""


class TestSpaceFile:
    @pytest.fixture(autouse=True)
    def _probe(self, tmp_path: pathlib.Path) -> None:
        """A probe bot in a fresh bots dir."""
        self.dir = str(tmp_path)
        os.mkdir(os.path.join(self.dir, "bots"))
        self.bot = os.path.join(self.dir, "bots", "probe.yaml")
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
        assert found.stem == "probe"
        assert found.weight == 0.0
        assert found.defaults() == {"DECAY": 0.9, "SELECT": 0}
        path = space.write(found, self.dir)
        assert space.load(path) == found

    @pytest.mark.parametrize(
        "data",
        [
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
        ],
    )
    def test_malformed_spaces_are_refused(self, data: dict[str, object]) -> None:
        with pytest.raises(space.SpaceError):
            self.load(data)

    def test_a_space_of_a_missing_bot_is_refused(self) -> None:
        with pytest.raises(space.SpaceError):
            space.from_data({"bot": "no/such/bot.yaml"}, "test")

    def test_a_bot_file_is_not_a_space_file(self) -> None:
        with pytest.raises(space.SpaceError, match="janken lab space"):
            space.load(self.bot)

    def test_scaffold_ranges_around_every_default(self) -> None:
        found = space.scaffold(
            self.bot, 0.5, dataclasses.replace(settings.config().space, spread=2.0)
        )
        assert found.weight == 0.5
        assert list(found.params) == ["DECAY", "MAX_LEN", "OFFSET", "SELECT", "LOCK_Z"]
        p = found.params
        assert (p["DECAY"].type, p["DECAY"].low, p["DECAY"].high) == (
            "float",
            0.45,
            1.0,
        )
        assert (p["MAX_LEN"].type, p["MAX_LEN"].low, p["MAX_LEN"].high) == (
            "int",
            6,
            24,
        )
        assert (p["OFFSET"].low, p["OFFSET"].high) == (-2, 0)
        assert (p["SELECT"].low, p["SELECT"].high) == (0, 1)
        assert (p["LOCK_Z"].low, p["LOCK_Z"].high) == (2.0, 8.0)
        for name, param in p.items():
            assert found.defaults()[name] in param.grid
            assert all(param.contains(v) for v in param.grid)
        # what scaffold writes, load accepts
        assert space.load(space.write(found, self.dir)) == found

    def test_scaffold_needs_defaults(self) -> None:
        empty = os.path.join(self.dir, "empty.yaml")
        with open(empty, "w") as f:
            f.write("blueprint: {}\n")
        with pytest.raises(space.SpaceError):
            space.scaffold(empty, 1.0, settings.config().space)

    def test_cli_writes_one_file_per_bot_and_keeps_existing_ones(self) -> None:
        out = os.path.join(self.dir, "spaces")
        argv = ["lab", "space", self.bot, "--spaces-dir", out, "--weight", "0"]
        runner = CliRunner()
        first = runner.invoke(app, argv)
        assert first.exit_code == 0, first.output
        assert "wrote" in first.output
        with open(os.path.join(out, "probe.yaml")) as f:
            assert yaml.safe_load(f)["weight"] == 0.0
        assert runner.invoke(app, argv).exit_code == 2  # it exists
        assert runner.invoke(app, [*argv, "--force"]).exit_code == 0
