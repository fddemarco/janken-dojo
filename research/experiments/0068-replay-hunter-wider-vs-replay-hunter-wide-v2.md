# 0068: replay_hunter_wider vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #64
- **Candidates:** `bots/inactive/legacy/replay_hunter_wider.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-144418_0068-replay-hunter-wider-vs-replay-hunter-wide-v2`
- **Verdict:** iterate

## Hypothesis

On pools of the hard opponents (research/gauntlet/hard_l4.txt, the field bots the best L4 wins under 70% vs), replay_hunter_wider beats replay_hunter_wide_v2 by >= 2 pts, where random pools tied them (notes 0056, 0057; the gauntlet on the same list: +8.5 +- 4.9 pts of rounds)

## Command

```bash
uv run janken lab experiment bots/inactive/legacy/replay_hunter_wider.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 10 --pool-size 12 --mode candidates --allow-small-pool --no-mocks --pool-list research/gauntlet/hard_l4.txt --seed 3760722358 --name 0068-replay-hunter-wider-vs-replay-hunter-wide-v2
```

## Results

10 of 10 round robin(s), pool 12, 250 rounds/match, seed 3760722358, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wider | 120 | 76-2-42 | 64.2% [55.3%, 72.2%] | +26.0 | 0 | 1623 +/- 120 |
| replay_hunter_wide_v2 | 120 | 71-3-46 | 60.4% [51.5%, 68.7%] | +4.8 | 0 | 1579 +/- 84 |

Paired comparisons:

- `replay_hunter_wider - replay_hunter_wide_v2 = +3.8 pts [-6.7, +14.2]` over 120 shared matches: no significant difference

Weakest matchups of replay_hunter_wider: l5_wide_hunter 30.0%, l5_hunter 40.0%, replay_hunter_gate_v2 45.0%, nash_v1 50.0%, sampled_markov_v1 50.0%, geometry_v1 55.0%.

Weakest matchups of replay_hunter_wide_v2: l5_wide_hunter 10.0%, l5_hunter 10.0%, geometry_v1 35.0%, nash_v1 40.0%, transition_matrix_v1 50.0%, replay_hunter_gate_v2 60.0%.

## Analysis

Scores vs the hard pool: replay_hunter_wider 64.2% of matches (+26.0 rounds per match), replay_hunter_wide_v2 60.4% (+4.8). The round gain matches the gauntlet on the same list (+8.5 pts of rounds +- 4.9, idea #64). The first evaluation through pool.lists (idea #60): the comparison random pools couldn't see shows up on a 12-opponent hard pool. Weakest matchups of replay_hunter_wider: the L5s that replay it (l5_wide_hunter 30%, l5_hunter 40%) and replay_hunter_gate_v2 (45%). Next: grow this run until the match score resolves, and use hard pools for the L3 comparisons of notes 0065-0067.

## Verdict

**iterate**. On pools of the hard opponents (research/gauntlet/hard_l4.txt, pool.lists), replay_hunter_wider - replay_hunter_wide_v2 = +3.8 pts [-6.7, +14.2] of match score over 120 paired matches (10 round robins of 12-bot pools, 250 rounds): not yet significant; but its paired round margin is +21.2 rounds per match +- 11.7 (95%), which excludes 0, where random pools tied the two (notes 0056, 0057). The hard pools separate them on rounds; matches need more round robins.
