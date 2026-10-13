# 0047: predator_normal vs predator_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l3/predator_normal.yaml`
- **Baselines:** `bots/l3/predator_v1.yaml`
- **Run:** `20261013-040522_0047-predator-normal`
- **Verdict:** keep
- **Species:** `predator_v2` (promoted over `predator_v1`)

## Hypothesis

predator_normal plays as well as predator_v1 (paired difference within +/-3 pts) at a fraction of its time: its anti_smartbot arm names anti_smartbot_v2, whose replay computes the likely move (estimate NORMAL)

## Command

```bash
uv run janken lab experiment bots/l3/predator_normal.yaml bots/l3/predator_v1.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 3038902948 --name 0047-predator-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 3038902948, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| predator_normal | 200 | 122-8-70 | 63.0% [56.1%, 69.4%] | +30.1 | 0 | 1630 +/- 74 |
| predator_v1 | 200 | 122-2-76 | 61.5% [54.6%, 68.0%] | +28.1 | 0 | 1590 +/- 65 |

Paired comparisons:

- `predator_normal - predator_v1 = +1.5 pts [-6.5, +9.2]` over 200 shared matches: no significant difference

Weakest matchups of predator_normal: anti_smartbot_sims_v3 0.0%, leader_hunter_v2 0.0%, anti_smartbot_v2 0.0%, l5_hunter 0.0%, gate_bandit_period_v2 0.0%, replay_hunter_gate_v2 0.0%.

Weakest matchups of predator_v1: leader_hunter_v2 0.0%, l5_council 0.0%, l5_wide_hunter 0.0%, gate_main_first_stationary_v3 0.0%, sampled_markov_v1 0.0%, l5_hunter 0.0%.

## Analysis

-

## Verdict

**keep**. No significant difference at 10 round robins: predator_normal - predator_v1 = +1.5 pts [-6.5, +9.2] over 200 shared matches. Its anti_smartbot arm names anti_smartbot_v2 (estimate NORMAL, 14.5x faster than anti_smartbot_v1, note 0035), so predator no longer names a retired version. Kept as equal and cheaper; classify decides from this paired run (species.promote_on_evaluation).

## Species

**promote**: its evaluation (run `20261013-040522_0047-predator-normal`) paired it with predator_v1: +1.5 pts [-6.5, +9.2]; no significant difference, and 14.1x faster.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `predator_v1` | L3 | 85.3% |
| `sims_lite_v1` | L3 | 70.7% |
| `sicilian_meta_v1` | L3 | 69.8% |
| `smartbot_sims_v2` | L3 | 67.0% |
| `leader_hunter_v2` | L3 | 66.0% |
