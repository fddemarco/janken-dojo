# 0059: replay_hunter_wide_v2 vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #59
- **Candidates:** `bots/l4/replay_hunter_wide_v2.yaml:GATE_DECAY=0.85`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-140236_0059-replay-hunter-wide-v2-vs-replay-hunter-wide-v2`
- **Verdict:** drop

## Hypothesis

Confirmation of note 0058 at the thorough budget on fresh seeds: replay_hunter_wide_v2 at GATE_DECAY 0.85 beats its defaults by >= 2 pts vs random pools (0058: +4.5 pts [-1.2, +10.5])

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_wide_v2.yaml:GATE_DECAY=0.85 bots/l4/replay_hunter_wide_v2.yaml --rounds 200 --round-robins 16 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 3289686443 --name 0059-replay-hunter-wide-v2-vs-replay-hunter-wide-v2
```

## Results

16 of 16 round robin(s), pool 20, 200 rounds/match, seed 3289686443, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide_v2 | 320 | 274-5-41 | 86.4% [82.2%, 89.7%] | +49.8 | 0 | 1818 +/- 63 |
| replay_hunter_wide_v2@5e5ca3 | 320 | 274-4-42 | 86.2% [82.0%, 89.6%] | +49.6 | 0 | 1833 +/- 76 |

Paired comparisons:

- `replay_hunter_wide_v2@5e5ca3 - replay_hunter_wide_v2 = -0.2 pts [-4.7, +4.4]` over 320 shared matches: no significant difference

Weakest matchups of replay_hunter_wide_v2@5e5ca3: l5_hunter 25.0%, multiscale_council_v1 30.0%, second_guess_v1 33.3%, transition_matrix_v1 40.0%, geometry_v1 50.0%, counter_council_v1 50.0%.

Weakest matchups of replay_hunter_wide_v2: l5_wide_hunter 0.0%, l5_hunter 0.0%, sampled_markov_v1 20.0%, replay_hunter_gate_v2 33.3%, geometry_v1 37.5%, transition_matrix_v1 50.0%.

## Analysis

Scores: 86.2% (+49.6 rounds per match) vs 86.4% (+49.8): identical. A forgetful gate fixes the one opponent that flips levels and gives the same amount back elsewhere, so the defaults stay. The double_bluff_gate fix belongs in a specialist expert (idea #59), not in the gate's global decay.

## Verdict

**drop**. On fresh seeds at the thorough budget, replay_hunter_wide_v2 at GATE_DECAY 0.85 minus its defaults = -0.2 pts [-4.7, +4.4] over 320 paired matches, stopped for futility at look 2: 0058's +4.5 was the high draw (the third such case today). Its head-to-head gain vs double_bluff_gate_v2 (33.6% --> 36.7% of rounds) is real but too narrow to move the pool score.
