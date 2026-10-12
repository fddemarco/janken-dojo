# 0033: replay_hunter_gate vs level_k_gate_v1 (whole field, 250 rounds)

- **Date:** 2026-10-12
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #43
- **Candidates:** `bots/l4/replay_hunter_gate.yaml`
- **Baselines:** `bots/l4/level_k_gate_v1.yaml`
- **Run:** `20261012-171926_0033-replay-hunter-vs-level-k-gate`
- **Verdict:** keep
- **Species:** `replay_hunter_gate_v1` (new species)

## Hypothesis

Replays of the eight learners lift the matchups level_k_gate splits near 1/3: head to head (seed ladder, 10 seeds, 250 rounds) replay_hunter_gate wins 38-49% of rounds vs dropswitch_council, l2_council, counter_council, backoff_family, smartbot_fast, vote_council, period_bandit (level_k_gate: 31-34% over 0032's 5 matches each) and 39.7% vs smartbot_sims_v2, but 31.6% vs sampled_markov (it samples its moves: no fixed move to replay). Over the whole field replay_hunter_gate - level_k_gate_v1 >= 0 pts, and fewer opponents under 36% of rounds than level_k_gate's 24 of 63.

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_gate.yaml bots/l4/level_k_gate_v1.yaml --rounds 250 --round-robins 1 --pool-size 62 --mode candidates --allow-small-pool --no-mocks --seed 3349391478 --name 0033-replay-hunter-vs-level-k-gate
```

## Results

1 of 1 round robin(s), pool 62, 250 rounds/match, seed 3349391478, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_gate | 62 | 57-0-5 | 91.9% [82.5%, 96.5%] | +69.6 | 0 | 1922 +/- - |
| level_k_gate_v1 | 62 | 46-2-14 | 75.8% [63.8%, 84.8%] | +60.0 | 0 | 1747 +/- - |

Paired comparisons:

- `replay_hunter_gate - level_k_gate_v1 = +16.1 pts [+4.8, +28.2]` over 62 shared matches: replay_hunter_gate better

Weakest matchups of replay_hunter_gate: geometry_v1 0.0%, dropswitch_matcher_v1 0.0%, double_bluff_gate_v1 0.0%, mirror_bandit_v1 0.0%, nash_v1 0.0%, anti_rps4_v1 100.0%.

Weakest matchups of level_k_gate_v1: l2_council_v1 0.0%, anti_rps4_v1 0.0%, multiscale_council_v1 0.0%, sampled_markov_v1 0.0%, geometry_v1 0.0%, leader_hunter_v1 0.0%.

## Analysis

A learner's own replay from its seat names its likeliest move, and BEAT beats it: the Thompson learners (period_bandit, backoff_family, smartbot_fast, the councils) commit to their posterior mode most rounds, so a 256-draw replay predicts them like anti_smartbot_sims predicts smartbot_sims (38-49% of rounds); the greedy dropswitch_council and the vote-sampling vote_council replay at draws 0 (best-scored arm) and still give 47-49%. sampled_markov (n-grams that sample their predictions, flattened Thompson at SHARP 0.5) has no fixed move to replay: 31.6% won, 34.1% lost, like nash. In this run's single matches, still under 36%: geometry_v1 27.6%, transition_matrix_v1 32.8% and nash_v1 35.6% (samplers), sampled_markov_v1 33.6%, mirror_bandit_v1 28.8%, dropswitch_matcher_v1 33.6%, anti_rps4_v1 34.0%, smartbot_wide_v1 34.0% (learners without a replay yet), double_bluff_gate_v1 31.6% (an L4, not replayable in an L4), and l2_council_v1 34.4% and gate_main_first_stationary_v2 35.2% (both 38.1% over 10-25 seeds: one match is noisy). Cost: about 2x level_k_gate per match (18.5s vs 8.7s for 10 matches vs rock). Next: replay the remaining learners (mirror_bandit, dropswitch_matcher, smartbot_wide, rps4_lite from our side for anti_rps4).

## Verdict

**keep**. replay_hunter_gate beats level_k_gate_v1 over the whole field, +16.1 pts [+4.8, +28.2] over 62 paired matches (1 round robin of the 62-bot field, 250 rounds, mode candidates; conclusive at the ladder's first step), 57-0-5 vs the field. Head to head (seed ladder, 10 seeds) its learner replays lift the matchups level_k_gate split near 1/3: dropswitch_council 49.0%, vote_council 47.1%, smartbot_fast 43.3%, period_bandit 42.2%, backoff_family 41.2%, counter_council 38.6%, l2_council 38.1% of rounds (level_k_gate: 31-34%), all conclusive above 36%, smartbot_sims_v2 39.7%; sampled_markov 31.6% (it samples its moves).

## Species

**new**: its core agrees with level_k_gate_v1 on 75% of the moves, below 80%.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `level_k_gate_v1` | L4 | 74.8% |
| `gate_main_first_stationary_v2` | L4 | 71.0% |
| `gate_main_first_v2` | L4 | 71.0% |
| `double_bluff_gate_v1` | L4 | 65.8% |
| `gate_edge_v2` | L4 | 62.2% |
