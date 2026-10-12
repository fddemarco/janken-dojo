"""janken/fleet.py: a fleet's champion file, scaffolded on a bot."""

import pathlib
import random

import pytest

from janken import botfile, fleet
from janken.kit.moves import PAPER, ROCK, SCISSORS

CREW = botfile.Fleet(("first", "second"), (ROCK, SCISSORS, PAPER), vigilant=True)


def base(defaults: dict[str, botfile.Number], blueprint: object) -> botfile.BotFile:
    """A base bot, as read."""
    return botfile.BotFile("base.yaml", "Base.", defaults, blueprint)


class TestHandshake:
    def test_a_handshake_is_its_length_in_moves(self) -> None:
        drawn = fleet.draw_handshake(random.Random(1), 12)
        assert len(drawn) == 12
        assert set(drawn) <= {ROCK, PAPER, SCISSORS}

    def test_the_same_seed_draws_the_same_handshake(self) -> None:
        assert fleet.draw_handshake(random.Random(7), 8) == fleet.draw_handshake(
            random.Random(7), 8
        )

    def test_a_handshake_has_a_move_at_least(self) -> None:
        with pytest.raises(fleet.FleetError):
            fleet.draw_handshake(random.Random(1), 0)


class TestChampionFile:
    def read(self, tmp_path: pathlib.Path, text: str) -> botfile.BotFile:
        path = tmp_path / "chief.yaml"
        path.write_text(text, encoding="utf-8")
        return botfile.read(str(path))

    def test_the_file_reads_back_as_the_fleet(self, tmp_path: pathlib.Path) -> None:
        found = base({"DECAY": 0.9, "WARMUP": 10}, {"core": "anything"})
        text = fleet.champion_file("base", found, CREW, "A.")
        found = self.read(tmp_path, text)
        assert found.fleet == CREW
        assert found.defaults == {"DECAY": 0.9, "WARMUP": 10}
        assert found.description == "A."
        assert found.blueprint == {
            "core": {"bot": "base", "space": {"DECAY": "$DECAY", "WARMUP": "$WARMUP"}}
        }

    def test_a_base_without_defaults_binds_none(self, tmp_path: pathlib.Path) -> None:
        text = fleet.champion_file("base", base({}, None), CREW, "A.")
        found = self.read(tmp_path, text)
        assert found.defaults == {}
        assert found.blueprint == {"core": {"bot": "base"}}

    def test_the_bases_guards_and_overlays_are_copied(
        self, tmp_path: pathlib.Path
    ) -> None:
        guards = [{"Noise": {"p": "$NOISE"}}]
        overlays = [{"Stall": {"lock_z": 4.0}}]
        found = base({"NOISE": 0.05}, {"guards": guards, "overlays": overlays})
        copied = self.read(tmp_path, fleet.champion_file("base", found, CREW, "A."))
        assert isinstance(copied.blueprint, dict)
        assert copied.blueprint["guards"] == guards
        assert copied.blueprint["overlays"] == overlays

    def test_a_base_playing_a_team_is_refused(self) -> None:
        found = base({}, {"overlays": [{"Team": {"role": "SUPPORT"}}]})
        with pytest.raises(fleet.FleetError):
            fleet.champion_file("base", found, CREW, "A.")

    def test_the_default_description_names_the_crew(self) -> None:
        text = fleet.default_description("base", "chief", CREW, "Plays well.\nMore.")
        assert "Fleet of 3: chief" in text
        assert "first, second" in text
        assert "base (Plays well.)" in text
        assert "Vigilant" in text
