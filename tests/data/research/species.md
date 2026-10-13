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
| `biased` | L1 | `biased_v1` | `biased` (2026-10-11 rename) --> v1 | |
| `copycat` | L1 | `copycat_v1` | `copycat` (2026-10-11 rename) --> v1 | |
| `counter_reactionary` | L1 | `counter_reactionary_v1` | `counter_reactionary` (2026-10-11 rename) --> v1 | |
| `cycler` | L1 | `cycler_v1` | `cycler` (2026-10-11 rename) --> v1 | |
| `frequency` | L1 | `frequency_v1` | `frequency` (2026-10-11 rename) --> v1 | |
| `geometry` | L1 | `geometry_v1` | `geometry` (2026-10-11 rename) --> v1 | |
| `markov2_joint` | L1 | `markov2_joint_v1` | `markov2_joint` (2026-10-11 rename) --> v1 | |
| `nash` | L1 | `nash_v1` | `nash` (2026-10-11 rename) --> v1 | |
| `pattern_memory` | L1 | `pattern_memory_v1` | `pattern_memory` (2026-10-11 rename) --> v1 | |
| `reactionary` | L1 | `reactionary_v1` | `reactionary` (2026-10-11 rename) --> v1 | |
| `rock` | L1 | `rock_v1` | `rock` (2026-10-11 rename) --> v1 | |
| `self_beater` | L1 | `self_beater_v1` | `self_beater` (2026-10-11 rename) --> v1 | |
| `transition_matrix` | L1 | `transition_matrix_v1` | `transition_matrix` (2026-10-11 rename) --> v1 | |
| `word2janken` | L1 | `word2janken_v1` | `word2janken` (2026-10-11 rename) --> v1 | |
| `wsls` | L1 | `wsls_v1` | `wsls` (2026-10-11 rename) --> v1 | |
| `iocaine_lite` | L2 | `iocaine_lite_v1` | `iocaine_lite` (2026-10-11 rename) --> v1 | |
| `rps4_lite` | L2 | `rps4_lite_v1` | `rps4_lite` (2026-10-11 rename) --> v1 | |
| `smartbot_fast` | L2 | `smartbot_fast_v1` | `smartbot_fast` (2026-10-11 rename) --> v1 | |
| `smartbot` | L2 | `smartbot_v1` | `smartbot` (2026-10-11 rename) --> v1 | |
| `word2janken_scoreboard` | L2 | `word2janken_scoreboard_v1` | `word2janken_scoreboard` (2026-10-11 rename) --> v1 | |
| `anti_smartbot_sims` | L3 | `anti_smartbot_sims_v1` | `anti_smartbot_sims` (2026-10-11 rename) --> v1 | |
| `smartbot_sims` | L3 | `smartbot_sims_v1` | `smartbot_sims` (2026-10-11 rename) --> v1 | |
| `gate_edge` | L4 | `gate_edge_v1` | `gate_edge` (2026-10-11 rename) --> v1 | |
