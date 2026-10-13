# 0046: replay_hunter_wide_normal vs replay_hunter_wide_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l4/replay_hunter_wide_normal.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v1.yaml`
- **Run:** `20261013-024435_0046-replay-hunter-wide-normal`
- **Verdict:** keep

## Hypothesis

replay_hunter_wide_normal plays as well as replay_hunter_wide_v1 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_wide_normal.yaml bots/l4/replay_hunter_wide_v1.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 700619142 --name 0046-replay-hunter-wide-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 700619142, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide_normal | 200 | 168-4-28 | 85.0% [79.4%, 89.3%] | +43.2 | 0 | 1804 +/- 66 |
| replay_hunter_wide_v1 | 200 | 158-7-35 | 80.8% [74.7%, 85.6%] | +42.6 | 0 | 1784 +/- 68 |

Paired comparisons:

- `replay_hunter_wide_normal - replay_hunter_wide_v1 = +4.2 pts [-2.2, +10.5]` over 200 shared matches: no significant difference

Weakest matchups of replay_hunter_wide_normal: anti_iocaine_v1 0.0%, l5_priority 0.0%, double_bluff_gate_v1 12.5%, l5_hunter 25.0%, l5_wide_hunter 25.0%, geometry_v1 33.3%.

Weakest matchups of replay_hunter_wide_v1: l5_lean_hunter 0.0%, l5_council 0.0%, l5_level_k 0.0%, anti_iocaine_v1 0.0%, gate_edge_normal 0.0%, sims_lite_v1 0.0%.

## Analysis

-

## Verdict

**keep**. No significant difference at 10 round robins: replay_hunter_wide_normal - replay_hunter_wide_v1 = +4.2 pts [-2.2, +10.5] over 200 shared matches: no significant difference. The copy computes its replays' likely move (estimate NORMAL) instead of drawing it 256 times, which in a 40-seed check of anti_smartbot_sims played about 12x faster and named the same move as 2048 draws in 98% of rounds. Kept as equal and cheaper; species classify's 40-round-robin paired run checks every matchup before it replaces the original.
