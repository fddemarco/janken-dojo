# Insights

Findings that held up. An entry needs:

- a linked experiment note;
- a run id;
- an effect whose 95% CI excludes zero, which in practice means a **paired**
  comparison inside one run.

**Epoch note (2026-10-10):** every entry below was measured on the bots as they were
before the blueprint refactor (see `README.md`, "structure epoch 2"). Idea #21 re-baselined
them in [0010](experiments/0010-rebaseline-epoch-2.md): the sims finding replicated (and is
restated for the new code), the metabot-replay one did not.

Newest entries go first. An entry that a later experiment contradicts is not deleted: it
gets marked ~~superseded~~ with a link to the new evidence.

Format:

```
## YYYY-MM-DD: <one-line finding>
- **Evidence:** experiments/NNNN-slug.md (run <run-id>): <effect, CI, n>
- **Mechanism:** why we think it works
- **Implication:** what to build or try next (and the new ideas.md entry)
```

______________________________________________________________________

## 2026-10-13: Identifying an opponent's family pays when done by records, not by a scripted probe: a gate over every family's natural counter beats a probe-then-switch, but an L3 holding them only ties the field's L3 council

- **Evidence:** experiments/0074-family-counters-vs-repeat-mirror-v1.md (run 20261013-160748_0074-family-counters-vs-repeat-mirror-v1): `family_counters - repeat_mirror_v1 = +12.2 pts [+4.2, +20.2]` over 200 shared matches: family_counters better; experiments/0075-family-counters-vs-l2-council-v1.md (run 20261013-160825_0075-family-counters-vs-l2-council-v1): tentative, no 95% CI excludes 0: `family_counters - l2_council_v1 = -1.9 pts [-10.9, +6.9]` over 160 shared matches: no significant difference
- **Mechanism:** an oracle that knows the family and switches to its counter gains +10 to +12 rounds per match, but a 24-round probe classifies the family only ~50% right and a wrong switch costs more than a right one gains; decayed counterfactual records over all the counters converge on the right one without the probe's cost (+18 rounds per match over repeat_mirror in the arena, +12.2 pts in the kit), and the field's L3 council already reaches the same level (-1.9 pts [-10.9, +6.9])
- **Implication:** use the atlases' natural counters as arms of any council, skip scripted probes, and look for gains above L2 on hard pools or in new kinds of aggregators, not in more L3 councils

## 2026-10-13: A move table pre-trained on the field's matches beats the best online L1 against parameter variants it never saw: pre-training generalises across parameters

- **Evidence:** experiments/0073-pretrained-context-vs-context-mixture-v1.md (run 20261013-155311_0073-pretrained-context-vs-context-mixture-v1): `pretrained_context - context_mixture_v1 = +9.8 pts [+5.6, +14.4]` over 320 shared matches: pretrained_context better; experiments/0072-pretrained-context-vs-context-mixture-v1.md (run 20261013-155257_0072-pretrained-context-vs-context-mixture-v1): `pretrained_context - context_mixture_v1 = +6.8 pts [+1.8, +12.0]` over 200 shared matches: pretrained_context better
- **Mechanism:** the prior (worth 5 observations per context) names how the field's bots respond to each 3-move joint context from the first rounds, where an online learner starts from nothing; trained on default-parameter matches and judged on variants, so it is generalisation, not memory: +9.8 pts [+5.6, +14.4] over context_mixture_v1 (320 matches, fresh seeds), after an arena probe showed +6.6 pts of net rounds over the same table online-only
- **Implication:** pre-train the priors of the strong online learners (CTW's KT counts, repeat_mirror's arms) on the dataset with parameter variants (ideas #72, #74, #75), and keep the prior light (weight ~5): a heavier one (20) helped less

## 2026-10-13: An L2 built from L1's strong set (both repeat followers read from both seats, and geometry, every rotation) beats the field's iocaine-style L2 by about 7 pts

- **Evidence:** experiments/0064-mirror-l1-bandit-vs-iocaine-lite-v1.md (run 20261013-142910_0064-mirror-l1-bandit-vs-iocaine-lite-v1): `mirror_l1_bandit - iocaine_lite_v1 = +7.3 pts [+3.0, +11.6]` over 480 shared matches: mirror_l1_bandit better; experiments/0063-mirror-l1-bandit-iocaine-lite-v1-vs-strong-l1-ba.md (run 20261013-142825_0063-mirror-l1-bandit-iocaine-lite-v1-vs-strong-l1-ba): `mirror_l1_bandit - iocaine_lite_v1 = +12.0 pts [+5.8, +18.8]` over 200 shared matches: mirror_l1_bandit better; `iocaine_lite_v1 - strong_l1_bandit = -9.2 pts [-16.5, -2.2]` over 200 shared matches: strong_l1_bandit better
- **Mechanism:** iocaine_lite holds only the longest repeat (from both seats) and frequency; adding the second-longest repeat and geometry, the other unbeaten L1s, gives the bandit an arm that names the move whenever any member of the strong set would, and every rotation of it covers their counters; confirmed on fresh seeds (+7.3 pts [+3.0, +11.6], 480 matches) after a +12.0 first run
- **Implication:** build each level from the strong set of the level below, found by its atlas; next at L2: an atlas of the L2s with repeat_mirror in it, and whether the mirror-counter arms add anything (+2.8 pts n.s. over the strong set alone)

## 2026-10-13: The strongest L1s fall to an L1 mirror counter: their own rule computed on our moves, played BEAT_BEAT, wins about 95% of rounds vs each, but nothing elsewhere

- **Evidence:** experiments/0062-anti-pattern-anti-second-repeat-vs-pattern-memor.md (run 20261013-142536_0062-anti-pattern-anti-second-repeat-vs-pattern-memor): `anti_pattern - pattern_memory_v1 = -27.1 pts [-34.5, -20.3]` over 190 shared matches: pattern_memory_v1 better; `anti_second_repeat - pattern_memory_v1 = -26.1 pts [-33.7, -17.9]` over 190 shared matches: pattern_memory_v1 better
- **Mechanism:** a repeat follower predicts our next move from the joint history and plays its beat; the same rule on our side (of: MY) names that prediction, and BEAT_BEAT beats their reply, so the counter is exact; it holds no model of anyone else, so it scores 27 pts below the target in an L1 pool and draws or loses vs the other strong L1s
- **Implication:** the counters of L1's strong set are arms, not bots: an L2 should hold them (longest_match / second_match with OF: MY, rotated BEAT_BEAT) beside the strong L1s and pick by record; the first L2 experiment of the bottom-up direction

## 2026-10-13: At L1, following an earlier repeat of the joint history beats fixed-order models, and the second-longest repeat is as strong as the longest

- **Evidence:** experiments/0060-second-repeat-vs-markov2-joint-v1.md (run 20261013-141615_0060-second-repeat-vs-markov2-joint-v1): `second_repeat - markov2_joint_v1 = +6.3 pts [+0.3, +12.9]` over 190 shared matches: second_repeat better; experiments/0061-backoff-ngram-vs-pattern-memory-v1.md (run 20261013-141620_0061-backoff-ngram-vs-pattern-memory-v1): tentative, no 95% CI excludes 0: `backoff_ngram - pattern_memory_v1 = -3.7 pts [-9.7, +2.4]` over 190 shared matches: no significant difference
- **Mechanism:** a fixed context (order-2 Markov) is a special case of the longest repeat, which adapts its context length; the runner-up repeat predicts an opponent that dodges the longest, and is the strongest L1 in the 20-species round robin (87% of matches); a variable-order n-gram only re-derives the longest repeat (83% core agreement)
- **Implication:** the L1 strong set is the repeat followers and geometry, with no strong counter at L1: the first thing L2 should add is a counter of that set (idea #65), and the next L1 diversity work goes to families with no signal yet, not to more repeat variants

## 2026-10-13: A 4-6 pt lead at the 10-round-robin cap is usually the high draw: on fresh seeds it falls to about +2 pts, so confirm such a lead before keeping or building on it

- **Evidence:** experiments/0052-l5-wide-hunter-vs-replay-hunter-wide-v2.md (run 20261013-123947_0052-l5-wide-hunter-vs-replay-hunter-wide-v2): tentative, no 95% CI excludes 0: `l5_wide_hunter - replay_hunter_wide_v2 = +6.0 pts [-0.5, +12.2]` over 200 shared matches: no significant difference; experiments/0053-l5-wide-hunter-vs-replay-hunter-wide-v2.md (run 20261013-124625_0053-l5-wide-hunter-vs-replay-hunter-wide-v2): tentative, no 95% CI excludes 0: `l5_wide_hunter - replay_hunter_wide_v2 = +1.9 pts [-5.3, +8.8]` over 160 shared matches: no significant difference; experiments/0056-replay-hunter-wider-vs-replay-hunter-wide-v2.md (run 20261013-135246_0056-replay-hunter-wider-vs-replay-hunter-wide-v2): tentative, no 95% CI excludes 0: `replay_hunter_wider - replay_hunter_wide_v2 = +4.0 pts [-1.8, +10.0]` over 200 shared matches: no significant difference; experiments/0057-replay-hunter-wider-vs-replay-hunter-wide-v2.md (run 20261013-135534_0057-replay-hunter-wider-vs-replay-hunter-wide-v2): tentative, no 95% CI excludes 0: `replay_hunter_wider - replay_hunter_wide_v2 = +1.9 pts [-2.8, +6.9]` over 320 shared matches: no significant difference
- **Mechanism:** 10 round robins give a paired CI of about +-6 pts, so among the experiments that reach the cap, the ones read as promising are selected partly for luck (winner's curse): l5_wide_hunter +6.0 [-0.5, +12.2] (0052) then +1.9 [-5.3, +8.8] (0053); replay_hunter_wider +4.0 [-1.8, +10.0] (0056) then +1.9 [-2.8, +6.9] over 320 matches (0057)
- **Implication:** plan the confirming run (fresh seeds, the thorough budget) before acting on a lead that didn't clear its CI; expect adding one more expert to a strong gate to be worth about +2 pts vs the pool

## 2026-10-13: Against an opponent that switches levels mid-match, a decayed Thompson bandit over level-k replays keeps up where a LEADER gate trails it

- **Evidence:** experiments/0032-level-k-vs-double-bluff-gate.md (run 20261012-164842_0032-level-k-vs-double-bluff-gate): `level_k_gate - double_bluff_gate_v1 = +9.0 pts [+2.8, +15.2]` over 305 shared matches: level_k_gate better; `level_k_bandit - double_bluff_gate_v1 = +7.5 pts [+1.6, +13.6]` over 305 shared matches: level_k_bandit better; experiments/0055-level-k-bandit-normal-vs-level-k-gate-v2.md (run 20261013-134613_0055-level-k-bandit-normal-vs-level-k-gate-v2): tentative, no 95% CI excludes 0: `level_k_bandit_normal - level_k_gate_v2 = -0.5 pts [-7.0, +6.0]` over 200 shared matches: no significant difference
- **Mechanism:** the bandit's decayed Dirichlet (0.85) and sharpened Thompson re-pick the arm within a few rounds of a switch, while a gate's undecayed record needs many rounds to hand over: vs double_bluff_gate the bandit wins 37.4% of rounds over 100 seeds (0055) where level_k_gate stays under 36%; over the whole field the two tie, since the gate's main bandit covers the learners the bandit doesn't replay
- **Implication:** use a decayed bandit, not a LEADER gate, for experts that model a flip-flopping counter; try level_k_bandit_normal as a gated expert inside replay_hunter_wide (-0.4 rounds per match vs double_bluff_gate_v2)

## 2026-10-13: A level's edge over the best bot below it shrinks against simpler opponents: the L4 gate beats the best L3 vs L2s but only matches the best L2 vs L1s

- **Evidence:** experiments/0026-l4-vs-l2-gate-anti-first-vs-anti-advanced-bots-l.md (run 20261010-214527_0026-l4-vs-l2-gate-anti-first-vs-anti-advanced-bots-l): `gate_anti_first - anti_advanced_bots = +3.7 pts [+0.9, +6.6]` over 600 shared matches: gate_anti_first better; experiments/0027-l4-vs-l1-gate-main-first-vs-iocaine-lite-l1-only.md (run 20261010-222411_0027-l4-vs-l1-gate-main-first-vs-iocaine-lite-l1-only): tentative, no 95% CI excludes 0: `gate_main_first - iocaine_lite = +0.1 pts [-2.2, +2.5]` over 680 shared matches: no significant difference
- **Mechanism:** against L1s the best L2 already wins about 91% of matches, so there is little left to gain; vs L2s, the L4's replays of whole learners name moves an L3 can't (0026: +3.7 pts [+0.9, +6.6] significant; 0027: +0.1 pts [-2.2, +2.5]); note 0051 found the same one level up, no L5 significantly better than the best L4
- **Implication:** aim new levels at the opponents one level down, and judge them there (level-restricted pools); don't expect a higher level to raise the score vs the zoo

## 2026-10-13: An Oracle mock calibrated on an expensive expert scores within noise of the real expert, leaning optimistic by a few points

- **Evidence:** experiments/0017-mock-replay-gate-vs-replay-gate-mock-validation.md (run 20261010-193336_0017-mock-replay-gate-vs-replay-gate-mock-validation): tentative, no 95% CI excludes 0: `mock_replay_gate - replay_gate = +2.5 pts [-2.5, +7.8]` over 200 shared matches: no significant difference; experiments/0022-arm-gate-anti-first-vs-gate-anti-first-per-level.md (run 20261010-204355_0022-arm-gate-anti-first-vs-gate-anti-first-per-level): tentative, no 95% CI excludes 0: `arm_gate_anti_first - gate_anti_first = +3.8 pts [-0.8, +8.5]` over 200 shared matches: no significant difference
- **Mechanism:** the Oracle wins with the expert's measured chance per opponent level, so it reproduces the average edge but not its matchup-by-matchup variation, which the real expert pays for (0017: +2.5 pts [-2.5, +7.8]; 0022: +3.8 pts [-0.8, +8.5], both mock minus real)
- **Implication:** screen ideas with mocks, but confirm any mocked gain under about 4 pts with the real bot before keeping it

## 2026-10-13: A bot built on one opponent (its exact replay, or a fleet impostor) beats that opponent outright, yet barely moves its pool score: single-opponent gains need head-to-head evidence

- **Evidence:** experiments/0014-sinon-vs-smartbot-sims3.md (run 20261010-165203_0014-sinon-vs-smartbot-sims3): tentative, no 95% CI excludes 0: `sinon - smartbot_sims3 = +0.8 pts [-2.7, +3.9]` over 800 shared matches: no significant difference; experiments/0015-mirror-sims3-vs-smartbot-sims3.md (run 20261010-173510_0015-mirror-sims3-vs-smartbot-sims3): tentative, no 95% CI excludes 0: `mirror_sims3 - smartbot_sims3 = +0.0 pts [-8.0, +8.3]` over 200 shared matches: no significant difference
- **Mechanism:** the target is 1 of ~40 pool slots, so a sure win vs it shifts the pooled score by about 1 pt, inside any pool CI (0014: 96.8% of rounds vs agamemnon, +0.8 pts vs the pool; 0015: 42% of rounds vs smartbot_sims3, +0.0 pts vs the pool)
- **Implication:** judge bot-specific specialists head to head (the evaluate skill's seed ladder, or idea #28's evaluation mode), and keep them as gated experts rather than as field bots

## 2026-10-13: Computing a replayed bandit's likely move (estimate NORMAL) plays about as well as drawing it (256 Thompson draws), at 10-15x less time

- **Evidence:** experiments/0035-anti-smartbot-normal.md (run 20261013-020744_0035-anti-smartbot-normal): tentative, no 95% CI excludes 0: `anti_smartbot_normal - anti_smartbot_v1 = +0.8 pts [-6.5, +8.0]` over 200 shared matches: no significant difference; experiments/0036-anti-smartbot-sims-normal.md (run 20261013-020828_0036-anti-smartbot-sims-normal): tentative, no 95% CI excludes 0: `anti_smartbot_sims_normal - anti_smartbot_sims_v2 = -0.5 pts [-7.8, +6.8]` over 200 shared matches: no significant difference; experiments/0037-leader-hunter-normal.md (run 20261013-021452_0037-leader-hunter-normal): tentative, no 95% CI excludes 0: `leader_hunter_normal - leader_hunter_v1 = +2.2 pts [-5.8, +10.2]` over 200 shared matches: no significant difference; experiments/0038-gate-edge-smartbot-normal.md (run 20261013-021719_0038-gate-edge-smartbot-normal): tentative, no 95% CI excludes 0: `gate_edge_smartbot_normal - gate_edge_smartbot_v1 = +2.2 pts [-4.2, +9.2]` over 200 shared matches: no significant difference; experiments/0039-gate-bandit-period-normal.md (run 20261013-021945_0039-gate-bandit-period-normal): tentative, no 95% CI excludes 0: `gate_bandit_period_normal - gate_bandit_period_v1 = +2.8 pts [-5.0, +10.5]` over 200 shared matches: no significant difference; experiments/0040-level-k-gate-normal.md (run 20261013-022209_0040-level-k-gate-normal): tentative, no 95% CI excludes 0: `level_k_gate_normal - level_k_gate_v1 = -3.2 pts [-10.2, +3.2]` over 200 shared matches: no significant difference; experiments/0041-gate-main-first-normal.md (run 20261013-022614_0041-gate-main-first-normal): tentative, no 95% CI excludes 0: `gate_main_first_normal - gate_main_first_v2 = -5.2 pts [-12.0, +1.5]` over 200 shared matches: no significant difference; experiments/0042-gate-main-first-stationary-normal.md (run 20261013-022912_0042-gate-main-first-stationary-normal): tentative, no 95% CI excludes 0: `gate_main_first_stationary_normal - gate_main_first_stationary_v2 = -3.8 pts [-10.5, +3.2]` over 200 shared matches: no significant difference; experiments/0043-gate-edge-normal.md (run 20261013-023206_0043-gate-edge-normal): tentative, no 95% CI excludes 0: `gate_edge_normal - gate_edge_v2 = +4.8 pts [-2.0, +11.5]` over 200 shared matches: no significant difference; experiments/0044-double-bluff-gate-normal.md (run 20261013-023506_0044-double-bluff-gate-normal): tentative, no 95% CI excludes 0: `double_bluff_gate_normal - double_bluff_gate_v1 = +1.0 pts [-7.8, +10.0]` over 200 shared matches: no significant difference; experiments/0045-replay-hunter-gate-normal.md (run 20261013-023804_0045-replay-hunter-gate-normal): tentative, no 95% CI excludes 0: `replay_hunter_gate_normal - replay_hunter_gate_v1 = +0.0 pts [-6.5, +6.8]` over 200 shared matches: no significant difference; experiments/0046-replay-hunter-wide-normal.md (run 20261013-024435_0046-replay-hunter-wide-normal): tentative, no 95% CI excludes 0: `replay_hunter_wide_normal - replay_hunter_wide_v1 = +4.2 pts [-2.2, +10.5]` over 200 shared matches: no significant difference; experiments/0047-predator-normal.md (run 20261013-040522_0047-predator-normal): tentative, no 95% CI excludes 0: `predator_normal - predator_v1 = +1.5 pts [-6.5, +9.2]` over 200 shared matches: no significant difference
- **Mechanism:** the normal approximation of each arm's draw names the same move as thousands of Thompson draws in about 98% of rounds, so the replay's prediction barely changes while its cost drops; across 13 bots no paired difference reached significance (from -5.2 to +4.8 pts, CIs about +-7 pts)
- **Implication:** use estimate NORMAL in every new replay of a Dirichlet bandit (draws 0 for other scorers); the time saved buys more experts or more round robins

## 2026-10-12: Replaying more of the field's learners keeps paying (+5.4 pts over the field for four more replays) until what is left under 36% of rounds is the unreplayable: the other strong L4s and the samplers

- **Evidence:** experiments/0034-replay-hunter-wide-vs-replay-hunter-gate.md (run 20261012-173356_0034-replay-hunter-wide-vs-replay-hunter-gate): `replay_hunter_wide - replay_hunter_gate_v1 = +5.4 pts [+0.8, +10.0]` over 315 shared matches: replay_hunter_wide better
- **Mechanism:** each replay turns a learner that splits the rounds near 1/3 into a 38-59% matchup; an L4 can't replay an L4 (that would be L5), and a sampler's next move is fresh randomness
- **Implication:** a per-round bar vs every bot is out of reach by construction; next gains: a frequency expert for fixed distributions (biased_v1 35.5%), replays of the last learners (geometry_ensemble, leader_hunter, period_detector, sicilian_meta), the EDGE-gate state model (#42) for double_bluff_gate

## 2026-10-12: An adaptive learner that splits the rounds with a metabot (31-34%) is beaten by its own replay from its seat: Thompson and greedy learners commit to a move a replay can name, lifting them to 38-49% of rounds; a learner that samples its moves (sampled_markov, transition_matrix, geometry, nash) has no fixed move to replay

- **Evidence:** experiments/0033-replay-hunter-vs-level-k-gate.md (run 20261012-171926_0033-replay-hunter-vs-level-k-gate): `replay_hunter_gate - level_k_gate_v1 = +16.1 pts [+4.8, +28.2]` over 62 shared matches: replay_hunter_gate better
- **Mechanism:** a 256-draw replay names a Thompson learner's posterior mode, a draws-0 replay a greedy learner's best arm; played BEAT inside a LEADER gate the arm takes over once it leads. Samplers draw fresh randomness each round, so nothing is predictable beyond what our main bandit already reads
- **Implication:** replay every replayable (L2/L3) learner of the field that splits the rounds with us, at every rotation; accept ~1/3 vs samplers; the cost grows ~linearly with the replays (2x level_k_gate for eight)

## 2026-10-12: Replays of the field's metabot from both seats, each played at every rotation, cover every level of a replay chain at once: no one-rotation specialist (anti, double-bluff counter) beats the bot that carries them, but against adaptive learners the round share still converges near 1/3

- **Evidence:** experiments/0032-level-k-vs-double-bluff-gate.md (run 20261012-164842_0032-level-k-vs-double-bluff-gate): `level_k_gate - double_bluff_gate_v1 = +9.0 pts [+2.8, +15.2]` over 305 shared matches: level_k_gate better; `level_k_bandit - double_bluff_gate_v1 = +7.5 pts [+1.6, +13.6]` over 305 shared matches: level_k_bandit better
- **Mechanism:** MY BEAT_BEAT beats an anti specialist, OPP BEAT the metabot itself and the gates' anti experts, OPP COPY a double-bluff counter; the gate or bandit picks the level that is winning. Against a learner that adapts as well (councils, gates, sampled_markov) neither side keeps an edge: 31-35% won, 30-35% lost per round
- **Implication:** a per-round bar of >= 36% holds only vs replayable bots; vs flip-flopping gated counters the next gain is modelling the opponent's gate state (idea #42), not more rotations or tuning (a 9-cell decay x sharpness screen stayed within 35-38%)

## 2026-10-12: A replay specialist that plays the mode of many Thompson draws is itself near-deterministic, so one more level of replay (the replayed bot from our side, played BEAT_BEAT) beats it in ~68% of rounds; gated by EDGE over the replayed bot's own arms it costs nothing against the rest of the field

- **Evidence:** experiments/0031-counter-anti-sims-vs-smartbot-sims.md (run 20261012-144707_0031-counter-anti-sims-vs-smartbot-sims): `gate_counter_sims - counter_anti_sims = +47.5 pts [+41.2, +53.7]` over 300 shared matches: gate_counter_sims better; `gate_counter_sims - smartbot_sims_v2 = +9.0 pts [+2.3, +15.7]` over 300 shared matches: gate_counter_sims better; `counter_anti_sims - smartbot_sims_v2 = -38.5 pts [-45.7, -31.2]` over 300 shared matches: smartbot_sims_v2 better
- **Mechanism:** anti_smartbot_sims_v2 plays beat(mode of 256 draws over smartbot_sims in our seat); our own 256-draw replay (own random stream since 1d3b9b7) names the same mode most rounds, and the ~15% of rounds lost are near-ties among smartbot_sims's arms where the two modes differ. The EDGE gate hands play to the counter only while it is winning, so the zoo still meets smartbot_sims's arms
- **Implication:** every deterministic replay specialist in the field (anti_smartbot_sims, gate_edge's anti expert, anti_iocaine, anti_rps4) invites a BEAT_BEAT counter one level up; a gate with several such counters is the next bot, and our own replays should sample their output (idea #10) rather than play the argmax

## 2026-10-10: An L4 gatekeeper that starts on the L3 arms and moves to the anti expert only once that expert's record leads (MAIN_FIRST, edge 0) keeps the best L2's strength vs L1 and beats the best L3 vs L2: the L3 regression vs lower levels is a gating problem, not a model problem

- **Evidence:** experiments/0028-l4-vs-l2-gate-main-first-vs-anti-advanced-bots-l.md (run 20261010-223059_0028-l4-vs-l2-gate-main-first-vs-anti-advanced-bots-l): `gate_main_first - anti_advanced_bots = +6.1 pts [+3.0, +9.4]` over 600 shared matches: gate_main_first better
- **Mechanism:** L3 bots regress vs lower levels: anti_advanced_bots plays at chance vs L1 (57% of matches), advanced_bot loses matches to the Thompson metabots. The L3 arms are as strong as the best L2 vs L1, so a gatekeeper that defaults to them loses nothing there (0027: +0.1 pts [-2.2, +2.5] vs iocaine_lite), and the anti expert's counterfactual record, kept every round, only leads vs bots running the replayed machinery, so it is played exactly vs the L2/L3 metabots (0028: +6.1 pts [+3.0, +9.4] vs anti_advanced_bots). Starting on the anti expert instead (ANTI_FIRST) costs L1 matches (0025: -1.5 [-3.8, +0.8]), mostly vs biased
- **Implication:** Build higher levels the same way: default to the strongest broad expert, gate in specialists on their own counterfactual records; screen gate rules with Oracle arms (they tracked the real L4 within ~2 pts) and validate per level with level-only pools (experiments/levels/L1, L2)

## 2026-10-10: The gatekeeper should start on the anti expert and switch to the advanced arms only once their counterfactual record leads by an edge (ANTI_FIRST), not wait for the anti expert to prove itself (EDGE)

- **Evidence:** experiments/0019-gatekeeper-rules-thorough-mocked.md (run 20261010-193841_0019-gatekeeper-rules-thorough-mocked): `mock_gate_anti_first - mock_replay_gate = +3.4 pts [+0.8, +6.0]` over 800 shared matches: mock_gate_anti_first better
- **Mechanism:** Against advanced opponents the anti expert is right from round 1, so EDGE loses the rounds it spends accumulating the replay's edge (84.5% vs 94.1% of advanced matches won). Against the zoo the advanced arms reach a large lead within a few rounds, so ANTI_FIRST pays only its warm-up, and once it switches it never reopens on noise (zoo margins +109.5 vs +89.7 rounds per match). Measured with the anti expert mocked (0017: mock faithful on the score, +2.5 pts [-2.5, +7.8]); the real twin is not confirmed yet
- **Implication:** Make ANTI_FIRST the default gatekeeper rule; tune its EDGE / WARMUP / GATE_DECAY with mocks; confirm a real twin vs replay_gate with mocks off; BANDIT is a close second (+2.4 pts [-0.1, +5.1]) worth a tuned rematch

## 2026-10-10: The gatekeeper: a selector that decides, per opponent, between the anti_advanced strategy (a replay of the field's best metabot) and the advanced strategy (that metabot's own arms) keeps both the zoo and the metabot family; it opens on the replay's own record (undecayed P(win) - P(loss) > ~0.06), not on how complex the opponent looks

- **Evidence:** experiments/0016-replay-gate-vs-advanced-bot-and-anti-advanced-bo.md (run 20261010-185932_0016-replay-gate-vs-advanced-bot-and-anti-advanced-bo): `replay_gate - advanced_bot = +11.2 pts [+5.2, +17.5]` over 200 shared matches: replay_gate better; `replay_gate - anti_advanced_bots = +18.8 pts [+11.2, +26.2]` over 200 shared matches: replay_gate better
- **Mechanism:** The gatekeeper (`Gatekeeper` selector, janken/kit/selectors.py) keeps the anti expert's counterfactual record every round, played or not, and plays it while that record clears the edge; otherwise Thompson over the advanced arms. It really tells advanced (multi-armed meta) opponents from the zoo, not complex from simple: the opponent's noisiness (conditional entropy, cheap-predictor hit rate) only isolates the trivial zoo, while word2janken, pattern_memory, staller, markov2_joint and transition_matrix look as random as the metabots, yet the advanced arms beat them and the replay can't. The replay's own edge separates the groups (+0.10 to +0.20 vs the family, ~0 vs the zoo) because it measures exactly whether the opponent runs the replayed machinery. Result: zoo 94.8% of matches (advanced_bot 95.7%, anti_advanced_bots 49.0%), family 83.7% (anti 94.7%, advanced 58.9%). Scoring the replay apart from the bandit avoids the dilution of 0015 (one replay arm among ~90 under Thompson)
- **Implication:** Add specialists as gated experts above the bandit, each with its own slow record, rather than as arms; tune the gate (EDGE, GATE_DECAY, WARMUP) to cut false openings vs staller / iocaine_lite; a bot that replays us (anti_advanced_bots: 10/10 vs replay_gate) needs its own expert, e.g. a replay of replay_gate's gate

## 2026-10-10: Simulating the opponent's model of us still beats near-deterministic bots outright on the blueprint code, and exact sims of greedy bots add more

- **Evidence:** experiments/0010-rebaseline-epoch-2.md (run 20261010-162748_0010-rebaseline-epoch-2): `smartbot_sims - smartbot_sims2 = -3.7 pts [-5.2, -2.3]` over 4000 shared matches: smartbot_sims2 better; `smartbot_sims - smartbot_sims3 = -5.0 pts [-6.4, -3.5]` over 4000 shared matches: smartbot_sims3 better; `smartbot_sims - smartbot_bandit = -5.0 pts [-6.4, -3.5]` over 4000 shared matches: smartbot_bandit better; `smartbot_sims - smartbot = +6.9 pts [+5.2, +8.5]` over 4000 shared matches: smartbot_sims better; `smartbot_sims2 - smartbot = +10.6 pts [+9.0, +12.2]` over 4000 shared matches: smartbot_sims2 better; `smartbot_sims3 - smartbot = +11.8 pts [+10.3, +13.4]` over 4000 shared matches: smartbot_sims3 better; `smartbot_bandit - smartbot = +11.8 pts [+10.3, +13.4]` over 4000 shared matches: smartbot_bandit better
- **Mechanism:** Bots that predict our next move and play its beat (word2janken, staller, markov2_joint, pattern_memory, iocaine_lite) are near-deterministic functions of the shared history; replaying them with roles swapped names their move, so the beat arm wins almost every round (76-82% -> 100%). The rps4_lite and staller sims of sims2 do the same for greedy-scoreboard bots (rps4_lite 70% -> 99%).
- **Implication:** Any new deterministic or greedy zoo bot should get a sim arm. The remaining losses are against adaptive bots and our own family, where sims don't name the move: try lead-lock stalling there (#22) and a self-sim (#13).

## 2026-10-10: ~~Replaying a Thompson metabot's arm scores tips the metabot matchups, but only by a few rounds~~ (superseded by [0010](experiments/0010-rebaseline-epoch-2.md))

- **Evidence:** experiments/0005-smartbot-sims3.md (run 20261010-001100_0005-smartbot-sims3):
  smartbot_sims3 - smartbot_sims2 = +1.3 pts [+0.1, +2.5], 4000 paired matches; per
  opponent smartbot_geo +18.9, meta_smartbot +11.0, smartbot +7.9 pts, with round margins
  of only +1...+4.
- **Mechanism:** the best-posterior-mean arm of a replayed metabot names its actual move
  ~45% of the time (diagnostic, chance 33%), so one arm can beat it. The metabot then
  adapts, because its own arms that model us start winning, so the edge stays at a few
  rounds per match. That is enough to win a coin-flip match more often, and not more.
- **Implication:** against adaptive bots, gains come from tipping close matches. Next:
  the bandit's own commitment and predictability (ideas #7, #10), and a replay of our own
  sims family (#13), now that it is in the pool.

## 2026-10-10: ~~Simulating the opponent's model of us beats near-deterministic bots outright~~ (superseded by [0010](experiments/0010-rebaseline-epoch-2.md))

- **Evidence:** experiments/0003-smartbot-sims.md (run 20261010-000022_0003-smartbot-sims):
  smartbot_sims - smartbot = +9.1 pts [+6.1, +12.2], 800 paired matches. pattern_memory,
  iocaine_lite, markov2_joint, word2janken and staller all go to 100% (from 52-89%),
  with round margins of +22...+164 instead of +1...+11.
- **Mechanism:** these bots predict *our* next move and play its beat. Replaying the same
  algorithm on the shared history (with the roles swapped) predicts their move 76-97% of
  the time; as three bandit arms it also covers bots that counter those models. smartbot's
  own predictors only model the opponent's moves, so they see these bots as noise.
- **Implication:** every deterministic or greedy zoo bot should get a sim arm. Next:
  sims of rps4_lite (greedy arm argmax) and staller (exact scoreboard), then posterior-mean
  sims of the Thompson metabots (ideas #11-#13). Since this is how Bow's 1st place
  jumped (rps_kaggle section 6.5), it confirms that idea here.
