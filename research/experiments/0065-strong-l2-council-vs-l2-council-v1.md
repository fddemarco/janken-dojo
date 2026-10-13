# 0065: strong_l2_council vs l2_council_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #66
- **Candidates:** `bots/l3/strong_l2_council.yaml`
- **Baselines:** `bots/l3/l2_council_v1.yaml`
- **Run:** `20261013-143407_0065-strong-l2-council-vs-l2-council-v1`
- **Verdict:** drop

## Hypothesis

Theory prediction one level up (theory/02-meta-strategies.md, claim 1): an L3 council of L2's strong set (geometry_ensemble, period_bandit, anti_smartbot, anti_rps4; L2 atlas) beats l2_council_v1 (a council of smartbot, smartbot_fast, iocaine, rps4) by >= 2 pts vs pools of L1-L3 bots, 250 rounds

## Command

```bash
uv run janken lab experiment bots/l3/strong_l2_council.yaml bots/l3/l2_council_v1.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 20069459 --name 0065-strong-l2-council-vs-l2-council-v1
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 20069459, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| l2_council_v1 | 200 | 154-2-44 | 77.5% [71.2%, 82.7%] | +59.0 | 0 | 1746 +/- 111 |
| strong_l2_council | 200 | 146-4-50 | 74.0% [67.5%, 79.6%] | +51.2 | 0 | 1715 +/- 73 |

Paired comparisons:

- `strong_l2_council - l2_council_v1 = -3.5 pts [-11.5, +4.8]` over 200 shared matches: no significant difference

Weakest matchups of strong_l2_council: repeat_mirror_v1 0.0%, anti_rps4_v1 0.0%, sampled_markov_v1 0.0%, multiscale_council_v1 25.0%, smartbot_fast_v1 25.0%, nash_v1 30.0%.

Weakest matchups of l2_council_v1: dropswitch_matcher_v1 0.0%, counter_council_v1 0.0%, sicilian_meta_v1 0.0%, predator_v2 25.0%, geometry_v1 33.3%, leader_new_l2_v1 33.3%.

## Analysis

Weakest matchups: repeat_mirror_v1, anti_rps4_v1 and sampled_markov_v1 (0% of matches), multiscale_council_v1 and smartbot_fast_v1 (25%), nash_v1 (30%). The council loses to one of its own arms' species (anti_rps4) and to the L2 built from L1's strong set. Refinement for the theory: a level's strong set made of learners (L1: the repeat followers and geometry) transfers to the next level; one made of counters is a property of the pool it was measured in, and transfers only to pools rich in their prey.

## Verdict

**drop**. The theory's prediction fails one level up: strong_l2_council (a Thompson council of L2's strong set: geometry_ensemble, period_bandit, anti_smartbot, anti_rps4, every rotation) - l2_council_v1 = -3.5 pts [-11.5, +4.8] over 200 paired matches vs pools of L1-L3 bots (10 round robins, 250 rounds). Half of L2's strong set are counters (anti_smartbot, anti_rps4), strong in the L2 round robin because their prey (smartbot-like and rps4-like L2s) fill it, and weak as arms in a mixed pool.
