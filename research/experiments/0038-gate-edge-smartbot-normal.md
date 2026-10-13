# 0038: gate_edge_smartbot_normal vs gate_edge_smartbot_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l3/gate_edge_smartbot_normal.yaml`
- **Baselines:** `bots/l3/gate_edge_smartbot_v1.yaml`
- **Run:** `20261013-021719_0038-gate-edge-smartbot-normal`
- **Verdict:** keep
- **Species:** `gate_edge_smartbot_v2` (promoted over `gate_edge_smartbot_v1`)

## Hypothesis

gate_edge_smartbot_normal plays as well as gate_edge_smartbot_v1 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l3/gate_edge_smartbot_normal.yaml bots/l3/gate_edge_smartbot_v1.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 4175640874 --name 0038-gate-edge-smartbot-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 4175640874, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| gate_edge_smartbot_normal | 200 | 118-8-74 | 61.0% [54.1%, 67.5%] | +22.5 | 0 | 1598 +/- 101 |
| gate_edge_smartbot_v1 | 200 | 117-1-82 | 58.8% [51.8%, 65.3%] | +20.7 | 0 | 1578 +/- 99 |

Paired comparisons:

- `gate_edge_smartbot_normal - gate_edge_smartbot_v1 = +2.2 pts [-4.2, +9.2]` over 200 shared matches: no significant difference

Weakest matchups of gate_edge_smartbot_normal: gate_bandit_period_v1 0.0%, gate_main_first_v2 0.0%, anti_smartbot_normal 0.0%, anti_smartbot_v1 0.0%, gate_main_first_normal 0.0%, anti_smartbot_sims_normal 0.0%.

Weakest matchups of gate_edge_smartbot_v1: l5_priority 0.0%, anti_smartbot_v1 0.0%, level_k_gate_normal 0.0%, anti_smartbot_sims_v2 0.0%, counter_council_v1 0.0%, gate_bandit_period_v1 0.0%.

## Analysis

-

## Verdict

**keep**. No significant difference at 10 round robins: gate_edge_smartbot_normal - gate_edge_smartbot_v1 = +2.2 pts [-4.2, +9.2] over 200 shared matches: no significant difference. The copy computes its replays' likely move (estimate NORMAL) instead of drawing it 256 times, which in a 40-seed check of anti_smartbot_sims played about 12x faster and named the same move as 2048 draws in 98% of rounds. Kept as equal and cheaper; classify decides from this paired run (species.promote_on_evaluation).

## Species

**promote**: its evaluation (run `20261013-021719_0038-gate-edge-smartbot-normal`) paired it with gate_edge_smartbot_v1: +2.2 pts [-4.2, +9.2]; no significant difference, and 13.7x faster.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `gate_edge_smartbot_v1` | L3 | 76.5% |
| `gate_bandit_period_v1` | L3 | 68.3% |
| `leader_hunter_v2` | L3 | 65.5% |
| `naive_bayes_markov_v1` | L3 | 62.8% |
| `predator_v1` | L3 | 62.5% |
