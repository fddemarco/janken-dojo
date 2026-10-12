# 0002: tune smartbot's decays at 200 rounds

- **Date:** 2026-10-09
- **Status:** analyzed
- **Idea:** ideas.md #4
- **Bots:** `bots/smartbot.py` (SPACE: ARM_DECAY, TABLE_DECAY, MAX_MATCH), baseline: its
  DEFAULTS (0.95 / 0.9 / 12)

## Hypothesis

smartbot is the best candidate so far (81.2% pooled) and its constants were never tuned.
`meta_smartbot` is the same program at 0.6 / 0.6 / 8, and the two are a coin flip head to
head, so the score surface is probably flat. Expectation: the best validated config beats
the defaults by **≥ +2 pts** in the paired validation comparison. More likely, given the
flat surface, no config clears the noise, which would tell us that the metabot's ceiling
is in its structure (arms, bandit, output), not its constants.

Tuning: TPE, 120 trials (40 per parameter), 10 round robins per trial (common random
numbers), median pruning. Only the validation run (defaults + top 5 on fresh pools,
40 round robins for paired CIs of about ±2 pts) is evidence.

## Command

```bash
uv run python -m janken tune bots/smartbot.py --study smartbot-v1 --trials 120 --round-robins 10 --validate-top 5 --validate-round-robins 40
```

Run id: `20261009-235502_validate-smartbot-v1` (validation; seed 1607579654, 40 round robins,
13000 matches on numba, 0 forfeits). Study `smartbot-v1`: 120 trials (92 complete, 28 pruned).

## Results

Tuning trials (fixed pools, not evidence): defaults (trial 0) 81.3%, best trial 84.8%,
mean of completed trials 78.8%. The top trials cluster at ARM_DECAY ≈ 0.96 with short
MAX_MATCH (2–3), which is the kind of corner a fixed pool rewards by chance.

Validation (fresh pools, 800 shared matches each):

| bot | params (ARM_DECAY / TABLE_DECAY / MAX_MATCH) | score vs pool [95% CI] |
|---|---|---|
| smartbot@fba169 | 0.873 / 0.930 / 8 | 79.9% [77.0, 82.6] |
| smartbot@06136d | 0.957 / 0.899 / 3 | 79.4% [76.4, 82.0] |
| smartbot@6e0b69 | 0.965 / 0.867 / 2 | 79.2% [76.3, 81.9] |
| smartbot (defaults) | 0.95 / 0.9 / 12 | 78.5% [75.5, 81.2] |
| smartbot@8aab2f | 0.964 / 0.900 / 3 | 78.3% [75.3, 81.0] |
| smartbot@5a938a | 0.987 / 0.989 / 2 | 77.7% [74.7, 80.4] |

Paired comparisons vs the defaults: every variant lies within −0.8 … +1.4 pts, with CIs
about ±3.2 pts (best: `fba169 − defaults = +1.4 pts [−1.8, +4.6]`). No pair of the six
differs significantly. Resolving +1.4 pts would take ~200 round robins.

Per-opponent view of the defaults (duckdb over `matches.parquet`, 29–38 matches each):
the strong bots are coin flips with round margins near 0 (geometry 40.0% / −2.3,
smart_staller 46.6%, nash 47.2%, transition_matrix 48.6%, meta_smartbot 51.4%, rps4_lite
54.2%). The **mid-tier is where points leak**: iocaine_lite 61.1% (margin +4.8 rounds),
pattern_memory 62.2% (+2.9), markov2_joint 73.5% (+5.9), staller 81.1% (+7.8),
word2janken 89.4%, biased 90.3%. These are exploitable bots that smartbot beats by only a
few rounds per 200, so matches still tip either way. Everything else saturates at 100%.

## Verdict

**drop** (no tuned config adopted; defaults stay). The metabot's score is flat in its
three constants at 200 rounds: the tuning gain (+3.5 pts on the fixed pools) vanished on
fresh pools. Its ceiling is structural. The leak is the tiny round margin against
exploitable mid-tier bots (iocaine_lite, pattern_memory, markov2_joint), which a 56-arm
Thompson bandit at ARM_DECAY 0.95 converts into wins too slowly or too noisily. This
raises idea #7 (greedy decayed scores with a random arm pinned at 0, which commits hard
to a winning arm) to P1, aimed at the mid-tier margin.
