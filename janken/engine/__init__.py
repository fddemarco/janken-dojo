"""The match engine: bot files in, MatchResults out, all compiled with numba.

    play_pairs([(spec_a, spec_b), ...], rounds, seeds) -> [MatchResult, ...]

A spec (janken/spec.py) is a bot file, parameter overrides and a result label.
build.py compiles the bots into one engine module, whose kernel (kernel.py)
referees every match in parallel, and result.py turns the raw moves into MatchResults.
"""

import os
import threading
from collections.abc import Callable, Iterator, Sequence

import numba
import numpy as np
from numba.np.ufunc import parallel

from .. import telemetry
from ..match import MatchResult
from .build import compile_bots
from .registry import param_vector
from .result import match_result


def _ignore(done: list[tuple[int, MatchResult]]) -> None:
    """The default `on_done`: nothing to do with finished matches."""


def dealt(costs: Sequence[float], threads: int) -> list[int]:
    """An order of the matches that spreads their cost evenly over `threads`
    equal, contiguous chunks (how numba's prange splits a loop): heaviest first,
    dealt round robin, so no chunk holds every heavy match."""
    heavy_first = sorted(range(len(costs)), key=lambda k: -costs[k])
    return [k for t in range(threads) for k in heavy_first[t::threads]]


def play_pairs(
    pairs: Sequence,
    rounds: int,
    seeds: Sequence[int],
    workers: int | None = None,
    on_done: Callable[[list[tuple[int, MatchResult]]], None] = _ignore,
    flush_s: float = 0.0,
) -> list[MatchResult]:
    """Play [(spec_a, spec_b), ...], match k seeded with seeds[k]; results in order.

    While the batch plays, every `flush_s` seconds (config `execution.flush_s`)
    `on_done` gets the matches finished since the last call, as (k, result): a
    slow match is reported soon after it ends, fast ones together. 0 reports
    them all once, at the end. A match depends only on its seed, so the order
    they are played in (dealt over the cores by cost) never changes a result."""
    if not pairs:
        return []
    with telemetry.span("engine.compile"):
        bots = compile_bots([s.path for pair in pairs for s in pair])
    threads = min(workers, parallel.NUM_THREADS) if workers else parallel.NUM_THREADS
    vectors = {}

    def vector(spec):
        key = (spec.path, spec.label)
        if key not in vectors:
            vectors[key] = param_vector(spec.path, spec.params)
        return vectors[key]

    def path(spec) -> str:
        return os.path.normpath(spec.path)

    costs = [bots.costs[path(a)] + bots.costs[path(b)] for a, b in pairs]
    order = dealt(costs, threads)
    played = [pairs[k] for k in order]
    codes_a = np.array([bots.codes[path(a)] for a, _ in played], np.int64)
    codes_b = np.array([bots.codes[path(b)] for _, b in played], np.int64)
    prm_a = np.array([vector(a) for a, _ in played])
    prm_b = np.array([vector(b) for _, b in played])
    batch_seeds = np.array([seeds[k] for k in order], np.int64)
    out = np.empty((len(pairs), rounds, 2), np.int8)
    status = np.zeros((len(pairs), 3), np.int64)
    done = np.zeros(len(pairs), np.int8)
    results: list[MatchResult | None] = [None] * len(pairs)
    failed: list[BaseException] = []

    def run() -> None:
        try:
            numba.set_num_threads(threads)  # per thread: set it in the one playing
            bots.play_batch(
                codes_a, codes_b, prm_a, prm_b, rounds, batch_seeds, out, status, done
            )
        except BaseException as exc:  # raised again in the caller's thread
            failed.append(exc)

    def flush() -> None:
        # done[j] is written after the match's moves and status, and x86 keeps
        # stores in order, so a match flagged done is complete. Read a snapshot:
        # numpy's nonzero counts, then fills, and raises if the engine's threads
        # flag another match in between.
        fresh = []
        for j in np.flatnonzero(done.copy()).tolist():
            k = order[j]
            if results[k] is None:
                a, b = pairs[k]
                results[k] = match_result(a.label, b.label, out[j], status[j])
                fresh.append((k, results[k]))
        if fresh:
            on_done(sorted(fresh, key=lambda kr: kr[0]))

    with telemetry.span("engine.play", matches=len(pairs), rounds=rounds):
        player = threading.Thread(target=run, name="janken-engine", daemon=True)
        player.start()
        while player.is_alive():
            player.join(flush_s or None)
            if player.is_alive():
                flush()
    if failed:
        raise failed[0]
    flush()
    return [r for r in results if r is not None]


def play_in_batches(
    pairs: Sequence,
    rounds: int,
    seeds: Sequence[int],
    size: int,
    workers: int | None = None,
) -> Iterator[tuple[range, list[MatchResult]]]:
    """`play_pairs`, `size` matches at a time: yields (indices, their results).

    Every match keeps its own seed, so the results don't depend on `size`; the
    engine is compiled once per process, so later batches start at once."""
    for start in range(0, len(pairs), size):
        span = range(start, min(start + size, len(pairs)))
        yield (
            span,
            play_pairs(
                pairs[span.start : span.stop],
                rounds,
                seeds[span.start : span.stop],
                workers,
            ),
        )
