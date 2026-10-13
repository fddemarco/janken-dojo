# 0040: level_k_gate_normal vs level_k_gate_v1

- **Date:** 2026-10-13
- **Status:** run
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l4/level_k_gate_normal.yaml`
- **Baselines:** `bots/l4/level_k_gate_v1.yaml`
- **Run:** `20261013-022209_0040-level-k-gate-normal`
- **Verdict:** -

## Hypothesis

level_k_gate_normal plays as well as level_k_gate_v1 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l4/level_k_gate_normal.yaml bots/l4/level_k_gate_v1.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 2956724662 --name 0040-level-k-gate-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 2956724662, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| level_k_gate_v1 | 200 | 146-2-52 | 73.5% [67.0%, 79.1%] | +35.3 | 0 | 1701 +/- 72 |
| level_k_gate_normal | 200 | 138-5-57 | 70.2% [63.6%, 76.2%] | +33.1 | 0 | 1690 +/- 76 |

Paired comparisons:

- `level_k_gate_normal - level_k_gate_v1 = -3.2 pts [-10.2, +3.2]` over 200 shared matches: no significant difference

Weakest matchups of level_k_gate_normal: l5_council 0.0%, dropswitch_council_v1 0.0%, l5_wide_hunter 0.0%, replay_hunter_gate_v1 0.0%, replay_hunter_gate_normal 0.0%, l5_lean_hunter 0.0%.

Weakest matchups of level_k_gate_v1: dropswitch_council_v1 0.0%, sicilian_meta_v1 0.0%, replay_hunter_gate_v1 0.0%, l5_lean_hunter 0.0%, l5_wide_hunter 0.0%, backoff_family_v1 0.0%.

## Analysis

-

## Verdict

-
