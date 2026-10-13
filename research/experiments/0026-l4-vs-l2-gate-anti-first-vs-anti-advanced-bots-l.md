# 0026: L4 vs L2: gate_anti_first vs anti_advanced_bots (L2-only pool)

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** -
- **Candidates:** `bots/gate_anti_first.yaml`
- **Baselines:** `bots/anti_advanced_bots.yaml`
- **Run:** `20261010-214527_0026-l4-vs-l2-gate-anti-first-vs-anti-advanced-bots-l`
- **Verdict:** keep

## Hypothesis

The real L4 gate_anti_first beats the best L3 vs L2 opponents: vs anti_advanced_bots over 600 paired matches against the 6 L2 bots (100 round robins), paired difference > 0 with a CI excluding 0 (sweeps: +5.7 [-2.1, +13.5] real on 16 seeds, +7.3 [+2.2, +12.4] arm on 32).

## Command

```bash
uv run janken lab experiment bots/gate_anti_first.yaml bots/anti_advanced_bots.yaml --rounds 200 --round-robins 100 --pool-size 6 --seed 2605825007 --name 0026-l4-vs-l2-gate-anti-first-vs-anti-advanced-bots-l
```

## Results

100 of 100 round robin(s), pool 6, 200 rounds/match, seed 2605825007, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| gate_anti_first | 600 | 566-5-29 | 94.8% [92.7%, 96.3%] | +58.6 | 0 | 1806 +/- 80 |
| anti_advanced_bots | 600 | 542-9-49 | 91.1% [88.5%, 93.1%] | +20.8 | 0 | 1775 +/- 89 |

Paired comparisons:

- `gate_anti_first - anti_advanced_bots = +3.7 pts [+0.9, +6.6]` over 600 shared matches: gate_anti_first better

Weakest matchups of gate_anti_first: smart_staller 86.5%, meta_smartbot 87.0%, smartbot 97.5%, rps4_lite 97.5%, staller 100.0%, iocaine_lite 100.0%.

Weakest matchups of anti_advanced_bots: staller 65.0%, meta_smartbot 91.5%, smart_staller 92.5%, smartbot 98.0%, rps4_lite 99.5%, iocaine_lite 100.0%.

## Analysis

L2-only pool (experiments/levels/L2: smartbot, meta_smartbot, smart_staller, iocaine_lite, rps4_lite, staller), candidates mode. anti_advanced_bots' weak spot is staller (65.0%), which the L4 wins 100%: once the advanced arms lead vs staller (L2 by the rule, a scoreboard of three rotations), the gatekeeper switches. The L4's weakest are smart_staller 86.5% and meta_smartbot 87.0% (anti: 92.5% and 91.5%): the Thompson metabots it reads through the anti expert; switching away on noise costs a few matches there.

## Verdict

**keep**. The real L4 beats the best L3 vs L2: gate_anti_first - anti_advanced_bots = +3.7 pts [+0.9, +6.6] over 600 paired matches against the 6 L2 bots (100 round robins, L2-only pool, no mocks): 94.8% vs 91.1%, margin +58.6 vs +20.8 rounds per match.
