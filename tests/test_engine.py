"""The engine and the tournament: refereeing, schedules, standings, ratings, CLI."""

import os
import pathlib
import random
import shutil
import textwrap
from collections import Counter

import pytest
from typer.testing import CliRunner

from janken import rating
from janken.cli import app
from janken.engine import play_pairs, registry
from janken.engine.build import BotContractError, load_bot, with_neighbours
from janken.kit import levels
from janken.match import INVALID_MOVE_LIMIT, MatchResult
from janken.spec import make_spec
from janken.tournament import Standing, balanced_schedule, discover_bots, run_tournament
from tests import data

BOTS_DIR = data.BOTS_DIR

# Fixture bots: name -> body of `step(f, i, prm, my, opp, n)`.
FIXTURES = {
    "rock": "return ROCK",
    "paper": "return PAPER",
    "scissors": "return SCISSORS",
    "randy": "return random.randrange(3)",
    "slips": f"return INVALID if n < {INVALID_MOVE_LIMIT - 1} else PAPER",
    "junk": "return INVALID",
    "alternator": "return INVALID if n % 2 == 0 else PAPER",
    "crashy": "return CRASH if n == 2 else PAPER",
    # State starts fresh every match: i[0] counts this match's rounds only.
    "counter": "i[0] += 1\n    return PAPER if i[0] == n + 1 else SCISSORS",
}


# YAML fixture bots: name -> bot file. They share the directory, so the engine
# dispatches both kinds of bot.
YAML_FIXTURES = {
    "stone": (
        "blueprint:\n"
        "  core:\n"
        "    Heuristic: {signal: {Constant: {move: ROCK}}, rotation: COPY}\n"
    ),
    # History matchers: their per-match workspace is sized by the match's rounds.
    "matcher": (
        "blueprint:\n"
        "  core:\n"
        "    Bandit:\n"
        "      predictors:\n"
        "        - {bot: longest}\n"
        "        - {bot: longest, side: OPP, space: {MAX_LEN: 3, CTX: OPP}}\n"
        "        - {bot: geometric}\n"
        "      scorer: {DecayedNet: {decay: 0.9}}\n"
        "      selector: Greedy\n"
    ),
}

# The L1 blocks the YAML fixtures name as arms (blocks/: never in a pool).
YAML_BLOCKS = {
    "longest": (
        "defaults: {MAX_LEN: 6, CTX: JOINT}\n"
        "blueprint:\n"
        "  core:\n"
        "    Heuristic:\n"
        "      signal: {LongestMatch: {max_len: $MAX_LEN, ctx: $CTX}}\n"
        "      rotation: BEAT\n"
    ),
    "geometric": (
        "blueprint:\n"
        "  core:\n"
        "    Heuristic: {signal: {Geometry: {alpha: 0.1, max_len: 6}}, rotation: BEAT}\n"
    ),
}


def bot_source(body: str, state: str = "(0, 1)") -> str:
    return textwrap.dedent("""\
        import random

        from janken.kit.jit import kernel
        from janken.kit.moves import CRASH, INVALID, PAPER, ROCK, SCISSORS

        STATE = %s


        @kernel
        def step(f, i, prm, my, opp, n):
            %s
        """) % (state, body)


@pytest.fixture(scope="class")
def fixture_bots_dir(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> None:
    cls = request.cls
    cls.dir = str(tmp_path_factory.mktemp("fixture_bots"))
    for name, body in FIXTURES.items():
        with open(cls.bot(name), "w") as f:
            f.write(bot_source(body))
    for name, text in YAML_FIXTURES.items():
        with open(os.path.join(cls.dir, name + ".yaml"), "w") as f:
            f.write(text)
    os.makedirs(os.path.join(cls.dir, "blocks"))
    for name, text in YAML_BLOCKS.items():
        with open(os.path.join(cls.dir, "blocks", name + ".yaml"), "w") as f:
            f.write(text)


@pytest.mark.usefixtures("fixture_bots_dir")
class FixtureBots:
    """Writes every fixture bot into one directory, so the suite compiles once."""

    dir: str

    @classmethod
    def bot(cls, name: str) -> str:
        suffix = ".yaml" if name in YAML_FIXTURES else ".py"
        return os.path.join(cls.dir, name + suffix)

    def play(self, a: str, b: str, rounds: int = 10, seed: int = 1) -> MatchResult:
        (m,) = play_pairs(
            [(make_spec(self.bot(a)), make_spec(self.bot(b)))], rounds, [seed]
        )
        return m


class TestReferee(FixtureBots):
    def test_transcript_records_every_round(self) -> None:
        m = self.play("paper", "rock")
        assert m.moves == "pr" * 10
        assert (m.wins_a, m.wins_b, m.draws) == (10, 0, 0)
        assert m.winner == "paper"

    def test_a_few_invalid_moves_cost_only_their_rounds(self) -> None:
        m = self.play("slips", "rock")
        slips = INVALID_MOVE_LIMIT - 1
        assert m.forfeit_a is None
        assert (m.wins_a, m.wins_b) == (10 - slips, slips)
        assert m.moves.startswith("xr" * slips)

    def test_invalid_moves_forfeit_the_match_at_the_limit(self) -> None:
        m = self.play("junk", "rock", rounds=9)
        assert m.forfeit_a == f"returned {INVALID_MOVE_LIMIT} invalid moves"
        assert m.winner == "rock"
        # It stops at the limit, and the round that tipped it over still counts.
        assert len(m.moves) // 2 == INVALID_MOVE_LIMIT
        assert m.wins_b == INVALID_MOVE_LIMIT

    def test_the_limit_is_cumulative_not_consecutive(self) -> None:
        m = self.play("alternator", "rock", rounds=9)
        assert m.forfeit_a == f"returned {INVALID_MOVE_LIMIT} invalid moves"
        assert len(m.moves) // 2 == 2 * INVALID_MOVE_LIMIT - 1

    def test_both_invalid_is_a_draw_and_both_forfeit(self) -> None:
        m = self.play("junk", "junk")
        assert m.draws == INVALID_MOVE_LIMIT
        assert m.forfeit_a and m.forfeit_b
        assert m.winner is None

    def test_a_crash_forfeits_and_stops_the_transcript(self) -> None:
        m = self.play("crashy", "rock")
        assert m.forfeit_a == "crashed"
        assert m.winner == "rock"
        assert m.moves == "pr" * 2  # the crashed round is not recorded

    def test_state_starts_fresh_every_match(self) -> None:
        pair = (make_spec(self.bot("counter")), make_spec(self.bot("rock")))
        for m in play_pairs([pair, pair], 5, [1, 2]):
            assert m.wins_a == 5

    def test_a_seed_makes_a_match_reproducible(self) -> None:
        one = self.play("randy", "randy", rounds=9, seed=7)
        two = self.play("randy", "randy", rounds=9, seed=7)
        other = self.play("randy", "randy", rounds=9, seed=8)
        assert one.moves == two.moves
        assert one.moves != other.moves

    def test_a_yaml_bot_plays_kernel_modules(self) -> None:
        m = self.play("stone", "paper", rounds=5)
        assert m.moves == "rp" * 5
        assert (m.wins_a, m.wins_b) == (0, 5)

    def test_the_workspace_follows_the_match_length_and_starts_fresh(self) -> None:
        short = self.play("matcher", "randy", rounds=4, seed=4)
        long = self.play("matcher", "randy", rounds=9, seed=4)
        assert long.moves[: len(short.moves)] == short.moves
        pair = (make_spec(self.bot("matcher")), make_spec(self.bot("randy")))
        again = play_pairs([pair, pair], 9, [4, 4])
        assert [m.moves for m in again] == [long.moves, long.moves]

    def test_a_bad_blueprint_is_refused(self, tmp_path: pathlib.Path) -> None:
        d = str(tmp_path)
        path = os.path.join(d, "bad.yaml")
        with open(path, "w") as f:
            f.write("defaults: {UNUSED: 1}\nblueprint: {}\n")
        with pytest.raises(BotContractError):
            load_bot(path)

    def test_a_file_without_step_is_refused(self, tmp_path: pathlib.Path) -> None:
        d = str(tmp_path)
        path = os.path.join(d, "lazy.py")
        with open(path, "w") as f:
            f.write("DEFAULTS = {}\n")
        with pytest.raises(ValueError):
            load_bot(path)


class TestTournament(FixtureBots):
    def test_round_robin_standings(self) -> None:
        paths = [self.bot(n) for n in ("rock", "paper", "scissors")]
        result = run_tournament(paths, rounds=10)
        # A perfect rock-paper-scissors cycle: everyone 1 win, 1 loss.
        assert len(result.matches) == 3
        for s in result.standings:
            assert (s.points, s.wins, s.losses) == (3, 1, 1)

    def test_balanced_schedule(self) -> None:
        bots = [f"/b/{i}.py" for i in range(12)]
        sched = balanced_schedule(bots, 6, random.Random(1234))
        games = Counter()
        for a, b in sched:
            assert a != b  # never a self-match
            games[a] += 1
            games[b] += 1
        assert len(sched) == 36  # 12 bots * 6 games / 2
        assert all(g == 6 for g in games.values())

    def test_balanced_schedule_tournament_runs(self) -> None:
        paths = [self.bot(n) for n in ("rock", "paper", "scissors", "randy")]
        result = run_tournament(paths, rounds=5, games_per_bot=2, seed=1)
        assert len(result.matches) == 4  # 4 bots * 2 / 2
        assert len(result.standings) == 4

    def test_underscore_files_skipped(self, tmp_path: pathlib.Path) -> None:
        d = str(tmp_path)
        for name in ("a.yaml", "b.py", "_helper.yaml", "notes.txt"):
            open(os.path.join(d, name), "w").close()
        names = [os.path.basename(p) for p in discover_bots(d)]
        assert names == ["a.yaml", "b.py"]

    def test_sort_key_tiebreakers(self) -> None:
        strong = Standing("strong", points=6, round_wins=50, round_losses=10)
        weak = Standing("weak", points=6, round_wins=30, round_losses=20)
        assert strong.sort_key() < weak.sort_key()

    def test_results_do_not_depend_on_thread_count(self) -> None:
        paths = discover_bots(self.dir)
        one = run_tournament(paths, rounds=10, seed=3, workers=1)
        two = run_tournament(paths, rounds=10, seed=3, workers=4)
        assert [m.moves for m in one.matches] == [m.moves for m in two.matches]

    def test_cli_tournament(self) -> None:
        args = ["tournament", "--bots-dir", self.dir, "--rounds", "5", "--seed", "1"]
        result = CliRunner().invoke(app, [*args, "--cache", "off"])
        assert result.exit_code == 0, result.output
        assert "rating" in result.output
        assert "matches in" in result.output


class TestRateTournament:
    def test_winners_rise_losers_fall_and_titles_follow(self) -> None:
        matches = [
            MatchResult("a", "b", wins_a=10),
            MatchResult("a", "c", wins_a=10),
            MatchResult("b", "c", wins_a=6, wins_b=4),
        ]
        ratings, titles = rating.rate_tournament(matches, ["a", "b", "c", "idle"])
        assert ratings["a"].after > ratings["b"].after
        assert ratings["b"].after > ratings["c"].after
        assert ratings["a"].games == 2
        assert ratings["idle"].after == rating.START_RATING
        assert ratings["idle"].games == 0
        assert titles["a"] == rating.title_for_rating(ratings["a"].after)
        assert titles["c"] == "novice"

    def test_match_order_does_not_matter(self) -> None:
        matches = [
            MatchResult("a", "b", wins_a=3),
            MatchResult("b", "c", wins_b=2),
            MatchResult("c", "a", draws=5),
        ]
        forward, _ = rating.rate_tournament(matches)
        backward, _ = rating.rate_tournament(list(reversed(matches)))
        for bot in forward:
            assert forward[bot].after == pytest.approx(
                backward[bot].after, rel=0, abs=0.5e-7
            )

    def test_a_forfeit_is_a_loss(self) -> None:
        ratings, _ = rating.rate_tournament(
            [MatchResult("a", "b", wins_a=5, forfeit_a="crashed")]
        )
        assert ratings["a"].after < ratings["b"].after


def touch(*parts: str) -> str:
    """An empty file at the joined path, its folders made; returns the path."""
    path = os.path.join(*parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()
    return os.path.normpath(path)


class TestLevelFolders:
    @pytest.mark.parametrize(
        ("level", "folder"), [(1, "l1"), (4, "l4"), (levels.ORACLE, "oracle")]
    )
    def test_folder(self, level: int, folder: str) -> None:
        assert levels.folder(level) == folder

    @pytest.mark.parametrize(
        ("name", "is_level"),
        [("l1", True), ("l12", True), ("oracle", True), ("l", False)]
        + [("lx", False), ("inactive", False), ("fleets", False)],
    )
    def test_is_level_folder(self, name: str, is_level: bool) -> None:
        assert levels.is_level_folder(name) is is_level

    def test_discover_reads_level_folders_only(self, tmp_path: pathlib.Path) -> None:
        d = str(tmp_path)
        found = [
            touch(d, "flat.yaml"),
            touch(d, "l1", "a.yaml"),
            touch(d, "l3", "b.yaml"),
            touch(d, "oracle", "c.yaml"),
        ]
        touch(d, "inactive", "legacy", "old.yaml")
        touch(d, "inactive", "d.yaml")
        touch(d, "notes", "e.yaml")
        assert registry.discover(d) == sorted(found)

    def test_field_root(self) -> None:
        assert registry.field_root(os.path.join("bots", "l2", "x.yaml")) == "bots"
        assert registry.field_root(os.path.join("bots", "x.yaml")) == "bots"
        fleet = os.path.join("bots", "inactive", "fleets", "f")
        assert registry.field_root(os.path.join(fleet, "x.yaml")) == fleet

    def test_find(self, tmp_path: pathlib.Path) -> None:
        d = str(tmp_path)
        a = touch(d, "l1", "a.yaml")
        touch(d, "l1", "twice.yaml")
        touch(d, "l2", "twice.yaml")
        assert registry.find(d, "a") == a
        with pytest.raises(FileNotFoundError, match="no bot"):
            registry.find(d, "missing")
        with pytest.raises(FileNotFoundError, match="2 bots named"):
            registry.find(d, "twice")

    def test_neighbours_span_the_field(self, tmp_path: pathlib.Path) -> None:
        d = str(tmp_path)
        field = [touch(d, "l1", "a.yaml"), touch(d, "l2", "b.yaml")]
        touch(d, "inactive", "c.yaml")
        assert with_neighbours([field[1]]) == sorted(field)

    def test_bot_check_refuses_a_misplaced_bot(self, tmp_path: pathlib.Path) -> None:
        d = str(tmp_path)
        rock = os.path.join(d, "l2", "rock.yaml")
        os.makedirs(os.path.dirname(rock))
        shutil.copy(registry.find(BOTS_DIR, "rock_v1"), rock)
        result = CliRunner().invoke(app, ["bot", "check", "--bots-dir", d, "rock"])
        assert result.exit_code == 2
        assert f"{os.sep}l1: move it there" in result.output
