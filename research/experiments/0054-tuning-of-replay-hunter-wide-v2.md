# 0054: tuning of replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** tuning
- **Idea:** #58
- **Candidates:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Baselines:** -
- **Study:** `0054-tuning-of-replay-hunter-wide-v2`
- **Verdict:** drop

## Hypothesis

A tuned gate (EDGE in [0, 0.3], GATE_DECAY in [0.8, 1], WARMUP in [0, 30]) beats replay_hunter_wide_v2's defaults (EDGE 0, GATE_DECAY 1, WARMUP 10) by >= 2 pts on fresh validation pools: the gate decides every round which expert plays, so its knobs move every matchup

## Command

```bash
uv run janken lab study run spaces/replay_hunter_wide_v2.yaml --study 0054-tuning-of-replay-hunter-wide-v2 --rounds 200 --round-robins 5 --pool-size 20 --seed 0
```

## Results

Validations of study 0054-tuning-of-replay-hunter-wide-v2:

| validated | run | champion | trial | train | n | score vs pool [95% CI] | vs defaults [95% CI] |
|---|---|---|---|---|---|---|---|
| 2026-10-13 13:43:47 | 20261013-133949_validate-0054-tuning-of-replay-hunter-wide-v2 | replay_hunter_wide_v2 | -1 | 86.5% | 200 | 86.2% [80.8%, 90.3%] | +0.0 pts [+0.0, +0.0] |
| 2026-10-13 13:43:47 | 20261013-133949_validate-0054-tuning-of-replay-hunter-wide-v2 | replay_hunter_wide_v2@d57b91 | 3 | 88.0% | 200 | 77.5% [71.2%, 82.7%] | -8.8 pts [-15.8, -2.0] |
| 2026-10-13 13:43:47 | 20261013-133949_validate-0054-tuning-of-replay-hunter-wide-v2 | replay_hunter_wide_v2@8593f5 | 23 | 91.0% | 200 | 85.0% [79.4%, 89.3%] | -1.2 pts [-7.2, +4.8] |
| 2026-10-13 13:43:47 | 20261013-133949_validate-0054-tuning-of-replay-hunter-wide-v2 | replay_hunter_wide_v2@3a8576 | 31 | 93.0% | 200 | 85.5% [80.0%, 89.7%] | -0.8 pts [-6.5, +4.8] |
| 2026-10-13 13:43:47 | 20261013-133949_validate-0054-tuning-of-replay-hunter-wide-v2 | replay_hunter_wide_v2@f583a0 | 68 | 90.0% | 200 | 85.5% [80.0%, 89.7%] | -0.8 pts [-6.2, +4.8] |
| 2026-10-13 13:43:47 | 20261013-133949_validate-0054-tuning-of-replay-hunter-wide-v2 | replay_hunter_wide_v2@3ba5f0 | 73 | 90.0% | 200 | 89.2% [84.2%, 92.8%] | +3.0 pts [-3.0, +9.0] |

## Analysis

100 TPE trials x 5 pools: the best training scores (88-93%) fell to 77.5-89.2% on validation, the usual overfit to training pools. Every trial that trained well kept the gate nearly as is (EDGE under 0.07, GATE_DECAY above 0.96, WARMUP 2-8); the one that moved it (a 0.29 edge and a forgetting gate) lost 8.8 pts: a demanding, forgetful gate hands rounds back to the main bandit that the replays would win. So the LEADER gate's knobs are not where replay_hunter_wide's remaining points are; they are in its experts (the samplers and adaptive gates it scores near 0 against, note 0051's weakest matchups).

## Verdict

**drop**. No tuned gate beats replay_hunter_wide_v2's defaults on fresh pools (validation, 10 round robins, 200 paired matches each): the best, trial 73 (EDGE 0.003, GATE_DECAY 0.994, WARMUP 5), +3.0 pts [-3.0, +9.0]; trials 23, 31, 68 (all near the defaults) -0.8 to -1.2 pts; trial 3 (EDGE 0.291, GATE_DECAY 0.888) -8.8 pts [-15.8, -2.0], significantly worse. The defaults (EDGE 0, GATE_DECAY 1, WARMUP 10) sit at the optimum's plateau.
