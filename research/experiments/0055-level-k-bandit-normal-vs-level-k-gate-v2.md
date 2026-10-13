# 0055: level_k_bandit_normal vs level_k_gate_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #40
- **Candidates:** `bots/l4/level_k_bandit_normal.yaml`
- **Baselines:** `bots/l4/level_k_gate_v2.yaml`
- **Run:** `20261013-134613_0055-level-k-bandit-normal-vs-level-k-gate-v2`
- **Verdict:** keep

## Hypothesis

level_k_bandit_normal is no worse than level_k_gate_v2 vs random pools (paired difference above -3 pts) and wins >= 36% of rounds head to head vs double_bluff_gate_v2, where the LEADER gate trails its level switches (idea #40)

## Command

```bash
uv run janken lab experiment bots/l4/level_k_bandit_normal.yaml bots/l4/level_k_gate_v2.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 335052947 --name 0055-level-k-bandit-normal-vs-level-k-gate-v2
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 335052947, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| level_k_gate_v2 | 200 | 153-3-44 | 77.2% [71.0%, 82.5%] | +54.7 | 0 | 1722 +/- 106 |
| level_k_bandit_normal | 200 | 151-5-44 | 76.8% [70.4%, 82.1%] | +53.5 | 0 | 1762 +/- 84 |

Paired comparisons:

- `level_k_bandit_normal - level_k_gate_v2 = -0.5 pts [-7.0, +6.0]` over 200 shared matches: no significant difference

Weakest matchups of level_k_bandit_normal: vote_council_v1 0.0%, transition_matrix_v1 0.0%, period_detector_v1 0.0%, geometry_ensemble_v1 0.0%, l2_council_v1 16.7%, period_bandit_v1 25.0%.

Weakest matchups of level_k_gate_v2: l5_hunter 0.0%, l5_wide_hunter 0.0%, vote_council_v1 0.0%, replay_hunter_gate_v2 0.0%, l2_council_v1 0.0%, anti_rps4_v1 25.0%.

## Analysis

Seed ladder (evaluate skill's head_to_head.py, threshold 36%, 250 rounds): the bandit 36.0% at 10 seeds, 36.8% at 25, 36.5% at 50, 37.4% [36.7%, 38.1%] at 100 (conclusive), lost 30.9%, worst match 30.0%; the gate 34.7% at 10, 34.5% [33.3%, 35.7%] at 25 (conclusive under). Mechanism: a decayed Dirichlet (0.85) and Thompson sharpened 3x switch arms within a few rounds, so they follow double_bluff_gate's flip-flopping counter, where a LEADER gate's undecayed record trails it (note 0032). Vs the pool it has no main bandit, so its weakest matchups are learners it doesn't replay (transition_matrix, period_detector, fast_greedy_markov, outcome_reader, smartbot_v1); the gate's main covers those, which is why the two tie overall. Next: classify it, and try it as a gated expert inside replay_hunter_wide (whose margin vs double_bluff_gate_v2 is -0.4 rounds per match).

## Verdict

**keep**. Equal vs random pools and simpler: level_k_bandit_normal - level_k_gate_v2 = -0.5 pts [-7.0, +6.0] over 200 paired matches (10 round robins), with two replays and no main bandit. Head to head it meets idea #40's goal vs double_bluff_gate_v2: 37.4% of rounds won [36.7%, 38.1%] over 100 seeds at 250 rounds (85 of 100 matches), where level_k_gate_v2 stays under 36% (34.5% [33.3%, 35.7%], 25 seeds).
