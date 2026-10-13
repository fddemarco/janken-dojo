# 0060: second_repeat vs markov2_joint_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #63
- **Candidates:** `bots/l1/second_repeat.yaml`
- **Baselines:** `bots/l1/markov2_joint_v1.yaml`
- **Run:** `20261013-141615_0060-second-repeat-vs-markov2-joint-v1`
- **Verdict:** keep
- **Species:** `second_repeat_v1` (new species)

## Hypothesis

second_repeat (follow the second-longest repeat) is a distinct L1 learner: in an L1-only pool it scores in the learner tier, no worse than markov2_joint_v1 by more than 5 pts, with core agreement under 70% with every L1 (idea #63)

## Command

```bash
uv run janken lab experiment bots/l1/second_repeat.yaml bots/l1/markov2_joint_v1.yaml --rounds 250 --round-robins 10 --pool-size 19 --mode candidates --allow-small-pool --no-mocks --seed 986847446 --name 0060-second-repeat-vs-markov2-joint-v1
```

## Results

10 of 10 round robin(s), pool 19, 250 rounds/match, seed 986847446, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| second_repeat | 190 | 154-1-35 | 81.3% [75.2%, 86.2%] | +106.2 | 0 | 1788 +/- 73 |
| markov2_joint_v1 | 190 | 141-3-46 | 75.0% [68.4%, 80.6%] | +101.9 | 0 | 1713 +/- 51 |

Paired comparisons:

- `second_repeat - markov2_joint_v1 = +6.3 pts [+0.3, +12.9]` over 190 shared matches: second_repeat better

Weakest matchups of second_repeat: pattern_memory_v1 40.0%, backoff_ngram 40.0%, period_detector_v1 40.0%, transition_matrix_v1 50.0%, geometry_v1 50.0%, nash_v1 60.0%.

Weakest matchups of markov2_joint_v1: pattern_memory_v1 0.0%, geometry_v1 10.0%, backoff_ngram 15.0%, nash_v1 30.0%, period_detector_v1 30.0%, transition_matrix_v1 60.0%.

## Analysis

Weakest matchups: pattern_memory_v1, backoff_ngram and period_detector_v1 (40% of matches), transition_matrix_v1 and geometry_v1 (50%): the strong set still beats or ties it, as the theory's claim of a small strong set predicts. Rounds +106.2 per match vs markov2's +101.9. Next: classify (a new species), and add it to the L1 atlas.

## Verdict

**keep**. A new L1 learner: second_repeat - markov2_joint_v1 = +6.3 pts [+0.3, +12.9] over 190 paired matches in an L1-only pool (10 round robins, 250 rounds), 81.3% of matches vs 75.0%; its core agrees at most 68% with any L1 (markov2_joint), so it adds a strategy the level lacked: following the second-longest repeat, which predicts an opponent that dodges the longest.

## Species

**new**: its core agrees with markov2_joint_v1 on 68% of the moves, below 80%.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `markov2_joint_v1` | L1 | 67.8% |
| `rotation_outcome_v1` | L1 | 65.2% |
| `pattern_memory_v1` | L1 | 60.6% |
| `period_detector_v1` | L1 | 56.6% |
| `transition_matrix_v1` | L1 | 56.0% |
