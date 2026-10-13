# 0015: mirror_sims3 vs smartbot_sims3

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #13
- **Candidates:** `bots/mirror_sims3.yaml`
- **Baselines:** `bots/smartbot_sims3.yaml`
- **Run:** `20261010-173510_0015-mirror-sims3-vs-smartbot-sims3`
- **Verdict:** keep

## Hypothesis

mirror_sims3 (an exact replay of smartbot_sims3 with a 256-draw Thompson vote, playing the beat of sims3's likeliest move, nothing else) wins its matches vs smartbot_sims3 (~42% of rounds head to head, seeds 1-40), but as a single-model specialist it scores far below smartbot_sims3 vs the pool (expect \<= -10 pts), losing to every bot that isn't sims3-like.

## Command

```bash
uv run janken lab experiment bots/mirror_sims3.yaml bots/smartbot_sims3.yaml --rounds 200 --round-robins 10 --pool-size 20 --seed 877486091 --name 0015-mirror-sims3-vs-smartbot-sims3
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 877486091, mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| mirror_sims3 | 200 | 156-5-39 | 79.2% [73.1%, 84.3%] | +13.1 | 0 | 1784 +/- 104 |
| smartbot_sims3 | 200 | 156-5-39 | 79.2% [73.1%, 84.3%] | +60.0 | 0 | 1739 +/- 41 |

Paired comparisons:

- `mirror_sims3 - smartbot_sims3 = +0.0 pts [-8.0, +8.3]` over 200 shared matches: no significant difference

Weakest matchups of mirror_sims3: copycat 16.7%, nash 25.0%, wsls 25.0%, word2janken 30.0%, counter_reactionary 33.3%, staller 37.5%.

Weakest matchups of smartbot_sims3: nash 0.0%, ajax 37.5%, smartbot_sims 40.0%, self_sim 42.9%, geometry 50.0%, tpi_lite 50.0%.

## Analysis

Per opponent the two are mirror images. mirror_sims3 wins every match vs the whole metabot family and its relatives (smartbot, smartbot_geo, smartbot_sims, \_sims2, \_sims3, smartbot_bandit, smart_staller, sims3_staller, sims3_second, self_sim, tpi_lite, the Iliad fleet, sinon, geometry, iocaine_lite, rps4_lite: 100% of matches, mostly 40-45% of rounds won), where smartbot_sims3 manages 38-83%: they share sims3's arms, signals and Dirichlet records, so a replay of sims3 predicts them too. It loses the zoo (copycat 17%, wsls 25%, word2janken 30%, counter_reactionary 33%, staller 38%, biased 50%, markov2_joint 64%; about 33% of rounds, i.e. chance), which smartbot_sims3 beats 100%, because a model of sims3 says nothing about them. Ceiling: diagnostics in plain Python put the mean top share of sims3's Thompson vote at about 44% of rounds, so the 42% head to head is near the limit of reading sims3 as it plays; the vote beats the best-mean arm (55 vs 47 hits in 120 rounds on the same match), and 64-1024 draws give the same 42%. Win share falls over the match (44% in rounds 0-49 to 40.5% in 200-249). A one-step lookahead that shapes sims3's records (prefer moves leaving its arm means lopsided) backfires: it feeds sims3's arms. Next: combine both experts (sims3's arms plus this replay, gated by which one is winning) to keep the zoo and the family.

## Verdict

**keep**. mirror_sims3, one signal (an exact replay of smartbot_sims3 with nested replays, naming the move its Thompson sampling picks most often over 256 draws) played with BEAT, matches smartbot_sims3 vs the pool with a far simpler blueprint: +0.0 pts [-8.0, +8.3] over 200 paired matches (both 79.2%), rating 1784 vs 1739. Head to head it beats smartbot_sims3: 10/10 matches in this run, and 42% of rounds won over seeds 1-40 at 250 rounds (mean, with 8-10 of the 40 matches below 40%). Kept as the new specialist vs the smartbot family.
