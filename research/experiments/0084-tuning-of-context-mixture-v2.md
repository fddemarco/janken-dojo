# 0084: tuning of context_mixture_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** tuning
- **Idea:** #83
- **Candidates:** `bots/l1/context_mixture_v2.yaml`
- **Baselines:** -
- **Study:** `0084-tuning-of-context-mixture-v2`
- **Verdict:** keep

## Hypothesis

A decay below 0.8 beats context_mixture_v2 (DECAY 0.81) by >= 2 pts on fresh validation pools: the first tuning's optimum sat at its space's lower bound (idea #83)

## Command

```bash
uv run janken lab study run spaces/context_mixture_v2.yaml --study 0084-tuning-of-context-mixture-v2 --rounds 200 --round-robins 5 --pool-size 20 --seed 0
```

## Results

Validations of study 0084-tuning-of-context-mixture-v2:

| validated | run | champion | trial | train | n | score vs pool [95% CI] | vs defaults [95% CI] |
|---|---|---|---|---|---|---|---|
| 2026-10-13 16:54:25 | 20261013-165325_validate-0084-tuning-of-context-mixture-v2 | context_mixture_v2 | -1 | 40.5% | 200 | 41.0% [34.4%, 47.9%] | +0.0 pts [+0.0, +0.0] |
| 2026-10-13 16:54:25 | 20261013-165325_validate-0084-tuning-of-context-mixture-v2 | context_mixture_v2@7f301c | 8 | 42.5% | 200 | 44.0% [37.3%, 50.9%] | +3.0 pts [-3.0, +9.2] |
| 2026-10-13 16:54:25 | 20261013-165325_validate-0084-tuning-of-context-mixture-v2 | context_mixture_v2@c8fc7e | 11 | 41.5% | 200 | 41.2% [34.7%, 48.2%] | +0.2 pts [-5.8, +6.2] |
| 2026-10-13 16:54:25 | 20261013-165325_validate-0084-tuning-of-context-mixture-v2 | context_mixture_v2@0d37a7 | 14 | 44.0% | 200 | 42.5% [35.9%, 49.4%] | +1.5 pts [-4.2, +7.5] |
| 2026-10-13 16:54:25 | 20261013-165325_validate-0084-tuning-of-context-mixture-v2 | context_mixture_v2@b00fe2 | 15 | 47.0% | 200 | 47.8% [40.9%, 54.6%] | +6.8 pts [+0.5, +13.2] |
| 2026-10-13 16:54:25 | 20261013-165325_validate-0084-tuning-of-context-mixture-v2 | context_mixture_v2@2f787c | 23 | 47.0% | 200 | 46.5% [39.7%, 53.4%] | +5.5 pts [-0.8, +12.0] |

## Analysis

30 TPE trials over DECAY in [0.5, 1.0]. The validated configurations cluster at 0.69-0.72, and only the upper end of that cluster clears the defaults: a narrow optimum, so the confirmation run decides.

## Verdict

**keep**. One validated configuration beats context_mixture_v2: trial 15 (DECAY 0.723) by +6.8 pts [+0.5, +13.2] on fresh pools (200 paired matches); trial 23 (0.724) +5.5 [-0.8, +12.0], trials at 0.69-0.71 +0.2 to +3.0 (n.s.). The optimum looks near 0.72, below the first tuning's bound.
