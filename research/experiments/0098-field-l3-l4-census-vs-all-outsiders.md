# 0098: anti_smartbot_sims_v3, bayes_predators_v1, counter_council_v1, dropswitch_council_v1, gate_bandit_period_v2, gate_edge_smartbot_v2, gate_fast_hold_v1, gate_leader_v1, gate_main_first_backoff_v1, l2_council_v1, leader_hunter_v2, leader_new_l2_v1, multiscale_council_v1, naive_bayes_markov_v1, predator_v2, sicilian_meta_v1, sims_lite_v1, smartbot_wide_v1, vote_council_v1, double_bluff_gate_v2, gate_edge_v3, gate_main_first_stationary_v3, gate_main_first_v3, level_k_gate_v2, replay_hunter_gate_v2, replay_hunter_wide_v2 vs smartbot_sims_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** -
- **Candidates:** `bots/l3/anti_smartbot_sims_v3.yaml`, `bots/l3/bayes_predators_v1.yaml`, `bots/l3/counter_council_v1.yaml`, `bots/l3/dropswitch_council_v1.yaml`, `bots/l3/gate_bandit_period_v2.yaml`, `bots/l3/gate_edge_smartbot_v2.yaml`, `bots/l3/gate_fast_hold_v1.yaml`, `bots/l3/gate_leader_v1.yaml`, `bots/l3/gate_main_first_backoff_v1.yaml`, `bots/l3/l2_council_v1.yaml`, `bots/l3/leader_hunter_v2.yaml`, `bots/l3/leader_new_l2_v1.yaml`, `bots/l3/multiscale_council_v1.yaml`, `bots/l3/naive_bayes_markov_v1.yaml`, `bots/l3/predator_v2.yaml`, `bots/l3/sicilian_meta_v1.yaml`, `bots/l3/sims_lite_v1.yaml`, `bots/l3/smartbot_wide_v1.yaml`, `bots/l3/vote_council_v1.yaml`, `bots/l4/double_bluff_gate_v2.yaml`, `bots/l4/gate_edge_v3.yaml`, `bots/l4/gate_main_first_stationary_v3.yaml`, `bots/l4/gate_main_first_v3.yaml`, `bots/l4/level_k_gate_v2.yaml`, `bots/l4/replay_hunter_gate_v2.yaml`, `bots/l4/replay_hunter_wide_v2.yaml`
- **Baselines:** `bots/l3/smartbot_sims_v2.yaml`
- **Run:** `20261013-191247_0098-field-l3-l4-census-vs-all-outsiders`
- **Verdict:** iterate

## Hypothesis

A census, not a test: which field L3-L4 does best vs both outsider families; expected none clearly above smartbot_sims_v2 (notes 0091, 0096)

## Command

```bash
uv run janken lab experiment bots/l3/anti_smartbot_sims_v3.yaml bots/l3/bayes_predators_v1.yaml bots/l3/counter_council_v1.yaml bots/l3/dropswitch_council_v1.yaml bots/l3/gate_bandit_period_v2.yaml bots/l3/gate_edge_smartbot_v2.yaml bots/l3/gate_fast_hold_v1.yaml bots/l3/gate_leader_v1.yaml bots/l3/gate_main_first_backoff_v1.yaml bots/l3/l2_council_v1.yaml bots/l3/leader_hunter_v2.yaml bots/l3/leader_new_l2_v1.yaml bots/l3/multiscale_council_v1.yaml bots/l3/naive_bayes_markov_v1.yaml bots/l3/predator_v2.yaml bots/l3/sicilian_meta_v1.yaml bots/l3/sims_lite_v1.yaml bots/l3/smartbot_wide_v1.yaml bots/l3/vote_council_v1.yaml bots/l4/double_bluff_gate_v2.yaml bots/l4/gate_edge_v3.yaml bots/l4/gate_main_first_stationary_v3.yaml bots/l4/gate_main_first_v3.yaml bots/l4/level_k_gate_v2.yaml bots/l4/replay_hunter_gate_v2.yaml bots/l4/replay_hunter_wide_v2.yaml bots/l3/smartbot_sims_v2.yaml --rounds 250 --round-robins 30 --pool-size 6 --mode candidates --no-allow-small-pool --no-mocks --pool-list research/gauntlet/outsiders_all.txt --seed 818637652 --name 0098-field-l3-l4-census-vs-all-outsiders
```

## Results

30 of 30 round robin(s), pool 6, 250 rounds/match, seed 818637652, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| sicilian_meta_v1 | 180 | 116-7-57 | 66.4% [59.2%, 72.9%] | +6.5 | 0 | 1602 +/- 74 |
| gate_edge_v3 | 180 | 110-5-65 | 62.5% [55.2%, 69.2%] | +4.3 | 0 | 1567 +/- 77 |
| counter_council_v1 | 180 | 107-4-69 | 60.6% [53.3%, 67.4%] | +3.7 | 0 | 1581 +/- 73 |
| smartbot_sims_v2 | 180 | 107-4-69 | 60.6% [53.3%, 67.4%] | +2.6 | 0 | 1437 +/- 72 |
| multiscale_council_v1 | 180 | 106-3-71 | 59.7% [52.4%, 66.6%] | +2.1 | 0 | 1545 +/- 60 |
| replay_hunter_gate_v2 | 180 | 103-5-72 | 58.6% [51.3%, 65.6%] | +3.7 | 0 | 1780 +/- 51 |
| predator_v2 | 180 | 102-5-73 | 58.1% [50.8%, 65.0%] | +3.5 | 0 | 1527 +/- 70 |
| vote_council_v1 | 180 | 102-2-76 | 57.2% [49.9%, 64.2%] | +2.3 | 0 | 1537 +/- 78 |
| dropswitch_council_v1 | 180 | 97-7-76 | 55.8% [48.5%, 62.9%] | +1.2 | 0 | 1512 +/- 89 |
| gate_edge_smartbot_v2 | 180 | 97-6-77 | 55.6% [48.3%, 62.6%] | +1.5 | 0 | 1443 +/- 59 |
| replay_hunter_wide_v2 | 180 | 95-9-76 | 55.3% [48.0%, 62.4%] | +3.3 | 0 | 1807 +/- 71 |
| gate_fast_hold_v1 | 180 | 94-8-78 | 54.4% [47.2%, 61.6%] | +1.1 | 0 | 1471 +/- 93 |
| gate_main_first_stationary_v3 | 180 | 94-4-82 | 53.3% [46.1%, 60.5%] | -0.2 | 0 | 1568 +/- 60 |
| gate_bandit_period_v2 | 180 | 92-4-84 | 52.2% [45.0%, 59.4%] | +0.8 | 0 | 1577 +/- 87 |
| gate_main_first_v3 | 180 | 87-2-91 | 48.9% [41.7%, 56.1%] | +1.1 | 0 | 1580 +/- 78 |
| l2_council_v1 | 180 | 85-5-90 | 48.6% [41.4%, 55.9%] | +0.8 | 0 | 1582 +/- 76 |
| smartbot_wide_v1 | 180 | 86-3-91 | 48.6% [41.4%, 55.9%] | -0.5 | 0 | 1439 +/- 90 |
| double_bluff_gate_v2 | 180 | 83-7-90 | 48.1% [40.9%, 55.3%] | +0.6 | 0 | 1535 +/- 86 |
| level_k_gate_v2 | 180 | 80-5-95 | 45.8% [38.7%, 53.1%] | -0.2 | 0 | 1614 +/- 86 |
| naive_bayes_markov_v1 | 180 | 73-7-100 | 42.5% [35.5%, 49.8%] | -2.9 | 0 | 1272 +/- 66 |
| gate_main_first_backoff_v1 | 180 | 73-3-104 | 41.4% [34.4%, 48.7%] | -4.5 | 0 | 1415 +/- 74 |
| leader_hunter_v2 | 180 | 68-8-104 | 40.0% [33.1%, 47.3%] | -3.6 | 0 | 1458 +/- 84 |
| bayes_predators_v1 | 180 | 64-5-111 | 36.9% [30.2%, 44.2%] | -4.8 | 0 | 1332 +/- 69 |
| anti_smartbot_sims_v3 | 180 | 64-1-115 | 35.8% [29.2%, 43.1%] | -20.1 | 0 | 1518 +/- 48 |
| leader_new_l2_v1 | 180 | 57-4-119 | 32.8% [26.3%, 39.9%] | -4.5 | 0 | 1310 +/- 83 |
| sims_lite_v1 | 180 | 42-2-136 | 23.9% [18.2%, 30.6%] | -24.2 | 0 | 1234 +/- 61 |
| gate_leader_v1 | 180 | 30-1-149 | 16.9% [12.2%, 23.1%] | -21.6 | 0 | 1200 +/- 59 |

Paired comparisons:

- `anti_smartbot_sims_v3 - bayes_predators_v1 = -1.1 pts [-10.6, +8.1]` over 180 shared matches: no significant difference
- `anti_smartbot_sims_v3 - counter_council_v1 = -24.7 pts [-34.7, -14.4]` over 180 shared matches: counter_council_v1 better
- `anti_smartbot_sims_v3 - dropswitch_council_v1 = -20.0 pts [-30.6, -9.4]` over 180 shared matches: dropswitch_council_v1 better
- `anti_smartbot_sims_v3 - gate_bandit_period_v2 = -16.4 pts [-25.0, -8.1]` over 180 shared matches: gate_bandit_period_v2 better
- `anti_smartbot_sims_v3 - gate_edge_smartbot_v2 = -19.7 pts [-28.1, -11.4]` over 180 shared matches: gate_edge_smartbot_v2 better
- `anti_smartbot_sims_v3 - gate_fast_hold_v1 = -18.6 pts [-26.7, -10.3]` over 180 shared matches: gate_fast_hold_v1 better
- `anti_smartbot_sims_v3 - gate_leader_v1 = +18.9 pts [+10.0, +27.8]` over 180 shared matches: anti_smartbot_sims_v3 better
- `anti_smartbot_sims_v3 - gate_main_first_backoff_v1 = -5.6 pts [-15.0, +3.3]` over 180 shared matches: no significant difference
- `anti_smartbot_sims_v3 - l2_council_v1 = -12.8 pts [-23.1, -3.1]` over 180 shared matches: l2_council_v1 better
- `anti_smartbot_sims_v3 - leader_hunter_v2 = -4.2 pts [-13.1, +4.7]` over 180 shared matches: no significant difference
- `anti_smartbot_sims_v3 - leader_new_l2_v1 = +3.1 pts [-6.7, +13.1]` over 180 shared matches: no significant difference
- `anti_smartbot_sims_v3 - multiscale_council_v1 = -23.9 pts [-33.6, -14.2]` over 180 shared matches: multiscale_council_v1 better
- `anti_smartbot_sims_v3 - naive_bayes_markov_v1 = -6.7 pts [-16.4, +3.1]` over 180 shared matches: no significant difference
- `anti_smartbot_sims_v3 - predator_v2 = -22.2 pts [-31.4, -13.3]` over 180 shared matches: predator_v2 better
- `anti_smartbot_sims_v3 - sicilian_meta_v1 = -30.6 pts [-39.2, -21.9]` over 180 shared matches: sicilian_meta_v1 better
- `anti_smartbot_sims_v3 - sims_lite_v1 = +11.9 pts [+3.6, +20.3]` over 180 shared matches: anti_smartbot_sims_v3 better
- `anti_smartbot_sims_v3 - smartbot_wide_v1 = -12.8 pts [-23.3, -1.9]` over 180 shared matches: smartbot_wide_v1 better
- `anti_smartbot_sims_v3 - vote_council_v1 = -21.4 pts [-31.7, -11.4]` over 180 shared matches: vote_council_v1 better
- `anti_smartbot_sims_v3 - double_bluff_gate_v2 = -12.2 pts [-22.2, -2.8]` over 180 shared matches: double_bluff_gate_v2 better
- `anti_smartbot_sims_v3 - gate_edge_v3 = -26.7 pts [-35.3, -18.1]` over 180 shared matches: gate_edge_v3 better
- `anti_smartbot_sims_v3 - gate_main_first_stationary_v3 = -17.5 pts [-26.4, -8.6]` over 180 shared matches: gate_main_first_stationary_v3 better
- `anti_smartbot_sims_v3 - gate_main_first_v3 = -13.1 pts [-21.7, -4.4]` over 180 shared matches: gate_main_first_v3 better
- `anti_smartbot_sims_v3 - level_k_gate_v2 = -10.0 pts [-18.9, -1.4]` over 180 shared matches: level_k_gate_v2 better
- `anti_smartbot_sims_v3 - replay_hunter_gate_v2 = -22.8 pts [-32.2, -12.8]` over 180 shared matches: replay_hunter_gate_v2 better
- `anti_smartbot_sims_v3 - replay_hunter_wide_v2 = -19.4 pts [-28.9, -9.7]` over 180 shared matches: replay_hunter_wide_v2 better
- `anti_smartbot_sims_v3 - smartbot_sims_v2 = -24.7 pts [-33.9, -15.8]` over 180 shared matches: smartbot_sims_v2 better
- `bayes_predators_v1 - counter_council_v1 = -23.6 pts [-33.1, -14.2]` over 180 shared matches: counter_council_v1 better
- `bayes_predators_v1 - dropswitch_council_v1 = -18.9 pts [-29.2, -9.2]` over 180 shared matches: dropswitch_council_v1 better
- `bayes_predators_v1 - gate_bandit_period_v2 = -15.3 pts [-25.6, -5.0]` over 180 shared matches: gate_bandit_period_v2 better
- `bayes_predators_v1 - gate_edge_smartbot_v2 = -18.6 pts [-27.5, -9.4]` over 180 shared matches: gate_edge_smartbot_v2 better
- `bayes_predators_v1 - gate_fast_hold_v1 = -17.5 pts [-27.5, -7.2]` over 180 shared matches: gate_fast_hold_v1 better
- `bayes_predators_v1 - gate_leader_v1 = +20.0 pts [+10.8, +28.6]` over 180 shared matches: bayes_predators_v1 better
- `bayes_predators_v1 - gate_main_first_backoff_v1 = -4.4 pts [-14.4, +6.1]` over 180 shared matches: no significant difference
- `bayes_predators_v1 - l2_council_v1 = -11.7 pts [-21.7, -2.5]` over 180 shared matches: l2_council_v1 better
- `bayes_predators_v1 - leader_hunter_v2 = -3.1 pts [-12.8, +6.7]` over 180 shared matches: no significant difference
- `bayes_predators_v1 - leader_new_l2_v1 = +4.2 pts [-5.3, +13.6]` over 180 shared matches: no significant difference
- `bayes_predators_v1 - multiscale_council_v1 = -22.8 pts [-32.8, -13.0]` over 180 shared matches: multiscale_council_v1 better
- `bayes_predators_v1 - naive_bayes_markov_v1 = -5.6 pts [-15.8, +5.0]` over 180 shared matches: no significant difference
- `bayes_predators_v1 - predator_v2 = -21.1 pts [-31.1, -11.1]` over 180 shared matches: predator_v2 better
- `bayes_predators_v1 - sicilian_meta_v1 = -29.4 pts [-39.2, -19.7]` over 180 shared matches: sicilian_meta_v1 better
- `bayes_predators_v1 - sims_lite_v1 = +13.1 pts [+4.4, +21.9]` over 180 shared matches: bayes_predators_v1 better
- `bayes_predators_v1 - smartbot_wide_v1 = -11.7 pts [-21.9, -1.7]` over 180 shared matches: smartbot_wide_v1 better
- `bayes_predators_v1 - vote_council_v1 = -20.3 pts [-30.0, -10.6]` over 180 shared matches: vote_council_v1 better
- `bayes_predators_v1 - double_bluff_gate_v2 = -11.1 pts [-21.4, -0.8]` over 180 shared matches: double_bluff_gate_v2 better
- `bayes_predators_v1 - gate_edge_v3 = -25.6 pts [-35.3, -16.1]` over 180 shared matches: gate_edge_v3 better
- `bayes_predators_v1 - gate_main_first_stationary_v3 = -16.4 pts [-26.4, -6.1]` over 180 shared matches: gate_main_first_stationary_v3 better
- `bayes_predators_v1 - gate_main_first_v3 = -11.9 pts [-21.7, -1.9]` over 180 shared matches: gate_main_first_v3 better
- `bayes_predators_v1 - level_k_gate_v2 = -8.9 pts [-18.6, +0.8]` over 180 shared matches: no significant difference
- `bayes_predators_v1 - replay_hunter_gate_v2 = -21.7 pts [-31.1, -12.2]` over 180 shared matches: replay_hunter_gate_v2 better
- `bayes_predators_v1 - replay_hunter_wide_v2 = -18.3 pts [-28.6, -7.8]` over 180 shared matches: replay_hunter_wide_v2 better
- `bayes_predators_v1 - smartbot_sims_v2 = -23.6 pts [-33.3, -13.9]` over 180 shared matches: smartbot_sims_v2 better
- `counter_council_v1 - dropswitch_council_v1 = +4.7 pts [-5.8, +15.3]` over 180 shared matches: no significant difference
- `counter_council_v1 - gate_bandit_period_v2 = +8.3 pts [-1.7, +18.6]` over 180 shared matches: no significant difference
- `counter_council_v1 - gate_edge_smartbot_v2 = +5.0 pts [-4.7, +14.7]` over 180 shared matches: no significant difference
- `counter_council_v1 - gate_fast_hold_v1 = +6.1 pts [-4.2, +16.4]` over 180 shared matches: no significant difference
- `counter_council_v1 - gate_leader_v1 = +43.6 pts [+34.2, +53.1]` over 180 shared matches: counter_council_v1 better
- `counter_council_v1 - gate_main_first_backoff_v1 = +19.2 pts [+9.2, +28.6]` over 180 shared matches: counter_council_v1 better
- `counter_council_v1 - l2_council_v1 = +11.9 pts [+1.7, +22.2]` over 180 shared matches: counter_council_v1 better
- `counter_council_v1 - leader_hunter_v2 = +20.6 pts [+11.4, +30.0]` over 180 shared matches: counter_council_v1 better
- `counter_council_v1 - leader_new_l2_v1 = +27.8 pts [+18.3, +37.2]` over 180 shared matches: counter_council_v1 better
- `counter_council_v1 - multiscale_council_v1 = +0.8 pts [-9.2, +11.1]` over 180 shared matches: no significant difference
- `counter_council_v1 - naive_bayes_markov_v1 = +18.1 pts [+9.2, +27.2]` over 180 shared matches: counter_council_v1 better
- `counter_council_v1 - predator_v2 = +2.5 pts [-8.1, +13.3]` over 180 shared matches: no significant difference
- `counter_council_v1 - sicilian_meta_v1 = -5.8 pts [-16.1, +4.2]` over 180 shared matches: no significant difference
- `counter_council_v1 - sims_lite_v1 = +36.7 pts [+27.5, +46.1]` over 180 shared matches: counter_council_v1 better
- `counter_council_v1 - smartbot_wide_v1 = +11.9 pts [+1.7, +21.9]` over 180 shared matches: counter_council_v1 better
- `counter_council_v1 - vote_council_v1 = +3.3 pts [-6.7, +13.3]` over 180 shared matches: no significant difference
- `counter_council_v1 - double_bluff_gate_v2 = +12.5 pts [+2.2, +22.5]` over 180 shared matches: counter_council_v1 better
- `counter_council_v1 - gate_edge_v3 = -1.9 pts [-12.5, +8.6]` over 180 shared matches: no significant difference
- `counter_council_v1 - gate_main_first_stationary_v3 = +7.2 pts [-2.5, +17.2]` over 180 shared matches: no significant difference
- `counter_council_v1 - gate_main_first_v3 = +11.7 pts [+1.9, +21.7]` over 180 shared matches: counter_council_v1 better
- `counter_council_v1 - level_k_gate_v2 = +14.7 pts [+4.7, +24.7]` over 180 shared matches: counter_council_v1 better
- `counter_council_v1 - replay_hunter_gate_v2 = +1.9 pts [-8.1, +11.9]` over 180 shared matches: no significant difference
- `counter_council_v1 - replay_hunter_wide_v2 = +5.3 pts [-5.3, +15.8]` over 180 shared matches: no significant difference
- `counter_council_v1 - smartbot_sims_v2 = +0.0 pts [-9.7, +9.7]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - gate_bandit_period_v2 = +3.6 pts [-6.4, +13.6]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - gate_edge_smartbot_v2 = +0.3 pts [-10.6, +11.7]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - gate_fast_hold_v1 = +1.4 pts [-8.1, +10.8]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - gate_leader_v1 = +38.9 pts [+30.3, +47.5]` over 180 shared matches: dropswitch_council_v1 better
- `dropswitch_council_v1 - gate_main_first_backoff_v1 = +14.4 pts [+3.6, +24.7]` over 180 shared matches: dropswitch_council_v1 better
- `dropswitch_council_v1 - l2_council_v1 = +7.2 pts [-3.3, +17.5]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - leader_hunter_v2 = +15.8 pts [+5.8, +25.6]` over 180 shared matches: dropswitch_council_v1 better
- `dropswitch_council_v1 - leader_new_l2_v1 = +23.1 pts [+13.3, +33.1]` over 180 shared matches: dropswitch_council_v1 better
- `dropswitch_council_v1 - multiscale_council_v1 = -3.9 pts [-14.2, +6.4]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - naive_bayes_markov_v1 = +13.3 pts [+2.8, +23.9]` over 180 shared matches: dropswitch_council_v1 better
- `dropswitch_council_v1 - predator_v2 = -2.2 pts [-11.9, +7.8]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - sicilian_meta_v1 = -10.6 pts [-20.0, -1.1]` over 180 shared matches: sicilian_meta_v1 better
- `dropswitch_council_v1 - sims_lite_v1 = +31.9 pts [+22.2, +41.7]` over 180 shared matches: dropswitch_council_v1 better
- `dropswitch_council_v1 - smartbot_wide_v1 = +7.2 pts [-2.8, +17.0]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - vote_council_v1 = -1.4 pts [-11.9, +9.4]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - double_bluff_gate_v2 = +7.8 pts [-2.8, +18.6]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - gate_edge_v3 = -6.7 pts [-16.9, +3.9]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - gate_main_first_stationary_v3 = +2.5 pts [-7.5, +12.2]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - gate_main_first_v3 = +6.9 pts [-3.9, +17.8]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - level_k_gate_v2 = +10.0 pts [-0.8, +20.8]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - replay_hunter_gate_v2 = -2.8 pts [-13.6, +7.8]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - replay_hunter_wide_v2 = +0.6 pts [-9.2, +10.6]` over 180 shared matches: no significant difference
- `dropswitch_council_v1 - smartbot_sims_v2 = -4.7 pts [-14.7, +5.3]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - gate_edge_smartbot_v2 = -3.3 pts [-13.6, +7.2]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - gate_fast_hold_v1 = -2.2 pts [-12.2, +7.8]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - gate_leader_v1 = +35.3 pts [+26.4, +43.9]` over 180 shared matches: gate_bandit_period_v2 better
- `gate_bandit_period_v2 - gate_main_first_backoff_v1 = +10.8 pts [+0.3, +21.1]` over 180 shared matches: gate_bandit_period_v2 better
- `gate_bandit_period_v2 - l2_council_v1 = +3.6 pts [-7.5, +14.4]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - leader_hunter_v2 = +12.2 pts [+3.1, +21.9]` over 180 shared matches: gate_bandit_period_v2 better
- `gate_bandit_period_v2 - leader_new_l2_v1 = +19.4 pts [+10.0, +29.4]` over 180 shared matches: gate_bandit_period_v2 better
- `gate_bandit_period_v2 - multiscale_council_v1 = -7.5 pts [-17.5, +2.8]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - naive_bayes_markov_v1 = +9.7 pts [-1.1, +20.3]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - predator_v2 = -5.8 pts [-15.6, +4.2]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - sicilian_meta_v1 = -14.2 pts [-24.4, -4.2]` over 180 shared matches: sicilian_meta_v1 better
- `gate_bandit_period_v2 - sims_lite_v1 = +28.3 pts [+19.2, +37.5]` over 180 shared matches: gate_bandit_period_v2 better
- `gate_bandit_period_v2 - smartbot_wide_v1 = +3.6 pts [-6.9, +14.4]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - vote_council_v1 = -5.0 pts [-15.0, +4.7]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - double_bluff_gate_v2 = +4.2 pts [-6.1, +14.2]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - gate_edge_v3 = -10.3 pts [-20.0, -0.3]` over 180 shared matches: gate_edge_v3 better
- `gate_bandit_period_v2 - gate_main_first_stationary_v3 = -1.1 pts [-11.4, +8.9]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - gate_main_first_v3 = +3.3 pts [-6.7, +13.1]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - level_k_gate_v2 = +6.4 pts [-3.3, +15.8]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - replay_hunter_gate_v2 = -6.4 pts [-16.4, +3.9]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - replay_hunter_wide_v2 = -3.1 pts [-12.5, +6.7]` over 180 shared matches: no significant difference
- `gate_bandit_period_v2 - smartbot_sims_v2 = -8.3 pts [-18.1, +1.1]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - gate_fast_hold_v1 = +1.1 pts [-8.3, +10.3]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - gate_leader_v1 = +38.6 pts [+29.7, +47.2]` over 180 shared matches: gate_edge_smartbot_v2 better
- `gate_edge_smartbot_v2 - gate_main_first_backoff_v1 = +14.2 pts [+4.2, +23.9]` over 180 shared matches: gate_edge_smartbot_v2 better
- `gate_edge_smartbot_v2 - l2_council_v1 = +6.9 pts [-2.8, +16.4]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - leader_hunter_v2 = +15.6 pts [+6.7, +24.7]` over 180 shared matches: gate_edge_smartbot_v2 better
- `gate_edge_smartbot_v2 - leader_new_l2_v1 = +22.8 pts [+13.1, +32.8]` over 180 shared matches: gate_edge_smartbot_v2 better
- `gate_edge_smartbot_v2 - multiscale_council_v1 = -4.2 pts [-14.2, +5.8]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - naive_bayes_markov_v1 = +13.1 pts [+3.1, +23.3]` over 180 shared matches: gate_edge_smartbot_v2 better
- `gate_edge_smartbot_v2 - predator_v2 = -2.5 pts [-11.4, +6.7]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - sicilian_meta_v1 = -10.8 pts [-20.6, -0.8]` over 180 shared matches: sicilian_meta_v1 better
- `gate_edge_smartbot_v2 - sims_lite_v1 = +31.7 pts [+22.8, +40.3]` over 180 shared matches: gate_edge_smartbot_v2 better
- `gate_edge_smartbot_v2 - smartbot_wide_v1 = +6.9 pts [-2.8, +16.4]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - vote_council_v1 = -1.7 pts [-11.9, +8.3]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - double_bluff_gate_v2 = +7.5 pts [-1.9, +16.9]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - gate_edge_v3 = -6.9 pts [-16.1, +2.5]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - gate_main_first_stationary_v3 = +2.2 pts [-7.5, +12.2]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - gate_main_first_v3 = +6.7 pts [-2.2, +15.8]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - level_k_gate_v2 = +9.7 pts [+0.8, +18.6]` over 180 shared matches: gate_edge_smartbot_v2 better
- `gate_edge_smartbot_v2 - replay_hunter_gate_v2 = -3.1 pts [-12.8, +6.7]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - replay_hunter_wide_v2 = +0.3 pts [-10.0, +10.6]` over 180 shared matches: no significant difference
- `gate_edge_smartbot_v2 - smartbot_sims_v2 = -5.0 pts [-14.4, +3.9]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - gate_leader_v1 = +37.5 pts [+28.6, +46.4]` over 180 shared matches: gate_fast_hold_v1 better
- `gate_fast_hold_v1 - gate_main_first_backoff_v1 = +13.1 pts [+3.3, +22.8]` over 180 shared matches: gate_fast_hold_v1 better
- `gate_fast_hold_v1 - l2_council_v1 = +5.8 pts [-4.2, +15.0]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - leader_hunter_v2 = +14.4 pts [+5.6, +23.1]` over 180 shared matches: gate_fast_hold_v1 better
- `gate_fast_hold_v1 - leader_new_l2_v1 = +21.7 pts [+11.9, +31.7]` over 180 shared matches: gate_fast_hold_v1 better
- `gate_fast_hold_v1 - multiscale_council_v1 = -5.3 pts [-15.8, +5.3]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - naive_bayes_markov_v1 = +11.9 pts [+1.9, +21.9]` over 180 shared matches: gate_fast_hold_v1 better
- `gate_fast_hold_v1 - predator_v2 = -3.6 pts [-12.5, +5.6]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - sicilian_meta_v1 = -11.9 pts [-21.1, -2.5]` over 180 shared matches: sicilian_meta_v1 better
- `gate_fast_hold_v1 - sims_lite_v1 = +30.6 pts [+22.2, +39.2]` over 180 shared matches: gate_fast_hold_v1 better
- `gate_fast_hold_v1 - smartbot_wide_v1 = +5.8 pts [-4.4, +16.4]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - vote_council_v1 = -2.8 pts [-12.5, +6.9]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - double_bluff_gate_v2 = +6.4 pts [-3.9, +16.4]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - gate_edge_v3 = -8.1 pts [-18.1, +1.7]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - gate_main_first_stationary_v3 = +1.1 pts [-8.6, +10.6]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - gate_main_first_v3 = +5.6 pts [-3.9, +15.0]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - level_k_gate_v2 = +8.6 pts [-1.1, +18.1]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - replay_hunter_gate_v2 = -4.2 pts [-14.4, +6.1]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - replay_hunter_wide_v2 = -0.8 pts [-11.1, +9.7]` over 180 shared matches: no significant difference
- `gate_fast_hold_v1 - smartbot_sims_v2 = -6.1 pts [-15.6, +3.6]` over 180 shared matches: no significant difference
- `gate_leader_v1 - gate_main_first_backoff_v1 = -24.4 pts [-33.6, -15.6]` over 180 shared matches: gate_main_first_backoff_v1 better
- `gate_leader_v1 - l2_council_v1 = -31.7 pts [-41.1, -22.2]` over 180 shared matches: l2_council_v1 better
- `gate_leader_v1 - leader_hunter_v2 = -23.1 pts [-32.2, -14.2]` over 180 shared matches: leader_hunter_v2 better
- `gate_leader_v1 - leader_new_l2_v1 = -15.8 pts [-24.7, -6.7]` over 180 shared matches: leader_new_l2_v1 better
- `gate_leader_v1 - multiscale_council_v1 = -42.8 pts [-51.4, -33.9]` over 180 shared matches: multiscale_council_v1 better
- `gate_leader_v1 - naive_bayes_markov_v1 = -25.6 pts [-35.3, -15.8]` over 180 shared matches: naive_bayes_markov_v1 better
- `gate_leader_v1 - predator_v2 = -41.1 pts [-49.7, -32.2]` over 180 shared matches: predator_v2 better
- `gate_leader_v1 - sicilian_meta_v1 = -49.4 pts [-58.3, -40.3]` over 180 shared matches: sicilian_meta_v1 better
- `gate_leader_v1 - sims_lite_v1 = -6.9 pts [-15.0, +1.4]` over 180 shared matches: no significant difference
- `gate_leader_v1 - smartbot_wide_v1 = -31.7 pts [-40.6, -22.8]` over 180 shared matches: smartbot_wide_v1 better
- `gate_leader_v1 - vote_council_v1 = -40.3 pts [-49.2, -31.7]` over 180 shared matches: vote_council_v1 better
- `gate_leader_v1 - double_bluff_gate_v2 = -31.1 pts [-40.3, -21.4]` over 180 shared matches: double_bluff_gate_v2 better
- `gate_leader_v1 - gate_edge_v3 = -45.6 pts [-54.4, -36.9]` over 180 shared matches: gate_edge_v3 better
- `gate_leader_v1 - gate_main_first_stationary_v3 = -36.4 pts [-45.6, -27.2]` over 180 shared matches: gate_main_first_stationary_v3 better
- `gate_leader_v1 - gate_main_first_v3 = -31.9 pts [-40.8, -23.1]` over 180 shared matches: gate_main_first_v3 better
- `gate_leader_v1 - level_k_gate_v2 = -28.9 pts [-38.1, -20.0]` over 180 shared matches: level_k_gate_v2 better
- `gate_leader_v1 - replay_hunter_gate_v2 = -41.7 pts [-50.8, -32.2]` over 180 shared matches: replay_hunter_gate_v2 better
- `gate_leader_v1 - replay_hunter_wide_v2 = -38.3 pts [-47.2, -29.4]` over 180 shared matches: replay_hunter_wide_v2 better
- `gate_leader_v1 - smartbot_sims_v2 = -43.6 pts [-52.8, -35.0]` over 180 shared matches: smartbot_sims_v2 better
- `gate_main_first_backoff_v1 - l2_council_v1 = -7.2 pts [-17.2, +2.8]` over 180 shared matches: no significant difference
- `gate_main_first_backoff_v1 - leader_hunter_v2 = +1.4 pts [-8.9, +11.4]` over 180 shared matches: no significant difference
- `gate_main_first_backoff_v1 - leader_new_l2_v1 = +8.6 pts [-1.1, +18.1]` over 180 shared matches: no significant difference
- `gate_main_first_backoff_v1 - multiscale_council_v1 = -18.3 pts [-28.1, -8.3]` over 180 shared matches: multiscale_council_v1 better
- `gate_main_first_backoff_v1 - naive_bayes_markov_v1 = -1.1 pts [-11.4, +9.4]` over 180 shared matches: no significant difference
- `gate_main_first_backoff_v1 - predator_v2 = -16.7 pts [-26.4, -6.7]` over 180 shared matches: predator_v2 better
- `gate_main_first_backoff_v1 - sicilian_meta_v1 = -25.0 pts [-34.4, -15.5]` over 180 shared matches: sicilian_meta_v1 better
- `gate_main_first_backoff_v1 - sims_lite_v1 = +17.5 pts [+8.1, +26.7]` over 180 shared matches: gate_main_first_backoff_v1 better
- `gate_main_first_backoff_v1 - smartbot_wide_v1 = -7.2 pts [-18.1, +3.3]` over 180 shared matches: no significant difference
- `gate_main_first_backoff_v1 - vote_council_v1 = -15.8 pts [-25.0, -6.1]` over 180 shared matches: vote_council_v1 better
- `gate_main_first_backoff_v1 - double_bluff_gate_v2 = -6.7 pts [-17.2, +3.6]` over 180 shared matches: no significant difference
- `gate_main_first_backoff_v1 - gate_edge_v3 = -21.1 pts [-30.6, -11.7]` over 180 shared matches: gate_edge_v3 better
- `gate_main_first_backoff_v1 - gate_main_first_stationary_v3 = -11.9 pts [-21.4, -2.5]` over 180 shared matches: gate_main_first_stationary_v3 better
- `gate_main_first_backoff_v1 - gate_main_first_v3 = -7.5 pts [-16.4, +1.4]` over 180 shared matches: no significant difference
- `gate_main_first_backoff_v1 - level_k_gate_v2 = -4.4 pts [-13.6, +4.7]` over 180 shared matches: no significant difference
- `gate_main_first_backoff_v1 - replay_hunter_gate_v2 = -17.2 pts [-26.9, -7.2]` over 180 shared matches: replay_hunter_gate_v2 better
- `gate_main_first_backoff_v1 - replay_hunter_wide_v2 = -13.9 pts [-23.9, -3.6]` over 180 shared matches: replay_hunter_wide_v2 better
- `gate_main_first_backoff_v1 - smartbot_sims_v2 = -19.2 pts [-28.1, -10.0]` over 180 shared matches: smartbot_sims_v2 better
- `l2_council_v1 - leader_hunter_v2 = +8.6 pts [-0.8, +18.6]` over 180 shared matches: no significant difference
- `l2_council_v1 - leader_new_l2_v1 = +15.8 pts [+5.8, +26.1]` over 180 shared matches: l2_council_v1 better
- `l2_council_v1 - multiscale_council_v1 = -11.1 pts [-20.8, -0.8]` over 180 shared matches: multiscale_council_v1 better
- `l2_council_v1 - naive_bayes_markov_v1 = +6.1 pts [-3.9, +16.4]` over 180 shared matches: no significant difference
- `l2_council_v1 - predator_v2 = -9.4 pts [-19.2, +0.8]` over 180 shared matches: no significant difference
- `l2_council_v1 - sicilian_meta_v1 = -17.8 pts [-26.9, -7.8]` over 180 shared matches: sicilian_meta_v1 better
- `l2_council_v1 - sims_lite_v1 = +24.7 pts [+15.6, +33.9]` over 180 shared matches: l2_council_v1 better
- `l2_council_v1 - smartbot_wide_v1 = +0.0 pts [-10.3, +10.8]` over 180 shared matches: no significant difference
- `l2_council_v1 - vote_council_v1 = -8.6 pts [-18.3, +1.7]` over 180 shared matches: no significant difference
- `l2_council_v1 - double_bluff_gate_v2 = +0.6 pts [-8.9, +10.0]` over 180 shared matches: no significant difference
- `l2_council_v1 - gate_edge_v3 = -13.9 pts [-24.2, -3.3]` over 180 shared matches: gate_edge_v3 better
- `l2_council_v1 - gate_main_first_stationary_v3 = -4.7 pts [-14.2, +5.3]` over 180 shared matches: no significant difference
- `l2_council_v1 - gate_main_first_v3 = -0.3 pts [-11.1, +10.8]` over 180 shared matches: no significant difference
- `l2_council_v1 - level_k_gate_v2 = +2.8 pts [-6.4, +12.5]` over 180 shared matches: no significant difference
- `l2_council_v1 - replay_hunter_gate_v2 = -10.0 pts [-20.0, +0.6]` over 180 shared matches: no significant difference
- `l2_council_v1 - replay_hunter_wide_v2 = -6.7 pts [-17.2, +4.5]` over 180 shared matches: no significant difference
- `l2_council_v1 - smartbot_sims_v2 = -11.9 pts [-21.7, -1.9]` over 180 shared matches: smartbot_sims_v2 better
- `leader_hunter_v2 - leader_new_l2_v1 = +7.2 pts [-2.8, +17.5]` over 180 shared matches: no significant difference
- `leader_hunter_v2 - multiscale_council_v1 = -19.7 pts [-29.7, -9.4]` over 180 shared matches: multiscale_council_v1 better
- `leader_hunter_v2 - naive_bayes_markov_v1 = -2.5 pts [-12.2, +6.7]` over 180 shared matches: no significant difference
- `leader_hunter_v2 - predator_v2 = -18.1 pts [-27.5, -8.1]` over 180 shared matches: predator_v2 better
- `leader_hunter_v2 - sicilian_meta_v1 = -26.4 pts [-36.4, -16.4]` over 180 shared matches: sicilian_meta_v1 better
- `leader_hunter_v2 - sims_lite_v1 = +16.1 pts [+7.8, +24.4]` over 180 shared matches: leader_hunter_v2 better
- `leader_hunter_v2 - smartbot_wide_v1 = -8.6 pts [-19.2, +2.2]` over 180 shared matches: no significant difference
- `leader_hunter_v2 - vote_council_v1 = -17.2 pts [-28.1, -7.2]` over 180 shared matches: vote_council_v1 better
- `leader_hunter_v2 - double_bluff_gate_v2 = -8.1 pts [-18.1, +1.4]` over 180 shared matches: no significant difference
- `leader_hunter_v2 - gate_edge_v3 = -22.5 pts [-32.2, -12.8]` over 180 shared matches: gate_edge_v3 better
- `leader_hunter_v2 - gate_main_first_stationary_v3 = -13.3 pts [-21.9, -5.0]` over 180 shared matches: gate_main_first_stationary_v3 better
- `leader_hunter_v2 - gate_main_first_v3 = -8.9 pts [-18.6, +0.8]` over 180 shared matches: no significant difference
- `leader_hunter_v2 - level_k_gate_v2 = -5.8 pts [-15.8, +3.6]` over 180 shared matches: no significant difference
- `leader_hunter_v2 - replay_hunter_gate_v2 = -18.6 pts [-28.1, -9.2]` over 180 shared matches: replay_hunter_gate_v2 better
- `leader_hunter_v2 - replay_hunter_wide_v2 = -15.3 pts [-25.3, -5.3]` over 180 shared matches: replay_hunter_wide_v2 better
- `leader_hunter_v2 - smartbot_sims_v2 = -20.6 pts [-30.0, -11.1]` over 180 shared matches: smartbot_sims_v2 better
- `leader_new_l2_v1 - multiscale_council_v1 = -26.9 pts [-37.2, -16.9]` over 180 shared matches: multiscale_council_v1 better
- `leader_new_l2_v1 - naive_bayes_markov_v1 = -9.7 pts [-18.9, -0.3]` over 180 shared matches: naive_bayes_markov_v1 better
- `leader_new_l2_v1 - predator_v2 = -25.3 pts [-35.3, -15.6]` over 180 shared matches: predator_v2 better
- `leader_new_l2_v1 - sicilian_meta_v1 = -33.6 pts [-43.3, -24.2]` over 180 shared matches: sicilian_meta_v1 better
- `leader_new_l2_v1 - sims_lite_v1 = +8.9 pts [-0.8, +18.9]` over 180 shared matches: no significant difference
- `leader_new_l2_v1 - smartbot_wide_v1 = -15.8 pts [-25.3, -6.4]` over 180 shared matches: smartbot_wide_v1 better
- `leader_new_l2_v1 - vote_council_v1 = -24.4 pts [-34.5, -14.2]` over 180 shared matches: vote_council_v1 better
- `leader_new_l2_v1 - double_bluff_gate_v2 = -15.3 pts [-25.6, -5.3]` over 180 shared matches: double_bluff_gate_v2 better
- `leader_new_l2_v1 - gate_edge_v3 = -29.7 pts [-40.3, -19.2]` over 180 shared matches: gate_edge_v3 better
- `leader_new_l2_v1 - gate_main_first_stationary_v3 = -20.6 pts [-31.4, -10.0]` over 180 shared matches: gate_main_first_stationary_v3 better
- `leader_new_l2_v1 - gate_main_first_v3 = -16.1 pts [-26.4, -5.8]` over 180 shared matches: gate_main_first_v3 better
- `leader_new_l2_v1 - level_k_gate_v2 = -13.1 pts [-23.6, -2.8]` over 180 shared matches: level_k_gate_v2 better
- `leader_new_l2_v1 - replay_hunter_gate_v2 = -25.8 pts [-35.6, -16.1]` over 180 shared matches: replay_hunter_gate_v2 better
- `leader_new_l2_v1 - replay_hunter_wide_v2 = -22.5 pts [-31.9, -13.1]` over 180 shared matches: replay_hunter_wide_v2 better
- `leader_new_l2_v1 - smartbot_sims_v2 = -27.8 pts [-38.1, -18.1]` over 180 shared matches: smartbot_sims_v2 better
- `multiscale_council_v1 - naive_bayes_markov_v1 = +17.2 pts [+7.2, +26.9]` over 180 shared matches: multiscale_council_v1 better
- `multiscale_council_v1 - predator_v2 = +1.7 pts [-8.1, +11.7]` over 180 shared matches: no significant difference
- `multiscale_council_v1 - sicilian_meta_v1 = -6.7 pts [-15.6, +2.5]` over 180 shared matches: no significant difference
- `multiscale_council_v1 - sims_lite_v1 = +35.8 pts [+26.4, +45.0]` over 180 shared matches: multiscale_council_v1 better
- `multiscale_council_v1 - smartbot_wide_v1 = +11.1 pts [+0.6, +21.4]` over 180 shared matches: multiscale_council_v1 better
- `multiscale_council_v1 - vote_council_v1 = +2.5 pts [-7.2, +12.2]` over 180 shared matches: no significant difference
- `multiscale_council_v1 - double_bluff_gate_v2 = +11.7 pts [+1.4, +21.9]` over 180 shared matches: multiscale_council_v1 better
- `multiscale_council_v1 - gate_edge_v3 = -2.8 pts [-12.5, +7.2]` over 180 shared matches: no significant difference
- `multiscale_council_v1 - gate_main_first_stationary_v3 = +6.4 pts [-3.9, +16.7]` over 180 shared matches: no significant difference
- `multiscale_council_v1 - gate_main_first_v3 = +10.8 pts [+1.1, +20.6]` over 180 shared matches: multiscale_council_v1 better
- `multiscale_council_v1 - level_k_gate_v2 = +13.9 pts [+3.6, +24.4]` over 180 shared matches: multiscale_council_v1 better
- `multiscale_council_v1 - replay_hunter_gate_v2 = +1.1 pts [-9.2, +11.7]` over 180 shared matches: no significant difference
- `multiscale_council_v1 - replay_hunter_wide_v2 = +4.4 pts [-5.6, +14.7]` over 180 shared matches: no significant difference
- `multiscale_council_v1 - smartbot_sims_v2 = -0.8 pts [-10.6, +8.9]` over 180 shared matches: no significant difference
- `naive_bayes_markov_v1 - predator_v2 = -15.6 pts [-25.8, -5.0]` over 180 shared matches: predator_v2 better
- `naive_bayes_markov_v1 - sicilian_meta_v1 = -23.9 pts [-32.8, -15.0]` over 180 shared matches: sicilian_meta_v1 better
- `naive_bayes_markov_v1 - sims_lite_v1 = +18.6 pts [+9.4, +27.5]` over 180 shared matches: naive_bayes_markov_v1 better
- `naive_bayes_markov_v1 - smartbot_wide_v1 = -6.1 pts [-15.8, +3.6]` over 180 shared matches: no significant difference
- `naive_bayes_markov_v1 - vote_council_v1 = -14.7 pts [-25.0, -4.4]` over 180 shared matches: vote_council_v1 better
- `naive_bayes_markov_v1 - double_bluff_gate_v2 = -5.6 pts [-14.7, +3.6]` over 180 shared matches: no significant difference
- `naive_bayes_markov_v1 - gate_edge_v3 = -20.0 pts [-30.0, -10.0]` over 180 shared matches: gate_edge_v3 better
- `naive_bayes_markov_v1 - gate_main_first_stationary_v3 = -10.8 pts [-20.8, -0.6]` over 180 shared matches: gate_main_first_stationary_v3 better
- `naive_bayes_markov_v1 - gate_main_first_v3 = -6.4 pts [-16.7, +3.9]` over 180 shared matches: no significant difference
- `naive_bayes_markov_v1 - level_k_gate_v2 = -3.3 pts [-13.6, +6.7]` over 180 shared matches: no significant difference
- `naive_bayes_markov_v1 - replay_hunter_gate_v2 = -16.1 pts [-26.1, -6.1]` over 180 shared matches: replay_hunter_gate_v2 better
- `naive_bayes_markov_v1 - replay_hunter_wide_v2 = -12.8 pts [-21.9, -3.6]` over 180 shared matches: replay_hunter_wide_v2 better
- `naive_bayes_markov_v1 - smartbot_sims_v2 = -18.1 pts [-27.8, -8.1]` over 180 shared matches: smartbot_sims_v2 better
- `predator_v2 - sicilian_meta_v1 = -8.3 pts [-18.1, +1.1]` over 180 shared matches: no significant difference
- `predator_v2 - sims_lite_v1 = +34.2 pts [+25.3, +42.8]` over 180 shared matches: predator_v2 better
- `predator_v2 - smartbot_wide_v1 = +9.4 pts [-1.1, +19.7]` over 180 shared matches: no significant difference
- `predator_v2 - vote_council_v1 = +0.8 pts [-9.2, +10.6]` over 180 shared matches: no significant difference
- `predator_v2 - double_bluff_gate_v2 = +10.0 pts [-0.8, +19.7]` over 180 shared matches: no significant difference
- `predator_v2 - gate_edge_v3 = -4.4 pts [-13.9, +4.7]` over 180 shared matches: no significant difference
- `predator_v2 - gate_main_first_stationary_v3 = +4.7 pts [-5.6, +14.7]` over 180 shared matches: no significant difference
- `predator_v2 - gate_main_first_v3 = +9.2 pts [-0.6, +18.9]` over 180 shared matches: no significant difference
- `predator_v2 - level_k_gate_v2 = +12.2 pts [+2.2, +21.4]` over 180 shared matches: predator_v2 better
- `predator_v2 - replay_hunter_gate_v2 = -0.6 pts [-10.3, +9.2]` over 180 shared matches: no significant difference
- `predator_v2 - replay_hunter_wide_v2 = +2.8 pts [-6.9, +12.5]` over 180 shared matches: no significant difference
- `predator_v2 - smartbot_sims_v2 = -2.5 pts [-11.7, +6.7]` over 180 shared matches: no significant difference
- `sicilian_meta_v1 - sims_lite_v1 = +42.5 pts [+33.9, +50.8]` over 180 shared matches: sicilian_meta_v1 better
- `sicilian_meta_v1 - smartbot_wide_v1 = +17.8 pts [+7.2, +28.1]` over 180 shared matches: sicilian_meta_v1 better
- `sicilian_meta_v1 - vote_council_v1 = +9.2 pts [-0.8, +18.6]` over 180 shared matches: no significant difference
- `sicilian_meta_v1 - double_bluff_gate_v2 = +18.3 pts [+8.1, +28.1]` over 180 shared matches: sicilian_meta_v1 better
- `sicilian_meta_v1 - gate_edge_v3 = +3.9 pts [-5.8, +13.6]` over 180 shared matches: no significant difference
- `sicilian_meta_v1 - gate_main_first_stationary_v3 = +13.1 pts [+3.3, +22.8]` over 180 shared matches: sicilian_meta_v1 better
- `sicilian_meta_v1 - gate_main_first_v3 = +17.5 pts [+8.1, +27.2]` over 180 shared matches: sicilian_meta_v1 better
- `sicilian_meta_v1 - level_k_gate_v2 = +20.6 pts [+11.1, +29.7]` over 180 shared matches: sicilian_meta_v1 better
- `sicilian_meta_v1 - replay_hunter_gate_v2 = +7.8 pts [-1.9, +17.8]` over 180 shared matches: no significant difference
- `sicilian_meta_v1 - replay_hunter_wide_v2 = +11.1 pts [+1.1, +21.1]` over 180 shared matches: sicilian_meta_v1 better
- `sicilian_meta_v1 - smartbot_sims_v2 = +5.8 pts [-4.2, +15.6]` over 180 shared matches: no significant difference
- `sims_lite_v1 - smartbot_wide_v1 = -24.7 pts [-35.0, -14.2]` over 180 shared matches: smartbot_wide_v1 better
- `sims_lite_v1 - vote_council_v1 = -33.3 pts [-43.3, -23.3]` over 180 shared matches: vote_council_v1 better
- `sims_lite_v1 - double_bluff_gate_v2 = -24.2 pts [-33.6, -14.4]` over 180 shared matches: double_bluff_gate_v2 better
- `sims_lite_v1 - gate_edge_v3 = -38.6 pts [-47.5, -29.4]` over 180 shared matches: gate_edge_v3 better
- `sims_lite_v1 - gate_main_first_stationary_v3 = -29.4 pts [-38.1, -20.6]` over 180 shared matches: gate_main_first_stationary_v3 better
- `sims_lite_v1 - gate_main_first_v3 = -25.0 pts [-34.4, -15.3]` over 180 shared matches: gate_main_first_v3 better
- `sims_lite_v1 - level_k_gate_v2 = -21.9 pts [-31.1, -13.1]` over 180 shared matches: level_k_gate_v2 better
- `sims_lite_v1 - replay_hunter_gate_v2 = -34.7 pts [-43.3, -25.8]` over 180 shared matches: replay_hunter_gate_v2 better
- `sims_lite_v1 - replay_hunter_wide_v2 = -31.4 pts [-41.1, -21.4]` over 180 shared matches: replay_hunter_wide_v2 better
- `sims_lite_v1 - smartbot_sims_v2 = -36.7 pts [-45.3, -28.3]` over 180 shared matches: smartbot_sims_v2 better
- `smartbot_wide_v1 - vote_council_v1 = -8.6 pts [-19.4, +1.7]` over 180 shared matches: no significant difference
- `smartbot_wide_v1 - double_bluff_gate_v2 = +0.6 pts [-9.4, +10.6]` over 180 shared matches: no significant difference
- `smartbot_wide_v1 - gate_edge_v3 = -13.9 pts [-24.4, -3.6]` over 180 shared matches: gate_edge_v3 better
- `smartbot_wide_v1 - gate_main_first_stationary_v3 = -4.7 pts [-15.6, +5.8]` over 180 shared matches: no significant difference
- `smartbot_wide_v1 - gate_main_first_v3 = -0.3 pts [-10.3, +9.4]` over 180 shared matches: no significant difference
- `smartbot_wide_v1 - level_k_gate_v2 = +2.8 pts [-7.5, +13.1]` over 180 shared matches: no significant difference
- `smartbot_wide_v1 - replay_hunter_gate_v2 = -10.0 pts [-20.6, +0.8]` over 180 shared matches: no significant difference
- `smartbot_wide_v1 - replay_hunter_wide_v2 = -6.7 pts [-16.7, +3.1]` over 180 shared matches: no significant difference
- `smartbot_wide_v1 - smartbot_sims_v2 = -11.9 pts [-22.8, -1.1]` over 180 shared matches: smartbot_sims_v2 better
- `vote_council_v1 - double_bluff_gate_v2 = +9.2 pts [-1.4, +19.7]` over 180 shared matches: no significant difference
- `vote_council_v1 - gate_edge_v3 = -5.3 pts [-15.8, +5.6]` over 180 shared matches: no significant difference
- `vote_council_v1 - gate_main_first_stationary_v3 = +3.9 pts [-7.0, +14.7]` over 180 shared matches: no significant difference
- `vote_council_v1 - gate_main_first_v3 = +8.3 pts [-2.2, +18.9]` over 180 shared matches: no significant difference
- `vote_council_v1 - level_k_gate_v2 = +11.4 pts [+0.3, +21.9]` over 180 shared matches: vote_council_v1 better
- `vote_council_v1 - replay_hunter_gate_v2 = -1.4 pts [-11.4, +8.9]` over 180 shared matches: no significant difference
- `vote_council_v1 - replay_hunter_wide_v2 = +1.9 pts [-7.8, +11.9]` over 180 shared matches: no significant difference
- `vote_council_v1 - smartbot_sims_v2 = -3.3 pts [-13.1, +6.4]` over 180 shared matches: no significant difference
- `double_bluff_gate_v2 - gate_edge_v3 = -14.4 pts [-23.6, -5.0]` over 180 shared matches: gate_edge_v3 better
- `double_bluff_gate_v2 - gate_main_first_stationary_v3 = -5.3 pts [-15.6, +5.3]` over 180 shared matches: no significant difference
- `double_bluff_gate_v2 - gate_main_first_v3 = -0.8 pts [-10.8, +9.2]` over 180 shared matches: no significant difference
- `double_bluff_gate_v2 - level_k_gate_v2 = +2.2 pts [-6.7, +11.4]` over 180 shared matches: no significant difference
- `double_bluff_gate_v2 - replay_hunter_gate_v2 = -10.6 pts [-20.6, +0.0]` over 180 shared matches: no significant difference
- `double_bluff_gate_v2 - replay_hunter_wide_v2 = -7.2 pts [-17.2, +3.1]` over 180 shared matches: no significant difference
- `double_bluff_gate_v2 - smartbot_sims_v2 = -12.5 pts [-22.5, -2.5]` over 180 shared matches: smartbot_sims_v2 better
- `gate_edge_v3 - gate_main_first_stationary_v3 = +9.2 pts [+0.3, +18.1]` over 180 shared matches: gate_edge_v3 better
- `gate_edge_v3 - gate_main_first_v3 = +13.6 pts [+4.7, +22.5]` over 180 shared matches: gate_edge_v3 better
- `gate_edge_v3 - level_k_gate_v2 = +16.7 pts [+6.9, +26.4]` over 180 shared matches: gate_edge_v3 better
- `gate_edge_v3 - replay_hunter_gate_v2 = +3.9 pts [-6.1, +13.9]` over 180 shared matches: no significant difference
- `gate_edge_v3 - replay_hunter_wide_v2 = +7.2 pts [-3.3, +17.5]` over 180 shared matches: no significant difference
- `gate_edge_v3 - smartbot_sims_v2 = +1.9 pts [-7.8, +11.7]` over 180 shared matches: no significant difference
- `gate_main_first_stationary_v3 - gate_main_first_v3 = +4.4 pts [-4.7, +13.6]` over 180 shared matches: no significant difference
- `gate_main_first_stationary_v3 - level_k_gate_v2 = +7.5 pts [-1.9, +16.1]` over 180 shared matches: no significant difference
- `gate_main_first_stationary_v3 - replay_hunter_gate_v2 = -5.3 pts [-15.3, +5.3]` over 180 shared matches: no significant difference
- `gate_main_first_stationary_v3 - replay_hunter_wide_v2 = -1.9 pts [-12.2, +8.1]` over 180 shared matches: no significant difference
- `gate_main_first_stationary_v3 - smartbot_sims_v2 = -7.2 pts [-16.7, +2.2]` over 180 shared matches: no significant difference
- `gate_main_first_v3 - level_k_gate_v2 = +3.1 pts [-6.1, +12.5]` over 180 shared matches: no significant difference
- `gate_main_first_v3 - replay_hunter_gate_v2 = -9.7 pts [-19.7, +0.6]` over 180 shared matches: no significant difference
- `gate_main_first_v3 - replay_hunter_wide_v2 = -6.4 pts [-16.1, +3.1]` over 180 shared matches: no significant difference
- `gate_main_first_v3 - smartbot_sims_v2 = -11.7 pts [-21.4, -2.2]` over 180 shared matches: smartbot_sims_v2 better
- `level_k_gate_v2 - replay_hunter_gate_v2 = -12.8 pts [-23.1, -1.7]` over 180 shared matches: replay_hunter_gate_v2 better
- `level_k_gate_v2 - replay_hunter_wide_v2 = -9.4 pts [-19.7, +0.6]` over 180 shared matches: no significant difference
- `level_k_gate_v2 - smartbot_sims_v2 = -14.7 pts [-23.9, -5.6]` over 180 shared matches: smartbot_sims_v2 better
- `replay_hunter_gate_v2 - replay_hunter_wide_v2 = +3.3 pts [-6.7, +12.8]` over 180 shared matches: no significant difference
- `replay_hunter_gate_v2 - smartbot_sims_v2 = -1.9 pts [-11.9, +7.8]` over 180 shared matches: no significant difference
- `replay_hunter_wide_v2 - smartbot_sims_v2 = -5.3 pts [-14.7, +3.6]` over 180 shared matches: no significant difference

Weakest matchups of anti_smartbot_sims_v3: outsider2_gate 0.0%, outsider2_council 0.0%, outsider_gate 23.3%, outsider2_greedy 28.3%, outsider_greedy 80.0%, outsider_council 83.3%.

Weakest matchups of bayes_predators_v1: outsider_gate 21.7%, outsider2_greedy 30.0%, outsider_greedy 36.7%, outsider_council 38.3%, outsider2_gate 41.7%, outsider2_council 53.3%.

Weakest matchups of counter_council_v1: outsider_gate 48.3%, outsider_council 56.7%, outsider2_council 58.3%, outsider2_greedy 58.3%, outsider_greedy 68.3%, outsider2_gate 73.3%.

Weakest matchups of dropswitch_council_v1: outsider_greedy 35.0%, outsider2_council 53.3%, outsider2_greedy 55.0%, outsider_council 61.7%, outsider_gate 61.7%, outsider2_gate 68.3%.

Weakest matchups of gate_bandit_period_v2: outsider2_council 28.3%, outsider2_gate 40.0%, outsider_gate 43.3%, outsider2_greedy 55.0%, outsider_council 73.3%, outsider_greedy 73.3%.

Weakest matchups of gate_edge_smartbot_v2: outsider2_gate 36.7%, outsider2_greedy 43.3%, outsider_gate 48.3%, outsider2_council 48.3%, outsider_greedy 76.7%, outsider_council 80.0%.

Weakest matchups of gate_fast_hold_v1: outsider2_greedy 35.0%, outsider2_gate 35.0%, outsider2_council 38.3%, outsider_gate 60.0%, outsider_greedy 76.7%, outsider_council 81.7%.

Weakest matchups of gate_leader_v1: outsider2_greedy 6.7%, outsider_greedy 13.3%, outsider2_council 16.7%, outsider_council 20.0%, outsider2_gate 21.7%, outsider_gate 23.3%.

Weakest matchups of gate_main_first_backoff_v1: outsider2_greedy 6.7%, outsider2_gate 31.7%, outsider2_council 40.0%, outsider_gate 50.0%, outsider_council 55.0%, outsider_greedy 65.0%.

Weakest matchups of l2_council_v1: outsider2_gate 35.0%, outsider2_council 40.0%, outsider_council 43.3%, outsider2_greedy 48.3%, outsider_greedy 53.3%, outsider_gate 71.7%.

Weakest matchups of leader_hunter_v2: outsider2_council 21.7%, outsider2_greedy 23.3%, outsider2_gate 26.7%, outsider_gate 41.7%, outsider_greedy 61.7%, outsider_council 65.0%.

Weakest matchups of leader_new_l2_v1: outsider2_greedy 25.0%, outsider_council 25.0%, outsider_gate 26.7%, outsider_greedy 35.0%, outsider2_council 40.0%, outsider2_gate 45.0%.

Weakest matchups of multiscale_council_v1: outsider2_greedy 48.3%, outsider2_council 53.3%, outsider_greedy 56.7%, outsider_council 60.0%, outsider_gate 70.0%, outsider2_gate 70.0%.

Weakest matchups of naive_bayes_markov_v1: outsider2_greedy 26.7%, outsider_gate 38.3%, outsider_greedy 43.3%, outsider2_council 48.3%, outsider2_gate 48.3%, outsider_council 50.0%.

Weakest matchups of predator_v2: outsider_gate 46.7%, outsider2_greedy 51.7%, outsider2_gate 55.0%, outsider2_council 56.7%, outsider_greedy 65.0%, outsider_council 73.3%.

Weakest matchups of sicilian_meta_v1: outsider2_gate 56.7%, outsider2_greedy 60.0%, outsider_council 65.0%, outsider2_council 68.3%, outsider_gate 68.3%, outsider_greedy 80.0%.

Weakest matchups of sims_lite_v1: outsider2_gate 0.0%, outsider2_greedy 0.0%, outsider_gate 5.0%, outsider_greedy 36.7%, outsider2_council 40.0%, outsider_council 61.7%.

Weakest matchups of smartbot_wide_v1: outsider_council 28.3%, outsider_gate 40.0%, outsider2_greedy 46.7%, outsider2_council 50.0%, outsider_greedy 63.3%, outsider2_gate 63.3%.

Weakest matchups of vote_council_v1: outsider2_greedy 46.7%, outsider2_gate 48.3%, outsider_council 50.0%, outsider2_council 53.3%, outsider_greedy 55.0%, outsider_gate 90.0%.

Weakest matchups of double_bluff_gate_v2: outsider_gate 43.3%, outsider_greedy 43.3%, outsider2_greedy 48.3%, outsider2_gate 48.3%, outsider2_council 51.7%, outsider_council 53.3%.

Weakest matchups of gate_edge_v3: outsider_gate 33.3%, outsider2_greedy 56.7%, outsider2_gate 58.3%, outsider2_council 63.3%, outsider_greedy 80.0%, outsider_council 83.3%.

Weakest matchups of gate_main_first_stationary_v3: outsider2_council 28.3%, outsider2_gate 43.3%, outsider_gate 46.7%, outsider2_greedy 50.0%, outsider_council 71.7%, outsider_greedy 80.0%.

Weakest matchups of gate_main_first_v3: outsider2_council 21.7%, outsider2_greedy 40.0%, outsider2_gate 46.7%, outsider_gate 46.7%, outsider_council 48.3%, outsider_greedy 90.0%.

Weakest matchups of level_k_gate_v2: outsider2_council 26.7%, outsider2_greedy 28.3%, outsider_gate 36.7%, outsider2_gate 38.3%, outsider_council 71.7%, outsider_greedy 73.3%.

Weakest matchups of replay_hunter_gate_v2: outsider2_gate 40.0%, outsider_gate 51.7%, outsider_greedy 58.3%, outsider_council 61.7%, outsider2_council 70.0%, outsider2_greedy 70.0%.

Weakest matchups of replay_hunter_wide_v2: outsider2_gate 46.7%, outsider_gate 50.0%, outsider2_council 51.7%, outsider_council 53.3%, outsider2_greedy 61.7%, outsider_greedy 68.3%.

Weakest matchups of smartbot_sims_v2: outsider2_greedy 41.7%, outsider_gate 48.3%, outsider2_council 56.7%, outsider2_gate 60.0%, outsider_council 75.0%, outsider_greedy 81.7%.

## Analysis

-

## Verdict

**iterate**. Census of the 27 field L3-L4s vs both outsider families (6-bot pools, 30 round robins, 180 matches each): sicilian_meta_v1 leads with 66.4% of matches (+6.5 rounds), +5.8 pts [-4.2, +15.6] over smartbot_sims_v2 (60.6%), not significant and exposed to the winner's curse; the best L4 replay_hunter_wide_v2 is 11th (55.3%), level_k_gate_v2 19th (45.8%), and bots built to read named field bots (anti_smartbot_sims_v3, sims_lite_v1, gate_leader_v1) fall to 17-36%. Next: confirm sicilian_meta_v1 on fresh seeds. (A first resume crashed mid-run in the engine's flush with no error printed; the second resume completed it.)
