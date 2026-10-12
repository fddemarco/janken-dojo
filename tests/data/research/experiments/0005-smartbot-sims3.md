# 0005: replaying the Thompson metabots (and confirming 0004)

- **Date:** 2026-10-10
- **Status:** analyzed
- **Idea:** ideas.md #12, plus the confirmation run for #11 asked by [0004](0004-smartbot-sims2.md)
- **Bots:** `bots/smartbot_sims3.py` (new), baselines: `bots/smartbot_sims2.py`,
  `bots/smartbot_sims.py`

## Hypothesis

The Thompson metabots (smartbot, meta_smartbot, smart_staller, smartbot_geo) are now the
weakest non-random matchups (40–60%). `smartbot_sims3` is smartbot_sims2 plus two
replays of smartbot's machinery from the opponent's side: its 18 predictors and 54 arm
scores, fed the swapped history, at smartbot's constants (0.95 / 0.9 / 12, shared by
smart_staller and smartbot_geo) and at meta_smartbot's (0.6 / 0.6 / 8). Each predicts the
move of the arm with the best posterior mean.

Pre-run diagnostic (scratchpad Python prototype, not a stored run; 6 matches each, rounds
10–199, while smartbot_sims2 played): the posterior-mean arm's move equals smartbot's
actual move 45.4% of the time and meta_smartbot's 45.9% (chance: 33%). A 20-sample Monte
Carlo of the Thompson draw does no better (45.4%, 45.8%), so the mean is as good a proxy
as sampling. If exploited fully, 45% accuracy is worth about +0.18 rounds per round.

Expectation:

- **smartbot_sims3 − smartbot_sims2 ≥ +2 pts**, from the four metabot matchups going from
  ~50% to ~70%. The metabots adapt to whatever we play, so the realised edge may be much
  smaller than the diagnostic suggests.
- **smartbot_sims2 − smartbot_sims ≈ +1.2 pts** as in 0004; at 200 round robins its CI
  should be about ±1.3 pts, enough to resolve it.

## Command

```bash
uv run python -m janken experiment bots/smartbot_sims3.py bots/smartbot_sims2.py bots/smartbot_sims.py --rounds 200 --round-robins 200 --name 0005-smartbot-sims3
```

Run id: `20261010-001100_0005-smartbot-sims3` (seed 1004331697, 200 round robins, 50600
matches on numba, 0 forfeits)

## Results

| bot | score vs pool [95% CI] | rounds +/- per match | rating ± sd |
|---|---|---|---|
| smartbot_sims3 | 87.3% [86.2, 88.3] | +90.3 | 1825 ± 58 |
| smartbot_sims2 | 86.0% [84.9, 87.1] | +89.3 | 1808 ± 60 |
| smartbot_sims | 85.2% [84.1, 86.3] | +86.4 | 1797 ± 68 |

Paired comparisons (4000 shared matches each):

- `smartbot_sims3 − smartbot_sims2 = +1.3 pts [+0.1, +2.5]`: **sims3 better**.
- `smartbot_sims3 − smartbot_sims = +2.1 pts [+0.9, +3.3]`: sims3 better.
- `smartbot_sims2 − smartbot_sims = +0.8 pts [−0.4, +2.1]`: still no significant
  difference. Together with 0004's +1.2 [−0.5, +3.0], the rps4/staller/geometry sims are
  worth about +1 pt that neither run resolves alone.

Head to head: sims3 vs sims2 104-3-93 (52.8%, margin +0.5); sims3 vs sims 116-7-77
(59.8% [52.8, 66.3], margin +2.4); sims2 vs sims 98-9-93.

Per opponent, sims3 − sims2 (paired, 162–172 matches each): smartbot_geo **+18.9**
(margin +3.9 vs +0.3), meta_smartbot **+11.0** (+1.3 vs −1.6), smartbot **+7.9** (+2.4
vs +0.6), nash +6.8 (noise: random play), transition_matrix +2.2; against that geometry
−5.8, biased −5.1, smart_staller −4.8 (margins +0.3 vs +2.5, +18.0 vs +21.0, +1.9 vs
+3.3). The replays win the metabot matchups, but by only +1…+4 rounds per match: far from
the +36 rounds that 45% accuracy would give against a static bot. The metabots adapt (their
arms that model us start winning once we exploit them), so the edge stays thin.

sims2 − sims per opponent: rps4_lite **+23.5** (99.7% vs 76.2%, margin +34.1 vs +7.2),
geometry +8.9, smart_staller +7.8, staller margin +54.8 vs +19.8; smartbot_geo −9.8 and
meta_smartbot −5.2 on margins within ±1.5 (noise).

Weakest matchups of smartbot_sims3: geometry 50.6%, meta_smartbot 53.2%, nash 54.9%,
smart_staller 55.1%, smartbot 59.5%, smartbot_geo 65.2%, transition_matrix 67.0%,
biased 87.0%.

## Verdict

**keep**. smartbot_sims3 is the new best: +1.3 pts [+0.1, +2.5] over sims2 and
+2.1 pts [+0.9, +3.3] over sims. Replaying a Thompson metabot's arm scores from its side
predicts it well enough to tip the metabot matchups (+8…+19 pts), but the realised round
margins are small, because those bots adapt. The rps4_lite sim of 0004 is confirmed per
opponent (+23.5 pts), and sims3 carries it. Left: geometry and nash (random-like), the
staller, and the samplers. Since what remains is mostly coin-flip matches, the bandit
itself (how sharply it commits, and how predictable its own output is) is the next lever:
ideas #7 and #10.
