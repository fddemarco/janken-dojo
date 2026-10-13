# 0076: pretrained_mirror vs repeat_mirror_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #72
- **Candidates:** `bots/l2/pretrained_mirror.yaml`
- **Baselines:** `bots/l2/repeat_mirror_v1.yaml`
- **Run:** `20261013-161048_0076-pretrained-mirror-vs-repeat-mirror-v1`
- **Verdict:** iterate

## Hypothesis

Adding the pre-trained context table as an arm lifts repeat_mirror: pretrained_mirror beats repeat_mirror_v1 by >= 2 pts vs L1+L2 pools of parameter variants the prior never trained on (pool.variants 1.0, 250 rounds); the table alone beat context_mixture by +9.8 pts (notes 0072, 0073) (idea #72)

## Command

```bash
uv run janken lab experiment bots/l2/pretrained_mirror.yaml bots/l2/repeat_mirror_v1.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --variants 1.0 --seed 453274464 --name 0076-pretrained-mirror-vs-repeat-mirror-v1
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 453274464, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| pretrained_mirror | 200 | 141-6-53 | 72.0% [65.4%, 77.8%] | +51.2 | 0 | 1692 +/- 86 |
| repeat_mirror_v1 | 200 | 131-2-67 | 66.0% [59.2%, 72.2%] | +46.3 | 0 | 1648 +/- 83 |

Paired comparisons:

- `pretrained_mirror - repeat_mirror_v1 = +6.0 pts [-1.0, +13.2]` over 200 shared matches: no significant difference

Weakest matchups of pretrained_mirror: geometry_v1 0.0%, anti_rps4_v1 20.0%, rps4_lite_v1 20.0%, mirror_bandit_v1 25.0%, geometry_ensemble_v1 25.0%, anti_iocaine_v1 30.0%.

Weakest matchups of repeat_mirror_v1: sampled_markov_v1 0.0%, second_guess_v1 16.7%, anti_iocaine_v1 20.0%, anti_rps4_v1 20.0%, anti_smartbot_v2 25.0%, smartbot_fast_v1 25.0%.

## Analysis

72.0% of matches vs 66.0%, +51.2 rounds per match vs +46.3. Weakest matchups: geometry_v1 (0%), anti_rps4, rps4_lite (20%), mirror_bandit and geometry_ensemble (25%).

## Verdict

**iterate**. Positive but unresolved: pretrained_mirror (repeat_mirror plus the pre-trained context table as an arm) - repeat_mirror_v1 = +6.0 pts [-1.0, +13.2] over 200 paired matches vs L1+L2 pools of parameter variants (250 rounds); confirmed or not on fresh seeds in note 0077.
