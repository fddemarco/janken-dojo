# 0097: replay_hunter_wide_v2 vs smartbot_sims_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** -
- **Candidates:** `bots/l3/anti_smartbot_sims_v3.yaml bots/l3/bayes_predators_v1.yaml bots/l3/counter_council_v1.yaml bots/l3/dropswitch_council_v1.yaml bots/l3/gate_bandit_period_v2.yaml bots/l3/gate_edge_smartbot_v2.yaml bots/l3/gate_fast_hold_v1.yaml bots/l3/gate_leader_v1.yaml bots/l3/gate_main_first_backoff_v1.yaml bots/l3/l2_council_v1.yaml bots/l3/leader_hunter_v2.yaml bots/l3/leader_new_l2_v1.yaml bots/l3/multiscale_council_v1.yaml bots/l3/naive_bayes_markov_v1.yaml bots/l3/predator_v2.yaml bots/l3/sicilian_meta_v1.yaml bots/l3/sims_lite_v1.yaml bots/l3/smartbot_wide_v1.yaml bots/l3/vote_council_v1.yaml bots/l4/double_bluff_gate_v2.yaml bots/l4/gate_edge_v3.yaml bots/l4/gate_main_first_stationary_v3.yaml bots/l4/gate_main_first_v3.yaml bots/l4/level_k_gate_v2.yaml bots/l4/replay_hunter_gate_v2.yaml bots/l4/replay_hunter_wide_v2.yaml`
- **Baselines:** `bots/l3/smartbot_sims_v2.yaml`
- **Run:** `20261013-191228_0097-field-l3-l4-vs-all-outsiders`
- **Verdict:** drop

## Hypothesis

A census, not a test: which field L3-L4 does best vs both outsider families; expected none clearly above smartbot_sims_v2 (notes 0091, 0096)

## Command

```bash
uv run janken lab experiment bots/l3/smartbot_sims_v2.yaml --rounds 250 --round-robins 30 --pool-size 6 --mode candidates --no-allow-small-pool --no-mocks --pool-list research/gauntlet/outsiders_all.txt --seed 762804797 --name 0097-field-l3-l4-vs-all-outsiders
```

## Results

30 of 30 round robin(s), pool 6, 250 rounds/match, seed 762804797, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| smartbot_sims_v2 | 180 | 89-15-76 | 53.6% [46.3%, 60.7%] | +0.8 | 0 | 1527 +/- 160 |

Weakest matchups of smartbot_sims_v2: outsider2_gate 38.3%, outsider2_greedy 46.7%, outsider_gate 53.3%, outsider2_council 55.0%, outsider_council 55.0%, outsider_greedy 73.3%.

## Analysis

-

## Verdict

**drop**. Void: a shell slip passed no candidates, so only the baseline played (smartbot_sims_v2 53.6% of matches vs both outsider families, +0.8 rounds). Rerun as note 0098.
