# 0050: l5_variant_hunter vs l5_hunter

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #51
- **Candidates:** `bots/l5/l5_variant_hunter.yaml`
- **Baselines:** `bots/l5/l5_hunter.yaml`
- **Run:** `20261013-121351_0050-l5-variant-hunter-vs-l5-hunter`
- **Verdict:** drop

## Hypothesis

Vs pools whose every member plays a parameter variant drawn from its space file (pool.variants 1.0, 250 rounds), l5_variant_hunter beats l5_hunter by >= 3 pts: its pooled variant replays (variant_pool) name the variants of rps4_lite, outcome_reader, iocaine_lite and period_bandit that l5_hunter's default-parameter replays miss (gauntlet of note 0049: +11.1 pts +- 4.1)

## Command

```bash
uv run janken lab experiment bots/l5/l5_variant_hunter.yaml bots/l5/l5_hunter.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --variants 1.0 --seed 278887558 --name 0050-l5-variant-hunter-vs-l5-hunter
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 278887558, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| l5_hunter | 200 | 166-3-31 | 83.8% [78.0%, 88.2%] | +51.8 | 0 | 1802 +/- 77 |
| l5_variant_hunter | 200 | 165-3-32 | 83.2% [77.5%, 87.8%] | +51.4 | 0 | 1798 +/- 72 |

Paired comparisons:

- `l5_variant_hunter - l5_hunter = -0.5 pts [-6.0, +5.2]` over 200 shared matches: no significant difference

Weakest matchups of l5_variant_hunter: l5_identify_hunter 0.0%, l5_level_k 0.0%, l5_council 0.0%, nash_v1 0.0%, sicilian_meta_v1 0.0%, l5_priority 0.0%.

Weakest matchups of l5_hunter: l5_priority 0.0%, period_bandit_v1 0.0%, sampled_markov_v1 40.0%, l5_council 50.0%, nash_v1 50.0%, l5_lean_hunter 50.0%.

## Analysis

Per opponent (same seeds, rounds won minus lost, l5_variant_hunter minus l5_hunter): rps4_lite_v1 variants +94.5 (2 matches), iocaine_lite_v1 +31.7 (3), and incidental gains vs sims_lite +50.3, anti_smartbot_v2 +27.5, gate_edge_smartbot_v2 +27.5 (2-4 matches each), offset by small losses elsewhere. So the identification gain is real but narrow: it covers the variants of the species it replays (note 0049's gauntlet: +11.1 pts +- 4.1 on a list made of them), and a variant pool of the whole field holds few of them. To generalise across the field, every species would need its variants pooled, at a replay cost per species; this note is also the first use of pool.variants (idea #54), and l5_hunter itself holds up vs a field of variants (83.8% of matches, +51.8 rounds, about its default-pool score), so its overfitting to exact defaults is smaller than feared.

## Verdict

**drop**. Vs pools whose every member with a space file plays a parameter variant (pool.variants 1.0, 250 rounds), l5_variant_hunter - l5_hunter = -0.5 pts [-6.0, +5.2] over 200 paired matches (10 round robins, the cap); per match the round margin is -0.34 +- 5.0. Not the >= 3 pts the hypothesis needed: its variant replays win big vs the four species they model, but those are 2-3 of 200 matches in a field-wide variant pool, and it is more complex than l5_hunter.
