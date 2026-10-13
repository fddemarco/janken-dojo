# 0052: l5_wide_hunter vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #46
- **Candidates:** `bots/l5/l5_wide_hunter.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-123947_0052-l5-wide-hunter-vs-replay-hunter-wide-v2`
- **Verdict:** iterate

## Hypothesis

Vs pools of parameter variants (pool.variants 1.0, 250 rounds) l5_wide_hunter beats replay_hunter_wide_v2 by >= 2 pts: replaying the L4 gatekeepers as they play generalises better than the L4's default-parameter replays (note 0051: +2.5 pts [-2.5, +8.0] vs default pools)

## Command

```bash
uv run janken lab experiment bots/l5/l5_wide_hunter.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --variants 1.0 --seed 1180903422 --name 0052-l5-wide-hunter-vs-replay-hunter-wide-v2
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 1180903422, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| l5_wide_hunter | 200 | 169-1-30 | 84.8% [79.1%, 89.1%] | +51.1 | 0 | 1829 +/- 56 |
| replay_hunter_wide_v2 | 200 | 156-3-41 | 78.8% [72.6%, 83.9%] | +44.8 | 0 | 1739 +/- 68 |

Paired comparisons:

- `l5_wide_hunter - replay_hunter_wide_v2 = +6.0 pts [-0.5, +12.2]` over 200 shared matches: no significant difference

Weakest matchups of l5_wide_hunter: sampled_markov_v1 0.0%, gate_edge_v3 0.0%, l5_council 25.0%, counter_council_v1 33.3%, geometry_ensemble_v1 33.3%, l5_priority 50.0%.

Weakest matchups of replay_hunter_wide_v2: l5_lean_hunter 0.0%, geometry_v1 0.0%, nash_v1 25.0%, l5_priority 25.0%, l5_hunter 33.3%, second_guess_v1 33.3%.

## Analysis

Scores vs the variant pools: l5_wide_hunter 84.8% (+51.1 rounds per match), replay_hunter_wide_v2 78.8% (+44.8); vs default pools (0051) 91.5% and 89.0%. Both lose a few points to variants, the L4 more (-10.2 vs -6.7 pts of match score), consistent with the L4's default-parameter replays missing variants while the L5 replays whole gatekeepers that adapt. Weakest of l5_wide_hunter: sampled_markov_v1 and gate_edge_v3 variants (0 of their matches), l5_council 1 of 4; of the L4: l5_lean_hunter, geometry_v1 (0), nash_v1. Next: a sharper test, head to head vs the variant L4 gatekeepers, or a second variant-pool run on fresh seeds to confirm the +6 pts before keeping it.

## Verdict

**iterate**. Vs pools of parameter variants (pool.variants 1.0, 250 rounds, 10 round robins, the cap) l5_wide_hunter - replay_hunter_wide_v2 = +6.0 pts [-0.5, +12.2] over 200 paired matches: just short of significant, the same sign as vs default pools (note 0051: +2.5 [-2.5, +8.0]). Its paired round margin is +6.2 rounds per match +- 4.5 (95%), which does exclude 0. Promising: the L5's gap over the L4 grows when the field plays variants.
