# 0079: pretrained_wide vs pretrained_context_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #72
- **Candidates:** `bots/l1/pretrained_wide.yaml`
- **Baselines:** `bots/l1/pretrained_context_v2.yaml`
- **Run:** `20261013-162134_0079-pretrained-wide-vs-pretrained-context-v2`
- **Verdict:** drop

## Hypothesis

A prior trained on L1-L4 matches beats the one trained on L1-L2 (pretrained_context_v2, same weight 1) by >= 2 pts vs pools of parameter variants of the whole field (pool.variants 1.0, 250 rounds): the prior has now seen the levels above L2 (insight of 2026-10-13)

## Command

```bash
uv run janken lab experiment bots/l1/pretrained_wide.yaml bots/l1/pretrained_context_v2.yaml --rounds 250 --round-robins 8 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --variants 1.0 --seed 1195836050 --name 0079-pretrained-wide-vs-pretrained-context-v2
```

## Results

8 of 8 round robin(s), pool 20, 250 rounds/match, seed 1195836050, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| pretrained_context_v2 | 160 | 85-2-73 | 53.8% [46.0%, 61.3%] | +26.5 | 0 | 1517 +/- 64 |
| pretrained_wide | 160 | 84-3-73 | 53.4% [45.7%, 61.0%] | +25.6 | 0 | 1548 +/- 54 |

Paired comparisons:

- `pretrained_wide - pretrained_context_v2 = -0.3 pts [-8.1, +7.8]` over 160 shared matches: no significant difference

Weakest matchups of pretrained_wide: pattern_memory_v1 0.0%, repeat_mirror_v1 0.0%, dropswitch_matcher_v1 0.0%, markov2_joint_v1 0.0%, double_bluff_gate_v2 0.0%, sicilian_meta_v1 0.0%.

Weakest matchups of pretrained_context_v2: rps4_lite_v1 0.0%, smartbot_sims_v2 0.0%, predator_v2 0.0%, level_k_gate_v2 0.0%, l5_wide_hunter 0.0%, second_guess_v1 0.0%.

## Analysis

With a prior worth one observation per context, the match's own counts dominate after a few occurrences of each context, so what the prior was trained on matters little; and an L3/L4 bot's next move is less predictable from the last three joint moves than an L1/L2's. The implication of the insight of 2026-10-13 (train on the widest data) doesn't hold at this weight: the weight was the lever, not the data's breadth.

## Verdict

**drop**. Wider training data adds nothing measurable: pretrained_wide (the context table trained on L1-L4 matches, 3513 matches, prior worth 1) - pretrained_context_v2 (trained on L1-L2) = -0.3 pts [-8.1, +7.8] over 160 paired matches vs pools of parameter variants of the whole field (thorough budget, futile at look 1).
