# 0093: replay_hunter_wide_v2, replay_hunter_wide_v2 vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** -
- **Candidates:** `bots/l4/replay_hunter_wide_v2.yaml:EDGE=0.05`, `bots/l4/replay_hunter_wide_v2.yaml:EDGE=0.15`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-185158_0093-hunter-edge-vs-outsiders`
- **Verdict:** drop

## Hypothesis

Against unknown opponents the main does the work and experts add ~2 rounds (note 0091); a gate that leaves its main only on a clear edge (EDGE 0.05, 0.15) follows fewer lucky experts and gains at least 2 rounds per match vs the outsiders

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_wide_v2.yaml:EDGE=0.05 bots/l4/replay_hunter_wide_v2.yaml:EDGE=0.15 bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 120 --pool-size 3 --mode candidates --no-allow-small-pool --no-mocks --pool-list research/gauntlet/outsiders.txt --seed 2138737101 --name 0093-hunter-edge-vs-outsiders
```

## Results

120 of 120 round robin(s), pool 3, 250 rounds/match, seed 2138737101, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide_v2 | 360 | 217-6-137 | 61.1% [56.0%, 66.0%] | +4.8 | 0 | 1609 +/- 133 |
| replay_hunter_wide_v2@8ddef3 | 360 | 201-10-149 | 57.2% [52.1%, 62.2%] | +2.3 | 0 | 1471 +/- 148 |
| replay_hunter_wide_v2@cc7140 | 360 | 199-13-148 | 57.1% [51.9%, 62.1%] | +2.3 | 0 | 1529 +/- 163 |

Paired comparisons:

- `replay_hunter_wide_v2@cc7140 - replay_hunter_wide_v2@8ddef3 = -0.1 pts [-6.5, +6.7]` over 360 shared matches: no significant difference
- `replay_hunter_wide_v2@cc7140 - replay_hunter_wide_v2 = -4.0 pts [-10.4, +2.5]` over 360 shared matches: no significant difference
- `replay_hunter_wide_v2@8ddef3 - replay_hunter_wide_v2 = -3.9 pts [-11.0, +3.3]` over 360 shared matches: no significant difference

Weakest matchups of replay_hunter_wide_v2@cc7140: outsider_gate 48.8%, outsider_council 60.0%, outsider_greedy 62.5%.

Weakest matchups of replay_hunter_wide_v2@8ddef3: outsider_gate 50.4%, outsider_council 52.1%, outsider_greedy 69.2%.

Weakest matchups of replay_hunter_wide_v2: outsider_gate 52.5%, outsider_council 60.8%, outsider_greedy 70.0%.

## Analysis

-

## Verdict

**drop**. A gate that leaves its main only on a clear edge loses vs the outsiders: EDGE 0.05 -3.9 pts [-11.0, +3.3], EDGE 0.15 -4.0 pts [-10.4, +2.5], both +2.3 rounds per match vs +4.8 at EDGE 0 (360 paired matches). The experts' small gain vs unknowns (note 0091) is real enough that using them less costs it.
