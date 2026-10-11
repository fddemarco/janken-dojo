# 0009: tpi_lite vs smartbot_sims3

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #2
- **Candidates:** `bots/tpi_lite.yaml`
- **Baselines:** `bots/smartbot_sims3.yaml`
- **Run:** `20261010-162333_0009-tpi-lite-vs-smartbot-sims3`
- **Verdict:** drop

## Hypothesis

tpi_lite (smartbot_sims3 plus a naive-Bayes combiner arm over its 28 signals) beats smartbot_sims3 by >= 1.5 pts in the paired comparison, mostly in the close matchups against the metabots, the smartbot family and geometry, where no single predictor dominates but their combined evidence does.

## Command

```bash
uv run janken lab experiment bots/tpi_lite.yaml bots/smartbot_sims3.yaml --rounds 200 --round-robins 40 --pool-size 20 --seed 2533817567 --name 0009-tpi-lite-vs-smartbot-sims3
```

## Results

40 of 40 round robin(s) · pool 20 · 200 rounds/match · seed 2533817567 · mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating ± sd |
|---|---|---|---|---|---|---|
| smartbot_sims3 | 800 | 635-16-149 | 80.4% [77.5%, 83.0%] | +69.3 | 0 | 1763 ± 80 |
| tpi_lite | 800 | 632-11-157 | 79.7% [76.8%, 82.3%] | +70.3 | 0 | 1775 ± 82 |

Paired comparisons:

- `tpi_lite − smartbot_sims3 = -0.7 pts [-3.9, +2.5]` over 800 shared matches: no significant difference

Weakest matchups of tpi_lite: hector 35.7%, smartbot_bandit 45.7%, smartbot_sims 45.8%, geometry 50.0%, odysseus 52.4%, nash 55.0%.

Weakest matchups of smartbot_sims3: agamemnon 38.9%, odysseus 47.6%, smartbot_sims 50.0%, smartbot_bandit 50.0%, achilles 53.1%, hector 57.1%.

## Analysis

Per opponent (20-30 matches each, so about +-20 pts of noise) the differences go both ways and look like noise: tpi_lite is ahead vs agamemnon (69% vs 39%), meta_smartbot (80 vs 63), smartbot (70 vs 59) and achilles (66 vs 53), behind vs hector (36 vs 57), geometry (50 vs 67), smartbot_sims2 (61 vs 78) and nash (55 vs 65; nash is uniform random, so 65% there is luck and shows the size of the noise). Mean round margins are within a few rounds everywhere. The combiner's evidence is heavily correlated (18 predictors that often agree, plus sims), so its posterior is overconfident, but the EV-best move is unaffected by that; the likelier reason for the null is dilution: its 3 arms compete with 87 others under one Dirichlet/Thompson bandit and are only picked when they lead, which is when the predictors they summarise already do. A test of TPI's actual design, the combiner deciding the move on its own (or as a fallback tie-breaker), is a different idea and is added as a follow-up. BAYES_DECAY (0.95) was not varied.

## Verdict

**drop**. Adding a TPI-lite naive-Bayes combiner arm (the new NaiveBayes stage over all 28 signals, x 3 rotations) to smartbot_sims3 changes nothing measurable: tpi_lite - smartbot_sims3 = -0.7 pts [-3.9, +2.5] over 800 paired matches (79.7% vs 80.4% vs the pool, 40 round robins). The stage stays in the kit; as one more arm among 90 under Thompson sampling it adds no edge.
