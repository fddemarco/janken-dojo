# 0018: Gatekeeper rules: anti first and bandit vs edge (mocked)

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #32
- **Candidates:** `bots/mock_gate_anti_first.yaml`, `bots/mock_gate_bandit.yaml`
- **Baselines:** `bots/mock_replay_gate.yaml`
- **Run:** `20261010-193816_0018-gatekeeper-rules-anti-first-and-bandit-vs-edge-m`
- **Verdict:** iterate

## Hypothesis

With the anti expert mocked (Oracle, calibration/anti_advanced_bots.yaml) and mocks in the pools (pool.mocks on; mocks draw each other on PAPER): ANTI_FIRST (play the anti expert until the advanced arms' counterfactual record leads it by 0.05, from round 10) wins more advanced matches than EDGE (no rounds lost waiting for the replay's edge) and loses a few zoo rounds early; BANDIT (Thompson between the two experts' records) avoids EDGE's false openings vs the zoo. Effect that matters: >= 3 pts vs mock_replay_gate (CI excluding 0); expect both within +-5 pts, since EDGE already wins ~90% of matches. Also covers idea #33 (BANDIT).

## Command

```bash
uv run janken lab experiment bots/mock_gate_anti_first.yaml bots/mock_gate_bandit.yaml bots/mock_replay_gate.yaml --rounds 200 --round-robins 10 --pool-size 20 --seed 4069874077 --name 0018-gatekeeper-rules-anti-first-and-bandit-vs-edge-m
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 4069874077, mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| mock_gate_anti_first | 200 | 180-8-12 | 92.0% [87.4%, 95.0%] | +71.9 | 0 | 1860 +/- 55 |
| mock_gate_bandit | 200 | 179-6-15 | 91.0% [86.2%, 94.2%] | +70.6 | 0 | 1852 +/- 38 |
| mock_replay_gate | 200 | 171-10-19 | 88.0% [82.8%, 91.8%] | +58.2 | 0 | 1826 +/- 40 |

Paired comparisons:

- `mock_gate_anti_first - mock_gate_bandit = +1.0 pts [-3.0, +5.0]` over 200 shared matches: no significant difference
- `mock_gate_anti_first - mock_replay_gate = +4.0 pts [-0.5, +8.5]` over 200 shared matches: no significant difference
- `mock_gate_bandit - mock_replay_gate = +3.0 pts [-1.8, +7.8]` over 200 shared matches: no significant difference

Weakest matchups of mock_gate_anti_first: mock_anti_advanced 50.0%, smart_staller 56.2%, geometry 57.1%, transition_matrix 60.0%, biased 66.7%, sims3_second 75.0%.

Weakest matchups of mock_gate_bandit: nash 42.9%, mock_anti_advanced 50.0%, meta_smartbot 57.1%, sims3_staller 60.0%, transition_matrix 60.0%, geometry 71.4%.

Weakest matchups of mock_replay_gate: biased 33.3%, nash 42.9%, mock_anti_advanced 50.0%, geometry 57.1%, transition_matrix 60.0%, sims3_staller 60.0%.

## Analysis

Round margins: +71.9 (ANTI_FIRST) and +70.6 (BANDIT) vs +58.2 (EDGE) per match. Weakest matchups: EDGE biased 33%, nash 43%; ANTI_FIRST smart_staller 56%, geometry 57%; BANDIT nash 43%, meta_smartbot 57%. All three draw mock_anti_advanced (50%: mocks draw on PAPER). Caveat from 0017: the mock overstates false openings of the gated arm vs the zoo, which hurts EDGE and ANTI_FIRST (both trust the gated arm) more than BANDIT.

## Verdict

**iterate**. Both new gatekeeper rules lean ahead of EDGE but unresolved at standard effort: ANTI_FIRST +4.0 pts [-0.5, +8.5], BANDIT +3.0 pts [-1.8, +7.8] vs mock_replay_gate over 200 paired matches (92.0% / 91.0% / 88.0%); ANTI_FIRST - BANDIT +1.0 [-3.0, +5.0]. Next: the same comparison at thorough effort (40 round robins), cheap with mocks (7.2 s for 2530 matches here vs 356 s for 0016).
