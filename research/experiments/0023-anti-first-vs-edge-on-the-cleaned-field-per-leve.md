# 0023: ANTI_FIRST vs EDGE on the cleaned field (per-level Oracles)

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** —
- **Candidates:** `bots/arm_gate_anti_first.yaml`
- **Baselines:** `bots/arm_replay_gate.yaml`
- **Run:** `20261010-204849_0023-anti-first-vs-edge-on-the-cleaned-field-per-leve`
- **Verdict:** iterate

## Hypothesis

On the cleaned field, with every L3/L4 pool bot a pure Oracle (pool.mocks) and both gatekeepers' anti experts per-level Oracle arms, ANTI_FIRST still beats EDGE (0019, old field: +3.4 pts [+0.8, +6.0]) by >= 2 pts with a CI excluding 0, and a 40-round-robin run takes seconds.

## Command

```bash
uv run janken lab experiment bots/arm_gate_anti_first.yaml bots/arm_replay_gate.yaml --rounds 200 --round-robins 40 --pool-size 20 --seed 1374732409 --name 0023-anti-first-vs-edge-on-the-cleaned-field-per-leve
```

## Results

40 of 40 round robin(s) · pool 20 · 200 rounds/match · seed 1374732409 · mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating ± sd |
|---|---|---|---|---|---|---|
| arm_replay_gate | 800 | 635-117-48 | 86.7% [84.2%, 88.9%] | +61.7 | 0 | 1828 ± 38 |
| arm_gate_anti_first | 800 | 627-119-54 | 85.8% [83.2%, 88.1%] | +83.1 | 0 | 1821 ± 45 |

Paired comparisons:

- `arm_gate_anti_first − arm_replay_gate = -0.9 pts [-2.9, +1.1]` over 800 shared matches: no significant difference

Weakest matchups of arm_gate_anti_first: transition_matrix 41.1%, oracle_advanced_bot 50.0%, oracle_anti_advanced 50.0%, oracle_replay_gate 50.0%, oracle_gate_anti_first 50.0%, geometry 58.9%.

Weakest matchups of arm_replay_gate: oracle_advanced_bot 50.0%, oracle_gate_anti_first 50.0%, oracle_replay_gate 50.0%, oracle_anti_advanced 50.0%, nash 53.0%, geometry 69.6%.

## Analysis

By design, pure Oracles make pools cheap but blind: a candidate can't do better or worse vs one. The cleanup also left only two real L3 bots (advanced_bot, anti_advanced_bots) and two L4s, so the old advanced matchups of 0019 (smartbot_sims, sims3\_*, sinon, ...) are now in legacy_bots/. Weakest matchups: transition_matrix 41.1% (ANTI_FIRST) and geometry 58.9% / 69.6%. To compare gatekeepers on advanced opponents, either run mocks off with the real L3/L4 bots in the pools (minutes), or bring cheap real L3s back from legacy_bots/ (smartbot_sims and sims3\_* are L3s without the 256-draw replay).

## Verdict

**iterate**. Uninformative on the advanced field: ANTI_FIRST - EDGE = -0.9 pts [-2.9, +1.1] over 800 paired matches, but with pool.mocks every L3/L4 opponent is a pure Oracle, and an Oracle's result is fixed by its own knobs (vs these ARM candidates: a forced draw, 50% of matches), so only the zoo and L2 opponents compare the gate rules. There the two rules tie; ANTI_FIRST's gain (0019, 0021) was against advanced opponents.
