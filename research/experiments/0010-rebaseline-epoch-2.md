# 0010: rebaseline epoch 2

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #21
- **Candidates:** `bots/smartbot_sims.yaml`, `bots/smartbot_sims2.yaml`, `bots/smartbot_sims3.yaml`, `bots/smartbot_bandit.yaml`
- **Baselines:** `bots/smartbot.yaml`
- **Run:** `20261010-162748_0010-rebaseline-epoch-2`
- **Verdict:** keep

## Hypothesis

On the blueprint code the paired effects behind the insights replicate in sign: smartbot_sims beats smartbot by several pts (0003: +9.1 [+6.1, +12.2]); smartbot_sims3 beats smartbot_sims2 by about +1 pt (0005: +1.3 [+0.1, +2.5], which needs ~4000 paired matches, hence 200 round robins); smartbot_bandit stays no better than smartbot_sims3 (0006: -0.4 [-1.9, +1.1]).

## Command

```bash
uv run janken lab experiment bots/smartbot_sims.yaml bots/smartbot_sims2.yaml bots/smartbot_sims3.yaml bots/smartbot_bandit.yaml bots/smartbot.yaml --rounds 200 --round-robins 200 --pool-size 20 --seed 1346550024 --name 0010-rebaseline-epoch-2
```

## Results

200 of 200 round robin(s) · pool 20 · 200 rounds/match · seed 1346550024 · mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating ± sd |
|---|---|---|---|---|---|---|
| smartbot_sims3 | 4000 | 3200-64-736 | 80.8% [79.6%, 82.0%] | +77.1 | 0 | 1757 ± 69 |
| smartbot_bandit | 4000 | 3200-64-736 | 80.8% [79.6%, 82.0%] | +77.1 | 0 | 1752 ± 76 |
| smartbot_sims2 | 4000 | 3152-57-791 | 79.5% [78.2%, 80.7%] | +76.4 | 0 | 1732 ± 70 |
| smartbot_sims | 4000 | 3008-51-941 | 75.8% [74.5%, 77.1%] | +70.2 | 0 | 1702 ± 68 |
| smartbot | 4000 | 2713-90-1197 | 69.0% [67.5%, 70.4%] | +52.3 | 0 | 1634 ± 80 |

Paired comparisons:

- `smartbot_sims − smartbot_sims2 = -3.7 pts [-5.2, -2.3]` over 4000 shared matches: smartbot_sims2 better
- `smartbot_sims − smartbot_sims3 = -5.0 pts [-6.4, -3.5]` over 4000 shared matches: smartbot_sims3 better
- `smartbot_sims − smartbot_bandit = -5.0 pts [-6.4, -3.5]` over 4000 shared matches: smartbot_bandit better
- `smartbot_sims − smartbot = +6.9 pts [+5.2, +8.5]` over 4000 shared matches: smartbot_sims better
- `smartbot_sims2 − smartbot_sims3 = -1.3 pts [-2.7, +0.2]` over 4000 shared matches: no significant difference
- `smartbot_sims2 − smartbot_bandit = -1.3 pts [-2.7, +0.2]` over 4000 shared matches: no significant difference
- `smartbot_sims2 − smartbot = +10.6 pts [+9.0, +12.2]` over 4000 shared matches: smartbot_sims2 better
- `smartbot_sims3 − smartbot_bandit = +0.0 pts [+0.0, +0.0]` over 4000 shared matches: no significant difference
- `smartbot_sims3 − smartbot = +11.8 pts [+10.3, +13.4]` over 4000 shared matches: smartbot_sims3 better
- `smartbot_bandit − smartbot = +11.8 pts [+10.3, +13.4]` over 4000 shared matches: smartbot_bandit better

Weakest matchups of smartbot_sims: achilles 35.6%, odysseus 36.4%, tpi_lite 38.0%, smartbot_geo 39.0%, ajax 41.3%, hector 42.7%.

Weakest matchups of smartbot_sims2: odysseus 38.6%, agamemnon 41.2%, ajax 42.7%, achilles 44.2%, hector 46.5%, tpi_lite 46.7%.

Weakest matchups of smartbot_sims3: agamemnon 44.2%, nash 51.7%, ajax 52.1%, odysseus 52.2%, meta_smartbot 52.9%, hector 53.8%.

Weakest matchups of smartbot_bandit: agamemnon 44.2%, nash 51.7%, ajax 52.1%, odysseus 52.2%, meta_smartbot 52.9%, hector 53.8%.

Weakest matchups of smartbot: agamemnon 29.6%, hector 33.5%, odysseus 34.9%, achilles 35.3%, tpi_lite 38.0%, ajax 38.2%.

## Analysis

Per opponent (about 130-150 matches each): the sims turn the deterministic zoo bots into sure wins on the new code too (word2janken 76% -> 100%, staller 82 -> 100, markov2_joint 74 -> 100 from smartbot to smartbot_sims); sims2's rps4_lite sim takes rps4_lite from 70% to 99%. sims3's two metabot replays help vs geometry (52 -> 62%) and the Iliad fleet bots playing sims3 as outsiders (odysseus 39 -> 52, achilles 44 -> 55, ajax 43 -> 52, hector 47 -> 54), but not vs meta_smartbot (54 -> 53) or smartbot_geo (60 -> 61), where 0005 found its gains, and they cost vs biased (91 -> 85) and transition_matrix (69 -> 61). Net: the metabot replays are roughly neutral; the pre-refactor 0005 insight does not replicate. Gap: 0006's bandit variants (SHARP 3 / 0.33, greedy SELECT=1) were not re-run; only the defaults' identity was checked. The pool now holds tpi_lite and the fleet, which differs from 0003-0006's zoo; this changes absolute scores, not the paired comparisons' validity.

## Verdict

**keep**. On the blueprint code the sims family's gains replicate in sign and size, except the last step: smartbot_sims - smartbot = +6.9 pts [+5.2, +8.5] (0003: +9.1), smartbot_sims2 - smartbot_sims = +3.7 [+2.3, +5.2], smartbot_sims3 - smartbot_sims2 = +1.3 [-0.2, +2.7] (0005: +1.3 [+0.1, +2.5]; same estimate, no longer significant), smartbot_sims3 - smartbot = +11.8 [+10.3, +13.4]; 4000 paired matches each (200 round robins). smartbot_bandit at its defaults equals smartbot_sims3 match for match (+0.0 [+0.0, +0.0]), as designed. smartbot_sims3 stays the best bot.
