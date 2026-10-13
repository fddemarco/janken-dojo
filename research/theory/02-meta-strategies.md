# L2 and up: aggregation, replays and gates

An L2+ bot combines bots: a bandit or a gate over arms, where an arm is an L1 signal
or a replay of a whole bot from either seat. This file holds what the top-down work
taught us, to be revisited level by level from the bottom (research/theory/README.md).

Phase: **specialised** at the top (replays of named bots); **bottom up from L2**
since 2026-10-13, starting with an L2 built from L1's strong set (`repeat_mirror`).

## Claims

1. **An L2 built from L1's strong set beats the field's L2s.** _supported._
   `repeat_mirror_v1` (both repeat followers from both seats and `geometry`, every
   rotation) beats `iocaine_lite_v1` by +7.3 pts [+3.0, +11.6] vs pools of L1s and
   L2s, confirmed on fresh seeds (notes 0063, 0064). The first result of the bottom-up
   direction: the L1 atlas named the strong set, and the L2 holding it wins.
   _Prediction:_ the same holds one level up. ~~An L3 built from the L2 strong set
   beats the field's L3s vs pools of L1-L3.~~ _Refuted_ (note 0065): a council of
   L2's strong set is -3.5 pts [-11.5, +4.8] vs `l2_council_v1`, see the next claim.

1. **A strong set made of counters doesn't transfer.** _supported._ Half of L2's
   strong set (L2 atlas) are counters (`anti_smartbot`, `anti_rps4`), strong in the
   L2 round robin because their prey fills it; as arms in a mixed L1-L3 pool they lose
   (note 0065). L1's strong set is made of learners, which do transfer (note 0064).
   _Prediction:_ an L3 built from L2's learners only (`geometry_ensemble`,
   `period_bandit`, `repeat_mirror`) beats `l2_council_v1` vs pools of L1-L3.
   _Refuted_ twice (notes 0066, 0067): from our seat it loses to its own arms; from
   both seats it ties (-2.8 pts), its holes moved elsewhere.

1. **Above L2, random pools saturate.** _supported._ Three L3 councils of different
   design (notes 0065-0067) tie `l2_council_v1` at 73-76% of matches; the best L4's
   gate and expert fixes tie their baseline in pools but resolve +5 to +8.5 pts on a
   list of hard opponents (ideas #60, #64). The differences between strong bots live
   in a few hard matchups that random pools dilute. _Prediction:_ evaluated on pools of
   hard opponents (idea #60), the same comparisons separate. _Supported on rounds_
   (note 0068): on hard pools `replay_hunter_wider` gains +21.2 rounds per match
   +- 11.7 over `replay_hunter_wide_v2`, where random pools tied them; its match-score
   gain (+3.8 pts) needs more round robins. _Refined_ (note 0069): on fresh seeds the
   round gain halves (+10.0 +- 9.9) and the match score shows none (-1.6 pts
   [-13.0, +9.9]). Hard pools separate round margins, not match wins: the extra
   experts widen matches already won.

1. **Replaying a named bot beats that bot, and only that bot.** _supported._ An exact
   replay or impostor wins its target outright (in note 0014, 96.8% of rounds vs
   agamemnon) but moves the pool score by about 1 pt, as the target is one pool slot.
   _Evidence:_ insights of 2026-10-13; notes 0014, 0015.

1. **The top bots don't overfit their opponents' exact parameters much.**
   _supported._ Against pools where every bot plays a parameter variant, the best L4
   and L5 lose only a few points of match score (notes 0050-0053). _Refines_ the
   starting worry of 2026-10-13 that L3-L5 were overfitted to exact defaults.

1. **Identifying an opponent's parameters pays only inside known species.**
   _supported._ A particle posterior names the species by round 150 89% of the time
   and gains 12.5 pts over rounds 151-250 when the species is a hypothesis; with an
   unknown architecture it loses 12.8 pts, and a switch between it and the probe
   only makes that safe (janken lab identify, ideas #51-53).

1. **A level gains most over the level just below.** _supported._ The L4 gate beats
   the best L3 vs L2s (+3.7 pts, significant) but only ties the best L2 vs L1s;
   no L5 is significantly better than the best L4 (notes 0026, 0027, 0051).

1. **The best L4's gate is at its optimum; its gains are in its experts.**
   _supported._ No tuned gate beats its defaults (note 0054). Single expert or gate
   fixes close specific holes (double_bluff_gate 33.6% --> 36.7% of rounds) but add
   about 2 pts vs random pools (notes 0056-0059), and +5 to +8.5 pts on a pool of the
   hard opponents (idea #64).

1. **A decayed bandit follows a level-switching opponent; a LEADER gate trails
   it.** _supported._ Notes 0032, 0055.

1. **The best L4 is overfitted to the field's architectures, not its parameters.**
   _supported._ It wins 80-85% of matches vs the field's L3-L4s all playing parameter
   variants (notes 0086-0088), but 61-65% (+5 rounds per match) vs outsiders, L3-L4s
   built from components it doesn't replay (research/gauntlet/outsiders.txt, notes
   0090-0095). There every field L4 scores about what its main does, and
   `smartbot_sims_v2` alone ties the best L4. Refines the claim above on parameters:
   the user's starting worry holds one level up. _Prediction:_ the same gap vs a second
   outsider family built from other components (idea #88). _Confirmed_ (note 0096):
   55% of matches there, tied with its main; `level_k_gate_v2`, which beats it in the
   field, wins 27%. In a census vs both families (note 0098) `sicilian_meta_v1` leads
   (66%, not significant over `smartbot_sims_v2`; it replays `iocaine_lite`, a
   component of the second family, so it may be reading a relative).

1. **Adding experts to the best L4's gate costs rounds, relevant or not.** _supported._
   Generalist learners played or only read, vs field variants or vs outsiders built
   from those learners: -2.5 to -4 rounds per match each time (notes 0086, 0090,
   0094); a gate edge costs too (note 0093). Mechanism open.

1. **Vs unknown opponents, a played deterministic learner is read exactly; a Thompson
   main holds.** _supported._ `context_mixture_v2` lost every match to the outsiders,
   `repeat_mirror_v1` 82%; `smartbot_sims_v2` and `l2_council_v1` win about 61%
   (note 0092). Even inside a Thompson council the learners are followed and read
   (-29 pts, note 0095).

## Open questions

- Are the strong strategies above L1 few enough to specialise against (the condition
  in README.md), and are they the same at their parameter variants?
- Does an evaluation on hard pools (idea #60) rank changes the same way head-to-head
  evidence does?
