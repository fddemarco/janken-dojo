# 0073: pretrained_context vs context_mixture_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #72
- **Candidates:** `bots/l1/pretrained_context.yaml`
- **Baselines:** `bots/l1/context_mixture_v1.yaml`
- **Run:** `20261013-155311_0073-pretrained-context-vs-context-mixture-v1`
- **Verdict:** keep
- **Species:** `pretrained_context_v1` (new species)

## Hypothesis

Confirmation on fresh seeds at the thorough budget: pretrained_context beats context_mixture_v1 by >= 2 pts in L1 pools of parameter variants (first run: +6.8 pts [+1.8, +12.0])

## Command

```bash
uv run janken lab experiment bots/l1/pretrained_context.yaml bots/l1/context_mixture_v1.yaml --rounds 250 --round-robins 16 --pool-size 20 --mode candidates --allow-small-pool --no-mocks --variants 1.0 --seed 1384431091 --name 0073-pretrained-context-vs-context-mixture-v1
```

## Results

16 of 16 round robin(s), pool 20, 250 rounds/match, seed 1384431091, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| pretrained_context | 320 | 258-3-59 | 81.1% [76.4%, 85.0%] | +75.6 | 0 | 1759 +/- 44 |
| context_mixture_v1 | 320 | 228-0-92 | 71.2% [66.1%, 75.9%] | +85.2 | 0 | 1710 +/- 37 |

Paired comparisons:

- `pretrained_context - context_mixture_v1 = +9.8 pts [+5.6, +14.4]` over 320 shared matches: pretrained_context better

Weakest matchups of pretrained_context: markov2_joint_v1 3.1%, second_repeat_v1 28.1%, pattern_memory_v1 31.2%, geometry_v1 37.5%, nash_v1 71.9%, period_detector_v1 75.0%.

Weakest matchups of context_mixture_v1: pattern_memory_v1 0.0%, geometry_v1 0.0%, markov2_joint_v1 0.0%, period_detector_v1 12.5%, transition_matrix_v1 31.2%, nash_v1 31.2%.

## Analysis

The arena probe predicted it (+6.6 pts of net rounds for the prior over the same table online-only). The prior was trained on default-parameter matches and judged against variants, so the gain is generalisation, not memory; its 64.5% core agreement with pattern_memory, the closest L1, makes it a new species. New stage kind PriorTable (janken/kit/signals.py): the prior lives in the knobs, so export inlines it.

## Verdict

**keep**. Confirmed on fresh seeds at the thorough budget: pretrained_context - context_mixture_v1 = +9.8 pts [+5.6, +14.4] over 320 paired matches in L1 pools of parameter variants (16 round robins, cleared at look 2), 81.1% of matches vs 71.2%. The first pre-trained species: a dataset prior over how the field plays, carried as data in the bot (an 18 KB block; a 74 KB export).

## Species

**new**: its core agrees with pattern_memory_v1 on 64% of the moves, below 80%.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `pattern_memory_v1` | L1 | 64.5% |
| `rotation_outcome_v1` | L1 | 61.8% |
| `markov2_joint_v1` | L1 | 61.4% |
| `context_mixture_v1` | L1 | 60.8% |
| `second_repeat_v1` | L1 | 57.3% |
