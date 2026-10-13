"""Sequential stopping: look at the evidence as it grows, stop once it is clear.

A fixed budget plays every match even when the first few already settle the
question (an opponent the candidate beats 60% of the time, a comparison whose
interval cleared 0 at the third round robin). Looking repeatedly at a growing
sample and stopping at the first clear answer inflates the error rate, though:
each look is another chance to stop on noise. So every look gets its own, smaller
share of the error rate alpha, from an alpha-spending function (Lan and DeMets,
1983) with O'Brien and Fleming's shape:

    alpha(t) = 2 - 2 Phi(z_{1 - alpha/2} / sqrt(t)),   t = information so far / at most

which spends almost nothing early and nearly all of alpha at the last look. Look
k may spend alpha(t_k) - alpha(t_{k-1}). By the union bound the chance of ever
stopping on noise stays at most alpha: conservative, since it ignores how
correlated the looks are, the price of needing no numerical integration.

A look tests a mean whose spread comes from the sample itself, so its bound is a
Student t quantile with n - 1 degrees of freedom, not a normal one: with three
matches a normal bound would stop on noise many times more often than it claims.

The functions are pure; gauntlet.py and workflows.py apply them.
"""

import dataclasses
import functools
import math
import statistics
from collections.abc import Sequence

NORMAL = statistics.NormalDist()
BETA_ITERATIONS = 200  # the continued fraction converges in far fewer
BETA_EPSILON = 3e-16
BISECTIONS = 100  # halvings of the t quantile's bracket: far below any precision used
T_MAX = 1e6  # a t quantile's bracket: no alpha used here needs one this far out


def spent(t: float, alpha: float) -> float:
    """The alpha spent by information fraction t (0 < t <= 1): O'Brien-Fleming's."""
    if t <= 0:
        return 0.0
    z = NORMAL.inv_cdf(1 - alpha / 2)
    return 2 - 2 * NORMAL.cdf(z / math.sqrt(min(t, 1.0)))


def look_alphas(fractions: Sequence[float], alpha: float) -> list[float]:
    """The alpha each look may spend, at the given increasing information
    fractions (the last one 1); they sum to alpha."""
    out = []
    before = 0.0
    for t in fractions:
        now = spent(t, alpha)
        out.append(now - before)
        before = now
    return out


def look_alpha(look: int, looks: int, alpha: float) -> float:
    """The alpha of look `look` (1-based) of `looks` equally spaced ones."""
    return look_alphas([k / looks for k in range(1, looks + 1)], alpha)[look - 1]


def _beta_fraction(a: float, b: float, x: float) -> float:
    """The continued fraction of the incomplete beta function (Lentz's method)."""
    tiny = 1e-300
    c, d = 1.0, 1.0 - (a + b) * x / (a + 1.0)
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, BETA_ITERATIONS + 1):
        for numerator in (
            m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m)),
            -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1)),
        ):
            d = 1.0 + numerator * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + numerator / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1.0) < BETA_EPSILON:
            break
    return h


def incomplete_beta(a: float, b: float, x: float) -> float:
    """The regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_front = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(log_front) * _beta_fraction(a, b, x) / a
    return 1.0 - math.exp(log_front) * _beta_fraction(b, a, 1.0 - x) / b


def t_two_sided(t: float, df: int) -> float:
    """P(|T| > t) for Student's t with `df` degrees of freedom."""
    return incomplete_beta(df / 2.0, 0.5, df / (df + t * t))


@functools.cache
def t_bound(alpha: float, df: int) -> float:
    """The two-sided bound of Student's t that `alpha` of it exceeds in size."""
    lo, hi = 0.0, T_MAX
    for _ in range(BISECTIONS):
        mid = (lo + hi) / 2
        if t_two_sided(mid, df) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


def mean_and_se(values: Sequence[float]) -> tuple[float, float]:
    """The sample mean and its standard error (0 with fewer than two values)."""
    n = len(values)
    mean = sum(values) / n
    if n < 2:
        return mean, 0.0
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return mean, math.sqrt(var / n)


def clear_of(values: Sequence[float], level: float, alpha: float) -> bool:
    """Whether the mean of `values` is clear of `level` either way, by a two-sided
    t test at `alpha` (never with fewer than two values: no spread to judge)."""
    if len(values) < 2:
        return False
    mean, se = mean_and_se(values)
    if se == 0.0:
        return mean != level
    return abs(mean - level) / se > t_bound(alpha, len(values) - 1)


def conditional_power(z: float, t: float, bound: float) -> float:
    """The chance the final look clears `bound` (two-sided) if the effect seen so
    far (z at information fraction t) is the true one: the B-value's projection,
    Z_final ~ N(z / sqrt(t), 1 - t). A small one makes going on futile."""
    if t >= 1.0:
        return float(abs(z) > bound)
    drift = z / math.sqrt(t)
    spread = math.sqrt(1.0 - t)
    return NORMAL.cdf((drift - bound) / spread) + NORMAL.cdf((-bound - drift) / spread)


def ladder(planned: int, looks: int) -> list[int]:
    """The sample sizes (1..planned) at which `looks` evenly spaced looks fall."""
    return sorted({max(1, round(planned * k / looks)) for k in range(1, looks + 1)})


@dataclasses.dataclass(frozen=True)
class Look:
    """What one look at a paired comparison found."""

    n: int  # paired units so far
    z: float  # mean / standard error (0 without a spread)
    alpha: float  # what this look may spend
    clear: bool  # the mean is clear of 0 at alpha: stop, the comparison is settled
    futile: bool  # conditional power under `futility`: stop, it won't be


def look(
    diffs: Sequence[float], t: float, alpha: float, final_alpha: float, futility: float
) -> Look:
    """A look at paired differences at information fraction t: clear of 0 at this
    look's `alpha`, or futile (conditional power to clear the last look's bound,
    `final_alpha`, under `futility`; never at the last look)."""
    if len(diffs) < 2:
        return Look(len(diffs), 0.0, alpha, False, False)
    mean, se = mean_and_se(diffs)
    z = mean / se if se > 0 else 0.0
    clear = clear_of(diffs, 0.0, alpha)
    final = NORMAL.inv_cdf(1 - final_alpha / 2)
    futile = not clear and t < 1.0 and conditional_power(z, t, final) < futility
    return Look(len(diffs), z, alpha, clear, futile)
