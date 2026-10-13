# 0086: hunter_generalists vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #84
- **Candidates:** `bots/l4/hunter_generalists.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-182424_0086-hunter-generalists-vs-l3-l4-variants`
- **Verdict:** drop

## Hypothesis

Generalist experts gain at least 4 pts of match score over replay_hunter_wide_v2 vs pools of L3-L4 parameter variants, where the replays' exact targets are gone

## Command

```bash
uv run janken lab experiment bots/l4/hunter_generalists.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 8 --pool-size 20 --mode full --no-allow-small-pool --no-mocks --variants 1.0 --pool-list research/gauntlet/l3_l4.txt --seed 415393531 --name 0086-hunter-generalists-vs-l3-l4-variants
```

## Results

8 of 8 round robin(s), pool 20, 250 rounds/match, seed 415393531, mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide_v2 | 160 | 138-2-20 | 86.9% [80.8%, 91.3%] | +24.5 | 0 | 1825 +/- 83 |
| hunter_generalists | 160 | 122-2-36 | 76.9% [69.8%, 82.7%] | +23.7 | 0 | 1746 +/- 77 |

Paired comparisons:

- `hunter_generalists - replay_hunter_wide_v2 = -10.0 pts [-18.1, -2.2]` over 160 shared matches: replay_hunter_wide_v2 better

Weakest matchups of hunter_generalists: level_k_gate_v2 25.0%, multiscale_council_v1 25.0%, double_bluff_gate_v2 41.7%, gate_edge_smartbot_v2 50.0%, l2_council_v1 50.0%, predator_v2 60.0%.

Weakest matchups of replay_hunter_wide_v2: level_k_gate_v2 25.0%, gate_edge_v3 50.0%, gate_leader_v1 60.0%, replay_hunter_gate_v2 66.7%, sicilian_meta_v1 66.7%, counter_council_v1 71.4%.

## Analysis

-

## Verdict

**drop**. Generalist experts cost the best L4 -10.0 pts [-18.1, -2.2] vs pools of L3-L4 parameter variants (160 matches, sequential stop at look 4), though its round margin is level (+23.7 vs +24.5 per match): seven more experts in a LEADER gate give it more chances to follow a lucky leader, and lose close matches. The replays transfer to variants (86.9% of matches); level_k_gate_v2 beats both (25%).
