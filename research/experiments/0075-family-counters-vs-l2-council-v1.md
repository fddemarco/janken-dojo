# 0075: family_counters vs l2_council_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #79
- **Candidates:** `bots/l3/family_counters.yaml`
- **Baselines:** `bots/l3/l2_council_v1.yaml`
- **Run:** `20261013-160825_0075-family-counters-vs-l2-council-v1`
- **Verdict:** drop

## Hypothesis

The family-counter gate beats the field's L3 council l2_council_v1 by >= 2 pts vs pools of parameter variants of the whole field (pool.variants 1.0, 250 rounds, fresh seeds, thorough budget); first run: +12.2 pts [+4.2, +20.2] over repeat_mirror_v1 (idea #79)

## Command

```bash
uv run janken lab experiment bots/l3/family_counters.yaml bots/l3/l2_council_v1.yaml --rounds 250 --round-robins 8 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --variants 1.0 --seed 2304157043 --name 0075-family-counters-vs-l2-council-v1
```

## Results

8 of 8 round robin(s), pool 20, 250 rounds/match, seed 2304157043, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| l2_council_v1 | 160 | 107-3-50 | 67.8% [60.2%, 74.6%] | +36.8 | 0 | 1682 +/- 117 |
| family_counters | 160 | 104-3-53 | 65.9% [58.3%, 72.8%] | +27.6 | 0 | 1620 +/- 92 |

Paired comparisons:

- `family_counters - l2_council_v1 = -1.9 pts [-10.9, +6.9]` over 160 shared matches: no significant difference

Weakest matchups of family_counters: bayes_predators_v1 0.0%, l5_hunter 0.0%, anti_smartbot_sims_v3 0.0%, gate_main_first_backoff_v1 0.0%, predator_v2 0.0%, mirror_bandit_v1 0.0%.

Weakest matchups of l2_council_v1: dropswitch_council_v1 0.0%, l5_hunter 0.0%, mirror_bandit_v1 0.0%, l5_wide_hunter 0.0%, smartbot_sims_v2 0.0%, fast_greedy_markov_v1 0.0%.

## Analysis

Scores: l2_council_v1 67.8% of matches (+36.8 rounds per match), family_counters 65.9% (+27.6). A fourth L3 design (after notes 0065-0067) that ties the field's L3 council: above L2 the councils saturate, whatever their arms. The family counters are good arms, not a better aggregator.

## Verdict

**drop**. No better than the field's L3 council: family_counters - l2_council_v1 = -1.9 pts [-10.9, +6.9] over 160 paired matches vs pools of parameter variants of the whole field (fresh seeds, stopped for futility at look 1). Its +12.2 pts over repeat_mirror_v1 (note 0074) is the L3-over-L2 effect, which l2_council_v1 already has.
