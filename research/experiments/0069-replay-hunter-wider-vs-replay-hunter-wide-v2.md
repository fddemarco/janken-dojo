# 0069: replay_hunter_wider vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #64
- **Candidates:** `bots/inactive/legacy/replay_hunter_wider.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-153653_0069-replay-hunter-wider-vs-replay-hunter-wide-v2`
- **Verdict:** drop

## Hypothesis

Confirmation of note 0068 at the thorough budget on fresh seeds: on pools of the hard opponents (research/gauntlet/hard_l4.txt), replay_hunter_wider beats replay_hunter_wide_v2 by >= 2 pts of match score (0068: +3.8 pts [-6.7, +14.2], +21.2 rounds per match +- 11.7)

## Command

```bash
uv run janken lab experiment bots/inactive/legacy/replay_hunter_wider.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 8 --pool-size 12 --mode candidates --allow-small-pool --no-mocks --pool-list research/gauntlet/hard_l4.txt --seed 2759298148 --name 0069-replay-hunter-wider-vs-replay-hunter-wide-v2
```

## Results

8 of 8 round robin(s), pool 12, 250 rounds/match, seed 2759298148, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide_v2 | 96 | 62-3-31 | 66.1% [56.2%, 74.8%] | +14.0 | 0 | 1615 +/- 55 |
| replay_hunter_wider | 96 | 61-2-33 | 64.6% [54.6%, 73.4%] | +24.1 | 0 | 1637 +/- 52 |

Paired comparisons:

- `replay_hunter_wider - replay_hunter_wide_v2 = -1.6 pts [-13.0, +9.9]` over 96 shared matches: no significant difference

Weakest matchups of replay_hunter_wider: l5_wide_hunter 12.5%, l5_hunter 31.2%, double_bluff_gate_v2 37.5%, nash_v1 37.5%, sampled_markov_v1 56.2%, replay_hunter_gate_v2 62.5%.

Weakest matchups of replay_hunter_wide_v2: l5_hunter 25.0%, replay_hunter_gate_v2 37.5%, nash_v1 37.5%, l5_wide_hunter 50.0%, transition_matrix_v1 62.5%, geometry_v1 68.8%.

## Analysis

Scores vs the hard pool: replay_hunter_wide_v2 66.1% of matches (+14.0 rounds per match), replay_hunter_wider 64.6% (+24.1). Two runs on the same hard list: the round gain is real but smaller than first seen (+21.2 then +10.0 rounds per match, the winner's curse again), and matches don't follow: vs these opponents a match is decided by a few rounds either way, and the experts add margin in matches already won. So a change that only adds round margin isn't a better bot by the lab's match-score test, even on hard pools.

## Verdict

**drop**. On fresh seeds the hard-pool gain doesn't reach the match score: replay_hunter_wider - replay_hunter_wide_v2 = -1.6 pts [-13.0, +9.9] over 96 paired matches (8 round robins of the hard list, stopped for futility at look 1); its paired round margin is +10.0 rounds per match +- 9.9, half of note 0068's +21.2. The extra experts win their matches by more rounds, not more matches.
