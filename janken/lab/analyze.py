"""Analysis of stored experiments: per run, across runs, and between candidates.

The headline number is a bot's **match score**, (wins + ½ draws) / matches,
since ratings come only from who won each match. A score is given with a
95% Wilson interval (draws count as half a success, a slight
approximation). The candidates' score is reported against the *pool* only,
so candidates playing each other don't blur it. Glicko-2 ratings are
computed per round robin, the way `run` rates a tournament, then averaged
(± SD across round robins).

Candidate vs candidate is a **paired** comparison: in one run both played the
same pool bots on the same round robins, so we bootstrap the mean per-match
score difference over those shared (round robin, opponent) units.
"""

import math

import numpy as np
import polars as pl

from .. import rating
from ..match import MatchResult
from .runs_db import COMPLETE, UNKNOWN_LIBRARY, RunStore

Z95 = 1.959964


def wilson(score: float, n: int, z: float = Z95):
    if n == 0:
        return (float("nan"), float("nan"))
    denom = 1 + z * z / n
    centre = score + z * z / (2 * n)
    half = z * math.sqrt(max(score * (1 - score), 0.0) / n + z * z / (4 * n * n))
    return ((centre - half) / denom, (centre + half) / denom)


def long_form(df: pl.DataFrame) -> pl.DataFrame:
    """One row per (match, side): bot, opp, result in {1, 0.5, 0}, round diff."""

    def side(me, them):
        f_me, f_them = pl.col("forfeit_" + me), pl.col("forfeit_" + them)
        w_me, w_them = pl.col("wins_" + me), pl.col("wins_" + them)
        result = (
            pl.when(f_me.is_not_null() & f_them.is_null())
            .then(0.0)
            .when(f_them.is_not_null() & f_me.is_null())
            .then(1.0)
            .when(f_me.is_not_null() & f_them.is_not_null())
            .then(0.5)
            .when(w_me > w_them)
            .then(1.0)
            .when(w_me < w_them)
            .then(0.0)
            .otherwise(0.5)
        )
        return df.select(
            pl.col("run_id"),
            pl.col("rounds"),
            pl.col("rr"),
            pl.col("k"),
            pl.col("bot_" + me).alias("bot"),
            pl.col("stem_" + me).alias("stem"),
            pl.col("bot_" + them).alias("opp"),
            pl.col("stem_" + them).alias("opp_stem"),
            pl.col("cand_" + me).alias("is_cand"),
            pl.col("cand_" + them).alias("opp_cand"),
            result.alias("result"),
            (w_me - w_them).alias("diff"),
            f_me.is_not_null().alias("forfeit"),
        )

    return pl.concat([side("a", "b"), side("b", "a")])


def _record(lf: pl.DataFrame, by: list[str]) -> pl.DataFrame:
    return lf.group_by(by).agg(
        pl.len().alias("n"),
        (pl.col("result") == 1.0).sum().alias("W"),
        (pl.col("result") == 0.5).sum().alias("D"),
        (pl.col("result") == 0.0).sum().alias("L"),
        pl.col("result").mean().alias("score"),
        pl.col("diff").mean().alias("diff"),
        pl.col("forfeit").sum().alias("forfeits"),
    )


def _rows_with_ci(table: pl.DataFrame) -> list[dict]:
    out = []
    for r in table.iter_rows(named=True):
        lo, hi = wilson(r["score"], r["n"])
        out.append({**r, "ci_lo": lo, "ci_hi": hi})
    return out


def ratings_per_rr(df: pl.DataFrame) -> dict[str, list[float]]:
    """{bot: [Glicko-2 rating in each round robin it played]}."""
    out: dict[str, list[float]] = {}
    for (_rr,), part in df.group_by(["rr"], maintain_order=True):
        matches = [
            MatchResult(
                bot_a=r["bot_a"],
                bot_b=r["bot_b"],
                wins_a=r["wins_a"],
                wins_b=r["wins_b"],
                draws=r["draws"],
                forfeit_a=r["forfeit_a"],
                forfeit_b=r["forfeit_b"],
            )
            for r in part.iter_rows(named=True)
        ]
        ratings, _ = rating.rate_tournament(matches)
        for bot, change in ratings.items():
            out.setdefault(bot, []).append(change.after)
    return out


def paired_diff(
    lf: pl.DataFrame,
    a: str,
    b: str,
    reps: int = 4000,
    seed: int = 0,
    level: float = 0.95,
):
    """Mean of score(a) - score(b) over shared (rr, pool opponent) units, with a
    bootstrap CI at `level` (95% by default); None if they share no opponents."""
    pool = lf.filter(~pl.col("opp_cand"))
    sa = pool.filter(pl.col("bot") == a).select(
        "rr", "opp", pl.col("result").alias("ra")
    )
    sb = pool.filter(pl.col("bot") == b).select(
        "rr", "opp", pl.col("result").alias("rb")
    )
    joined = sa.join(sb, on=["rr", "opp"])
    if joined.height == 0:
        return None
    d = (joined["ra"] - joined["rb"]).to_numpy()
    rng = np.random.default_rng(seed)
    boots = d[rng.integers(0, d.size, (reps, d.size))].mean(axis=1)
    tail = (1 - level) / 2
    lo, hi = np.quantile(boots, [tail, 1 - tail])
    return {
        "a": a,
        "b": b,
        "n": int(d.size),
        "mean": float(d.mean()),
        "ci_lo": float(lo),
        "ci_hi": float(hi),
    }


def summarize(manifest: dict, df: pl.DataFrame) -> dict:
    lf = long_form(df)
    cands = [c["label"] for c in manifest["candidates"]]
    rr_ratings = ratings_per_rr(df)

    def rated(rows):
        for r in rows:
            xs = rr_ratings.get(r["bot"], [])
            r["rating"] = float(np.mean(xs)) if xs else None
            r["rating_sd"] = float(np.std(xs, ddof=1)) if len(xs) > 1 else None
        return rows

    vs_pool = _rows_with_ci(
        _record(lf.filter(pl.col("is_cand") & ~pl.col("opp_cand")), ["bot"]).sort(
            "score", descending=True
        )
    )
    field = _rows_with_ci(_record(lf, ["bot"]).sort("score", descending=True))
    matchups = {}
    for c in cands:
        t = _record(lf.filter((pl.col("bot") == c) & ~pl.col("opp_cand")), ["opp_stem"])
        matchups[c] = _rows_with_ci(t.sort(["score", "diff"]))
    h2h = []
    comparisons = []
    for i, a in enumerate(cands):
        for b in cands[i + 1 :]:
            rec = _record(
                lf.filter((pl.col("bot") == a) & (pl.col("opp") == b)), ["bot"]
            )
            if rec.height:
                h2h.append({"a": a, "b": b, **_rows_with_ci(rec)[0]})
            cmp = paired_diff(lf, a, b)
            if cmp:
                comparisons.append(cmp)
    return {
        "run_id": manifest["run_id"],
        "config": manifest["config"],
        "round_robins_played": int(df["rr"].n_unique()),
        "candidates": cands,
        "candidates_vs_pool": rated(vs_pool),
        "field": rated(field),
        "matchups": matchups,
        "head_to_head": h2h,
        "comparisons": comparisons,
    }


# --- formatting ----------------------------------------------------------------


def _pct(x):
    return (
        "—"
        if x is None or (isinstance(x, float) and math.isnan(x))
        else "%.1f%%" % (100 * x)
    )


def _num(x, fmt="%.0f"):
    return "—" if x is None else fmt % x


def _md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


def _record_row(r, name_key="bot"):
    return [
        r[name_key],
        r["n"],
        "{}-{}-{}".format(r["W"], r["D"], r["L"]),
        "{} [{}, {}]".format(_pct(r["score"]), _pct(r["ci_lo"]), _pct(r["ci_hi"])),
        "{:+.1f}".format(r["diff"]),
        r["forfeits"],
    ]


def render(summary: dict, worst: int = 6) -> str:
    cfg = summary["config"]
    out = [
        "# Experiment {}".format(summary["run_id"]),
        "",
        "{} round robin(s) · pool {} · {} rounds/match · seed {} · mode {}".format(
            cfg["round_robins"],
            cfg["pool_size"],
            cfg["rounds"],
            cfg["seed"],
            cfg["mode"],
        ),
        "",
    ]
    played = summary.get("round_robins_played", cfg["round_robins"])
    if summary.get("status", COMPLETE) != COMPLETE or played < cfg["round_robins"]:
        out += [
            "**Partial: {} of {} round robins played (run {}).**".format(
                played, cfg["round_robins"], summary.get("status", "incomplete")
            ),
            "",
        ]
    out += ["## Candidates vs pool", ""]
    out.append(
        _md_table(
            [
                "bot",
                "n",
                "W-D-L",
                "score [95% CI]",
                "rounds +/- per match",
                "forfeits",
                "rating ± sd",
            ],
            [
                _record_row(r)
                + ["{} ± {}".format(_num(r["rating"]), _num(r["rating_sd"]))]
                for r in summary["candidates_vs_pool"]
            ],
        )
    )
    if summary["comparisons"]:
        out += ["", "## Paired comparisons (same pool matches)", ""]
        out.append(
            _md_table(
                ["a", "b", "shared", "score(a) − score(b) [95% CI]", "verdict"],
                [
                    [
                        c["a"],
                        c["b"],
                        c["n"],
                        "{:+.1f} pts [{:+.1f}, {:+.1f}]".format(
                            100 * c["mean"], 100 * c["ci_lo"], 100 * c["ci_hi"]
                        ),
                        (
                            "a better"
                            if c["ci_lo"] > 0
                            else "b better"
                            if c["ci_hi"] < 0
                            else "no significant difference"
                        ),
                    ]
                    for c in summary["comparisons"]
                ],
            )
        )
    if summary["head_to_head"]:
        out += ["", "## Head to head", ""]
        out.append(
            _md_table(
                [
                    "a vs b",
                    "n",
                    "W-D-L (a)",
                    "score(a) [95% CI]",
                    "rounds +/- per match",
                    "forfeits",
                ],
                [
                    ["{} vs {}".format(h["a"], h["b"])] + _record_row(h)[1:]
                    for h in summary["head_to_head"]
                ],
            )
        )
    for cand, rows in summary["matchups"].items():
        out += ["", f"## {cand}: matchups, weakest first", ""]
        shown = rows if len(rows) <= 2 * worst else rows[:worst] + rows[-worst:]
        out.append(
            _md_table(
                [
                    "opponent",
                    "n",
                    "W-D-L",
                    "score [95% CI]",
                    "rounds +/- per match",
                    "forfeits",
                ],
                [_record_row(r, "opp_stem") for r in shown],
            )
        )
        if len(rows) > 2 * worst:
            out.append(
                f"\n({len(rows) - 2 * worst} middle matchups omitted; see the summary"
                " in the runs database's `reports` table)"
            )
    out += ["", "## Whole field (every match, incl. pool vs pool)", ""]
    out.append(
        _md_table(
            [
                "bot",
                "n",
                "W-D-L",
                "score [95% CI]",
                "rounds +/- per match",
                "forfeits",
                "rating ± sd",
            ],
            [
                _record_row(r)
                + ["{} ± {}".format(_num(r["rating"]), _num(r["rating_sd"]))]
                for r in summary["field"]
            ],
        )
    )
    return "\n".join(out) + "\n"


def analyze_run(ref: str, root: str | None = None, write: bool = True) -> dict:
    """Summarize the run `ref` resolves to (finished or not) and, with `write`,
    store its report.

    Raises:
        SystemExit: the run has no match stored yet.
    """
    runs = RunStore.at(root or "")
    run_id, manifest, df = runs.load_run(ref)
    if not df.height:
        raise SystemExit(f"run {run_id} has no round robin stored yet")
    summary = summarize(manifest, df)
    summary["status"] = runs.status(run_id)
    if write:
        runs.save_report(run_id, summary, render(summary))
    return summary


# --- across runs ----------------------------------------------------------------


def _sql_long(src: str = "matches") -> str:
    side = """SELECT run_id, rounds, rr, bot_{m} AS bot, stem_{m} AS stem, bot_{t} AS opp,
                     cand_{m} AS is_cand, cand_{t} AS opp_cand,
                     CASE WHEN forfeit_{m} IS NOT NULL AND forfeit_{t} IS NULL THEN 0.0
                          WHEN forfeit_{t} IS NOT NULL AND forfeit_{m} IS NULL THEN 1.0
                          WHEN forfeit_{m} IS NOT NULL THEN 0.5
                          WHEN wins_{m} > wins_{t} THEN 1.0
                          WHEN wins_{m} < wins_{t} THEN 0.0 ELSE 0.5 END AS result,
                     wins_{m} - wins_{t} AS diff
              FROM {src}"""
    return "({} UNION ALL {})".format(
        side.format(m="a", t="b", src=src),
        side.format(m="b", t="a", src=src),
    )


def _stored(root: str | None) -> RunStore:
    runs = RunStore.at(root or "")
    if not runs.run_ids():
        raise SystemExit(f"no stored runs in {runs.path}")
    return runs


def history(stem: str, root: str | None = None) -> pl.DataFrame:
    """Every stored run in which `stem` (or a variant of it) was a candidate:
    its score vs the pool, per run."""
    runs = _stored(root)
    df = runs.query(
        f"""
        SELECT run_id, bot, any_value(rounds) AS rounds, count(*) AS n,
               avg(result) AS score, avg(diff) AS diff
        FROM {_sql_long()} WHERE is_cand AND NOT opp_cand AND stem = ?
        GROUP BY run_id, bot ORDER BY run_id, score DESC""",
        [stem],
    )
    libraries = run_libraries(root)
    df = df.with_columns(
        pl.Series(
            "library",
            [libraries.get(r, UNKNOWN_LIBRARY) for r in df["run_id"]],
            dtype=pl.Utf8,
        )
    )
    return _with_ci(df)


def run_libraries(root: str | None = None) -> dict[str, str]:
    """{run id: hash of the kit + engine it ran on}. Runs from before the hash was
    recorded (the pre-blueprint bots) are UNKNOWN_LIBRARY. Scores from runs on
    different libraries may come from different bot code under the same name."""
    runs = RunStore.at(root or "")
    if not runs.exists():
        return {}
    frame = runs.query("SELECT run_id, library FROM runs")
    return {str(r): str(lib) for r, lib in zip(frame["run_id"], frame["library"])}


def leaderboard(root: str | None = None, rounds: int | None = None) -> pl.DataFrame:
    """Every candidate label ever tested, pooled over runs: score vs pool."""
    runs = _stored(root)
    where = "is_cand AND NOT opp_cand" + (f" AND rounds = {rounds:d}" if rounds else "")
    df = runs.query(
        f"""
        SELECT bot, count(DISTINCT run_id) AS runs, count(*) AS n,
               avg(result) AS score, avg(diff) AS diff
        FROM {_sql_long()} WHERE {where} GROUP BY bot ORDER BY score DESC"""
    )
    params = candidate_params(root)
    df = df.with_columns(
        pl.Series("params", [params.get(b, "") for b in df["bot"]], dtype=pl.Utf8)
    )
    return _with_ci(df)


def candidate_params(root: str | None = None) -> dict[str, str]:
    """{label: "NAME=value ..."} for every candidate in the stored manifests."""
    out = {}
    for manifest in RunStore.at(root or "").manifests():
        for c in manifest["candidates"]:
            out[c["label"]] = " ".join(
                "{}={}".format(*kv) for kv in sorted(c["params"].items())
            )
    return out


def _with_ci(df: pl.DataFrame) -> pl.DataFrame:
    if df.height == 0:
        return df
    ci = [wilson(s, n) for s, n in zip(df["score"], df["n"])]
    return df.with_columns(
        pl.Series("ci_lo", [c[0] for c in ci]), pl.Series("ci_hi", [c[1] for c in ci])
    )


def render_frame(df: pl.DataFrame) -> str:
    if df.height == 0:
        return "(nothing stored yet)"
    rows = []
    for r in df.iter_rows(named=True):
        row = []
        for k, v in r.items():
            if k in ("score", "ci_lo", "ci_hi"):
                row.append(_pct(v))
            elif k == "diff":
                row.append(f"{v:+.1f}")
            else:
                row.append(str(v))
        rows.append(row)
    return _md_table(list(df.columns), rows)


# --- stored runs and validations -----------------------------------------------


def list_runs(root: str | None = None) -> pl.DataFrame:
    """Every stored run, oldest first (runs_db.RunStore.runs)."""
    return RunStore.at(root or "").runs()


def run_progress(run: dict) -> str:
    """A run's status, with how much of it is stored when it isn't complete."""
    if run["status"] == COMPLETE:
        return COMPLETE
    return "{} ({}/{} round robins)".format(
        run["status"], run["rrs_played"], run["round_robins"]
    )


def render_runs(frame: pl.DataFrame) -> str:
    if not frame.height:
        return "(no runs stored yet)"
    return _md_table(
        ["run", "status", "rounds", "matches"],
        [
            [
                r["run_id"],
                run_progress(r),
                r["rounds"],
                f"{r['played']}/{r['n_matches']}",
            ]
            for r in frame.iter_rows(named=True)
        ],
    )


def render_validations(study: str, root: str | None = None) -> str:
    """Every recorded validation of `study` (tune and predict-tune)."""
    runs = RunStore.at(root or "")
    out = [f"Validations of study {study}:", ""]
    tuned = runs.validations("tune_validations", study)
    if tuned.height:
        out.append(
            _md_table(
                [
                    "validated",
                    "run",
                    "champion",
                    "trial",
                    "train",
                    "n",
                    "score vs pool [95% CI]",
                    "vs defaults [95% CI]",
                ],
                [
                    [
                        r["validated_at"],
                        r["run_id"],
                        r["champion"],
                        r["trial"],
                        _pct(r["train_value"]),
                        r["n"],
                        "{} [{}, {}]".format(
                            _pct(r["score"]), _pct(r["ci_lo"]), _pct(r["ci_hi"])
                        ),
                        "{:+.1f} pts [{:+.1f}, {:+.1f}]".format(
                            100 * r["vs_defaults"],
                            100 * r["vs_defaults_lo"],
                            100 * r["vs_defaults_hi"],
                        ),
                    ]
                    for r in tuned.iter_rows(named=True)
                ],
            )
        )
    predicted = runs.validations("predict_validations", study)
    if predicted.height:
        out.append(
            _md_table(
                [
                    "validated",
                    "predictor",
                    "trial",
                    "train",
                    "split",
                    "n",
                    "accuracy",
                    "macro F1",
                    "kappa",
                    "edge",
                ],
                [
                    [
                        r["validated_at"],
                        r["config"],
                        r["trial"],
                        "—"
                        if math.isnan(r["train_value"])
                        else f"{r['train_value']:.4f}",
                        r["split"],
                        r["n"],
                        f"{r['accuracy']:.4f}",
                        f"{r['macro_f1']:.4f}",
                        f"{r['kappa']:.4f}",
                        f"{r['edge']:+.4f}",
                    ]
                    for r in predicted.iter_rows(named=True)
                ],
            )
        )
    if not (tuned.height or predicted.height):
        out.append("(no validation recorded for this study)")
    return "\n".join(out)


# --- a note's results ----------------------------------------------------------


def comparison_text(c: dict) -> str:
    """`a − b = +x.x pts [lo, hi]` and its verdict."""
    verdict = (
        "a better"
        if c["ci_lo"] > 0
        else "b better"
        if c["ci_hi"] < 0
        else "no significant difference"
    )
    return (
        "`{} − {} = {:+.1f} pts [{:+.1f}, {:+.1f}]` over {} shared matches: {}".format(
            c["a"],
            c["b"],
            100 * c["mean"],
            100 * c["ci_lo"],
            100 * c["ci_hi"],
            c["n"],
            verdict.replace("a better", f"{c['a']} better").replace(
                "b better", f"{c['b']} better"
            ),
        )
    )


def render_brief(summary: dict, worst: int = 6) -> str:
    """A run's results for its note: candidates vs pool, paired comparisons, and
    each candidate's weakest matchups."""
    cfg = summary["config"]
    out = [
        "{} of {} round robin(s) · pool {} · {} rounds/match · seed {} · mode {}".format(
            summary.get("round_robins_played", cfg["round_robins"]),
            cfg["round_robins"],
            cfg["pool_size"],
            cfg["rounds"],
            cfg["seed"],
            cfg["mode"],
        ),
        "",
        _md_table(
            [
                "bot",
                "n",
                "W-D-L",
                "score vs pool [95% CI]",
                "rounds +/-",
                "forfeits",
                "rating ± sd",
            ],
            [
                _record_row(r)
                + ["{} ± {}".format(_num(r["rating"]), _num(r["rating_sd"]))]
                for r in summary["candidates_vs_pool"]
            ],
        ),
    ]
    if summary["comparisons"]:
        out += ["", "Paired comparisons:", ""]
        out += [f"- {comparison_text(c)}" for c in summary["comparisons"]]
    for cand, rows in summary["matchups"].items():
        weakest = ", ".join(
            "{} {}".format(r["opp_stem"], _pct(r["score"])) for r in rows[:worst]
        )
        out += ["", f"Weakest matchups of {cand}: {weakest}."]
    return "\n".join(out)


def significant(summary: dict) -> list[dict]:
    """The paired comparisons whose 95% CI excludes 0."""
    return [c for c in summary["comparisons"] if c["ci_lo"] > 0 or c["ci_hi"] < 0]
