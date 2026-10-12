# 0027: L4 vs L1: gate_main_first vs iocaine_lite (L1-only pool)

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #35
- **Candidates:** `bots/gate_main_first.yaml`
- **Baselines:** `bots/iocaine_lite.yaml`
- **Run:** `20261010-222411_0027-l4-vs-l1-gate-main-first-vs-iocaine-lite-l1-only`
- **Verdict:** keep

## Hypothesis

The real MAIN_FIRST L4 is at least as good as the best L2 vs L1: gate_main_first - iocaine_lite over 680 paired matches vs the 17 L1 bots, point estimate >= 0 and CI lower bound above -3 pts (non-inferiority); Oracle-arm screen: +0.4 [-2.2, +2.9]; ANTI_FIRST was -1.5 [-3.8, +0.8] (0025), losing biased.

## Command

```bash
uv run janken lab experiment bots/gate_main_first.yaml bots/iocaine_lite.yaml --rounds 200 --round-robins 40 --pool-size 17 --seed 3354815560 --name 0027-l4-vs-l1-gate-main-first-vs-iocaine-lite-l1-only
```

## Results

40 of 40 round robin(s), pool 17, 200 rounds/match, seed 3354815560, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| gate_main_first | 680 | 614-7-59 | 90.8% [88.4%, 92.8%] | +110.2 | 0 | 1882 +/- 50 |
| iocaine_lite | 680 | 614-5-61 | 90.7% [88.2%, 92.6%] | +103.6 | 0 | 1830 +/- 40 |

Paired comparisons:

- `gate_main_first - iocaine_lite = +0.1 pts [-2.2, +2.5]` over 680 shared matches: no significant difference

Weakest matchups of gate_main_first: nash 48.8%, geometry 58.8%, transition_matrix 63.7%, biased 75.0%, rotation_outcome 97.5%, markov2_joint 100.0%.

Weakest matchups of iocaine_lite: transition_matrix 33.8%, geometry 46.2%, nash 61.3%, biased 100.0%, rotation_outcome 100.0%, markov2_joint 100.0%.

## Analysis

MAIN_FIRST plays advanced_bot's arms from round 1, so vs L1 the anti expert (chance there) is never played and nothing is lost to the gate: biased 75.0% (ANTI_FIRST 78.8%, iocaine 100%), geometry 58.8% (iocaine 46.2%), transition_matrix 63.7% (iocaine 33.8%), nash 48.8% (iocaine 61.3%, noise). It trades iocaine's sure win vs biased (Thompson over ~90 arms explores where iocaine's greedy 9 arms exploit) for wins over geometry and transition_matrix.

## Verdict

**keep**. The real L4 gate_main_first matches the best L2 vs L1: gate_main_first - iocaine_lite = +0.1 pts [-2.2, +2.5] over 680 paired matches vs the 17 L1 bots (40 round robins, L1-only pool, no mocks): 90.8% vs 90.7%, margin +110.2 vs +103.6 rounds per match; the CI's lower bound clears a -3 pt non-inferiority margin, where ANTI_FIRST (0025) did not (-1.5 [-3.8, +0.8]).
