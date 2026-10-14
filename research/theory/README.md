# Theory: the lab's model of rock-paper-scissors

`insights.md` records findings one at a time. This folder holds the **theory** they add
up to: what we believe about how RPS bots win and lose, paradigm by paradigm, what
would refute it, and what we're doing about it. An experiment either confirms a claim,
refutes it, or opens a question. The theory is rewritten as that happens; the history
stays in the journal below and in git.

## The cycle: diversify, specialise, diversify

The lab alternates two phases, at every level of bots (research/README.md, Research
direction: bottom up, by level):

1. **Diversify.** Widen the field before narrowing it: new strategy families, the
   kit's unused signals, variants of parameters. A field of near-copies teaches
   nothing, and a bot tuned against it overfits it.
1. **Specialise (overfit, on purpose).** When the level's strong strategies are
   **few** (a handful win most matchups), a specialist per strong strategy can pay: a
   replay or counter of each, gated. When they are many, specialists dilute (one
   opponent is one pool slot in ~40: insight of 2026-10-13), and generalists win.
1. **Diversify again**, against the specialists: the counters of the counters, until
   the field's strong set changes. Then specialise again.

Before specialising, check the condition: how many strategies win most matchups at
this level, and do they stay strong across their parameter variants (`pool.variants`)?
A specialist for a strategy that isn't in the strong set, or that only exists at one
parameter setting, is overfitting by accident.

## The scientific lifecycle of a claim

Each paradigm file states claims with a status:

- **conjecture**: believed, not yet tested;
- **supported**: an experiment could have refuted it and didn't (with its notes or
  runs);
- **refuted**: an experiment contradicted it (struck through, kept, with the
  evidence);
- **open question**: what we don't know and how we'd find out.

Every claim names the observation behind it and a **prediction** that would test it.
A claim with no possible refutation isn't a claim.

## Paradigms

| file | paradigm | phase |
|---|---|---|
| [01-l1-heuristics.md](01-l1-heuristics.md) | single heuristics: one signal, one rotation | specialise: each strong L1 has an exact L1 counter; next, an L2 holding them |
| [02-meta-strategies.md](02-meta-strategies.md) | aggregation: bandits, gates, replays (L2 and up) | bottom up from L2: atlas done; a strong set of counters didn't transfer |
| [algorithms/](algorithms/README.md) | the learning, ML and statistical algorithms, in use and candidates, with their exploits and size budget | reference |

## Journal

- **2026-10-13.** Theory started. After a day of top-down work (identification of
  opponent parameters, L5 bots, gate tuning, wider experts), the evidence says the top
  bots' remaining gains are narrow, a few points that pools can't resolve. The user
  set the direction: bottom up by level, diversify and specialise in turn. First step:
  the L1 atlas (research/l1_atlas.md), which finds L1's strong set small (two
  learners at the top, four close behind).
- **2026-10-13, later.** L1 atlas with 20 species and the counter map: four families
  (fixed, reactive, frequency, learners), each with a natural counter, and a small
  strong set (the repeat followers and `geometry`) with no strong counter at L1. New
  species `second_repeat_v1` (note 0060) tops the L1 round robin; `backoff_ngram`
  re-derived the longest repeat and was dropped (note 0061). Process lesson: a
  diversity candidate's evaluation baseline declares a succession at classify time
  (research/README.md, Research direction, step 3).
- **2026-10-13, later still.** Conjecture refuted: the strong L1s have exact L1
  counters, their own rule on our moves turned BEAT_BEAT (about 95% of rounds vs each,
  note 0062), each useless elsewhere. L1 moves to **specialise**: the counters become
  arms of an L2 beside the strong L1s.
- **2026-10-13, end of the bottom-up hour.** First replicated gain of the direction:
  `repeat_mirror_v1`, an L2 built from L1's strong set, beats `iocaine_lite_v1` by
  +7.3 pts [+3.0, +11.6] on fresh seeds (notes 0063, 0064). Next: an L2 atlas, to
  find L2's strong set and its counters, as at L1.
- **2026-10-13, L2.** The L2 atlas (research/l2_atlas.md) shows L1's three-part
  shape one level up: adaptive bandits share one natural counter (`anti_smartbot`),
  near-deterministic L2s fall to their exact replay counter, and a small strong set
  has no strong counter. But building an L3 from that strong set fails (note 0065):
  half of it are counters, strong only where their prey is common. Algorithm cards
  added (`algorithms/`), for the RL, ML and statistical methods in use and the
  candidates, with their exploits and the 200 MB export budget.
- **2026-10-13, step back.** Three L3 councils built from L2's strong set tie the
  field's L3 council (notes 0065-0067): above L2, random pools saturate, and the lab's
  evaluation can't see what separates strong bots. Next: hard-opponent pools
  (idea #60) before more L3 designs.
- **2026-10-13, close of session.** Hard-opponent pools exist (`pool.lists`, idea
  #60) and work as predicted on rounds: a change random pools tied gains +21.2 rounds
  per match on them (note 0068). Next session: grow 0068 to resolve match score, then
  revisit the L3 councils (notes 0065-0067) on hard pools, and the L1 diversity ideas
  (CTW, families with no signal).
- **2026-10-13, learning.** Two new stage kinds: context-tree weighting
  (`context_mixture_v1`, the L1 with the widest margins) and a pre-trained prior
  (`pretrained_context_v1`, +9.8 pts [+5.6, +14.4] over CTW on parameter variants,
  confirmed: notes 0071-0073). Pre-training generalises across parameters; online
  combining (VW over the strong L1s) is level with the best L2 (ideas #72-75).
- **2026-10-13, opening probes** (the user's idea; research/probe_study.md). A
  scripted 24-round opening names an opponent's coarse class (simple rule, L1
  learner, adaptive L2+) 80% of the time vs held-out variants, 21 pts above a random
  opening; families and species stay unreliable (52%, 43% at 48 rounds). It costs
  about 2.8 rounds per match; whether knowing the class pays is next (ideas #77, #78).
- **2026-10-13, probes answered.** Knowing an opponent's family is worth +10 to +12
  rounds per match (oracle), but a probe's classifier loses it on mistakes; a gate
  over every family's natural counter identifies by record and gains most (+18 rounds
  per match over `repeat_mirror` in the arena). In the kit that gate is an L3 that ties
  the field's L3 council (notes 0074, 0075): a fourth L3 design at the same score.
- **2026-10-13, close of the learning hour.** Pre-training pays where a learner starts
  weak, and a light prior pays most: `pretrained_context_v2` (prior worth 1
  observation) beats v1 (worth 5) by +7.3 pts vs whole-field variant pools, and both
  beat CTW by 12-30 pts there; as an arm beside strong online arms the prior adds
  nothing (note 0077). Opening probes: the family is worth knowing, but records
  identify it better than a script (notes 0074, 0075).
- **2026-10-13, last.** The pre-trained prior is a cold start, and a longer context
  sharpens it: `pretrained_context_v3` (4 joint moves, 158 KB) beats v2 (3 moves) by
  +7.9 pts on whole-field variants (note 0080). Next: the prior inside the strong
  online learners as their cold start (CTW's KT counts, the repeat followers' empty
  matches), and k = 5 with a hashed table.
- **2026-10-13, end of session.** More loop steps: one-sided models stay weak (CTW over
  the opponent's own moves, note 0081); CTW should forget (decay 0.81: +8.2 pts,
  `context_mixture_v2`, notes 0082-0083), but not faster (0.72 didn't confirm, notes
  0084-0085).
- **2026-10-13, unknown L3-L4s.** A held-out benchmark: outsiders, L3-L4s built from
  components no field L4 replays. The best L4 wins 80-85% of matches vs the field's
  L3-L4 variants but only 61-65% vs outsiders, where it's no better than its main
  alone (notes 0086-0095): overfitted to architectures, not parameters. Nine changes
  (new experts, mains, gate edge and decay, learner councils) all tied or lost. Next:
  a second outsider family, and logging which experts lead vs outsiders.
- **2026-10-13, close of the unknown-L3-L4 hour.** The overfitting holds vs a second
  outsider family (note 0096), and a census of the 27 field L3-L4s vs both families
  (note 0098) ranks self-contained councils first (`sicilian_meta_v1` 66%,
  `smartbot_sims_v2` 61%) and the replay-built bots last. Next: confirm
  `sicilian_meta_v1` on fresh seeds (idea #90), then build the next gate on the
  winner as its main, judged on outsiders and the field together.
- **2026-10-13, probing the tournament.** The competition's exports hold scores only,
  so five scripted probes (the `Script` signal: a cycle, De Bruijn sequences of order
  2-4, switching blocks) turn final scores into fingerprints: how far back a bot looks
  and how fast it forgets. In the lab they separate families cleanly, and every fleet
  core beats each by 200+ rounds (research/probes.md, `janken lab gauntlet fingerprint`).
- **2026-10-13, generated opponents.** Unknown strong bots can't be written by hand in
  numbers, so they are sampled: random architectures from the kit's grammar, the strong
  half kept, two seeds as train and test (idea #91). They reproduce the tournament's
  verdict (the V3 core over V4) and retire the outsider census's leader (idea #90,
  dropped). Next: tune the V3 core on the train population, confirm on test.
- **2026-10-14, field twins.** Scripts saturate on strong bots, but our V3 fleet's real
  records are an adaptive probe: with them, lab twins of 18 strong tournament bots
  predict V3's real record (rank correlation +0.61). On that bench V3's core is at a
  local optimum: no new main, parameter or upgrade with the newer learners beats it,
  and the computed replay estimate ties the 256-draw replay (research/probes.md).
