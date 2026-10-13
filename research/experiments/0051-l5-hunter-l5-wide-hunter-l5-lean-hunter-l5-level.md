# 0051: l5_hunter, l5_wide_hunter, l5_lean_hunter, l5_level_k, l5_priority, l5_council vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #46
- **Candidates:** `bots/l5/l5_hunter.yaml`, `bots/l5/l5_wide_hunter.yaml`, `bots/l5/l5_lean_hunter.yaml`, `bots/l5/l5_level_k.yaml`, `bots/l5/l5_priority.yaml`, `bots/l5/l5_council.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-122356_0051-l5-hunter-l5-wide-hunter-l5-lean-hunter-l5-level`
- **Verdict:** drop

## Hypothesis

At least one L5 (a gate or bandit over replays of the L4 gatekeepers) beats replay_hunter_wide_v2, the best L4, by >= 2 pts vs random pools; the L5s were never evaluated (idea #46)

## Command

```bash
uv run janken lab experiment bots/l5/l5_hunter.yaml bots/l5/l5_wide_hunter.yaml bots/l5/l5_lean_hunter.yaml bots/l5/l5_level_k.yaml bots/l5/l5_priority.yaml bots/l5/l5_council.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 636112117 --name 0051-l5-hunter-l5-wide-hunter-l5-lean-hunter-l5-level
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 636112117, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| l5_wide_hunter | 200 | 183-0-17 | 91.5% [86.8%, 94.6%] | +54.6 | 0 | 1787 +/- 62 |
| replay_hunter_wide_v2 | 200 | 177-2-21 | 89.0% [83.9%, 92.6%] | +52.8 | 0 | 1739 +/- 56 |
| l5_hunter | 200 | 175-3-22 | 88.2% [83.1%, 92.0%] | +55.5 | 0 | 1776 +/- 65 |
| l5_council | 200 | 163-5-32 | 82.8% [76.9%, 87.4%] | +49.0 | 0 | 1809 +/- 95 |
| l5_level_k | 200 | 162-4-34 | 82.0% [76.1%, 86.7%] | +47.6 | 0 | 1738 +/- 95 |
| l5_lean_hunter | 200 | 142-3-55 | 71.8% [65.1%, 77.5%] | +42.9 | 0 | 1655 +/- 84 |
| l5_priority | 200 | 134-5-61 | 68.2% [61.5%, 74.3%] | +40.2 | 0 | 1642 +/- 94 |

Paired comparisons:

- `l5_hunter - l5_wide_hunter = -3.2 pts [-8.5, +2.0]` over 200 shared matches: no significant difference
- `l5_hunter - l5_lean_hunter = +16.5 pts [+9.8, +23.2]` over 200 shared matches: l5_hunter better
- `l5_hunter - l5_level_k = +6.2 pts [-0.2, +13.0]` over 200 shared matches: no significant difference
- `l5_hunter - l5_priority = +20.0 pts [+12.8, +27.5]` over 200 shared matches: l5_hunter better
- `l5_hunter - l5_council = +5.5 pts [-1.0, +11.8]` over 200 shared matches: no significant difference
- `l5_hunter - replay_hunter_wide_v2 = -0.8 pts [-6.5, +5.0]` over 200 shared matches: no significant difference
- `l5_wide_hunter - l5_lean_hunter = +19.8 pts [+12.8, +27.0]` over 200 shared matches: l5_wide_hunter better
- `l5_wide_hunter - l5_level_k = +9.5 pts [+4.0, +15.2]` over 200 shared matches: l5_wide_hunter better
- `l5_wide_hunter - l5_priority = +23.2 pts [+16.0, +30.5]` over 200 shared matches: l5_wide_hunter better
- `l5_wide_hunter - l5_council = +8.8 pts [+2.2, +15.2]` over 200 shared matches: l5_wide_hunter better
- `l5_wide_hunter - replay_hunter_wide_v2 = +2.5 pts [-2.5, +8.0]` over 200 shared matches: no significant difference
- `l5_lean_hunter - l5_level_k = -10.2 pts [-17.8, -2.8]` over 200 shared matches: l5_level_k better
- `l5_lean_hunter - l5_priority = +3.5 pts [-4.0, +11.0]` over 200 shared matches: no significant difference
- `l5_lean_hunter - l5_council = -11.0 pts [-18.0, -4.0]` over 200 shared matches: l5_council better
- `l5_lean_hunter - replay_hunter_wide_v2 = -17.2 pts [-23.8, -11.0]` over 200 shared matches: replay_hunter_wide_v2 better
- `l5_level_k - l5_priority = +13.8 pts [+6.0, +21.5]` over 200 shared matches: l5_level_k better
- `l5_level_k - l5_council = -0.8 pts [-7.5, +6.0]` over 200 shared matches: no significant difference
- `l5_level_k - replay_hunter_wide_v2 = -7.0 pts [-13.0, -1.2]` over 200 shared matches: replay_hunter_wide_v2 better
- `l5_priority - l5_council = -14.5 pts [-21.8, -7.2]` over 200 shared matches: l5_council better
- `l5_priority - replay_hunter_wide_v2 = -20.8 pts [-28.0, -13.5]` over 200 shared matches: replay_hunter_wide_v2 better
- `l5_council - replay_hunter_wide_v2 = -6.2 pts [-12.2, -0.2]` over 200 shared matches: replay_hunter_wide_v2 better

Weakest matchups of l5_hunter: nash_v1 0.0%, gate_fast_hold_v1 33.3%, predator_v2 50.0%, transition_matrix_v1 50.0%, geometry_v1 50.0%, gate_main_first_stationary_v3 50.0%.

Weakest matchups of l5_wide_hunter: outcome_reader_v1 0.0%, sicilian_meta_v1 0.0%, leader_hunter_v2 33.3%, second_guess_v1 50.0%, geometry_v1 50.0%, gate_main_first_stationary_v3 50.0%.

Weakest matchups of l5_lean_hunter: gate_fast_hold_v1 0.0%, outcome_reader_v1 0.0%, nash_v1 0.0%, anti_iocaine_v1 0.0%, counter_council_v1 0.0%, vote_council_v1 20.0%.

Weakest matchups of l5_level_k: second_guess_v1 0.0%, leader_hunter_v2 0.0%, counter_council_v1 0.0%, sicilian_meta_v1 0.0%, l2_council_v1 20.0%, geometry_v1 25.0%.

Weakest matchups of l5_priority: multiscale_council_v1 0.0%, nash_v1 0.0%, sampled_markov_v1 0.0%, zoo_hunter_v1 0.0%, predator_v2 0.0%, geometry_v1 12.5%.

Weakest matchups of l5_council: predator_v2 0.0%, outcome_reader_v1 0.0%, sampled_markov_v1 0.0%, anti_iocaine_v1 33.3%, double_bluff_gate_v2 40.0%, multiscale_council_v1 50.0%.

Weakest matchups of replay_hunter_wide_v2: nash_v1 50.0%, transition_matrix_v1 50.0%, counter_council_v1 50.0%, geometry_v1 50.0%, double_bluff_gate_v2 60.0%, smartbot_wide_v1 60.0%.

## Analysis

Scores vs the pool: l5_wide_hunter 91.5% (+54.6 rounds), replay_hunter_wide_v2 89.0% (+52.8), l5_hunter 88.2% (+55.5), l5_council 82.8%, l5_level_k 82.0%, l5_lean_hunter 71.8%, l5_priority 68.2%. The leanest and the priority gates lose most: dropping experts or forcing an order on them gives up matchups the L4 wins. l5_wide_hunter's weakest matchups are outcome_reader_v1 and sicilian_meta_v1 (0 of their matches) and leader_hunter_v2 (1 of 3), where the L4 has no such holes (its weakest are nash_v1, transition_matrix_v1, counter_council_v1 and geometry_v1 at 50%). If L5s are retried, l5_wide_hunter is the one, with a sharper test: head to head vs the L4 gates it replays, and vs variant pools (pool.variants), where note 0050 found l5_hunter about as strong as vs defaults.

## Verdict

**drop**. No L5 beats the best L4 vs random pools (10 round robins, the cap, 200 paired matches each): l5_wide_hunter - replay_hunter_wide_v2 = +2.5 pts [-2.5, +8.0] (the only one not worse), l5_hunter -0.8 [-6.5, +5.0], and four are significantly worse: l5_council -6.2 [-12.2, -0.2], l5_level_k -7.0 [-13.0, -1.2], l5_lean_hunter -17.2 [-23.8, -11.0], l5_priority -20.8 [-28.0, -13.5]. The fifth layer of replays costs time and doesn't pay at 200 rounds.
