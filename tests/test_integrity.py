"""janken/integrity.py: the rules the field, its spaces and species.md must keep,
checked on hand-made facts (and on bot files written here, for how they're read)."""

import dataclasses
import os
import pathlib

import pytest

from janken import integrity
from janken.engine import registry
from janken.kit import levels
from janken.lab import space
from janken.notebook import species

GOOD = integrity.BotFacts(
    path="bots/l1/a_v1.yaml",
    is_yaml=True,
    description="A bot.",
    n_defaults=1,
    folder="bots/l1",
    expected_folder="bots/l1",
    level=1,
    error="",
)
TUNABLE = {"NOISE": space.Param(type="float", low=0.0, high=0.5)}
FIELD = {"a_v1": "bots/l1/a_v1.yaml", "b": "bots/l2/b.yaml"}


def row(name: str, level: str, current: str) -> species.Species:
    return species.Species(name, level, current, f"`{name}` --> v1", "")


class TestContract:
    def test_a_sound_bot_has_no_problems(self) -> None:
        assert integrity.contract_problems(GOOD) == []

    @pytest.mark.parametrize(
        ("changes", "says"),
        [
            ({"is_yaml": False}, "not a kernel module"),
            ({"description": ""}, "needs a description"),
            ({"n_defaults": registry.P_MAX + 1}, f"at most {registry.P_MAX}"),
            ({"folder": "bots/l2"}, "belongs in bots/l1"),
        ],
        ids=["kernel module", "no description", "too many defaults", "wrong folder"],
    )
    def test_each_broken_rule_is_one_problem(
        self, changes: dict[str, object], says: str
    ) -> None:
        (problem,) = integrity.contract_problems(dataclasses.replace(GOOD, **changes))
        assert says in problem
        assert problem.startswith(GOOD.path)

    def test_an_unreadable_bot_reports_only_why(self) -> None:
        broken = dataclasses.replace(GOOD, error="bad blueprint", folder="x")
        assert integrity.contract_problems(broken) == [f"{GOOD.path}: bad blueprint"]


class TestBlocks:
    @pytest.mark.parametrize("level", [1, levels.ORACLE])
    def test_a_block_is_a_heuristic_or_an_oracle_stand_in(self, level: int) -> None:
        block = dataclasses.replace(GOOD, level=level, folder="bots/blocks")
        assert integrity.block_problems(block) == []

    def test_a_block_above_l1_is_refused(self) -> None:
        (problem,) = integrity.block_problems(dataclasses.replace(GOOD, level=2))
        assert "not L2" in problem


def test_only_shared_stems_are_problems() -> None:
    found = integrity.stem_problems(
        {"a": ["bots/l1/a.yaml"], "b": ["bots/l1/b.yaml", "bots/blocks/b.yaml"]}
    )
    assert found == ["2 bots named 'b': bots/l1/b.yaml, bots/blocks/b.yaml"]


class TestSpaces:
    def test_a_space_fits_its_field_bot(self) -> None:
        found = space.Space(bot="bots/l1/a_v1.yaml", weight=1.0, params=TUNABLE)
        assert integrity.space_problems("a_v1.yaml", found, FIELD) == []

    @pytest.mark.parametrize(
        ("name", "bot", "params", "says"),
        [
            ("x.yaml", "bots/l1/a_v1.yaml", TUNABLE, "not a bot named 'x'"),
            ("c.yaml", "bots/l1/c.yaml", TUNABLE, "no field bot is named 'c'"),
            ("b.yaml", "bots/inactive/b.yaml", TUNABLE, "but b is bots/l2/b.yaml"),
            ("a_v1.yaml", "bots/l1/a_v1.yaml", {}, "no params"),
        ],
        ids=["misnamed", "not in the field", "another file", "nothing to tune"],
    )
    def test_each_misfit_is_one_problem(
        self, name: str, bot: str, params: dict[str, space.Param], says: str
    ) -> None:
        found = space.Space(bot=bot, weight=1.0, params=params)
        (problem,) = integrity.space_problems(name, found, FIELD)
        assert says in problem


class TestSpecies:
    def test_the_book_and_the_field_agree(self) -> None:
        book = [row("a", "L1", "a_v1")]
        assert integrity.species_problems(book, {"a_v1": "l1", "plain": "l2"}) == []

    @pytest.mark.parametrize(
        ("book", "field", "says"),
        [
            ([], {"a_v1": "l1"}, "a_v1: not a species' current version"),
            ([row("a", "L2", "a_v1")], {"a_v1": "l1"}, "species.md says L2"),
            ([row("a", "L1", "a_v1")], {}, "a_v1 is not in the field"),
            ([row("b", "L1", "a_v1")], {"a_v1": "l1"}, "not one of its versions"),
        ],
        ids=["unlisted version", "wrong level", "retired version", "foreign version"],
    )
    def test_each_disagreement_is_one_problem(
        self, book: list[species.Species], field: dict[str, str], says: str
    ) -> None:
        (problem,) = integrity.species_problems(book, field)
        assert says in problem


class TestReadingAField:
    """Bot files written here, read and checked end to end."""

    HEURISTIC = """\
description: copies the opponent.
defaults: {OF: OPP}
blueprint:
  core: {Heuristic: {signal: {LastMove: {of: $OF}}, rotation: COPY}}
"""

    @pytest.fixture(autouse=True)
    def _lab(self, tmp_path: pathlib.Path) -> None:
        self.bots = tmp_path / "bots"
        self.spaces = tmp_path / "spaces"
        self.notebook = tmp_path / "research"
        for folder in (self.bots / "l1", self.spaces, self.notebook):
            folder.mkdir(parents=True)
        (self.notebook / species.FILE).write_text(
            "# Species\n\n| species | level | current | versions | variants |\n"
            "|---|---|---|---|---|\n| `copy` | L1 | `copy_v1` | `copy` --> v1 | |\n"
        )

    def write(self, rel: str, text: str) -> str:
        path = self.bots / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return str(path)

    def problems(self) -> list[str]:
        return integrity.field_problems(
            str(self.bots), str(self.spaces), str(self.notebook)
        )

    def test_a_heuristic_is_read_as_a_sound_l1(self) -> None:
        facts = integrity.read_bot(self.write("l1/copy_v1.yaml", self.HEURISTIC))
        assert (facts.level, facts.n_defaults, facts.error) == (1, 1, "")
        assert facts.folder == facts.expected_folder == os.path.dirname(facts.path)
        assert self.problems() == []

    def test_an_unreadable_bot_is_a_problem_not_a_crash(self) -> None:
        facts = integrity.read_bot(self.write("l1/copy_v1.yaml", "blueprint: 3\n"))
        assert facts.error

    def test_a_misplaced_bot_and_its_orphan_space_are_found(self) -> None:
        self.write("l2/copy_v1.yaml", self.HEURISTIC)
        (self.spaces / "gone.yaml").write_text("bot: bots/l1/gone.yaml\n")
        found = "\n".join(self.problems())
        assert "an L1 bot belongs in" in found
        assert "no bot file" in found
