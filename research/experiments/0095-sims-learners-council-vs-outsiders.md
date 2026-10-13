# 0095: sims_learners_council vs smartbot_sims_v2, replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #87
- **Candidates:** `bots/l4/sims_learners_council.yaml`
- **Baselines:** `bots/l3/smartbot_sims_v2.yaml`, `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-190254_0095-sims-learners-council-vs-outsiders`
- **Verdict:** drop

## Hypothesis

A Thompson council of smartbot_sims_v2 and the strong learners beats smartbot_sims_v2 by at least 3 rounds per match vs the outsiders, and matches replay_hunter_wide_v2 there

## Command

```bash
uv run janken lab experiment bots/l4/sims_learners_council.yaml bots/l3/smartbot_sims_v2.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 120 --pool-size 3 --mode candidates --no-allow-small-pool --no-mocks --pool-list research/gauntlet/outsiders.txt --seed 705060083 --name 0095-sims-learners-council-vs-outsiders
```

## Results

120 of 120 round robin(s), pool 3, 250 rounds/match, seed 705060083, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| smartbot_sims_v2 | 360 | 224-11-125 | 63.7% [58.7%, 68.5%] | +4.0 | 0 | 1530 +/- 142 |
| replay_hunter_wide_v2 | 360 | 216-21-123 | 62.9% [57.8%, 67.7%] | +4.6 | 0 | 1622 +/- 136 |
| sims_learners_council | 360 | 120-10-230 | 34.7% [30.0%, 39.8%] | -8.8 | 0 | 1397 +/- 153 |

Paired comparisons:

- `sims_learners_council - smartbot_sims_v2 = -29.0 pts [-35.6, -22.5]` over 360 shared matches: smartbot_sims_v2 better
- `sims_learners_council - replay_hunter_wide_v2 = -28.2 pts [-35.0, -21.5]` over 360 shared matches: replay_hunter_wide_v2 better
- `smartbot_sims_v2 - replay_hunter_wide_v2 = +0.8 pts [-6.1, +7.6]` over 360 shared matches: no significant difference

Weakest matchups of sims_learners_council: outsider_gate 5.0%, outsider_greedy 40.0%, outsider_council 59.2%.

Weakest matchups of smartbot_sims_v2: outsider_gate 54.2%, outsider_greedy 67.9%, outsider_council 69.2%.

Weakest matchups of replay_hunter_wide_v2: outsider_gate 55.0%, outsider_council 63.7%, outsider_greedy 70.0%.

## Analysis

-

## Verdict

**drop**. Putting the strong learners inside a Thompson council with smartbot_sims_v2 collapses vs the outsiders: -29.0 pts [-35.6, -22.5] vs smartbot_sims_v2 (34.7% vs 63.7% of matches; -12.8 rounds per match +- 2.1). Sampling doesn't protect deterministic learners from opponents holding their counters; the council follows them when they lead and is read. smartbot_sims_v2 alone ties the best L4 vs unknown opponents (+0.8 pts [-6.1, +7.6]).
