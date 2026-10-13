# 0088: hunter_three_mains vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #85
- **Candidates:** `bots/l4/hunter_three_mains.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-183106_0088-hunter-three-mains-vs-l3-l4-variants`
- **Verdict:** drop

## Hypothesis

With three mains to play (two as COPY experts from our seat), the gate leaves a countered main: at least +4 pts over replay_hunter_wide_v2 vs pools of L3-L4 parameter variants, without the holes notes 0087's single swaps opened

## Command

```bash
uv run janken lab experiment bots/l4/hunter_three_mains.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode full --no-allow-small-pool --no-mocks --variants 1.0 --pool-list research/gauntlet/l3_l4.txt --seed 3461690159 --name 0088-hunter-three-mains-vs-l3-l4-variants
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 3461690159, mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide_v2 | 200 | 169-2-29 | 85.0% [79.4%, 89.3%] | +24.7 | 0 | 1818 +/- 59 |
| hunter_three_mains | 200 | 167-1-32 | 83.8% [78.0%, 88.2%] | +26.9 | 0 | 1798 +/- 76 |

Paired comparisons:

- `hunter_three_mains - replay_hunter_wide_v2 = -1.2 pts [-7.8, +5.5]` over 200 shared matches: no significant difference

Weakest matchups of hunter_three_mains: replay_hunter_gate_v2 37.5%, counter_council_v1 37.5%, multiscale_council_v1 57.1%, sicilian_meta_v1 62.5%, double_bluff_gate_v2 66.7%, smartbot_sims_v2 66.7%.

Weakest matchups of replay_hunter_wide_v2: double_bluff_gate_v2 50.0%, multiscale_council_v1 57.1%, l2_council_v1 58.3%, replay_hunter_gate_v2 62.5%, sicilian_meta_v1 62.5%, counter_council_v1 75.0%.

## Analysis

-

## Verdict

**drop**. Three mains (two more played as COPY experts) tie the best L4 vs pools of L3-L4 parameter variants: -1.2 pts [-7.8, +5.5] over 200 matches, rounds +2.2 per match +- 2.9. Paired round margins tie for notes 0086-0087 too (+1.7 +- 3.3, -1.0 +- 3.3, -0.9 +- 3.3): vs unknown L3-L4s the best L4 sits at about +24 rounds and 80-85% of matches whatever its main or extra experts.
