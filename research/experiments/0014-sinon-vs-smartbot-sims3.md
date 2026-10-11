# 0014: sinon vs smartbot_sims3

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #25
- **Candidates:** `bots/sinon.yaml`
- **Baselines:** `bots/smartbot_sims3.yaml`
- **Run:** `20261010-165203_0014-sinon-vs-smartbot-sims3`
- **Verdict:** keep

## Hypothesis

sinon (smartbot_sims3 + Team IMPOSTOR) wins every match vs agamemnon (~97% of rounds) and pays at most a round or two of handshake vs everyone else, so it beats smartbot_sims3 in the paired comparison by about the share of its matches against agamemnon (~1/40 of pool slots: +1 to +2 pts), with no loss vs the other bots.

## Command

```bash
uv run janken lab experiment bots/sinon.yaml bots/smartbot_sims3.yaml --rounds 200 --round-robins 40 --pool-size 20 --seed 2582389146 --name 0014-sinon-vs-smartbot-sims3
```

## Results

40 of 40 round robin(s) · pool 20 · 200 rounds/match · seed 2582389146 · mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating ± sd |
|---|---|---|---|---|---|---|
| sinon | 800 | 592-12-196 | 74.8% [71.6%, 77.6%] | +68.1 | 0 | 1722 ± 85 |
| smartbot_sims3 | 800 | 582-20-198 | 74.0% [70.9%, 76.9%] | +62.2 | 0 | 1715 ± 61 |

Paired comparisons:

- `sinon − smartbot_sims3 = +0.8 pts [-2.7, +3.9]` over 800 shared matches: no significant difference

Weakest matchups of sinon: achilles 36.0%, odysseus 37.5%, smartbot_sims 40.5%, geometry 47.6%, sims3_second 47.7%, nash 48.1%.

Weakest matchups of smartbot_sims3: nash 29.6%, ajax 37.0%, sims3_staller 42.0%, hector 44.0%, achilles 46.0%, meta_smartbot 47.6%.

## Analysis

Mechanism: Team.team_move authenticates a support by the 8-move handshake and one role move only. sinon plays both, agamemnon (CHAMPION) answers ROCK and then plays PAPER every round from round 10, expecting a thrown ROCK; sinon plays SCISSORS. Each 250-round match is 8 tied handshake rounds, then 242 wins. Against outsiders the handshake breaks at their first mismatch (usually round 0 or 1), the same cost smartbot_sims3's opponents already pay vs the fleet; vs the supports (achilles 36% vs 46, ajax 52 vs 37, hector 58 vs 44, odysseus 38 vs 55; 20-27 matches each) the differences go both ways and are noise. Implication for the fleet design (idea #19): its handshake is a shared secret any pool bot can replay, so a champion that trusts it is exploitable by a single impostor; a challenge-response (e.g. a role move derived from the opponent's moves) would close it.

## Verdict

**keep**. sinon (smartbot_sims3 posing as a fleet support, Team role IMPOSTOR) beats agamemnon outright: 21 of 21 matches in the run (+192 rounds a match; smartbot_sims3 69%), and 96.8% of rounds over 10 x 250-round matches (seeds 1-10; smartbot_sims3: 33.1%). Over the whole pool sinon - smartbot_sims3 = +0.8 pts [-2.7, +3.9] (800 paired matches): agamemnon is 1 of ~40 pool slots, so a sure win vs it moves the pool score by about the measured +0.8 and the CI can't exclude 0. Kept for the decisive, deterministic result vs agamemnon; no cost elsewhere is detectable.
