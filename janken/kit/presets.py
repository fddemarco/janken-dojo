"""Blueprint pieces shared by bot families.

metabot(...)     smartbot's core: 18 cheap opponent models x 3 rotations, a
                 Dirichlet per arm, Thompson sampling, a scored random arm
                 (the Kaggle RPS 1st-place recipe, rps_kaggle §2)
iocaine(...)     Iocaine Powder's sicilian reasoning over three predictors
rps4(...)        rpscontest #4: joint-context tables of both players, greedy
staller()        word2janken's predictor, its counter and counter-counter,
                 on a scoreboard
sims(n)          the first n "model of us" signals: zoo bots replayed from
                 the opponent's side (experiments 0003-0005)
"""

import dataclasses

from . import codes as c
from .blueprint import (
    ALL_ROTATIONS,
    Backoff,
    DecayedNet,
    Dirichlet,
    Ensemble,
    Frequency,
    Geometry,
    LongestMatch,
    NGram,
    Relative,
    Replay,
    SignalLike,
    Sim,
    Value,
)


def metabot_signals(table_decay: Value, max_match: Value) -> tuple[SignalLike, ...]:
    """smartbot's 18 opponent models: frequencies, n-grams over three histories,
    history matches, rotation models."""
    return (
        Frequency(c.OPP, 1.0),
        Frequency(c.OPP, 0.9),
        *(NGram(o, ctx=c.OPP, decay=table_decay) for o in (1, 2, 3, 4)),
        *(NGram(o, ctx=c.JOINT, decay=table_decay) for o in (1, 2, 3)),
        *(NGram(o, ctx=c.MY, decay=table_decay) for o in (1, 2, 3)),
        LongestMatch(max_match, ctx=c.OPP),
        LongestMatch(max_match, ctx=c.JOINT),
        LongestMatch(max_match, ctx=c.MY),
        Relative(c.OPP, decay=table_decay),
        Relative(c.OPP, by_outcome=True, decay=table_decay),
        Relative(c.MY, decay=table_decay),
    )


def metabot(arm_decay: Value, table_decay: Value, max_match: Value) -> Ensemble:
    """smartbot's core; pair it with the Thompson selector."""
    return Ensemble(
        metabot_signals(table_decay, max_match),
        ALL_ROTATIONS,
        Dirichlet(arm_decay),
        c.RA_SCORED,
    )


def iocaine(decay: Value, max_len: Value) -> Ensemble:
    """The opponent's most frequent move, and the opponent's and our move after the
    longest joint match, each x 3 rotations, on decayed net scores."""
    return Ensemble(
        (
            Frequency(c.OPP),
            LongestMatch(max_len, ctx=c.JOINT, of=c.OPP),
            LongestMatch(max_len, ctx=c.JOINT, of=c.MY),
        ),
        ALL_ROTATIONS,
        DecayedNet(decay),
    )


def rps4(decay: Value, table_decay: Value) -> Ensemble:
    """Order 0..3 joint-context tables of both players' next moves, x 3 rotations,
    on decayed net scores, with the random arm pinned at 0."""
    tables = tuple(
        NGram(o, ctx=c.JOINT, of=of, decay=table_decay)
        for o in range(4)
        for of in (c.OPP, c.MY)
    )
    return Ensemble(tables, ALL_ROTATIONS, DecayedNet(decay), c.RA_PINNED)


def staller() -> Ensemble:
    """word2janken's predictor played straight, countered and counter-countered, on
    a plain scoreboard, random while nothing is ahead."""
    return Ensemble(
        (Backoff(3, ctx=c.JOINT),),
        (c.BEAT, c.BEAT_BEAT, c.COPY),
        DecayedNet(1.0),
        c.RA_PINNED,
    )


def _replayed(core: Ensemble) -> Replay:
    """A replay of `core`; its random arm can't be its best guess, so it goes."""
    return Replay(dataclasses.replace(core, random_arm=c.RA_NONE))


SIMS: tuple[SignalLike, ...] = (
    Sim(Backoff(3, ctx=c.JOINT)),  # word2janken
    Sim(LongestMatch(10, ctx=c.JOINT)),  # pattern_memory
    Sim(NGram(2, ctx=c.JOINT)),  # markov2_joint
    _replayed(iocaine(0.9, 12)),  # iocaine_lite
    Sim(NGram(1, ctx=c.OPP, decay=0.95)),  # transition_matrix
    Replay(rps4(0.85, 1.0)),  # rps4_lite
    Replay(staller()),  # word2janken_scoreboard
    Sim(Geometry(0.05, 20, sample=False)),  # geometry, its most likely move
    _replayed(metabot(0.95, 0.9, 12)),  # smartbot
    _replayed(metabot(0.6, 0.6, 8)),  # smartbot_fast
)


def sims(n: int) -> tuple[SignalLike, ...]:
    """The first n model-of-us signals (5: smartbot_sims, 8: _sims2, 10: _sims3)."""
    return SIMS[:n]


def smartbot_sims(
    n: int, arm_decay: Value, table_decay: Value, max_match: Value
) -> Ensemble:
    """smartbot's core plus the first n sims."""
    core = metabot(arm_decay, table_decay, max_match)
    return dataclasses.replace(core, signals=core.signals + sims(n))
