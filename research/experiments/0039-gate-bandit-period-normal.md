# 0039: gate_bandit_period_normal vs gate_bandit_period_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l3/gate_bandit_period_normal.yaml`
- **Baselines:** `bots/l3/gate_bandit_period_v1.yaml`
- **Run:** `20261013-021945_0039-gate-bandit-period-normal`
- **Verdict:** keep
- **Species:** `gate_bandit_period_v2` (promoted over `gate_bandit_period_v1`)

## Hypothesis

gate_bandit_period_normal plays as well as gate_bandit_period_v1 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l3/gate_bandit_period_normal.yaml bots/l3/gate_bandit_period_v1.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 1795809987 --name 0039-gate-bandit-period-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 1795809987, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| gate_bandit_period_normal | 200 | 140-3-57 | 70.8% [64.1%, 76.6%] | +25.9 | 0 | 1699 +/- 71 |
| gate_bandit_period_v1 | 200 | 133-6-61 | 68.0% [61.2%, 74.1%] | +27.8 | 0 | 1648 +/- 117 |

Paired comparisons:

- `gate_bandit_period_normal - gate_bandit_period_v1 = +2.8 pts [-5.0, +10.5]` over 200 shared matches: no significant difference

Weakest matchups of gate_bandit_period_normal: replay_hunter_wide_normal 0.0%, replay_hunter_gate_normal 0.0%, replay_hunter_wide_v1 0.0%, l2_council_v1 0.0%, vote_council_v1 0.0%, l5_wide_hunter 0.0%.

Weakest matchups of gate_bandit_period_v1: replay_hunter_gate_normal 0.0%, predator_v1 0.0%, double_bluff_gate_v1 0.0%, l5_council 0.0%, replay_hunter_wide_v1 0.0%, replay_hunter_gate_v1 0.0%.

## Analysis

-

## Verdict

**keep**. No significant difference at 10 round robins: gate_bandit_period_normal - gate_bandit_period_v1 = +2.8 pts [-5.0, +10.5] over 200 shared matches: no significant difference. The copy computes its replays' likely move (estimate NORMAL) instead of drawing it 256 times, which in a 40-seed check of anti_smartbot_sims played about 12x faster and named the same move as 2048 draws in 98% of rounds. Kept as equal and cheaper; classify decides from this paired run (species.promote_on_evaluation).

## Species

**promote**: its evaluation (run `20261013-021945_0039-gate-bandit-period-normal`) paired it with gate_bandit_period_v1: +2.8 pts [-5.0, +10.5]; no significant difference, and 13.9x faster.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `gate_bandit_period_v1` | L3 | 77.4% |
| `gate_edge_smartbot_v2` | L3 | 69.5% |
| `leader_hunter_v2` | L3 | 64.5% |
| `leader_new_l2_v1` | L3 | 63.4% |
| `predator_v1` | L3 | 62.9% |
