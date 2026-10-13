# 0066: learner_council vs l2_council_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #67
- **Candidates:** `bots/l3/learner_council.yaml`
- **Baselines:** `bots/l3/l2_council_v1.yaml`
- **Run:** `20261013-143819_0066-learner-council-vs-l2-council-v1`
- **Verdict:** drop

## Hypothesis

Theory prediction (theory/02-meta-strategies.md): an L3 council of L2's strong learners only (geometry_ensemble, period_bandit, repeat_mirror; no counters) beats l2_council_v1 by >= 2 pts vs pools of L1-L3 bots, 250 rounds (idea #67)

## Command

```bash
uv run janken lab experiment bots/l3/learner_council.yaml bots/l3/l2_council_v1.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 4089941211 --name 0066-learner-council-vs-l2-council-v1
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 4089941211, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| l2_council_v1 | 200 | 149-5-46 | 75.8% [69.4%, 81.2%] | +61.0 | 0 | 1726 +/- 72 |
| learner_council | 200 | 145-3-52 | 73.2% [66.7%, 78.9%] | +56.3 | 0 | 1713 +/- 69 |

Paired comparisons:

- `learner_council - l2_council_v1 = -2.5 pts [-10.0, +5.0]` over 200 shared matches: no significant difference

Weakest matchups of learner_council: geometry_ensemble_v1 0.0%, dropswitch_matcher_v1 0.0%, second_guess_v1 0.0%, repeat_mirror_v1 0.0%, nash_v1 25.0%, predator_v2 25.0%.

Weakest matchups of l2_council_v1: backoff_family_v1 0.0%, smartbot_sims_v2 0.0%, geometry_ensemble_v1 0.0%, multiscale_council_v1 0.0%, leader_new_l2_v1 0.0%, dropswitch_council_v1 16.7%.

## Analysis

A council that plays its arms' moves (replays from our seat, turned) holds no model of those arms as opponents, so it can't beat them head to head. repeat_mirror worked at L2 because its arms read each L1 rule from both seats (the rule and its counter, iocaine's principle); these L3 councils read their L2 arms from our seat only. Next: the same arms from both seats (idea #67's follow-up).

## Verdict

**drop**. A council of L2's strong learners doesn't beat l2_council_v1 either: learner_council - l2_council_v1 = -2.5 pts [-10.0, +5.0] over 200 paired matches vs pools of L1-L3 (10 round robins, 250 rounds). It loses every match to its own arms' species (geometry_ensemble_v1, repeat_mirror_v1), as well as to dropswitch_matcher_v1 and second_guess_v1.
