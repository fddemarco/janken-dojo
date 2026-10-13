# 0080: pretrained_deep vs pretrained_context_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #72
- **Candidates:** `bots/l1/pretrained_deep.yaml`
- **Baselines:** `bots/l1/pretrained_context_v2.yaml`
- **Run:** `20261013-162753_0080-pretrained-deep-vs-pretrained-context-v2`
- **Verdict:** keep
- **Species:** `pretrained_context_v3` (promoted over `pretrained_context_v2`)

## Hypothesis

A pre-trained table over the last 4 joint moves beats the one over 3 (pretrained_context_v2) by >= 2 pts vs pools of parameter variants of the whole field (pool.variants 1.0, 250 rounds, fresh seeds, thorough budget); lab experiment prior-context-4: +12.2 pts [+3.4, +21.6]

## Command

```bash
uv run janken lab experiment bots/l1/pretrained_deep.yaml bots/l1/pretrained_context_v2.yaml --rounds 250 --round-robins 32 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --variants 1.0 --seed 4085164331 --name 0080-pretrained-deep-vs-pretrained-context-v2
```

## Results

32 of 32 round robin(s), pool 20, 250 rounds/match, seed 4085164331, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| pretrained_deep | 640 | 389-16-235 | 62.0% [58.2%, 65.7%] | +25.6 | 0 | 1613 +/- 106 |
| pretrained_context_v2 | 640 | 340-13-287 | 54.1% [50.3%, 58.0%] | +22.6 | 0 | 1531 +/- 104 |

Paired comparisons:

- `pretrained_deep - pretrained_context_v2 = +7.9 pts [+3.4, +12.3]` over 640 shared matches: pretrained_deep better

Weakest matchups of pretrained_deep: repeat_mirror_v1 12.5%, markov2_joint_v1 14.3%, l5_wide_hunter 16.7%, pattern_memory_v1 25.0%, context_mixture_v1 25.0%, gate_main_first_stationary_v3 29.2%.

Weakest matchups of pretrained_context_v2: rps4_lite_v1 0.0%, gate_main_first_stationary_v3 8.3%, pattern_memory_v1 12.5%, repeat_mirror_v1 12.5%, l5_wide_hunter 16.7%, smartbot_sims_v2 18.8%.

## Analysis

Lab experiments: context length 1, 2, 3 win 19.0%, 22.5%, 44.5% of matches vs whole-field variants (k=3 - k=2 = +22.0 pts [+13.0, +31.0]); k=4 - k=3 = +12.2 pts [+3.4, +21.6] (8 round robins), confirmed here. The prior only acts as a cold start (weights 0.25-1 play identically), and a longer context names the opponent's habit more precisely when the match hasn't shown that context yet. PriorTable's joint order now goes to 4 (19,683 knobs, a 158 KB bot).

## Verdict

**keep**. A longer context makes a sharper cold start: pretrained_deep (the pre-trained table over the last 4 joint moves, prior worth 1) - pretrained_context_v2 (3 moves) = +7.9 pts [+3.4, +12.3] over 640 paired matches vs pools of parameter variants of the whole field (32 round robins at the thorough budget, fresh seeds), 62.0% of matches vs 54.1%.

## Species

**promote**: its evaluation (run `20261013-162753_0080-pretrained-deep-vs-pretrained-context-v2`) paired it with pretrained_context_v2: +7.9 pts [+3.4, +12.3]; better.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `pretrained_context_v2` | L1 | 73.9% |
| `pattern_memory_v1` | L1 | 59.3% |
| `rotation_outcome_v1` | L1 | 58.2% |
| `markov2_joint_v1` | L1 | 56.7% |
| `context_mixture_v1` | L1 | 55.8% |
