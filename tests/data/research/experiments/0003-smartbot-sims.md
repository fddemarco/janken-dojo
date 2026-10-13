# 0003: "model of us" sim predictors in the metabot

- **Date:** 2026-10-09
- **Status:** analyzed
- **Idea:** ideas.md #3 (bot-specific beaters), first cut
- **Bots:** `bots/smartbot_sims.py` (new), baseline: `bots/smartbot.py` (predecessor, same
  constants and bandit)

## Hypothesis

smartbot predicts the opponent only from the opponent's side. Several zoo bots are
near-deterministic models of *us* that play the beat of our predicted move, and smartbot
beats them by only +3...+10 rounds per 200 ([0002](0002-tune-smartbot.md): iocaine_lite
61%, pattern_memory 62%, markov2_joint 74%, staller 81%, word2janken 89%).
`smartbot_sims` adds five predictors that replay those models from the opponent's side
(word2janken/staller's n-gram, pattern_memory, markov2_joint, iocaine_lite,
transition_matrix), each as three arms. Everything else is smartbot.

Expectation: **smartbot_sims - smartbot >= +3 pts** in the paired comparison (about +5 if
the five mid-tier matchups go to ~95-100%). The gain should sit entirely in those
matchups; against the strong adaptive bots (metabots, geometry, rps4_lite, nash) we
expect no change, or a small loss from 15 more arms diluting the bandit.

Pre-run diagnostic (scratchpad Python, not a stored run; 4 matches each): sim accuracy vs
its target bot is pattern_memory 0.97, word2janken 0.91, iocaine_lite 0.90,
markov2_joint 0.76; match margins +167, +142, +146, +63 rounds. Staller is only +23
(it switches between three rotations of the janken prediction, and its scoreboard uses
its own noisy draws), and transition_matrix +24 (it samples).

## Command

```bash
uv run python -m janken experiment bots/smartbot_sims.py bots/smartbot.py --rounds 200 --round-robins 40 --name 0003-smartbot-sims
```

Run id: `20261010-000022_0003-smartbot-sims` (seed 2577442715, 40 round robins, 9240
matches on numba, 0 forfeits)

## Results

| bot | score vs pool [95% CI] | rounds +/- per match | rating +/- sd |
|---|---|---|---|
| smartbot_sims | 87.2% [84.7, 89.3] | +87.6 | 1833 +/- 60 |
| smartbot | 78.1% [75.1, 80.8] | +65.0 | 1751 +/- 75 |

Paired comparison: `smartbot_sims - smartbot = +9.1 pts [+6.1, +12.2]` over 800 shared
matches. Head to head: 19-3-18 (51.2%), margin +0.1: the sims don't help against
smartbot itself.

Per opponent (paired, 31-39 matches each; duckdb over `matches.parquet`):

| opponent | sims | smartbot | diff | margin sims / smartbot |
|---|---|---|---|---|
| pattern_memory | 100.0 | 51.6 | +48.4 | +164.3 / +0.6 |
| transition_matrix | 73.7 | 32.9 | +40.8 | +4.1 / -2.0 |
| iocaine_lite | 100.0 | 68.6 | +31.4 | +147.7 / +4.6 |
| markov2_joint | 100.0 | 75.6 | +24.4 | +64.6 / +6.3 |
| rps4_lite | 77.0 | 56.8 | +20.3 | +7.3 / +2.9 |
| staller | 100.0 | 81.6 | +18.4 | +21.8 / +8.2 |
| word2janken | 100.0 | 88.6 | +11.4 | +151.3 / +11.2 |
| meta_smartbot | 60.0 | 51.4 | +8.6 | -0.2 / -2.2 |
| smartbot_geo | 56.3 | 50.0 | +6.3 | +0.9 / -0.3 |
| geometry | 45.3 | 48.4 | -3.1 | -1.3 / +0.2 |
| smart_staller | 50.0 | 52.9 | -2.9 | +0.5 / +1.8 |
| nash | 41.2 | 44.1 | -2.9 | -3.0 / -1.4 |
| 11 trivial bots | 96-100 | 95-100 | 0...+1.4 | saturated |

All five targeted bots go to 100% (transition_matrix, which samples its move, to 74%).
rps4_lite also gains +20 pts though it has no dedicated sim: its order-k tables of *our*
moves resemble sim_markov2 / sim_janken. The small losses against geometry,
smart_staller and nash are inside the noise (round margins within +/-3).

Weakest matchups of smartbot_sims: nash 41.2% (pure random, unwinnable), geometry 45.3%,
smart_staller 50.0%, smartbot_geo 56.3%, meta_smartbot 60.0%, transition_matrix 73.7%,
rps4_lite 77.0%.

## Verdict

**keep**. Predicting the opponent as a model *of us* (replaying its algorithm from its
side of the board) is worth +9.1 pts [+6.1, +12.2], almost double the expected effect, and
the effect sits exactly in the targeted matchups. smartbot_sims is the new best bot.
Recorded in insights.md. What is left is the adaptive, stochastic group (metabots,
geometry, smart_staller, rps4_lite, transition_matrix), which only a sim of *their*
randomised decisions, or a better bandit, can reach.
