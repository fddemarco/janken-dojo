# 0034: replay_hunter_wide vs replay_hunter_gate_v1 (whole field, 250 rounds)

- **Date:** 2026-10-12
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #44
- **Candidates:** `bots/l4/replay_hunter_wide.yaml`
- **Baselines:** `bots/l4/replay_hunter_gate_v1.yaml`
- **Run:** `20261012-173356_0034-replay-hunter-wide-vs-replay-hunter-gate`
- **Verdict:** keep
- **Species:** `replay_hunter_wide_v1` (new species)

## Hypothesis

Four more replays lift the remaining replayable matchups: head to head (seed ladder, 10 seeds) replay_hunter_wide wins 41.2% vs mirror_bandit, 59.2% vs dropswitch_matcher, 56.8% vs anti_rps4, 38.5% vs smartbot_wide, 39.8% vs smartbot_sims_v2, every one conclusive above 36%. Over the whole field replay_hunter_wide - replay_hunter_gate_v1 >= 0 pts. Under 36% of rounds should remain only the samplers (nash, sampled_markov, transition_matrix, geometry) and double_bluff_gate_v1 (an L4).

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_wide.yaml bots/l4/replay_hunter_gate_v1.yaml --rounds 250 --round-robins 5 --pool-size 63 --mode candidates --allow-small-pool --no-mocks --seed 1270068519 --name 0034-replay-hunter-wide-vs-replay-hunter-gate
```

## Results

5 of 5 round robin(s), pool 63, 250 rounds/match, seed 1270068519, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide | 315 | 281-7-27 | 90.3% [86.5%, 93.1%] | +66.4 | 0 | 1891 +/- 47 |
| replay_hunter_gate_v1 | 315 | 267-1-47 | 84.9% [80.5%, 88.5%] | +63.2 | 0 | 1853 +/- 42 |

Paired comparisons:

- `replay_hunter_wide - replay_hunter_gate_v1 = +5.4 pts [+0.8, +10.0]` over 315 shared matches: replay_hunter_wide better

Weakest matchups of replay_hunter_wide: bayes_predators_v1 50.0%, transition_matrix_v1 50.0%, sampled_markov_v1 60.0%, geometry_v1 60.0%, biased_v1 60.0%, period_detector_v1 60.0%.

Weakest matchups of replay_hunter_gate_v1: smartbot_wide_v1 20.0%, geometry_ensemble_v1 20.0%, multiscale_council_v1 20.0%, nash_v1 40.0%, sampled_markov_v1 40.0%, geometry_v1 40.0%.

## Analysis

The 11 left under 36%: two L4s an L4 can't replay (double_bluff_gate_v1 32.2%, replay_hunter_gate_v1 32.6%, its own predecessor: near-equals split the rounds); the samplers (sampled_markov 33.6%, transition_matrix 34.5%, nash 34.5%, geometry 35.6%), whose moves are fresh randomness; biased_v1 35.5% (a fixed distribution worth 50% to an always-paper: the LEADER gate's replay arms crowd out the main bandit's frequency arms; a frequency expert as in gate_main_first_stationary would take it); and replayable learners not yet covered, all within 0.5 pts of the bar over 5 matches (geometry_ensemble 34.6%, leader_hunter 35.7%, period_detector 35.8%, sicilian_meta 35.8%). Cost: 25.8s per 10 matches vs rock (replay_hunter_gate_v1 18.5s, level_k_gate_v1 8.7s). A >= 36% bar vs every bot is out of reach by construction: an L4 can't replay the other strong L4s, and samplers can't be predicted.

## Verdict

**keep**. replay_hunter_wide beats replay_hunter_gate_v1 over the whole field, +5.4 pts [+0.8, +10.0] over 315 paired matches (5 round robins of the 63-bot field, 250 rounds, mode candidates; inconclusive at 1 and 3, conclusive at 5), 281-7-27 vs the field. Head to head (seed ladder, 10 seeds) its four new replays win 59.2% of rounds vs dropswitch_matcher, 56.8% vs anti_rps4, 41.2% vs mirror_bandit, 38.5% vs smartbot_wide, and it keeps 39.8% vs smartbot_sims_v2. Over 5 matches per opponent it is under 36% of rounds vs 11 of 64 bots (replay_hunter_gate_v1: 14 of 63), worst 32.2% (double_bluff_gate_v1), mean 50.9%.

## Species

**new**: its core agrees with replay_hunter_gate_v1 on 76% of the moves, below 80%.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `replay_hunter_gate_v1` | L4 | 76.3% |
| `level_k_gate_v1` | L4 | 73.8% |
| `gate_main_first_v2` | L4 | 71.5% |
| `gate_main_first_stationary_v2` | L4 | 71.4% |
| `double_bluff_gate_v1` | L4 | 65.3% |
