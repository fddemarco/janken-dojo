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

1. Export the probes and make the upload copies, named by their aliases
   (`gauntlet.fingerprint_aliases`: Nimbus = cycle3, Thistle = debruijn2, Corvina =
   debruijn3, Marigold = debruijn4, Bramble = blocks50), so other players can't tell
   from a name what they are. The copies drop the export's header comment, which
   names and describes the probe; the code is unchanged:

   ```bash
   for b in probe_cycle3 probe_debruijn2 probe_debruijn3 probe_debruijn4 probe_blocks50; do
     uv run janken bot export $b --out exports/probes
   done
   mkdir -p exports/probes/upload
   for pair in Nimbus=probe_cycle3 Thistle=probe_debruijn2 Corvina=probe_debruijn3 Marigold=probe_debruijn4 Bramble=probe_blocks50; do
     awk 'NR==1,/^$/{if (/^#/ || /^$/) next} {print}' exports/probes/${pair#*=}/${pair#*=}.py > exports/probes/upload/${pair%%=*}.py
   done
   ```

   Submit each under its alias. A tournament bot is read as a probe when its whole
   name matches an alias (ignoring case and punctuation), or when its name contains a
   probe's stem (`Probe_Cycle3`).

1. Play the probes vs the lab's bots once (the lab side; already done in the `probes`
   log):
   `janken lab gauntlet run research/gauntlet/fingerprint_lab.txt --cand bots/inactive/probes/probe_cycle3.yaml ... --name probes --rounds 250 --no-sequential`.

1. After the tournament has played them for a while, export the matches and run
   `janken lab gauntlet fingerprint logs/<export>.csv --name probes`: every bot that
   met a probe, its margins per round, and the `gauntlet.fingerprint_nearest` closest
   lab bots.

## First reading (tournament export of 2026-10-14, 1700 matches vs the probes)

35 bots met the probes, 30 of them at least 4 times each (most 6-17). Margins are per
round played; nearest lab bots by `janken lab gauntlet fingerprint`.

- **Calibration holds.** The house bots, whose code we know, land where they should:
  Rocky on `rock_v1` (0% away), Copycat on `wsls_v1` / `copycat_v1` (the reactive
  family, -100% vs cycle3), Brainy among the frequency counters (`frequency_v1` 8%
  away; only blocks50 pays it, +20%), Randy at 0 on every probe.
- **Most strong bots are our cores' family.** Bot Snow, Botman, Claudy, Jevsusnator,
  Moriartsusnator, Harry Botter, Metajevsusnator, Yiscroftnator, Ginny, Lord Botemort,
  Bot Riddle, Raging Kratos, Hannibot Lecter, Darth Botter 442b and Sparks all score
  +93% to +99% on cycle3 and debruijn2, +86% to +94% on debruijn3 and +76% to +90% on
  debruijn4: deep learners that find long repeats on our moves, 0-2% from the
  smartbot-based gates (`gate_main_first_v1`, our V3 core, among them). Matches with
  them are mirror matches, which is why they are coin flips.
- **Some add randomness.** AtendeDOS, Atendedor De Botludos, Viejo (Im)putable and Sir
  Claude Von Janken learn every probe but stop at +76% to +90%: the same learners with
  about 10-20% random moves (AtendeDOS also scores only 208 vs Rocky). Darth Botter
  0b0f stops near +45% on every probe: about half its moves random.
- **Charly is Nash-like:** about 0 on every probe, like Randy. No bot can beat it by
  more than luck.
- **The weak ones look 1-2 moves back:** AuraFarmer (debruijn2 +85%, debruijn3 +7%),
  Bitsy (debruijn2 +29%), Magnus Jankssen (cycle3 and blocks50 only), Megaman.

So the probes have done their job: the tournament's strong field is one family, our
own, plus noisier and Nash-like variants of it. More matches won't split that family,
since species within it differ by less than a match's noise.

## Field twins: a bench that looks like the tournament (2026-10-14)

The five scripts saturate on strong bots: Claudy (we win 99%) and Bot Snow (we win
36%) fingerprint the same. Adding one adaptive probe separates them, and we already
have it: our V3 fleet's real record against each bot. In the lab, a bot's margin vs
`smartbot_v1` predicts its margin vs the V3 core with leave-one-out R^2 0.91 over 81
strong lab bots (gauntlet log `reactive-probes`), so the V3 core is the right
adaptive probe.

- **Twins**: lab bots (the field, the outsiders, 240 strong random-architecture bots,
  and those wrapped in 10-20% noise, `bots/inactive/noisy/`) whose margins over the
  five scripts and vs the V3 core are within 0.04 of a tournament bot's (its real
  margin vs our V3 fleet). 18 of the 19 strong tournament bots have twins (not Bitsy);
  the noisy ones fit 10-15% noise. Lists: `research/gauntlet/twins_train.txt` and
  `twins_test.txt` (each tournament bot's twins alternate between them).
- **Validation**: the V3 core vs each bot's twins predicts its real match share with
  rank correlation +0.61 over 18 tournament bots, mean 56.6% predicted vs 58.7% real
  (Metajevsusnator the outlier: 23% vs 55%).
- **Search** (gauntlet logs `bench-train`, `bench-test`; shares of matches won):
  - the V3 core is the best of 12 candidates on the train bench (66.7%): the field's
    L3-L4s, and new mains that read the readers or go a level up (-15 to -30 pts);

  - none of 13 gate and main parameter changes beats its defaults;

  - the computed replay estimate (`gate_main_first_v3`) ties the 256-draw replay
    (-5.6 pts train, +1.7 test, CIs about +-10), and the fleet's handshake costs
    nothing;

  - V3 upgraded with the strong learners found since (`gate_main_first_plus`) ties or
    loses: -11.1 pts on train, -0.7 on test, vs `gate_main_first_v3`.

  - being less predictable hurts (full bench, 312 paired matches each, vs
    `gate_main_first_v3`): 5% random moves -7.5 pts +-7.3, Thompson sharpness 2
    -9.5 +-6.9, sharpness 0.5 -2.6 +-7.1. V3 doesn't lose to these bots by being
    read; its edge is reading them, and its default selection is the best of three.

  - stronger opponent models alone in V3's main (the strong L1 learners, 3 ways each)
    lose too: -5.8 pts +-7.0. More arms dilute the main, as more experts dilute a
    gate (theory 02).

  - pruning V3's main loses too (-2.3 to -6.6 pts): every arm pulls its weight.

  - **the expert is the lever**: replaying `l2_council_v1` from the opponent's seat
    instead of `smartbot_sims_v2` (`gate_mf_expert_l2_council`) is the one change
    that held: +5.2 pts +-5.3 and +1.6 rounds +-1.5 on 624 fresh paired matches;
    pooled over 936, +3.1 pts +-4.4 (59.6% vs 56.5% of matches) and +0.9 rounds
    +-1.3 vs V3's deployed core, +4.0 pts +-4.2 vs its estimate version. Exported as
    the Iliad v5 fleet (`bots/inactive/fleets/iliad_v5/`, menelaus_v1 and
    patroclus_v1): 1.5 ms a move vs 51 for V3's export and 269 for V4's (which timed
    out). Next: a tournament A/B next to the V3 fleet.

Apart from the expert, V3's core sits at a local optimum against twins of the real
strong bots. The bench
resolves about +-10 points per comparison at these sizes; a 3-point gain needs about
1000 paired matches per comparison.
