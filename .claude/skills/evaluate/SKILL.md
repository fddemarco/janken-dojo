---
name: evaluate
description: Test a janken bot against random pools with `janken evaluate` (hypothesis first, a baseline in the same run for a paired comparison), read the results statistically, and close the note with `janken verdict`. Use when a bot is built, a note is planned or has results, or the user asks whether one bot beats another.
---

# Evaluate

`janken evaluate` writes the note, plays the experiment, analyzes it and puts the results
in the note. You bring the hypothesis and the judgement. Run every command as
`uv run janken ...`.

## 1. Design it

- **Candidates:** the new bot, plus a **baseline** in the same run (usually the bot it
  improves on). Only candidates in one run get a paired comparison, which is far sharper
  than comparing two runs.
- **Hypothesis**, written before the run: what you expect, and the effect size that would
  matter. For example: "bayes_combiner beats smartbot_sims by >= 2 pts, mostly against the
  metabots".
- **Effort:**
  - `standard`: 10 round robins, a score CI of about +/-6 pts;
  - `thorough`: 40 round robins, about +/-3 pts, for effects of 1-3 pts;
  - `quick`: a smoke check, proves nothing.

## 2. Run it

```bash
uv run janken evaluate bots/<level>/<new>.yaml --baseline bots/<level>/<old>.yaml \
  --hypothesis "..." --idea <N> --effort standard
```

- **What it prints:** the note path, the results (candidates vs pool, paired comparisons,
  weakest matchups) and the run id.
- **A planned or interrupted note:** `uv run janken evaluate --note NNNN` runs
  or resumes it.
- **Tuning** instead: `/tune`.

## 3. Read it, then decide

- **A real difference** is a paired comparison whose **CI excludes 0**. Overlapping score
  CIs from separate runs are no evidence.
- **The weakest matchups** carry the information; headline scores saturate.
- **Digging further:**
  - `janken lab report <run>`: every matchup;
  - `janken lab query "SELECT ... FROM matches WHERE run_id = '...'"`: transcripts in
    `moves`;
  - `janken lab match A B`.

```bash
uv run janken verdict NNNN keep|drop|iterate \
  --summary "one paragraph: the paired result with its CI, and what it means" \
  --analysis "the longer reading: per opponent, mechanism, surprises"
```

- **keep:** the candidate is better (CI excludes 0 in its favour), or it's equal and
  simpler. The idea becomes `done`, and the bot goes to `/classify` next (a new species,
  the next version of one, or a variant that retires).
- **drop:** no better, or worse. The idea becomes `dropped`.
- **iterate:** promising but unresolved (say why). The idea stays in progress. Plan the
  follow-up as a new note, with `--effort thorough` or a variant.

Next: a `keep` whose CI excludes 0 goes to `/learn`. A kept bot with tunable defaults may
go to `/tune`.
