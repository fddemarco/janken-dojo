"""Calibrate an Oracle: measure a bot's win chances per opponent level.

The bot plays `seeds` seeded matches against every other bot in the bots dir but
the Oracles (which only stand in for bots); each opponent's row is the share of
rounds it won, tied and lost, and the per-level means of the win shares are a
pure Oracle's `wins` (janken/mocks.py, janken/kit/levels.py).
"""

import dataclasses
import random
from collections.abc import Mapping, Sequence

from .. import mocks
from ..engine import play_pairs
from ..engine.registry import discover
from ..match import MatchResult, bot_name
from ..spec import make_spec


@dataclasses.dataclass(frozen=True)
class Row:
    """A bot's (win, tie, loss) shares of the rounds vs one opponent, and its level."""

    win: float
    tie: float
    loss: float
    level: int


def opponents(path: str, bots_dir: str) -> list[str]:
    """Every bot the bot at `path` is measured against: not itself, no Oracle."""
    stem = bot_name(path)
    return [
        p for p in discover(bots_dir) if bot_name(p) != stem and not mocks.is_mock(p)
    ]


def row(results: Sequence[MatchResult], level: int) -> Row:
    """The bot's shares over its matches vs one opponent (the bot is bot a)."""
    won = sum(m.wins_a for m in results)
    tied = sum(m.draws for m in results)
    lost = sum(m.wins_b for m in results)
    total = max(won + tied + lost, 1)
    return Row(won / total, tied / total, lost / total, level)


def level_wins(rows: Mapping[str, Row]) -> dict[int, float]:
    """The mean win share per opponent level, in level order."""
    by_level: dict[int, list[float]] = {}
    for r in rows.values():
        by_level.setdefault(r.level, []).append(r.win)
    return {lv: sum(w) / len(w) for lv, w in sorted(by_level.items())}


def calibrate(
    path: str, bots_dir: str, rounds: int, seeds: int, seed: int, workers: int
) -> dict[str, Row]:
    """The bot's row vs every opponent, by stem.

    Args:
        path: the bot's file.
        bots_dir: where its opponents are.
        rounds: rounds per match.
        seeds: matches vs each opponent.
        seed: draws the match seeds.
        workers: threads playing matches (0: every core).
    """
    found = opponents(path, bots_dir)
    rng = random.Random(seed)
    me = make_spec(path)
    pairs = [(me, make_spec(p)) for p in found for _ in range(seeds)]
    results = play_pairs(
        pairs, rounds, [rng.getrandbits(32) for _ in pairs], workers or None
    )
    return {
        bot_name(p): row(results[k * seeds : (k + 1) * seeds], mocks.path_level(p))
        for k, p in enumerate(found)
    }
