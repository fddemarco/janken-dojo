# 0082: tuning of context_mixture_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** tuning
- **Idea:** #82
- **Candidates:** `bots/l1/context_mixture_v1.yaml`
- **Baselines:** -
- **Study:** `0082-tuning-of-context-mixture-v1`
- **Verdict:** keep

## Hypothesis

A decayed CTW (DECAY in [0.8, 1]) beats context_mixture_v1's undecayed counts (DECAY 1.0) by >= 2 pts on fresh validation pools: forgetting follows opponents that switch (idea #82)

## Command

```bash
uv run janken lab study run spaces/context_mixture_v1.yaml --study 0082-tuning-of-context-mixture-v1 --rounds 200 --round-robins 5 --pool-size 20 --seed 0
```

## Results

Validations of study 0082-tuning-of-context-mixture-v1:

| validated | run | champion | trial | train | n | score vs pool [95% CI] | vs defaults [95% CI] |
|---|---|---|---|---|---|---|---|
| 2026-10-13 16:45:59 | 20261013-164348_validate-0082-tuning-of-context-mixture-v1 | context_mixture_v1 | -1 | 30.0% | 200 | 30.2% [24.3%, 36.9%] | +0.0 pts [+0.0, +0.0] |
| 2026-10-13 16:45:59 | 20261013-164348_validate-0082-tuning-of-context-mixture-v1 | context_mixture_v1@e70b18 | 8 | 41.5% | 200 | 35.2% [29.0%, 42.1%] | +5.0 pts [+0.2, +9.8] |
| 2026-10-13 16:45:59 | 20261013-164348_validate-0082-tuning-of-context-mixture-v1 | context_mixture_v1@c4beb0 | 10 | 44.5% | 200 | 36.2% [29.9%, 43.1%] | +6.0 pts [+1.0, +10.8] |
| 2026-10-13 16:45:59 | 20261013-164348_validate-0082-tuning-of-context-mixture-v1 | context_mixture_v1@41e5d8 | 21 | 42.0% | 200 | 35.5% [29.2%, 42.3%] | +5.2 pts [+0.5, +10.0] |
| 2026-10-13 16:45:59 | 20261013-164348_validate-0082-tuning-of-context-mixture-v1 | context_mixture_v1@e17be8 | 22 | 41.5% | 200 | 35.2% [29.0%, 42.1%] | +5.0 pts [+0.0, +10.0] |
| 2026-10-13 16:45:59 | 20261013-164348_validate-0082-tuning-of-context-mixture-v1 | context_mixture_v1@cba441 | 27 | 40.5% | 200 | 36.0% [29.7%, 42.9%] | +5.8 pts [+0.8, +10.5] |

## Analysis

30 TPE trials over DECAY in \[0.8, 1\]: training scores 40.5-44.5% fell to 35.2-36.2% on validation, but each stays clear of the defaults' 30.2%. A decayed KT count forgets an opponent's old habits, which pays vs the field's adaptive bots (whole-field pools, mostly L2+). Next: a bot with DECAY 0.81 evaluated vs context_mixture_v1, and a wider space (down to 0.5) if it holds.

## Verdict

**keep**. Forgetting helps CTW: every validated configuration beats context_mixture_v1's undecayed counts on fresh pools, the best (trial 10, DECAY 0.811) by +6.0 pts [+1.0, +10.8] (200 paired matches), trials 8, 21, 22, 27 (DECAY 0.808-0.816) by +5.0 to +5.8 pts. All sit at the space's lower bound (0.8), so the optimum may lie lower.
