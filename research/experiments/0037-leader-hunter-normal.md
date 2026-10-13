# 0037: leader_hunter_normal vs leader_hunter_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l3/leader_hunter_normal.yaml`
- **Baselines:** `bots/l3/leader_hunter_v1.yaml`
- **Run:** `20261013-021452_0037-leader-hunter-normal`
- **Verdict:** keep
- **Species:** `leader_hunter_v2` (promoted over `leader_hunter_v1`)

## Hypothesis

leader_hunter_normal plays as well as leader_hunter_v1 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l3/leader_hunter_normal.yaml bots/l3/leader_hunter_v1.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 1128089513 --name 0037-leader-hunter-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 1128089513, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| leader_hunter_normal | 200 | 122-7-71 | 62.7% [55.9%, 69.2%] | +28.5 | 0 | 1614 +/- 140 |
| leader_hunter_v1 | 200 | 118-6-76 | 60.5% [53.6%, 67.0%] | +28.0 | 0 | 1594 +/- 77 |

Paired comparisons:

- `leader_hunter_normal - leader_hunter_v1 = +2.2 pts [-5.8, +10.2]` over 200 shared matches: no significant difference

Weakest matchups of leader_hunter_normal: replay_hunter_wide_normal 0.0%, level_k_gate_v1 0.0%, period_bandit_v1 0.0%, anti_smartbot_sims_normal 0.0%, gate_main_first_stationary_normal 0.0%, l5_priority 0.0%.

Weakest matchups of leader_hunter_v1: multiscale_council_v1 0.0%, l2_council_v1 0.0%, replay_hunter_gate_normal 0.0%, anti_smartbot_normal 0.0%, nash_v1 0.0%, gate_bandit_period_normal 0.0%.

## Analysis

-

## Verdict

**keep**. No significant difference at 10 round robins: leader_hunter_normal - leader_hunter_v1 = +2.2 pts [-5.8, +10.2] over 200 shared matches: no significant difference. The copy computes its replays' likely move (estimate NORMAL) instead of drawing it 256 times, which in a 40-seed check of anti_smartbot_sims played about 12x faster and named the same move as 2048 draws in 98% of rounds. Kept as equal and cheaper; classify decides from this paired run (species.promote_on_evaluation).

## Species

**promote**: its evaluation (run `20261013-021452_0037-leader-hunter-normal`) paired it with leader_hunter_v1: +2.2 pts [-5.8, +10.2]; no significant difference, and 15.2x faster.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `leader_hunter_v1` | L3 | 77.1% |
| `gate_main_first_backoff_v1` | L3 | 69.3% |
| `smartbot_sims_v2` | L3 | 67.0% |
| `smartbot_wide_v1` | L3 | 66.3% |
| `naive_bayes_markov_v1` | L3 | 66.2% |
