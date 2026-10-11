# 0007: agamemnon-v2

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** tuning
- **Idea:** —
- **Candidates:** `agamemnon`
- **Baselines:** —
- **Study:** `0007-agamemnon-v2`
- **Verdict:** drop

## Hypothesis

defaults are not optimal

## Command

```bash
uv run janken lab study run spaces/agamemnon.yaml --study 0007-agamemnon-v2 --rounds 250 --round-robins 1 --pool-size 20 --seed 0
```

## Results

Validations of study 0007-agamemnon-v2:

| validated | run | champion | trial | train | n | score vs pool [95% CI] | vs defaults [95% CI] |
|---|---|---|---|---|---|---|---|
| 2026-10-10 15:55:09 | 20261010-155453_validate-0007-agamemnon-v2 | agamemnon | -1 | 80.0% | 200 | 86.8% [81.4%, 90.8%] | +0.0 pts [+0.0, +0.0] |
| 2026-10-10 15:55:09 | 20261010-155453_validate-0007-agamemnon-v2 | agamemnon@e68f92 | 3 | 95.0% | 200 | 82.8% [76.9%, 87.4%] | -4.0 pts [-10.0, +2.0] |
| 2026-10-10 15:55:09 | 20261010-155453_validate-0007-agamemnon-v2 | agamemnon@19c6a3 | 16 | 100.0% | 200 | 84.8% [79.1%, 89.1%] | -2.0 pts [-7.0, +3.2] |
| 2026-10-10 15:55:09 | 20261010-155453_validate-0007-agamemnon-v2 | agamemnon@441e99 | 22 | 100.0% | 200 | 80.2% [74.2%, 85.2%] | -6.5 pts [-12.0, -0.8] |
| 2026-10-10 15:55:09 | 20261010-155453_validate-0007-agamemnon-v2 | agamemnon@3d2c00 | 49 | 100.0% | 200 | 84.2% [78.6%, 88.6%] | -2.5 pts [-8.2, +3.2] |
| 2026-10-10 15:55:09 | 20261010-155453_validate-0007-agamemnon-v2 | agamemnon@9d63dc | 96 | 100.0% | 200 | 86.2% [80.8%, 90.3%] | -0.5 pts [-5.5, +4.8] |

## Analysis

With one 20-bot pool per trial the training objective saturates: five of the six top trials scored 100% in training, so TPE had no signal to rank them and the 'best' trials are noise. Validation on 200 fresh matches puts every one of them at or below the defaults (86.8%), one significantly worse. The study design, not the space, is the problem; 0008 reruns it with 10 round robins per trial.

## Verdict

**drop**. Tuning agamemnon's ARM_DECAY/TABLE_DECAY/MAX_MATCH with 1 round robin per trial found nothing: none of the 6 validated configs beats the defaults (best -0.5 pts [-5.5, +4.8]; worst @441e99 -6.5 pts [-12.0, -0.8]). Superseded by 0008, which repeats the study with 10 round robins per trial.
