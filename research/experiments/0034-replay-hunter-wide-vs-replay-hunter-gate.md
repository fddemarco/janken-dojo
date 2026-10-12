# 0034: replay_hunter_wide vs replay_hunter_gate_v1 (whole field, 250 rounds)

- **Date:** 2026-10-12
- **Status:** run
- **Kind:** evaluation
- **Idea:** #44
- **Candidates:** `bots/l4/replay_hunter_wide.yaml`
- **Baselines:** `bots/l4/replay_hunter_gate_v1.yaml`
- **Run:** `20261012-173356_0034-replay-hunter-wide-vs-replay-hunter-gate`
- **Verdict:** -

## Hypothesis

Four more replays lift the remaining replayable matchups: head to head (seed ladder, 10 seeds) replay_hunter_wide wins 41.2% vs mirror_bandit, 59.2% vs dropswitch_matcher, 56.8% vs anti_rps4, 38.5% vs smartbot_wide, 39.8% vs smartbot_sims_v2, every one conclusive above 36%. Over the whole field replay_hunter_wide - replay_hunter_gate_v1 >= 0 pts. Under 36% of rounds should remain only the samplers (nash, sampled_markov, transition_matrix, geometry) and double_bluff_gate_v1 (an L4).

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_wide.yaml bots/l4/replay_hunter_gate_v1.yaml --rounds 250 --round-robins 3 --pool-size 63 --mode candidates --allow-small-pool --no-mocks --seed 1270068519 --name 0034-replay-hunter-wide-vs-replay-hunter-gate
```

## Results

3 of 3 round robin(s), pool 63, 250 rounds/match, seed 1270068519, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide | 189 | 166-4-19 | 88.9% [83.6%, 92.6%] | +66.4 | 0 | 1877 +/- 16 |
| replay_hunter_gate_v1 | 189 | 159-0-30 | 84.1% [78.2%, 88.6%] | +62.8 | 0 | 1845 +/- 57 |

Paired comparisons:

- `replay_hunter_wide - replay_hunter_gate_v1 = +4.8 pts [-1.6, +10.9]` over 189 shared matches: no significant difference

Weakest matchups of replay_hunter_wide: transition_matrix_v1 16.7%, leader_hunter_v1 33.3%, bayes_predators_v1 50.0%, nash_v1 66.7%, sampled_markov_v1 66.7%, sicilian_meta_v1 66.7%.

Weakest matchups of replay_hunter_gate_v1: smartbot_wide_v1 0.0%, multiscale_council_v1 0.0%, geometry_v1 0.0%, nash_v1 33.3%, geometry_ensemble_v1 33.3%, gate_main_first_backoff_v1 33.3%.

## Analysis

-

## Verdict

-
