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
| `iocaine_lite` | L2 | `iocaine_lite_v1` | v1 ← `iocaine_lite` (2026-10-11 rename) | |
| `rps4_lite` | L2 | `rps4_lite_v1` | v1 ← `rps4_lite` (2026-10-11 rename) | |
| `smartbot_fast` | L2 | `smartbot_fast_v1` | v1 ← `smartbot_fast` (2026-10-11 rename) | |
| `smartbot_staller` | L2 | `smartbot_staller_v1` | v1 ← `smartbot_staller` (2026-10-11 rename) | |
| `smartbot` | L2 | `smartbot_v1` | v1 ← `smartbot` (2026-10-11 rename) | |
| `word2janken_scoreboard` | L2 | `word2janken_scoreboard_v1` | v1 ← `word2janken_scoreboard` (2026-10-11 rename) | |
| `anti_smartbot_sims` | L3 | `anti_smartbot_sims_v1` | v1 ← `anti_smartbot_sims` (2026-10-11 rename) | |
| `smartbot_sims` | L3 | `smartbot_sims_v1` | v1 ← `smartbot_sims` (2026-10-11 rename) | |
| `gate_anti_first` | L4 | `gate_anti_first_v1` | v1 ← `gate_anti_first` (2026-10-11 rename) | |
| `gate_edge` | L4 | `gate_edge_v1` | v1 ← `gate_edge` (2026-10-11 rename) | |
| `gate_main_first_stationary` | L4 | `gate_main_first_stationary_v1` | v1 ← `gate_main_first_stationary` (2026-10-11 rename) | |
| `gate_main_first` | L4 | `gate_main_first_v1` | v1 ← `gate_main_first` (2026-10-11 rename) | |
