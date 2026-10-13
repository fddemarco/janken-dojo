"""DuckDB helpers shared by the move dataset and the runs database."""

import os
import tempfile
from collections.abc import Sequence

import duckdb
import polars as pl


def insert_frame(
    con: duckdb.DuckDBPyConnection,
    table: str,
    frame: pl.DataFrame,
    on_conflict_ignore: bool = False,
) -> None:
    """Append `frame` to `table`, by column name, through a parquet file; with
    `on_conflict_ignore`, rows whose primary key is already there are skipped."""
    verb = "INSERT OR IGNORE" if on_conflict_ignore else "INSERT"
    with tempfile.TemporaryDirectory(prefix="janken-duck-") as tmp:
        path = os.path.join(tmp, f"{table}.parquet")
        frame.write_parquet(path)
        con.execute(
            f"{verb} INTO {table} BY NAME SELECT * FROM read_parquet(?)", [path]
        )


def fetch_frame(
    con: duckdb.DuckDBPyConnection, sql: str, params: Sequence[object] = ()
) -> pl.DataFrame:
    """A query's result as a polars frame (built from rows: no pyarrow needed)."""
    rel = con.execute(sql, list(params))
    columns = [d[0] for d in rel.description or []]
    return pl.DataFrame(
        rel.fetchall(), schema=columns, orient="row", infer_schema_length=None
    )
