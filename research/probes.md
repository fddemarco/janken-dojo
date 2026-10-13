# Probes: reading tournament bots from their final scores

The tournament's exports hold only each match's final score (rounds won by each bot,
and draws), never the moves. A **probe** turns that score into a measurement. It is a
bot that ignores its opponent and plays a fixed script of moves. Against a fixed
script, an opponent's final margin depends only on what kind of learner it is: how
far back it looks for patterns, and how fast it forgets. So each probe asks every bot
in the tournament one question, and the margins over five probes are that bot's
**fingerprint**. Comparing a fingerprint with those of the lab's bots against the same
probes names the lab bots that play most like it.

The opening-probe study (research/probe_study.md) asked the same question from inside
a match, with the moves in hand; this is the version for when only scores are
available.

## The five probes

All live in `bots/inactive/probes/` (outside the field, so never in a pool), built on
the `Script` signal (a fixed move sequence, repeated), and export with
`janken bot export <stem> --out exports/probes`.

| probe | script | the question it asks |
|---|---|---|
| `probe_cycle3` | rock, paper, scissors, repeated | does it learn the simplest pattern, and how fast? Fixed and reactive bots get nothing or lose |
| `probe_debruijn2` | a De Bruijn sequence of order 2 (9 moves, every pair once), repeated | does it look 2 moves back? One move of context predicts nothing |
| `probe_debruijn3` | order 3 (27 moves, every 3 in a row once), repeated | does it look 3+ moves back on our moves alone, or find long repeats? |
| `probe_debruijn4` | order 4 (81 moves, every 4 in a row once), repeated | does it find long repeats (longest match, rfind, Markov of order 4+)? |
| `probe_blocks50` | 50 rocks, 50 papers, 50 scissors, repeated | how fast does it re-adapt after a switch (how fast it forgets)? |

A De Bruijn sequence of order k holds every run of k moves exactly once per period,
so a context shorter than k moves is followed equally often by each move: a bot that
looks fewer than k moves back scores about 0, one that looks k or more back (or
matches whole repeats) learns the sequence after one period and wins almost every
round after it.

A sixth candidate, a fixed sequence with no pattern but half rocks, was dropped: it
barely separated the lab's bots (about -10 to +20 rounds for nearly all), and our own
V3 core only draws with it, so it would cost the fleet matches.

## What the lab's bots show (250 rounds, margin of the bot over the probe)

From the first fingerprint of every field bot (3 seeds; the gauntlet log `probes`
holds the full run):

| family | cycle3 | debruijn3 | debruijn4 | blocks50 |
|---|---|---|---|---|
| fixed and reactive L1s (rock, copycat, win-stay, nash) | -250 to 0 | about 0 | about 0 | -50 to +240 |
| an undecayed frequency counter (`frequency_v1`, the house bot Brainy) | -33 | +14 | +8 | +75 |
| L1 learners with 1-2 moves of context or joint contexts (`markov2_joint`, `pattern_memory`, `second_repeat`, CTW, `iocaine_lite`, `repeat_mirror`) | +220 to +247 | -25 to +45 | -10 to +45 | +205 to +245 |
| L2s with a deep sequence learner (`backoff_family`, `fast_greedy_markov`) | +225 to +245 | +195 to +215 | +25 to +40 | +215 to +235 |
| L2s with long repeats on our moves (`smartbot`, `second_guess`, `geometry_ensemble`, `dropswitch_matcher`, `multiscale`) | +245 | +215 to +240 | +120 to +220 | +235 to +242 |
| the smartbot-based L3-L5s (both fleet cores among them: V3 `gate_main_first_v1` +242 / +224 / +209 / +236, V4 `replay_hunter_wide_v1` +246 / +234 / +218 / +238; both beat `probe_debruijn2` by +235 or more) | +240 to +246 | +210 to +235 | +200 to +225 | +235 to +242 |
| L3s without a deep learner (`sicilian_meta`, `predator`, `gate_bandit_period`, the first outsiders) | +215 to +245 | about 0 to +30 | about 0 to +30 | +160 to +240 |

Held out one at a time, every lab bot's nearest fingerprint is a bot of its own
family (the smartbot-based L3-L5s 2-5 rounds apart, the L1 learners 10-16, the
period learners 10), and bots that differ by tens of rounds are different families.
So the probes separate the families clearly: the order-3 and order-4 probes tell
apart "looks a few moves back" (about 0), "deep Markov but not long repeats" (+200
then +30) and "long repeats" (+200 on both). `blocks50` singles out slow forgetters
(an undecayed counter: +75; fast adapters: +235 and more). Every fleet core beats
every probe by 200 rounds or more, so submitting the probes costs the fleet nothing.

## Limits

- **A fingerprint names a family, not a species.** Within a family (the smartbot-based
  L3-L5s) the margins differ by a few rounds, inside a match's noise (about +-15
  rounds at 250 rounds).
- **It reads how a bot learns, not whether it reads us.** A script ignores its
  opponent, so it can't show whether a bot replays our own bots (the question of the
  outsider benchmark, theory 02). That needs a probe that plays like one of our bots,
  which the fleet's cores already are.
- **Openings and noise shift the margins by a few rounds.** A bot with a 10-move
  opening or 5% random moves loses some rounds to every probe alike; the comparison
  is between families, tens of rounds apart, so it survives that.
- **Each probe needs several matches against each bot** (the tournament plays each
  pair about 5-20 times over a few days, judging by the exports).

## How to use it

1. Export the probes (`janken bot export probe_cycle3 --out exports/probes`, and the
   other four) and submit them under names that contain their stems, such as
   `Probe_Cycle3` or `Probe DeBruijn4`: a tournament bot is read as a probe when its
   name, reduced to letters and digits, contains the stem's (`gauntlet.fingerprint_probes`).
1. Play the probes vs the lab's bots once (the lab side; already done in the `probes`
   log):
   `janken lab gauntlet run research/gauntlet/fingerprint_lab.txt --cand bots/inactive/probes/probe_cycle3.yaml ... --name probes --rounds 250 --no-sequential`.
1. After the tournament has played them for a while, export the matches and run
   `janken lab gauntlet fingerprint logs/<export>.csv --name probes`: every bot that
   met a probe, its margins per round, and the `gauntlet.fingerprint_nearest` closest
   lab bots.
