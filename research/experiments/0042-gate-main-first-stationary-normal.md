# 0042: gate_main_first_stationary_normal vs gate_main_first_stationary_v2

- **Date:** 2026-10-13
- **Status:** run
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l4/gate_main_first_stationary_normal.yaml`
- **Baselines:** `bots/l4/gate_main_first_stationary_v2.yaml`
- **Run:** `20261013-022912_0042-gate-main-first-stationary-normal`
- **Verdict:** -

## Hypothesis

gate_main_first_stationary_normal plays as well as gate_main_first_stationary_v2 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l4/gate_main_first_stationary_normal.yaml bots/l4/gate_main_first_stationary_v2.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 1294707814 --name 0042-gate-main-first-stationary-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 1294707814, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| gate_main_first_stationary_v2 | 200 | 135-0-65 | 67.5% [60.7%, 73.6%] | +33.5 | 0 | 1654 +/- 70 |
| gate_main_first_stationary_normal | 200 | 127-1-72 | 63.7% [56.9%, 70.1%] | +31.3 | 0 | 1625 +/- 113 |

Paired comparisons:

- `gate_main_first_stationary_normal - gate_main_first_stationary_v2 = -3.8 pts [-10.5, +3.2]` over 200 shared matches: no significant difference

Weakest matchups of gate_main_first_stationary_normal: geometry_v1 0.0%, l5_wide_hunter 0.0%, l5_council 0.0%, l5_level_k 0.0%, l5_lean_hunter 0.0%, sicilian_meta_v1 0.0%.

Weakest matchups of gate_main_first_stationary_v2: replay_hunter_gate_normal 0.0%, l5_hunter 0.0%, l5_wide_hunter 0.0%, sampled_markov_v1 0.0%, level_k_gate_v1 0.0%, l5_level_k 0.0%.

## Analysis

-

## Verdict

-
