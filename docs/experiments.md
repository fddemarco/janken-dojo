# Experiments and analysis

An **experiment** asks how a bot (a *candidate*) does against bots it wasn't written for.
It plays the candidates against several randomly drawn pools, stores every match, and
analyzes the run. This is the lab's evidence; a single [tournament](tournaments.md) is
too noisy to decide anything.

## How an experiment is played

- **Pools.** Each **round robin** draws a fresh pool of `--pool-size` bots from the bots
  dir, leaving out the candidates' stems, and plays the pool and the candidates.
  - `evaluation.mode = full`: every pair plays.
  - `candidates`: only the matches with a candidate.
- **Paired comparisons.** Every candidate meets a given pool bot **with the same match
  seed** (common random numbers), so candidates in the same run get a **paired**
  comparison: differences between them come from their play, not the draw. Put the bot to
  beat in the same run, as a `--baseline`.
- **Seeds.** `--seed` reproduces a run. `-1` (the default) draws a fresh seed and records
  it.
- **Effort.** `--effort` sets how many round robins: `quick` 2, `standard` 10 (a score CI
  of about ±6 pts), `thorough` 40 (about ±3 pts). `--round-robins` overrides it.

## With a note: `janken evaluate`

```bash
uv run janken evaluate bots/l2/new.yaml --baseline bots/l2/old.yaml \
  --hypothesis "new beats old by >= 2 pts, mostly vs the metabots" --idea 7
uv run janken evaluate --note 0007        # run a planned note, or resume a cut one
uv run janken verdict 0007 keep --summary "+3.1 pts [+0.8, +5.4] vs old ..."
```

`evaluate` does four things:

1. writes `research/experiments/NNNN-<name>.md` with the hypothesis (status `planned`);
1. plays the run;
1. analyzes it;
1. writes the reproducible low-level command and the results into the note (status
   `run`).

The results are the candidates vs the pool, the paired comparisons and the weakest
matchups. `verdict` closes the note.

## Without a note: `janken lab …`

```bash
uv run janken lab experiment bots/l1/a.yaml bots/l1/a.yaml:DECAY=0.8 --effort thorough
uv run janken lab resume 20261010-144016          # finish an interrupted run
uv run janken lab report latest                    # a run's full report
uv run janken lab runs                             # every run, with its status
uv run janken lab history smartbot_sims              # a bot across runs
uv run janken lab leaderboard --rounds 200         # every candidate, pooled
uv run janken lab query "SELECT run_id, status FROM runs"
```

### Reading a report

A run's report gives, per bot:

- the match score with a 95% Wilson CI;
- the Glicko-2 rating across the round robins;
- the weakest matchups;
- the **paired comparisons** between candidates, with bootstrap CIs.

A comparison whose CI excludes 0 is a real difference. One that straddles 0 is not
evidence. A run that isn't complete is analyzed on what it holds, and its report says
so.

## Where runs are stored

Every run lives in one DuckDB file in the workspace, `experiments/runs.duckdb` (settings
under `runs` in `janken.toml`):

| table | one row per |
| --- | --- |
| `runs` | run: id, name, status, rounds, round robins, seed, kit/engine version, study, the full manifest (JSON) |
| `matches` | match, tagged with its `run_id` and round robin `rr`, with the move transcript (`moves`) |
| `reports` | run: its latest analysis (summary JSON and markdown report) |
| `tune_validations`, `predict_validations` | validated configuration ([Tuning](tuning.md#validation)) |

- **Saved as it plays.** A run is stored (`running`) before it plays, and each round
  robin is committed as soon as it's played.
  - You can analyze a run while it plays.
  - A run stopped by Ctrl-C or a crash keeps its finished round robins and becomes
    `interrupted`.
- **Resume.** `lab resume` (or `evaluate --note`) plays only the missing round robins.
  The rebuilt schedule makes the result identical to an uninterrupted run. It refuses if
  a bot file or the kit/engine changed meanwhile.
- **Shared file.** Several processes can share the file: each write is a short
  transaction, and a process that finds the file busy waits up to `runs.lock_timeout_s`.
