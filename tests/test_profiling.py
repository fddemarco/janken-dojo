"""janken/lab/profiling.py: hotspots, buckets, records, spans and the budget rule."""

import dataclasses
import datetime
import json
import os
import pathlib
from typing import cast

import polars as pl
import pyinstrument
import pytest
from pyinstrument.frame import Frame

from janken import settings, telemetry
from janken.lab import profiling

CFG = settings.config().profile
ARGV = ("lab", "experiment", "bots/l1/x.yaml")


def record(
    hotspots: tuple[profiling.Hotspot, ...] = (),
    times: tuple[float, ...] = (10.0,),
    kind: str = profiling.PROFILE,
    record_id: str = "20260101-000000-profile-lab-experiment-abc123",
    argv: tuple[str, ...] = ARGV,
    fingerprint: str = "f1",
) -> profiling.Record:
    return profiling.Record(
        id=record_id,
        kind=kind,
        created="2026-01-01T00:00:00+00:00",
        argv=argv,
        jit=True,
        fingerprint=fingerprint,
        git={"commit": "abc", "dirty": False},
        times=times,
        hotspots=hotspots,
        buckets={"janken": 1.0},
    )


def spot(share: float) -> profiling.Hotspot:
    return profiling.Hotspot("janken/x.py:f:1", share * 10, share, "janken")


@dataclasses.dataclass(frozen=True)
class FakeFrame:
    """What `bucket` and `owner` read of a pyinstrument frame."""

    function: str
    file_path: str
    line_no: int = 1


def stack(*frames: tuple[str, str]) -> list[Frame]:
    return [cast(Frame, FakeFrame(fn, path)) for fn, path in frames]


SITE = os.sep + os.path.join("venv", "site-packages") + os.sep


@pytest.mark.parametrize(
    "frames, expected",
    [
        ([("main", profiling.JANKEN_DIR + "a.py")], profiling.JANKEN),
        (
            [("main", profiling.JANKEN_DIR + "a.py"), ("f", SITE + "numba/x.py")],
            profiling.COMPILE,
        ),
        (
            [("_find_and_load", "<frozen>"), ("f", SITE + "numba/x.py")],
            profiling.IMPORT,
        ),
        ([("main", "x.py"), ("q", SITE + "duckdb/q.py")], profiling.STORAGE),
        ([("main", "x.py"), ("t", SITE + "optuna/t.py")], profiling.OPTUNA),
        ([("main", "x.py"), ("len", "<built-in>")], profiling.OTHER),
    ],
)
def test_a_sample_falls_in_one_bucket(
    frames: list[tuple[str, str]], expected: str
) -> None:
    assert profiling.bucket(stack(*frames)) == expected


def test_a_sample_belongs_to_the_innermost_janken_function() -> None:
    frames = stack(
        ("outer", profiling.JANKEN_DIR + "a.py"),
        ("inner", profiling.JANKEN_DIR + "b.py"),
        ("sort", SITE + "numpy/s.py"),
    )
    assert profiling.owner(frames) == os.path.join("janken", "b.py") + ":inner:1"
    assert profiling.owner(stack(("f", "x.py"))) == profiling.OUTSIDE


def test_a_profile_is_attributed_to_janken_functions() -> None:
    profiler = pyinstrument.Profiler(interval=0.0001)
    profiler.start()
    for _ in range(5):
        telemetry.code_fingerprint()
    profiler.stop()
    session = profiler.last_session
    assert session is not None
    spots, buckets = profiling.attribute(session, 3)
    assert spots[0].where.startswith(os.path.join("janken", "telemetry.py"))
    assert sum(buckets.values()) == pytest.approx(1.0, abs=0.01)
    assert all(0 < h.share <= 1 for h in spots)


@pytest.mark.parametrize(
    "share, runs, worth",
    [
        (0.05, 10_000, False),  # too small a share, however often it runs
        (0.5, 1, False),  # big, but too rare to pay a session back
        (0.5, 300, True),
    ],
)
def test_the_budget_rule(share: float, runs: int, worth: bool) -> None:
    stats = pl.DataFrame(
        {"op": ["command"], "command": ["lab experiment"], "n": [runs]}
        | {"median_s": [60.0]}
    )
    verdict = profiling.worth(record((spot(share),)), stats, CFG)
    assert verdict.worth is worth
    assert verdict.typical_s == 60.0


def test_without_history_a_command_is_assumed_daily() -> None:
    verdict = profiling.worth(record((spot(0.5),)), pl.DataFrame(), CFG)
    assert verdict.uses == CFG.horizon_days
    assert verdict.typical_s == 10.0


def test_a_change_is_kept_only_above_the_minimum_gain() -> None:
    before = record(times=(10.0, 11.0), kind=profiling.BENCH)
    assert profiling.gain(before, record(times=(8.0,))) == pytest.approx(0.2)
    assert profiling.keep(0.2, CFG)
    assert not profiling.keep(CFG.min_gain / 2, CFG)
    with pytest.raises(profiling.ProfileError):
        profiling.gain(before, record(argv=("lab", "match")))


def test_records_round_trip_and_are_found(tmp_path: pathlib.Path) -> None:
    workspace = str(tmp_path)
    first = record((spot(0.5),))
    second = record(record_id="20260102-000000-bench-lab-match-def456", kind="bench")
    for r in (first, second):
        folder = profiling.folder_of(workspace, r)
        os.makedirs(folder)
        profiling.save(r, folder)
    assert profiling.records(workspace) == [first, second]
    assert profiling.find(workspace, "latest") == second
    assert profiling.find(workspace, "abc123") == first
    with pytest.raises(profiling.ProfileError):
        profiling.find(workspace, "2026010")  # both


def test_the_same_code_is_not_profiled_twice() -> None:
    stored = [record(), record(fingerprint="f2"), record(kind=profiling.BENCH)]
    assert profiling.same_code(stored, ARGV, True, "f1") == [stored[0]]
    assert profiling.same_code(stored, ARGV, False, "f1") == []
    assert profiling.same_code(stored, ("lab", "match"), True, "f1") == []


def test_the_command_is_the_longest_known_prefix() -> None:
    known = ["lab", "lab experiment", "evaluate"]
    assert profiling.command_name(ARGV, known) == "lab experiment"
    assert profiling.command_name(("tune", "x"), known) == "tune"


def test_span_stats_flag_a_slow_last_run(tmp_path: pathlib.Path) -> None:
    now = datetime.datetime.now().astimezone()
    rows = [
        (now - datetime.timedelta(days=400), "command", 99.0),  # outside the window
        (now - datetime.timedelta(hours=3), "command", 1.0),
        (now - datetime.timedelta(hours=2), "command", 1.0),
        (now - datetime.timedelta(hours=1), "command", 2.0),
        (now - datetime.timedelta(hours=1), "engine.play", 0.5),
    ]
    path = pathlib.Path(profiling.spans_glob(str(tmp_path)).replace("*", ""))
    path.parent.mkdir(parents=True)
    path.write_text(
        "".join(
            json.dumps(
                {"ts": ts.isoformat(), "op": op, "seconds": s, "command": "lab x"}
            )
            + "\n"
            for ts, op, s in rows
        )
    )
    frame = profiling.span_stats(str(tmp_path), 30, 1.5)
    command = frame.filter(pl.col("op") == "command").row(0, named=True)
    assert command["n"] == 3
    assert command["slow"] is True
    assert profiling.command_runs(frame) == {"lab x": (3, 1.0)}
    only = profiling.span_stats(str(tmp_path), 30, 1.5, op="engine.play")
    assert only["op"].to_list() == ["engine.play"]
    assert profiling.span_stats(str(tmp_path / "none"), 30, 1.5).height == 0
