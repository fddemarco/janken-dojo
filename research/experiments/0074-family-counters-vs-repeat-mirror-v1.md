# 0074: family_counters vs repeat_mirror_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #79
- **Candidates:** `bots/l3/family_counters.yaml`
- **Baselines:** `bots/l2/repeat_mirror_v1.yaml`
- **Run:** `20261013-160748_0074-family-counters-vs-repeat-mirror-v1`
- **Verdict:** iterate

## Hypothesis

A bandit over the natural counter of each family (frequency, rotation_outcome, pattern_memory, anti_smartbot, geometry_ensemble) beside repeat_mirror, greedy on decayed records, beats repeat_mirror_v1 by >= 2 pts vs pools of parameter variants of the whole field (pool.variants 1.0, 250 rounds); arena: +7.2 pts of net rounds +- 1.3 on held-out L1-L4 variants (idea #79)

## Command

```bash
uv run janken lab experiment bots/l3/family_counters.yaml bots/l2/repeat_mirror_v1.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --variants 1.0 --seed 1097397572 --name 0074-family-counters-vs-repeat-mirror-v1
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 1097397572, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| family_counters | 200 | 126-4-70 | 64.0% [57.1%, 70.3%] | +32.1 | 0 | 1621 +/- 65 |
| repeat_mirror_v1 | 200 | 102-3-95 | 51.7% [44.9%, 58.6%] | +27.8 | 0 | 1520 +/- 98 |

Paired comparisons:

- `family_counters - repeat_mirror_v1 = +12.2 pts [+4.2, +20.2]` over 200 shared matches: family_counters better

Weakest matchups of family_counters: counter_council_v1 0.0%, anti_rps4_v1 0.0%, predator_v2 0.0%, l2_council_v1 0.0%, bayes_predators_v1 0.0%, gate_bandit_period_v2 0.0%.

Weakest matchups of repeat_mirror_v1: predator_v2 0.0%, level_k_gate_v2 0.0%, anti_iocaine_v1 0.0%, sims_lite_v1 0.0%, replay_hunter_gate_v2 0.0%, gate_main_first_v3 0.0%.

## Analysis

64.0% of matches vs 51.7%. Weakest matchups: the field's L3 councils and gates (counter_council, l2_council, predator, bayes_predators, gate_bandit_period: 0%) and anti_rps4: bots that replay or out-aggregate its arms. Origin: the opening-probe study (research/probe_study.md), where a gate over the family counters beat both the probe and the oracle-switch bound: identification by record, not by script.

## Verdict

**iterate**. Better than its L2 baseline: family_counters (a greedy decayed-net bandit over repeat_mirror and each family's natural counter) - repeat_mirror_v1 = +12.2 pts [+4.2, +20.2] over 200 paired matches vs pools of parameter variants of the whole field (250 rounds), as the arena predicted (+7.2 pts of net rounds over repeat_mirror on held-out variants). But it is an L3: the comparison that decides it is vs the field's L3 council, note 0075.
