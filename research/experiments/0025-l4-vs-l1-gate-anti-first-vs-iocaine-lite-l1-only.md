# 0025: L4 vs L1: gate_anti_first vs iocaine_lite (L1-only pool)

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** —
- **Candidates:** `bots/gate_anti_first.yaml`
- **Baselines:** `bots/iocaine_lite.yaml`
- **Run:** `20261010-213919_0025-l4-vs-l1-gate-anti-first-vs-iocaine-lite-l1-only`
- **Verdict:** iterate

## Hypothesis

The real L4 gate_anti_first is at least as good as the best L2 vs L1 opponents: vs iocaine_lite over 680 paired matches against the 17 L1 bots (40 round robins), paired difference >= -2 pts with the CI's lower bound above -3 pts (non-inferiority), point estimate near 0 (sweeps: -1.1 [-4.8, +2.6] real, -0.7 [-3.3, +1.8] arm).

## Command

```bash
uv run janken lab experiment bots/gate_anti_first.yaml bots/iocaine_lite.yaml --rounds 200 --round-robins 40 --pool-size 17 --seed 2457783218 --name 0025-l4-vs-l1-gate-anti-first-vs-iocaine-lite-l1-only
```

## Results

40 of 40 round robin(s) · pool 17 · 200 rounds/match · seed 2457783218 · mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating ± sd |
|---|---|---|---|---|---|---|
| iocaine_lite | 680 | 623-2-55 | 91.8% [89.5%, 93.6%] | +103.2 | 0 | 1839 ± 39 |
| gate_anti_first | 680 | 610-7-63 | 90.2% [87.8%, 92.2%] | +108.7 | 0 | 1877 ± 55 |

Paired comparisons:

- `gate_anti_first − iocaine_lite = -1.5 pts [-3.8, +0.8]` over 680 shared matches: no significant difference

Weakest matchups of gate_anti_first: nash 33.8%, geometry 61.3%, transition_matrix 62.5%, biased 78.8%, rotation_outcome 97.5%, markov2_joint 100.0%.

Weakest matchups of iocaine_lite: geometry 45.0%, transition_matrix 57.5%, nash 57.5%, rotation_outcome 100.0%, biased 100.0%, markov2_joint 100.0%.

## Analysis

The deficit is two opponents: nash 33.8% vs 57.5% (uniform random: pure noise, nobody beats it in expectation; 1.4 pts of the gap) and biased 78.8% vs 100% (a weighted coin the advanced arms should always beat). Hypothesis for biased: ANTI_FIRST returns to the anti expert (chance vs L1) whenever the main expert's Thompson-sampled lead dips under the edge. Next: the ANTI_FIRST_HOLD rule (hysteresis: once on the main expert, stay until the gated arm leads by the edge), screened with the Oracle arm, then this comparison again with the real L4. geometry: 61.3% vs 45.0%, transition_matrix 62.5% vs 57.5% (the L4 better).

## Verdict

**iterate**. Vs L1 the real L4 is just short of the best L2: gate_anti_first - iocaine_lite = -1.5 pts [-3.8, +0.8] over 680 paired matches against the 17 L1 bots (40 round robins, L1-only pool, no mocks): 90.2% vs 91.8%, but a larger margin (+108.7 vs +103.2 rounds per match).
