# L1 atlas (draft)

Idea #61, step 1 of the research direction in `README.md`: the 19 L1 species against each other. Source: `janken tournament --bots-dir bots/l1 --matches 10 --rounds 250 --seed 61` (2026-10-13, 1710 matches; `experiments/l1_atlas_preview.json`). Margins are rounds won minus lost per 250-round match, over 10 matches per pair: a draft, enough to see the shape, not to settle close pairs.

## Standings

| L1 | won | drawn | lost | rounds +/- per match | its best counter (margin) | L1s beating it by > 5 |
|---|---|---|---|---|---|---|
| `pattern_memory_v1` | 162 | 1 | 17 | +119 | `geometry_v1` (+1) | 0 |
| `markov2_joint_v1` | 151 | 1 | 28 | +110 | `pattern_memory_v1` (+33) | 3 |
| `geometry_v1` | 148 | 0 | 32 | +95 | `transition_matrix_v1` (+7) | 1 |
| `transition_matrix_v1` | 138 | 2 | 40 | +73 | `pattern_memory_v1` (+4) | 0 |
| `period_detector_v1` | 138 | 0 | 42 | +83 | `rotation_outcome_v1` (+19) | 2 |
| `rotation_outcome_v1` | 137 | 0 | 43 | +120 | `pattern_memory_v1` (+52) | 3 |
| `reactionary_v1` | 88 | 3 | 89 | -9 | `rotation_outcome_v1` (+234) | 7 |
| `self_beater_v1` | 82 | 4 | 94 | -40 | `rotation_outcome_v1` (+234) | 8 |
| `nash_v1` | 78 | 4 | 98 | -1 | `rock_v1` (+10) | 3 |
| `cycler_v1` | 75 | 2 | 103 | -43 | `rotation_outcome_v1` (+220) | 8 |
| `counter_reactionary_v1` | 73 | 2 | 105 | -41 | `rotation_outcome_v1` (+235) | 8 |
| `score_reader_v1` | 69 | 1 | 110 | -15 | `pattern_memory_v1` (+168) | 11 |
| `biased_v1` | 64 | 4 | 112 | -9 | `frequency_v1` (+66) | 9 |
| `anti_frequency_v1` | 53 | 6 | 121 | -17 | `balancer_hunter_v1` (+124) | 10 |
| `frequency_v1` | 54 | 1 | 125 | -30 | `anti_frequency_v1` (+150) | 13 |
| `wsls_v1` | 45 | 12 | 123 | -85 | `rotation_outcome_v1` (+247) | 11 |
| `copycat_v1` | 44 | 3 | 133 | -62 | `rotation_outcome_v1` (+232) | 11 |
| `balancer_hunter_v1` | 42 | 2 | 136 | -129 | `period_detector_v1` (+247) | 13 |
| `rock_v1` | 37 | 16 | 127 | -121 | `period_detector_v1` (+249) | 11 |

## The six learners, against each other

Rounds won minus lost per match, row vs column.

| | `pattern_memory_v1` | `markov2_joint_v1` | `geometry_v1` | `transition_matrix_v1` | `period_detector_v1` | `rotation_outcome_v1` |
|---|---|---|---|---|---|---|
| `pattern_memory_v1` | - | +33.0 | -0.6 | +3.8 | +2.0 | +52.0 |
| `markov2_joint_v1` | -33.0 | - | -5.5 | -6.9 | +7.5 | +28.1 |
| `geometry_v1` | +0.6 | +5.5 | - | -7.1 | +0.6 | +24.8 |
| `transition_matrix_v1` | -3.8 | +6.9 | +7.1 | - | -1.1 | +2.2 |
| `period_detector_v1` | -2.0 | -7.5 | -0.6 | +1.1 | - | -18.6 |
| `rotation_outcome_v1` | -52.0 | -28.1 | -24.8 | -2.2 | +18.6 | - |

## First reading

- **Two tiers.** Six learners (`pattern_memory`, `markov2_joint`, `geometry`,
  `transition_matrix`, `period_detector`, `rotation_outcome`) win 76-90% of their
  matches; the 13 fixed, reactive and frequency strategies are prey, each beaten by
  3-13 other L1s by more than 5 rounds per match (`nash_v1` by noise only: -1 round
  per match overall).
- **Gaps (no L1 counter), consistent over this run and an earlier preview on another
  seed:** no L1 beats `pattern_memory_v1`; `geometry_v1` and `transition_matrix_v1`
  are beaten by at most one L1, by under 10 rounds per match; only
  `rotation_outcome_v1` beats `period_detector_v1` (+14 and +19). Idea #65.
- **The learners' order is close:** apart from `pattern_memory` over `markov2_joint`
  (+33) and `rotation_outcome` losing to most learners (-2 to -52), the learner pairs
  sit within 10 rounds per match, which 10 matches per pair can't order.
- **Next (ideas #61-63):** more matches per pair for the close learner pairs, the
  mechanism behind each matchup, and the strategy families the level lacks.

## The learners' order, settled (100 matches per pair)

Source: `janken tournament` on the six learners only, 100 matches per pair x 250
rounds, seed 61 (`experiments/l1_learners.json`). Rounds won minus lost per match,
row vs column, with the 95% CI half-width; "tie" when the CI covers 0.

| pair | margin |
|---|---|
| `pattern_memory` vs `geometry` | +0.8 +- 2.2 (tie) |
| `pattern_memory` vs `markov2_joint` | +32.8 +- 1.6 |
| `pattern_memory` vs `period_detector` | +3.9 +- 2.4 |
| `pattern_memory` vs `transition_matrix` | +5.8 +- 2.6 |
| `pattern_memory` vs `rotation_outcome` | +55.1 +- 3.9 |
| `geometry` vs `markov2_joint` | +6.4 +- 2.4 |
| `geometry` vs `period_detector` | +3.1 +- 2.3 |
| `geometry` vs `transition_matrix` | +0.9 +- 2.6 (tie) |
| `geometry` vs `rotation_outcome` | +20.3 +- 2.2 |
| `markov2_joint` vs `period_detector` | +2.2 +- 2.1 |
| `markov2_joint` vs `transition_matrix` | +1.0 +- 2.7 (tie) |
| `markov2_joint` vs `rotation_outcome` | +26.6 +- 3.2 |
| `period_detector` vs `transition_matrix` | +3.8 +- 2.6 |
| `period_detector` vs `rotation_outcome` | -14.1 +- 5.5 |
| `transition_matrix` vs `rotation_outcome` | -1.9 +- 2.1 (tie) |

- **Top pair:** `pattern_memory` and `geometry` tie each other and beat the rest
  (`geometry` ties `transition_matrix`).
- **A cycle in the middle:** `markov2_joint` > `period_detector` > `transition_matrix`
  ~ `markov2_joint`, all within 4 rounds per match.
- **`rotation_outcome`** is last among the learners, yet the only one that beats
  `period_detector` (+14.1): a non-transitive niche.
- **Few strong strategies:** two at the top, four close behind. A small set like this
  is where a specialist per strong strategy can pay (research/theory/README.md).

## Species and their natural counters (20 species, 2026-10-13)

Source: `janken tournament --bots-dir bots/l1 --matches 20 --rounds 250 --seed 62`
(3800 matches, `experiments/l1_atlas_v2.json`), after `second_repeat_v1` joined the
field (note 0060). Counter margins are rounds won minus lost per 250-round match by
the counter vs the species, over 20 matches.

Top of the standings: `second_repeat_v1` 87% of matches (+108 rounds per match),
`pattern_memory_v1` 86% (+113), `geometry_v1` 84% (+91), `markov2_joint_v1` 76%
(+104), `period_detector_v1` 76% (+79), `transition_matrix_v1` 74% (+69),
`rotation_outcome_v1` 72% (+114), `nash_v1` 50% (+0).

| family | species | what it does | natural counter (margin) | why it works |
|---|---|---|---|---|
| fixed | `rock_v1` | always rock | `frequency_v1` (+249) | a constant is its own most frequent move |
| fixed | `biased_v1` | weighted coin | `frequency_v1` (+68) | only its bias is exploitable; learners chase its noise |
| reactive | `copycat_v1` | copies our last move | `rotation_outcome_v1` (+233), `self_beater_v1` (+225) | its move is our last, a fixed rotation of the history |
| reactive | `reactionary_v1` | beats our last move | `rotation_outcome_v1` (+234) | a fixed rotation (BEAT) of our last move |
| reactive | `counter_reactionary_v1` | after a win, beats our likely reply | `rotation_outcome_v1` (+236) | a rotation conditioned on the outcome, which rotation_outcome models |
| reactive | `self_beater_v1` | beats its own last move | `rotation_outcome_v1` (+234) | a fixed rotation of its own last move |
| reactive | `wsls_v1` | win-stay, lose-shift | `rotation_outcome_v1` (+248) | exactly an outcome-conditioned rotation |
| reactive | `cycler_v1` | R --> P --> S | `rotation_outcome_v1` (+224) | a constant rotation |
| frequency | `frequency_v1` | beats our most frequent move | `anti_frequency_v1` (+143) | built to beat it: assumes that rule, beats it |
| frequency | `anti_frequency_v1` | beats frequency's move | `balancer_hunter_v1` (+125) | the next rule up the counting chain |
| frequency | `balancer_hunter_v1` | beats our least frequent move | `rotation_outcome_v1` (+245), every learner (+244 to +245) | a deterministic function of counts any learner models |
| frequency | `score_reader_v1` | beats our most frequent move given the score | `pattern_memory_v1` (+176) | still a counting rule, keyed on a 3-state score |
| learner | `rotation_outcome_v1` | models our rotation relative to its last move, given the outcome | `pattern_memory_v1` (+60), `markov2_joint_v1` (+30), `geometry_v1` (+22) | its own rule is a short, repeating pattern of the joint history |
| learner | `markov2_joint_v1` | order-2 Markov on the joint history | `pattern_memory_v1` (+31), `geometry_v1` (+12) | a fixed order-2 context is a special case of the longest repeat |
| learner | `period_detector_v1` | beats our move one period back | `rotation_outcome_v1` (+15) | weak |
| learner | `transition_matrix_v1` | order-1 transitions of our moves | none above +7 | no L1 models it well |
| learner | `geometry_v1` | Superant's RPS geometry | none above +3 | unbeaten at L1 |
| learner | `pattern_memory_v1` | follows the longest earlier repeat | `geometry_v1` (+5) | nearly unbeaten |
| learner | `second_repeat_v1` | follows the second-longest repeat | `pattern_memory_v1` (+6) | nearly unbeaten |
| Nash | `nash_v1` | uniform random | none above +4 | unexploitable, and never exploits |

**The map.** Four families, with natural counters that are themselves strategies:

- **fixed** --> beaten by a frequency count;
- **reactive** (fixed rules of the last round) --> beaten by a model of the rotation
  (`rotation_outcome`), one learner covering the whole family;
- **frequency** --> a chain where each counting rule beats the one below
  (`frequency` < `anti_frequency` < `balancer_hunter`), and any learner beats them all;
- **learners** --> counter each other weakly (mostly under 10 rounds per match),
  except the longest-repeat followers vs the short-pattern learners (`rotation_outcome`,
  `markov2_joint`).

The strong set at L1 is the repeat followers and `geometry` (`second_repeat`,
`pattern_memory`, `geometry`), with no strong natural counter at L1: that is where L2
must add something (research/theory/01-l1-heuristics.md).
