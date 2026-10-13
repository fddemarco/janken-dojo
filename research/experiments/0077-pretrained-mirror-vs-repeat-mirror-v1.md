# 0077: pretrained_mirror vs repeat_mirror_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #72
- **Candidates:** `bots/l2/pretrained_mirror.yaml`
- **Baselines:** `bots/l2/repeat_mirror_v1.yaml`
- **Run:** `20261013-161127_0077-pretrained-mirror-vs-repeat-mirror-v1`
- **Verdict:** drop

## Hypothesis

Confirmation on fresh seeds at the thorough budget: pretrained_mirror beats repeat_mirror_v1 by >= 2 pts vs L1+L2 pools of parameter variants (first run: +6.0 pts [-1.0, +13.2])

## Command

```bash
uv run janken lab experiment bots/l2/pretrained_mirror.yaml bots/l2/repeat_mirror_v1.yaml --rounds 250 --round-robins 16 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --variants 1.0 --seed 2797168282 --name 0077-pretrained-mirror-vs-repeat-mirror-v1
```

## Results

16 of 16 round robin(s), pool 20, 250 rounds/match, seed 2797168282, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| pretrained_mirror | 320 | 231-8-81 | 73.4% [68.3%, 78.0%] | +53.6 | 0 | 1710 +/- 62 |
| repeat_mirror_v1 | 320 | 228-7-85 | 72.3% [67.2%, 77.0%] | +51.2 | 0 | 1700 +/- 73 |

Paired comparisons:

- `pretrained_mirror - repeat_mirror_v1 = +1.1 pts [-4.5, +7.0]` over 320 shared matches: no significant difference

Weakest matchups of pretrained_mirror: anti_smartbot_v2 16.7%, anti_rps4_v1 25.0%, period_bandit_v1 25.0%, smartbot_fast_v1 33.3%, mirror_bandit_v1 33.3%, anti_iocaine_v1 35.0%.

Weakest matchups of repeat_mirror_v1: anti_smartbot_v2 16.7%, iocaine_lite_v1 16.7%, anti_iocaine_v1 20.0%, vote_ensemble_v1 22.2%, anti_rps4_v1 25.0%, smartbot_v1 25.0%.

## Analysis

Scores: 73.4% of matches (+53.6 rounds per match) vs 72.3% (+51.2). Pre-training pays where the learner starts weak (a context table with no other knowledge), not as one more arm among strong online predictors that learn the same contexts within the match.

## Verdict

**drop**. On fresh seeds the pre-trained arm adds nothing measurable: pretrained_mirror - repeat_mirror_v1 = +1.1 pts [-4.5, +7.0] over 320 paired matches vs L1+L2 pools of parameter variants (thorough budget, futile at look 2): note 0076's +6.0 was the high draw. The prior that lifts a plain table by +9.8 pts over CTW doesn't lift a bandit whose online arms are already strong.
