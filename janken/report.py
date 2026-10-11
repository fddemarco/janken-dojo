"""Presenting a tournament: the standings table, match lines and the JSON dump."""

import dataclasses
from collections.abc import Iterable

from . import rating


def describe_match(m):
    base = f"{m.bot_a} vs {m.bot_b}: "
    forfeits = [(m.bot_a, m.forfeit_a), (m.bot_b, m.forfeit_b)]
    notes = [f"{n} forfeited ({r})" for n, r in forfeits if r]
    if notes:
        return base + "; ".join(notes)
    outcome = "draw" if m.is_draw else f"{m.winner} wins"
    return base + f"{m.wins_a:d}-{m.wins_b:d} ({m.draws:d} draws) -> {outcome}"


def format_table(headers, rows):
    widths = [
        max(len(h), *(len(r[c]) for r in rows)) if rows else len(h)
        for c, h in enumerate(headers)
    ]

    def line(cells: Iterable[str]) -> str:
        return "  ".join(f"{cell:<{w}}" for cell, w in zip(cells, widths, strict=True))

    lines = [line(headers), line("-" * w for w in widths)]
    lines += [line(r) for r in rows]
    return "\n".join(lines)


def standings_table(result, titles, ratings, league="all"):
    """Rank the field by rating, with the title (league) as a label.

    Ties on rating fall back to the run's own points order. With a `league`
    other than "all", only bots holding that title are listed, each keeping its
    position in the full field.
    """
    points_order = {s.name: i for i, s in enumerate(result.standings)}
    standings = sorted(
        result.standings, key=lambda s: (-ratings[s.name].after, points_order[s.name])
    )
    headers = ["#", "bot", "title", "rating", "rd", "W", "D", "L", "forf", "rounds +/-"]
    rows = []
    for i, s in enumerate(standings):
        if league != "all" and titles[s.name] != league:
            continue
        r = ratings[s.name]
        rows.append(
            [
                str(i + 1),
                s.name,
                rating.abbr(titles[s.name]),
                str(round(r.after)),
                str(round(r.rd)),
                str(s.wins),
                str(s.draws),
                str(s.losses),
                str(s.forfeits),
                f"{s.diff:+d}",
            ]
        )
    return format_table(headers, rows)


def result_to_dict(result, titles, ratings):
    return {
        "rounds": result.rounds,
        "matches_per_pair": result.matches_per_pair,
        "titles": titles,
        "ratings": {
            name: {
                "rating": round(c.after, 1),
                "rd": round(c.rd, 1),
                "rated_matches": c.games,
            }
            for name, c in ratings.items()
        },
        "standings": [dataclasses.asdict(s) for s in result.standings],
        "matches": [dataclasses.asdict(m) for m in result.matches],
    }
