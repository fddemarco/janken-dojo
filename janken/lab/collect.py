"""Grow the move dataset: play a round robin and append every round to it.

    uv run janken lab dataset add bots/ [bots/x.yaml:NAME=value ...] --matches 2

Every pair of the given bots plays `matches_per_pair` matches. Each match draws
its seed and its holdout key from one stream seeded by the batch seed (recorded
with every match), so a batch is reproducible. A batch is committed in chunks of
`[tool.janken.dataset] batch_matches`, each its own transaction, under one batch
id.
"""

import datetime
import itertools
import os
import random
import sys
from collections.abc import Sequence

from .. import _numba_cache, progress, settings
from ..engine import play_in_batches, play_pairs
from ..engine.registry import discover
from ..spec import BotSpec, make_spec, parse_spec
from . import dataset


def expand(entries: Sequence[str]) -> list[BotSpec]:
    """Bot specs from directories (each bot in it, at its defaults) and specs
    (`bots/x.yaml` or `bots/x.yaml:NAME=value,...`), in order, without repeats.

    Raises:
        ValueError: a spec is malformed, or two entries share a label.
    """
    specs: list[BotSpec] = []
    for entry in entries:
        if os.path.isdir(entry):
            specs += [make_spec(p) for p in discover(entry)]
        else:
            specs.append(parse_spec(entry))
    unique = list(dict.fromkeys(specs))
    labels = [s.label for s in unique]
    clashes = sorted({x for x in labels if labels.count(x) > 1})
    if clashes:
        raise ValueError(f"two different bots share the label(s) {', '.join(clashes)}")
    return unique


def draw(
    specs: Sequence[BotSpec], matches_per_pair: int, seed: int
) -> tuple[list[tuple[BotSpec, BotSpec]], list[int], list[float]]:
    """The round robin's pairs, and each match's seed and holdout key, all drawn up
    front from the batch seed (so chunking a batch never changes it)."""
    if len(specs) < 2:
        raise ValueError(f"a round robin needs at least 2 bots, got {len(specs)}")
    rng = random.Random(seed)
    pairs = [
        pair
        for pair in itertools.combinations(specs, 2)
        for _ in range(matches_per_pair)
    ]
    # 32 bits: numba seeds its generator from the low 32 bits only.
    seeds = [rng.getrandbits(32) for _ in pairs]
    keys = [rng.random() for _ in pairs]
    return pairs, seeds, keys


def _batch(
    played: Sequence[dataset.PlayedMatch],
    rounds: int,
    seed: int,
    command: Sequence[str],
    played_at: datetime.datetime,
) -> dataset.Batch:
    return dataset.Batch(
        matches=played,
        rounds=rounds,
        seed=seed,
        library=_numba_cache.digest(),
        git=dataset.GitInfo.current(),
        command=command,
        played_at=played_at,
    )


def play_batch(
    specs: Sequence[BotSpec],
    rounds: int,
    matches_per_pair: int,
    seed: int,
    workers: int,
    command: Sequence[str],
) -> dataset.Batch:
    """Play the round robin of `specs` in one go (`workers` 0: numba's default)."""
    pairs, seeds, keys = draw(specs, matches_per_pair, seed)
    played_at = datetime.datetime.now().replace(microsecond=0)
    results = play_pairs(pairs, rounds, seeds, workers or None)
    return _batch(
        [
            dataset.PlayedMatch(p1=a, p2=b, seed=s, holdout_key=k, result=r)
            for (a, b), s, k, r in zip(pairs, seeds, keys, results)
        ],
        rounds,
        seed,
        command,
        played_at,
    )


def grow(
    path: str,
    specs: Sequence[BotSpec],
    rounds: int,
    matches_per_pair: int,
    seed: int,
    workers: int,
    chunk: int = settings.config().dataset.batch_matches,
) -> range:
    """Play a batch and append it to the dataset at `path`, `chunk` matches per
    transaction under one batch id; returns its match ids.

    An interrupted batch keeps the chunks it committed: a prefix of the batch."""
    pairs, seeds, keys = draw(specs, matches_per_pair, seed)
    print(
        f"dataset: {len(specs)} bots, {len(pairs)} matches"
        f" ({matches_per_pair} per pair) of {rounds} rounds (seed {seed}) -> {path}",
        file=sys.stderr,
    )
    played_at = datetime.datetime.now().replace(microsecond=0)
    batch_id = -1  # allocated by the first chunk
    stored = range(0)
    with progress.bar(len(pairs), "compiling", "match") as bar:
        for span, results in play_in_batches(
            pairs, rounds, seeds, chunk, workers or None
        ):
            played = [
                dataset.PlayedMatch(
                    p1=pairs[i][0],
                    p2=pairs[i][1],
                    seed=seeds[i],
                    holdout_key=keys[i],
                    result=r,
                )
                for i, r in zip(span, results)
            ]
            con = dataset.connect(path, read_only=False)
            try:
                if batch_id < 0:
                    batch_id = dataset.next_batch_id(con)
                ids = dataset.append_to(
                    con, _batch(played, rounds, seed, sys.argv, played_at), batch_id
                )
            finally:
                con.close()
            stored = range(stored.start if stored else ids.start, ids.stop)
            bar.set_description(f"batch {batch_id}")
            bar.set_postfix(stored=len(stored))
            bar.update(len(results))
    return stored
