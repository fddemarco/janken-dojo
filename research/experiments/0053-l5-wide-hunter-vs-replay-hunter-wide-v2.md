# 0053: l5_wide_hunter vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #46
- **Candidates:** `bots/l5/l5_wide_hunter.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-124625_0053-l5-wide-hunter-vs-replay-hunter-wide-v2`
- **Verdict:** drop

## Hypothesis

Confirmation of note 0052 on fresh seeds: vs pools of parameter variants (pool.variants 1.0, 250 rounds) l5_wide_hunter beats replay_hunter_wide_v2 by >= 2 pts (0052: +6.0 pts [-0.5, +12.2])

## Command

```bash
uv run janken lab experiment bots/l5/l5_wide_hunter.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 8 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --variants 1.0 --seed 1546165804 --name 0053-l5-wide-hunter-vs-replay-hunter-wide-v2
```

## Results

8 of 8 round robin(s), pool 20, 250 rounds/match, seed 1546165804, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| l5_wide_hunter | 160 | 134-1-25 | 84.1% [77.6%, 88.9%] | +54.5 | 0 | 1827 +/- 65 |
| replay_hunter_wide_v2 | 160 | 130-3-27 | 82.2% [75.5%, 87.3%] | +51.5 | 0 | 1766 +/- 59 |

Paired comparisons:

- `l5_wide_hunter - replay_hunter_wide_v2 = +1.9 pts [-5.3, +8.8]` over 160 shared matches: no significant difference

Weakest matchups of l5_wide_hunter: replay_hunter_gate_v2 0.0%, sampled_markov_v1 0.0%, level_k_gate_v2 0.0%, nash_v1 0.0%, vote_council_v1 0.0%, l5_level_k 33.3%.

Weakest matchups of replay_hunter_wide_v2: l5_priority 0.0%, predator_v2 0.0%, nash_v1 0.0%, gate_main_first_stationary_v3 0.0%, geometry_v1 25.0%, l5_level_k 33.3%.

## Analysis

Scores: l5_wide_hunter 84.1% (+54.5 rounds per match), replay_hunter_wide_v2 82.2% (+51.5). The three runs agree in sign but not in size: 0052's +6 was the high draw. Both bots lose about the same few points of match score to a variant field (0051 vs 0052/0053), so neither the L4's default-parameter replays nor the L5's replays of whole gatekeepers overfit the field's exact defaults much: the variant pools (idea #54, pool.variants) show no large generalisation gap to close.

## Verdict

**drop**. On fresh seeds the variant-pool lead of note 0052 doesn't hold: l5_wide_hunter - replay_hunter_wide_v2 = +1.9 pts [-5.3, +8.8] over 160 paired matches (pool.variants 1.0, 250 rounds), stopped for futility at look 4 of 5. With 0051 (+2.5 [-2.5, +8.0], default pools) and 0052 (+6.0 [-0.5, +12.2]), the L5's edge over the best L4 is a few points at most, vs defaults and vs variants alike.
