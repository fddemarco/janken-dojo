"""janken/experimental/ and the `experimental` flag: research-only bots and learners.

An experimental bot is never exported, nor is any bot built on one; the arena
referees a Python player like the engine; only the experimental package (and its
CLI command) imports it or its third-party libraries.
"""

import ast
import os
import pathlib

import numpy as np
import pytest

import janken
from janken import botfile, export, library
from janken.engine import play_pairs
from janken.experimental import arena, features, vw
from janken.kit.moves import INVALID, PAPER, ROCK, SCISSORS
from janken.spec import make_spec

R, P, S, X = ROCK, PAPER, SCISSORS, INVALID
NOISY = """\
description: beats our last move, but for its noise
defaults: {NOISE: 0.3}
blueprint:
  guards: [{Noise: {p: $NOISE}}]
  core: {Heuristic: {signal: {LastMove: {of: OPP}}, rotation: BEAT}}
"""
ROCKY = """\
description: always rock
blueprint:
  core: {Heuristic: {signal: {Constant: [ROCK]}, rotation: COPY}}
"""
BUILT_ON = """\
description: a bandit naming {stem}
blueprint:
  core:
    Bandit:
      predictors: [{{bot: {stem}}}]
      scorer: {{DecayedNet: {{decay: 0.9}}}}
      selector: Greedy
"""
LEARNER = vw.Settings("--csoaa 3 --power_t 0 --learning_rate 0.1 --quiet", 2, 0.0)
MAX_ROUNDS = 64
# What may import the experimental package or its libraries (repo-relative).
ALLOWED = ("janken/experimental/", "janken/cli/arena.py")
EXPERIMENTAL_LIBRARIES = ("vowpalwabbit",)


def write(folder: pathlib.Path, name: str, text: str) -> str:
    path = folder / (name + ".yaml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)


def flagged(text: str) -> str:
    return "experimental: true\n" + text


class TestTheFlag:
    def test_a_bot_is_not_experimental_by_default(self, tmp_path) -> None:
        assert not botfile.read(write(tmp_path, "rocky", ROCKY)).experimental

    def test_the_flag_is_read(self, tmp_path) -> None:
        assert botfile.read(write(tmp_path, "rocky", flagged(ROCKY))).experimental

    def test_the_flag_is_true_or_false(self, tmp_path) -> None:
        path = write(tmp_path, "rocky", "experimental: yes please\n" + ROCKY)
        with pytest.raises(botfile.BotFileError, match="true or false"):
            botfile.read(path)


class TestExport:
    def test_an_experimental_bot_is_not_exported(self, tmp_path) -> None:
        path = write(tmp_path, "rocky", flagged(ROCKY))
        with pytest.raises(export.ExportError, match="experimental bot.*rocky"):
            export.scripts(path, MAX_ROUNDS)

    def test_neither_is_a_bot_built_on_one(self, tmp_path) -> None:
        write(tmp_path / "blocks", "rocky", flagged(ROCKY))
        write(tmp_path / "l2", "board", BUILT_ON.format(stem="rocky"))
        tower = write(tmp_path / "l3", "tower", BUILT_ON.format(stem="board"))
        assert library.experimental(tower) == ["rocky"]
        with pytest.raises(export.ExportError, match="rocky"):
            export.scripts(tower, MAX_ROUNDS)

    def test_a_bot_with_no_experimental_bot_is_exported(self, tmp_path) -> None:
        write(tmp_path / "blocks", "rocky", ROCKY)
        board = write(tmp_path / "l2", "board", BUILT_ON.format(stem="rocky"))
        assert library.experimental(board) == []
        assert list(export.scripts(board, MAX_ROUNDS)) == ["board"]


class TestArena:
    @pytest.mark.parametrize(
        ("mine", "theirs", "outcome"),
        [(P, R, 1), (R, P, -1), (S, S, 0), (X, R, -1), (R, X, 1), (X, X, 0)],
    )
    def test_score(self, mine: int, theirs: int, outcome: int) -> None:
        assert arena.score(mine, theirs) == outcome

    @pytest.mark.parametrize("seed", [1, 7])
    def test_it_referees_kit_bots_like_the_engine(self, tmp_path, seed: int) -> None:
        a = make_spec(write(tmp_path, "noisy", NOISY))
        b = make_spec(write(tmp_path, "noisier", NOISY), {"NOISE": 0.6})
        rounds = 40
        (engine,) = play_pairs([(a, b)], rounds, [seed])
        played = arena.play_match(
            arena.KitBot(a, arena.SIDE_A), arena.KitBot(b, arena.SIDE_B), rounds, seed
        )
        assert played == arena.gauntlet.Played(
            engine.wins_a / rounds, engine.wins_b / rounds
        )

    def test_run_skips_the_matches_already_played(self, tmp_path) -> None:
        rocky = write(tmp_path, "rocky", ROCKY)
        job = arena.gauntlet.Job("me", rocky, 1)
        got: list[arena.gauntlet.Job] = []
        arena.run(
            vw.VWPlayer(LEARNER),
            [rocky],
            [1, 2],
            10,
            "me",
            {job: arena.gauntlet.Played(0.0, 0.0)},
            lambda j, _: got.append(j),
        )
        assert got == [arena.gauntlet.Job("me", rocky, 2)]


class TestFeatures:
    def test_history_tokens_read_the_last_rounds_newest_first(self) -> None:
        my = np.array([R, P, S], np.int64)
        opp = np.array([P, X, R], np.int64)
        assert features.history_tokens(my, opp, 3, 2) == [
            *["o1=R", "m1=S", "j1=SR"],
            *["o2=X", "m2=P", "j2=PX", "os2=RX", "js2=SRPX"],
        ]

    def test_no_history_before_the_first_round(self) -> None:
        empty = np.zeros(0, np.int64)
        assert features.history_tokens(empty, empty, 0, 3) == []

    def test_experts_sit_in_both_seats(self, tmp_path) -> None:
        experts = features.Experts.of([make_spec(write(tmp_path, "noisy", NOISY))])
        experts.reset(1, 4)
        my = np.array([R, R, R, R], np.int64)
        opp = np.array([P, P, P, P], np.int64)
        tokens = experts.tokens(my, opp, 1)
        assert [t[:4] for t in tokens] == ["e0m=", "e0o="]


class TestLearner:
    def test_the_costs_of_each_move(self) -> None:
        assert vw.label(ROCK) == "1:1 2:0 3:2"

    def test_it_learns_to_beat_a_constant_bot(self, tmp_path) -> None:
        rocky = arena.KitBot(make_spec(write(tmp_path, "rocky", ROCKY)), arena.SIDE_B)
        played = arena.play_match(vw.VWPlayer(LEARNER), rocky, 60, 1)
        assert played.won > 0.8


def _imports(path: str) -> set[str]:
    """The modules a source file imports (relative ones resolved in janken)."""
    package = os.path.relpath(os.path.dirname(path), REPO).replace(os.sep, ".")
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            base = package.rsplit(".", node.level - 1)[0] if node.level else ""
            module = ".".join(p for p in (base, node.module or "") if p)
            found.add(module)
            found |= {f"{module}.{alias.name}" for alias in node.names}
    return found


REPO = os.path.dirname(os.path.dirname(os.path.abspath(janken.__file__)))


def test_only_the_experimental_package_imports_it_or_its_libraries() -> None:
    root = os.path.dirname(os.path.abspath(janken.__file__))
    offenders = []
    for folder, _, files in os.walk(root):
        for name in files:
            path = os.path.join(folder, name)
            relative = os.path.relpath(path, REPO).replace(os.sep, "/")
            if not name.endswith(".py") or relative.startswith(ALLOWED):
                continue
            for module in _imports(path):
                top = module.split(".")[0]
                if top in EXPERIMENTAL_LIBRARIES or module.startswith(
                    "janken.experimental"
                ):
                    offenders.append(f"{relative}: {module}")
    assert offenders == []
