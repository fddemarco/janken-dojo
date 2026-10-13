# 0071: context_mixture vs pattern_memory_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #68
- **Candidates:** `bots/l1/context_mixture.yaml`
- **Baselines:** `bots/l1/pattern_memory_v1.yaml`
- **Run:** `20261013-154436_0071-context-mixture-vs-pattern-memory-v1`
- **Verdict:** keep
- **Species:** `context_mixture_v1` (new species)

## Hypothesis

Context-tree weighting (context_mixture, a Bayesian mixture of every joint context up to 3 moves) is a strong L1 learner: in an L1-only pool it scores within 5 pts of pattern_memory_v1, the top L1, or better (idea #68)

## Command

```bash
uv run janken lab experiment bots/l1/context_mixture.yaml bots/l1/pattern_memory_v1.yaml --rounds 250 --round-robins 10 --pool-size 19 --mode candidates --allow-small-pool --no-mocks --seed 389912996 --name 0071-context-mixture-vs-pattern-memory-v1
```

## Results

10 of 10 round robin(s), pool 19, 250 rounds/match, seed 389912996, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| pattern_memory_v1 | 190 | 164-1-25 | 86.6% [81.0%, 90.7%] | +112.4 | 0 | 1849 +/- 55 |
| context_mixture | 190 | 155-1-34 | 81.8% [75.7%, 86.7%] | +121.1 | 0 | 1760 +/- 50 |

Paired comparisons:

- `context_mixture - pattern_memory_v1 = -4.7 pts [-10.5, +0.8]` over 190 shared matches: no significant difference

Weakest matchups of context_mixture: geometry_v1 0.0%, transition_matrix_v1 10.0%, second_repeat_v1 50.0%, period_detector_v1 60.0%, nash_v1 65.0%, markov2_joint_v1 70.0%.

Weakest matchups of pattern_memory_v1: period_detector_v1 40.0%, nash_v1 40.0%, second_repeat_v1 45.0%, geometry_v1 60.0%, transition_matrix_v1 60.0%, biased_v1 100.0%.

## Analysis

Its weakest matchups: geometry_v1 (0% of matches) and transition_matrix_v1 (10%), the two learners that model a different structure (geometry's offsets, the opponent's own transitions); vs the repeat followers it is level (second_repeat 50%). It wins its matches by wider margins than any L1, as a full mixture should vs structured prey, but its expected-probability choice (first maximum of the mixture) is deterministic, so a mirror counter (CTW on our moves, BEAT_BEAT) would beat it as for the repeat followers (note 0062). New stage kind CTW (janken/kit/signals.py), with a block, unit tests and export.

## Verdict

**keep**. A new L1 learner of the strong tier: context_mixture (context-tree weighting over the joint history, depth 3) - pattern_memory_v1 = -4.7 pts [-10.5, +0.8] over 190 paired matches in an L1-only pool (250 rounds), no significant difference; 81.8% of matches and the most rounds per match of any L1 (+121.1 vs +112.4). Core agreement 74.5% with pattern_memory: a new mechanism (a Bayesian mixture of context lengths), kept for diversity as the research direction's diversify phase asks.

## Species

**new**: its core agrees with pattern_memory_v1 on 74% of the moves, below 80%.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `pattern_memory_v1` | L1 | 74.5% |
| `markov2_joint_v1` | L1 | 72.1% |
| `rotation_outcome_v1` | L1 | 69.9% |
| `second_repeat_v1` | L1 | 67.2% |
| `period_detector_v1` | L1 | 60.9% |
