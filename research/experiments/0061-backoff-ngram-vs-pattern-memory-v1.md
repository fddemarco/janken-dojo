# 0061: backoff_ngram vs pattern_memory_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #63
- **Candidates:** `bots/l1/backoff_ngram.yaml`
- **Baselines:** `bots/l1/pattern_memory_v1.yaml`
- **Run:** `20261013-141620_0061-backoff-ngram-vs-pattern-memory-v1`
- **Verdict:** drop

## Hypothesis

backoff_ngram (a variable-order n-gram over the joint history) scores within 5 pts of pattern_memory_v1, the top L1, in an L1-only pool (idea #63)

## Command

```bash
uv run janken lab experiment bots/l1/backoff_ngram.yaml bots/l1/pattern_memory_v1.yaml --rounds 250 --round-robins 10 --pool-size 19 --mode candidates --allow-small-pool --no-mocks --seed 800974852 --name 0061-backoff-ngram-vs-pattern-memory-v1
```

## Results

10 of 10 round robin(s), pool 19, 250 rounds/match, seed 800974852, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| pattern_memory_v1 | 190 | 164-1-25 | 86.6% [81.0%, 90.7%] | +111.5 | 0 | 1849 +/- 63 |
| backoff_ngram | 190 | 157-1-32 | 82.9% [76.9%, 87.6%] | +123.9 | 0 | 1769 +/- 60 |

Paired comparisons:

- `backoff_ngram - pattern_memory_v1 = -3.7 pts [-9.7, +2.4]` over 190 shared matches: no significant difference

Weakest matchups of backoff_ngram: geometry_v1 20.0%, transition_matrix_v1 40.0%, nash_v1 45.0%, period_detector_v1 60.0%, markov2_joint_v1 60.0%, second_repeat 60.0%.

Weakest matchups of pattern_memory_v1: second_repeat 30.0%, geometry_v1 30.0%, nash_v1 60.0%, period_detector_v1 70.0%, biased_v1 75.0%, transition_matrix_v1 80.0%.

## Analysis

It wins more rounds per match (+123.9 vs +111.5) but fewer matches (82.9% vs 86.6%), and loses to geometry_v1 (20% of matches), which pattern_memory ties. A variant of pattern_memory's idea, not a new family; out of the field.

## Verdict

**drop**. No gain and no diversity: backoff_ngram - pattern_memory_v1 = -3.7 pts [-9.7, +2.4] over 190 paired matches in an L1-only pool (250 rounds), and its core agrees 83% with pattern_memory_v1: a variable-order n-gram on the joint history mostly names the move the longest repeat names.
