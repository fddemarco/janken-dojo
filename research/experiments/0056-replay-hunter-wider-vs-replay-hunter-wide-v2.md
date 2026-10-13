# 0056: replay_hunter_wider vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #45
- **Candidates:** `bots/l4/replay_hunter_wider.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-135246_0056-replay-hunter-wider-vs-replay-hunter-wide-v2`
- **Verdict:** iterate

## Hypothesis

replay_hunter_wider beats replay_hunter_wide_v2 by >= 2 pts vs random pools: its new experts (replays of geometry_ensemble, leader_hunter, period_detector, sicilian_meta, and frequency_v1 from our seat) cover learners and fixed distributions the L4 scores near 0 against (idea #45)

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_wider.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 200 --round-robins 10 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 1500543587 --name 0056-replay-hunter-wider-vs-replay-hunter-wide-v2
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 1500543587, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wider | 200 | 179-1-20 | 89.8% [84.8%, 93.2%] | +55.9 | 0 | 1856 +/- 73 |
| replay_hunter_wide_v2 | 200 | 170-3-27 | 85.8% [80.2%, 89.9%] | +51.8 | 0 | 1820 +/- 64 |

Paired comparisons:

- `replay_hunter_wider - replay_hunter_wide_v2 = +4.0 pts [-1.8, +10.0]` over 200 shared matches: no significant difference

Weakest matchups of replay_hunter_wider: l5_wide_hunter 0.0%, multiscale_council_v1 0.0%, l5_hunter 50.0%, anti_iocaine_v1 50.0%, replay_hunter_gate_v2 50.0%, second_guess_v1 50.0%.

Weakest matchups of replay_hunter_wide_v2: l5_hunter 0.0%, outcome_reader_v1 0.0%, replay_hunter_gate_v2 0.0%, geometry_v1 0.0%, l5_wide_hunter 33.3%, sampled_markov_v1 33.3%.

## Analysis

Scores vs the pool: replay_hunter_wider 89.8% (+55.9 rounds per match), replay_hunter_wide_v2 85.8% (+51.8). The new experts' targets left the weakest list: the L4's 0% matchups vs outcome_reader_v1 and geometry_v1 and 33% vs sampled_markov_v1 are gone from replay_hunter_wider's, whose weakest are now l5_wide_hunter, multiscale_council_v1 (0 of their matches), l5_hunter, anti_iocaine_v1, replay_hunter_gate_v2 and second_guess_v1 (half). Five experts more (period_detector as a Sim, sicilian_meta at its best arm, frequency_v1 from our seat), no measurable cost elsewhere.

## Verdict

**iterate**. replay_hunter_wider - replay_hunter_wide_v2 = +4.0 pts [-1.8, +10.0] over 200 paired matches (10 round robins, the cap), +4.0 rounds per match +- 4.3: positive all the way up the ladder (+5.0, +6.0, +4.6, +4.0) but unresolved at 10 round robins, whose CI (+-6 pts) can't settle a 4 pt effect. Next: the same comparison at the thorough budget (40 round robins, +-3 pts) on fresh seeds.
