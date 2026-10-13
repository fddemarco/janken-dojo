# 0070: response_markov vs markov2_joint_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #63
- **Candidates:** `bots/l1/response_markov.yaml`
- **Baselines:** `bots/l1/markov2_joint_v1.yaml`
- **Run:** `20261013-153941_0070-response-markov-vs-markov2-joint-v1`
- **Verdict:** drop

## Hypothesis

response_markov (the opponent's next move given our last two moves: how they respond to us) is a distinct L1 learner: in an L1-only pool it scores within 5 pts of markov2_joint_v1 or better, with core agreement under 70% with every L1 (idea #63)

## Command

```bash
uv run janken lab experiment bots/l1/response_markov.yaml bots/l1/markov2_joint_v1.yaml --rounds 250 --round-robins 10 --pool-size 19 --mode candidates --allow-small-pool --no-mocks --seed 4128709669 --name 0070-response-markov-vs-markov2-joint-v1
```

## Results

10 of 10 round robin(s), pool 19, 250 rounds/match, seed 4128709669, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| markov2_joint_v1 | 190 | 147-0-43 | 77.4% [70.9%, 82.7%] | +103.2 | 0 | 1753 +/- 50 |
| response_markov | 190 | 123-1-66 | 65.0% [58.0%, 71.4%] | +83.1 | 0 | 1624 +/- 75 |

Paired comparisons:

- `response_markov - markov2_joint_v1 = -12.4 pts [-18.4, -6.3]` over 190 shared matches: markov2_joint_v1 better

Weakest matchups of response_markov: period_detector_v1 0.0%, pattern_memory_v1 0.0%, geometry_v1 0.0%, anti_frequency_v1 20.0%, transition_matrix_v1 30.0%, second_repeat_v1 40.0%.

Weakest matchups of markov2_joint_v1: pattern_memory_v1 0.0%, geometry_v1 20.0%, second_repeat_v1 30.0%, period_detector_v1 30.0%, nash_v1 30.0%, transition_matrix_v1 60.0%.

## Analysis

It loses every match to the strong set (pattern_memory, geometry) and to period_detector: a model of their reply to our moves alone misses the structure the joint history carries. Its sibling reaction_outcome (Relative with ref MY, by outcome) was never evaluated: it agrees 100% with rotation_outcome_v1, since once the last outcome is known our last move and theirs determine each other, so a rotation model conditioned on the outcome is the same from either reference.

## Verdict

**drop**. A distinct but weaker L1: response_markov (the opponent's next move given our last two moves) - markov2_joint_v1 = -12.4 pts [-18.4, -6.3] over 190 paired matches in an L1-only pool (250 rounds); 65.0% of matches vs 77.4%, core agreement 67% with markov2_joint.
