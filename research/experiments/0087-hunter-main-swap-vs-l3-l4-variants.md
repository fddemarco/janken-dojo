# 0087: hunter_council_main, hunter_multiscale_main vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #85
- **Candidates:** `bots/l4/hunter_council_main.yaml`, `bots/l4/hunter_multiscale_main.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-182720_0087-hunter-main-swap-vs-l3-l4-variants`
- **Verdict:** drop

## Hypothesis

A main no field bot replays gains at least 4 pts of match score over replay_hunter_wide_v2 vs pools of L3-L4 parameter variants, mostly vs level_k_gate_v2 and the gates built on smartbot_sims

## Command

```bash
uv run janken lab experiment bots/l4/hunter_council_main.yaml bots/l4/hunter_multiscale_main.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode full --no-allow-small-pool --no-mocks --variants 1.0 --pool-list research/gauntlet/l3_l4.txt --seed 3885712662 --name 0087-hunter-main-swap-vs-l3-l4-variants
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 3885712662, mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| hunter_council_main | 200 | 164-2-34 | 82.5% [76.6%, 87.1%] | +25.0 | 0 | 1770 +/- 69 |
| hunter_multiscale_main | 200 | 159-0-41 | 79.5% [73.4%, 84.5%] | +22.4 | 0 | 1762 +/- 80 |
| replay_hunter_wide_v2 | 200 | 158-2-40 | 79.5% [73.4%, 84.5%] | +23.4 | 0 | 1753 +/- 53 |

Paired comparisons:

- `hunter_council_main - hunter_multiscale_main = +3.0 pts [-4.5, +10.2]` over 200 shared matches: no significant difference
- `hunter_council_main - replay_hunter_wide_v2 = +3.0 pts [-4.5, +10.2]` over 200 shared matches: no significant difference
- `hunter_multiscale_main - replay_hunter_wide_v2 = +0.0 pts [-7.8, +7.5]` over 200 shared matches: no significant difference

Weakest matchups of hunter_council_main: multiscale_council_v1 7.1%, sicilian_meta_v1 37.5%, level_k_gate_v2 57.1%, predator_v2 57.1%, counter_council_v1 60.0%, double_bluff_gate_v2 62.5%.

Weakest matchups of hunter_multiscale_main: replay_hunter_gate_v2 28.6%, counter_council_v1 40.0%, gate_edge_v3 50.0%, gate_main_first_backoff_v1 57.1%, l2_council_v1 66.7%, vote_council_v1 66.7%.

Weakest matchups of replay_hunter_wide_v2: multiscale_council_v1 28.6%, smartbot_sims_v2 44.4%, gate_main_first_backoff_v1 50.0%, l2_council_v1 55.6%, replay_hunter_gate_v2 57.1%, double_bluff_gate_v2 62.5%.

## Analysis

-

## Verdict

**drop**. Swapping the best L4's main ties it vs pools of L3-L4 parameter variants (200 matches, 10 round robins): l2_council_v1 as main +3.0 pts [-4.5, +10.2], multiscale_council_v1 +0.0 [-7.8, +7.5]. The holes move: the council main fixes level_k_gate_v2 (57% vs 25-33% of matches) and loses to multiscale_council_v1 (7%); the multiscale main loses to replay_hunter_gate_v2 (29%). Each main has a counter in the field, so a single main is the hole.
