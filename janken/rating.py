"""The chess titles a rating earns, and rating one tournament in memory.

There is one pool, everybody plays everybody, and a result is worth what the
opponent is worth: beating a strong bot moves you a lot, beating a bot you were
expected to beat moves you barely at all. Titles are labels read off a bot's
peak rating - the "leagues" a bot is placed in.

Nothing persists between runs: every bot enters a run at the starting rating and
the whole run is a single Glicko-2 rating period (see `glicko.py`).
"""

import dataclasses
from collections.abc import Sequence

from . import glicko

START_RATING = glicko.START_RATING

# Titles, weakest first, stored as slugs. `novice` is where every bot starts;
# every rung above it is a floor on the peak rating.
TITLES = ("novice", "cm", "master", "im", "gm")

TITLE_NAMES = {
    "novice": "Novice",
    "cm": "Candidate Master",
    "master": "Master",
    "im": "International Master",
    "gm": "Grandmaster",
}
# Short forms, for fixed-width tables where the full name would dominate a row.
TITLE_ABBR = {
    "novice": "Novice",
    "cm": "CM",
    "master": "Master",
    "im": "IM",
    "gm": "GM",
}

# Peak rating that earns each title, strongest first. Everyone starts at 1500,
# and `rating - 1500` reads as a match win rate against an average bot:
#   cm 1600 = 64%   master 1700 = 76%   im 1900 = 91%   gm 2100 = 97%
RATING_TITLES = (
    ("gm", 2100.0),
    ("im", 1900.0),
    ("master", 1700.0),
    ("cm", 1600.0),
)


def title_for_rating(peak_rating: float) -> str:
    """The strongest title this peak rating reaches (`novice` if none)."""
    for name, floor in RATING_TITLES:
        if peak_rating >= floor:
            return name
    return TITLES[0]


def name(title: str) -> str:
    """Full display name, for prose and announcements."""
    return TITLE_NAMES.get(title, title)


def abbr(title: str) -> str:
    """Short display name, for table cells."""
    return TITLE_ABBR.get(title, title)


def floor_for(title: str):
    """The rating floor that earns `title`, or None for `novice`, the start."""
    return dict(RATING_TITLES).get(title)


def ladder() -> str:
    """The ladder as one line of prose, e.g. for a help string."""
    parts = []
    for title in TITLES:
        floor = floor_for(title)
        parts.append(name(title) if not floor else f"{name(title)} {int(floor)}+")
    return " --> ".join(parts)


@dataclasses.dataclass
class RatingChange:
    before: float
    after: float
    rd: float
    games: int

    @property
    def delta(self) -> float:
        return self.after - self.before


def _period_pairs(matches, score) -> dict[str, list[tuple[str, float]]]:
    """One period's matches as {bot: [(opponent, score), ...]}."""
    by_bot: dict[str, list[tuple[str, float]]] = {}
    for m in matches:
        a, b = m.bot_a, m.bot_b
        by_bot.setdefault(a, []).append(
            (b, score(m.wins_a, m.wins_b, m.draws, m.forfeit_a, m.forfeit_b))
        )
        by_bot.setdefault(b, []).append(
            (a, score(m.wins_b, m.wins_a, m.draws, m.forfeit_b, m.forfeit_a))
        )
    return by_bot


def rate_tournament(
    matches: Sequence, names: Sequence[str] = (), ladder: glicko.Ladder = glicko.MATCH
):
    """Rate one run: `(ratings, titles)`, both keyed by bot name.

    The whole run is one rating period: every match is scored against the
    ratings the bots brought in - all fresh, since nothing persists - so the
    order matches finished in cannot change the answer. A bot in `names` that
    played no match keeps the starting rating.
    """
    fresh = ladder.fresh()
    by_bot = _period_pairs(matches, ladder.score)
    ratings: dict[str, RatingChange] = {}
    titles: dict[str, str] = {}
    for bot in sorted(set(names) | set(by_bot)):
        results = by_bot.get(bot, [])
        new = ladder.update(fresh, [(fresh, score) for _other, score in results])
        ratings[bot] = RatingChange(
            before=fresh.rating, after=new.rating, rd=new.rd, games=len(results)
        )
        titles[bot] = title_for_rating(max(START_RATING, new.rating))
    return ratings, titles
