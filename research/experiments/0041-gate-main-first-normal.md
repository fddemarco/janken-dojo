# 0041: gate_main_first_normal vs gate_main_first_v2

- **Date:** 2026-10-13
- **Status:** run
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l4/gate_main_first_normal.yaml`
- **Baselines:** `bots/l4/gate_main_first_v2.yaml`
- **Run:** `20261013-022614_0041-gate-main-first-normal`
- **Verdict:** -

## Hypothesis

gate_main_first_normal plays as well as gate_main_first_v2 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l4/gate_main_first_normal.yaml bots/l4/gate_main_first_v2.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 1318986214 --name 0041-gate-main-first-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 1318986214, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| gate_main_first_v2 | 200 | 130-6-64 | 66.5% [59.7%, 72.7%] | +24.6 | 0 | 1645 +/- 108 |
| gate_main_first_normal | 200 | 120-5-75 | 61.3% [54.3%, 67.7%] | +25.3 | 0 | 1603 +/- 84 |

Paired comparisons:

- `gate_main_first_normal - gate_main_first_v2 = -5.2 pts [-12.0, +1.5]` over 200 shared matches: no significant difference

Weakest matchups of gate_main_first_normal: l5_council 0.0%, level_k_gate_normal 0.0%, l5_wide_hunter 0.0%, l5_hunter 0.0%, replay_hunter_gate_v1 0.0%, replay_hunter_wide_v1 0.0%.

Weakest matchups of gate_main_first_v2: level_k_gate_normal 0.0%, l5_council 0.0%, replay_hunter_gate_v1 0.0%, replay_hunter_wide_normal 0.0%, l5_lean_hunter 0.0%, level_k_gate_v1 0.0%.

## Analysis

-

## Verdict

-
