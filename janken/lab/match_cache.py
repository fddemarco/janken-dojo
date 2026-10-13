"""A cache of played matches: a match already played is read back, not replayed.

A match depends only on what plays it (janken/engine/kernel.py): the two bots'
code and parameters, its seed and its rounds. Many lab steps replay matches they
or another step already played:

    tuning      every study plays the same pools and seeds (tuning.seed), so the
                defaults' matches, and the support bots', recur
    gauntlets   seeds 1..N against the same opponents, in every log
    species     the incumbent's matches vs the pool, in every paired run

So every match played through `MatchCache.play` is kept in the runs database
(table match_cache), keyed by a hash of what decides it:

    each bot's source hash (library.source_hash: its file and every bot it
    names), its parameter overrides, the seed, the rounds, and the kit and
    engine's code (_numba_cache.digest)

and a later match with the same key is read back. Editing a bot (or one it
names) or the kit changes the key, so a stale match is never read. The cache is
on by default (runs.match_cache); it only ever skips work, never changes a result.
"""

import dataclasses
import functools
import hashlib
import json
from collections.abc import Callable, Sequence

from .. import _numba_cache, library
from ..engine import play_pairs
from ..match import MatchResult
from ..spec import BotSpec
from .runs_db import RunStore

Done = Callable[[list[tuple[int, MatchResult]]], None]


@functools.cache
def _code() -> str:
    """The kit and engine's digest: what this process plays with."""
    return _numba_cache.digest()


def _ignore(done: list[tuple[int, MatchResult]]) -> None:
    """The default `on_done`: nothing to do with finished matches."""


def match_key(
    a: BotSpec, b: BotSpec, seed: int, rounds: int, hashes: dict[str, str], code: str
) -> str:
    """What decides a match, hashed (`hashes`: source hashes by path, filled in
    as they are first needed; `code`: the kit and engine's digest)."""
    for path in (a.path, b.path):
        if path not in hashes:
            hashes[path] = library.source_hash(path)
    blob = json.dumps(
        [hashes[a.path], a.params, hashes[b.path], b.params, seed, rounds, code],
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(blob.encode()).hexdigest()


def _result(a: BotSpec, b: BotSpec, row: dict[str, object]) -> MatchResult:
    def text(name: str) -> str | None:
        value = row[name]
        return None if value is None else str(value)  # None: a column's NULL

    return MatchResult(
        bot_a=a.label,
        bot_b=b.label,
        wins_a=int(str(row["wins_a"])),
        wins_b=int(str(row["wins_b"])),
        draws=int(str(row["draws"])),
        forfeit_a=text("forfeit_a"),
        forfeit_b=text("forfeit_b"),
        moves=str(row["moves"]),
    )


def _row(key: str, m: MatchResult) -> dict[str, object]:
    return {
        "key": key,
        "wins_a": m.wins_a,
        "wins_b": m.wins_b,
        "draws": m.draws,
        "forfeit_a": m.forfeit_a,
        "forfeit_b": m.forfeit_b,
        "moves": m.moves,
    }


@dataclasses.dataclass(frozen=True)
class MatchCache:
    """Matches kept in `store`; `enabled` False plays every match (and keeps none)."""

    store: RunStore
    enabled: bool

    def play(
        self,
        pairs: Sequence[tuple[BotSpec, BotSpec]],
        rounds: int,
        seeds: Sequence[int],
        workers: int | None = None,
        on_done: Done = _ignore,
        flush_s: float = 0.0,
    ) -> list[MatchResult]:
        """`engine.play_pairs`, reading back every match already played: those
        reach `on_done` first, at once; the rest as they are played, and kept."""
        if not self.enabled:
            return play_pairs(pairs, rounds, seeds, workers, on_done, flush_s)
        hashes: dict[str, str] = {}
        code = _code()
        keys = [
            match_key(a, b, s, rounds, hashes, code)
            for (a, b), s in zip(pairs, seeds, strict=True)
        ]
        found = self.store.cached(keys)
        results: list[MatchResult | None] = [None] * len(pairs)
        hits: list[tuple[int, MatchResult]] = []
        for k, ((a, b), key) in enumerate(zip(pairs, keys, strict=True)):
            if key in found:
                hit = _result(a, b, found[key])
                results[k] = hit
                hits.append((k, hit))
        if hits:
            on_done(hits)
        todo = [k for k, r in enumerate(results) if r is None]

        def keep(finished: list[tuple[int, MatchResult]]) -> None:
            played = [(todo[j], m) for j, m in finished]
            self.store.cache([_row(keys[k], m) for k, m in played])
            for k, m in played:
                results[k] = m
            on_done(played)

        play_pairs(
            [pairs[k] for k in todo],
            rounds,
            [seeds[k] for k in todo],
            workers,
            keep,
            flush_s,
        )
        return [r for r in results if r is not None]
