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
| `anti_frequency` | L1 | `anti_frequency_v1` | v1 ← `anti_frequency` (2026-10-11 rename) | |
| `biased` | L1 | `biased_v1` | v1 ← `biased` (2026-10-11 rename) | |
| `copycat` | L1 | `copycat_v1` | v1 ← `copycat` (2026-10-11 rename) | |
| `counter_reactionary` | L1 | `counter_reactionary_v1` | v1 ← `counter_reactionary` (2026-10-11 rename) | |
| `cycler` | L1 | `cycler_v1` | v1 ← `cycler` (2026-10-11 rename) | |
| `frequency` | L1 | `frequency_v1` | v1 ← `frequency` (2026-10-11 rename) | |
| `geometry` | L1 | `geometry_v1` | v1 ← `geometry` (2026-10-11 rename) | |
| `markov2_joint` | L1 | `markov2_joint_v1` | v1 ← `markov2_joint` (2026-10-11 rename) | |
| `nash` | L1 | `nash_v1` | v1 ← `nash` (2026-10-11 rename) | |
| `pattern_memory` | L1 | `pattern_memory_v1` | v1 ← `pattern_memory` (2026-10-11 rename) | |
| `reactionary` | L1 | `reactionary_v1` | v1 ← `reactionary` (2026-10-11 rename) | |
| `rock` | L1 | `rock_v1` | v1 ← `rock` (2026-10-11 rename) | |
| `rotation_outcome` | L1 | `rotation_outcome_v1` | v1 ← `rotation_outcome` (2026-10-11 rename) | |
| `self_beater` | L1 | `self_beater_v1` | v1 ← `self_beater` (2026-10-11 rename) | |
| `transition_matrix` | L1 | `transition_matrix_v1` | v1 ← `transition_matrix` (2026-10-11 rename) | |
| `word2janken` | L1 | `word2janken_v1` | v1 ← `word2janken` (2026-10-11 rename) | |
| `wsls` | L1 | `wsls_v1` | v1 ← `wsls` (2026-10-11 rename) | |
| `balancer_hunter` | L1 | `balancer_hunter_v1` | v1 ← `balancer_hunter` (2026-10-12 seeded) | |
| `period_detector` | L1 | `period_detector_v1` | v1 ← `period_detector` (2026-10-12 seeded) | |
| `score_reader` | L1 | `score_reader_v1` | v1 ← `score_reader` (2026-10-12 seeded) | |
| `iocaine_lite` | L2 | `iocaine_lite_v1` | v1 ← `iocaine_lite` (2026-10-11 rename) | |
| `rps4_lite` | L2 | `rps4_lite_v1` | v1 ← `rps4_lite` (2026-10-11 rename) | |
| `smartbot_fast` | L2 | `smartbot_fast_v1` | v1 ← `smartbot_fast` (2026-10-11 rename) | |
| `smartbot` | L2 | `smartbot_v1` | v1 ← `smartbot` (2026-10-11 rename) | |
| `word2janken_scoreboard` | L2 | `word2janken_scoreboard_v1` | v1 ← `word2janken_scoreboard` (2026-10-11 rename) | |
| `anti_iocaine` | L2 | `anti_iocaine_v1` | v1 ← `anti_iocaine` (2026-10-12 seeded) | |
| `anti_rps4` | L2 | `anti_rps4_v1` | v1 ← `anti_rps4` (2026-10-12 seeded) | |
| `zoo_hunter` | L2 | `zoo_hunter_v1` | v1 ← `zoo_hunter` (2026-10-12 seeded) | |
| `second_guess` | L2 | `second_guess_v1` | v1 ← `second_guess` (2026-10-12 seeded) | |
| `dropswitch_matcher` | L2 | `dropswitch_matcher_v1` | v1 ← `dropswitch_matcher` (2026-10-12 seeded) | |
| `vote_ensemble` | L2 | `vote_ensemble_v1` | v1 ← `vote_ensemble` (2026-10-12 seeded) | |
| `mirror_bandit` | L2 | `mirror_bandit_v1` | v1 ← `mirror_bandit` (2026-10-12 seeded) | |
| `period_bandit` | L2 | `period_bandit_v1` | v1 ← `period_bandit` (2026-10-12 seeded) | |
| `fast_greedy_markov` | L2 | `fast_greedy_markov_v1` | v1 ← `fast_greedy_markov` (2026-10-12 seeded) | |
| `geometry_ensemble` | L2 | `geometry_ensemble_v1` | v1 ← `geometry_ensemble` (2026-10-12 seeded) | |
| `backoff_family` | L2 | `backoff_family_v1` | v1 ← `backoff_family` (2026-10-12 seeded) | |
| `outcome_reader` | L2 | `outcome_reader_v1` | v1 ← `outcome_reader` (2026-10-12 seeded) | |
| `multiscale` | L2 | `multiscale_v1` | v1 ← `multiscale` (2026-10-12 seeded) | |
| `sampled_markov` | L2 | `sampled_markov_v1` | v1 ← `sampled_markov` (2026-10-12 seeded) | |
| `anti_smartbot` | L2 | `anti_smartbot_v1` | v1 ← `anti_smartbot` (2026-10-12 seeded) | |
| `anti_smartbot_sims` | L3 | `anti_smartbot_sims_v1` | v1 ← `anti_smartbot_sims` (2026-10-11 rename) | |
| `smartbot_sims` | L3 | `smartbot_sims_v1` | v1 ← `smartbot_sims` (2026-10-11 rename) | |
| `l2_council` | L3 | `l2_council_v1` | v1 ← `l2_council` (2026-10-12 seeded) | |
| `naive_bayes_markov` | L3 | `naive_bayes_markov_v1` | v1 ← `naive_bayes_markov` (2026-10-12 seeded) | |
| `gate_leader` | L3 | `gate_leader_v1` | v1 ← `gate_leader` (2026-10-12 seeded) | |
| `predator` | L3 | `predator_v1` | v1 ← `predator` (2026-10-12 seeded) | |
| `leader_hunter` | L3 | `leader_hunter_v1` | v1 ← `leader_hunter` (2026-10-12 seeded) | |
| `gate_edge_smartbot` | L3 | `gate_edge_smartbot_v1` | v1 ← `gate_edge_smartbot` (2026-10-12 seeded) | |
| `gate_fast_hold` | L3 | `gate_fast_hold_v1` | v1 ← `gate_fast_hold` (2026-10-12 seeded) | |
| `gate_anti_first` | L4 | `gate_anti_first_v1` | v1 ← `gate_anti_first` (2026-10-11 rename) | |
| `gate_edge` | L4 | `gate_edge_v1` | v1 ← `gate_edge` (2026-10-11 rename) | |
| `gate_main_first_stationary` | L4 | `gate_main_first_stationary_v1` | v1 ← `gate_main_first_stationary` (2026-10-11 rename) | |
| `gate_main_first` | L4 | `gate_main_first_v1` | v1 ← `gate_main_first` (2026-10-11 rename) | |
