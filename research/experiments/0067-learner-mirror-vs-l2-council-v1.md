# 0067: learner_mirror vs l2_council_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #67
- **Candidates:** `bots/l3/learner_mirror.yaml`
- **Baselines:** `bots/l3/l2_council_v1.yaml`
- **Run:** `20261013-143946_0067-learner-mirror-vs-l2-council-v1`
- **Verdict:** drop

## Hypothesis

Iocaine's principle one level up: an L3 council of L2's strong learners read from both seats (each learner and its counter, every rotation) beats l2_council_v1 by >= 2 pts vs pools of L1-L3 bots, 250 rounds; the one-seat council lost to its own arms (note 0066)

## Command

```bash
uv run janken lab experiment bots/l3/learner_mirror.yaml bots/l3/l2_council_v1.yaml --rounds 250 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 3127081735 --name 0067-learner-mirror-vs-l2-council-v1
```

## Results

10 of 10 round robin(s), pool 20, 250 rounds/match, seed 3127081735, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| l2_council_v1 | 200 | 150-4-46 | 76.0% [69.6%, 81.4%] | +56.8 | 0 | 1722 +/- 73 |
| learner_mirror | 200 | 144-5-51 | 73.2% [66.7%, 78.9%] | +57.0 | 0 | 1719 +/- 66 |

Paired comparisons:

- `learner_mirror - l2_council_v1 = -2.8 pts [-10.8, +5.8]` over 200 shared matches: no significant difference

Weakest matchups of learner_mirror: transition_matrix_v1 0.0%, anti_smartbot_v2 0.0%, zoo_hunter_v1 0.0%, second_guess_v1 0.0%, gate_fast_hold_v1 16.7%, anti_rps4_v1 20.0%.

Weakest matchups of l2_council_v1: repeat_mirror_v1 0.0%, transition_matrix_v1 0.0%, nash_v1 33.3%, predator_v2 33.3%, period_bandit_v1 33.3%, second_repeat_v1 33.3%.

## Analysis

Three L3 councils built from L2's strong set (0065: with its counters; 0066: learners from our seat; this note: learners from both seats) all tie l2_council_v1 at 73-76% of matches. Each design closes one set of holes and opens another: the L3 level, judged vs mixed L1-L3 pools, is saturated around the same score, and the differences live in a handful of hard matchups that random pools can't weigh (the lesson of the hard-pool gauntlet, idea #60).

## Verdict

**drop**. Reading L2's strong learners from both seats doesn't lift the council: learner_mirror - l2_council_v1 = -2.8 pts [-10.8, +5.8] over 200 paired matches vs pools of L1-L3 (10 round robins, 250 rounds). It no longer loses to its own arms' species (geometry_ensemble, repeat_mirror left its weakest list), but loses instead to anti_smartbot_v2, transition_matrix_v1 and second_guess_v1.
