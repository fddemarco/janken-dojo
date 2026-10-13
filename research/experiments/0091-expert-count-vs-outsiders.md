# 0091: level_k_gate_v2, replay_hunter_gate_v2, smartbot_sims_v2 vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** -
- **Candidates:** `bots/l4/level_k_gate_v2.yaml`, `bots/l4/replay_hunter_gate_v2.yaml`, `bots/l3/smartbot_sims_v2.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-184603_0091-expert-count-vs-outsiders`
- **Verdict:** drop

## Hypothesis

Against unknown L3-L4s (outsiders), a gate's replays of field bots are dead weight: gates with fewer experts on the same main (level_k_gate_v2: 6, replay_hunter_gate_v2) and the bare main score at least as well as replay_hunter_wide_v2 (42 experts)

## Command

```bash
uv run janken lab experiment bots/l4/level_k_gate_v2.yaml bots/l4/replay_hunter_gate_v2.yaml bots/l3/smartbot_sims_v2.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 120 --pool-size 3 --mode candidates --no-allow-small-pool --no-mocks --pool-list research/gauntlet/outsiders.txt --seed 1469653032 --name 0091-expert-count-vs-outsiders
```

## Results

120 of 120 round robin(s), pool 3, 250 rounds/match, seed 1469653032, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide_v2 | 360 | 231-8-121 | 65.3% [60.2%, 70.0%] | +5.1 | 0 | 1646 +/- 136 |
| replay_hunter_gate_v2 | 360 | 222-16-122 | 63.9% [58.8%, 68.7%] | +5.1 | 0 | 1641 +/- 126 |
| level_k_gate_v2 | 360 | 215-8-137 | 60.8% [55.7%, 65.7%] | +4.4 | 0 | 1540 +/- 135 |
| smartbot_sims_v2 | 360 | 209-11-140 | 59.6% [54.4%, 64.5%] | +2.9 | 0 | 1362 +/- 109 |

Paired comparisons:

- `level_k_gate_v2 - replay_hunter_gate_v2 = -3.1 pts [-10.0, +3.8]` over 360 shared matches: no significant difference
- `level_k_gate_v2 - smartbot_sims_v2 = +1.2 pts [-5.6, +7.6]` over 360 shared matches: no significant difference
- `level_k_gate_v2 - replay_hunter_wide_v2 = -4.4 pts [-11.7, +2.8]` over 360 shared matches: no significant difference
- `replay_hunter_gate_v2 - smartbot_sims_v2 = +4.3 pts [-2.5, +11.1]` over 360 shared matches: no significant difference
- `replay_hunter_gate_v2 - replay_hunter_wide_v2 = -1.4 pts [-8.2, +5.4]` over 360 shared matches: no significant difference
- `smartbot_sims_v2 - replay_hunter_wide_v2 = -5.7 pts [-12.2, +1.0]` over 360 shared matches: no significant difference

Weakest matchups of level_k_gate_v2: outsider_gate 50.4%, outsider_council 61.3%, outsider_greedy 70.8%.

Weakest matchups of replay_hunter_gate_v2: outsider_gate 50.8%, outsider_council 62.1%, outsider_greedy 78.8%.

Weakest matchups of smartbot_sims_v2: outsider_gate 39.2%, outsider_council 66.2%, outsider_greedy 73.3%.

Weakest matchups of replay_hunter_wide_v2: outsider_gate 56.7%, outsider_council 63.3%, outsider_greedy 75.8%.

## Analysis

-

## Verdict

**drop**. Against the outsiders every L4 scores about what its main does: replay_hunter_wide_v2 65.3% of matches (+5.1 rounds), replay_hunter_gate_v2 63.9%, level_k_gate_v2 60.8%, the bare main smartbot_sims_v2 59.6% (+2.9 rounds); no pair differs significantly over 360 paired matches (best L4 - main +5.7 pts [-1.0, +12.2]). Against unknown opponents the replays of field bots add little, and the main does the work.
