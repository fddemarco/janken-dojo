# 0035: anti_smartbot_normal vs anti_smartbot_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l2/anti_smartbot_normal.yaml`
- **Baselines:** `bots/l2/anti_smartbot_v1.yaml`
- **Run:** `20261013-020744_0035-anti-smartbot-normal`
- **Verdict:** keep
- **Species:** `anti_smartbot_v2` (promoted over `anti_smartbot_v1`)

## Hypothesis

anti_smartbot_normal plays as well as anti_smartbot_v1 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l2/anti_smartbot_normal.yaml bots/l2/anti_smartbot_v1.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 3253009607 --name 0035-anti-smartbot-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 3253009607, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| anti_smartbot_normal | 200 | 110-3-87 | 55.8% [48.8%, 62.5%] | -3.3 | 0 | 1543 +/- 85 |
| anti_smartbot_v1 | 200 | 109-2-89 | 55.0% [48.1%, 61.7%] | -3.5 | 0 | 1554 +/- 86 |

Paired comparisons:

- `anti_smartbot_normal - anti_smartbot_v1 = +0.8 pts [-6.5, +8.0]` over 200 shared matches: no significant difference

Weakest matchups of anti_smartbot_normal: replay_hunter_gate_normal 0.0%, double_bluff_gate_normal 0.0%, l5_priority 0.0%, replay_hunter_wide_normal 0.0%, replay_hunter_wide_v1 0.0%, l2_council_v1 0.0%.

Weakest matchups of anti_smartbot_v1: level_k_gate_v1 0.0%, double_bluff_gate_normal 0.0%, replay_hunter_wide_v1 0.0%, l5_hunter 0.0%, level_k_gate_normal 0.0%, double_bluff_gate_v1 0.0%.

## Analysis

-

## Verdict

**keep**. No significant difference at 10 round robins: anti_smartbot_normal - anti_smartbot_v1 = +0.8 pts [-6.5, +8.0] over 200 shared matches: no significant difference. The copy computes its replays' likely move (estimate NORMAL) instead of drawing it 256 times, which in a 40-seed check of anti_smartbot_sims played about 12x faster and named the same move as 2048 draws in 98% of rounds. Kept as equal and cheaper; species classify's 40-round-robin paired run checks every matchup before it replaces the original.

## Species

**promote**: its evaluation (run `20261013-020744_0035-anti-smartbot-normal`) paired it with anti_smartbot_v1: +0.8 pts [-6.5, +8.0]; no significant difference, and 14.5x faster.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `anti_smartbot_v1` | L2 | 95.4% |
| `anti_rps4_v1` | L2 | 71.5% |
| `anti_iocaine_v1` | L2 | 70.1% |
| `zoo_hunter_v1` | L2 | 41.8% |
| `iocaine_lite_v1` | L2 | 40.9% |
