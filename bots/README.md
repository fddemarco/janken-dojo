# Bots

One YAML file per bot (grammar: [docs/writing-bots.md](../docs/writing-bots.md)); its
tuning space, when it has one, is `spaces/<name>.yaml`. The field is the level folders:
each bot sits in the folder of its level, computed from the blueprint
(`janken/kit/levels.py`; `janken bot check` refuses a bot in the wrong one), and stems
are unique across them. Pools, tournaments and `janken bot list` read the level folders
only, never `inactive/`.

```
bots/
  l1/                the zoo's heuristics
  l2/                bandits over L1 arms: smartbot and its variants, iocaine, rps4
  l3/                smartbot_sims and its specialist
  l4/                the gatekeepers
  oracle/            the research-only Oracles
  inactive/          bots out of the field
    fleets/iliad_v3/ the Iliad v3 fleet: a champion and four supports (Team overlay)
    legacy/          retired bots, kept for the research record
```

## The field

| level | bot | what it does |
|---|---|---|
| L1 | `rock` | always rock (optional noise) |
| L1 | `nash` | uniform random, the Nash equilibrium |
| L1 | `biased` | a weighted coin over the three moves |
| L1 | `cycler` | rock → paper → scissors (or the reverse) |
| L1 | `copycat` | plays the opponent's last move |
| L1 | `reactionary` | beats the opponent's last move |
| L1 | `counter_reactionary` | after a win, beats the beat of its own last move |
| L1 | `self_beater` | beats its own last move |
| L1 | `wsls` | win-stay, lose-shift |
| L1 | `frequency` | beats the opponent's most frequent move |
| L1 | `anti_frequency` | beats the move that beats our most frequent move |
| L1 | `transition_matrix` | order-1 opponent transitions, sampled |
| L1 | `markov2_joint` | order-2 Markov model on the joint history |
| L1 | `pattern_memory` | longest earlier repeat of the joint history |
| L1 | `rotation_outcome` | learned win-stay/lose-shift (rotation by outcome) |
| L1 | `geometry` | Superant's RPS Geometry |
| L1 | `word2janken` | variable-order n-gram with a 12% noise floor |
| L2 | `word2janken_scoreboard` | scoreboard of word2janken's predictor, its counter and counter-counter |
| L2 | `iocaine_lite` | Iocaine Powder's sicilian reasoning over three predictors |
| L2 | `rps4_lite` | Rpscontest #4 in miniature: Markov orders 0-3, greedy arms |
| L2 | `smartbot` | 18 predictors × 3 arms, Thompson sampling (Kaggle 1st place) |
| L2 | `smartbot_fast` | smartbot with faster memories (0.6, 0.6, 8) |
| L2 | `smartbot_staller` | smartbot plus stalling (random play on drawdown or a safe lead) |
| L3 | `smartbot_sims` | smartbot plus 10 "model of us" sims (replays of the metabots included) |
| L3 | `anti_smartbot_sims` | replays smartbot_sims exactly and beats its likeliest move |
| L4 | `gate_edge` | smartbot_sims's arms + anti expert, gated by EDGE |
| L4 | `gate_anti_first` | same experts, the anti expert first (ANTI_FIRST) |
| L4 | `gate_main_first` | same experts, the main arms first (MAIN_FIRST) — the fleet's core |
| L4 | `gate_main_first_stationary` | gate_main_first plus a stationary (frequency) expert |
| Oracle | `oracle_smartbot_sims`, `oracle_anti_smartbot_sims`, `oracle_gate_edge`, `oracle_gate_anti_first` | pure Oracles: calibrated win chances per level, drawn with `pool.mocks` |
| Oracle | `oracle_arm_gate_edge`, `oracle_arm_gate_anti_first` | gatekeepers whose anti expert is an Oracle arm |

Oracles cheat: they never enter a pool (unless `pool.mocks`), a tournament or an export.

## Renames

The research notes (`research/`) and the runs database keep the names a bot had when it
was run. Current names, and the old ones they replace:

| bot | was |
|---|---|
| `smartbot_sims` | `advanced_bot`, before that `smartbot_sims3` |
| `anti_smartbot_sims` | `anti_advanced_bots`, before that `mirror_sims3` |
| `smartbot_fast` | `meta_smartbot` |
| `smartbot_staller` | `smart_staller` |
| `word2janken_scoreboard` | `staller` (the kit preset is still `staller`) |
| `gate_edge` | `replay_gate` |
| `oracle_smartbot_sims` | `oracle_advanced_bot` |
| `oracle_anti_smartbot_sims` | `oracle_anti_advanced` |
| `oracle_gate_edge` | `oracle_replay_gate` |
| `oracle_arm_gate_edge` | `arm_replay_gate` |
| `oracle_arm_gate_anti_first` | `arm_gate_anti_first` |

Legacy bots and their old names: [inactive/legacy/README.md](inactive/legacy/README.md).
