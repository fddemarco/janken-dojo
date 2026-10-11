# 0004: sims of rps4_lite, staller and geometry

- **Date:** 2026-10-10
- **Status:** analyzed
- **Idea:** ideas.md #11 (+ a geometry sim)
- **Bots:** `bots/smartbot_sims2.py` (new), baseline: `bots/smartbot_sims.py` (predecessor)

## Hypothesis

[0003](0003-smartbot-sims.md) showed that replaying an opponent's model of us wins the
near-deterministic matchups outright. `smartbot_sims2` adds three sims to smartbot_sims:
rps4_lite (its 24 greedy arms with decayed scores, from its side), staller (its
janken / counter / anti-counter scoreboard) and geometry (the mode of the distribution it
samples from). Everything else is unchanged.

Pre-run diagnostic (scratchpad Python, not a stored run; 4 matches each): sim accuracy
rps4_lite 0.64 (its count tables tie often and it breaks ties at random), staller 0.73,
geometry 0.41, with margins rps4_lite +27…+73 (smartbot_sims: +7), staller +43…+60 (+22),
geometry −7…+35 (−1).

Expectation: **smartbot_sims2 − smartbot_sims ≥ +1 pt**, concentrated in rps4_lite
(77% → ~95%) and maybe geometry. staller is already at 100% match score, so its margin
gain doesn't count. The effect is small, so 100 round robins (2000 paired matches).

## Command

```bash
uv run python -m janken experiment bots/smartbot_sims2.py bots/smartbot_sims.py --rounds 200 --round-robins 100 --name 0004-smartbot-sims2
```

Run id: `20261010-000523_0004-smartbot-sims2` (seed 681609550, 100 round robins, 23100
matches on numba, 0 forfeits)

## Results

| bot | score vs pool [95% CI] | rounds +/- per match | rating ± sd |
|---|---|---|---|
| smartbot_sims2 | 86.0% [84.4, 87.4] | +88.8 | 1823 ± 64 |
| smartbot_sims | 84.7% [83.1, 86.2] | +85.6 | 1809 ± 72 |

Paired comparison: `smartbot_sims2 − smartbot_sims = +1.2 pts [−0.5, +3.0]` over 2000
shared matches: **no significant difference** at this n (resolving +1.2 pts would take
~250 round robins). Head to head 53-1-46 (53.5%), margin −1.3.

Per opponent (paired, 74–91 matches each):

| opponent | sims2 | sims | diff | margin sims2 / sims |
|---|---|---|---|---|
| rps4_lite | 98.9 | 66.9 | **+32.0** | +33.9 / +6.0 |
| geometry | 61.5 | 50.5 | +11.0 | +2.2 / +1.3 |
| smartbot_geo | 60.2 | 52.8 | +7.4 | +1.9 / +0.5 |
| biased | 87.8 | 82.9 | +4.9 | +18.7 / +15.8 |
| staller | 100.0 | 98.8 | +1.2 | +56.4 / +18.8 |
| smart_staller | 55.6 | 54.3 | +1.2 | +1.1 / +1.9 |
| nash | 48.8 | 51.2 | −2.5 | +0.6 / −0.7 |
| meta_smartbot | 39.9 | 50.6 | −10.7 | −0.6 / −0.6 |
| smartbot | 50.0 | 66.5 | −16.5 | +0.2 / +3.5 |
| 15 others | 98.6–100 | 100 | 0 / −1.4 | saturated |

The targeted effects are there: rps4_lite goes from 67% to 99% (margin +34 rounds instead
of +6), and staller's margin triples. The losses to smartbot and meta_smartbot are not
backed by the round margins (meta_smartbot: −0.6 for both bots); a paired difference of
coin-flip matches at n ≈ 85 has a CI of about ±15 pts, so those are noise. They are also
what keeps the overall CI from excluding 0.

Weakest matchups of smartbot_sims2: meta_smartbot 39.9%, nash 48.8%, smartbot 50.0%,
smart_staller 55.6%, smartbot_geo 60.2%, geometry 61.5%, transition_matrix 65.7%. What is
left is the Thompson metabots, random play, and the samplers.

## Verdict

**iterate**. The rps4_lite sim works as designed (+32 pts in that matchup), but the
overall gain (+1.2 pts) is under the resolution of 100 round robins, because the matches
between metabots are coin flips that add noise. Next run: carry smartbot_sims2 and
smartbot_sims along as candidates with ≥ 200 round robins, together with the next bot
(idea #12: sims of the Thompson metabots, which are now the weakest matchups).
