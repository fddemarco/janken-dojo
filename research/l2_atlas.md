# L2 atlas (draft)

Idea #66, step 1 of the research direction (`README.md`) at L2: the 20 L2 species against each other. Source: `janken tournament --bots-dir bots/l2 --matches 20 --rounds 250 --seed 66` (2026-10-13, 3800 matches, `experiments/l2_atlas.json`). Margins are rounds won minus lost per 250-round match, over 20 matches per pair.

## Standings and natural counters

| L2 | family | matches won | rounds +/- per match | natural counter (margin) | next counters | L2s beating it by > 5 |
|---|---|---|---|---|---|---|
| `anti_smartbot_v2` | replay counter | 81% | +18 | `geometry_ensemble_v1` (+13) | `period_bandit_v1` (-0), `anti_rps4_v1` (-0) | 1 |
| `anti_rps4_v1` | replay counter | 68% | +11 | `second_guess_v1` (+9) | `multiscale_v1` (+4), `anti_iocaine_v1` (+3) | 1 |
| `second_guess_v1` | adaptive bandit | 56% | +3 | `anti_smartbot_v2` (+33) | `repeat_mirror_v1` (+6), `mirror_bandit_v1` (+3) | 2 |
| `geometry_ensemble_v1` | adaptive bandit | 56% | +5 | `mirror_bandit_v1` (+3) | `backoff_family_v1` (+3), `rps4_lite_v1` (+3) | 0 |
| `dropswitch_matcher_v1` | adaptive bandit | 53% | +2 | `anti_smartbot_v2` (+20) | `anti_rps4_v1` (+2), `multiscale_v1` (+1) | 1 |
| `period_bandit_v1` | adaptive bandit | 54% | +2 | `geometry_ensemble_v1` (+4) | `fast_greedy_markov_v1` (+3), `smartbot_v1` (+2) | 0 |
| `smartbot_v1` | adaptive bandit | 53% | +1 | `anti_smartbot_v2` (+31) | `smartbot_fast_v1` (+6), `second_guess_v1` (+5) | 3 |
| `anti_iocaine_v1` | replay counter | 52% | +11 | `geometry_ensemble_v1` (+32) | `outcome_reader_v1` (+18), `multiscale_v1` (+15) | 7 |
| `smartbot_fast_v1` | adaptive bandit | 51% | +1 | `anti_smartbot_v2` (+24) | `anti_rps4_v1` (+9), `anti_iocaine_v1` (+9) | 3 |
| `backoff_family_v1` | adaptive bandit | 50% | +0 | `anti_smartbot_v2` (+18) | `anti_rps4_v1` (+17), `anti_iocaine_v1` (+4) | 2 |
| `mirror_bandit_v1` | adaptive bandit | 50% | -1 | `anti_rps4_v1` (+18) | `anti_iocaine_v1` (+13), `sampled_markov_v1` (+7) | 4 |
| `sampled_markov_v1` | adaptive bandit | 49% | +1 | `anti_smartbot_v2` (+6) | `anti_rps4_v1` (+5), `dropswitch_matcher_v1` (+3) | 2 |
| `fast_greedy_markov_v1` | adaptive bandit | 49% | -0 | `anti_smartbot_v2` (+26) | `anti_rps4_v1` (+16), `anti_iocaine_v1` (+14) | 3 |
| `vote_ensemble_v1` | adaptive bandit | 48% | -2 | `anti_smartbot_v2` (+59) | `anti_rps4_v1` (+11), `sampled_markov_v1` (+7) | 6 |
| `repeat_mirror_v1` | adaptive bandit | 47% | -1 | `anti_iocaine_v1` (+18) | `anti_smartbot_v2` (+14), `anti_rps4_v1` (+8) | 6 |
| `multiscale_v1` | adaptive bandit | 46% | -2 | `anti_smartbot_v2` (+29) | `second_guess_v1` (+12), `repeat_mirror_v1` (+8) | 4 |
| `rps4_lite_v1` | near-deterministic | 43% | -7 | `anti_rps4_v1` (+97) | `anti_iocaine_v1` (+27), `anti_smartbot_v2` (+22) | 5 |
| `iocaine_lite_v1` | near-deterministic | 29% | -17 | `anti_iocaine_v1` (+221) | `anti_rps4_v1` (+31), `anti_smartbot_v2` (+29) | 12 |
| `outcome_reader_v1` | adaptive bandit | 28% | -6 | `anti_smartbot_v2` (+23) | `geometry_ensemble_v1` (+11), `multiscale_v1` (+10) | 13 |
| `zoo_hunter_v1` | zoo specialist | 12% | -19 | `geometry_ensemble_v1` (+45) | `second_guess_v1` (+36), `vote_ensemble_v1` (+29) | 18 |

## First reading

- **The same three-part shape as L1, one level up.** Adaptive bandits (the smartbot,
  Markov and ensemble families) share one natural counter, `anti_smartbot_v2`, a
  replay of the smartbot model that beats most of them (+18 to +59 rounds per
  match), as `rotation_outcome` beats every reactive L1. Near-deterministic L2s fall
  to their exact replay counter: `iocaine_lite` to `anti_iocaine` (+221), `rps4_lite`
  to `anti_rps4` (+97), as each strong L1 falls to its mirror counter.
- **A small strong set with no strong counter:** `geometry_ensemble_v1` and
  `period_bandit_v1` are beaten by no L2 by more than 5 rounds; `anti_smartbot_v2`
  and `anti_rps4_v1` by one each (`geometry_ensemble` +13, `second_guess` +9). The
  ensemble of geometries is the one that beats the main replay counter, as `geometry`
  stood at the top of L1.
- **`repeat_mirror_v1`** (built from L1's strong set) is mid-table among L2s (47% of
  matches): it beats iocaine-style L2s and the L1s, but `anti_iocaine` (+18) and
  `anti_smartbot` (+14) model it. Its edge is over the level below, the pattern of the
  insight of 2026-10-13 on levels.
- **Next:** an L3 built from this strong set, judged against pools of L1-L3, the
  theory's prediction one level up (research/theory/02-meta-strategies.md).
