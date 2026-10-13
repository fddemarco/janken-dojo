# 0045: replay_hunter_gate_normal vs replay_hunter_gate_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l4/replay_hunter_gate_normal.yaml`
- **Baselines:** `bots/l4/replay_hunter_gate_v1.yaml`
- **Run:** `20261013-023804_0045-replay-hunter-gate-normal`
- **Verdict:** keep

## Hypothesis

replay_hunter_gate_normal plays as well as replay_hunter_gate_v1 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_gate_normal.yaml bots/l4/replay_hunter_gate_v1.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 2768898313 --name 0045-replay-hunter-gate-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 2768898313, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_gate_v1 | 200 | 162-3-35 | 81.8% [75.8%, 86.5%] | +35.4 | 0 | 1780 +/- 76 |
| replay_hunter_gate_normal | 200 | 163-1-36 | 81.8% [75.8%, 86.5%] | +37.5 | 0 | 1789 +/- 107 |

Paired comparisons:

- `replay_hunter_gate_normal - replay_hunter_gate_v1 = +0.0 pts [-6.5, +6.8]` over 200 shared matches: no significant difference

Weakest matchups of replay_hunter_gate_normal: l5_priority 0.0%, geometry_v1 0.0%, nash_v1 0.0%, level_k_gate_v1 0.0%, l5_hunter 25.0%, anti_iocaine_v1 25.0%.

Weakest matchups of replay_hunter_gate_v1: nash_v1 0.0%, sicilian_meta_v1 0.0%, sampled_markov_v1 0.0%, l5_lean_hunter 25.0%, l5_council 33.3%, l5_wide_hunter 37.5%.

## Analysis

-

## Verdict

**keep**. No significant difference at 10 round robins: replay_hunter_gate_normal - replay_hunter_gate_v1 = +0.0 pts [-6.5, +6.8] over 200 shared matches: no significant difference. The copy computes its replays' likely move (estimate NORMAL) instead of drawing it 256 times, which in a 40-seed check of anti_smartbot_sims played about 12x faster and named the same move as 2048 draws in 98% of rounds. Kept as equal and cheaper; species classify's 40-round-robin paired run checks every matchup before it replaces the original.
