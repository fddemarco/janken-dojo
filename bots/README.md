# Bots

One YAML file per bot (grammar: [docs/writing-bots.md](../docs/writing-bots.md)); its
tuning space, when it has one, is `spaces/<name>.yaml`. The field is the level folders:
each bot sits in the folder of its level, computed from the blueprint
(`janken/kit/levels.py`; `janken bot check` refuses a bot in the wrong one). Stems are
unique across every folder here. Pools, tournaments and `janken bot list` read the level
folders only, never `blocks/` or `inactive/`.

## Levels

- **L1**, a heuristic: one signal played with one rotation, no Bandit and no Gate.
- **L2**, a meta-heuristic: a Bandit or a Gate over L1s.
- **L3**: a Bandit or a Gate over L2s (and L1s).
- **L4**: a Bandit or a Gate over L3s (and L2s and L1s), and so on.

An aggregator's arms are bots, named (`{bot: frequency, arms: 2, space: {DECAY: [1.0, 0.9]}}`),
so every bot above L1 is built from the bots below it. A bot can name any bot here: a
field version, a block, a retired bot of `inactive/`.

## Species and versions

The field holds one bot per **species**, its current **version**: `<species>_vN.yaml`
(`smartbot_v1`, `smartbot_v2`, ...). A new bot starts with a plain stem (`janken bot new`
refuses a `_vN` one). Once it is kept, `janken species classify` decides what it is
(`/classify`; how: [docs/experiments.md](../docs/experiments.md#species)):

- a **new species**: it behaves like no species of the field, and is renamed
  `<name>_v1`;
- the **next version** of a species: it behaves like it, is no worse on any matchup and
  better on at least one, and is renamed `<species>_v{N+1}`; the old version moves to
  `inactive/legacy/`;
- a **variant**: it behaves like a species without beating it, and moves to
  `inactive/legacy/`.

Oracles and `inactive/` are not species. The lineage of every species (its versions,
their old stems and the notes that decided them) is
[research/species.md](../research/species.md).

```
bots/
  l1/                the zoo's heuristics
  l2/                bandits over L1s (smartbot, iocaine, rps4, ...) and the
                     specialists that replay one L2
  l3/                bandits and gates over L2s (and L1s): smartbot_sims, councils,
                     gatekeepers, naive-Bayes combiners
  l4/                the gatekeepers (over smartbot_sims and its replay)
  oracle/            the research-only Oracles
  blocks/            L1 heuristics that exist to be named as arms, every field a parameter
                     (frequency, ngram, backoff, longest_match, second_match, relative,
                     geometry, rarest, period, score_state; oracle_expert,
                     research only): never in a pool
  inactive/          bots out of the field
    fleets/iliad_v3/ the Iliad v3 fleet: a champion and four supports (Team overlay)
    legacy/          retired bots, kept for the research record
```

## The field

| level | bot | what it does |
|---|---|---|
| L1 | `rock_v1` | always rock (optional noise) |
| L1 | `nash_v1` | uniform random, the Nash equilibrium |
| L1 | `biased_v1` | a weighted coin over the three moves |
| L1 | `cycler_v1` | rock --> paper --> scissors (or the reverse) |
| L1 | `copycat_v1` | plays the opponent's last move |
| L1 | `reactionary_v1` | beats the opponent's last move |
| L1 | `counter_reactionary_v1` | after a win, beats the beat of its own last move |
| L1 | `self_beater_v1` | beats its own last move |
| L1 | `wsls_v1` | win-stay, lose-shift |
| L1 | `frequency_v1` | beats the opponent's most frequent move |
| L1 | `anti_frequency_v1` | beats the move that beats our most frequent move |
| L1 | `transition_matrix_v1` | order-1 opponent transitions, sampled |
| L1 | `markov2_joint_v1` | order-2 Markov model on the joint history |
| L1 | `pattern_memory_v1` | longest earlier repeat of the joint history |
| L1 | `rotation_outcome_v1` | learned win-stay/lose-shift (rotation by outcome) |
| L1 | `geometry_v1` | Superant's RPS Geometry |
| L1 | `balancer_hunter_v1` | beats the opponent's least frequent move (Rarest) |
| L1 | `period_detector_v1` | detects the opponent's period (1-12) and beats the move one period back |
| L1 | `score_reader_v1` | beats the opponent's favourite move given the match score (ScoreState) |
| L2 | `iocaine_lite_v1` | Iocaine Powder's sicilian reasoning over three predictors |
| L2 | `rps4_lite_v1` | Rpscontest #4 in miniature: Markov orders 0-3, greedy arms |
| L2 | `smartbot_v1` | 18 predictors x 3 arms, Thompson sampling (Kaggle 1st place) |
| L2 | `smartbot_fast_v1` | smartbot with faster memories (0.6, 0.6, 8) |
| L2 | `smartbot_staller_v1` | smartbot plus stalling (random play on drawdown or a safe lead) |
| L2 | `anti_smartbot_v1` | replays smartbot exactly and beats its likeliest move |
| L2 | `anti_iocaine_v1` | replays iocaine_lite exactly and beats its move |
| L2 | `anti_rps4_v1` | replays rps4_lite exactly and beats its move |
| L2 | `zoo_hunter_v1` | names which non-learning zoo L1 the opponent is (sims), greedy |
| L2 | `mirror_bandit_v1` | the learning zoo L1s as models of us, Thompson |
| L2 | `second_guess_v1` | smartbot's predictors played only BEAT_BEAT and COPY |
| L2 | `dropswitch_matcher_v1` | history matchers whose score drops at a loss (DropSwitch) |
| L2 | `vote_ensemble_v1` | frequency, n-gram, back-off and rotation arms, a sampled vote |
| L2 | `period_bandit_v1` | period, rarest-move and score-state models, Thompson |
| L2 | `fast_greedy_markov_v1` | short-memory Markov arms, greedy, a noise floor |
| L2 | `geometry_ensemble_v1` | geometry at four learning rates plus matchers, sharp Thompson |
| L2 | `backoff_family_v1` | back-off n-grams of every order and history, Thompson |
| L2 | `outcome_reader_v1` | outcome-conditioned rotation and score-state models, DropSwitch |
| L2 | `multiscale_v1` | frequency and n-grams at four memories, greedy |
| L2 | `sampled_markov_v1` | sampling n-grams under flattened Thompson (SHARP 0.5) |
| L3 | `smartbot_sims_v2` | smartbot plus 8 "model of us" sims (replays of the metabots included) |
| L3 | `anti_smartbot_sims_v2` | replays smartbot_sims exactly and beats its likeliest move |
| L3 | `l2_council_v1` | four original L2s replayed, three rotations each, Thompson |
| L3 | `naive_bayes_markov_v1` | n-grams of orders 1-3 on three histories plus a NaiveBayes arm |
| L3 | `gate_leader_v1` | a Markov bandit and three pattern experts, LEADER gate |
| L3 | `predator_v1` | the anti-L2 specialists and zoo_hunter replayed, greedy |
| L3 | `leader_hunter_v1` | smartbot with iocaine/rps4/smartbot_fast replays gated, LEADER |
| L3 | `gate_edge_smartbot_v1` | smartbot with its own replay gated by EDGE |
| L3 | `gate_fast_hold_v1` | smartbot_fast vs rps4_lite's counter, ANTI_FIRST_HOLD |
| L3 | `gate_bandit_period_v1` | period_bandit vs smartbot's counter, BANDIT gate |
| L3 | `gate_main_first_backoff_v1` | backoff_family first, iocaine_lite's counter, MAIN_FIRST |
| L3 | `leader_new_l2_v1` | mirror_bandit with zoo_hunter/period_bandit/outcome_reader gated, LEADER |
| L3 | `vote_council_v1` | seven newer L2s replayed, a sampled vote |
| L3 | `dropswitch_council_v1` | five newer L2s replayed, DropSwitch |
| L3 | `counter_council_v1` | only models of us: eight L2s played from the opponent's side |
| L3 | `sims_lite_v1` | iocaine's predictors plus three cheap L2 models of us, greedy |
| L3 | `sicilian_meta_v1` | iocaine_lite and rps4_lite from both sides, sicilian reasoning |
| L3 | `multiscale_council_v1` | the memory-shaped L2s replayed, sharp Thompson |
| L3 | `bayes_predators_v1` | the zoo's models of us plus a NaiveBayes arm |
| L3 | `smartbot_wide_v1` | smartbot's arms, the newest signals, zoo_hunter and second_guess |
| L4 | `gate_edge_v2` | smartbot_sims's arms + anti expert, gated by EDGE |
| L4 | `gate_main_first_v2` | same experts, the main arms first (MAIN_FIRST) - the fleet's core |
| L4 | `gate_main_first_stationary_v2` | gate_main_first plus a stationary (frequency) expert |
| Oracle | `oracle_smartbot_sims`, `oracle_anti_smartbot_sims`, `oracle_gate_edge`, `oracle_gate_anti_first` | pure Oracles: calibrated win chances per level, drawn with `pool.mocks` |
| Oracle | `oracle_arm_gate_edge`, `oracle_arm_gate_anti_first` | gatekeepers whose anti expert is an Oracle arm |

On 2026-10-12 the hierarchy was redefined (L1: heuristics only; each aggregator one level
above the bots it combines) and every aggregator was rewritten to name its arms as bots.
Each rewrite plays exactly as before (same moves, every bot vs four opponents, two seeds),
and every field bot kept its level.

Oracles cheat: they never enter a pool (unless `pool.mocks`), a tournament or an export.

## Renames

The research notes (`research/`) and the runs database keep the names a bot had when it
was run. On 2026-10-11 every bot of the field became version 1 of its species
(`smartbot` --> `smartbot_v1`; the species lineage is in
[research/species.md](../research/species.md)). Earlier renames, by their names before
the versions:

| bot | was |
|---|---|
| `smartbot_sims` | `advanced_bot`, before that `smartbot_sims3` |
| `anti_smartbot_sims` | `anti_advanced_bots`, before that `mirror_sims3` |
| `smartbot_fast` | `meta_smartbot` |
| `smartbot_staller` | `smart_staller` |
| `word2janken_scoreboard` | `staller` |
| `gate_edge` | `replay_gate` |
| `oracle_smartbot_sims` | `oracle_advanced_bot` |
| `oracle_anti_smartbot_sims` | `oracle_anti_advanced` |
| `oracle_gate_edge` | `oracle_replay_gate` |
| `oracle_arm_gate_edge` | `arm_replay_gate` |
| `oracle_arm_gate_anti_first` | `arm_gate_anti_first` |

Legacy bots and their old names: [inactive/legacy/README.md](inactive/legacy/README.md).
