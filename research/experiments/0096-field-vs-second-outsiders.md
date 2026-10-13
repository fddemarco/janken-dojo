# 0096: replay_hunter_wide_v2, l2_council_v1, level_k_gate_v2 vs smartbot_sims_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #88
- **Candidates:** `bots/l4/replay_hunter_wide_v2.yaml`, `bots/l3/l2_council_v1.yaml`, `bots/l4/level_k_gate_v2.yaml`
- **Baselines:** `bots/l3/smartbot_sims_v2.yaml`
- **Run:** `20261013-190838_0096-field-vs-second-outsiders`
- **Verdict:** iterate

## Hypothesis

The gap holds vs a second outsider family built from other components: the best L4 wins under 70% of matches and doesn't beat its main smartbot_sims_v2 significantly (prediction of theory 02, the architecture-overfitting claim)

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_wide_v2.yaml bots/l3/l2_council_v1.yaml bots/l4/level_k_gate_v2.yaml bots/l3/smartbot_sims_v2.yaml --rounds 250 --round-robins 120 --pool-size 3 --mode candidates --no-allow-small-pool --no-mocks --pool-list research/gauntlet/outsiders2.txt --seed 1079431110 --name 0096-field-vs-second-outsiders
```

## Results

120 of 120 round robin(s), pool 3, 250 rounds/match, seed 1079431110, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| smartbot_sims_v2 | 360 | 195-10-155 | 55.6% [50.4%, 60.6%] | +2.0 | 0 | 1407 +/- 118 |
| l2_council_v1 | 360 | 189-19-152 | 55.1% [50.0%, 60.2%] | +1.6 | 0 | 1515 +/- 147 |
| replay_hunter_wide_v2 | 360 | 193-11-156 | 55.1% [50.0%, 60.2%] | +2.2 | 0 | 1652 +/- 118 |
| level_k_gate_v2 | 360 | 92-11-257 | 27.1% [22.8%, 31.9%] | -6.5 | 0 | 1399 +/- 111 |

Paired comparisons:

- `replay_hunter_wide_v2 - l2_council_v1 = +0.0 pts [-6.8, +6.9]` over 360 shared matches: no significant difference
- `replay_hunter_wide_v2 - level_k_gate_v2 = +28.1 pts [+20.8, +34.6]` over 360 shared matches: replay_hunter_wide_v2 better
- `replay_hunter_wide_v2 - smartbot_sims_v2 = -0.4 pts [-7.8, +6.8]` over 360 shared matches: no significant difference
- `l2_council_v1 - level_k_gate_v2 = +28.1 pts [+21.1, +34.6]` over 360 shared matches: l2_council_v1 better
- `l2_council_v1 - smartbot_sims_v2 = -0.4 pts [-7.6, +6.5]` over 360 shared matches: no significant difference
- `level_k_gate_v2 - smartbot_sims_v2 = -28.5 pts [-35.1, -21.5]` over 360 shared matches: smartbot_sims_v2 better

Weakest matchups of replay_hunter_wide_v2: outsider2_council 46.2%, outsider2_gate 53.3%, outsider2_greedy 65.8%.

Weakest matchups of l2_council_v1: outsider2_council 52.1%, outsider2_greedy 52.5%, outsider2_gate 60.8%.

Weakest matchups of level_k_gate_v2: outsider2_council 23.3%, outsider2_gate 23.8%, outsider2_greedy 34.2%.

Weakest matchups of smartbot_sims_v2: outsider2_greedy 45.8%, outsider2_gate 54.2%, outsider2_council 66.7%.

## Analysis

-

## Verdict

**iterate**. Prediction confirmed vs a second outsider family (L3-L4s built from iocaine_lite, geometry_ensemble, outcome_reader, second_guess, fast_greedy_markov, zoo_hunter): the best L4 wins 55.1% of matches (+2.2 rounds), tied with its main smartbot_sims_v2 (-0.4 pts [-7.8, +6.8]) and l2_council_v1 (+0.0). level_k_gate_v2, which beats the best L4 in the field, wins 27.1% here (-28.1 pts): the field rewards bots built to read the field. Next: judge L3-L4 work on both outsider lists.
