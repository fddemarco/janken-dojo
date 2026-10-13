# 0049: l5_variant_hunter vs l5_hunter

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #51
- **Candidates:** `bots/l5/l5_variant_hunter.yaml`
- **Baselines:** `bots/l5/l5_hunter.yaml`
- **Run:** `20261013-120010_0049-l5-variant-hunter-vs-l5-hunter`
- **Verdict:** iterate

## Hypothesis

l5_variant_hunter is no worse than l5_hunter (paired difference above -2 pts) and gains vs rps4_lite, outcome_reader, iocaine_lite and period_bandit: the 32 parameter variants enter the gate pooled as one expert (variant_pool), so they can't make the false leads that cost note 0048 10 pts

## Command

```bash
uv run janken lab experiment bots/l5/l5_variant_hunter.yaml bots/l5/l5_hunter.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 1602441684 --name 0049-l5-variant-hunter-vs-l5-hunter
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 1602441684, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| l5_hunter | 200 | 170-2-28 | 85.5% [80.0%, 89.7%] | +47.3 | 0 | 1818 +/- 80 |
| l5_variant_hunter | 200 | 169-3-28 | 85.2% [79.7%, 89.5%] | +49.8 | 0 | 1816 +/- 71 |

Paired comparisons:

- `l5_variant_hunter - l5_hunter = -0.2 pts [-6.2, +5.8]` over 200 shared matches: no significant difference

Weakest matchups of l5_variant_hunter: l5_priority 0.0%, l5_lean_hunter 0.0%, sicilian_meta_v1 0.0%, nash_v1 33.3%, l5_identify_hunter 33.3%, geometry_v1 50.0%.

Weakest matchups of l5_hunter: l5_level_k 0.0%, l5_lean_hunter 0.0%, l5_identify_hunter 33.3%, nash_v1 33.3%, outcome_reader_v1 50.0%, sampled_markov_v1 50.0%.

## Analysis

Gauntlet (janken lab gauntlet run research/gauntlet/identify_bandits.txt, 24 opponents: 8 bandit species at their defaults and 2 variants each, drawn with a different seed from variant_pool's own, 5 seeds x 250 rounds, log experiments/gauntlet/variant_hunter.jsonl): mean share won 50.1% vs l5_hunter's 42.9%; paired rounds won minus lost +11.1 pts +- 4.1 (95%) over 120 matches. Per species: rps4_lite +43.1, outcome_reader +25.1, iocaine_lite +21.8, period_bandit +2.9, multiscale_council +1.3, geometry_ensemble +0.7, sampled_markov -1.2, smartbot -4.7. Both stay under 36% vs 5 opponents (sampled_markov and multiscale variants for both). Caveat: every opponent's species is among the replayed ones or the field's; janken lab identify found no gain vs held-out species, only no loss.

## Verdict

**iterate**. Vs random pools of the field (default parameters, 200 rounds) l5_variant_hunter - l5_hunter = -0.2 pts [-6.2, +5.8] over 200 paired matches (10 round robins, the cap): pooling the 32 variants into one gated expert removed note 0048's 10 pt loss, but the pools hold no parameter variants, so the effect it is built for can't show here. On the variants list it is far better (below), so the next step is an evaluation whose pools hold variants.
