# 0063: mirror_l1_bandit, iocaine_lite_v1 vs strong_l1_bandit

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #63
- **Candidates:** `bots/l2/mirror_l1_bandit.yaml`, `bots/l2/iocaine_lite_v1.yaml`
- **Baselines:** `bots/l2/strong_l1_bandit.yaml`
- **Run:** `20261013-142825_0063-mirror-l1-bandit-iocaine-lite-v1-vs-strong-l1-ba`
- **Verdict:** iterate

## Hypothesis

Theory prediction (theory/01-l1-heuristics.md, claim 6): an L2 holding the strong L1s and their mirror counters (mirror_l1_bandit) beats the same L2 without the counters (strong_l1_bandit) by >= 2 pts vs pools of L1s and L2s (250 rounds)

## Command

```bash
uv run janken lab experiment bots/l2/mirror_l1_bandit.yaml bots/l2/iocaine_lite_v1.yaml bots/l2/strong_l1_bandit.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 2004486911 --name 0063-mirror-l1-bandit-iocaine-lite-v1-vs-strong-l1-ba
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 2004486911, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| mirror_l1_bandit | 200 | 145-4-51 | 73.5% [67.0%, 79.1%] | +75.2 | 0 | 1727 +/- 66 |
| strong_l1_bandit | 200 | 141-1-58 | 70.8% [64.1%, 76.6%] | +67.0 | 0 | 1670 +/- 69 |
| iocaine_lite_v1 | 200 | 122-2-76 | 61.5% [54.6%, 68.0%] | +66.6 | 0 | 1582 +/- 88 |

Paired comparisons:

- `mirror_l1_bandit - iocaine_lite_v1 = +12.0 pts [+5.8, +18.8]` over 200 shared matches: mirror_l1_bandit better
- `mirror_l1_bandit - strong_l1_bandit = +2.8 pts [-4.0, +9.5]` over 200 shared matches: no significant difference
- `iocaine_lite_v1 - strong_l1_bandit = -9.2 pts [-16.5, -2.2]` over 200 shared matches: strong_l1_bandit better

Weakest matchups of mirror_l1_bandit: anti_iocaine_v1 0.0%, anti_rps4_v1 14.3%, anti_smartbot_v2 25.0%, outcome_reader_v1 25.0%, smartbot_fast_v1 33.3%, rps4_lite_v1 40.0%.

Weakest matchups of iocaine_lite_v1: anti_iocaine_v1 0.0%, anti_rps4_v1 0.0%, smartbot_fast_v1 0.0%, anti_smartbot_v2 0.0%, smartbot_v1 0.0%, fast_greedy_markov_v1 0.0%.

Weakest matchups of strong_l1_bandit: anti_iocaine_v1 0.0%, anti_smartbot_v2 0.0%, geometry_ensemble_v1 16.7%, smartbot_fast_v1 33.3%, smartbot_v1 40.0%, rps4_lite_v1 40.0%.

## Analysis

What separates them from iocaine_lite (longest_match from both seats plus frequency, every rotation) is the strong set's other members as arms: second_match and geometry. Their weakest matchups are the replay specialists of the L2 level (anti_iocaine_v1 0%, anti_rps4_v1, anti_smartbot_v2) and smartbot_fast: opponents that model them, which an L2 of L1 signals can't answer, the limit the L2 theory has to address next. The mirror counters' own value needs a sharper test: head to head vs pattern_memory and second_repeat, or a pool rich in them.

## Verdict

**iterate**. The theory's prediction is unresolved: mirror_l1_bandit (L1's strong set plus their mirror counters as arms) - strong_l1_bandit (the strong set alone) = +2.8 pts [-4.0, +9.5] over 200 paired matches in L1+L2 pools (10 round robins, 250 rounds). Both beat the L2 species iocaine_lite_v1, significantly: mirror_l1_bandit +12.0 pts [+5.8, +18.8], strong_l1_bandit +9.2 [+2.2, +16.5]; the first is confirmed on fresh seeds in note 0064.
