# 0085: context_mixture_faster vs context_mixture_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #83
- **Candidates:** `bots/l1/context_mixture_faster.yaml`
- **Baselines:** `bots/l1/context_mixture_v2.yaml`
- **Run:** `20261013-165502_0085-context-mixture-faster-vs-context-mixture-v2`
- **Verdict:** drop

## Hypothesis

context_mixture with DECAY 0.72 beats context_mixture_v2 (0.81) by >= 2 pts vs random pools of the field on fresh seeds (tuning: +6.8 pts [+0.5, +13.2] validated)

## Command

```bash
uv run janken lab experiment bots/l1/context_mixture_faster.yaml bots/l1/context_mixture_v2.yaml --rounds 200 --round-robins 16 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 209985894 --name 0085-context-mixture-faster-vs-context-mixture-v2
```

## Results

16 of 16 round robin(s), pool 20, 200 rounds/match, seed 209985894, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| context_mixture_v2 | 320 | 112-3-205 | 35.5% [30.4%, 40.9%] | -0.0 | 0 | 1359 +/- 104 |
| context_mixture_faster | 320 | 106-6-208 | 34.1% [29.1%, 39.4%] | -1.9 | 0 | 1369 +/- 74 |

Paired comparisons:

- `context_mixture_faster - context_mixture_v2 = -1.4 pts [-5.2, +2.3]` over 320 shared matches: no significant difference

Weakest matchups of context_mixture_faster: leader_new_l2_v1 0.0%, level_k_gate_v2 0.0%, bayes_predators_v1 0.0%, replay_hunter_gate_v2 0.0%, l5_hunter 0.0%, sims_lite_v1 0.0%.

Weakest matchups of context_mixture_v2: level_k_gate_v2 0.0%, leader_new_l2_v1 0.0%, bayes_predators_v1 0.0%, iocaine_lite_v1 0.0%, mirror_bandit_v1 0.0%, replay_hunter_gate_v2 0.0%.

## Analysis

Scores: 34.1% vs 35.5% of matches. Of the second tuning's five validated configurations only one cleared the defaults, at the upper end of a cluster (0.69-0.72) whose others showed nothing: a single selected lead, which the insight of 2026-10-13 on 10-round-robin leads predicts to shrink.

## Verdict

**drop**. Forgetting faster doesn't pay: context_mixture with DECAY 0.72 - context_mixture_v2 (0.81) = -1.4 pts [-5.2, +2.3] over 320 paired matches vs random pools on fresh seeds (thorough budget, futile at look 2). The second tuning's +6.8 pts (note 0084) was the winner's curse: 0.81 stays.
