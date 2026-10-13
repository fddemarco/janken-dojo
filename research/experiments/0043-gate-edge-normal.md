# 0043: gate_edge_normal vs gate_edge_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l4/gate_edge_normal.yaml`
- **Baselines:** `bots/l4/gate_edge_v2.yaml`
- **Run:** `20261013-023206_0043-gate-edge-normal`
- **Verdict:** keep
- **Species:** `gate_edge_v3` (promoted over `gate_edge_v2`)

## Hypothesis

gate_edge_normal plays as well as gate_edge_v2 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l4/gate_edge_normal.yaml bots/l4/gate_edge_v2.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 2717074285 --name 0043-gate-edge-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 2717074285, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| gate_edge_normal | 200 | 121-7-72 | 62.3% [55.4%, 68.7%] | +20.6 | 0 | 1601 +/- 57 |
| gate_edge_v2 | 200 | 113-4-83 | 57.5% [50.6%, 64.1%] | +19.7 | 0 | 1576 +/- 91 |

Paired comparisons:

- `gate_edge_normal - gate_edge_v2 = +4.8 pts [-2.0, +11.5]` over 200 shared matches: no significant difference

Weakest matchups of gate_edge_normal: level_k_gate_normal 0.0%, anti_smartbot_sims_v2 0.0%, gate_main_first_stationary_v2 0.0%, anti_smartbot_sims_normal 0.0%, l5_wide_hunter 0.0%, period_bandit_v1 0.0%.

Weakest matchups of gate_edge_v2: gate_main_first_stationary_normal 0.0%, level_k_gate_v1 0.0%, gate_bandit_period_v1 0.0%, replay_hunter_wide_v1 0.0%, anti_smartbot_v1 0.0%, gate_main_first_v2 0.0%.

## Analysis

-

## Verdict

**keep**. No significant difference at 10 round robins: gate_edge_normal - gate_edge_v2 = +4.8 pts [-2.0, +11.5] over 200 shared matches: no significant difference. The copy computes its replays' likely move (estimate NORMAL) instead of drawing it 256 times, which in a 40-seed check of anti_smartbot_sims played about 12x faster and named the same move as 2048 draws in 98% of rounds. Kept as equal and cheaper; classify decides from this paired run (species.promote_on_evaluation).

## Species

**promote**: its evaluation (run `20261013-023206_0043-gate-edge-normal`) paired it with gate_edge_v2: +4.8 pts [-2.0, +11.5]; no significant difference, and 13.9x faster.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `gate_edge_v2` | L4 | 76.2% |
| `gate_main_first_v3` | L4 | 76.0% |
| `gate_main_first_stationary_v3` | L4 | 69.8% |
| `level_k_gate_v2` | L4 | 66.4% |
| `replay_hunter_gate_v1` | L4 | 65.4% |
