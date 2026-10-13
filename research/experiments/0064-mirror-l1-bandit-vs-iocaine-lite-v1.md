# 0064: mirror_l1_bandit vs iocaine_lite_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #63
- **Candidates:** `bots/l2/mirror_l1_bandit.yaml`
- **Baselines:** `bots/l2/iocaine_lite_v1.yaml`
- **Run:** `20261013-142910_0064-mirror-l1-bandit-vs-iocaine-lite-v1`
- **Verdict:** keep
- **Species:** `repeat_mirror_v1` (new species)

## Hypothesis

Confirmation on fresh seeds at the thorough budget: mirror_l1_bandit (L1's strong set and their mirror counters, every rotation) beats iocaine_lite_v1 by >= 2 pts vs pools of L1s and L2s, 250 rounds (first run: +12.0 pts [+5.8, +18.8])

## Command

```bash
uv run janken lab experiment bots/l2/mirror_l1_bandit.yaml bots/l2/iocaine_lite_v1.yaml --rounds 250 --round-robins 24 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 2817200584 --name 0064-mirror-l1-bandit-vs-iocaine-lite-v1
```

## Results

24 of 24 round robin(s), pool 20, 250 rounds/match, seed 2817200584, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| mirror_l1_bandit | 480 | 330-12-138 | 70.0% [65.8%, 73.9%] | +65.5 | 0 | 1692 +/- 99 |
| iocaine_lite_v1 | 480 | 297-8-175 | 62.7% [58.3%, 66.9%] | +56.0 | 0 | 1601 +/- 87 |

Paired comparisons:

- `mirror_l1_bandit - iocaine_lite_v1 = +7.3 pts [+3.0, +11.6]` over 480 shared matches: mirror_l1_bandit better

Weakest matchups of mirror_l1_bandit: anti_iocaine_v1 11.8%, anti_rps4_v1 18.8%, anti_smartbot_v2 22.2%, mirror_bandit_v1 27.8%, fast_greedy_markov_v1 30.8%, multiscale_v1 36.4%.

Weakest matchups of iocaine_lite_v1: anti_iocaine_v1 0.0%, anti_rps4_v1 0.0%, anti_smartbot_v2 0.0%, smartbot_fast_v1 0.0%, dropswitch_matcher_v1 13.6%, fast_greedy_markov_v1 15.4%.

## Analysis

The first run's +12.0 (note 0063) settled to +7.3, the shrinkage the insight of 2026-10-13 on 10-round-robin leads predicts, but the CI stays clear of 0. Core agreement with iocaine_lite_v1 is 77% (below the 80% species bar), so it is classified as a new species, not iocaine's next version, which would also have forced new versions of the eight field bots that name iocaine_lite_v1.

## Verdict

**keep**. Confirmed on fresh seeds: mirror_l1_bandit - iocaine_lite_v1 = +7.3 pts [+3.0, +11.6] over 480 paired matches in pools of L1s and L2s (24 round robins at the thorough budget, 250 rounds; the sequential test cleared at look 3), 70.0% of matches vs 62.7%. An L2 built from L1's strong set (both repeat followers from both seats, and geometry, every rotation) beats the field's iocaine-style L2.

## Species

**new**: its core agrees with iocaine_lite_v1 on 77% of the moves, below 80%.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `iocaine_lite_v1` | L2 | 77.2% |
| `rps4_lite_v1` | L2 | 66.9% |
| `dropswitch_matcher_v1` | L2 | 64.9% |
| `backoff_family_v1` | L2 | 64.6% |
| `geometry_ensemble_v1` | L2 | 63.9% |
