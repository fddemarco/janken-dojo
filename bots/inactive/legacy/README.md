# Legacy bots

Bots taken out of the field so that no pool, compile or test spends time on them. Bot
discovery doesn't recurse, so nothing under `bots/legacy/` is drawn into a pool or a
tournament. They are kept for the record: their notes in `research/experiments/` still
name them (by their old names, below), and any of them can be moved back to `bots/`
(`janken tune` scaffolds a missing space file).

| bot | old name | level | why it left |
|---|---|---|---|
| smartbot_geometry | smartbot_geo | L2 | dropped, [0001](../../../research/experiments/0001-smartbot-geo.md) |
| smartbot_sims_naive_bayes | tpi_lite | L4 | dropped, [0009](../../../research/experiments/0009-tpi-lite-vs-smartbot-sims3.md); an expensive L4 |
| smartbot_sims_staller | sims3_staller | L3 | dropped, [0012](../../../research/experiments/0012-sims3-staller-triggers-split.md) |
| smartbot_sims_second_match | sims3_second | L3 | dropped, [0013](../../../research/experiments/0013-sims3-second-vs-smartbot-sims3.md) |
| smartbot_sims_self_replay | self_sim | L4 | an L4 replay of an L3, superseded by anti_smartbot_sims, [0015](../../../research/experiments/0015-mirror-sims3-vs-smartbot-sims3.md) |
| word2janken_v1 | word2janken | L1 | variant of pattern_memory (2026-10-12): 83.2% alike, -8.4 pts [-12.7, -4.2] in 40 paired pools, 0-40 head to head |
| gate_anti_first_v1 | gate_anti_first | L4 | variant of gate_main_first (2026-10-12): 93.1% alike, -0.6 pts [-4.6, +3.4] in 40 paired pools |
| word2janken_scoreboard_v1 | staller | L2 | retired with word2janken (2026-10-12): a scoreboard over its three rotations |
| smartbot_sims_v1 | advanced_bot | L3 | superseded by smartbot_sims_v2 (2026-10-12): no word2janken sims |
| anti_smartbot_sims_v1 | anti_advanced_bots | L3 | superseded by v2 over smartbot_sims_v2 (2026-10-12) |
| anti_smartbot_v1 | anti_smartbot_v1 | L2 | superseded by anti_smartbot_v2 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0035](../../../research/experiments/0035-anti-smartbot-normal.md) |
| anti_smartbot_sims_v2 | anti_smartbot_sims_v2 | L3 | superseded by anti_smartbot_sims_v3 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0036](../../../research/experiments/0036-anti-smartbot-sims-normal.md) |
| leader_hunter_v1 | leader_hunter_v1 | L3 | superseded by leader_hunter_v2 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0037](../../../research/experiments/0037-leader-hunter-normal.md) |
| gate_edge_smartbot_v1 | gate_edge_smartbot_v1 | L3 | superseded by gate_edge_smartbot_v2 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0038](../../../research/experiments/0038-gate-edge-smartbot-normal.md) |
| gate_bandit_period_v1 | gate_bandit_period_v1 | L3 | superseded by gate_bandit_period_v2 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0039](../../../research/experiments/0039-gate-bandit-period-normal.md) |
| level_k_gate_v1 | level_k_gate_v1 | L4 | superseded by level_k_gate_v2 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0040](../../../research/experiments/0040-level-k-gate-normal.md) |
| gate_main_first_v2 | gate_main_first_v2 | L4 | superseded by gate_main_first_v3 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0041](../../../research/experiments/0041-gate-main-first-normal.md) |
| gate_main_first_stationary_v2 | gate_main_first_stationary_v2 | L4 | superseded by gate_main_first_stationary_v3 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0042](../../../research/experiments/0042-gate-main-first-stationary-normal.md) |
| gate_edge_v2 | gate_edge_v2 | L4 | superseded by gate_edge_v3 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0043](../../../research/experiments/0043-gate-edge-normal.md) |
| double_bluff_gate_v1 | double_bluff_gate_v1 | L4 | superseded by double_bluff_gate_v2 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0044](../../../research/experiments/0044-double-bluff-gate-normal.md) |
| replay_hunter_gate_v1 | replay_hunter_gate_v1 | L4 | superseded by replay_hunter_gate_v2 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0045](../../../research/experiments/0045-replay-hunter-gate-normal.md) |
| replay_hunter_wide_v1 | replay_hunter_wide_v1 | L4 | superseded by replay_hunter_wide_v2 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0046](../../../research/experiments/0046-replay-hunter-wide-normal.md) |
| predator_v1 | predator_v1 | L3 | superseded by predator_v2 (2026-10-13): the same bot with its replays computed (estimate NORMAL), no worse in its paired evaluation and over 12x faster, [0047](../../../research/experiments/0047-predator-normal.md) |
| gate_edge_v1 | replay_gate | L4 | superseded by v2 over smartbot_sims_v2 (2026-10-12) |
| gate_main_first_v1 | gate_main_first | L4 | superseded by v2 over smartbot_sims_v2 (2026-10-12); the Iliad v3 fleet still names it |
| gate_main_first_stationary_v1 | gate_main_first_stationary | L4 | superseded by v2 over smartbot_sims_v2 (2026-10-12) |

Removed as duplicates (in git history before the clean-up commit):

- `smartbot_sims` (n=5) and `smartbot_sims2` (n=8): shorter prefixes of today's
  `smartbot_sims` (n=10, once `smartbot_sims3` / `advanced_bot`), [0005](../../../research/experiments/0005-smartbot-sims3.md).
- `smartbot_bandit`: at its defaults it was `smartbot_sims` exactly, [0006](../../../research/experiments/0006-smartbot-bandit.md).
- `mock_anti_advanced`, `mock_replay_gate`, `mock_gate_anti_first`, `mock_gate_bandit`:
  the calibrated mocks of [0017](../../../research/experiments/0017-mock-replay-gate-vs-replay-gate-mock-validation.md)-[0020](../../../research/experiments/0020-tuning-of-mock-gate-anti-first.md),
  which no longer loaded (the Oracle stage changed) and were replaced by the per-level
  Oracles (`oracle_*`).
  | counter_anti_sims | counter_anti_sims | L3 | a pure specialist vs anti_smartbot_sims_v2 (71.7% of rounds, 10/10 at 250 rounds) but -38.5 pts [-45.7, -31.2] vs smartbot_sims_v2 over the field; its idea lives on gated in gate_counter_sims, [0031](../../../research/experiments/0031-counter-anti-sims-vs-smartbot-sims.md) |
  | level_k_bandit | level_k_bandit | L4 | the bandit form of level_k_gate (same 6 arms, Thompson, decay 0.85, sharp 3): +7.5 pts [+1.6, +13.6] vs double_bluff_gate_v1, no different from the gate over the field (+1.5 [-4.4, +7.2] for the gate) but it beats the gate head to head (42.2% vs 29.5% of rounds over 5 matches); out of the field so the note classifies one bot, [0032](../../../research/experiments/0032-level-k-vs-double-bluff-gate.md) |
  | level_k_bandit_normal | level_k_bandit_normal | L4 | a variant of level_k_gate: equal vs the field (-0.5 pts [-7.0, +6.0]) at 1.1x its speed, but 37.4% of rounds [36.7%, 38.1%] vs double_bluff_gate_v2 over 100 seeds where the gate stays under 36%; worth trying as a gated expert, [0055](../../../research/experiments/0055-level-k-bandit-normal-vs-level-k-gate-v2.md) |
  | replay_hunter_wider | replay_hunter_wider | L4 | replay_hunter_wide_v2 plus replays of geometry_ensemble, leader_hunter, period_detector, sicilian_meta and frequency_v1: +4.0 pts [-1.8, +10.0] at 10 round robins, then +1.9 [-2.8, +6.9] over 320 matches on fresh seeds (futile); its experts close specific holes but add ~2 pts to the pool score, [0056](../../../research/experiments/0056-replay-hunter-wider-vs-replay-hunter-wide-v2.md), [0057](../../../research/experiments/0057-replay-hunter-wider-vs-replay-hunter-wide-v2.md) |
  | backoff_ngram | backoff_ngram | L1 | the backoff block as an L1: -3.7 pts [-9.7, +2.4] vs pattern_memory_v1 in an L1 pool, 83% core agreement with it: a variant of the longest-repeat idea, [0061](../../../research/experiments/0061-backoff-ngram-vs-pattern-memory-v1.md) |
  | anti_pattern | anti_pattern | L1 | mirror counter of pattern_memory (LongestMatch of our moves, BEAT_BEAT): 94.7% of rounds head to head, but -27.1 pts vs pattern_memory_v1 in an L1 pool; an arm config of the longest_match block, [0062](../../../research/experiments/0062-anti-pattern-anti-second-repeat-vs-pattern-memor.md) |
  | anti_second_repeat | anti_second_repeat | L1 | mirror counter of second_repeat (SecondMatch of our moves, BEAT_BEAT): 95.0% of rounds head to head, -26.1 pts in an L1 pool; an arm config of the second_match block, [0062](../../../research/experiments/0062-anti-pattern-anti-second-repeat-vs-pattern-memor.md) |
  | strong_l1_bandit | strong_l1_bandit | L2 | the control for repeat_mirror (L1's strong set as arms, from the opponent's seat only): +9.2 pts [+2.2, +16.5] over iocaine_lite_v1, +2.8 [-4.0, +9.5] below repeat_mirror (n.s.) in L1+L2 pools, [0063](../../../research/experiments/0063-mirror-l1-bandit-iocaine-lite-v1-vs-strong-l1-ba.md) |
  | strong_l2_council | strong_l2_council | L3 | a council of L2's strong set (geometry_ensemble, period_bandit, anti_smartbot, anti_rps4): -3.5 pts [-11.5, +4.8] vs l2_council_v1 in L1-L3 pools; counters are strong only where their prey is common, [0065](../../../research/experiments/0065-strong-l2-council-vs-l2-council-v1.md) |
  | learner_council | learner_council | L3 | a council of L2's strong learners from our seat: -2.5 pts [-10.0, +5.0] vs l2_council_v1 in L1-L3 pools, loses to its own arms' species, [0066](../../../research/experiments/0066-learner-council-vs-l2-council-v1.md) |
  | learner_mirror | learner_mirror | L3 | the same learners from both seats: -2.8 pts [-10.8, +5.8] vs l2_council_v1, its holes move to anti_smartbot and the samplers, [0067](../../../research/experiments/0067-learner-mirror-vs-l2-council-v1.md) |
  | response_markov | response_markov | L1 | their next move given our last two moves: -12.4 pts [-18.4, -6.3] vs markov2_joint_v1 in an L1 pool, [0070](../../../research/experiments/0070-response-markov-vs-markov2-joint-v1.md) |
  | family_counters | family_counters | L3 | a greedy bandit over repeat_mirror and each family's natural counter: +12.2 pts [+4.2, +20.2] over repeat_mirror_v1, -1.9 [-10.9, +6.9] vs l2_council_v1 on variant pools, [0074](../../../research/experiments/0074-family-counters-vs-repeat-mirror-v1.md), [0075](../../../research/experiments/0075-family-counters-vs-l2-council-v1.md) |
  | pretrained_mirror | pretrained_mirror | L2 | repeat_mirror plus the pre-trained context table as an arm: +6.0 then +1.1 pts [-4.5, +7.0] vs repeat_mirror_v1 on variant pools, [0076](../../../research/experiments/0076-pretrained-mirror-vs-repeat-mirror-v1.md), [0077](../../../research/experiments/0077-pretrained-mirror-vs-repeat-mirror-v1.md) |
  | pretrained_context_v1 | pretrained_context | L1 | the first pre-trained species (prior worth 5 observations per context), superseded by v2 (worth 1): +7.3 pts [+3.3, +11.4] for v2 on whole-field variant pools, [0078](../../../research/experiments/0078-pretrained-light-vs-pretrained-context-v1.md) |
  | pretrained_wide | pretrained_wide | L1 | the context table trained on L1-L4 matches (its block prior_context_wide is here too): -0.3 pts [-8.1, +7.8] vs pretrained_context_v2 (trained on L1-L2) on whole-field variant pools, [0079](../../../research/experiments/0079-pretrained-wide-vs-pretrained-context-v2.md) |
  | pretrained_context_v2 | pretrained_context | L1 | the 3-move table (prior worth 1), superseded by v3 (4 moves): +7.9 pts [+3.4, +12.3] for v3 on whole-field variant pools, [0080](../../../research/experiments/0080-pretrained-deep-vs-pretrained-context-v2.md) |
  | self_mixture | self_mixture | L1 | CTW over the opponent's own sequence (depth 5): -11.0 pts [-15.5, -6.5] vs context_mixture_v1 in L1 variant pools, [0081](../../../research/experiments/0081-self-mixture-vs-context-mixture-v1.md) |
