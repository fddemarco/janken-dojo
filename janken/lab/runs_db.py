"""The runs database: every experiment run, its matches, reports and validations.

One DuckDB file, `[tool.janken.runs] file` in the experiments directory:

    runs               one row per run: its status, setup and manifest (JSON)
    matches            one row per match (MATCH_SCHEMA), tagged with its run_id
    reports            the latest analysis of a run: summary (JSON) and report
    tune_validations   one row per configuration a `tune --validate-top` replayed
    predict_validations  one row per configuration `predict-tune --validate-top` scored

A run is created `running` with its whole manifest, and every round robin is
committed in its own transaction as soon as it's played, so a run is analyzable
while it plays and keeps what it played when it's interrupted (status
`interrupted`; `janken lab resume` plays the rest).

Every operation opens the file, does its work and closes it, so processes share
the file: one that finds it locked retries for `[tool.janken.runs]
lock_timeout_s` seconds.
"""

import contextlib
import datetime
import json
import os
import re
import time
from collections.abc import Generator, Mapping, Sequence

import duckdb
import polars as pl

from .. import settings
from . import duck, store

RUNNING, COMPLETE, INTERRUPTED = "running", "complete", "interrupted"

MATCH_SCHEMA = {
    "run_id": pl.Utf8,
    "rounds": pl.Int64,
    "rr": pl.Int64,
    "k": pl.Int64,
    "bot_a": pl.Utf8,
    "bot_b": pl.Utf8,
    "stem_a": pl.Utf8,
    "stem_b": pl.Utf8,
    "cand_a": pl.Boolean,
    "cand_b": pl.Boolean,
    "seed": pl.Int64,
    "wins_a": pl.Int64,
    "wins_b": pl.Int64,
    "draws": pl.Int64,
    "forfeit_a": pl.Utf8,
    "forfeit_b": pl.Utf8,
    "moves": pl.Utf8,
}

UNKNOWN_LIBRARY = "pre-blueprint"  # runs from before the library hash was recorded

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    created TIMESTAMP NOT NULL,
    status VARCHAR NOT NULL,
    rounds INTEGER NOT NULL,
    round_robins INTEGER NOT NULL,
    mode VARCHAR NOT NULL,
    seed BIGINT NOT NULL,
    library VARCHAR NOT NULL,
    study VARCHAR NOT NULL,
    n_matches BIGINT NOT NULL,
    elapsed_s DOUBLE NOT NULL,
    manifest JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS matches (
    run_id VARCHAR NOT NULL,
    rounds INTEGER NOT NULL,
    rr INTEGER NOT NULL,
    k INTEGER NOT NULL,
    bot_a VARCHAR NOT NULL,
    bot_b VARCHAR NOT NULL,
    stem_a VARCHAR NOT NULL,
    stem_b VARCHAR NOT NULL,
    cand_a BOOLEAN NOT NULL,
    cand_b BOOLEAN NOT NULL,
    seed BIGINT NOT NULL,
    wins_a INTEGER NOT NULL,
    wins_b INTEGER NOT NULL,
    draws INTEGER NOT NULL,
    forfeit_a VARCHAR,
    forfeit_b VARCHAR,
    moves VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS reports (
    run_id VARCHAR PRIMARY KEY,
    analyzed_at TIMESTAMP NOT NULL,
    summary JSON NOT NULL,
    report VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS tune_validations (
    study VARCHAR NOT NULL,
    validated_at TIMESTAMP NOT NULL,
    run_id VARCHAR NOT NULL,
    config VARCHAR NOT NULL,
    champion VARCHAR NOT NULL,
    trial BIGINT NOT NULL,
    train_value DOUBLE NOT NULL,
    n BIGINT NOT NULL,
    score DOUBLE NOT NULL,
    ci_lo DOUBLE NOT NULL,
    ci_hi DOUBLE NOT NULL,
    vs_defaults DOUBLE NOT NULL,
    vs_defaults_lo DOUBLE NOT NULL,
    vs_defaults_hi DOUBLE NOT NULL,
    params JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS predict_validations (
    study VARCHAR NOT NULL,
    validated_at TIMESTAMP NOT NULL,
    config VARCHAR NOT NULL,
    trial BIGINT NOT NULL,
    train_value DOUBLE NOT NULL,
    metric VARCHAR NOT NULL,
    split VARCHAR NOT NULL,
    upto_match_id BIGINT NOT NULL,
    n BIGINT NOT NULL,
    accuracy DOUBLE NOT NULL,
    macro_f1 DOUBLE NOT NULL,
    kappa DOUBLE NOT NULL,
    edge DOUBLE NOT NULL
);
"""


def default_path(root: str = "") -> str:
    """The runs database of the experiments directory `root` ("": the default)."""
    return os.path.join(root or store.EXPERIMENTS, settings.config().runs.file)


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", text).strip("-")[:60] or "run"


class RunStore:
    """The runs database at `path`, opened per operation."""

    def __init__(self, path: str, lock_timeout_s: float) -> None:
        self.path: str = path
        self.lock_timeout_s: float = lock_timeout_s

    @classmethod
    def at(cls, root: str = "") -> "RunStore":
        """The store of the experiments directory `root` ("": the default)."""
        return cls(default_path(root), settings.config().runs.lock_timeout_s)

    # --- connections -------------------------------------------------------------

    @contextlib.contextmanager
    def _connect(self, read_only: bool) -> Generator[duckdb.DuckDBPyConnection]:
        """A connection, retried while another process holds the file's lock."""
        if not read_only:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        deadline = time.monotonic() + self.lock_timeout_s
        wait = 0.05
        while True:
            try:
                con = duckdb.connect(self.path, read_only=read_only)
                break
            except duckdb.IOException as exc:
                if "lock" not in str(exc).lower() or time.monotonic() > deadline:
                    raise
                time.sleep(wait)
                wait = min(2 * wait, 1.0)
        try:
            if not read_only:
                con.execute(SCHEMA)
            yield con
        finally:
            con.close()

    @contextlib.contextmanager
    def _transaction(self) -> Generator[duckdb.DuckDBPyConnection]:
        with self._connect(read_only=False) as con:
            con.execute("BEGIN TRANSACTION")
            try:
                yield con
                con.execute("COMMIT")
            except BaseException:
                con.execute("ROLLBACK")
                raise

    def exists(self) -> bool:
        """Whether anything was ever stored (reads never create the file)."""
        return os.path.isfile(self.path)

    def query(self, sql: str, params: Sequence[object] = ()) -> pl.DataFrame:
        """Read-only SQL over the tables.

        Raises:
            SystemExit: nothing was ever stored.
        """
        if not self.exists():
            raise SystemExit(f"no runs stored yet (no {self.path})")
        with self._connect(read_only=True) as con:
            return duck.fetch_frame(con, sql, params)

    # --- writing a run -----------------------------------------------------------

    def create_run(self, name: str, manifest: dict) -> str:
        """Store a new `running` run; returns its id (also set in `manifest`)."""
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        base = f"{stamp}_{_slug(name)}"
        with self._transaction() as con:
            taken = {
                r[0]
                for r in con.execute(
                    "SELECT run_id FROM runs WHERE run_id LIKE ?", [base + "%"]
                ).fetchall()
            }
            run_id, n = base, 1
            while run_id in taken:
                n += 1
                run_id = f"{base}-{n:d}"
            manifest["run_id"] = run_id
            self._insert_run(con, manifest, RUNNING, elapsed_s=0.0)
        return run_id

    def _insert_run(
        self,
        con: duckdb.DuckDBPyConnection,
        manifest: Mapping[str, object],
        status: str,
        elapsed_s: float,
    ) -> None:
        config = manifest["config"]
        if not isinstance(config, dict):
            raise TypeError("a manifest's config must be a mapping")
        tuning = manifest.get("tuning", {})
        con.execute(
            "INSERT INTO runs VALUES (?, ?, CAST(? AS TIMESTAMP), ?, ?, ?, ?, ?, ?, ?,"
            " ?, ?, ?)",
            [
                manifest["run_id"],
                manifest.get("name") or "",
                manifest["created"],
                status,
                config["rounds"],
                config["round_robins"],
                config.get("mode", "full"),
                config["seed"],
                manifest.get("library", UNKNOWN_LIBRARY),
                tuning.get("study", "") if isinstance(tuning, dict) else "",
                manifest["n_matches"],
                elapsed_s,
                json.dumps(manifest, default=str),
            ],
        )

    def retarget(self, run_id: str, manifest: Mapping[str, object]) -> None:
        """Replace a run's manifest (a grown schedule) and its target size."""
        config = manifest["config"]
        if not isinstance(config, dict):
            raise TypeError("a manifest's config must be a mapping")
        with self._transaction() as con:
            con.execute(
                "UPDATE runs SET round_robins = ?, n_matches = ?, manifest = ?"
                " WHERE run_id = ?",
                [
                    config["round_robins"],
                    manifest["n_matches"],
                    json.dumps(manifest, default=str),
                    run_id,
                ],
            )

    def append_matches(self, rows: Sequence[Mapping[str, object]]) -> None:
        """Commit a batch of match rows (MATCH_SCHEMA), in one transaction."""
        if not rows:
            return
        frame = pl.DataFrame(rows, schema=MATCH_SCHEMA)
        with self._transaction() as con:
            duck.insert_frame(con, "matches", frame)

    def finish(self, run_id: str, status: str, elapsed_s: float) -> None:
        """Set a run's status and add `elapsed_s` to its playing time."""
        with self._transaction() as con:
            con.execute(
                "UPDATE runs SET status = ?, elapsed_s = elapsed_s + ? WHERE run_id = ?",
                [status, elapsed_s, run_id],
            )

    def save_report(
        self, run_id: str, summary: Mapping[str, object], report: str
    ) -> None:
        """Store a run's latest analysis, replacing any earlier one."""
        with self._transaction() as con:
            con.execute("DELETE FROM reports WHERE run_id = ?", [run_id])
            con.execute(
                "INSERT INTO reports VALUES (?, CAST(? AS TIMESTAMP), ?, ?)",
                [run_id, _now(), json.dumps(summary, default=str), report],
            )

    def add_validations(self, table: str, rows: Sequence[Mapping[str, object]]) -> None:
        """Append validation rows to `tune_validations` or `predict_validations`."""
        if table not in ("tune_validations", "predict_validations"):
            raise ValueError(f"not a validations table: {table!r}")
        if not rows:
            return
        frame = pl.DataFrame(
            [{"validated_at": _now(), **r} for r in rows], infer_schema_length=None
        ).with_columns(pl.col("validated_at").str.to_datetime())
        with self._transaction() as con:
            duck.insert_frame(con, table, frame)

    # --- reading -----------------------------------------------------------------

    def runs(self) -> pl.DataFrame:
        """Every run, oldest first, with how many round robins it has stored."""
        if not self.exists():
            return pl.DataFrame()
        return self.query(
            """SELECT r.run_id, r.name, r.created, r.status, r.rounds, r.round_robins,
                      r.n_matches, coalesce(m.played, 0) AS played,
                      coalesce(m.rrs, 0) AS rrs_played, r.library, r.study
               FROM runs r LEFT JOIN (
                   SELECT run_id, count(*) AS played, count(DISTINCT rr) AS rrs
                   FROM matches GROUP BY run_id) m USING (run_id)
               ORDER BY r.run_id"""
        )

    def run_ids(self) -> list[str]:
        """Every run id, oldest first."""
        if not self.exists():
            return []
        frame = self.query("SELECT run_id FROM runs ORDER BY run_id")
        return [str(r) for r in frame["run_id"]]

    def resolve(self, ref: str) -> str:
        """A run id from an id, a unique id prefix/substring, or 'latest'."""
        runs = self.run_ids()
        if not runs:
            raise SystemExit(f"no runs stored in {self.path}")
        if ref == "latest":
            return runs[-1]
        hits = [r for r in runs if r == ref] or [r for r in runs if ref in r]
        if len(hits) != 1:
            raise SystemExit(
                "{} run matches {!r}{}".format(
                    "no" if not hits else "more than one",
                    ref,
                    "" if not hits else ": " + ", ".join(hits),
                )
            )
        return hits[0]

    def manifest(self, run_id: str) -> dict:
        frame = self.query("SELECT manifest FROM runs WHERE run_id = ?", [run_id])
        if not frame.height:
            raise SystemExit(f"no run {run_id!r}")
        return json.loads(frame["manifest"][0])

    def status(self, run_id: str) -> str:
        frame = self.query("SELECT status FROM runs WHERE run_id = ?", [run_id])
        return str(frame["status"][0])

    def manifests(self) -> list[dict]:
        """Every run's manifest, oldest first."""
        if not self.exists():
            return []
        frame = self.query("SELECT manifest FROM runs ORDER BY run_id")
        return [json.loads(m) for m in frame["manifest"]]

    def matches(self, run_id: str) -> pl.DataFrame:
        """A run's matches (MATCH_SCHEMA), in schedule order."""
        frame = self.query(
            "SELECT {} FROM matches WHERE run_id = ? ORDER BY rr, k".format(
                ", ".join(MATCH_SCHEMA)
            ),
            [run_id],
        )
        return pl.DataFrame(frame.to_dicts(), schema=MATCH_SCHEMA)

    def load_run(self, ref: str) -> tuple[str, dict, pl.DataFrame]:
        """(run id, manifest, matches) of the run `ref` resolves to."""
        run_id = self.resolve(ref)
        return run_id, self.manifest(run_id), self.matches(run_id)

    def played_round_robins(self, run_id: str) -> set[int]:
        frame = self.query("SELECT DISTINCT rr FROM matches WHERE run_id = ?", [run_id])
        return {int(r) for r in frame["rr"]}

    def summaries(self) -> dict[str, dict]:
        """{run id: its latest summary}."""
        if not self.exists():
            return {}
        frame = self.query("SELECT run_id, summary FROM reports")
        return {
            str(r): json.loads(s) for r, s in zip(frame["run_id"], frame["summary"])
        }

    def validations(self, table: str, study: str) -> pl.DataFrame:
        """A study's validation rows, oldest first."""
        if not self.exists():
            return pl.DataFrame()
        if table not in ("tune_validations", "predict_validations"):
            raise ValueError(f"not a validations table: {table!r}")
        return self.query(
            f"SELECT * FROM {table} WHERE study = ? ORDER BY validated_at, trial",
            [study],
        )


def _now() -> str:
    return datetime.datetime.now().replace(microsecond=0).isoformat(sep=" ")
