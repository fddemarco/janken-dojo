# 0031: counter to anti_smartbot_sims: gated and bare, vs smartbot_sims_v2 (whole field, 250 rounds)

- **Date:** 2026-10-12
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #37
- **Candidates:** `bots/l4/gate_counter_sims.yaml`, `bots/l3/counter_anti_sims.yaml`
- **Baselines:** `bots/l3/smartbot_sims_v2.yaml`
- **Run:** `20261012-144707_0031-counter-anti-sims-vs-smartbot-sims`
- **Verdict:** keep
- **Species:** `double_bluff_gate_v1` (new species)

## Hypothesis

Head to head, both candidates win >= 36% of rounds vs anti_smartbot_sims_v2 in every match (250 rounds) and win every match (scratch probe over seeds 1-200: gated 69.1%, bare 73.3% of rounds), where smartbot_sims_v2 wins ~29%. Over the whole field (anti_smartbot_sims_v2 in every round robin), gate_counter_sims - smartbot_sims_v2 >= 0 pts (the gated expert costs nothing elsewhere and wins the anti_smartbot_sims match); counter_anti_sims - smartbot_sims_v2 far below 0 (a pure specialist).

## Command

```bash
uv run janken lab experiment bots/l4/gate_counter_sims.yaml bots/l3/counter_anti_sims.yaml bots/l3/smartbot_sims_v2.yaml --rounds 250 --round-robins 5 --pool-size 60 --mode candidates --allow-small-pool --no-mocks --seed 3404695743 --name 0031-counter-anti-sims-vs-smartbot-sims
```

## Results

5 of 5 round robin(s), pool 60, 250 rounds/match, seed 3404695743, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| gate_counter_sims | 300 | 217-3-80 | 72.8% [67.5%, 77.6%] | +50.7 | 0 | 1725 +/- 62 |
| smartbot_sims_v2 | 300 | 188-7-105 | 63.8% [58.3%, 69.1%] | +47.5 | 0 | 1647 +/- 44 |
| counter_anti_sims | 300 | 72-8-220 | 25.3% [20.7%, 30.5%] | -11.3 | 0 | 1244 +/- 57 |

Paired comparisons:

- `gate_counter_sims - counter_anti_sims = +47.5 pts [+41.2, +53.7]` over 300 shared matches: gate_counter_sims better
- `gate_counter_sims - smartbot_sims_v2 = +9.0 pts [+2.3, +15.7]` over 300 shared matches: gate_counter_sims better
- `counter_anti_sims - smartbot_sims_v2 = -38.5 pts [-45.7, -31.2]` over 300 shared matches: smartbot_sims_v2 better

Weakest matchups of gate_counter_sims: bayes_predators_v1 20.0%, sicilian_meta_v1 20.0%, dropswitch_council_v1 20.0%, transition_matrix_v1 20.0%, second_guess_v1 20.0%, l2_council_v1 30.0%.

Weakest matchups of counter_anti_sims: predator_v1 0.0%, counter_council_v1 0.0%, gate_main_first_v2 0.0%, geometry_ensemble_v1 0.0%, gate_main_first_stationary_v2 0.0%, rotation_outcome_v1 0.0%.

Weakest matchups of smartbot_sims_v2: anti_smartbot_sims_v2 0.0%, gate_main_first_v2 0.0%, gate_main_first_stationary_v2 0.0%, gate_edge_v2 0.0%, counter_council_v1 0.0%, predator_v1 0.0%.

## Analysis

Mechanism: anti_smartbot_sims_v2 plays the beat of the mode of 256 Thompson draws over a replay of smartbot_sims_v2 in our seat; the mode is nearly deterministic, so our own replay of smartbot_sims_v2 from our side (draws 256, with our own random stream since the per-side RNG fix 1d3b9b7) names the same move X most rounds, and BEAT_BEAT plays beat(beat(X)). The ~14-17% of rounds lost are rounds where the two 256-draw modes disagree (near-ties among smartbot_sims's arms). The gate costs about 3 points of round share vs the bare counter against the target (68.4% vs 71.7%: the first WARMUP=20 rounds and EDGE checks run on smartbot_sims's main bandit) but turns a specialist (25.3% vs the field) into the best bot of the run (72.8% vs 63.8% for smartbot_sims_v2). In the run, every match vs anti_smartbot_sims_v2 went to the candidates: gated 165-176 of 250 rounds (5/5), bare 169-186 (5/5), smartbot_sims_v2 62-73 (0/5). The rest of the gain over smartbot_sims_v2 is spread: its weakest matchups at 5 round robins are bayes_predators_v1, sicilian_meta_v1, dropswitch_council_v1, transition_matrix_v1, second_guess_v1 (20% each, 1 of 5) and l2_council_v1 (30%), all small samples. The 36-40% goal is cleared by both counters with a wide margin.

## Verdict

**keep**. gate_counter_sims beats smartbot_sims_v2 over the whole field, +9.0 pts [+2.3, +15.7] over 300 paired matches (5 round robins of the 60-bot field, 250 rounds, mode candidates; the round-robin ladder was inconclusive at 1 and 3, conclusive at 5), and beats anti_smartbot_sims_v2 head to head in every match: 68.4% of rounds [66.9%, 69.8%] over seeds 1-10 (worst match 66.0%, 10/10 matches; the seed ladder was conclusive vs the 36% goal at its first step), where smartbot_sims_v2 wins 28.9% [27.7%, 30.0%] and 0/10. The bare counter_anti_sims wins 71.7% [69.1%, 74.3%] of rounds vs anti_smartbot_sims_v2 (10/10) but is a pure specialist: -38.5 pts [-45.7, -31.2] vs smartbot_sims_v2 over the field.

## Species

**new**: its core agrees with gate_main_first_stationary_v2 on 66% of the moves, below 80%.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `gate_main_first_stationary_v2` | L4 | 65.7% |
| `gate_main_first_v2` | L4 | 65.5% |
| `gate_edge_v2` | L4 | 60.2% |
