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
