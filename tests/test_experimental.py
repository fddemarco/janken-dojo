"""janken/experimental/ and the `experimental` flag: research-only bots and learners.

An experimental bot is never exported, nor is any bot built on one; the arena
referees a Python player like the engine; only the experimental package (and its
CLI command) imports it or its third-party libraries.
"""

import ast
import os
import pathlib
from collections.abc import Sequence

import numpy as np
import pytest

import janken
from janken import botfile, export, library
from janken.engine import play_pairs
from janken.experimental import arena, features, identify, pretrained, vw
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
ALLOWED = ("janken/experimental/", "janken/cli/arena.py", "janken/cli/identify.py")
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
            arena.KitBot.of(a, arena.SIDE_A),
            arena.KitBot.of(b, arena.SIDE_B),
            rounds,
            seed,
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
        rocky = arena.KitBot.of(
            make_spec(write(tmp_path, "rocky", ROCKY)), arena.SIDE_B
        )
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


# --- identifying an opponent's parameters (janken/experimental/identify.py) --------

LAST = """\
defaults: {OF: OPP}
blueprint:
  core: {Heuristic: {signal: {LastMove: {of: $OF}}, rotation: BEAT}}
"""
BOARD = """\
description: a greedy bandit over the last move, turned three ways
defaults: {DECAY: 0.9}
blueprint:
  core:
    Bandit:
      predictors: [{bot: last, rotations: [COPY, BEAT, BEAT_BEAT]}]
      scorer: {DecayedNet: {decay: $DECAY}}
      selector: Greedy
"""
TALLY = BOARD.replace("DecayedNet: {decay: $DECAY}", "Dirichlet: {decay: $DECAY}")
SPACE = """\
bot: {path}
weight: 1.0
params:
  DECAY: {{type: float, low: 0.1, high: 0.99}}
"""
IDENTIFY_ROUNDS = 40


class Stub:
    """A particle that predicts one fixed move."""

    def __init__(self, move: int) -> None:
        self.at: int = move

    def reset(self, seed: int, rounds: int) -> None:
        del seed, rounds

    def move(self, my: np.ndarray, opp: np.ndarray, n: int) -> int:
        del my, opp, n
        return self.at


def posterior(*moves: int, stems: tuple[str, ...] = ()) -> identify.Posterior:
    found = [
        identify.Hypothesis(stems[k] if stems else f"s{k}", {"X": k})
        for k in range(len(moves))
    ]
    built = identify.Posterior(found, [Stub(m) for m in moves], 0.5, 1.0)
    built.reset(1, 10, "")
    return built


def observed(post: identify.Posterior, theirs: Sequence[int]) -> None:
    empty = np.zeros(0, np.int64)
    for n, move in enumerate(theirs):
        post.step(empty, empty, n)
        post.observe(move)


class TestPosterior:
    def test_the_particle_that_names_their_moves_wins(self) -> None:
        post = posterior(R, P, S)
        observed(post, [P, P, R, P])
        assert post.best().params == {"X": 1}
        assert post.weights().sum() == pytest.approx(1.0)
        assert post.vote() == P

    def test_a_miss_lowers_a_particle_without_killing_it(self) -> None:
        post = posterior(R, P)
        observed(post, [R, R, P])
        assert 0 < post.weights()[1] < post.weights()[0]

    def test_pruning_keeps_the_best_particle(self) -> None:
        post = posterior(R, P, S)
        observed(post, [S] * 8)
        post.prune(1e-2)
        assert post.alive.tolist() == [False, False, True]
        assert post.best().params == {"X": 2}

    def test_an_excluded_species_never_lives(self) -> None:
        post = posterior(R, P, stems=("a", "b"))
        post.reset(1, 10, "a")
        observed(post, [R, R, R])
        assert post.best().stem == "b"
        with pytest.raises(ValueError, match="no hypothesis"):
            posterior(R, stems=("a",)).reset(1, 10, "a")

    def test_moves_that_arent_moves_get_no_vote(self) -> None:
        post = posterior(INVALID, P)
        observed(post, [P])
        assert post.vote() == P


def test_a_particle_replays_the_bot_from_the_opponents_seat() -> None:
    data = identify.particle_data(identify.Hypothesis("board", {"DECAY": 0.5}), True)
    signal = {
        "bot": "board",
        "side": "OPP",
        "rotations": ["COPY"],
        "space": {"DECAY": 0.5},
        "estimate": "NORMAL",
    }
    assert data == {"core": {"Heuristic": {"signal": signal, "rotation": "COPY"}}}


class TestStudy:
    @pytest.fixture(autouse=True)
    def _field(self, tmp_path: pathlib.Path) -> None:
        bots = tmp_path / "bots"
        write(bots / "blocks", "last", LAST)
        self.board = write(bots / "l2", "board", BOARD)
        self.tally = write(bots / "l2", "tally", TALLY)
        self.probe = write(bots / "l1", "noisy", NOISY)
        self.spaces = tmp_path / "spaces"
        for path in (self.board, self.tally):
            write(self.spaces, pathlib.Path(path).stem, SPACE.format(path=path))

    def setup_for(self, leave_one_out: bool) -> identify.Setup:
        return identify.Setup(
            hypotheses=(self.board, self.tally),
            spaces_dir=str(self.spaces),
            particles=3,
            sampler_seed=0,
            eps=0.5,
            commit=20,
            every=10,
            prune_ratio=1e-6,
            near=0.1,
            probe=self.probe,
            rounds=IDENTIFY_ROUNDS,
            leave_one_out=leave_one_out,
            forget=1.0,
            switch_decay=0.9,
            components=(),
        )

    def test_a_match_logs_its_checkpoints_and_three_branches(self) -> None:
        setup = self.setup_for(False)
        drawn = identify.field(setup).hypotheses[1]
        opponent = f"{self.board}:DECAY={drawn.params['DECAY']}"
        row = identify.study(setup, opponent, 3)
        assert row["prefix_agrees"]
        assert [c["round"] for c in row["checkpoints"]] == [10, 20, 30]
        last = row["checkpoints"][-1]
        assert last["correct"] and last["param_error"] == pytest.approx(0.0)
        for branch in identify.BRANCHES:
            won, lost = row[branch]["won"], row[branch]["lost"]
            assert 0 <= won + lost <= 1

    def test_leave_one_out_never_names_the_opponents_species(self) -> None:
        row = identify.study(self.setup_for(True), self.board, 3)
        assert {c["map"] for c in row["checkpoints"]} == {"tally"}


def test_curves_and_gains_average_matches() -> None:
    def row(exploit: float, correct: bool) -> dict:
        point = {"round": 25, "correct": correct, "species_mass": 1.0}
        point |= {"near_mass": 0.5, "hit": 0.5, "alive": 4}
        if correct:
            point["param_error"] = 0.2
        return {
            "checkpoints": [point],
            "exploit": {"won": exploit, "lost": 0.0},
            "keep": {"won": 0.1, "lost": 0.0},
            "oracle": {"won": 0.5, "lost": 0.0},
            "switch": {"won": 0.1, "lost": 0.0},
        }

    rows = [row(0.3, True), row(0.5, False)]
    (point,) = identify.curve(rows)
    assert (point.correct, point.param_error, point.matches) == (0.5, 0.2, 2)
    exploit = identify.gains(rows)[0]
    assert exploit.vs_keep == pytest.approx(0.3)
    assert exploit.half_width > 0


def test_a_component_is_read_from_both_seats_at_every_rotation() -> None:
    read = identify.components("bots/blocks/ngram.yaml")
    assert {(h.side, h.rotation) for h in read} == {
        (side, rotation)
        for side in ("OPP", "MY")
        for rotation in ("COPY", "BEAT", "BEAT_BEAT")
    }
    assert {h.stem for h in read} == {"ngram"} and all(not h.params for h in read)


class TestPretrainedTable:
    """janken/experimental/pretrained.py: a context table, pre-trained or not."""

    def test_context_reads_the_last_k_joint_moves(self) -> None:
        my = np.array([R, P, S], np.int64)
        opp = np.array([S, R, P], np.int64)
        assert pretrained.context(my, opp, 3, 2) == (P * 3 + R) * 9 + (S * 3 + P)

    def test_counts_skip_rounds_next_to_invalid_moves(self) -> None:
        table = np.zeros((9, 3))
        my = np.array([R, R, R, R], np.int64)
        opp = np.array([P, X, P, P], np.int64)
        pretrained._count(table, my, opp, 1)
        assert table.sum() == 1 and table[R * 3 + P, P] == 1

    def test_a_prior_plays_its_belief_from_the_first_context(self) -> None:
        prior = np.zeros((9, 3))
        prior[R * 3 + R] = [0.0, 0.0, 1.0]  # after (R, R) they play scissors
        player = pretrained.Table(prior, 1, 5.0)
        player.reset(1, 4)
        my = np.array([R, R], np.int64)
        opp = np.array([R, R], np.int64)
        assert player.move(my, opp, 1) == R  # beats scissors

    def test_without_a_prior_it_learns_the_match(self) -> None:
        rocky = arena.KitBot.of(
            make_spec(write(pathlib.Path(self.tmp), "rocky", ROCKY)), arena.SIDE_B
        )
        player = pretrained.Table(np.zeros((9, 3)), 1, 0.0)
        assert arena.play_match(player, rocky, 60, 1).won > 0.8

    @pytest.fixture(autouse=True)
    def _tmp(self, tmp_path: pathlib.Path) -> None:
        self.tmp = str(tmp_path)
