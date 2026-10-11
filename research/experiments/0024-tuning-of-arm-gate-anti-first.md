# 0024: tuning of arm_gate_anti_first

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** tuning
- **Idea:** —
- **Candidates:** `bots/arm_gate_anti_first.yaml`
- **Baselines:** —
- **Study:** `0024-tuning-of-arm-gate-anti-first`
- **Verdict:** drop

## Hypothesis

Optuna (TPE) over ANTI_FIRST's knobs (EDGE 0-0.3, GATE_DECAY 0.95-1.0, WARMUP 0-40), with the anti expert as a per-level Oracle arm, against a pool of only L1 and L2 bots (all 23): a validated configuration raises the L4's score vs L1 to at least the best L2's (iocaine_lite ~91.5%) without losing its lead over the best L3 vs L2 (anti_advanced_bots), i.e. a validated gain >= 1 pt vs the defaults.

## Command

```bash
uv run janken lab study run spaces/arm_gate_anti_first.yaml --study 0024-tuning-of-arm-gate-anti-first --rounds 200 --round-robins 5 --pool-size 23 --seed 0
```

## Results

Validations of study 0024-tuning-of-arm-gate-anti-first:

| validated | run | champion | trial | train | n | score vs pool [95% CI] | vs defaults [95% CI] |
|---|---|---|---|---|---|---|---|
| 2026-10-10 21:38:56 | 20261010-213840_validate-0024-tuning-of-arm-gate-anti-first | arm_gate_anti_first | -1 | 91.7% | 230 | 92.2% [88.0%, 95.0%] | +0.0 pts [+0.0, +0.0] |
| 2026-10-10 21:38:56 | 20261010-213840_validate-0024-tuning-of-arm-gate-anti-first | arm_gate_anti_first@739cee | 34 | 95.7% | 230 | 90.7% [86.2%, 93.8%] | -1.5 pts [-5.0, +2.0] |
| 2026-10-10 21:38:56 | 20261010-213840_validate-0024-tuning-of-arm-gate-anti-first | arm_gate_anti_first@f1f492 | 54 | 95.7% | 230 | 92.6% [88.5%, 95.3%] | +0.4 pts [-3.7, +4.3] |
| 2026-10-10 21:38:56 | 20261010-213840_validate-0024-tuning-of-arm-gate-anti-first | arm_gate_anti_first@d12b02 | 75 | 94.8% | 230 | 93.0% [89.0%, 95.7%] | +0.9 pts [-3.3, +5.0] |
| 2026-10-10 21:38:56 | 20261010-213840_validate-0024-tuning-of-arm-gate-anti-first | arm_gate_anti_first@a41f52 | 80 | 95.2% | 230 | 91.5% [87.2%, 94.5%] | -0.7 pts [-5.7, +4.1] |
| 2026-10-10 21:38:56 | 20261010-213840_validate-0024-tuning-of-arm-gate-anti-first | arm_gate_anti_first@c7eb86 | 93 | 96.5% | 230 | 93.5% [89.5%, 96.0%] | +1.3 pts [-2.8, +5.2] |

## Analysis

Anti expert as a per-level Oracle arm (arm_gate_anti_first), pool = the 23 L1 and L2 bots (experiments/levels/L12), candidates mode. The training winners cluster at EDGE ~0.01, GATE_DECAY ~0.985, WARMUP ~20 but don't validate. On 32 paired seeds the defaults already sit at -0.7 pts [-3.3, +1.8] vs iocaine_lite (best L2) vs L1 and +7.3 pts [+2.2, +12.4] vs anti_advanced_bots (best L3) vs L2; BANDIT is equivalent (-0.9 / +6.5), EDGE (arm_replay_gate) loses the L2 lead (+1.0 [-4.8, +6.9]).

## Verdict

**drop**. Optuna (TPE, 100 trials) over ANTI_FIRST's knobs vs an L1+L2-only pool finds nothing better than the defaults (EDGE 0.05, GATE_DECAY 1.0, WARMUP 10): the top 5 trials (94.8-96.5% in training) validate between -1.5 pts [-5.0, +2.0] and +1.3 pts [-2.8, +5.2]; flat, like 0020.
