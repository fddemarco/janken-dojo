"""Gauntlets: candidates vs a list of opponents, each judged on its own.

A pool experiment scores a bot against random opponents, pooled; a gauntlet asks a
per-opponent question instead: does the candidate win at least a share of the
rounds against every opponent of the list, parameter variations included? Three
steps, each a `janken lab gauntlet` command:

    variations  draws parameter variants of the field's bots from their space
                files, keeping those that change the bot's play (the gauntlet's
                opponents, one spec per line);
    nash        which bots of such a list are Nash "with extra steps": no simple
                probe bot skews their results either way, so no bot can be
                expected to beat them (they leave the gauntlet);
    run         candidates vs every opponent on a ladder of seeds, every match
                appended to a log (JSON lines) as it is played, so a long
                gauntlet resumes; the report lists the opponents under the bar.

The functions here are pure but for `play` (the engine) and the log's reading and
writing; janken/cli/gauntlet.py wires them to the command line.
"""

import dataclasses
import json
import math
import os
import random
from collections.abc import Callable, Mapping, Sequence

from . import space as spaces

Z95 = 1.96
OVERRIDES = ":"  # a spec's path and its overrides: bots/l1/x.yaml:NAME=value


@dataclasses.dataclass(frozen=True)
class Job:
    """One match of a gauntlet: bot `a` (the one judged) vs `b`, on a seed."""

    a: str
    b: str
    seed: int


@dataclasses.dataclass(frozen=True)
class Played:
    """A match's shares of rounds won and lost by its bot `a`."""

    won: float
    lost: float


Log = dict[Job, Played]


@dataclasses.dataclass(frozen=True)
class Share:
    """A's mean share of rounds won vs one opponent, over its seeds."""

    opponent: str
    won: float
    lost: float
    half_width: float  # of the 95% CI of the mean share won (normal approximation)
    matches: int


@dataclasses.dataclass(frozen=True)
class NashVerdict:
    """A bot's most skewed matchup vs the probes, and whether it is Nash-like."""

    bot: str
    probe: str
    won: float
    lost: float
    nash_like: bool


# --- the log ----------------------------------------------------------------------


def load(path: str, rounds: int) -> Log:
    """Every match of `rounds` rounds in a gauntlet log; empty when there is none."""
    done: Log = {}
    if os.path.isfile(path):
        with open(path) as lines:
            for line in lines:
                row = json.loads(line)
                if int(row["rounds"]) != rounds:
                    continue
                job = Job(row["a"], row["b"], int(row["seed"]))
                done[job] = Played(float(row["won"]), float(row["lost"]))
    return done


def append(path: str, rounds: int, played: Mapping[Job, Played]) -> None:
    """Add matches to a gauntlet log."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as sink:
        for job, p in played.items():
            row = {"a": job.a, "b": job.b, "seed": job.seed, "rounds": rounds}
            row |= {"won": p.won, "lost": p.lost}
            sink.write(json.dumps(row) + "\n")


def missing(
    bots: Sequence[str], opponents: Sequence[str], seeds: Sequence[int], done: Log
) -> list[Job]:
    """The matches still to play, seed by seed (every opponent met early)."""
    jobs = [Job(a, b, s) for s in seeds for a in bots for b in opponents]
    return [j for j in jobs if j not in done]


def play(
    jobs: Sequence[Job],
    rounds: int,
    batch: int,
    log: str,
    workers: int,
    on_batch: Callable[[int, int], None],
) -> None:
    """Play the jobs in batches over every core, logging each batch as it ends."""
    from ..engine import play_pairs
    from .workflows import specs

    for k in range(0, len(jobs), batch):
        chunk = jobs[k : k + batch]
        pairs = [tuple(specs([j.a, j.b])) for j in chunk]
        out = play_pairs(pairs, rounds, [j.seed for j in chunk], workers or None)
        append(
            log,
            rounds,
            {
                j: Played(r.wins_a / rounds, r.wins_b / rounds)
                for j, r in zip(chunk, out, strict=True)
            },
        )
        on_batch(k + len(chunk), len(jobs))


# --- reading it -------------------------------------------------------------------


def shares(
    done: Log, bot: str, opponents: Sequence[str], seeds: Sequence[int]
) -> list[Share]:
    """The bot's share of rounds won vs each opponent it has met, in list order."""
    out = []
    for o in opponents:
        got = [done[Job(bot, o, s)] for s in seeds if Job(bot, o, s) in done]
        if got:
            out.append(share(o, got))
    return out


def share(opponent: str, played: Sequence[Played]) -> Share:
    """The mean share won over matches, with its 95% CI half-width."""
    n = len(played)
    won = sum(p.won for p in played) / n
    var = sum((p.won - won) ** 2 for p in played) / (n - 1) if n > 1 else 0.0
    return Share(
        opponent=opponent,
        won=won,
        lost=sum(p.lost for p in played) / n,
        half_width=Z95 * math.sqrt(var / n),
        matches=n,
    )


def nash_verdict(
    bot: str, played: Mapping[str, Sequence[Played]], skew: float
) -> NashVerdict:
    """A bot vs each probe (`played`: probe --> its matches) is Nash-like when, vs
    every probe, its mean share won minus lost stays under `skew` in size: a
    real bot exploits some simple bot or is exploited by one."""
    rows = [share(probe, matches) for probe, matches in played.items()]
    top = max(rows, key=lambda r: abs(r.won - r.lost))
    return NashVerdict(
        bot=bot,
        probe=top.opponent,
        won=top.won,
        lost=top.lost,
        nash_like=abs(top.won - top.lost) < skew,
    )


def nash_verdicts(
    done: Log,
    bots: Sequence[str],
    probes: Sequence[str],
    seeds: Sequence[int],
    skew: float,
) -> list[NashVerdict]:
    """Every bot's Nash verdict from a log of its matches vs the probes."""
    return [
        nash_verdict(
            b,
            {
                p: [done[Job(b, p, s)] for s in seeds if Job(b, p, s) in done]
                for p in probes
            },
            skew,
        )
        for b in bots
    ]


# --- variations -------------------------------------------------------------------


def quantiles(param: spaces.Param, n: int, rng: random.Random) -> list[float | int]:
    """n values spread over a space param's range: one per stratum, shuffled (a
    Latin hypercube column; on a log scale where the space says so)."""
    if param.type == "categorical":
        values = [param.choices[k % len(param.choices)] for k in range(n)]
        rng.shuffle(values)
        return list(values)
    lo, hi = float(param.low), float(param.high)
    log = param.log and lo > 0
    a, b = (math.log(lo), math.log(hi)) if log else (lo, hi)
    drawn = [a + (b - a) * (k + rng.random()) / n for k in range(n)]
    rng.shuffle(drawn)
    values = [math.exp(x) if log else x for x in drawn]
    if param.type == "int":
        return [round(v) for v in values]
    return [round(v, 3) for v in values]


def spec_text(path: str, values: Mapping[str, float | int]) -> str:
    """A bot spec with overrides, its parameters sorted."""
    return path + OVERRIDES + ",".join(f"{k}={v}" for k, v in sorted(values.items()))


def is_valid(values: Mapping[str, float | int]) -> bool:
    """A variant whose move probabilities (P_ROCK, P_PAPER) still sum to <= 1."""
    return float(values.get("P_ROCK", 0)) + float(values.get("P_PAPER", 0)) <= 1.0


def candidates(
    path: str, space: spaces.Space, per_bot: int, draws: int, seed: int
) -> list[str]:
    """Up to per_bot x draws distinct, valid variant specs of a bot, drawn from its
    space (draws Latin hypercubes of per_bot rows), seeded per bot stem."""
    stem = os.path.splitext(os.path.basename(path))[0]
    rng = random.Random(f"{seed}:{stem}")
    found: list[str] = []
    for _ in range(draws):
        columns = {n: quantiles(p, per_bot, rng) for n, p in space.params.items()}
        for k in range(per_bot):
            values = {n: col[k] for n, col in columns.items()}
            text = spec_text(path, values)
            if text not in found and is_valid(values):
                found.append(text)
    return found


def changing(
    default: str, variants: Sequence[str], probes: Sequence[str], rounds: int
) -> list[str]:
    """The variants whose moves differ from the default's in the same seeded
    matches vs the probes: their parameters change the bot's play."""
    from ..engine import play_pairs
    from .workflows import specs

    bots = [default, *variants]
    jobs = [(b, p, s) for b in bots for s, p in enumerate(probes, start=1)]
    out = play_pairs(
        [tuple(specs([b, p])) for b, p, _ in jobs], rounds, [s for *_, s in jobs]
    )
    moves: dict[str, list[str]] = {}
    for (b, _, _), result in zip(jobs, out, strict=True):
        moves.setdefault(b, []).append(result.moves[0::2])
    return [v for v in variants if moves[v] != moves[default]]
