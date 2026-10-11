"""The match engine: bot files in, MatchResults out, all compiled with numba.

    play_pairs([(spec_a, spec_b), ...], rounds, seeds) -> [MatchResult, ...]

A spec (janken/spec.py) is a bot file, parameter overrides and a result label.
build.py compiles the bots into one engine module, whose kernel (kernel.py)
referees every match in parallel, and result.py turns the raw moves into MatchResults.
"""

import os
from collections.abc import Iterator, Sequence

import numba
import numpy as np
from numba.np.ufunc import parallel

from ..match import MatchResult
from .build import compile_bots
from .registry import param_vector
from .result import match_result


def play_pairs(
    pairs: Sequence, rounds: int, seeds: Sequence[int], workers: int | None = None
) -> list[MatchResult]:
    """Play [(spec_a, spec_b), ...], match k seeded with seeds[k]; results in order."""
    if not pairs:
        return []
    if workers:
        numba.set_num_threads(min(workers, parallel.NUM_THREADS))
    bots = compile_bots([s.path for pair in pairs for s in pair])
    vectors = {}

    def vector(spec):
        key = (spec.path, spec.label)
        if key not in vectors:
            vectors[key] = param_vector(spec.path, spec.params)
        return vectors[key]

    codes_a = np.array(
        [bots.codes[os.path.normpath(a.path)] for a, _ in pairs], np.int64
    )
    codes_b = np.array(
        [bots.codes[os.path.normpath(b.path)] for _, b in pairs], np.int64
    )
    prm_a = np.array([vector(a) for a, _ in pairs])
    prm_b = np.array([vector(b) for _, b in pairs])
    out, status = bots.play_batch(
        codes_a, codes_b, prm_a, prm_b, rounds, np.array(seeds, np.int64)
    )
    return [
        match_result(a.label, b.label, out[k], status[k])
        for k, (a, b) in enumerate(pairs)
    ]


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
