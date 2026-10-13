# 0057: replay_hunter_wider vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #45
- **Candidates:** `bots/l4/replay_hunter_wider.yaml`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-135534_0057-replay-hunter-wider-vs-replay-hunter-wide-v2`
- **Verdict:** drop

## Hypothesis

Confirmation of note 0056 at the thorough budget on fresh seeds: replay_hunter_wider beats replay_hunter_wide_v2 by >= 2 pts vs random pools (0056: +4.0 pts [-1.8, +10.0] at 10 round robins)

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_wider.yaml bots/l4/replay_hunter_wide_v2.yaml --rounds 200 --round-robins 16 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 3419226415 --name 0057-replay-hunter-wider-vs-replay-hunter-wide-v2
```

## Results

16 of 16 round robin(s), pool 20, 200 rounds/match, seed 3419226415, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wider | 320 | 278-4-38 | 87.5% [83.4%, 90.7%] | +55.0 | 0 | 1841 +/- 65 |
| replay_hunter_wide_v2 | 320 | 271-6-43 | 85.6% [81.4%, 89.0%] | +51.2 | 0 | 1813 +/- 56 |

Paired comparisons:

- `replay_hunter_wider - replay_hunter_wide_v2 = +1.9 pts [-2.8, +6.9]` over 320 shared matches: no significant difference

Weakest matchups of replay_hunter_wider: smartbot_fast_v1 0.0%, l5_wide_hunter 25.0%, sampled_markov_v1 33.3%, l2_council_v1 41.7%, replay_hunter_gate_v2 50.0%, geometry_v1 50.0%.

Weakest matchups of replay_hunter_wide_v2: l5_wide_hunter 0.0%, l5_hunter 0.0%, bayes_predators_v1 0.0%, counter_council_v1 25.0%, sampled_markov_v1 33.3%, geometry_v1 50.0%.

## Analysis

Scores: replay_hunter_wider 87.5% (+55.0 rounds per match), replay_hunter_wide_v2 85.6% (+51.2). Same pattern as the L5s (0051-0053) and the insight of 2026-10-13 on single-opponent gains: each new expert wins its target, and the target is a few of ~40 pool slots, so the pooled effect stays near +2 pts, which a 40-round-robin evaluation can't separate from 0.

## Verdict

**drop**. At the thorough budget on fresh seeds, replay_hunter_wider - replay_hunter_wide_v2 = +1.9 pts [-2.8, +6.9] over 320 paired matches, stopped for futility at look 2 of 5 (16 round robins): 0056's +4.0 was the high draw. The five new experts close specific holes (outcome_reader, geometry_v1, sampled_markov) but the gain they bring the pool score is about 2 pts, below what's worth the extra experts.
