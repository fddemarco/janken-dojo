# NNNN: <title>

The CLI writes and fills notes; this shows their shape (janken/notebook/notes.py). A note
is created by `janken evaluate` / `janken tune` (status planned), gets its results
(status run), and is closed by `janken verdict` (status analyzed).

- **Date:** YYYY-MM-DD
- **Status:** planned | run | analyzed
- **Kind:** evaluation | tuning
- **Idea:** #<n>
- **Candidates:** `bots/<new>.yaml`
- **Baselines:** `bots/<old>.yaml`
- **Run:** `<run id>` (a tuning note has **Study:** `<NNNN-slug>` and, for a fleet,
  **Supports:**)
- **Verdict:** keep | drop | iterate

## Hypothesis

What we expect, and the size of effect that would matter, written before the run. For
example: "geometry+stall beats geometry by >= 3 points in the paired comparison, mostly
against the metabots."

## Command

The reproducible low-level command (`janken lab experiment ...` / `janken lab study run ...`),
written by the CLI.

## Results

Written by the CLI: candidates vs pool, paired comparisons, weakest matchups (or a
study's recorded validations).

## Analysis

The longer reading (`janken verdict --analysis`): per opponent, mechanism, surprises.

## Verdict

**keep | drop | iterate**. One paragraph (`janken verdict --summary`): what we learned,
and what goes into insights.md / ideas.md.
