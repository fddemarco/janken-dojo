"""The bot pipeline, compiled: one blueprint (janken/kit/blueprint/), one round.

    guards -> valid-only view -> track -> signals -> arms -> select -> overlays

Every bot's `step` is `pipeline.play(f, i, prm, my, opp, n, SPEC, KNOBS)`.

Each round arrives once: its invalid moves are counted, and a valid round is
appended to the valid-only history and to the bot's match indexes (matching.py),
all in the bot's per-match workspace, so no stage rescans the whole history.
"""

import numpy as np

from . import bayes, ensemble, guards, matching, oracle, overlays, replay, selectors
from . import codes as c
from .jit import kernel
from .moves import INVALID, scan_invalid


@kernel
def resolve_knobs(
    spec: np.ndarray, f: np.ndarray, prm: np.ndarray, knobs: np.ndarray
) -> np.ndarray:
    """The knob values this match (bound ones from prm), kept in f; returns them."""
    at = spec[c.H_KNOB_F]
    count = spec[c.H_NKNOB]
    binds = spec[c.H_BIND_AT]
    for j in range(count):
        b = spec[binds + j]
        f[at + j] = prm[b] if b >= 0 else knobs[j]
    return f[at : at + count]


@kernel
def oracle_play(
    f: np.ndarray,
    prm: np.ndarray,
    opp: int,
    level: int,
    spec: np.ndarray,
    knobs: np.ndarray,
) -> int:
    """A pure Oracle bot's move (janken/kit/oracle.py): no pipeline runs."""
    return oracle.pure_move(spec, resolve_knobs(spec, f, prm, knobs), opp, level)


@kernel
def valid_history(spec: np.ndarray, i: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The valid-only history kept in the per-match workspace: (my, opp) views,
    filled up to the valid rounds folded so far."""
    stride = i[spec[c.H_ROUNDS_I]]
    at_my = matching.slot_at(spec, i, c.VIEW_MY_SLOT)
    at_opp = matching.slot_at(spec, i, c.VIEW_OPP_SLOT)
    return i[at_my : at_my + stride], i[at_opp : at_opp + stride]


@kernel
def _fold(
    spec: np.ndarray,
    core: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    k: int,
    rk: int,
    my: np.ndarray,
    opp: np.ndarray,
) -> None:
    ensemble.fold(spec, core, f, i, kn, k, rk, my, opp)
    for s in range(spec[core + c.E_NSIG]):
        r = spec[core + c.E_SIG_AT] + s * c.REC
        if spec[r + c.R_KIND] == c.S_REPLAY:
            replay.fold(spec, r, f, i, kn, k, rk, my, opp)


@kernel
def _choose(
    spec: np.ndarray,
    core: int,
    f: np.ndarray,
    i: np.ndarray,
    kn: np.ndarray,
    n: int,
    rn: int,
    my: np.ndarray,
    opp: np.ndarray,
) -> int:
    symbols = ensemble.predictions(spec, core, f, i, kn, n, rn, my, opp)
    for s in range(spec[core + c.E_NSIG]):
        r = spec[core + c.E_SIG_AT] + s * c.REC
        if spec[r + c.R_KIND] == c.S_REPLAY:
            symbols[s] = replay.predict(spec, r, f, i, kn, n, rn, my, opp)
    bayes.combine(spec, core, f, symbols)
    ensemble.set_arms(spec, core, i, symbols, rn)
    pick = 0
    options = spec[c.H_NSEL]
    if options > 1:
        pick = min(max(int(kn[spec[c.H_SEL_K]]), 0), options - 1)
    return selectors.choose(
        spec, spec[c.H_SEL_AT] + pick * c.REC, core, f, i, kn, n, rn, opp
    )


@kernel
def play(
    f: np.ndarray,
    i: np.ndarray,
    prm: np.ndarray,
    my: np.ndarray,
    opp: np.ndarray,
    n: int,
    spec: np.ndarray,
    knobs: np.ndarray,
) -> int:
    """The move for round n, given my[:n] and opp[:n]."""
    kn = resolve_knobs(spec, f, prm, knobs)
    view = spec[c.H_VIEW_I]
    scan_invalid(view, i, my, opp, n)
    for g in range(spec[c.H_NGUARD]):
        move = guards.apply(spec, spec[c.H_GUARD_AT] + g * c.REC, i, kn, my, opp, n)
        if move != c.PASS:
            return move

    cursor = spec[c.H_CURSOR_I]
    core = spec[c.H_CORE]
    vm, vo = valid_history(spec, i)
    k = i[view]
    for rk in range(i[cursor], n):
        if my[rk] == INVALID or opp[rk] == INVALID:
            continue
        vm[k] = my[rk]
        vo[k] = opp[rk]
        for x in range(spec[c.H_NIDX]):
            matching.fold(spec, spec[c.H_IDX_AT] + x * c.IDX, i, k, vm, vo)
        _fold(spec, core, f, i, kn, k, rk, vm, vo)
        k += 1
    i[cursor] = n
    i[view] = k

    move = _choose(spec, core, f, i, kn, k, n, vm, vo)
    for o in range(spec[c.H_NOVER]):
        move = overlays.apply(
            spec, spec[c.H_OVER_AT] + o * c.REC, i, kn, move, my, opp, n
        )
    return move
