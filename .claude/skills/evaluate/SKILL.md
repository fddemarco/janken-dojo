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
- **Size: the ladder.** Start with 1 round robin and grow the same run only while
  the result is inconclusive: 1 --> 3 --> 5 --> 7 --> 10, never past 10 (section 2).
  For reference, 10 round robins give a score CI of about +/-6 pts, so an effect
  under ~3 pts won't resolve: say so in the verdict rather than playing on. `--effort
  quick` is a smoke check and proves nothing.

## 2. Run it

```bash
uv run janken evaluate bots/<level>/<new>.yaml --baseline bots/<level>/<old>.yaml \
  --hypothesis "..." --idea <N> --mode candidates --round-robins 1
uv run janken evaluate --note NNNN --round-robins 3   # only if inconclusive
uv run janken evaluate --note NNNN --round-robins 5   # ... then 7, then 10 (the cap)
```

- **The ladder.** `--note NNNN --round-robins K` grows the note's run to K round
  robins and plays only the missing ones. Round robin k's pool and seeds don't depend
  on K, so a grown run equals one planned at K: stepping costs nothing extra and the
  comparison stays paired. After each step, read the paired comparisons and stop as
  soon as each one is **conclusive**: its CI excludes 0, or it is clearly beyond the
  hypothesis's threshold either way. Grow only for the inconclusive ones. At 10,
  decide with what you have (an unresolved effect is `drop` or `iterate`, never more
  round robins).
- **`--mode candidates`** plays only the candidates' matches (~20x fewer than `full`,
  the config default, which also plays pool vs pool for the ratings). Paired
  comparisons need only the candidates' matches.

- **What it prints:** the note path, the results (candidates vs pool, paired comparisons,
  weakest matchups) and the run id.
- **A planned or interrupted note:** `uv run janken evaluate --note NNNN` runs
  or resumes it.
- **Tuning** instead: `/tune`.

### Head to head: the seed ladder

A claim about one opponent ("X wins >= 36% of rounds vs Y at 250 rounds") is checked
head to head, not in the pools, where Y meets X once per round robin:

```bash
uv run python .claude/skills/evaluate/scripts/head_to_head.py bots/<level>/<x>.yaml \
  bots/<level>/<y>.yaml --threshold 0.36 --rounds 250
```

It plays seeds 1..n for n = 10 --> 25 --> 50 --> 100, adding only the new seeds at each
step, and stops at the first step whose 95% CI of the share of rounds won is clear of
the threshold. More seeds only for an inconclusive result, never past 100; at 100,
decide with what you have. Never start bigger (a 1000-seed run of an L4 bot takes
over 10 minutes and adds nothing once 10 seeds are clear). It also prints the worst
match and the match record. Put its lines in the verdict's analysis.

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
  follow-up as a new note: a sharper test (a pool where the effect lives) or a
  variant, not more round robins of the same.

Next: a `keep` whose CI excludes 0 goes to `/learn`. A kept bot with tunable defaults may
go to `/tune`.
