"""The move dataset: every round of every match, in one DuckDB file, append-only.

    matches   one row per match: when and how it was played, both players'
              configurations, its outcome and its holdout key
    rounds    one row per round played: (match_id, round, p1_move, p2_move)

Moves are 0/1/2 = rock/paper/scissors, 3 an invalid move (janken.kit.moves). A
match that ended early (a forfeit) has fewer rounds than scheduled: its
`rounds_played`.

Nothing here updates or deletes a row: `append` adds matches in one transaction
(all of them or none), under match ids that continue the stored ones, so an id
range is a fixed snapshot of the data. A large batch is committed in chunks
(`append_to` its batch id), each its own transaction, so an interrupted batch
keeps a complete prefix of its matches. The holdout key is drawn once per
match, when it is stored, so a match's split never changes as the dataset grows.
"""

import dataclasses
import datetime
import json
import os
from collections.abc import Sequence

import duckdb
import numpy as np
import polars as pl

from .. import botfile, settings
from ..kit.moves import INVALID
from ..match import MatchResult
from ..spec import BotSpec
from . import duck, store

SPLITS = ("train", "test", "all")

SCHEMA = """
CREATE TABLE IF NOT EXISTS matches (
    match_id BIGINT PRIMARY KEY,
    batch_id BIGINT NOT NULL,
    played_at TIMESTAMP NOT NULL,
    rounds INTEGER NOT NULL,
    rounds_played INTEGER NOT NULL,
    seed BIGINT NOT NULL,
    batch_seed BIGINT NOT NULL,
    holdout_key DOUBLE NOT NULL,
    p1_label VARCHAR NOT NULL,
    p1_stem VARCHAR NOT NULL,
    p1_path VARCHAR NOT NULL,
    p1_params JSON NOT NULL,
    p1_overrides JSON NOT NULL,
    p1_sha256 VARCHAR NOT NULL,
    p2_label VARCHAR NOT NULL,
    p2_stem VARCHAR NOT NULL,
    p2_path VARCHAR NOT NULL,
    p2_params JSON NOT NULL,
    p2_overrides JSON NOT NULL,
    p2_sha256 VARCHAR NOT NULL,
    p1_wins INTEGER NOT NULL,
    p2_wins INTEGER NOT NULL,
    draws INTEGER NOT NULL,
    p1_forfeit VARCHAR,
    p2_forfeit VARCHAR,
    library VARCHAR NOT NULL,
    git_commit VARCHAR NOT NULL,
    git_dirty BOOLEAN NOT NULL,
    command VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS rounds (
    match_id BIGINT NOT NULL,
    round INTEGER NOT NULL,
    p1_move TINYINT NOT NULL,
    p2_move TINYINT NOT NULL
);
"""

# Move codes by transcript character (MatchResult.moves).
_MOVE_CODES = np.full(256, -1, np.int8)
for _code, _char in enumerate("rpsx"):
    _MOVE_CODES[ord(_char)] = _code


@dataclasses.dataclass(frozen=True)
class PlayedMatch:
    """One match to store: who played, under which seed, and what happened."""

    p1: BotSpec
    p2: BotSpec
    seed: int
    holdout_key: float
    result: MatchResult


@dataclasses.dataclass(frozen=True)
class GitInfo:
    """The code a batch was played with ("" when it isn't a git checkout)."""

    commit: str
    dirty: bool

    @classmethod
    def current(cls) -> "GitInfo":
        info = store.git_info()
        return cls(commit=info["commit"] or "", dirty=bool(info["dirty"]))


@dataclasses.dataclass(frozen=True)
class Batch:
    """Matches played together, by one command."""

    matches: Sequence[PlayedMatch]
    rounds: int
    seed: int
    library: str
    git: GitInfo
    command: Sequence[str]
    played_at: datetime.datetime


@dataclasses.dataclass(frozen=True)
class Sequences:
    """Matches as move sequences, ready for the prediction kernel.

    Match k's rounds are p1[starts[k]:starts[k + 1]] (and p2 likewise); its players
    are labels[p1_index[k]] and labels[p2_index[k]].
    """

    match_ids: np.ndarray  # int64[m]
    seeds: np.ndarray  # int64[m]
    starts: np.ndarray  # int64[m + 1]
    p1: np.ndarray  # int64[total], moves
    p2: np.ndarray  # int64[total]
    p1_index: np.ndarray  # int64[m], into labels
    p2_index: np.ndarray  # int64[m]
    labels: list[str]

    @property
    def n_matches(self) -> int:
        return int(self.match_ids.size)

    @property
    def n_rounds(self) -> int:
        return int(self.p1.size)

    def take(self, first: int, stop: int) -> "Sequences":
        """Matches first..stop-1 only."""
        lo, hi = int(self.starts[first]), int(self.starts[stop])
        return dataclasses.replace(
            self,
            match_ids=self.match_ids[first:stop],
            seeds=self.seeds[first:stop],
            starts=self.starts[first : stop + 1] - lo,
            p1=self.p1[lo:hi],
            p2=self.p2[lo:hi],
            p1_index=self.p1_index[first:stop],
            p2_index=self.p2_index[first:stop],
        )

    def spread(self, n: int) -> "Sequences":
        """`n` matches evenly spread over the whole set (all of them if fewer), so
        every part of the dataset is represented, in id order."""
        if n >= self.n_matches:
            return self
        keep = np.unique(np.linspace(0, self.n_matches - 1, n).round().astype(np.int64))
        lengths = np.diff(self.starts)[keep]
        rounds = np.concatenate(
            [np.arange(self.starts[k], self.starts[k + 1]) for k in keep]
        )
        return dataclasses.replace(
            self,
            match_ids=self.match_ids[keep],
            seeds=self.seeds[keep],
            starts=np.concatenate([[0], np.cumsum(lengths)]).astype(np.int64),
            p1=self.p1[rounds],
            p2=self.p2[rounds],
            p1_index=self.p1_index[keep],
            p2_index=self.p2_index[keep],
        )


def default_path() -> str:
    """The dataset file: `[tool.janken.dataset] file` in the experiments directory."""
    return os.path.join(store.EXPERIMENTS, settings.config().dataset.file)


def connect(path: str, read_only: bool) -> duckdb.DuckDBPyConnection:
    """Open the dataset (read-only, or creating it and its tables).

    Raises:
        SystemExit: a read-only open of a dataset that doesn't exist.
    """
    if read_only:
        if not os.path.isfile(path):
            raise SystemExit(
                f"no dataset at {path}; build one with `janken lab dataset add`"
            )
        return duckdb.connect(path, read_only=True)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    con = duckdb.connect(path)
    con.execute(SCHEMA)
    return con


def append(con: duckdb.DuckDBPyConnection, batch: Batch) -> range:
    """Store a batch as a new batch id, in one transaction; returns its match ids."""
    return append_to(con, batch, next_batch_id(con))


def append_to(con: duckdb.DuckDBPyConnection, batch: Batch, batch_id: int) -> range:
    """Store `batch`'s matches under `batch_id` (new, or one being committed in
    chunks), in one transaction; returns their match ids."""
    if not batch.matches:
        return range(0)
    con.execute("BEGIN TRANSACTION")
    try:
        first, _ = _next_ids(con)
        ids = range(first, first + len(batch.matches))
        duck.insert_frame(con, "matches", _matches_frame(batch, ids, batch_id))
        duck.insert_frame(con, "rounds", _rounds_frame(batch, ids))
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")
        raise
    return ids


def next_batch_id(con: duckdb.DuckDBPyConnection) -> int:
    """The id the next new batch gets."""
    return _next_ids(con)[1]


def _next_ids(con: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    row = con.execute(
        "SELECT coalesce(max(match_id) + 1, 0), coalesce(max(batch_id) + 1, 0)"
        " FROM matches"
    ).fetchone()
    if row is None:
        raise RuntimeError("the matches table returned no row")
    return int(row[0]), int(row[1])


def _player(prefix: str, spec: BotSpec) -> dict[str, object]:
    params = {**botfile.defaults(spec.path), **spec.params}
    return {
        f"{prefix}_label": spec.label,
        f"{prefix}_stem": spec.stem,
        f"{prefix}_path": spec.path,
        f"{prefix}_params": json.dumps(params, sort_keys=True),
        f"{prefix}_overrides": json.dumps(spec.params, sort_keys=True),
        f"{prefix}_sha256": botfile.source_hash(spec.path),
    }


def _matches_frame(batch: Batch, ids: range, batch_id: int) -> pl.DataFrame:
    rows = [
        {
            "match_id": match_id,
            "batch_id": batch_id,
            "played_at": batch.played_at,
            "rounds": batch.rounds,
            "rounds_played": len(m.result.moves) // 2,
            "seed": m.seed,
            "batch_seed": batch.seed,
            "holdout_key": m.holdout_key,
            **_player("p1", m.p1),
            **_player("p2", m.p2),
            "p1_wins": m.result.wins_a,
            "p2_wins": m.result.wins_b,
            "draws": m.result.draws,
            "p1_forfeit": m.result.forfeit_a,
            "p2_forfeit": m.result.forfeit_b,
            "library": batch.library,
            "git_commit": batch.git.commit,
            "git_dirty": batch.git.dirty,
            "command": json.dumps(list(batch.command)),
        }
        for match_id, m in zip(ids, batch.matches)
    ]
    return pl.DataFrame(
        rows,
        infer_schema_length=None,
        schema_overrides={"p1_forfeit": pl.Utf8, "p2_forfeit": pl.Utf8},
    )


def decode_moves(transcript: str) -> np.ndarray:
    """A MatchResult transcript as int8[rounds, 2] move codes."""
    codes = _MOVE_CODES[np.frombuffer(transcript.encode("ascii"), np.uint8)]
    if codes.size % 2 or np.any(codes < 0):
        raise ValueError(f"not a match transcript: {transcript[:20]!r}...")
    return codes.reshape(-1, 2)


def _rounds_frame(batch: Batch, ids: range) -> pl.DataFrame:
    moves = [decode_moves(m.result.moves) for m in batch.matches]
    lengths = [len(x) for x in moves]
    stacked = np.concatenate(moves) if moves else np.zeros((0, 2), np.int8)
    return pl.DataFrame(
        {
            "match_id": np.repeat(np.array(ids, np.int64), lengths),
            "round": np.concatenate([np.arange(n, dtype=np.int32) for n in lengths])
            if lengths
            else np.zeros(0, np.int32),
            "p1_move": stacked[:, 0],
            "p2_move": stacked[:, 1],
        }
    )


def split_filter(split: str, holdout: float) -> str:
    """The SQL condition (on `matches`) selecting a split."""
    if split not in SPLITS:
        raise ValueError(f"unknown split {split!r} (one of {', '.join(SPLITS)})")
    if split == "all":
        return "TRUE"
    sign = "<" if split == "test" else ">="
    return f"holdout_key {sign} {float(holdout)!r}"


def last_match_id(con: duckdb.DuckDBPyConnection) -> int:
    """The newest match's id (-1 when the dataset is empty)."""
    row = con.execute("SELECT coalesce(max(match_id), -1) FROM matches").fetchone()
    return int(row[0]) if row else -1


def load(
    con: duckdb.DuckDBPyConnection, split: str, holdout: float, upto: int
) -> Sequences:
    """The matches of `split` with ids up to `upto`, as sequences, in id order."""
    where = f"{split_filter(split, holdout)} AND match_id <= {int(upto)}"
    meta = con.execute(
        f"SELECT match_id, seed, p1_label, p2_label FROM matches WHERE {where}"
        " ORDER BY match_id"
    ).fetchnumpy()
    moves = con.execute(
        "SELECT match_id, p1_move, p2_move FROM rounds"
        f" WHERE match_id IN (SELECT match_id FROM matches WHERE {where})"
        " ORDER BY match_id, round"
    ).fetchnumpy()
    match_ids = np.asarray(meta["match_id"], np.int64)
    labels, index = np.unique(
        np.concatenate([np.asarray(meta["p1_label"]), np.asarray(meta["p2_label"])]),
        return_inverse=True,
    )
    m = match_ids.size
    owner = np.asarray(moves["match_id"], np.int64)
    return Sequences(
        match_ids=match_ids,
        seeds=np.asarray(meta["seed"], np.int64),
        starts=np.searchsorted(owner, np.append(match_ids, upto + 1)).astype(np.int64),
        p1=np.asarray(moves["p1_move"], np.int64),
        p2=np.asarray(moves["p2_move"], np.int64),
        p1_index=index[:m].astype(np.int64),
        p2_index=index[m:].astype(np.int64),
        labels=[str(x) for x in labels],
    )


def summary(con: duckdb.DuckDBPyConnection, holdout: float) -> dict[str, object]:
    """Totals: matches, rounds, batches, players, and the test split's share."""
    row = con.execute(
        "SELECT count(*), coalesce(sum(rounds_played), 0), count(DISTINCT batch_id),"
        f" coalesce(sum(CAST({split_filter('test', holdout)} AS INTEGER)), 0),"
        " min(played_at), max(played_at)"
        " FROM matches"
    ).fetchone()
    if row is None:
        raise RuntimeError("the matches table returned no row")
    return {
        "matches": int(row[0]),
        "rounds": int(row[1]),
        "batches": int(row[2]),
        "test_matches": int(row[3]),
        "first": row[4],
        "last": row[5],
    }


def players(con: duckdb.DuckDBPyConnection) -> list[tuple[str, int, int, int]]:
    """Each player label: (label, matches, rounds played, invalid moves)."""
    rows = con.execute(
        f"""
        WITH invalid AS (
            SELECT match_id,
                   count(*) FILTER (WHERE p1_move = {INVALID}) AS p1,
                   count(*) FILTER (WHERE p2_move = {INVALID}) AS p2
            FROM rounds GROUP BY match_id
        ), sides AS (
            SELECT m.p1_label AS label, m.rounds_played, coalesce(i.p1, 0) AS bad
            FROM matches m LEFT JOIN invalid i USING (match_id)
            UNION ALL
            SELECT m.p2_label, m.rounds_played, coalesce(i.p2, 0)
            FROM matches m LEFT JOIN invalid i USING (match_id)
        )
        SELECT label, count(*), sum(rounds_played), sum(bad)
        FROM sides GROUP BY label ORDER BY label
        """
    ).fetchall()
    return [(str(r[0]), int(r[1]), int(r[2]), int(r[3])) for r in rows]
