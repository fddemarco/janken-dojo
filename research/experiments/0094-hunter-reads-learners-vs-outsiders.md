# 0094: hunter_reads_learners vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #86
- **Candidates:** `bots/l4/hunter_reads_learners.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-185812_0094-hunter-reads-learners-vs-outsiders`
- **Verdict:** drop

## Hypothesis

Experts that read public learners gain at least 3 rounds per match over replay_hunter_wide_v2 vs the outsiders (caveat: the outsiders are built from those learners, so this is the favourable case; note it must also hold vs the field)

## Command

```bash
uv run janken lab experiment bots/l4/hunter_reads_learners.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 120 --pool-size 3 --mode candidates --no-allow-small-pool --no-mocks --pool-list research/gauntlet/outsiders.txt --seed 2956684134 --name 0094-hunter-reads-learners-vs-outsiders
```

## Results

120 of 120 round robin(s), pool 3, 250 rounds/match, seed 2956684134, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide_v2 | 360 | 230-6-124 | 64.7% [59.7%, 69.5%] | +5.2 | 0 | 1572 +/- 176 |
| hunter_reads_learners | 360 | 199-13-148 | 57.1% [51.9%, 62.1%] | +2.7 | 0 | 1538 +/- 169 |

Paired comparisons:

- `hunter_reads_learners - replay_hunter_wide_v2 = -7.6 pts [-14.6, -0.7]` over 360 shared matches: replay_hunter_wide_v2 better

Weakest matchups of hunter_reads_learners: outsider_gate 49.2%, outsider_council 58.3%, outsider_greedy 63.7%.

Weakest matchups of replay_hunter_wide_v2: outsider_gate 55.0%, outsider_council 68.8%, outsider_greedy 70.4%.

## Analysis

-

## Verdict

**drop**. Experts that read the outsiders' own components, without playing them, still cost the best L4 vs the outsiders: -7.6 pts [-14.6, -0.7], -2.5 rounds per match +- 1.7 (360 paired matches), in the favourable case where the opponents are built from what the experts read. With notes 0086 and 0090, every expert added to replay_hunter_wide_v2's LEADER gate this session cost 2.5-4 rounds per match, relevant or not; a gate edge (note 0093) didn't help either, so the cost isn't simply a lucky leader followed. Mechanism open.
