# 0013: sims3_second vs smartbot_sims3

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #5
- **Candidates:** `bots/sims3_second.yaml`
- **Baselines:** `bots/smartbot_sims3.yaml`
- **Run:** `20261010-164703_0013-sims3-second-vs-smartbot-sims3`
- **Verdict:** drop

## Hypothesis

sims3_second (smartbot_sims3 + SecondMatch over the opponent, joint and our histories) beats smartbot_sims3 by >= 1.5 pts in the paired comparison, from opponents with longer-range regularities (transition_matrix, geometry, smartbot_geo, the metabots) where a second, older witness of a matched pattern confirms or corrects the first.

## Command

```bash
uv run janken lab experiment bots/sims3_second.yaml bots/smartbot_sims3.yaml --rounds 200 --round-robins 40 --pool-size 20 --seed 3685861615 --name 0013-sims3-second-vs-smartbot-sims3
```

## Results

40 of 40 round robin(s), pool 20, 200 rounds/match, seed 3685861615, mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| smartbot_sims3 | 800 | 611-16-173 | 77.4% [74.3%, 80.1%] | +67.8 | 0 | 1746 +/- 81 |
| sims3_second | 800 | 594-17-189 | 75.3% [72.2%, 78.2%] | +67.3 | 0 | 1725 +/- 65 |

Paired comparisons:

- `sims3_second - smartbot_sims3 = -2.1 pts [-5.4, +1.4]` over 800 shared matches: no significant difference

Weakest matchups of sims3_second: agamemnon 36.4%, hector 36.5%, achilles 37.5%, smartbot_bandit 40.7%, smart_staller 43.1%, tpi_lite 50.0%.

Weakest matchups of smartbot_sims3: tpi_lite 34.6%, nash 40.5%, geometry 43.2%, hector 44.2%, smartbot_bandit 46.3%, odysseus 47.5%.

## Analysis

The point estimate is negative, in line with 0009: nine more arms under one Thompson bandit dilute it slightly more than they inform it. Its weakest matchups (agamemnon 36%, hector 37%, achilles 38%, smartbot_bandit 41%) are smartbot_sims3's clones, the same coin flips every sims3 variant has; nothing suggests the second-order witness predicts adaptive bots better than the first-order LongestMatch arms already in the core. In 200-round matches a suffix's matched point rarely has its own long repeat, so the signal is often NO_MOVE or a short-context echo of LongestMatch.

## Verdict

**drop**. Second-order history matching (the new SecondMatch stage over the opponent, joint and our histories, x 3 rotations) adds nothing to smartbot_sims3: sims3_second - smartbot_sims3 = -2.1 pts [-5.4, +1.4] over 800 paired matches (40 round robins). The stage stays in the kit, tested against its brute-force definition.
