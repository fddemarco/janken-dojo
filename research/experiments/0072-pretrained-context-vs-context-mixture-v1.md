# 0072: pretrained_context vs context_mixture_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #72
- **Candidates:** `bots/l1/pretrained_context.yaml`
- **Baselines:** `bots/l1/context_mixture_v1.yaml`
- **Run:** `20261013-155257_0072-pretrained-context-vs-context-mixture-v1`
- **Verdict:** keep

## Hypothesis

A pre-trained prior generalises: pretrained_context (a k=3 joint-context table trained on the move dataset, worth 5 observations per context) scores within 5 pts of context_mixture_v1 or better in an L1 pool whose every member plays a parameter variant it never trained on (pool.variants 1.0, 250 rounds; arena probe: +6.6 pts of net rounds over the same table online-only) (idea #72)

## Command

```bash
uv run janken lab experiment bots/l1/pretrained_context.yaml bots/l1/context_mixture_v1.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode candidates --allow-small-pool --no-mocks --variants 1.0 --seed 3168410998 --name 0072-pretrained-context-vs-context-mixture-v1
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 3168410998, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| pretrained_context | 200 | 156-1-43 | 78.2% [72.0%, 83.4%] | +77.2 | 0 | 1731 +/- 54 |
| context_mixture_v1 | 200 | 141-4-55 | 71.5% [64.9%, 77.3%] | +88.1 | 0 | 1715 +/- 30 |

Paired comparisons:

- `pretrained_context - context_mixture_v1 = +6.8 pts [+1.8, +12.0]` over 200 shared matches: pretrained_context better

Weakest matchups of pretrained_context: pattern_memory_v1 0.0%, geometry_v1 20.0%, markov2_joint_v1 30.0%, nash_v1 35.0%, second_repeat_v1 50.0%, period_detector_v1 50.0%.

Weakest matchups of context_mixture_v1: pattern_memory_v1 0.0%, markov2_joint_v1 0.0%, period_detector_v1 5.0%, transition_matrix_v1 15.0%, geometry_v1 20.0%, nash_v1 30.0%.

## Analysis

78.2% of matches vs 71.5%, but fewer rounds per match (+77.2 vs +88.1): the prior wins more matches by naming the field's habits from the first rounds, and the online mixture wins its matches wider once it has learned. Weakest matchups: pattern_memory_v1 (0%), geometry_v1 (20%), markov2_joint_v1 (30%): the strong learners, which a context table of 3 moves doesn't out-predict.

## Verdict

**keep**. A pre-trained table generalises to parameters it never saw: pretrained_context (a k=3 joint-context table trained on the move dataset's default-parameter matches, worth 5 observations per context, refined online) - context_mixture_v1 = +6.8 pts [+1.8, +12.0] over 200 paired matches in L1 pools whose every member plays a parameter variant (pool.variants 1.0, 250 rounds); confirmed on fresh seeds in note 0073.
