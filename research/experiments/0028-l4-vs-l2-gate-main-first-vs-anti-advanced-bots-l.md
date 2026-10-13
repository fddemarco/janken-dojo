# 0028: L4 vs L2: gate_main_first vs anti_advanced_bots (L2-only pool)

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #35
- **Candidates:** `bots/gate_main_first.yaml`
- **Baselines:** `bots/anti_advanced_bots.yaml`
- **Run:** `20261010-223059_0028-l4-vs-l2-gate-main-first-vs-anti-advanced-bots-l`
- **Verdict:** keep

## Hypothesis

The real MAIN_FIRST L4 beats the best L3 vs L2: gate_main_first - anti_advanced_bots over 600 paired matches vs the 6 L2 bots, CI excluding 0 (Oracle-arm screen +8.6 [+3.8, +13.4]; ANTI_FIRST: +3.7 [+0.9, +6.6], 0026).

## Command

```bash
uv run janken lab experiment bots/gate_main_first.yaml bots/anti_advanced_bots.yaml --rounds 200 --round-robins 100 --pool-size 6 --seed 627683978 --name 0028-l4-vs-l2-gate-main-first-vs-anti-advanced-bots-l
```

## Results

100 of 100 round robin(s), pool 6, 200 rounds/match, seed 627683978, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| gate_main_first | 600 | 561-4-35 | 93.8% [91.6%, 95.5%] | +58.5 | 0 | 1778 +/- 90 |
| anti_advanced_bots | 600 | 524-5-71 | 87.8% [84.9%, 90.1%] | +19.6 | 0 | 1775 +/- 93 |

Paired comparisons:

- `gate_main_first - anti_advanced_bots = +6.1 pts [+3.0, +9.4]` over 600 shared matches: gate_main_first better

Weakest matchups of gate_main_first: meta_smartbot 81.0%, smart_staller 89.5%, smartbot 95.0%, rps4_lite 97.5%, staller 100.0%, iocaine_lite 100.0%.

Weakest matchups of anti_advanced_bots: staller 53.5%, meta_smartbot 84.5%, smart_staller 91.0%, rps4_lite 98.5%, smartbot 99.0%, iocaine_lite 100.0%.

## Analysis

Vs L2 the anti expert's record leads the advanced arms' vs the Thompson metabots (smartbot, meta_smartbot, smart_staller) and the gate moves to it; vs staller, iocaine_lite and rps4_lite the advanced arms lead and it stays: staller 100% (anti 53.5%), iocaine_lite and rps4_lite 97.5-100%. Weakest: meta_smartbot 81.0% (anti 84.5%), smart_staller 89.5% (anti 91.0%): the rounds before the anti expert's record leads cost a few matches vs the metabots. With 0027 the L4 meets both level targets; screening used Oracle arms (32 paired seeds: ANTI_FIRST, ANTI_FIRST_HOLD, BANDIT, EDGE, MAIN_FIRST at several EDGE / WARMUP), and an Optuna study of ANTI_FIRST (0024) was flat.

## Verdict

**keep**. The real L4 gate_main_first beats the best L3 vs L2: gate_main_first - anti_advanced_bots = +6.1 pts [+3.0, +9.4] over 600 paired matches vs the 6 L2 bots (100 round robins, L2-only pool, no mocks): 93.8% vs 87.8%, margin +58.5 vs +19.6 rounds per match.
