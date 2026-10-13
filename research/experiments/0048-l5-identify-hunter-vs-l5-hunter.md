# 0048: l5_identify_hunter vs l5_hunter

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #51
- **Candidates:** `bots/l5/l5_identify_hunter.yaml`
- **Baselines:** `bots/l5/l5_hunter.yaml`
- **Run:** `20261013-115606_0048-l5-identify-hunter-vs-l5-hunter`
- **Verdict:** iterate

## Hypothesis

l5_identify_hunter beats l5_hunter by >= 2 pts vs random pools, the gain coming from rps4_lite, outcome_reader, iocaine_lite and period_bandit (its parameter-variant replays of them lead the gate once they name the opponent's moves), with no loss elsewhere (janken lab identify: +12.3 pts after round 150 vs those species' variants)

## Command

```bash
uv run janken lab experiment bots/l5/l5_identify_hunter.yaml bots/l5/l5_hunter.yaml --rounds 200 --round-robins 3 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 4128428813 --name 0048-l5-identify-hunter-vs-l5-hunter
```

## Results

3 of 3 round robin(s), pool 20, 200 rounds/match, seed 4128428813, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| l5_hunter | 60 | 52-2-6 | 88.3% [77.8%, 94.2%] | +63.3 | 0 | 1836 +/- 78 |
| l5_identify_hunter | 60 | 47-0-13 | 78.3% [66.4%, 86.9%] | +59.6 | 0 | 1761 +/- 93 |

Paired comparisons:

- `l5_identify_hunter - l5_hunter = -10.0 pts [-20.8, +0.8]` over 60 shared matches: no significant difference

Weakest matchups of l5_identify_hunter: transition_matrix_v1 0.0%, l5_lean_hunter 0.0%, nash_v1 0.0%, replay_hunter_gate_v2 0.0%, gate_main_first_v3 0.0%, gate_edge_smartbot_v2 0.0%.

Weakest matchups of l5_hunter: l5_lean_hunter 0.0%, nash_v1 0.0%, l5_level_k 50.0%, double_bluff_gate_v2 50.0%, l5_priority 50.0%, gate_fast_hold_v1 50.0%.

## Analysis

Per match (same seeds), the losses are everywhere, not only vs the variant species: rotation_outcome_v1 +37 vs +173 rounds, multiscale_v1 +23 vs +123, transition_matrix_v1 -32 vs +19, gate_bandit_period_v2 -18 vs +18, replay_hunter_gate_v2 -13 vs +15, and even iocaine_lite_v1 (a variant species) +141 vs +177. Mechanism (hypothesis): LEADER over 52 experts, 32 of them near-copies, hands the gate to whichever expert's record is luckiest, so the max of many noisy records makes false leads; janken lab identify instead pooled the particles into one vote and switched between only two options (keep vs exploit). Next: one gated expert that is the variants pooled (a Bandit over the 32 replays, its likeliest move), not 32 experts.

## Verdict

**iterate**. l5_identify_hunter - l5_hunter = -10.0 pts [-20.8, +0.8] over 60 paired matches (3 round robins): the upper bound is below the +2 pts hypothesis, so it can't hold. Adding 32 parameter-variant replays as separate gated experts under the LEADER gate costs points broadly instead of winning vs the four species.
