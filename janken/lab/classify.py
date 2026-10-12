"""How a kept bot relates to the field's species: alike, better, or new.

Two bots are **alike** when both hold:

- their cores agree on most of the moves they predict, replayed on the same stored
  histories with the same random numbers (`agreement`: a fingerprint that needs no new
  match, but leaves out guards and overlays);
- their per-opponent scores in one paired run correlate (`profile_correlation`: what
  the whole bot does, overlays included).

A challenger alike its species' current version **dominates** it when no matchup's 95%
CI is below 0 and at least one matchup's CI is above 0 at the Bonferroni level
`alpha / m` over the m matchups compared. Without the correction, a copy of the
incumbent would "win" one of ~28 matchups by chance about half the time. A matchup is a
pool opponent (paired over the round robins both met it in), or the head-to-head.

A challenger **as good** as the incumbent (worse on no matchup, better on none) also
replaces it when it is at least `speed_factor` times **faster**: same play, less time.

Versions never cross levels: only a species of the candidate's own level can have it
as its next version or variant.

Everything here is pure: arrays and frames in, values out.
"""

import dataclasses
import statistics
from collections.abc import Mapping, Sequence

import numpy as np
import polars as pl

from .. import settings
from . import analyze

NEW, PROMOTE, VARIANT = "new", "promote", "variant"
OUTCOMES = (NEW, PROMOTE, VARIANT)
HEAD_TO_HEAD = "(head-to-head)"
MOVES = 3  # predictions outside 0..2 are abstentions
BOOTSTRAP_REPS = 20000  # the Bonferroni tails are far out: they need many draws


@dataclasses.dataclass(frozen=True)
class Kin:
    """A field bot, as close as its core is to the candidate's."""

    stem: str
    level: str
    agreement: float


@dataclasses.dataclass(frozen=True)
class Matchup:
    """The challenger minus the incumbent against one opponent.

    `lo`/`hi` is the 95% CI (the "worse" test); `strict_lo` is the lower bound at the
    Bonferroni level (the "better" test). For the head-to-head, `mean` is the
    challenger's score minus ½.
    """

    opponent: str
    n: int
    mean: float
    lo: float
    hi: float
    strict_lo: float

    @property
    def worse(self) -> bool:
        return self.hi < 0

    @property
    def better(self) -> bool:
        return self.strict_lo > 0


@dataclasses.dataclass(frozen=True)
class Decision:
    """What the candidate is, and why."""

    outcome: str  # new | promote | variant
    reasons: tuple[str, ...]


def agreement(pa: np.ndarray, pb: np.ndarray) -> float:
    """The share of rounds where two cores predict the same move.

    Rounds where either abstains (a prediction outside 0..2) are left out; with no
    round left, the agreement is 0.
    """
    a, b = np.ravel(pa), np.ravel(pb)
    both = (a >= 0) & (a < MOVES) & (b >= 0) & (b < MOVES)
    if not both.any():
        return 0.0
    return float(np.mean(a[both] == b[both]))


def ranked(
    candidate: np.ndarray, field: Mapping[str, np.ndarray], levels: Mapping[str, str]
) -> list[Kin]:
    """The field bots by their agreement with the candidate, closest first.

    Args:
        candidate: the candidate core's predictions.
        field: {stem: predictions on the same histories}.
        levels: {stem: level name}, for every stem of `field`.
    """
    kin = [Kin(s, levels[s], agreement(candidate, p)) for s, p in field.items()]
    return sorted(kin, key=lambda k: (-k.agreement, k.stem))


def pairs(field: Mapping[str, np.ndarray]) -> list[tuple[str, str, float]]:
    """Every pair of field bots with its agreement, the most alike first."""
    stems = sorted(field)
    found = [
        (a, b, agreement(field[a], field[b]))
        for i, a in enumerate(stems)
        for b in stems[i + 1 :]
    ]
    return sorted(found, key=lambda x: (-x[2], x[0], x[1]))


def _profile(lf: pl.DataFrame, bot: str) -> dict[str, float]:
    rows = (
        lf.filter((pl.col("bot") == bot) & ~pl.col("opp_cand"))
        .group_by("opp_stem")
        .agg(pl.col("result").mean().alias("score"))
    )
    return dict(zip(rows["opp_stem"], rows["score"], strict=True))


def profile_correlation(lf: pl.DataFrame, a: str, b: str) -> float:
    """Pearson correlation of a's and b's mean score per pool opponent both met.

    A flat profile has no correlation: then two equal profiles count as 1, and
    unequal ones as 0.

    Args:
        lf: a run's matches in long form (`analyze.long_form`).
        a: one bot's label.
        b: the other's.
    """
    pa, pb = _profile(lf, a), _profile(lf, b)
    shared = sorted(set(pa) & set(pb))
    x = np.array([pa[o] for o in shared], np.float64)
    y = np.array([pb[o] for o in shared], np.float64)
    if x.size < 2 or x.std() == 0 or y.std() == 0:
        return 1.0 if x.size and np.allclose(x, y) else 0.0
    return float(np.corrcoef(x, y)[0, 1])


def _counts(lf: pl.DataFrame, a: str, b: str) -> dict[str, int]:
    pool = lf.filter(~pl.col("opp_cand"))
    sa = pool.filter(pl.col("bot") == a).select("rr", "opp", "opp_stem")
    sb = pool.filter(pl.col("bot") == b).select("rr", "opp")
    joined = sa.join(sb, on=["rr", "opp"]).group_by("opp_stem").len()
    return dict(zip(joined["opp_stem"], joined["len"], strict=True))


def _head_to_head(lf: pl.DataFrame, a: str, b: str) -> pl.Series:
    return lf.filter((pl.col("bot") == a) & (pl.col("opp") == b))["result"]


def matchups(
    lf: pl.DataFrame, a: str, b: str, config: settings.SpeciesConfig
) -> list[Matchup]:
    """The challenger `a` minus the incumbent `b`, per matchup, weakest first.

    Only matchups with at least `config.min_matchup_matches` matches count.

    Args:
        lf: a run in long form where `a` and `b` are both candidates.
        a: the challenger's label.
        b: the incumbent's label.
        config: the species settings (the minimum matches and alpha).
    """
    counts = _counts(lf, a, b)
    opponents = sorted(o for o, n in counts.items() if n >= config.min_matchup_matches)
    h2h = _head_to_head(lf, a, b)
    with_h2h = h2h.len() >= config.min_matchup_matches
    m = len(opponents) + int(with_h2h)
    strict = 1 - config.alpha / max(m, 1)
    found = []
    for opp in opponents:
        part = lf.filter(pl.col("opp_stem") == opp)
        loose = analyze.paired_diff(part, a, b, reps=BOOTSTRAP_REPS)
        tight = analyze.paired_diff(part, a, b, reps=BOOTSTRAP_REPS, level=strict)
        if loose is None or tight is None:
            continue
        found.append(
            Matchup(
                opp,
                loose["n"],
                loose["mean"],
                loose["ci_lo"],
                loose["ci_hi"],
                tight["ci_lo"],
            )
        )
    if with_h2h:
        score, n = float(h2h.to_numpy().mean()), h2h.len()
        lo, hi = analyze.wilson(score, n)
        z = statistics.NormalDist().inv_cdf(1 - (1 - strict) / 2)
        strict_lo, _ = analyze.wilson(score, n, z)
        found.append(
            Matchup(HEAD_TO_HEAD, n, score - 0.5, lo - 0.5, hi - 0.5, strict_lo - 0.5)
        )
    return sorted(found, key=lambda x: (x.mean, x.opponent))


def as_good(compared: Sequence[Matchup]) -> bool:
    """Worse on no matchup and better on none: then speed decides."""
    return not any(m.worse or m.better for m in compared)


def needs_run(nearest: Kin, level: str, config: settings.SpeciesConfig) -> bool:
    """Whether the closest species is close enough to need a paired run."""
    return nearest.level == level and nearest.agreement >= config.agreement


def decide(
    nearest: Kin,
    level: str,
    correlation: float,
    compared: Sequence[Matchup],
    config: settings.SpeciesConfig,
    speedup: float = 1.0,
) -> Decision:
    """New species, the next version of `nearest`'s species, or a variant of it.

    Args:
        nearest: the field bot whose core is closest to the candidate's.
        level: the candidate's level.
        correlation: the profile correlation with `nearest` (any value when no
            run was needed).
        compared: the matchups of the paired run (empty when no run was needed).
        config: the species settings.
        speedup: the incumbent's playing time over the challenger's (1: as fast;
            only read when the two are as good as each other).
    """
    if nearest.level != level:
        return Decision(
            NEW, (f"no {level} species is alike (nearest: {nearest.stem})",)
        )
    if nearest.agreement < config.agreement:
        moves = (
            f"its core agrees with {nearest.stem} on {nearest.agreement:.0%}"
            f" of the moves, below {config.agreement:.0%}"
        )
        return Decision(NEW, (moves,))
    if correlation < config.profile_correlation:
        profile = (
            f"its profile correlates {correlation:+.2f} with {nearest.stem}'s,"
            f" below {config.profile_correlation:+.2f}"
        )
        return Decision(NEW, (profile,))
    alike = (
        f"alike {nearest.stem}: agreement {nearest.agreement:.0%},"
        f" profile correlation {correlation:+.2f}"
    )
    worse = [m.opponent for m in compared if m.worse]
    better = [m.opponent for m in compared if m.better]
    if worse:
        return Decision(VARIANT, (alike, f"worse vs {', '.join(worse)}"))
    if not better:
        tie = f"better on no matchup at alpha {config.alpha} / {len(compared)}"
        if speedup > config.speed_factor:
            return Decision(
                PROMOTE,
                (alike, f"{tie}, worse on none, and {speedup:.1f}× faster"),
            )
        return Decision(
            VARIANT,
            (
                alike,
                f"{tie}; {speedup:.1f}× the speed, below {config.speed_factor:.1f}×",
            ),
        )
    return Decision(
        PROMOTE, (alike, f"better vs {', '.join(better)}, worse on no matchup")
    )
