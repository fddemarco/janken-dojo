# 0017: mock_replay_gate vs replay_gate (mock validation)

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #30
- **Candidates:** `bots/mock_replay_gate.yaml`
- **Baselines:** `bots/replay_gate.yaml`
- **Run:** `20261010-193336_0017-mock-replay-gate-vs-replay-gate-mock-validation`
- **Verdict:** keep

## Hypothesis

mock_replay_gate is replay_gate with its anti expert (the 256-draw replay) swapped for an Oracle calibrated on anti_advanced_bots (16 seeds x 34 opponents, calibration/anti_advanced_bots.yaml). If the mock is faithful, the paired difference vs replay_gate is within +-3 pts with a CI covering 0, and its zoo / family match shares are within a few points of replay_gate's (0016: 94.8% / 83.7%). Known gap: vs anti_advanced_bots the mock uses the advanced fallback odds (~40% wins) where the real replay is read by anti (replay_gate lost 10/10), so the mock should look better in that one matchup. The run should take far less than 0016's 356 s.

## Command

```bash
uv run janken lab experiment bots/mock_replay_gate.yaml bots/replay_gate.yaml --rounds 200 --round-robins 10 --pool-size 20 --seed 326188217 --name 0017-mock-replay-gate-vs-replay-gate-mock-validation
```

## Results

10 of 10 round robin(s) · pool 20 · 200 rounds/match · seed 326188217 · mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating ± sd |
|---|---|---|---|---|---|---|
| mock_replay_gate | 200 | 178-3-19 | 89.8% [84.8%, 93.2%] | +54.3 | 0 | 1856 ± 71 |
| replay_gate | 200 | 174-1-25 | 87.2% [81.9%, 91.2%] | +68.0 | 0 | 1833 ± 75 |

Paired comparisons:

- `mock_replay_gate − replay_gate = +2.5 pts [-2.5, +7.8]` over 200 shared matches: no significant difference

Weakest matchups of mock_replay_gate: meta_smartbot 37.5%, smart_staller 60.0%, nash 62.5%, anti_advanced_bots 62.5%, tpi_lite 66.7%, biased 66.7%.

Weakest matchups of replay_gate: anti_advanced_bots 12.5%, geometry 12.5%, sims3_second 66.7%, biased 66.7%, transition_matrix 71.4%, nash 75.0%.

## Analysis

Calibration: calibration/anti_advanced_bots.yaml, 16 seeds x 34 opponents (janken lab calibrate). anti_advanced_bots wins 38-47% of rounds vs every advanced bot (iocaine_lite 46.8%, advanced_bot 43.0%, meta_smartbot 37.7%) and 33-35% vs the zoo, staller included (advanced by the rule, chance in practice). Differences: (1) vs anti_advanced_bots the mock wins 62.5% of matches where replay_gate wins 12.5%, the predicted gap: the mock gets the advanced fallback odds there, while the real anti reads replay_gate's closed-gate play. (2) Zoo round margins are smaller with the mock (+81.1 vs +109.7 per match) while matches won are equal or better: the mock's outcomes vs the zoo are i.i.d. near-even draws, so its record wanders over the edge more often than the real replay's, which falls behind vs reactive zoo bots once it plays; the mock overstates false openings vs the zoo, a bias against every rule that trusts the gated arm early. (3) Cost: this run still played the real replay_gate in every round robin (239.9 s for 2310 matches); mock-only runs avoid the 256-draw nested replay entirely. EDGE rule unchanged by the new Gatekeeper rules: two 0016 transcripts of replay_gate vs smartbot replay bit-identically.

## Verdict

**keep**. The mock is faithful on the score: mock_replay_gate (replay_gate with its 256-draw replay swapped for an Oracle calibrated on anti_advanced_bots) scores 89.8% vs replay_gate's 87.2%, +2.5 pts [-2.5, +7.8] over 200 paired matches, no significant difference; advanced opponents 86.3% vs 85.8% of matches (42.0% vs 40.9% of rounds), zoo 92.9% vs 88.6%. Kept as the research stand-in for replay_gate (pool.mocks).
