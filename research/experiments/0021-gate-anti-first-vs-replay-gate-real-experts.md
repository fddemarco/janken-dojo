# 0021: gate_anti_first vs replay_gate (real experts)

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** —
- **Candidates:** `bots/gate_anti_first.yaml`
- **Baselines:** `bots/replay_gate.yaml`
- **Run:** `20261010-194831_0021-gate-anti-first-vs-replay-gate-real-experts`
- **Verdict:** iterate

## Hypothesis

The real twin confirms the mocked result of 0019 (ANTI_FIRST +3.4 pts [+0.8, +6.0] vs EDGE): gate_anti_first (the 256-draw Replay as the gated arm, Gatekeeper rule ANTI_FIRST, EDGE 0.05, WARMUP 10) beats replay_gate by >= 3 pts with the gain on advanced opponents (0019: 94.1% vs 84.5% of advanced matches). At standard effort (CI about +-6 pts) a CI excluding 0 is not expected; the direction and the per-class split are what to check. Real anti_advanced_bots is in the pools (mocks off) and beat replay_gate 10/10 in 0016.

## Command

```bash
uv run janken lab experiment bots/gate_anti_first.yaml bots/replay_gate.yaml --rounds 200 --round-robins 10 --pool-size 20 --seed 574314134 --name 0021-gate-anti-first-vs-replay-gate-real-experts
```

## Results

10 of 10 round robin(s) · pool 20 · 200 rounds/match · seed 574314134 · mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating ± sd |
|---|---|---|---|---|---|---|
| gate_anti_first | 200 | 178-1-21 | 89.2% [84.2%, 92.8%] | +72.2 | 0 | 1863 ± 58 |
| replay_gate | 200 | 172-2-26 | 86.5% [81.1%, 90.6%] | +62.7 | 0 | 1816 ± 66 |

Paired comparisons:

- `gate_anti_first − replay_gate = +2.8 pts [-2.0, +7.8]` over 200 shared matches: no significant difference

Weakest matchups of gate_anti_first: nash 16.7%, anti_advanced_bots 16.7%, biased 33.3%, geometry 62.5%, sims3_staller 71.4%, tpi_lite 80.0%.

Weakest matchups of replay_gate: anti_advanced_bots 16.7%, nash 16.7%, geometry 43.8%, smart_staller 60.0%, smartbot_sims 60.0%, transition_matrix 66.7%.

## Analysis

Per class, the mechanism matches 0019: vs advanced bots 91.1% vs 85.4% of matches, 46.0% vs 40.4% of rounds, margin +37.8 vs +20.0 rounds per match; vs the zoo 87.5% vs 87.5%, margins +103.9 vs +102.0. Both lose to the real anti_advanced_bots (16.7%: it replays the advanced arms both play once switched) and to nash (16.7%, noise). geometry: 62.5% vs 43.8%. The mock predicted the class split well (0019 advanced 94.1% vs 84.5%); its zoo bias (0017) shows as the zoo match share being 2 pts lower mocked than real for ANTI_FIRST. Cost: 382.8 s for this run vs seconds mocked.

## Verdict

**iterate**. With the real experts, gate_anti_first (ANTI_FIRST gatekeeper) leads replay_gate (EDGE) by +2.8 pts [-2.0, +7.8] over 200 paired matches (89.2% vs 86.5%), the same direction and size as the mocked +3.4 pts [+0.8, +6.0] of 0019, but unresolved at standard effort. A thorough real run (40 round robins, ~25 min) would settle it.
