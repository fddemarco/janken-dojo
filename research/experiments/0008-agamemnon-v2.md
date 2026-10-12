# 0008: agamemnon-v2

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** tuning
- **Idea:** -
- **Candidates:** `agamemnon`
- **Baselines:** -
- **Study:** `0008-agamemnon-v2`
- **Verdict:** drop

## Hypothesis

defaults are not optimal

## Command

```bash
uv run janken lab study run spaces/agamemnon.yaml --study 0008-agamemnon-v2 --rounds 250 --round-robins 10 --pool-size 20 --seed 0
```

## Results

Validations of study 0008-agamemnon-v2:

| validated | run | champion | trial | train | n | score vs pool [95% CI] | vs defaults [95% CI] |
|---|---|---|---|---|---|---|---|
| 2026-10-10 16:05:56 | 20261010-160535_validate-0008-agamemnon-v2 | agamemnon | -1 | 85.0% | 200 | 88.2% [83.1%, 92.0%] | +0.0 pts [+0.0, +0.0] |
| 2026-10-10 16:05:56 | 20261010-160535_validate-0008-agamemnon-v2 | agamemnon@47a301 | 26 | 90.2% | 200 | 86.0% [80.5%, 90.1%] | -2.2 pts [-7.0, +2.3] |
| 2026-10-10 16:05:56 | 20261010-160535_validate-0008-agamemnon-v2 | agamemnon@7897bb | 75 | 90.2% | 200 | 84.8% [79.1%, 89.1%] | -3.5 pts [-9.0, +1.8] |
| 2026-10-10 16:05:56 | 20261010-160535_validate-0008-agamemnon-v2 | agamemnon@8304c4 | 84 | 91.5% | 200 | 86.2% [80.8%, 90.3%] | -2.0 pts [-7.0, +3.2] |
| 2026-10-10 16:05:56 | 20261010-160535_validate-0008-agamemnon-v2 | agamemnon@7acddc | 89 | 91.8% | 200 | 86.5% [81.1%, 90.6%] | -1.8 pts [-6.5, +3.2] |
| 2026-10-10 16:05:56 | 20261010-160535_validate-0008-agamemnon-v2 | agamemnon@9e15ff | 93 | 92.2% | 200 | 85.0% [79.4%, 89.3%] | -3.2 pts [-8.8, +2.0] |

## Analysis

Training scores of the top trials (90-92%) exceed the defaults' 85% on the training pools, but none of that survives fresh pools: the five validated configs are all negative, each CI crossing 0, mean about -2.5 pts. They are overfit to the fixed pools. The winners share a direction (ARM_DECAY ~0.97-0.99, TABLE_DECAY ~0.61-0.77, MAX_MATCH 14-20): forgetting the pattern tables faster. In validation that costs against the strong opponents. The defaults' weakest matchups are the smartbot family (sims3 33%, bandit 40%, meta_smartbot 44%), while the tuned @7acddc and @9e15ff drop to 17-33% vs nash and 25-33% vs smartbot_geo, whom the defaults hold at 50%. Fleet supports (achilles, ajax, hector, odysseus) in the pool throw every match to any agamemnon variant, inflating absolute scores equally for all candidates; the paired differences are unaffected. Agamemnon's knobs are near a flat optimum; further gains need new signals, not decay tuning.

## Verdict

**drop**. Tuning agamemnon (10 round robins per trial, 100 trials) does not improve on its defaults ARM_DECAY 0.95, TABLE_DECAY 0.9, MAX_MATCH 12: all 5 validated configs score below them, from -1.8 pts [-6.5, +3.2] to -3.5 pts [-9.0, +1.8] vs the defaults' 88.2%. Keep the defaults.
