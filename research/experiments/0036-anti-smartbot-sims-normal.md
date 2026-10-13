# 0036: anti_smartbot_sims_normal vs anti_smartbot_sims_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l3/anti_smartbot_sims_normal.yaml`
- **Baselines:** `bots/l3/anti_smartbot_sims_v2.yaml`
- **Run:** `20261013-020828_0036-anti-smartbot-sims-normal`
- **Verdict:** keep

## Hypothesis

anti_smartbot_sims_normal plays as well as anti_smartbot_sims_v2 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l3/anti_smartbot_sims_normal.yaml bots/l3/anti_smartbot_sims_v2.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 1796289887 --name 0036-anti-smartbot-sims-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 1796289887, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| anti_smartbot_sims_v2 | 200 | 109-5-86 | 55.8% [48.8%, 62.5%] | -12.1 | 0 | 1551 +/- 116 |
| anti_smartbot_sims_normal | 200 | 108-5-87 | 55.2% [48.3%, 62.0%] | -12.3 | 0 | 1547 +/- 74 |

Paired comparisons:

- `anti_smartbot_sims_normal - anti_smartbot_sims_v2 = -0.5 pts [-7.8, +6.8]` over 200 shared matches: no significant difference

Weakest matchups of anti_smartbot_sims_normal: level_k_gate_normal 0.0%, replay_hunter_wide_normal 0.0%, replay_hunter_wide_v1 0.0%, replay_hunter_gate_normal 0.0%, level_k_gate_v1 0.0%, replay_hunter_gate_v1 0.0%.

Weakest matchups of anti_smartbot_sims_v2: level_k_gate_v1 0.0%, replay_hunter_wide_v1 0.0%, level_k_gate_normal 0.0%, replay_hunter_gate_normal 0.0%, replay_hunter_gate_v1 0.0%, double_bluff_gate_v1 0.0%.

## Analysis

-

## Verdict

**keep**. No significant difference at 10 round robins: anti_smartbot_sims_normal - anti_smartbot_sims_v2 = -0.5 pts [-7.8, +6.8] over 200 shared matches: no significant difference. The copy computes its replays' likely move (estimate NORMAL) instead of drawing it 256 times, which in a 40-seed check of anti_smartbot_sims played about 12x faster and named the same move as 2048 draws in 98% of rounds. Kept as equal and cheaper; species classify's 40-round-robin paired run checks every matchup before it replaces the original.
