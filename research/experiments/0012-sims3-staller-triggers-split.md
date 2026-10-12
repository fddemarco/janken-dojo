# 0012: sims3-staller triggers split

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #22
- **Candidates:** `bots/sims3_staller.yaml:DD_TRIGGER=1000`, `bots/sims3_staller.yaml:LOCK_Z=100`
- **Baselines:** `bots/smartbot_sims3.yaml`
- **Run:** `20261010-163917_0012-sims3-staller-triggers-split`
- **Verdict:** drop

## Hypothesis

Splitting 0011's two triggers: the lead lock alone (DD_TRIGGER=1000, the drawdown never fires) keeps the gains vs our own clones without 0011's losses and beats smartbot_sims3 by >= 1 pt; the drawdown stall alone (LOCK_Z=100, never locks) is what cost 0011 its leads vs smartbot, smartbot_sims, smartbot_geo and rotation_outcome, and is \<= 0 vs smartbot_sims3.

## Command

```bash
uv run janken lab experiment bots/sims3_staller.yaml:DD_TRIGGER=1000 bots/sims3_staller.yaml:LOCK_Z=100 bots/smartbot_sims3.yaml --rounds 200 --round-robins 200 --pool-size 20 --seed 314607615 --name 0012-sims3-staller-triggers-split
```

## Results

200 of 200 round robin(s), pool 20, 200 rounds/match, seed 314607615, mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| sims3_staller@511b62 | 4000 | 3093-71-836 | 78.2% [76.9%, 79.5%] | +19.8 | 0 | 1741 +/- 75 |
| smartbot_sims3 | 4000 | 3093-71-836 | 78.2% [76.9%, 79.5%] | +67.2 | 0 | 1740 +/- 70 |
| sims3_staller@553e5e | 4000 | 3063-89-848 | 77.7% [76.4%, 79.0%] | +65.6 | 0 | 1740 +/- 81 |

Paired comparisons:

- `sims3_staller@511b62 - sims3_staller@553e5e = +0.5 pts [-0.9, +1.9]` over 4000 shared matches: no significant difference
- `sims3_staller@511b62 - smartbot_sims3 = +0.0 pts [+0.0, +0.0]` over 4000 shared matches: no significant difference
- `sims3_staller@553e5e - smartbot_sims3 = -0.5 pts [-1.9, +0.9]` over 4000 shared matches: no significant difference

Weakest matchups of sims3_staller@511b62: tpi_lite 42.1%, achilles 47.0%, odysseus 49.6%, smartbot_sims2 50.0%, agamemnon 51.7%, smartbot_sims 53.7%.

Weakest matchups of sims3_staller@553e5e: tpi_lite 48.1%, hector 48.4%, nash 51.6%, agamemnon 53.0%, odysseus 53.0%, meta_smartbot 53.1%.

Weakest matchups of smartbot_sims3: tpi_lite 42.1%, achilles 47.0%, odysseus 49.6%, smartbot_sims2 50.0%, agamemnon 51.7%, smartbot_sims 53.7%.

## Analysis

The lead lock at LOCK_Z 4 only fires once the lead is 4 random-walk SDs above what the remaining rounds could undo, which in 200-round matches with smartbot_sims3's drift happens only in matches it was already going to win; it never converted a close match, so under match scoring it is a no-op (and the same RNG stream keeps every result identical). A looser lock (LOCK_Z 1-2) would lock coin-flip leads earlier, but random play forfeits sims3's positive drift, so it can only help against opponents that catch up late; nothing in 0010-0012 shows such opponents beyond noise. The drawdown stall's 15 random rounds after a -5 net over 20 rounds cost vs the adaptive non-clone bots in 0011 and are null-to-negative here. smart_staller's gain over meta_smartbot (pre-refactor) does not carry to the sims3 core.

## Verdict

**drop**. Neither stall trigger helps smartbot_sims3. Lead lock alone (DD_TRIGGER=1000) leaves every match result unchanged: +0.0 pts [+0.0, +0.0] vs smartbot_sims3 over 4000 paired matches (same 3093-71-836 record), only the round margin falls from +67 to +20. Drawdown stall alone (LOCK_Z=100): -0.5 pts [-1.9, +0.9]. So 0011's -0.8 came from the drawdown trigger, and idea #22 (Stall on smartbot_sims3) is dropped.
