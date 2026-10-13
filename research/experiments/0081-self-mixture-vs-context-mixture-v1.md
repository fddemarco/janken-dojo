# 0081: self_mixture vs context_mixture_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #63
- **Candidates:** `bots/l1/self_mixture.yaml`
- **Baselines:** `bots/l1/context_mixture_v1.yaml`
- **Run:** `20261013-163833_0081-self-mixture-vs-context-mixture-v1`
- **Verdict:** drop

## Hypothesis

CTW over the opponent's own sequence (depth 5) is a distinct L1 learner within 5 pts of context_mixture_v1 (CTW over the joint history) or better, in L1 pools of parameter variants (pool.variants 1.0, 250 rounds) (idea #63)

## Command

```bash
uv run janken lab experiment bots/l1/self_mixture.yaml bots/l1/context_mixture_v1.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode candidates --allow-small-pool --no-mocks --variants 1.0 --seed 2670867526 --name 0081-self-mixture-vs-context-mixture-v1
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 2670867526, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| context_mixture_v1 | 200 | 142-0-58 | 71.0% [64.4%, 76.8%] | +84.0 | 0 | 1710 +/- 81 |
| self_mixture | 200 | 120-0-80 | 60.0% [53.1%, 66.5%] | +49.4 | 0 | 1567 +/- 37 |

Paired comparisons:

- `self_mixture - context_mixture_v1 = -11.0 pts [-15.5, -6.5]` over 200 shared matches: context_mixture_v1 better

Weakest matchups of self_mixture: pattern_memory_v1 0.0%, geometry_v1 0.0%, markov2_joint_v1 0.0%, second_repeat_v1 0.0%, transition_matrix_v1 0.0%, pretrained_context_v3 10.0%.

Weakest matchups of context_mixture_v1: pattern_memory_v1 0.0%, geometry_v1 0.0%, markov2_joint_v1 0.0%, nash_v1 30.0%, period_detector_v1 33.3%, transition_matrix_v1 33.3%.

## Analysis

It loses every match to the strong learners (pattern_memory, geometry, markov2_joint, second_repeat, transition_matrix) and 90% to pretrained_context_v3: the information is in how the opponent answers us, which a model of their sequence alone can't see, deeper or not. Same lesson as response_markov (note 0070, our moves alone): the joint history carries what one side's sequence doesn't.

## Verdict

**drop**. Reading the opponent's own sequence alone is weaker than the joint history: self_mixture (CTW over their moves, depth 5) - context_mixture_v1 (CTW over the joint history, depth 3) = -11.0 pts [-15.5, -6.5] over 200 paired matches in L1 pools of parameter variants (250 rounds); 60.0% of matches vs 71.0%.
