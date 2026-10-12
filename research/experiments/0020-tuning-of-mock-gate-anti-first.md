# 0020: tuning of mock_gate_anti_first

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** tuning
- **Idea:** #32
- **Candidates:** `bots/mock_gate_anti_first.yaml`
- **Baselines:** -
- **Study:** `0020-tuning-of-mock-gate-anti-first`
- **Verdict:** drop

## Hypothesis

ANTI_FIRST's knobs (EDGE lead margin 0-0.3, GATE_DECAY 0.95-1.0, WARMUP 0-40) have a validated better configuration than the defaults (0.05, 1.0, 10) by >= 2 pts: a shorter warm-up should recover the zoo matches ANTI_FIRST lost vs EDGE in 0019 (89.6% vs 91.6%), a decay < 1 may let it switch back when an advanced opponent adapts. Anti expert mocked, mocks in the pools.

## Command

```bash
uv run janken lab study run spaces/mock_gate_anti_first.yaml --study 0020-tuning-of-mock-gate-anti-first --rounds 200 --round-robins 10 --pool-size 20 --seed 0
```

## Results

Validations of study 0020-tuning-of-mock-gate-anti-first:

| validated | run | champion | trial | train | n | score vs pool [95% CI] | vs defaults [95% CI] |
|---|---|---|---|---|---|---|---|
| 2026-10-10 19:47:18 | 20261010-194615_validate-0020-tuning-of-mock-gate-anti-first | mock_gate_anti_first | -1 | 89.8% | 800 | 89.3% [87.0%, 91.3%] | +0.0 pts [+0.0, +0.0] |
| 2026-10-10 19:47:18 | 20261010-194615_validate-0020-tuning-of-mock-gate-anti-first | mock_gate_anti_first@92e58e | 149 | 93.2% | 800 | 89.5% [87.2%, 91.4%] | +0.2 pts [-1.8, +2.1] |
| 2026-10-10 19:47:18 | 20261010-194615_validate-0020-tuning-of-mock-gate-anti-first | mock_gate_anti_first@b77c11 | 151 | 93.2% | 800 | 89.9% [87.6%, 91.8%] | +0.6 pts [-1.4, +2.6] |
| 2026-10-10 19:47:18 | 20261010-194615_validate-0020-tuning-of-mock-gate-anti-first | mock_gate_anti_first@0c6cf9 | 209 | 93.2% | 800 | 88.2% [85.8%, 90.2%] | -1.1 pts [-3.2, +0.9] |
| 2026-10-10 19:47:18 | 20261010-194615_validate-0020-tuning-of-mock-gate-anti-first | mock_gate_anti_first@3aee36 | 242 | 93.5% | 800 | 88.9% [86.6%, 90.9%] | -0.4 pts [-2.3, +1.6] |
| 2026-10-10 19:47:18 | 20261010-194615_validate-0020-tuning-of-mock-gate-anti-first | mock_gate_anti_first@d61298 | 294 | 93.2% | 800 | 89.2% [86.9%, 91.2%] | -0.1 pts [-2.1, +1.9] |

## Analysis

300 TPE trials, thorough effort, anti expert mocked, mocks in the pools. The training winners agree (EDGE ~0.21, GATE_DECAY ~0.97-0.99, WARMUP 4-9), so the surface has a ridge there, but on fresh pools it is flat within +-2 pts of the defaults: once the gatekeeper starts on the anti expert, when exactly it switches matters little. Next: confirm the real twin (gate_anti_first: the Replay instead of the Oracle, defaults) vs replay_gate with mocks off.

## Verdict

**drop**. Tuning ANTI_FIRST finds nothing better than its defaults (EDGE 0.05, GATE_DECAY 1.0, WARMUP 10): the top 5 trials (93.2-93.5% in training) validate between -1.1 pts [-3.2, +0.9] and +0.6 pts [-1.4, +2.6] vs the defaults over 800 matches each; the training gain was overfitting. Defaults kept.
