"""Selectors, compiled: pick the move to play from an ensemble's pending arms.

    First        the first arm with a move, else a fallback
    Greedy       the best-scored arm (ties: first, or random); deterministic play
                 is readable by opponents that replay us (experiment 0006)
    Thompson     Thompson sampling of each arm's Dirichlet (the Kaggle winner's
                 bandit; rps_kaggle §4.5)
    SampledVote  a move sampled from the arms' softmax vote: exploits like the
                 best arms while staying hard to predict (idea #10; a sampled arm
                 inside an argmax bandit is inert, experiment 0001)
    Gatekeeper   a Gate, compiled (janken/kit/blueprint/lowering.py): two
                 experts, the last arm (a replay) and Thompson over the rest,
                 picked by the last arm's own record (EDGE), the main expert's
                 lead over it (ANTI_FIRST) or a bandit over both (BANDIT); idea
                 #30: the replay of smartbot_sims wins the metabot family, its
                 arms the zoo (experiments 0015, 0016)

A random arm is the defence when no model beats chance (dllu): scored like any
arm, or pinned at a score of 0, so random play wins once every model is losing.
"""

import math
import random

import numpy as np

from . import codes as c
from .ensemble import score_arm, value
from .jit import kernel


@kernel
def _random_value(spec: np.ndarray, e: int, f: np.ndarray, i: np.ndarray) -> float:
    """The random arm's score: its record when scored, 0 when pinned."""
    if spec[e + c.E_RANDOM] == c.RA_SCORED:
        at = spec[e + c.E_SCORE_F] + 3 * spec[e + c.E_NARMS]
        return value(spec[e + c.E_SCORER], f, at)
    return 0.0


@kernel
def _play(move: int) -> int:
    """A pending move as played: the pinned random arm draws its move now."""
    return random.randrange(3) if move == c.RANDOM_MOVE else move


@kernel
def _first(spec: np.ndarray, sel: int, e: int, i: np.ndarray) -> int:
    pend = spec[e + c.E_PEND_I]
    for a in range(spec[e + c.E_NARMS]):
        if i[pend + 1 + a] >= 0:
            return i[pend + 1 + a]
    fallback = spec[sel + c.R_A]
    return random.randrange(3) if fallback == c.RANDOM_MOVE else fallback


@kernel
def _greedy(spec: np.ndarray, sel: int, e: int, f: np.ndarray, i: np.ndarray) -> int:
    pend = spec[e + c.E_PEND_I]
    n_arms = spec[e + c.E_NARMS]
    scorer = spec[e + c.E_SCORER]
    score_f = spec[e + c.E_SCORE_F]
    has_random = spec[e + c.E_RANDOM] != c.RA_NONE
    vals = np.empty(n_arms + 1)
    best = -math.inf
    for a in range(n_arms + 1):
        vals[a] = -math.inf
        if a < n_arms and i[pend + 1 + a] >= 0:
            vals[a] = value(scorer, f, score_f + 3 * a)
        elif a == n_arms and has_random:
            vals[a] = _random_value(spec, e, f, i)
        best = max(best, vals[a])
    if best == -math.inf:
        return random.randrange(3)
    cand = np.empty(n_arms + 1, np.int64)
    k = 0
    for a in range(n_arms + 1):
        if vals[a] > -math.inf and vals[a] >= best - 1e-9:
            cand[k] = a
            k += 1
    pick = cand[0]
    if spec[sel + c.R_A] == c.TIES_RANDOM and k > 1:
        pick = cand[random.randrange(k)]
    return _play(i[pend + 1 + pick])


@kernel
def _draw(f: np.ndarray, at: int, sharp: float) -> float:
    """A Thompson draw of the Dirichlet record f[at : at + 3] (counts times
    `sharp`): a sampled P(win) - P(loss)."""
    gw = random.gammavariate(1.0 + sharp * f[at], 1.0)
    gt = random.gammavariate(1.0 + sharp * f[at + 1], 1.0)
    gl = random.gammavariate(1.0 + sharp * f[at + 2], 1.0)
    return (gw - gl) / (gw + gt + gl)


@kernel
def _sample(
    spec: np.ndarray, e: int, f: np.ndarray, i: np.ndarray, sharp: float, skip: int
) -> int:
    """Thompson sampling over ensemble e's arms but arm `skip` (-1: none)."""
    return _sample_but(spec, e, f, i, sharp, skip, skip + 1)


@kernel
def _sample_but(
    spec: np.ndarray,
    e: int,
    f: np.ndarray,
    i: np.ndarray,
    sharp: float,
    lo: int,
    hi: int,
) -> int:
    """Thompson sampling over ensemble e's arms but arms lo .. hi - 1."""
    pend = spec[e + c.E_PEND_I]
    score_f = spec[e + c.E_SCORE_F]
    best = -2.0
    pick = c.NO_MOVE
    for a in range(spec[e + c.E_NARMS] + 1):
        move = i[pend + 1 + a]
        if move < 0 or lo <= a < hi:
            continue
        sampled = _draw(f, score_f + 3 * a, sharp)
        if sampled > best:
            best = sampled
            pick = move
    return random.randrange(3) if pick < 0 else pick


@kernel
def _thompson(
    spec: np.ndarray, sel: int, e: int, f: np.ndarray, i: np.ndarray, kn: np.ndarray
) -> int:
    return _sample(spec, e, f, i, kn[spec[sel + c.R_K]], -1)


@kernel
def _keeper(
    spec: np.ndarray,
    sel: int,
    e: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    k: int,
    rn: int,
    opp: np.ndarray,
) -> int:
    """Score the experts' moves of the last round, if that round was valid (k
    valid rounds now, one more than then), keep this round's, then pick by the
    rule (EDGE draws the main expert's move only when it plays)."""
    kk = spec[sel + c.R_K]  # edge, decay, warmup, sharp
    rule = spec[sel + c.R_A]
    rec = spec[sel + c.R_F]  # the gated arm's record, then the main expert's
    at = spec[sel + c.R_I]
    if i[at + 1] == rn and k == i[at + 2] + 1:
        if i[at] >= 0:
            score_arm(c.SC_DIRICHLET, f, rec, i[at], opp[k - 1], kn, kk + 1)
        if rule != c.EDGE:
            score_arm(c.SC_DIRICHLET, f, rec + 3, i[at + 3], opp[k - 1], kn, kk + 1)
    gated = spec[e + c.E_NARMS] - 1
    move = i[spec[e + c.E_PEND_I] + 1 + gated]
    i[at] = move
    i[at + 1] = rn + 1
    i[at + 2] = k
    edge = kn[kk]
    warm = rn >= kn[kk + 2]
    sharp = kn[kk + 3]
    if rule == c.EDGE:
        if move >= 0 and warm and value(c.SC_DIRICHLET, f, rec) > edge:
            return move
        return _sample(spec, e, f, i, sharp, gated)
    main = _sample(spec, e, f, i, sharp, gated)
    i[at + 3] = main
    if move < 0:
        return main
    if rule == c.ANTI_FIRST or rule == c.ANTI_FIRST_HOLD:
        lead = value(c.SC_DIRICHLET, f, rec + 3) - value(c.SC_DIRICHLET, f, rec)
        held = rule == c.ANTI_FIRST_HOLD and i[at + 4] == 1 and lead >= -edge
        on_main = warm and (lead > edge or held)
        i[at + 4] = 1 if on_main else 0
        return main if on_main else move
    if rule == c.MAIN_FIRST:
        lead = value(c.SC_DIRICHLET, f, rec) - value(c.SC_DIRICHLET, f, rec + 3)
        held = i[at + 4] == 1 and lead >= -edge
        on_gated = warm and (lead > edge or held)
        i[at + 4] = 1 if on_gated else 0
        return move if on_gated else main
    return move if _draw(f, rec, sharp) > _draw(f, rec + 3, sharp) else main


@kernel
def _leader(
    spec: np.ndarray,
    sel: int,
    e: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    k: int,
    rn: int,
    opp: np.ndarray,
) -> int:
    """The LEADER rule over the main expert (0) and the last K arms (1 .. K):
    score every expert's move of the last round if it was valid, keep this
    round's, then from round `warmup` on move to the best-scored expert once its
    record leads the current expert's by more than `edge`. LEADER_PRIORITY: from
    a gated expert, only the main expert or the last gated one can take over."""
    kk = spec[sel + c.R_K]  # edge, decay, warmup, sharp
    n_gated = spec[sel + c.R_B]
    rec = spec[sel + c.R_F]  # expert j's record at rec + 3 j
    at = spec[sel + c.R_I]  # [round + 1, k, current expert, each expert's move]
    if i[at] == rn and k == i[at + 1] + 1:
        for j in range(n_gated + 1):
            move = i[at + 3 + j]
            if move >= 0:
                score_arm(c.SC_DIRICHLET, f, rec + 3 * j, move, opp[k - 1], kn, kk + 1)
    first = spec[e + c.E_NARMS] - n_gated
    pend = spec[e + c.E_PEND_I]
    main = _sample_but(spec, e, f, i, kn[kk + 3], first, first + n_gated)
    i[at] = rn + 1
    i[at + 1] = k
    i[at + 3] = main
    for j in range(1, n_gated + 1):
        i[at + 3 + j] = i[pend + first + j]
    current = i[at + 2]
    open_to_all = spec[sel + c.R_A] == c.LEADER or current == 0
    if rn >= kn[kk + 2]:
        best = current
        for j in range(n_gated + 1):
            allowed = open_to_all or j == 0 or j == n_gated
            if (
                allowed
                and i[at + 3 + j] >= 0
                and value(c.SC_DIRICHLET, f, rec + 3 * j)
                > value(c.SC_DIRICHLET, f, rec + 3 * best)
            ):
                best = j
        lead = value(c.SC_DIRICHLET, f, rec + 3 * best) - value(
            c.SC_DIRICHLET, f, rec + 3 * current
        )
        if lead > kn[kk]:
            current = best
    i[at + 2] = current
    move = i[at + 3 + current]
    return move if move >= 0 else main


@kernel
def _vote(
    spec: np.ndarray, sel: int, e: int, f: np.ndarray, i: np.ndarray, kn: np.ndarray
) -> int:
    pend = spec[e + c.E_PEND_I]
    n_arms = spec[e + c.E_NARMS]
    scorer = spec[e + c.E_SCORER]
    score_f = spec[e + c.E_SCORE_F]
    has_random = spec[e + c.E_RANDOM] != c.RA_NONE
    temperature = max(kn[spec[sel + c.R_K]], 1e-6)
    top = -math.inf
    for a in range(n_arms):
        if i[pend + 1 + a] >= 0:
            top = max(top, value(scorer, f, score_f + 3 * a))
    if has_random:
        top = max(top, _random_value(spec, e, f, i))
    if top == -math.inf:
        return random.randrange(3)
    weights = np.zeros(3)
    for a in range(n_arms):
        move = i[pend + 1 + a]
        if move >= 0:
            v = value(scorer, f, score_f + 3 * a)
            weights[move] += math.exp((v - top) / temperature)
    if has_random:
        share = math.exp((_random_value(spec, e, f, i) - top) / temperature) / 3.0
        for m in range(3):
            weights[m] += share
    u = random.random() * (weights[0] + weights[1] + weights[2])
    if u < weights[0]:
        return 0
    return 1 if u < weights[0] + weights[1] else 2


@kernel
def choose(
    spec: np.ndarray,
    sel: int,
    e: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    k: int,
    rn: int,
    opp: np.ndarray,
) -> int:
    """The move selector record `sel` picks from ensemble `e`'s pending arms for
    raw round rn, after k valid rounds of the opponent's valid-only history."""
    kind = spec[sel + c.R_KIND]
    if kind == c.SEL_KEEPER:
        if spec[sel + c.R_A] == c.LEADER or spec[sel + c.R_A] == c.LEADER_PRIORITY:
            return _leader(spec, sel, e, f, i, kn, k, rn, opp)
        return _keeper(spec, sel, e, f, i, kn, k, rn, opp)
    if kind == c.SEL_FIRST:
        return _first(spec, sel, e, i)
    if kind == c.SEL_GREEDY:
        return _greedy(spec, sel, e, f, i)
    if kind == c.SEL_THOMPSON:
        return _thompson(spec, sel, e, f, i, kn)
    return _vote(spec, sel, e, f, i, kn)
