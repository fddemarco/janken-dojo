"""Where a command's time goes, whether fixing it pays, and whether a fix worked.

`janken lab profile` (janken/cli/profile.py) is a thin layer over this module:

    run_profiled   a janken command under pyinstrument, in a subprocess
    bench          a janken command timed (no profiler), `repeats` times
    hotspots       the profile's time per janken function, and per bucket
    worth          the optimization budget: is a session worth its cost?
    span_stats     the timing spans every command logs (janken/telemetry.py)

The command runs in a **subprocess** because the JIT is settled when the engine is
imported (janken/kit/jit.py): `jit` picks compiled bots or plain Python. With the JIT
on, a compiled kernel is opaque to the profiler: its time is the self time of the
janken function that calls it. With it off, the kernels' Python shows, slower but in
the same proportions, roughly. Profiled and benchmarked commands log no spans
($JANKEN_SPANS=off), so the analytics hold real use only.

Each profile or benchmark is a folder of the workspace's `profile.dir`: `meta.json`
(the `Record`), and for a profile `session.pyisession`, `profile.html` and the
command's output.
"""

import collections
import dataclasses
import datetime
import glob
import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
from collections.abc import Iterator, Mapping, Sequence
from typing import Any

import duckdb
import polars as pl
from pyinstrument import renderers
from pyinstrument.frame import Frame
from pyinstrument.session import Session

from .. import settings, telemetry
from . import duck, store

PROFILE, BENCH = "profile", "bench"
META, SESSION, HTML, OUTPUT = "meta.json", "session.pyisession", "profile.html", "output.txt"
JANKEN_DIR = os.path.join(settings.ROOT, "janken") + os.sep
OUTSIDE = "(outside janken)"
COMMAND_OP = "command"
# Buckets, by the library a sample's frames are in. The first two claim a sample when
# a frame on its stack matches: importing or compiling is what the whole stack does.
COMPILE, IMPORT, STORAGE, OPTUNA, JANKEN, OTHER = (
    "compile",
    "import",
    "storage",
    "optuna",
    "janken",
    "other",
)
COMPILE_PATHS = (f"{os.sep}numba{os.sep}", f"{os.sep}llvmlite{os.sep}")
IMPORT_FUNCTIONS = ("_find_and_load", "_handle_fromlist")
STORAGE_PATHS = tuple(
    f"{os.sep}{lib}{os.sep}" for lib in ("duckdb", "polars", "pyarrow", "pandas")
)
OPTUNA_PATHS = (f"{os.sep}optuna{os.sep}", f"{os.sep}sqlalchemy{os.sep}")


class ProfileError(ValueError):
    """A profile that can't be taken or found, or a target command that failed."""


@dataclasses.dataclass(frozen=True)
class Hotspot:
    """Time spent in one janken function, and in what it calls outside janken."""

    where: str  # path:function:line, or OUTSIDE
    seconds: float
    share: float  # of the profiled (sampled) time
    bucket: str  # where most of that time went


@dataclasses.dataclass(frozen=True)
class Record:
    """One profile or benchmark of a janken command."""

    id: str
    kind: str  # PROFILE or BENCH
    created: str  # ISO 8601, local time
    argv: tuple[str, ...]  # the janken command, without `janken`
    jit: bool
    fingerprint: str  # telemetry.code_fingerprint() when it ran
    git: Mapping[str, object]
    times: tuple[float, ...]  # wall seconds of each run (a profile: one)
    hotspots: tuple[Hotspot, ...] = ()
    buckets: Mapping[str, float] = dataclasses.field(default_factory=dict)

    @property
    def wall_s(self) -> float:
        """The fastest run's wall time."""
        return min(self.times)

    @property
    def target(self) -> str:
        """The command, as typed."""
        return "janken " + " ".join(self.argv)

    def to_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Record":
        """A record as `to_dict` (and meta.json) holds it."""
        return cls(
            id=str(data["id"]),
            kind=str(data["kind"]),
            created=str(data["created"]),
            argv=tuple(str(a) for a in data["argv"]),
            jit=bool(data["jit"]),
            fingerprint=str(data["fingerprint"]),
            git=dict(data["git"]),
            times=tuple(float(t) for t in data["times"]),
            hotspots=tuple(Hotspot(**h) for h in data["hotspots"]),
            buckets={str(k): float(v) for k, v in data["buckets"].items()},
        )


@dataclasses.dataclass(frozen=True)
class Worth:
    """The budget rule's verdict on one profile (docs/development.md, Performance)."""

    worth: bool
    reason: str
    share: float  # the top hotspot's share of wall time
    typical_s: float  # a real run of the command (median of its spans, else the profile)
    uses: float  # projected runs over the horizon
    saving_s: float  # what cutting expected_cut of the hotspot saves over the horizon
    cost_s: float  # the session's cost


@dataclasses.dataclass(frozen=True)
class Profiled:
    """A finished profile: its record and its folder."""

    record: Record
    folder: str


# --- storing records ----------------------------------------------------------------


def profiles_dir(workspace: str) -> str:
    return os.path.join(workspace, settings.config().profile.dir)


def new_id(kind: str, argv: Sequence[str], when: datetime.datetime) -> str:
    """A sortable, readable id: time, kind, the command's words and a short hash."""
    words = [w for w in argv[:3] if not w.startswith("-") and os.sep not in w]
    digest = hashlib.sha256(" ".join(argv).encode()).hexdigest()[:6]
    return "-".join([when.strftime("%Y%m%d-%H%M%S"), kind, *words, digest])


def _new_folder(workspace: str, kind: str, argv: Sequence[str]) -> tuple[str, str]:
    now = datetime.datetime.now()
    base = new_id(kind, argv, now)
    record_id, n = base, 1
    while os.path.exists(os.path.join(profiles_dir(workspace), record_id)):
        n += 1
        record_id = f"{base}-{n}"
    folder = os.path.join(profiles_dir(workspace), record_id)
    os.makedirs(folder)
    return record_id, folder


def save(record: Record, folder: str) -> None:
    with open(os.path.join(folder, META), "w", encoding="utf-8") as f:
        json.dump(record.to_dict(), f, indent=2)


def records(workspace: str) -> list[Record]:
    """Every stored profile and benchmark, oldest first."""
    found = []
    for path in sorted(glob.glob(os.path.join(profiles_dir(workspace), "*", META))):
        with open(path, encoding="utf-8") as f:
            found.append(Record.from_dict(json.load(f)))
    return found


def find(workspace: str, ref: str) -> Record:
    """A record by id, a unique part of one, or `latest`.

    Raises:
        ProfileError: none, or more than one, matches.
    """
    stored = records(workspace)
    if ref == "latest" and stored:
        return stored[-1]
    exact = [r for r in stored if r.id == ref]
    matches = exact or [r for r in stored if ref in r.id]
    if len(matches) != 1:
        found = "no" if not matches else f"{len(matches)}"
        raise ProfileError(f"{found} profile or benchmark matches {ref!r}")
    return matches[0]


def folder_of(workspace: str, record: Record) -> str:
    return os.path.join(profiles_dir(workspace), record.id)


def same_code(
    stored: Sequence[Record], argv: Sequence[str], jit: bool, fingerprint: str
) -> list[Record]:
    """The profiles of this very command on this very code: re-profiling it would
    only measure noise."""
    return [
        r
        for r in stored
        if r.kind == PROFILE
        and r.argv == tuple(argv)
        and r.jit == jit
        and r.fingerprint == fingerprint
    ]


# --- running ------------------------------------------------------------------------


def _environment(jit: bool) -> dict[str, str]:
    """The command's environment: the JIT as asked, no spans, no bars, and caching
    left to the command (this process's own decision must not leak into it)."""
    env = {k: v for k, v in os.environ.items() if k != settings.CACHE_ENV}
    return env | {
        settings.JIT_ENV: "on" if jit else "off",
        settings.SPANS_ENV: "off",
        settings.PROGRESS_ENV: "off",
    }


def _run(command: Sequence[str], jit: bool, output: str) -> float:
    """Run `command` from the project root; returns its wall seconds.

    Raises:
        ProfileError: it failed (the tail of its output says why).
    """
    started = time.perf_counter()
    with open(output, "w", encoding="utf-8") as out:
        done = subprocess.run(
            list(command),
            cwd=settings.ROOT,
            env=_environment(jit),
            stdout=out,
            stderr=subprocess.STDOUT,
            check=False,
        )
    elapsed = time.perf_counter() - started
    if done.returncode != 0:
        with open(output, encoding="utf-8", errors="replace") as f:
            tail = "".join(f.readlines()[-15:])
        raise ProfileError(
            f"the command exited with status {done.returncode} (output: {output}):"
            f"\n{tail}"
        )
    return elapsed


def _janken(argv: Sequence[str]) -> list[str]:
    return [sys.executable, "-m", "janken", *argv]


def run_profiled(
    workspace: str,
    argv: Sequence[str],
    jit: bool,
    warmup: bool,
    interval: float,
    top: int,
) -> Profiled:
    """Profile `janken <argv>` (after one unmeasured run, with `warmup`) and store
    the profile in the workspace."""
    record_id, folder = _new_folder(workspace, PROFILE, argv)
    if warmup:
        _run(_janken(argv), jit, os.path.join(folder, OUTPUT))
    session_path = os.path.join(folder, SESSION)
    wall = _run(
        [
            sys.executable,
            "-m",
            "pyinstrument",
            "--interval",
            str(interval),
            "--renderer",
            "pyisession",
            "--outfile",
            session_path,
            "-m",
            "janken",
            *argv,
        ],
        jit,
        os.path.join(folder, OUTPUT),
    )
    session = Session.load(session_path)
    with open(os.path.join(folder, HTML), "w", encoding="utf-8") as f:
        f.write(renderers.HTMLRenderer().render(session))
    spots, shares = attribute(session, top)
    record = Record(
        id=record_id,
        kind=PROFILE,
        created=_now(),
        argv=tuple(argv),
        jit=jit,
        fingerprint=telemetry.code_fingerprint(),
        git=store.git_info(),
        times=(wall,),
        hotspots=tuple(spots),
        buckets=shares,
    )
    save(record, folder)
    return Profiled(record, folder)


def bench(
    workspace: str, argv: Sequence[str], jit: bool, warmup: bool, repeats: int
) -> Profiled:
    """Time `janken <argv>` `repeats` times (no profiler; after one unmeasured run,
    with `warmup`) and store the benchmark."""
    record_id, folder = _new_folder(workspace, BENCH, argv)
    command = _janken(argv)
    output = os.path.join(folder, OUTPUT)
    if warmup:
        _run(command, jit, output)
    times = tuple(_run(command, jit, output) for _ in range(repeats))
    record = Record(
        id=record_id,
        kind=BENCH,
        created=_now(),
        argv=tuple(argv),
        jit=jit,
        fingerprint=telemetry.code_fingerprint(),
        git=store.git_info(),
        times=times,
    )
    save(record, folder)
    return Profiled(record, folder)


def gain(baseline: Record, new: Record) -> float:
    """The share of the baseline's wall time the new run cut (negative: slower).

    Raises:
        ProfileError: they didn't time the same command the same way.
    """
    if (baseline.argv, baseline.jit) != (new.argv, new.jit):
        raise ProfileError(
            f"the baseline {baseline.id} timed another command"
            f" ({baseline.target}, jit {baseline.jit})"
        )
    return 1 - new.wall_s / baseline.wall_s


def _now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


# --- reading a session ----------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Sample:
    """Self time of one frame, with the stack above it."""

    seconds: float
    stack: tuple[Frame, ...]  # root first; the last frame holds the time


def samples(root: Frame) -> Iterator[Sample]:
    """Every frame's self time, with its stack."""
    stack: list[tuple[Frame, tuple[Frame, ...]]] = [(root, (root,))]
    while stack:
        frame, path = stack.pop()
        own = frame.time - sum(
            c.time for c in frame.children if not c.is_synthetic_leaf
        )
        if own > 0:
            yield Sample(own, path)
        stack += [
            (c, (*path, c)) for c in frame.children if not c.is_synthetic_leaf
        ]


def _path(frame: Frame) -> str:
    return frame.file_path or ""


def bucket(stack: Sequence[Frame]) -> str:
    """What a sample's time is: importing or compiling (whichever the stack does
    first, from its root: numba compiles on import too), else the leaf's library."""
    for frame in stack:
        if frame.function in IMPORT_FUNCTIONS:
            return IMPORT
        if any(p in _path(frame) for p in COMPILE_PATHS):
            return COMPILE
    leaf = _path(stack[-1])
    if any(p in leaf for p in STORAGE_PATHS):
        return STORAGE
    if any(p in leaf for p in OPTUNA_PATHS):
        return OPTUNA
    if leaf.startswith(JANKEN_DIR):
        return JANKEN
    return OTHER


def owner(stack: Sequence[Frame]) -> str:
    """The innermost janken function on the stack: the code to change."""
    for frame in reversed(stack):
        path = _path(frame)
        if path.startswith(JANKEN_DIR):
            where = os.path.relpath(path, settings.ROOT)
            return f"{where}:{frame.function}:{frame.line_no}"
    return OUTSIDE


def _largest(times: Mapping[str, float]) -> list[str]:
    """The keys, largest time first."""
    return sorted(times, key=lambda k: -times[k])


def attribute(session: Session, top: int) -> tuple[list[Hotspot], dict[str, float]]:
    """The `top` janken functions by the time spent in them and in what they call
    outside janken, and every bucket's share of the wall time."""
    root = session.root_frame()
    if root is None or root.time <= 0:
        return [], {}
    wall = root.time  # sampled time (session.duration also counts the profiler's own)
    seconds: dict[str, float] = collections.defaultdict(float)
    by_owner: dict[str, dict[str, float]] = collections.defaultdict(
        lambda: collections.defaultdict(float)
    )
    buckets: dict[str, float] = collections.defaultdict(float)
    for s in samples(root):
        kind, where = bucket(s.stack), owner(s.stack)
        seconds[where] += s.seconds
        by_owner[where][kind] += s.seconds
        buckets[kind] += s.seconds
    spots = [
        Hotspot(
            where=where,
            seconds=round(seconds[where], 6),
            share=round(seconds[where] / wall, 6),
            bucket=_largest(by_owner[where])[0],
        )
        for where in _largest(seconds)[:top]
    ]
    shares = {k: round(buckets[k] / wall, 6) for k in _largest(buckets)}
    return spots, shares


# --- spans ------------------------------------------------------------------------------


def spans_glob(workspace: str) -> str:
    """The spans file and its rotated copies (loguru renames them stem.<date>.ext)."""
    stem, ext = os.path.splitext(settings.config().telemetry.file)
    return os.path.join(workspace, stem + "*" + ext)


SPAN_STATS = """
SELECT op, coalesce(command, '') AS command, count(*) AS n,
       round(sum(seconds), 3) AS total_s, round(median(seconds), 3) AS median_s,
       round(quantile_cont(seconds, 0.95), 3) AS p95_s,
       round(arg_max(seconds, ts), 3) AS last_s,
       CAST(max(ts) AS VARCHAR) AS last_at,
       count(*) >= 3 AND arg_max(seconds, ts) >= ? * median(seconds) AS slow
FROM read_json({files}, format = 'newline_delimited', union_by_name = true,
               columns = {{ts: 'TIMESTAMPTZ', op: 'VARCHAR', seconds: 'DOUBLE',
                           command: 'VARCHAR'}})
WHERE ts >= CAST(? AS TIMESTAMPTZ) {op_filter}
GROUP BY ALL
ORDER BY total_s DESC
"""


def span_stats(
    workspace: str, days: int, slow_factor: float, op: str = ""
) -> pl.DataFrame:
    """Per operation and command over the last `days`: runs, total, median, p95 and
    last seconds, and `slow` when the last run took `slow_factor` times the median."""
    files = sorted(glob.glob(spans_glob(workspace)))
    if not files:
        return pl.DataFrame()
    since = datetime.datetime.now().astimezone() - datetime.timedelta(days=days)
    listed = "[" + ", ".join("'" + f.replace("'", "''") + "'" for f in files) + "]"
    sql = SPAN_STATS.format(files=listed, op_filter="AND op = ?" if op else "")
    params: list[object] = [slow_factor, since.isoformat(), *([op] if op else [])]
    con = duckdb.connect()
    try:
        return duck.fetch_frame(con, sql, params)
    finally:
        con.close()


def command_runs(stats: pl.DataFrame) -> dict[str, tuple[int, float]]:
    """Each command's runs and median seconds, from `span_stats`."""
    if not stats.height:
        return {}
    rows = stats.filter(pl.col("op") == COMMAND_OP).iter_rows(named=True)
    return {r["command"]: (int(r["n"]), float(r["median_s"])) for r in rows}


def command_name(argv: Sequence[str], known: Sequence[str]) -> str:
    """The lab command `argv` runs, as spans name it ("lab experiment"): the longest
    known prefix, else its first word."""
    for k in range(min(len(argv), 3), 0, -1):
        name = " ".join(argv[:k])
        if name in known:
            return name
    return argv[0] if argv else ""


# --- the budget -----------------------------------------------------------------------


def worth(
    record: Record, stats: pl.DataFrame, cfg: settings.ProfileConfig
) -> Worth:
    """Whether optimizing the profile's top hotspot is worth a session.

    It must hold `min_share` of the wall time (less gains under ~11% even if removed
    whole); and cutting `expected_cut` of it on every run projected over
    `horizon_days` must save at least the session's cost, `session_minutes`.
    """
    cost = cfg.session_minutes * 60.0
    spots = [h for h in record.hotspots if h.where != OUTSIDE] or list(record.hotspots)
    share = spots[0].share if spots else 0.0
    runs = command_runs(stats)
    name = command_name(record.argv, list(runs))
    if name in runs:
        n, typical = runs[name]
        uses = n / cfg.window_days * cfg.horizon_days
        basis = f"{n} run(s) in {cfg.window_days} days"
    else:
        typical = record.wall_s
        uses = float(cfg.horizon_days)  # no history: once a day
        basis = "no span history: assumed once a day"
    saving = share * typical * cfg.expected_cut * uses
    if share < cfg.min_share:
        verdict, reason = (
            False,
            f"the top hotspot holds {share:.0%} of the time, under min_share"
            f" {cfg.min_share:.0%}",
        )
    elif saving < cost:
        verdict, reason = (
            False,
            f"it would save {saving / 60:.0f} min over {cfg.horizon_days} days"
            f" ({basis}), under the session's {cfg.session_minutes} min",
        )
    else:
        verdict, reason = (
            True,
            f"it would save {saving / 60:.0f} min over {cfg.horizon_days} days"
            f" ({basis}), over the session's {cfg.session_minutes} min",
        )
    return Worth(verdict, reason, share, typical, uses, saving, cost)


def keep(change: float, cfg: settings.ProfileConfig) -> bool:
    """Whether a benchmarked change cut enough wall time to stay."""
    return change >= cfg.min_gain


# --- rendering --------------------------------------------------------------------------


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in rows])


def render(record: Record, folder: str) -> str:
    """A profile or benchmark as markdown."""
    times = ", ".join(f"{t:.2f}s" for t in record.times)
    lines = [
        f"## {record.kind} {record.id}",
        "",
        f"`{record.target}` (jit {'on' if record.jit else 'off'},"
        f" code {record.fingerprint}): {times}",
    ]
    if record.buckets:
        lines += [
            "",
            _table(
                ["bucket", "share"],
                [[k, f"{v:.1%}"] for k, v in record.buckets.items()],
            ),
        ]
    if record.hotspots:
        lines += [
            "",
            _table(
                ["hotspot", "seconds", "share", "mostly"],
                [
                    [f"`{h.where}`", f"{h.seconds:.2f}", f"{h.share:.1%}", h.bucket]
                    for h in record.hotspots
                ],
            ),
        ]
    if record.kind == PROFILE:
        lines += ["", f"flame graph: {os.path.join(folder, HTML)}"]
    return "\n".join(lines)


def render_worth(verdict: Worth) -> str:
    word = "worth optimizing" if verdict.worth else "not worth optimizing"
    return f"**{word}**: {verdict.reason}."


def render_list(stored: Sequence[Record], fingerprint: str) -> str:
    if not stored:
        return "(no profiles yet)"
    return _table(
        ["id", "command", "jit", "wall", "top hotspot", "code"],
        [
            [
                r.id,
                f"`{r.target}`",
                "on" if r.jit else "off",
                f"{r.wall_s:.2f}s",
                f"`{r.hotspots[0].where}` {r.hotspots[0].share:.0%}"
                if r.hotspots
                else "",
                "current" if r.fingerprint == fingerprint else "stale",
            ]
            for r in stored
        ],
    )
