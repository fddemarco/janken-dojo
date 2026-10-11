# 0011: sims3_staller vs smartbot_sims3

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #22
- **Candidates:** `bots/sims3_staller.yaml`
- **Baselines:** `bots/smartbot_sims3.yaml`
- **Run:** `20261010-163340_0011-sims3-staller-vs-smartbot-sims3`
- **Verdict:** iterate

## Hypothesis

sims3_staller (smartbot_sims3 + smart_staller's Stall overlay) beats smartbot_sims3 by >= 1 pt in the paired comparison, from the close matchups vs the smartbot family, meta_smartbot and geometry (0010: 52-62%, margins +1..+4 rounds), while staying at ~100% vs the exploitable bots (lead lock only stalls once the lead is safe). 200 round robins for a ~1 pt effect.

## Command

```bash
uv run janken lab experiment bots/sims3_staller.yaml bots/smartbot_sims3.yaml --rounds 200 --round-robins 200 --pool-size 20 --seed 2523968947 --name 0011-sims3-staller-vs-smartbot-sims3
```

## Results

200 of 200 round robin(s) · pool 20 · 200 rounds/match · seed 2523968947 · mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating ± sd |
|---|---|---|---|---|---|---|
| smartbot_sims3 | 4000 | 3071-59-870 | 77.5% [76.2%, 78.8%] | +68.1 | 0 | 1746 ± 75 |
| sims3_staller | 4000 | 3036-69-895 | 76.8% [75.4%, 78.0%] | +19.5 | 0 | 1740 ± 84 |

Paired comparisons:

- `sims3_staller − smartbot_sims3 = -0.8 pts [-2.1, +0.6]` over 4000 shared matches: no significant difference

Weakest matchups of sims3_staller: ajax 47.6%, achilles 47.9%, nash 48.5%, tpi_lite 50.0%, smartbot_sims 51.3%, odysseus 51.3%.

Weakest matchups of smartbot_sims3: smartbot_bandit 44.7%, odysseus 45.7%, agamemnon 46.8%, ajax 47.6%, nash 50.4%, achilles 51.7%.

## Analysis

Per opponent (about 115-130 matches each, so about +-9 pts of noise): ahead vs the sims3 clones, as hypothesised (agamemnon 54% vs 47, smartbot_bandit 52 vs 45, odysseus 51 vs 46, smartbot_sims2 58 vs 53, hector 58 vs 55), behind vs smartbot (58 vs 67), smartbot_sims (51 vs 59), smartbot_geo (59 vs 66), transition_matrix (54 vs 61) and rotation_outcome (94 vs 100). The rotation_outcome loss, against a bot smartbot_sims3 always beats, means stalling throws away exploitable leads: either the drawdown trigger (net -5 over 20 rounds) fires on ordinary variance and its 15 random rounds hand back the lead, or the lead lock stalls too early for a bot that only becomes readable later. Follow-up: the same run design with the triggers split, sims3_staller:DD_TRIGGER=1000 (lead lock only) and sims3_staller:LOCK_Z=100 (drawdown only), against smartbot_sims3.

## Verdict

**iterate**. smartbot_sims3 + smart_staller's Stall overlay is no better overall: sims3_staller - smartbot_sims3 = -0.8 pts [-2.1, +0.6] over 4000 paired matches (200 round robins), with its round margin cut from +68 to +20 by stalling. Per opponent it wins the coin flips vs our own clones but loses them vs the other adaptive bots; the two triggers need separating before the idea is judged.
