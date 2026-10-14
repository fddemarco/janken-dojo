"""Tournament A/B: two groups of our bots compared on the opponents both met.

A candidate fleet plays the tournament next to the deployed one; both meet many of
the same opponents in the same days. The fair comparison takes only the window in
which both groups were playing, only opponents both met there, and averages each
group's results per opponent, so an opponent met often doesn't outweigh the rest;
the difference is then a mean over opponents, with a CI (research/probes.md).

    window     the span of time in which both groups played
    records    a group's results vs each opponent: share of matches won, margin
    compare    the per-opponent differences of two groups, and their mean and CI

Matches between the groups' own bots, and vs `excluded` names (their fleets), are
left out. The functions are pure; janken/cli/gauntlet.py wires them to
`janken lab gauntlet compare`.
"""

import dataclasses
import math
from collections.abc import Sequence

from . import fingerprint, gauntlet


@dataclasses.dataclass(frozen=True)
class Record:
    """A group's matches vs one opponent: how many, share won (a draw is half),
    and mean margin per round played."""

    matches: int
    won: float
    margin: float


@dataclasses.dataclass(frozen=True)
class Difference:
    """Group a minus group b vs one opponent."""

    opponent: str
    a: Record
    b: Record


@dataclasses.dataclass(frozen=True)
class Comparison:
    """The per-opponent differences, and their mean with a 95% CI half-width
    (normal approximation over opponents), in share won and margin per round."""

    window: tuple[str, str]
    differences: tuple[Difference, ...]
    won: float
    won_half_width: float
    margin: float
    margin_half_width: float


def window(
    matches: Sequence[fingerprint.Match], a: Sequence[str], b: Sequence[str]
) -> tuple[str, str]:
    """From the later first match of the two groups to the earlier last one (an
    empty span, start after end, when they never overlap or one never played)."""
    spans = []
    for group in (set(a), set(b)):
        times = [m.when for m in matches if m.a in group or m.b in group]
        if not times:
            return ("~", "")
        spans.append((min(times), max(times)))
    return (max(s[0] for s in spans), min(s[1] for s in spans))


def records(
    matches: Sequence[fingerprint.Match],
    group: Sequence[str],
    excluded: Sequence[str],
    span: tuple[str, str],
) -> dict[str, Record]:
    """The group's record vs each opponent in the span (matches that ended before
    a round was played are skipped; `excluded` names never count as opponents)."""
    members = set(group)
    out: dict[str, list[tuple[float, float]]] = {}
    for m in matches:
        if not span[0] <= m.when <= span[1] or m.rounds == 0:
            continue
        for me, opp, mine, theirs in (
            (m.a, m.b, m.wins_a, m.wins_b),
            (m.b, m.a, m.wins_b, m.wins_a),
        ):
            if me in members and opp not in members and opp not in excluded:
                result = 1.0 if mine > theirs else 0.5 if mine == theirs else 0.0
                out.setdefault(opp, []).append((result, (mine - theirs) / m.rounds))
    return {
        opp: Record(
            len(rows),
            sum(r for r, _ in rows) / len(rows),
            sum(x for _, x in rows) / len(rows),
        )
        for opp, rows in out.items()
    }


def compare(
    matches: Sequence[fingerprint.Match],
    a: Sequence[str],
    b: Sequence[str],
    excluded: Sequence[str],
) -> Comparison:
    """Group a minus group b over the opponents both met in their common window.

    Raises:
        ValueError: no opponent met by both groups in their common window.
    """
    span = window(matches, a, b)
    skip = [*excluded, *a, *b]
    rec_a = records(matches, a, skip, span)
    rec_b = records(matches, b, skip, span)
    diffs = tuple(
        Difference(opp, rec_a[opp], rec_b[opp]) for opp in sorted(rec_a) if opp in rec_b
    )
    if not diffs:
        raise ValueError("the two groups met no common opponent in their common window")
    won, won_hw = _mean_ci([d.a.won - d.b.won for d in diffs])
    margin, margin_hw = _mean_ci([d.a.margin - d.b.margin for d in diffs])
    return Comparison(span, diffs, won, won_hw, margin, margin_hw)


def _mean_ci(values: Sequence[float]) -> tuple[float, float]:
    mean = sum(values) / len(values)
    if len(values) < 2:
        return mean, math.inf
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return mean, gauntlet.Z95 * math.sqrt(var / len(values))
