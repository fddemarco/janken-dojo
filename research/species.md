# Species

The field holds one bot per species, its current version: `bots/<level>/<species>_vN.yaml`.
A kept bot is classified with `janken species classify` (`/classify`): a **new species**
(named, version 1), the **next version** of one (it is no worse on any matchup and better
on at least one; the old version moves to `bots/inactive/legacy/`), or a **variant** (it
behaves like a species without beating it, and moves to `bots/inactive/legacy/`).
How it decides: [docs/experiments.md](../docs/experiments.md#species).

`versions` is each species' lineage: the stem every version had before it was
classified, and the note that decided it. The CLI edits this table; keep the rows.

| species | level | current | versions | variants |
|---|---|---|---|---|
| `anti_frequency` | L1 | `anti_frequency_v1` | `anti_frequency` (2026-10-11 rename) --> v1 | |
| `biased` | L1 | `biased_v1` | `biased` (2026-10-11 rename) --> v1 | |
| `copycat` | L1 | `copycat_v1` | `copycat` (2026-10-11 rename) --> v1 | |
| `counter_reactionary` | L1 | `counter_reactionary_v1` | `counter_reactionary` (2026-10-11 rename) --> v1 | |
| `cycler` | L1 | `cycler_v1` | `cycler` (2026-10-11 rename) --> v1 | |
| `frequency` | L1 | `frequency_v1` | `frequency` (2026-10-11 rename) --> v1 | |
| `geometry` | L1 | `geometry_v1` | `geometry` (2026-10-11 rename) --> v1 | |
| `markov2_joint` | L1 | `markov2_joint_v1` | `markov2_joint` (2026-10-11 rename) --> v1 | |
| `nash` | L1 | `nash_v1` | `nash` (2026-10-11 rename) --> v1 | |
| `pattern_memory` | L1 | `pattern_memory_v1` | `pattern_memory` (2026-10-11 rename) --> v1 | `word2janken_v1` (2026-10-12 fused: 83.2% core agreement, -8.4 pts [-12.7, -4.2] vs pattern_memory_v1, 40 pools) |
| `reactionary` | L1 | `reactionary_v1` | `reactionary` (2026-10-11 rename) --> v1 | |
| `rock` | L1 | `rock_v1` | `rock` (2026-10-11 rename) --> v1 | |
| `rotation_outcome` | L1 | `rotation_outcome_v1` | `rotation_outcome` (2026-10-11 rename) --> v1 | |
| `self_beater` | L1 | `self_beater_v1` | `self_beater` (2026-10-11 rename) --> v1 | |
| `transition_matrix` | L1 | `transition_matrix_v1` | `transition_matrix` (2026-10-11 rename) --> v1 | |
| `wsls` | L1 | `wsls_v1` | `wsls` (2026-10-11 rename) --> v1 | |
| `balancer_hunter` | L1 | `balancer_hunter_v1` | `balancer_hunter` (2026-10-12 seeded) --> v1 | |
| `period_detector` | L1 | `period_detector_v1` | `period_detector` (2026-10-12 seeded) --> v1 | |
| `score_reader` | L1 | `score_reader_v1` | `score_reader` (2026-10-12 seeded) --> v1 | |
| `iocaine_lite` | L2 | `iocaine_lite_v1` | `iocaine_lite` (2026-10-11 rename) --> v1 | |
| `rps4_lite` | L2 | `rps4_lite_v1` | `rps4_lite` (2026-10-11 rename) --> v1 | |
| `smartbot_fast` | L2 | `smartbot_fast_v1` | `smartbot_fast` (2026-10-11 rename) --> v1 | |
| `smartbot` | L2 | `smartbot_v1` | `smartbot` (2026-10-11 rename) --> v1 | |
| `anti_iocaine` | L2 | `anti_iocaine_v1` | `anti_iocaine` (2026-10-12 seeded) --> v1 | |
| `anti_rps4` | L2 | `anti_rps4_v1` | `anti_rps4` (2026-10-12 seeded) --> v1 | |
| `zoo_hunter` | L2 | `zoo_hunter_v1` | `zoo_hunter` (2026-10-12 seeded) --> v1 | |
| `second_guess` | L2 | `second_guess_v1` | `second_guess` (2026-10-12 seeded) --> v1 | |
| `dropswitch_matcher` | L2 | `dropswitch_matcher_v1` | `dropswitch_matcher` (2026-10-12 seeded) --> v1 | |
| `vote_ensemble` | L2 | `vote_ensemble_v1` | `vote_ensemble` (2026-10-12 seeded) --> v1 | |
| `mirror_bandit` | L2 | `mirror_bandit_v1` | `mirror_bandit` (2026-10-12 seeded) --> v1 | |
| `period_bandit` | L2 | `period_bandit_v1` | `period_bandit` (2026-10-12 seeded) --> v1 | |
| `fast_greedy_markov` | L2 | `fast_greedy_markov_v1` | `fast_greedy_markov` (2026-10-12 seeded) --> v1 | |
| `geometry_ensemble` | L2 | `geometry_ensemble_v1` | `geometry_ensemble` (2026-10-12 seeded) --> v1 | |
| `backoff_family` | L2 | `backoff_family_v1` | `backoff_family` (2026-10-12 seeded) --> v1 | |
| `outcome_reader` | L2 | `outcome_reader_v1` | `outcome_reader` (2026-10-12 seeded) --> v1 | |
| `multiscale` | L2 | `multiscale_v1` | `multiscale` (2026-10-12 seeded) --> v1 | |
| `sampled_markov` | L2 | `sampled_markov_v1` | `sampled_markov` (2026-10-12 seeded) --> v1 | |
| `anti_smartbot` | L2 | `anti_smartbot_v1` | `anti_smartbot` (2026-10-12 seeded) --> v1 | |
| `anti_smartbot_sims` | L3 | `anti_smartbot_sims_v2` | `anti_smartbot_sims` (2026-10-11 rename) --> v1; `anti_smartbot_sims_v1` over smartbot_sims_v2 (2026-10-12) --> v2 | |
| `smartbot_sims` | L3 | `smartbot_sims_v2` | `smartbot_sims` (2026-10-11 rename) --> v1; `smartbot_sims_v1` minus the word2janken and word2janken_scoreboard sims (2026-10-12) --> v2 | |
| `l2_council` | L3 | `l2_council_v1` | `l2_council` (2026-10-12 seeded) --> v1 | |
| `naive_bayes_markov` | L3 | `naive_bayes_markov_v1` | `naive_bayes_markov` (2026-10-12 seeded) --> v1 | |
| `gate_leader` | L3 | `gate_leader_v1` | `gate_leader` (2026-10-12 seeded) --> v1 | |
| `predator` | L3 | `predator_v1` | `predator` (2026-10-12 seeded) --> v1 | |
| `leader_hunter` | L3 | `leader_hunter_v1` | `leader_hunter` (2026-10-12 seeded) --> v1 | |
| `gate_edge_smartbot` | L3 | `gate_edge_smartbot_v1` | `gate_edge_smartbot` (2026-10-12 seeded) --> v1 | |
| `gate_fast_hold` | L3 | `gate_fast_hold_v1` | `gate_fast_hold` (2026-10-12 seeded) --> v1 | |
| `gate_bandit_period` | L3 | `gate_bandit_period_v1` | `gate_bandit_period` (2026-10-12 seeded) --> v1 | |
| `gate_main_first_backoff` | L3 | `gate_main_first_backoff_v1` | `gate_main_first_backoff` (2026-10-12 seeded) --> v1 | |
| `leader_new_l2` | L3 | `leader_new_l2_v1` | `leader_new_l2` (2026-10-12 seeded) --> v1 | |
| `vote_council` | L3 | `vote_council_v1` | `vote_council` (2026-10-12 seeded) --> v1 | |
| `dropswitch_council` | L3 | `dropswitch_council_v1` | `dropswitch_council` (2026-10-12 seeded) --> v1 | |
| `counter_council` | L3 | `counter_council_v1` | `counter_council` (2026-10-12 seeded) --> v1 | |
| `sims_lite` | L3 | `sims_lite_v1` | `sims_lite` (2026-10-12 seeded) --> v1 | |
| `sicilian_meta` | L3 | `sicilian_meta_v1` | `sicilian_meta` (2026-10-12 seeded) --> v1 | |
| `multiscale_council` | L3 | `multiscale_council_v1` | `multiscale_council` (2026-10-12 seeded) --> v1 | |
| `bayes_predators` | L3 | `bayes_predators_v1` | `bayes_predators` (2026-10-12 seeded) --> v1 | |
| `smartbot_wide` | L3 | `smartbot_wide_v1` | `smartbot_wide` (2026-10-12 seeded) --> v1 | |
| `gate_edge` | L4 | `gate_edge_v2` | `gate_edge` (2026-10-11 rename) --> v1; `gate_edge_v1` over smartbot_sims_v2 (2026-10-12) --> v2 | |
| `gate_main_first_stationary` | L4 | `gate_main_first_stationary_v2` | `gate_main_first_stationary` (2026-10-11 rename) --> v1; `gate_main_first_stationary_v1` over smartbot_sims_v2 (2026-10-12) --> v2 | |
| `gate_main_first` | L4 | `gate_main_first_v2` | `gate_main_first` (2026-10-11 rename) --> v1; `gate_main_first_v1` over smartbot_sims_v2 (2026-10-12) --> v2 | `gate_anti_first_v1` (2026-10-12 fused: 93.1% core agreement, -0.6 pts [-4.6, +3.4] vs gate_main_first_v1, 40 pools) |
| `double_bluff_gate` | L4 | `double_bluff_gate_v1` | `gate_counter_sims` ([0031](experiments/0031-counter-anti-sims-vs-smartbot-sims.md)) --> v1 | |
| `level_k_gate` | L4 | `level_k_gate_v1` | `level_k_gate` ([0032](experiments/0032-level-k-vs-double-bluff-gate.md)) --> v1 | |
