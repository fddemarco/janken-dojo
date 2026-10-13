# 0032: level-k gate and bandit (specialists at every rotation) vs double_bluff_gate_v1 (whole field, 250 rounds)

- **Date:** 2026-10-12
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #39
- **Candidates:** `bots/l4/level_k_gate.yaml`, `bots/l4/level_k_bandit.yaml`
- **Baselines:** `bots/l4/double_bluff_gate_v1.yaml`
- **Run:** `20261012-164842_0032-level-k-vs-double-bluff-gate`
- **Verdict:** keep
- **Species:** `level_k_gate_v1` (new species)

## Hypothesis

Both level-k bots beat double_bluff_gate_v1 over the whole field (paired, >= 0 pts; their extra rotations cover the levels a one-rotation counter leaves open) and win every head-to-head vs the L4 gates and smartbot_sims_v2. The goal is >= 36% of rounds vs every field bot but nash (chance, 33%): head to head (seed ladder, 2026-10-12) level_k_gate wins 38-41% vs gate_main_first_v2, gate_edge_v2, gate_main_first_stationary_v2, smartbot_sims_v2 and 71% vs anti_smartbot_sims_v2 but 34.7% vs double_bluff_gate_v1; level_k_bandit ~36-37% vs double_bluff_gate_v1 and smartbot_sims_v2. Expect the per-opponent round shares vs the zoo far above 36%, with the weakest matchups among the L3/L4 metabots.

## Command

```bash
uv run janken lab experiment bots/l4/level_k_gate.yaml bots/l4/level_k_bandit.yaml bots/l4/double_bluff_gate_v1.yaml --rounds 250 --round-robins 5 --pool-size 61 --mode candidates --allow-small-pool --no-mocks --seed 413136723 --name 0032-level-k-vs-double-bluff-gate
```

## Results

5 of 5 round robin(s), pool 61, 250 rounds/match, seed 413136723, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| level_k_gate | 305 | 244-3-58 | 80.5% [75.7%, 84.5%] | +61.0 | 0 | 1796 +/- 39 |
| level_k_bandit | 305 | 238-6-61 | 79.0% [74.1%, 83.2%] | +55.7 | 0 | 1788 +/- 37 |
| double_bluff_gate_v1 | 305 | 215-6-84 | 71.5% [66.2%, 76.3%] | +50.7 | 0 | 1702 +/- 32 |

Paired comparisons:

- `level_k_gate - level_k_bandit = +1.5 pts [-4.4, +7.2]` over 305 shared matches: no significant difference
- `level_k_gate - double_bluff_gate_v1 = +9.0 pts [+2.8, +15.2]` over 305 shared matches: level_k_gate better
- `level_k_bandit - double_bluff_gate_v1 = +7.5 pts [+1.6, +13.6]` over 305 shared matches: level_k_bandit better

Weakest matchups of level_k_gate: dropswitch_council_v1 20.0%, sampled_markov_v1 20.0%, l2_council_v1 40.0%, vote_council_v1 40.0%, backoff_family_v1 40.0%, period_bandit_v1 40.0%.

Weakest matchups of level_k_bandit: dropswitch_council_v1 10.0%, mirror_bandit_v1 20.0%, smartbot_fast_v1 20.0%, sicilian_meta_v1 30.0%, predator_v1 40.0%, vote_council_v1 40.0%.

Weakest matchups of double_bluff_gate_v1: mirror_bandit_v1 10.0%, fast_greedy_markov_v1 20.0%, period_detector_v1 20.0%, multiscale_v1 20.0%, l2_council_v1 30.0%, predator_v1 40.0%.

## Analysis

Every rotation of both replays closes the one-rotation exploit of 0031: anti_smartbot_sims is beaten by MY BEAT_BEAT (71%), the L4 gates' anti experts and smartbot_sims by OPP BEAT, double_bluff_gate's counter by OPP COPY. The LEADER gate commits, which pays vs smartbot_sims_v2 (41%) but trails double_bluff_gate_v1, whose EDGE gate flips to its counter whenever we play BEAT Y and back when we play Y (cumulative record vs 0.06): 34.7%; gate decays 0.9/0.8 don't help (35.6% at 50 seeds). A Thompson bandit over the 6 arms tracks the flips (decay 0.9: 37.0% vs double_bluff_gate at 50 seeds) but over-explores vs smartbot_sims_v2 (35.7%); sharpening (3) trades one for the other, and a 9-cell screen of decay x sharpness (10 seeds each) stays within 35-38% on both, inside the noise. The bandit beats the gate head to head in this run (44.4% vs 25.6% of rounds in one match; 42.2% vs 29.5% over 5). Over the field the round share converges near 1/3 against every adaptive learner (councils, gates, sampled_markov, backoff_family, smartbot_fast, period_bandit: 31-35% won, 30-35% lost): two bots that adapt about as well split the rounds, and vs nash_v1 the expectation is 33.3%. A >= 36% bar vs the whole field is out of reach of any bot that doesn't read its opponent's code; the bar holds vs the replayable bots (the smartbot family and its specialists). Next: a model of an EDGE gate's state (predict when a gated counter is on, from our own moves vs its predictor) would turn the double_bluff_gate flips into wins.

## Verdict

**keep**. level_k_gate beats double_bluff_gate_v1 over the whole field, +9.0 pts [+2.8, +15.2] over 305 paired matches (5 round robins of the 61-bot field, 250 rounds, mode candidates; conclusive at 1 round robin, +14.8 [+1.6, +27.9]), and level_k_bandit does too, +7.5 pts [+1.6, +13.6]; the gate and the bandit don't differ (+1.5 pts [-4.4, +7.2] at 5; an effect under ~3 pts, not played further). Head to head (seed ladder, 250 rounds) level_k_gate wins 38-41% of rounds vs gate_main_first_v2, gate_edge_v2, gate_main_first_stationary_v2 and smartbot_sims_v2, 71% vs anti_smartbot_sims_v2, every match, but 34.7% [33.5, 35.8] vs double_bluff_gate_v1 (20/25 matches); level_k_bandit (decay 0.85, sharp 3) 35.8-37% vs double_bluff_gate_v1 and smartbot_sims_v2. The goal's >= 36% of rounds vs every bot is not met: per opponent over 5 matches, level_k_gate is under 36% vs 24 of 63 bots (worst 29.5%, vs level_k_bandit), level_k_bandit vs 31 of 62, double_bluff_gate_v1 vs 37 of 61.

## Species

**new**: its core agrees with gate_main_first_stationary_v2 on 73% of the moves, below 80%.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `gate_main_first_stationary_v2` | L4 | 73.3% |
| `gate_main_first_v2` | L4 | 72.3% |
| `double_bluff_gate_v1` | L4 | 67.3% |
| `gate_edge_v2` | L4 | 63.5% |
