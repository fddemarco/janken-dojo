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
