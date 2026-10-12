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
