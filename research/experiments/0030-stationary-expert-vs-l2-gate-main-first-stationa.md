# 0030: Stationary expert vs L2: gate_main_first_stationary vs gate_main_first

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #36
- **Candidates:** `bots/gate_main_first_stationary.yaml`
- **Baselines:** `bots/gate_main_first.yaml`
- **Run:** `20261010-233059_0030-stationary-expert-vs-l2-gate-main-first-stationa`
- **Verdict:** iterate

## Hypothesis

Check for degradation vs L2: the Oracle-arm screen predicts -3.9 pts [-7.8, -0.0] vs gate_main_first, lost to smartbot and meta_smartbot (the stationary expert takes the gate early and gets exploited); pass only if the paired difference's CI lower bound is above -3 pts.

## Command

```bash
uv run janken lab experiment bots/gate_main_first_stationary.yaml bots/gate_main_first.yaml --rounds 200 --round-robins 50 --pool-size 6 --seed 2130153524 --name 0030-stationary-expert-vs-l2-gate-main-first-stationa
```

## Results

50 of 50 round robin(s) · pool 6 · 200 rounds/match · seed 2130153524 · mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating ± sd |
|---|---|---|---|---|---|---|
| gate_main_first | 300 | 284-1-15 | 94.8% [91.7%, 96.8%] | +60.7 | 0 | 1817 ± 72 |
| gate_main_first_stationary | 300 | 278-2-20 | 93.0% [89.5%, 95.4%] | +57.9 | 0 | 1778 ± 84 |

Paired comparisons:

- `gate_main_first_stationary − gate_main_first = -1.8 pts [-5.2, +1.7]` over 300 shared matches: no significant difference

Weakest matchups of gate_main_first_stationary: meta_smartbot 64.0%, smart_staller 96.0%, smartbot 98.0%, rps4_lite 100.0%, staller 100.0%, iocaine_lite 100.0%.

Weakest matchups of gate_main_first: meta_smartbot 81.0%, smart_staller 92.0%, smartbot 96.0%, rps4_lite 100.0%, staller 100.0%, iocaine_lite 100.0%.

## Analysis

The stationary expert takes the gate from the main expert early vs meta_smartbot (fast decays 0.6/0.6: it looks stationary for a few rounds), then gets exploited, delaying the anti expert; LEADER_PRIORITY (only main or anti may take over from it) halved the mocked cost of plain LEADER (-4.7 to -6.2) but didn't remove it, and decayed gate records made it worse. Next options: a per-expert warm-up (the stationary expert needs more evidence, e.g. 30-50 rounds, before it can take the gate), or a stricter edge for it alone.

## Verdict

**iterate**. Vs L2 a small, not significant cost: gate_main_first_stationary - gate_main_first = -1.8 pts [-5.2, +1.7] over 300 paired matches (6 L2 bots, 50 round robins, no mocks), all of it vs meta_smartbot (64% vs 81% of matches); the Oracle-arm screen predicted -3.9 [-7.8, -0.0], the same place.
