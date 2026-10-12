"""janken/library.py: bots read by stem, so an aggregator names its arms."""

import os
import pathlib

import pytest

from janken import library
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
