# 0044: double_bluff_gate_normal vs double_bluff_gate_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l4/double_bluff_gate_normal.yaml`
- **Baselines:** `bots/l4/double_bluff_gate_v1.yaml`
- **Run:** `20261013-023506_0044-double-bluff-gate-normal`
- **Verdict:** keep
- **Species:** `double_bluff_gate_v2` (promoted over `double_bluff_gate_v1`)

## Hypothesis

double_bluff_gate_normal plays as well as double_bluff_gate_v1 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l4/double_bluff_gate_normal.yaml bots/l4/double_bluff_gate_v1.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 3229787241 --name 0044-double-bluff-gate-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 3229787241, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| double_bluff_gate_normal | 200 | 123-3-74 | 62.3% [55.4%, 68.7%] | +25.6 | 0 | 1614 +/- 136 |
| double_bluff_gate_v1 | 200 | 119-7-74 | 61.3% [54.3%, 67.7%] | +24.2 | 0 | 1596 +/- 55 |

Paired comparisons:

- `double_bluff_gate_normal - double_bluff_gate_v1 = +1.0 pts [-7.8, +10.0]` over 200 shared matches: no significant difference

Weakest matchups of double_bluff_gate_normal: gate_main_first_stationary_v2 0.0%, smartbot_sims_v2 0.0%, second_guess_v1 0.0%, smartbot_wide_v1 0.0%, geometry_v1 0.0%, l5_level_k 0.0%.

Weakest matchups of double_bluff_gate_v1: l5_level_k 0.0%, gate_main_first_stationary_normal 0.0%, level_k_gate_v1 0.0%, smartbot_v1 0.0%, replay_hunter_gate_v1 0.0%, vote_council_v1 0.0%.

## Analysis

-

## Verdict

**keep**. No significant difference at 10 round robins: double_bluff_gate_normal - double_bluff_gate_v1 = +1.0 pts [-7.8, +10.0] over 200 shared matches: no significant difference. The copy computes its replays' likely move (estimate NORMAL) instead of drawing it 256 times, which in a 40-seed check of anti_smartbot_sims played about 12x faster and named the same move as 2048 draws in 98% of rounds. Kept as equal and cheaper; classify decides from this paired run (species.promote_on_evaluation).

## Species

**promote**: its evaluation (run `20261013-023506_0044-double-bluff-gate-normal`) paired it with double_bluff_gate_v1: +1.0 pts [-7.8, +10.0]; no significant difference, and 12.8x faster.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `double_bluff_gate_v1` | L4 | 71.5% |
| `level_k_gate_v2` | L4 | 69.1% |
| `gate_main_first_v3` | L4 | 66.6% |
| `replay_hunter_gate_v1` | L4 | 66.6% |
| `replay_hunter_wide_v1` | L4 | 65.8% |
