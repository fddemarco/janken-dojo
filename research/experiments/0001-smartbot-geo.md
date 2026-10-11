# 0001: geometry arm in the metabot

- **Date:** 2026-10-09
- **Status:** analyzed
- **Idea:** ideas.md #1
- **Bots:** `bots/smartbot_geo.py` (new), baselines: `bots/smartbot.py` (predecessor, same
  constants), `bots/geometry.py` (the standalone arm)

## Hypothesis

`smartbot_geo` is `smartbot` with the same predictors, bandit and constants, plus one
extra arm. That arm runs geometry's learned complex offset (ALPHA 0.05) on the joint-match
predictor's feature and plays a *sampled* move. A paired comparison against `smartbot`
therefore measures only that arm.

Expectation: **smartbot_geo − smartbot ≥ +2 pts** in the paired comparison, with the gain
concentrated against the strong bots (metabots, staller family, iocaine, rps4). Against
those opponents, smartbot's deterministic arms are themselves predictable and a sampled
arm is harder to exploit. Against the trivial zoo bots, both should saturate.

Null or drop condition: a paired CI that includes 0. One extra arm also costs a little
bandit exploration, so a small negative effect is possible against easy bots.

`geometry` rides along as a reference. We expect it to be weaker than both metabots
overall, but strong against the metabots.

40 round robins (800 matches per candidate, score CI ±3 pts) because the effect is
expected to be small. Excluding 3 stems leaves 21 eligible pool bots.

## Command

```bash
uv run python -m janken experiment bots/smartbot_geo.py bots/smartbot.py bots/geometry.py --rounds 200 --round-robins 40 --name 0001-smartbot-geo
```

Run id: `20261009-234556_0001-smartbot-geo` (seed 418889057, 40 round robins, 10120 matches on numba, 0 forfeits)

## Results

| bot | score vs pool [95% CI] | rounds +/- per match | rating ± sd |
|---|---|---|---|
| smartbot | 82.1% [79.3, 84.6] | +73.2 | 1777 ± 62 |
| smartbot_geo | 80.2% [77.3, 82.9] | +72.8 | 1760 ± 75 |
| geometry | 76.5% [73.4, 79.3] | +52.6 | 1726 ± 75 |

Paired comparisons (800 shared pool matches each):

- `smartbot_geo − smartbot = −1.9 pts [−4.9, +1.3]`: **no detectable difference**.
  Resolving an effect of this size would take about 110 round robins, which isn't worth it
  for an effect pointing the wrong way.
- `smartbot_geo − geometry = +3.8 pts [+0.4, +7.1]`, `smartbot − geometry = +5.6 pts [+2.2, +8.8]`:
  both metabots beat the standalone geometry bot.
- Head to head, smartbot_geo vs smartbot: 19-1-20 (48.8%).

Per-opponent paired differences (geo − smartbot, about 38 matches each) are all inside the
noise. The round-margin CI includes 0 for every opponent. The large match-score swings,
word2janken −21 pts and transition_matrix +21 pts, have margin differences of −0.3 and
+3.4 rounds: they are close matches that tip either way. The closest thing to a lead is
smart_staller: −14.5 pts, margin −3.6 ± 5.1. The easy zoo bots saturate at 100% for both.

Weakest matchups: smartbot_geo's are smart_staller 39.5%, pattern_memory 50%, nash
51.4%, meta_smartbot 51.4% and iocaine_lite 51.4%. smartbot's are nash 45.9%,
pattern_memory 46.2%, meta_smartbot 47.3% and transition_matrix 48.6%. Everything strong
in the zoo is about a coin flip against both.

**Mechanism diagnostic.** An instrumented Python copy of the bot, run in the scratchpad (not a
stored run), played 6 matches each against 7 opponents. The geometry arm is *available* in
95% of rounds but the bandit *picks* it in only 0.7–3.0% of them, which is the share of an
average arm (1/56 ≈ 1.8%). Against strong opponents the learned offset stays small (|a| ≈
0.10–0.22), so the arm's sampled move is close to uniform. In practice it is a second
random arm. It only learns a strong rotation against trivially exploitable bots (copycat
|a| ≈ 0.82), and the deterministic arms already beat those.

## Verdict

**drop** (as built). Adding geometry as one bandit arm changes nothing measurable:
−1.9 pts [−4.9, +1.3]. The diagnostic shows why. Geometry's value is that it samples its
move every round, which makes it hard to exploit. A Thompson argmax over 56 arms almost
never selects it, and when it does, the move is nearly uniform. To get geometry's
benefit, the metabot's *own output* would have to be sampled: a mixed strategy over arms,
not one more arm. That becomes idea #10. Nothing goes to insights.md, because there is no
positive effect. The standalone geometry bot is 5.6 pts behind smartbot
[+2.2, +8.8] in this pool, so it is not a stronger base either.
