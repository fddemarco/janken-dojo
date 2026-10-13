# 0058: replay_hunter_wide_v2 vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #59
- **Candidates:** `bots/l4/replay_hunter_wide_v2.yaml:GATE_DECAY=0.85`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-140044_0058-replay-hunter-wide-v2-vs-replay-hunter-wide-v2`
- **Verdict:** iterate

## Hypothesis

replay_hunter_wide_v2 with a forgetful gate (GATE_DECAY 0.85, other knobs at defaults) is no worse than its defaults vs random pools (paired difference above -2 pts): head to head it lifts double_bluff_gate_v2 from 33.6% to 36.7% of rounds (25 seeds, 250 rounds), and note 0054's only forgetful trial also had a 0.29 edge

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_wide_v2.yaml:GATE_DECAY=0.85 bots/l4/replay_hunter_wide_v2.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 2300653536 --name 0058-replay-hunter-wide-v2-vs-replay-hunter-wide-v2
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 2300653536, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide_v2@5e5ca3 | 200 | 171-6-23 | 87.0% [81.6%, 91.0%] | +45.6 | 0 | 1836 +/- 83 |
| replay_hunter_wide_v2 | 200 | 165-0-35 | 82.5% [76.6%, 87.1%] | +47.1 | 0 | 1786 +/- 115 |

Paired comparisons:

- `replay_hunter_wide_v2@5e5ca3 - replay_hunter_wide_v2 = +4.5 pts [-1.2, +10.5]` over 200 shared matches: no significant difference

Weakest matchups of replay_hunter_wide_v2@5e5ca3: l5_hunter 0.0%, l5_wide_hunter 0.0%, gate_bandit_period_v2 33.3%, nash_v1 50.0%, second_guess_v1 50.0%, gate_main_first_backoff_v1 60.0%.

Weakest matchups of replay_hunter_wide_v2: l5_wide_hunter 0.0%, geometry_v1 0.0%, anti_iocaine_v1 0.0%, nash_v1 0.0%, l5_hunter 25.0%, l2_council_v1 33.3%.

## Analysis

Scores: 87.0% (+45.6 rounds per match) vs 82.5% (+47.1); more matches won, slightly smaller margins, as a gate that hands over sooner trades some blow-outs for fewer losses. Its weakest matchups lose geometry_v1, anti_iocaine_v1 and nash_v1's 0% (the defaults' holes) and gain gate_bandit_period_v2 at 33%. Note 0054's tuning never validated this point: its one forgetful configuration (trial 3) also demanded a 0.29 edge and lost 8.8 pts, so it was the edge, not the decay, that cost.

## Verdict

**iterate**. A forgetful gate is no worse and maybe better: replay_hunter_wide_v2 at GATE_DECAY 0.85 minus its defaults = +4.5 pts [-1.2, +10.5] over 200 paired matches (10 round robins), above the -2 pt non-inferiority margin; head to head it lifts double_bluff_gate_v2 from 33.6% [32.4, 34.8] to 36.7% [35.4, 37.9] of rounds (25 seeds, 250 rounds; GATE_DECAY 0.7: 36.6%). A +4.5 lead at the cap usually shrinks (insight of 2026-10-13), so it is confirmed at the thorough budget before a bot is made of it.
