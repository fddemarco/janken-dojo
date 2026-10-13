# 0040: level_k_gate_normal vs level_k_gate_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #50
- **Candidates:** `bots/l4/level_k_gate_normal.yaml`
- **Baselines:** `bots/l4/level_k_gate_v1.yaml`
- **Run:** `20261013-022209_0040-level-k-gate-normal`
- **Verdict:** keep
- **Species run:** `20261013-032007_species-0040`
- **Species:** `level_k_gate_v2` (promoted over `level_k_gate_v1`)

## Hypothesis

level_k_gate_normal plays as well as level_k_gate_v1 (paired difference within +/-3 pts) at a fraction of its time: its replays compute the likely move (estimate NORMAL) instead of drawing it 256 times

## Command

```bash
uv run janken lab experiment bots/l4/level_k_gate_normal.yaml bots/l4/level_k_gate_v1.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 2956724662 --name 0040-level-k-gate-normal
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 2956724662, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| level_k_gate_v1 | 200 | 146-2-52 | 73.5% [67.0%, 79.1%] | +35.3 | 0 | 1701 +/- 72 |
| level_k_gate_normal | 200 | 138-5-57 | 70.2% [63.6%, 76.2%] | +33.1 | 0 | 1690 +/- 76 |

Paired comparisons:

- `level_k_gate_normal - level_k_gate_v1 = -3.2 pts [-10.2, +3.2]` over 200 shared matches: no significant difference

Weakest matchups of level_k_gate_normal: l5_council 0.0%, dropswitch_council_v1 0.0%, l5_wide_hunter 0.0%, replay_hunter_gate_v1 0.0%, replay_hunter_gate_normal 0.0%, l5_lean_hunter 0.0%.

Weakest matchups of level_k_gate_v1: dropswitch_council_v1 0.0%, sicilian_meta_v1 0.0%, replay_hunter_gate_v1 0.0%, l5_lean_hunter 0.0%, l5_wide_hunter 0.0%, backoff_family_v1 0.0%.

## Analysis

-

## Verdict

**keep**. No significant difference at 10 round robins: level_k_gate_normal - level_k_gate_v1 = -3.2 pts [-10.2, +3.2] over 200 shared matches: no significant difference. The copy computes its replays' likely move (estimate NORMAL) instead of drawing it 256 times, which in a 40-seed check of anti_smartbot_sims played about 12x faster and named the same move as 2048 draws in 98% of rounds. Kept as equal and cheaper; classify decides from this paired run (species.promote_on_evaluation).

## Species

**promote**: alike level_k_gate_v1: agreement 82%, profile correlation +0.87; better on no matchup at alpha 0.05 / 47, worse on none, and 14.2x faster.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `level_k_gate_v1` | L4 | 81.6% |
| `replay_hunter_gate_v1` | L4 | 75.0% |
| `gate_main_first_v2` | L4 | 74.3% |
| `replay_hunter_wide_v1` | L4 | 74.2% |
| `gate_main_first_stationary_v2` | L4 | 74.1% |

Paired run `20261013-032007_species-0040`: profile correlation +0.87. Self-play speed: 14.25x the incumbent's. Challenger minus incumbent, per matchup (points; the strict bound is the Bonferroni test for 'better'):

| opponent | n | diff | 95% CI | strict lower bound | |
|---|---|---|---|---|---|
| replay_hunter_wide_normal | 12 | -33.3 | [-66.7, +0.0] | -83.3 | |
| multiscale_council_v1 | 11 | -27.3 | [-63.6, +9.1] | -81.8 | |
| dropswitch_council_v1 | 12 | -25.0 | [-58.3, +8.3] | -75.0 | |
| vote_council_v1 | 14 | -25.0 | [-53.6, +3.6] | -71.4 | |
| anti_rps4_v1 | 11 | -18.2 | [-54.5, +18.2] | -72.7 | |
| naive_bayes_markov_v1 | 13 | -15.4 | [-38.5, +0.0] | -53.8 | |
| geometry_v1 | 10 | -15.0 | [-55.0, +25.0] | -75.0 | |
| second_guess_v1 | 14 | -14.3 | [-42.9, +14.3] | -57.1 | |
| l2_council_v1 | 10 | -10.0 | [-40.0, +20.0] | -60.0 | |
| sims_lite_v1 | 10 | -10.0 | [-30.0, +0.0] | -50.0 | |
| gate_edge_normal | 11 | -9.1 | [-27.3, +0.0] | -45.5 | |
| bayes_predators_v1 | 12 | -8.3 | [-50.0, +33.3] | -75.0 | |
| gate_edge_smartbot_v1 | 12 | -8.3 | [-25.0, +0.0] | -41.7 | |
| l5_council | 15 | -6.7 | [-26.7, +13.3] | -46.7 | |
| anti_frequency_v1 | 11 | +0.0 | [+0.0, +0.0] | +0.0 | |
| anti_smartbot_sims_v2 | 14 | +0.0 | [+0.0, +0.0] | +0.0 | |
| anti_smartbot_v1 | 13 | +0.0 | [+0.0, +0.0] | +0.0 | |
| balancer_hunter_v1 | 14 | +0.0 | [+0.0, +0.0] | +0.0 | |
| counter_reactionary_v1 | 10 | +0.0 | [+0.0, +0.0] | +0.0 | |
| cycler_v1 | 10 | +0.0 | [+0.0, +0.0] | +0.0 | |
| gate_edge_v2 | 12 | +0.0 | [+0.0, +0.0] | +0.0 | |
| gate_leader_v1 | 12 | +0.0 | [+0.0, +0.0] | +0.0 | |
| gate_main_first_v2 | 14 | +0.0 | [-21.4, +21.4] | -35.7 | |
| leader_hunter_v1 | 11 | +0.0 | [-36.4, +36.4] | -57.8 | |
| outcome_reader_v1 | 11 | +0.0 | [+0.0, +0.0] | +0.0 | |
| pattern_memory_v1 | 11 | +0.0 | [+0.0, +0.0] | +0.0 | |
| score_reader_v1 | 12 | +0.0 | [+0.0, +0.0] | +0.0 | |
| self_beater_v1 | 10 | +0.0 | [+0.0, +0.0] | +0.0 | |
| smartbot_sims_v2 | 10 | +0.0 | [-30.0, +30.0] | -50.0 | |
| vote_ensemble_v1 | 14 | +0.0 | [+0.0, +0.0] | +0.0 | |
| wsls_v1 | 10 | +0.0 | [+0.0, +0.0] | +0.0 | |
| replay_hunter_wide_v1 | 13 | +3.8 | [-19.2, +26.9] | -34.6 | |
| smartbot_wide_v1 | 13 | +3.8 | [-26.9, +34.6] | -46.2 | |
| (head-to-head) | 40 | +6.2 | [-9.0, +20.4] | -17.9 | |
| l5_level_k | 14 | +7.1 | [+0.0, +21.4] | +0.0 | |
| predator_v1 | 12 | +8.3 | [-33.3, +50.0] | -58.3 | |
| gate_main_first_normal | 10 | +10.0 | [+0.0, +30.0] | +0.0 | |
| l5_lean_hunter | 10 | +10.0 | [+0.0, +30.0] | +0.0 | |
| l5_wide_hunter | 10 | +10.0 | [-10.0, +35.0] | -20.0 | |
| fast_greedy_markov_v1 | 14 | +10.7 | [-32.1, +50.0] | -57.1 | |
| multiscale_v1 | 10 | +20.0 | [-20.0, +60.0] | -40.0 | |
| replay_hunter_gate_v1 | 10 | +20.0 | [+0.0, +50.0] | +0.0 | |
| zoo_hunter_v1 | 15 | +20.0 | [+0.0, +40.0] | +0.0 | |
| backoff_family_v1 | 14 | +21.4 | [-21.4, +57.1] | -50.0 | |
| leader_hunter_normal | 12 | +25.0 | [-16.7, +66.7] | -41.7 | |
| gate_main_first_stationary_normal | 11 | +27.3 | [+0.0, +54.5] | +0.0 | |
| gate_bandit_period_v1 | 10 | +40.0 | [+0.0, +80.0] | -30.0 | |
