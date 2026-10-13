# 0090: hunter_generalists, hunter_three_mains vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #84
- **Candidates:** `bots/l4/hunter_generalists.yaml`, `bots/l4/hunter_three_mains.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-184023_0090-hunters-vs-outsiders`
- **Verdict:** drop

## Hypothesis

Against L3-L4s built from components the field's L4s don't replay (research/gauntlet/outsiders.txt), the replays of field bots are idle and generalist experts pay: hunter_generalists beats replay_hunter_wide_v2 by at least 5 pts, the reverse of note 0086

## Command

```bash
uv run janken lab experiment bots/l4/hunter_generalists.yaml bots/l4/hunter_three_mains.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 120 --pool-size 3 --mode candidates --no-allow-small-pool --no-mocks --pool-list research/gauntlet/outsiders.txt --seed 2019146458 --name 0090-hunters-vs-outsiders
```

## Results

120 of 120 round robin(s), pool 3, 250 rounds/match, seed 2019146458, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| hunter_three_mains | 360 | 231-13-116 | 66.0% [60.9%, 70.7%] | +5.3 | 0 | 1550 +/- 138 |
| replay_hunter_wide_v2 | 360 | 223-7-130 | 62.9% [57.8%, 67.7%] | +4.8 | 0 | 1567 +/- 159 |
| hunter_generalists | 360 | 184-5-171 | 51.8% [46.7%, 56.9%] | +0.8 | 0 | 1516 +/- 166 |

Paired comparisons:

- `hunter_generalists - hunter_three_mains = -14.2 pts [-21.0, -7.5]` over 360 shared matches: hunter_three_mains better
- `hunter_generalists - replay_hunter_wide_v2 = -11.1 pts [-18.3, -3.9]` over 360 shared matches: replay_hunter_wide_v2 better
- `hunter_three_mains - replay_hunter_wide_v2 = +3.1 pts [-3.3, +10.0]` over 360 shared matches: no significant difference

Weakest matchups of hunter_generalists: outsider_gate 41.7%, outsider_council 54.6%, outsider_greedy 59.2%.

Weakest matchups of hunter_three_mains: outsider_gate 57.5%, outsider_council 65.4%, outsider_greedy 75.0%.

Weakest matchups of replay_hunter_wide_v2: outsider_council 57.9%, outsider_gate 60.4%, outsider_greedy 70.4%.

## Analysis

-

## Verdict

**drop**. Against three outsiders (L3-L4s built from components no field L4 replays) the best L4 wins only 62.9% of matches (+4.8 rounds), against 80-85% vs the field's L3-L4 variants (notes 0086-0088): its edge comes from knowing the field's architectures, not their parameters. Generalist experts lose here too, -11.1 pts [-18.3, -3.9] (-4.0 rounds +- 2.0), so their cost in note 0086 isn't about the pool; three mains tie (+3.1 pts [-3.3, +10.0], +0.4 rounds +- 1.8). 360 paired matches each (120 round robins of the 3 outsiders).
