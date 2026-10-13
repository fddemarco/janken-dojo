"""Experiments: candidates against randomly drawn pools, stored for analysis.

Each round robin `rr` draws a fresh pool of `pool_size` bots (from
`seed` and `rr`, so a run is reproducible), then plays one match per pair:

  mode "full"        every pair of pool + candidates (a true round robin)
  mode "candidates"  only the pairs with a candidate in them (the tuner's
                     cheap mode: every bot enters fresh, so pool-vs-pool
                     matches can't change a candidate's rating)

Pools and match seeds depend only on (seed, rr, the candidates' stems), never
on their parameters, so two variants of one bot run on identical schedules.
Within a round robin, every candidate meets a given pool bot with the *same*
match seed. Each side draws from its own stream of that seed (engine/kernel.py),
so the pool bot draws the same whoever it meets, two candidates that behave
identically get identical matches, and a real
difference between them isn't drowned in seed noise: common random numbers,
which is what makes paired comparisons and tuning sharp.

A run is stored in the runs database (runs_db.py) before it plays, and its
matches are committed as they end (every `execution.flush_s` seconds, so a slow
L4 vs L5 match shows up soon after it's played). An interrupted run keeps them,
and `resume_experiment` plays the rest of the same schedule. Round robin k's pool and
seeds depend only on k, never on how many the run plays, so `resume_experiment`
can also grow a run (1 --> 3 --> 5 ... round robins): the grown run equals one
planned at its new size.
"""

import collections
import itertools
import random
import sys
import time
from collections.abc import Callable, Collection, Sequence

from .. import _numba_cache, library, progress, settings, telemetry
from ..match import MatchResult, bot_name
from ..spec import BotSpec, make_spec, to_dict
from . import store
from .match_cache import MatchCache
from .pool import sample_pool, vary
from .runs_db import COMPLETE, INTERRUPTED, RUNNING, RunStore

MODES = ("full", "candidates")


def build_schedule(
    candidates: Sequence[BotSpec],
    bots_dir: str,
    pool_size: int,
    round_robins: int,
    seed: int,
    mode: str = "full",
    allow_small: bool = False,
    use_mocks: bool = False,
    variants: float = 0.0,
    spaces_dir: str = "",
):
    """[{rr, pool: [BotSpec], pairs: [(BotSpec, BotSpec)], seeds: [int]}, ...]

    With `variants`, that share of each pool's members play a variant drawn
    from their space file (pool.vary), from a stream of their own: the pool's
    bots and the match seeds stay those of the same run without variants."""
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    labels = [c.label for c in candidates]
    if len(set(labels)) != len(labels):
        raise SystemExit(
            f"candidates must differ: duplicate label(s) {sorted({x for x in labels if labels.count(x) > 1})}"
        )
    stems = sorted({c.stem for c in candidates})
    schedule = []
    for rr in range(round_robins):
        rng = random.Random("{}:{}:{:d}".format(seed, ",".join(stems), rr))
        pool = sample_pool(
            bots_dir,
            pool_size,
            rng,
            exclude_stems=stems,
            allow_small=allow_small,
            use_mocks=use_mocks,
        )
        if variants > 0:
            key = "{}:{}:{:d}:variants".format(seed, ",".join(stems), rr)
            pool = vary(pool, spaces_dir, variants, random.Random(key))
        opp_seed = {p.label: rng.getrandbits(32) for p in pool}
        pairs = list(itertools.combinations(candidates, 2))
        pairs += [(c, p) for c in candidates for p in pool]
        seeds = [
            rng.getrandbits(32) for _ in range(len(pairs) - len(candidates) * len(pool))
        ]
        seeds += [opp_seed[p.label] for c in candidates for p in pool]
        if mode == "full":
            pool_pairs = list(itertools.combinations(pool, 2))
            pairs += pool_pairs
            seeds += [rng.getrandbits(32) for _ in pool_pairs]
        schedule.append({"rr": rr, "pool": pool, "pairs": pairs, "seeds": seeds})
    return schedule


def _no_hook(rr: int) -> None:
    """The default `on_batch`: nothing to do after a round robin is stored."""


def match_row(
    rr: int,
    k: int,
    pair: tuple[BotSpec, BotSpec],
    seed: int,
    m: MatchResult,
    rounds: int,
    run_id: str,
    candidates: set[str],
) -> dict[str, object]:
    """Match k of round robin `rr` as a row (runs_db.MATCH_SCHEMA)."""
    a, b = pair
    return {
        "run_id": run_id,
        "rounds": rounds,
        "rr": rr,
        "k": k,
        "bot_a": a.label,
        "bot_b": b.label,
        "stem_a": a.stem,
        "stem_b": b.stem,
        "cand_a": a.label in candidates,
        "cand_b": b.label in candidates,
        "seed": seed,
        "wins_a": m.wins_a,
        "wins_b": m.wins_b,
        "draws": m.draws,
        "forfeit_a": m.forfeit_a,
        "forfeit_b": m.forfeit_b,
        "moves": m.moves,
    }


def match_rows(
    rr: int,
    pairs: Sequence[tuple[BotSpec, BotSpec]],
    seeds: Sequence[int],
    results: Sequence[MatchResult],
    rounds: int,
    run_id: str,
    candidates: set[str],
) -> list[dict[str, object]]:
    """One row per match of round robin `rr` (runs_db.MATCH_SCHEMA)."""
    return [
        match_row(rr, k, pair, seed, m, rounds, run_id, candidates)
        for k, (pair, seed, m) in enumerate(zip(pairs, seeds, results))
    ]


def play_into(
    runs: RunStore,
    run_id: str,
    schedule: Sequence[dict],
    rounds: int,
    workers: int | None,
    candidates: Sequence[BotSpec],
    on_batch: Callable[[int], None] = _no_hook,
    flush_s: float = 0.0,
    played: Collection[tuple[int, int]] = frozenset(),
    cache: bool = False,
) -> float:
    """Play `schedule` into run `run_id` but the matches already `played` (as
    (rr, k)); returns the seconds spent.

    Every round robin plays in one batch, so the cores stay busy, and matches are
    committed as they end, every `flush_s` seconds (0: once, at the end): an
    interrupted run keeps every finished match. `on_batch(rr)` runs once a
    round robin's matches are all stored. With `cache`, a match already played
    (match_cache.py) is read back instead.

    The run ends `complete`; if anything stops it (Ctrl-C included) it ends
    `interrupted`, keeping every match committed so far, and the error goes on.
    """
    labels = {c.label for c in candidates}
    started = time.perf_counter()
    todo = [
        (rr, k)
        for rr in schedule
        for k in range(len(rr["pairs"]))
        if (rr["rr"], k) not in played
    ]
    left = collections.Counter(rr["rr"] for rr, _ in todo)
    try:
        with progress.bar(len(todo), "playing", "match") as bar:

            def store(finished: list[tuple[int, MatchResult]]) -> None:
                rows = []
                for j, m in finished:
                    rr, k = todo[j]
                    pair, seed = rr["pairs"][k], rr["seeds"][k]
                    rows.append(
                        match_row(rr["rr"], k, pair, seed, m, rounds, run_id, labels)
                    )
                runs.append_matches(rows)
                bar.update(len(finished))
                for j, _ in finished:
                    number = todo[j][0]["rr"]
                    left[number] -= 1
                    if not left[number]:
                        on_batch(number)

            with telemetry.span("experiment.play", matches=len(todo)):
                MatchCache(runs, cache).play(
                    [rr["pairs"][k] for rr, k in todo],
                    rounds,
                    [rr["seeds"][k] for rr, k in todo],
                    workers,
                    store,
                    flush_s,
                )
    except BaseException:
        elapsed = time.perf_counter() - started
        runs.finish(run_id, INTERRUPTED, elapsed)
        progress.log(
            f"run {run_id} interrupted; its finished matches are stored."
            f" Resume with: janken lab resume {run_id} (or janken evaluate --note NNNN)"
        )
        raise
    elapsed = time.perf_counter() - started
    runs.finish(run_id, COMPLETE, elapsed)
    return elapsed


def run_experiment(
    candidates: list[BotSpec],
    bots_dir: str,
    pool_size: int,
    rounds: int,
    round_robins: int,
    seed: int,
    mode: str = "full",
    name: str | None = None,
    workers: int | None = None,
    allow_small: bool = False,
    use_mocks: bool = False,
    variants: float = 0.0,
    spaces_dir: str = "",
    root: str | None = None,
    extra: dict | None = None,
    on_batch: Callable[[int], None] = _no_hook,
    on_start: Callable[[str], None] = lambda run_id: None,
    flush_s: float = 0.0,
    cache: bool = False,
) -> str:
    """Play and store one experiment, matches stored as they end (every
    `flush_s` seconds); returns its run id.

    `on_start` gets the run id once the run is stored, before it plays."""
    if not candidates:
        raise SystemExit("an experiment needs at least one candidate bot")
    if seed == settings.RANDOM_SEED:
        seed = random.SystemRandom().getrandbits(32)
    schedule = build_schedule(
        candidates,
        bots_dir,
        pool_size,
        round_robins,
        seed,
        mode,
        allow_small,
        use_mocks,
        variants,
        spaces_dir,
    )
    n = sum(len(rr["pairs"]) for rr in schedule)
    manifest = {
        "run_id": "",
        "name": name,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "git": store.git_info(),
        "library": _numba_cache.digest(),
        "command": sys.argv,
        "config": {
            "bots_dir": bots_dir,
            "pool_size": len(schedule[0]["pool"]),
            "rounds": rounds,
            "round_robins": round_robins,
            "seed": seed,
            "mode": mode,
            "allow_small": allow_small,
            "mocks": use_mocks,
            "variants": variants,
            "spaces_dir": spaces_dir,
        },
        "candidates": [to_dict(c) for c in candidates],
        "pools": [[p.label for p in rr["pool"]] for rr in schedule],
        "bots": used_bots(schedule),
        "n_matches": n,
        **(extra or {}),
    }
    runs = RunStore.at(root or "")
    run_id = runs.create_run(name or "+".join(c.label for c in candidates), manifest)
    print(
        f"experiment {run_id}: {len(candidates)} candidate(s) x {round_robins}"
        f" round robin(s) of {len(schedule[0]['pool'])}-bot pools,"
        f" {n} matches of {rounds} rounds (seed {seed})",
        file=sys.stderr,
    )
    on_start(run_id)
    elapsed = play_into(
        runs,
        run_id,
        schedule,
        rounds,
        workers,
        candidates,
        on_batch,
        flush_s,
        (),
        cache,
    )
    print(f"played {n} matches in {elapsed:.1f}s -> run {run_id}", file=sys.stderr)
    return run_id


def resume_experiment(
    ref: str,
    root: str = "",
    workers: int | None = None,
    on_batch: Callable[[int], None] = _no_hook,
    round_robins: int = 0,
    flush_s: float = 0.0,
    cache: bool = False,
) -> str:
    """Play the matches a stored run is missing; returns its run id.

    The schedule is rebuilt from the run's manifest (pools and seeds depend only
    on its seed), so the resumed run equals one that was never interrupted.
    `round_robins` above the run's own grows it to that many (0: its own).

    Raises:
        SystemExit: a bot or the library changed since the run started, so the
            rest of it would not be the same experiment; or `round_robins` would
            shrink it.
    """
    runs = RunStore.at(root)
    run_id = runs.resolve(ref)
    manifest = runs.manifest(run_id)
    config = manifest["config"]
    candidates = [make_spec(c["path"], c["params"]) for c in manifest["candidates"]]
    if manifest.get("library") != _numba_cache.digest():
        raise SystemExit(
            f"run {run_id} was played on another kit/engine version; start a new run"
        )
    if round_robins and round_robins < config["round_robins"]:
        raise SystemExit(
            f"run {run_id} plans {config['round_robins']} round robin(s): a run"
            f" only grows, not to {round_robins}"
        )
    target = max(round_robins, config["round_robins"])
    schedule = build_schedule(
        candidates,
        config["bots_dir"],
        config["pool_size"],
        target,
        config["seed"],
        config["mode"],
        config.get("allow_small", False),
        config.get("mocks", False),
        config.get("variants", 0.0),
        config.get("spaces_dir", ""),
    )
    pools = [[p.label for p in rr["pool"]] for rr in schedule]
    if pools[: len(manifest["pools"])] != manifest["pools"]:
        raise SystemExit(f"run {run_id}: its pools can't be rebuilt; start a new run")
    if used_bots(schedule[: len(manifest["pools"])]) != manifest["bots"]:
        raise SystemExit(
            f"run {run_id}: a bot file changed since the run started; start a new run"
        )
    if target > config["round_robins"]:
        _grow(runs, run_id, manifest, schedule, pools)
    played = runs.played_matches(run_id)
    todo = sum(len(rr["pairs"]) for rr in schedule) - len(played)
    if not todo:
        runs.finish(run_id, COMPLETE, 0.0)
        print(f"run {run_id} has every match already", file=sys.stderr)
        return run_id
    print(f"resuming {run_id}: {todo} match(es) to play", file=sys.stderr)
    runs.finish(run_id, RUNNING, 0.0)
    play_into(
        runs,
        run_id,
        schedule,
        config["rounds"],
        workers,
        candidates,
        on_batch,
        flush_s,
        played,
        cache,
    )
    return run_id


def _grow(
    runs: RunStore,
    run_id: str,
    manifest: dict,
    schedule: Sequence[dict],
    pools: list[list[str]],
) -> None:
    """Store the run's grown schedule: its target, pools and match count."""
    grown = {
        **manifest,
        "config": {**manifest["config"], "round_robins": len(schedule)},
        "pools": pools,
        "bots": used_bots(schedule),
        "n_matches": sum(len(rr["pairs"]) for rr in schedule),
    }
    runs.retarget(run_id, grown)
    print(
        f"growing {run_id} from {manifest['config']['round_robins']} to"
        f" {len(schedule)} round robin(s)",
        file=sys.stderr,
    )


def used_bots(schedule: Sequence[dict]) -> dict[str, str]:
    """{bot name: source hash} of every bot file the schedule plays."""
    paths = {s.path for rr in schedule for pair in rr["pairs"] for s in pair}
    return {bot_name(p): library.source_hash(p) for p in sorted(paths)}
