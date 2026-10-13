# 0062: anti_pattern, anti_second_repeat vs pattern_memory_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #65
- **Candidates:** `bots/l1/anti_pattern.yaml`, `bots/l1/anti_second_repeat.yaml`
- **Baselines:** `bots/l1/pattern_memory_v1.yaml`
- **Run:** `20261013-142536_0062-anti-pattern-anti-second-repeat-vs-pattern-memor`
- **Verdict:** drop

## Hypothesis

The strong L1s fall to an L1 mirror counter (their own rule on our moves, turned BEAT_BEAT): head to head anti_pattern and anti_second_repeat win > 40% of rounds vs pattern_memory_v1 and second_repeat_v1 (measured: 94.7% and 95.0%, 10 seeds); as specialists they score below pattern_memory_v1 in an L1 pool (idea #65)

## Command

```bash
uv run janken lab experiment bots/l1/anti_pattern.yaml bots/l1/anti_second_repeat.yaml bots/l1/pattern_memory_v1.yaml --rounds 250 --round-robins 10 --pool-size 19 --mode candidates --allow-small-pool --no-mocks --seed 2181550167 --name 0062-anti-pattern-anti-second-repeat-vs-pattern-memor
```

## Results

10 of 10 round robin(s), pool 19, 250 rounds/match, seed 2181550167, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| pattern_memory_v1 | 190 | 168-1-21 | 88.7% [83.4%, 92.4%] | +113.3 | 0 | 1793 +/- 50 |
| anti_second_repeat | 190 | 115-8-67 | 62.6% [55.6%, 69.2%] | +16.7 | 0 | 1634 +/- 81 |
| anti_pattern | 190 | 114-6-70 | 61.6% [54.5%, 68.2%] | -2.5 | 0 | 1607 +/- 74 |

Paired comparisons:

- `anti_pattern - anti_second_repeat = -1.1 pts [-8.9, +6.8]` over 190 shared matches: no significant difference
- `anti_pattern - pattern_memory_v1 = -27.1 pts [-34.5, -20.3]` over 190 shared matches: pattern_memory_v1 better
- `anti_second_repeat - pattern_memory_v1 = -26.1 pts [-33.7, -17.9]` over 190 shared matches: pattern_memory_v1 better

Weakest matchups of anti_pattern: geometry_v1 0.0%, balancer_hunter_v1 20.0%, biased_v1 30.0%, copycat_v1 35.0%, self_beater_v1 35.0%, anti_frequency_v1 40.0%.

Weakest matchups of anti_second_repeat: geometry_v1 30.0%, copycat_v1 35.0%, anti_frequency_v1 35.0%, rock_v1 35.0%, nash_v1 40.0%, self_beater_v1 40.0%.

Weakest matchups of pattern_memory_v1: geometry_v1 40.0%, nash_v1 50.0%, second_repeat_v1 50.0%, period_detector_v1 70.0%, transition_matrix_v1 85.0%, biased_v1 90.0%.

## Analysis

Each counter is narrow: anti_pattern vs second_repeat_v1 mostly draws (1.8% won, 2.7% lost: both name the same move), anti_second_repeat vs pattern_memory_v1 wins only 34.5% of rounds. Vs the rest of the L1 pool they score 61.6-62.6% of matches, weakest vs geometry_v1 (0-30%), balancer_hunter, biased and copycat: a mirror counter has no defence of its own. So at L1 the strong set is countered one by one, each counter is useless elsewhere: exactly the condition where a level above should hold the counters as arms and choose between them (theory/README.md: few strong strategies --> specialise).

## Verdict

**drop**. The strong L1s fall to an L1 mirror counter, as hypothesised: head to head, anti_pattern (LongestMatch of our own moves, BEAT_BEAT) wins 94.7% of rounds [94.1, 95.3] vs pattern_memory_v1 and anti_second_repeat 95.0% [94.6, 95.5] vs second_repeat_v1 (10 seeds, 250 rounds, 10 of 10 matches each). As field bots they are specialists: anti_pattern - pattern_memory_v1 = -27.1 pts [-34.5, -20.3] and anti_second_repeat -26.1 [-33.7, -17.9] in an L1 pool (190 paired matches). Dropped from the field; the counter lives on as an arm of the existing blocks ({bot: longest_match / second_match, space: {OF: MY}, rotations: [BEAT_BEAT]}).
