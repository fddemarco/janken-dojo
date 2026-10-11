# 0022: arm_gate_anti_first vs gate_anti_first (per-level Oracle arm validation)

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** —
- **Candidates:** `bots/arm_gate_anti_first.yaml`
- **Baselines:** `bots/gate_anti_first.yaml`
- **Run:** `20261010-204355_0022-arm-gate-anti-first-vs-gate-anti-first-per-level`
- **Verdict:** keep

## Hypothesis

After the cleanup (27 regular bots; L3: advanced_bot, anti_advanced_bots; L4: replay_gate, gate_anti_first), the ANTI_FIRST gatekeeper with its anti expert as a per-level Oracle arm (win 0.337 / 0.406 / 0.415 / 0.368 vs L1-L4, calibrated 2026-10-11) plays like the real one: paired difference within +-3 pts with a CI covering 0. New field: not comparable with 0016-0021. Expected gap: vs anti_advanced_bots and replay_gate (L3/L4 opponents that read or mirror it) the arm's i.i.d. outcomes may differ from the real replay's.

## Command

```bash
uv run janken lab experiment bots/arm_gate_anti_first.yaml bots/gate_anti_first.yaml --rounds 200 --round-robins 10 --pool-size 20 --seed 1534642689 --name 0022-arm-gate-anti-first-vs-gate-anti-first-per-level
```

## Results

10 of 10 round robin(s) · pool 20 · 200 rounds/match · seed 1534642689 · mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating ± sd |
|---|---|---|---|---|---|---|
| arm_gate_anti_first | 200 | 189-0-11 | 94.5% [90.4%, 96.9%] | +89.4 | 0 | 1912 ± 42 |
| gate_anti_first | 200 | 181-1-18 | 90.8% [85.9%, 94.0%] | +88.1 | 0 | 1851 ± 78 |

Paired comparisons:

- `arm_gate_anti_first − gate_anti_first = +3.8 pts [-0.8, +8.5]` over 200 shared matches: no significant difference

Weakest matchups of arm_gate_anti_first: transition_matrix 62.5%, geometry 66.7%, replay_gate 71.4%, advanced_bot 85.7%, biased 87.5%, smartbot 88.9%.

Weakest matchups of gate_anti_first: geometry 27.8%, transition_matrix 62.5%, biased 62.5%, anti_advanced_bots 75.0%, nash 83.3%, meta_smartbot 85.7%.

## Analysis

The arm wins like anti_advanced_bots per opponent level (0.337 / 0.406 / 0.415 / 0.368 vs L1-L4, janken lab calibrate, 16 seeds). The biggest gap is geometry (L1): 66.7% of matches for the arm vs 27.8% for the real bot. The real replay seems to lose more than the L1 mean vs geometry's sampled moves, and per-level odds can't see that (the per-opponent calibration measured anti at 34.6% wins vs geometry). Other gaps: biased 87.5% vs 62.5%, anti_advanced_bots (real gate 75.0%). Rounds margins match (+89.4 vs +88.1). Cost: 269.6 s, all of it from the real gate_anti_first.

## Verdict

**keep**. The per-level Oracle arm stands in for the real anti expert within noise: arm_gate_anti_first scores 94.5% vs gate_anti_first's 90.8%, +3.8 pts [-0.8, +8.5] over 200 paired matches (first run on the cleaned field: 27 regular bots, not comparable with 0016-0021). It leans optimistic, so a mocked gain under ~4 pts needs a real confirmation.
