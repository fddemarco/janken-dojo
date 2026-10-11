"""The engine and the tournament: refereeing, schedules, standings, ratings, CLI."""

import os
import random
import shutil
import sys
import tempfile
import textwrap
import unittest
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typer.testing import CliRunner

from janken import rating
from janken.cli import app
from janken.engine import play_pairs
from janken.engine.build import BotContractError, load_bot
from janken.match import INVALID_MOVE_LIMIT, MatchResult
from janken.spec import make_spec
from janken.tournament import Standing, balanced_schedule, discover_bots, run_tournament

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
    "stone": "blueprint:\n  signals: [{Constant: {move: ROCK}}]\n  rotations: [COPY]\n",
    # History matchers: their per-match workspace is sized by the match's rounds.
    "matcher": (
        "blueprint:\n"
        "  signals:\n"
        "    - LongestMatch: {max_len: 6, ctx: JOINT}\n"
        "    - Sim: {signal: {LongestMatch: {max_len: 3, ctx: OPP}}}\n"
        "    - Geometry: {alpha: 0.1, max_len: 6}\n"
        "  scorer: {DecayedNet: {decay: 0.9}}\n"
        "  selector: Greedy\n"
    ),
}


def bot_source(body, state="(0, 1)"):
    return textwrap.dedent("""\
        import random

        from janken.kit.jit import kernel
        from janken.kit.moves import CRASH, INVALID, PAPER, ROCK, SCISSORS

        STATE = %s


        @kernel
        def step(f, i, prm, my, opp, n):
            %s
        """) % (state, body)


class FixtureBots(unittest.TestCase):
    """Writes every fixture bot into one directory, so the suite compiles once."""

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        for name, body in FIXTURES.items():
            with open(cls.bot(name), "w") as f:
                f.write(bot_source(body))
        for name, text in YAML_FIXTURES.items():
            with open(os.path.join(cls.dir, name + ".yaml"), "w") as f:
                f.write(text)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir)

    @classmethod
    def bot(cls, name):
        suffix = ".yaml" if name in YAML_FIXTURES else ".py"
        return os.path.join(cls.dir, name + suffix)

    def play(self, a, b, rounds=10, seed=1):
        (m,) = play_pairs(
            [(make_spec(self.bot(a)), make_spec(self.bot(b)))], rounds, [seed]
        )
        return m


class RefereeTest(FixtureBots):
    def test_transcript_records_every_round(self):
        m = self.play("paper", "rock")
        self.assertEqual(m.moves, "pr" * 10)
        self.assertEqual((m.wins_a, m.wins_b, m.draws), (10, 0, 0))
        self.assertEqual(m.winner, "paper")

    def test_a_few_invalid_moves_cost_only_their_rounds(self):
        m = self.play("slips", "rock")
        slips = INVALID_MOVE_LIMIT - 1
        self.assertIsNone(m.forfeit_a)
        self.assertEqual((m.wins_a, m.wins_b), (10 - slips, slips))
        self.assertTrue(m.moves.startswith("xr" * slips))

    def test_invalid_moves_forfeit_the_match_at_the_limit(self):
        m = self.play("junk", "rock", rounds=50)
        self.assertEqual(m.forfeit_a, f"returned {INVALID_MOVE_LIMIT} invalid moves")
        self.assertEqual(m.winner, "rock")
        # It stops at the limit, and the round that tipped it over still counts.
        self.assertEqual(len(m.moves) // 2, INVALID_MOVE_LIMIT)
        self.assertEqual(m.wins_b, INVALID_MOVE_LIMIT)

    def test_the_limit_is_cumulative_not_consecutive(self):
        m = self.play("alternator", "rock", rounds=100)
        self.assertEqual(m.forfeit_a, f"returned {INVALID_MOVE_LIMIT} invalid moves")
        self.assertEqual(len(m.moves) // 2, 2 * INVALID_MOVE_LIMIT - 1)

    def test_both_invalid_is_a_draw_and_both_forfeit(self):
        m = self.play("junk", "junk")
        self.assertEqual(m.draws, INVALID_MOVE_LIMIT)
        self.assertTrue(m.forfeit_a and m.forfeit_b)
        self.assertIsNone(m.winner)

    def test_a_crash_forfeits_and_stops_the_transcript(self):
        m = self.play("crashy", "rock")
        self.assertEqual(m.forfeit_a, "crashed")
        self.assertEqual(m.winner, "rock")
        self.assertEqual(m.moves, "pr" * 2)  # the crashed round is not recorded

    def test_state_starts_fresh_every_match(self):
        pair = (make_spec(self.bot("counter")), make_spec(self.bot("rock")))
        for m in play_pairs([pair, pair], 5, [1, 2]):
            self.assertEqual(m.wins_a, 5)

    def test_a_seed_makes_a_match_reproducible(self):
        one = self.play("randy", "randy", rounds=50, seed=7)
        two = self.play("randy", "randy", rounds=50, seed=7)
        other = self.play("randy", "randy", rounds=50, seed=8)
        self.assertEqual(one.moves, two.moves)
        self.assertNotEqual(one.moves, other.moves)

    def test_a_yaml_bot_plays_kernel_modules(self):
        m = self.play("stone", "paper", rounds=5)
        self.assertEqual(m.moves, "rp" * 5)
        self.assertEqual((m.wins_a, m.wins_b), (0, 5))

    def test_the_workspace_follows_the_match_length_and_starts_fresh(self):
        short = self.play("matcher", "randy", rounds=20, seed=4)
        long = self.play("matcher", "randy", rounds=60, seed=4)
        self.assertEqual(long.moves[: len(short.moves)], short.moves)
        pair = (make_spec(self.bot("matcher")), make_spec(self.bot("randy")))
        again = play_pairs([pair, pair], 60, [4, 4])
        self.assertEqual([m.moves for m in again], [long.moves, long.moves])

    def test_a_bad_blueprint_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "bad.yaml")
            with open(path, "w") as f:
                f.write("defaults: {UNUSED: 1}\nblueprint: {}\n")
            with self.assertRaises(BotContractError):
                load_bot(path)

    def test_a_file_without_step_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "lazy.py")
            with open(path, "w") as f:
                f.write("DEFAULTS = {}\n")
            with self.assertRaises(ValueError):
                load_bot(path)


class TournamentTest(FixtureBots):
    def test_round_robin_standings(self):
        paths = [self.bot(n) for n in ("rock", "paper", "scissors")]
        result = run_tournament(paths, rounds=10)
        # A perfect rock-paper-scissors cycle: everyone 1 win, 1 loss.
        self.assertEqual(len(result.matches), 3)
        for s in result.standings:
            self.assertEqual((s.points, s.wins, s.losses), (3, 1, 1))

    def test_balanced_schedule(self):
        bots = [f"/b/{i}.py" for i in range(12)]
        sched = balanced_schedule(bots, 6, random.Random(1234))
        games = Counter()
        for a, b in sched:
            self.assertNotEqual(a, b)  # never a self-match
            games[a] += 1
            games[b] += 1
        self.assertEqual(len(sched), 36)  # 12 bots * 6 games / 2
        self.assertTrue(all(g == 6 for g in games.values()))

    def test_balanced_schedule_tournament_runs(self):
        paths = [self.bot(n) for n in ("rock", "paper", "scissors", "randy")]
        result = run_tournament(paths, rounds=5, games_per_bot=2, seed=1)
        self.assertEqual(len(result.matches), 4)  # 4 bots * 2 / 2
        self.assertEqual(len(result.standings), 4)

    def test_underscore_files_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.yaml", "b.py", "_helper.yaml", "notes.txt"):
                open(os.path.join(d, name), "w").close()
            names = [os.path.basename(p) for p in discover_bots(d)]
            self.assertEqual(names, ["a.yaml", "b.py"])

    def test_sort_key_tiebreakers(self):
        strong = Standing("strong", points=6, round_wins=50, round_losses=10)
        weak = Standing("weak", points=6, round_wins=30, round_losses=20)
        self.assertLess(strong.sort_key(), weak.sort_key())

    def test_results_do_not_depend_on_thread_count(self):
        paths = discover_bots(self.dir)
        one = run_tournament(paths, rounds=10, seed=3, workers=1)
        two = run_tournament(paths, rounds=10, seed=3, workers=4)
        self.assertEqual([m.moves for m in one.matches], [m.moves for m in two.matches])

    def test_cli_tournament(self):
        args = ["tournament", "--bots-dir", self.dir, "--rounds", "5", "--seed", "1"]
        result = CliRunner().invoke(app, [*args, "--cache", "off"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("rating", result.output)
        self.assertIn("matches in", result.output)


class RateTournamentTest(unittest.TestCase):
    def test_winners_rise_losers_fall_and_titles_follow(self):
        matches = [
            MatchResult("a", "b", wins_a=10),
            MatchResult("a", "c", wins_a=10),
            MatchResult("b", "c", wins_a=6, wins_b=4),
        ]
        ratings, titles = rating.rate_tournament(matches, ["a", "b", "c", "idle"])
        self.assertGreater(ratings["a"].after, ratings["b"].after)
        self.assertGreater(ratings["b"].after, ratings["c"].after)
        self.assertEqual(ratings["a"].games, 2)
        self.assertEqual(ratings["idle"].after, rating.START_RATING)
        self.assertEqual(ratings["idle"].games, 0)
        self.assertEqual(titles["a"], rating.title_for_rating(ratings["a"].after))
        self.assertEqual(titles["c"], "novice")

    def test_match_order_does_not_matter(self):
        matches = [
            MatchResult("a", "b", wins_a=3),
            MatchResult("b", "c", wins_b=2),
            MatchResult("c", "a", draws=5),
        ]
        forward, _ = rating.rate_tournament(matches)
        backward, _ = rating.rate_tournament(list(reversed(matches)))
        for bot in forward:
            self.assertAlmostEqual(forward[bot].after, backward[bot].after)

    def test_a_forfeit_is_a_loss(self):
        ratings, _ = rating.rate_tournament(
            [MatchResult("a", "b", wins_a=5, forfeit_a="crashed")]
        )
        self.assertLess(ratings["a"].after, ratings["b"].after)


if __name__ == "__main__":
    unittest.main()
