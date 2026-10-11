"""A tournament over a set of bot files: who plays whom, and the run's standings.

The schedule is a round robin, or a balanced random schedule for large fields.
Points summarise the run; the CLI ranks by the Glicko-2 rating from
`rating.rate_tournament`, and points only break ties.
"""

import dataclasses
import itertools
import random
from collections.abc import Callable

from . import mocks, progress, settings
from .engine import play_in_batches
from .engine.registry import discover
from .match import MatchResult, bot_name
from .spec import make_spec

POINTS_WIN = 3  # this run only: ranking is the rating, see rating.py
POINTS_DRAW = 1

Schedule = list[tuple[str, str]]


@dataclasses.dataclass
class Standing:
    name: str
    points: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    forfeits: int = 0
    round_wins: int = 0
    round_losses: int = 0

    @property
    def diff(self) -> int:
        return self.round_wins - self.round_losses

    def sort_key(self):
        # Higher is better on every axis; name breaks remaining ties.
        return (-self.points, -self.diff, -self.round_wins, self.name)

    def record(
        self, won: bool | None, round_wins: int, round_losses: int, forfeited: bool
    ) -> None:
        """Add one match: won True / False, or None for a draw."""
        self.round_wins += round_wins
        self.round_losses += round_losses
        self.forfeits += forfeited
        if won is None:
            self.points += POINTS_DRAW
            self.draws += 1
        elif won:
            self.points += POINTS_WIN
            self.wins += 1
        else:
            self.losses += 1


@dataclasses.dataclass
class TournamentResult:
    standings: list[Standing]
    matches: list[MatchResult]
    rounds: int
    matches_per_pair: int


def discover_bots(directory: str) -> list[str]:
    """The bot files in `directory` but the mocks (research only, they cheat:
    janken/mocks.py); a tournament needs at least two."""
    paths = [p for p in discover(directory) if not mocks.is_mock(p)]
    if len(paths) < 2:
        raise SystemExit(f"need at least 2 bots in {directory!r}, found {len(paths)}")
    return paths


def round_robin(bot_paths: list[str], matches_per_pair: int = 1) -> Schedule:
    """Every pair of bots, `matches_per_pair` times."""
    return [
        pair
        for pair in itertools.combinations(bot_paths, 2)
        for _ in range(matches_per_pair)
    ]


def balanced_schedule(
    bot_paths: list[str], games_per_bot: int, rng: random.Random
) -> Schedule:
    """A random schedule where each bot plays about `games_per_bot` matches.

    Give every bot that many tokens, shuffle, and pair adjacent tokens (swapping
    to avoid self-matches). Balanced games per bot keep the points fair without
    playing all O(n^2) pairs.
    """
    tokens = [p for p in bot_paths for _ in range(games_per_bot)]
    rng.shuffle(tokens)
    pairs: Schedule = []
    i, n = 0, len(tokens)
    while i + 1 < n:
        a, b = tokens[i], tokens[i + 1]
        if a == b:  # avoid a self-match: swap in a later, different token
            swap = next((j for j in range(i + 2, n) if tokens[j] != a), None)
            if swap is None:
                break
            tokens[i + 1], tokens[swap] = tokens[swap], tokens[i + 1]
            b = tokens[i + 1]
        pairs.append((a, b))
        i += 2
    return pairs


def standings(names: list[str], matches: list[MatchResult]) -> list[Standing]:
    """Each bot's record over `matches`, best first."""
    table = {name: Standing(name=name) for name in names}
    for m in matches:
        winner = m.winner
        for me, mine, theirs, forfeit in (
            (m.bot_a, m.wins_a, m.wins_b, m.forfeit_a),
            (m.bot_b, m.wins_b, m.wins_a, m.forfeit_b),
        ):
            won = None if winner is None else winner == me
            table[me].record(won, mine, theirs, bool(forfeit))
    return sorted(table.values(), key=Standing.sort_key)


def run_tournament(
    bot_paths: list[str],
    rounds: int,
    matches_per_pair: int = 1,
    on_match: Callable[[MatchResult], None] | None = None,
    workers: int | None = None,
    games_per_bot: int | None = None,
    seed: int | None = None,
    batch_matches: int = settings.config().tournament.batch_matches,
) -> TournamentResult:
    """Play a round robin (or, with `games_per_bot`, a balanced random schedule).

    With `seed`, the schedule and every match are reproducible: each match gets
    its own seed from a master stream. Matches are played `batch_matches` at a
    time, each batch one step of the progress bar.
    """
    rng = random.Random(seed)
    if games_per_bot:
        schedule = balanced_schedule(bot_paths, games_per_bot, rng)
    else:
        schedule = round_robin(bot_paths, matches_per_pair)
    # 32 bits: numba seeds its generator from the low 32 bits only.
    seeds = [rng.getrandbits(32) for _ in schedule]

    specs = {p: make_spec(p) for p in bot_paths}
    pairs = [(specs[a], specs[b]) for a, b in schedule]
    matches: list[MatchResult] = []
    with progress.bar(len(pairs), "compiling", "match") as bar:
        for _, results in play_in_batches(pairs, rounds, seeds, batch_matches, workers):
            bar.set_description("matches")
            bar.update(len(results))
            matches += results
            if on_match:
                for m in results:
                    on_match(m)
    return TournamentResult(
        standings=standings([bot_name(p) for p in bot_paths], matches),
        matches=matches,
        rounds=rounds,
        matches_per_pair=matches_per_pair,
    )
