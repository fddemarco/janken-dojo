# 0092: l2_council_v1, multiscale_council_v1, repeat_mirror_v1, geometry_ensemble_v1, context_mixture_v2 vs smartbot_sims_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #85
- **Candidates:** `bots/l3/l2_council_v1.yaml`, `bots/l3/multiscale_council_v1.yaml`, `bots/l2/repeat_mirror_v1.yaml`, `bots/l2/geometry_ensemble_v1.yaml`, `bots/l1/context_mixture_v2.yaml`
- **Baselines:** `bots/l3/smartbot_sims_v2.yaml`
- **Run:** `20261013-185052_0092-mains-vs-outsiders`
- **Verdict:** drop

## Hypothesis

Against unknown L3-L4s the gate's main does the work (note 0091), so the best main differs from smartbot_sims_v2: some Thompson council (l2_council_v1, multiscale_council_v1) beats it by at least 5 pts vs the outsiders; the learners they replay (repeat_mirror, CTW) lose

## Command

```bash
uv run janken lab experiment bots/l3/l2_council_v1.yaml bots/l3/multiscale_council_v1.yaml bots/l2/repeat_mirror_v1.yaml bots/l2/geometry_ensemble_v1.yaml bots/l1/context_mixture_v2.yaml bots/l3/smartbot_sims_v2.yaml --rounds 250 --round-robins 120 --pool-size 3 --mode candidates --no-allow-small-pool --no-mocks --pool-list research/gauntlet/outsiders.txt --seed 165958001 --name 0092-mains-vs-outsiders
```

## Results

120 of 120 round robin(s), pool 3, 250 rounds/match, seed 165958001, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| l2_council_v1 | 360 | 219-6-135 | 61.7% [56.5%, 66.5%] | +3.2 | 0 | 1600 +/- 143 |
| smartbot_sims_v2 | 360 | 211-17-132 | 61.0% [55.8%, 65.9%] | +3.9 | 0 | 1641 +/- 122 |
| multiscale_council_v1 | 360 | 193-8-159 | 54.7% [49.6%, 59.8%] | +1.2 | 0 | 1562 +/- 123 |
| geometry_ensemble_v1 | 360 | 176-17-167 | 51.2% [46.1%, 56.4%] | -0.5 | 0 | 1515 +/- 136 |
| repeat_mirror_v1 | 360 | 62-5-293 | 17.9% [14.3%, 22.2%] | -64.8 | 0 | 1417 +/- 93 |
| context_mixture_v2 | 360 | 0-0-360 | 0.0% [0.0%, 1.1%] | -245.7 | 0 | 1103 +/- 30 |

Paired comparisons:

- `l2_council_v1 - multiscale_council_v1 = +6.9 pts [-0.1, +14.3]` over 360 shared matches: no significant difference
- `l2_council_v1 - repeat_mirror_v1 = +43.8 pts [+37.1, +50.1]` over 360 shared matches: l2_council_v1 better
- `l2_council_v1 - geometry_ensemble_v1 = +10.4 pts [+3.5, +17.4]` over 360 shared matches: l2_council_v1 better
- `l2_council_v1 - context_mixture_v2 = +61.7 pts [+56.7, +66.7]` over 360 shared matches: l2_council_v1 better
- `l2_council_v1 - smartbot_sims_v2 = +0.7 pts [-6.1, +7.6]` over 360 shared matches: no significant difference
- `multiscale_council_v1 - repeat_mirror_v1 = +36.8 pts [+30.0, +43.6]` over 360 shared matches: multiscale_council_v1 better
- `multiscale_council_v1 - geometry_ensemble_v1 = +3.5 pts [-3.9, +11.0]` over 360 shared matches: no significant difference
- `multiscale_council_v1 - context_mixture_v2 = +54.7 pts [+49.6, +59.9]` over 360 shared matches: multiscale_council_v1 better
- `multiscale_council_v1 - smartbot_sims_v2 = -6.2 pts [-13.2, +0.7]` over 360 shared matches: no significant difference
- `repeat_mirror_v1 - geometry_ensemble_v1 = -33.3 pts [-39.9, -26.8]` over 360 shared matches: geometry_ensemble_v1 better
- `repeat_mirror_v1 - context_mixture_v2 = +17.9 pts [+14.0, +21.9]` over 360 shared matches: repeat_mirror_v1 better
- `repeat_mirror_v1 - smartbot_sims_v2 = -43.1 pts [-49.2, -36.4]` over 360 shared matches: smartbot_sims_v2 better
- `geometry_ensemble_v1 - context_mixture_v2 = +51.2 pts [+46.4, +56.2]` over 360 shared matches: geometry_ensemble_v1 better
- `geometry_ensemble_v1 - smartbot_sims_v2 = -9.7 pts [-16.9, -2.8]` over 360 shared matches: smartbot_sims_v2 better
- `context_mixture_v2 - smartbot_sims_v2 = -61.0 pts [-65.8, -55.8]` over 360 shared matches: smartbot_sims_v2 better

Weakest matchups of l2_council_v1: outsider_greedy 55.8%, outsider_council 59.2%, outsider_gate 70.0%.

Weakest matchups of multiscale_council_v1: outsider_council 50.8%, outsider_greedy 52.9%, outsider_gate 60.4%.

Weakest matchups of repeat_mirror_v1: outsider_gate 0.0%, outsider_greedy 0.0%, outsider_council 53.8%.

Weakest matchups of geometry_ensemble_v1: outsider_greedy 41.7%, outsider_council 43.8%, outsider_gate 68.3%.

Weakest matchups of context_mixture_v2: outsider_greedy 0.0%, outsider_gate 0.0%, outsider_council 0.0%.

Weakest matchups of smartbot_sims_v2: outsider_gate 49.6%, outsider_council 63.3%, outsider_greedy 70.0%.

## Analysis

-

## Verdict

**drop**. No main beats smartbot_sims_v2 vs the outsiders: l2_council_v1 61.7% of matches vs 61.0% (+3.2 vs +3.9 rounds), multiscale_council_v1 54.7%, geometry_ensemble_v1 51.2%. The deterministic learners the outsiders are built from are read exactly: repeat_mirror_v1 17.9% (-64.8 rounds), context_mixture_v2 0% (-245.7 rounds, the outsiders hold its BEAT_BEAT counter). A Thompson main is the robust choice vs unknowns.
