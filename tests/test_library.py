"""janken/library.py: bots read by stem, so an aggregator names its arms."""

import os
import pathlib

import pytest

from janken import botfile, library
from janken.kit import bot, levels
from janken.kit.blueprint import BlueprintError

LAST = """\
defaults: {OF: OPP}
blueprint:
  core: {Heuristic: {signal: {LastMove: {of: $OF}}, rotation: BEAT}}
"""
BOARD = """\
blueprint:
  core:
    Bandit:
      predictors: [{bot: last, rotations: [COPY, BEAT]}]
      scorer: {DecayedNet: {decay: 0.9}}
      selector: Greedy
"""
TOWER = """\
blueprint:
  core:
    Bandit:
      predictors: [{bot: board}, {bot: last}]
      scorer: {DecayedNet: {decay: 0.9}}
      selector: Greedy
"""


class TestLibrary:
    @pytest.fixture(autouse=True)
    def _bots(self, tmp_path: pathlib.Path) -> None:
        """A bots dir: a block, an L2 over it in the field, a retired L3 over both."""
        self.root = str(tmp_path / "bots")
        self.last = self.write("blocks/last", LAST)
        self.board = self.write("l2/board", BOARD)
        self.tower = self.write("inactive/legacy/tower", TOWER)

    def write(self, name: str, text: str) -> str:
        path = os.path.join(self.root, name + ".yaml")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_the_root_is_the_folder_holding_the_blocks(self) -> None:
        for path in (self.last, self.board, self.tower):
            assert library.library_root(path) == self.root

    def test_a_bot_reads_the_bots_it_names_anywhere_under_the_root(self) -> None:
        tower = library.read_blueprint(self.tower)
        assert levels.level(tower) == 3
        assert isinstance(tower.core, bot.Bandit)
        assert tower.core.predictors[1] == bot.Rotated(bot.LastMove(), (bot.BEAT,))
        assert library.references(self.tower) == ["board", "last"]

    def test_the_hash_covers_the_bots_named(self) -> None:
        before = library.source_hash(self.tower)
        own = library.source_hash(self.last)
        self.write("blocks/last", LAST.replace("OPP", "MY"))
        assert library.source_hash(self.last) != own
        assert library.source_hash(self.tower) != before  # through board too

    def test_bots_naming_each_other_are_refused(self) -> None:
        self.write("blocks/last", BOARD.replace("{bot: last", "{bot: tower"))
        with pytest.raises(BlueprintError, match="cycle"):
            library.read_blueprint(self.tower)

    def test_a_stem_names_one_bot(self) -> None:
        self.write("l1/last", LAST)
        with pytest.raises(BlueprintError, match="2 bots named 'last'"):
            library.read_blueprint(self.board)
        with pytest.raises(BlueprintError, match="0 bots named 'nobody'"):
            library.Library(self.root).path("nobody")

    def test_a_fleets_champion_plays_its_fleets_team(self) -> None:
        chief = self.write(
            "inactive/fleets/chief",
            "fleet: {size: 2, handshake: [ROCK, PAPER], vigilant: true}\n" + BOARD,
        )
        assert library.read_blueprint(chief).overlays == (
            bot.Team(bot.CHAMPION, (bot.ROCK, bot.PAPER), vigilant=True),
        )

    def test_a_champion_declares_no_team_of_its_own(self) -> None:
        chief = self.write(
            "inactive/fleets/chief",
            "fleet: {size: 2, handshake: [ROCK]}\n"
            + BOARD
            + "  overlays: [{Team: {role: SUPPORT, handshake: [ROCK]}}]\n",
        )
        with pytest.raises(BlueprintError, match="fleet section"):
            library.read_blueprint(chief)


class TestFleetSection:
    @pytest.fixture(autouse=True)
    def _folder(self, tmp_path: pathlib.Path) -> None:
        self.folder = tmp_path

    def fleet(self, section: str) -> botfile.Fleet:
        path = self.folder / "chief.yaml"
        path.write_text(f"fleet: {section}\n", encoding="utf-8")
        return botfile.read(str(path)).fleet

    def test_a_fleet_names_its_supports_and_its_handshake(self) -> None:
        found = self.fleet("{size: 3, supports: [a, b], handshake: [SCISSORS, ROCK]}")
        assert found == botfile.Fleet(("a", "b"), (bot.SCISSORS, bot.ROCK))
        assert found.size == 3
        assert found.declared

    def test_unnamed_supports_are_numbered_after_the_champion(self) -> None:
        found = self.fleet("{size: 3, handshake: [ROCK]}")
        assert found.supports == ("chief_support_1", "chief_support_2")

    def test_a_bot_without_a_fleet_section_leads_none(self) -> None:
        path = self.folder / "loner.yaml"
        path.write_text("description: alone\n", encoding="utf-8")
        assert not botfile.read(str(path)).fleet.declared

    @pytest.mark.parametrize(
        "section",
        [
            "{size: 1, handshake: [ROCK]}",  # no supports
            "{size: 3, supports: [a], handshake: [ROCK]}",  # size - 1 names
            "{size: 3, supports: [a, a], handshake: [ROCK]}",  # one name each
            "{size: 2, supports: [chief], handshake: [ROCK]}",  # the champion's
            "{size: 2, handshake: []}",  # no handshake
            "{size: 2, handshake: [BEAT]}",  # not a move
            "{size: 2, handshake: [ROCK], vigilant: 1}",
            "{size: 2, handshake: [ROCK], role: SUPPORT}",  # unknown key
        ],
    )
    def test_a_broken_fleet_section_is_refused(self, section: str) -> None:
        with pytest.raises(botfile.BotFileError):
            self.fleet(section)
