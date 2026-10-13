# L2 and up: aggregation, replays and gates

An L2+ bot combines bots: a bandit or a gate over arms, where an arm is an L1 signal
or a replay of a whole bot from either seat. This file holds what the top-down work
taught us, to be revisited level by level from the bottom (research/theory/README.md).

Phase: **specialised** (the field's top is built of replays of named bots). To revisit
bottom up, after L1.

## Claims

1. **Replaying a named bot beats that bot, and only that bot.** _supported._ An exact
   replay or impostor wins its target outright (96.8% of rounds vs agamemnon, note
   0014\) but moves the pool score by about 1 pt, since the target is one pool slot.
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

## Open questions

- Are the strong strategies above L1 few enough to specialise against (the condition
  in README.md), and are they the same at their parameter variants?
- Does an evaluation on hard pools (idea #60) rank changes the same way head-to-head
  evidence does?
