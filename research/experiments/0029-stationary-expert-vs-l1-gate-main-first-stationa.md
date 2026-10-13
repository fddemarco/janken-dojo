# 0029: Stationary expert vs L1: gate_main_first_stationary vs gate_main_first

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #36
- **Candidates:** `bots/gate_main_first_stationary.yaml`
- **Baselines:** `bots/gate_main_first.yaml`
- **Run:** `20261010-232522_0029-stationary-expert-vs-l1-gate-main-first-stationa`
- **Verdict:** iterate

## Hypothesis

Adding a stationary expert (long-memory frequency, BEAT) as a third gated expert under LEADER_PRIORITY doesn't degrade the L4 vs L1 (paired difference vs gate_main_first above -3 pts) and wins more vs biased; Oracle-arm screen: -0.4 [-2.9, +2.1] overall, biased 97% vs 86%.

## Command

```bash
uv run janken lab experiment bots/gate_main_first_stationary.yaml bots/gate_main_first.yaml --rounds 200 --round-robins 20 --pool-size 17 --seed 498489768 --name 0029-stationary-expert-vs-l1-gate-main-first-stationa
```

## Results

20 of 20 round robin(s), pool 17, 200 rounds/match, seed 498489768, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| gate_main_first | 340 | 307-2-31 | 90.6% [87.0%, 93.3%] | +109.7 | 0 | 1851 +/- 52 |
| gate_main_first_stationary | 340 | 307-1-32 | 90.4% [86.8%, 93.1%] | +111.2 | 0 | 1857 +/- 38 |

Paired comparisons:

- `gate_main_first_stationary - gate_main_first = -0.1 pts [-3.7, +3.4]` over 340 shared matches: no significant difference

Weakest matchups of gate_main_first_stationary: geometry 37.5%, transition_matrix 50.0%, nash 60.0%, rotation_outcome 95.0%, biased 95.0%, markov2_joint 100.0%.

Weakest matchups of gate_main_first: geometry 55.0%, nash 60.0%, transition_matrix 65.0%, biased 65.0%, rotation_outcome 95.0%, markov2_joint 100.0%.

## Analysis

What it gains vs biased it gives back on geometry (37.5% vs 55.0%) and transition_matrix (50.0% vs 65.0%), 20 matches each: either noise or the long-memory frequency expert taking the gate vs these mildly non-stationary bots. Oracle-arm screen (32 paired seeds, LEADER_PRIORITY EDGE 0): L1 -0.4 [-2.9, +2.1], biased 97% vs 86%.

## Verdict

**iterate**. Vs L1 the stationary expert is neutral overall and fixes biased: gate_main_first_stationary - gate_main_first = -0.1 pts [-3.7, +3.4] over 340 paired matches (17 L1 bots, 20 round robins, no mocks); biased 95% vs 65% of matches, +40.6 vs +6.8 rounds per match. Underpowered for a non-inferiority call (lower bound -3.7).
