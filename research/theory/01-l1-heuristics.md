# L1: single heuristics

An L1 bot plays one signal turned by one rotation: no memory of how its prediction
fared, no choice between ideas. Data: research/l1_atlas.md (19 species, every pair).

Phase: **diversify** (2026-10-13). Next: fill the gaps below, then specialise if the
strong set stays small.

## Claims

1. **Two tiers.** _supported._ L1 splits into learners, which model the opponent's
   moves from the history (patterns, transitions, periods, geometry, outcomes), and
   prey: fixed, cyclic, reactive and frequency strategies. The six learners win
   76-90% of their matches vs the other L1s; the prey are each beaten by 3-13 L1s
   by more than 5 rounds per match. _Evidence:_ L1 atlas, two seeds, 10 matches per
   pair.
1. **The strong set is small.** _supported._ `pattern_memory` and `geometry` tie at
   the top and beat the other four learners; the middle four sit within ~4 rounds
   per match of each other. _Evidence:_ the learners' round robin, 100 matches per
   pair. _Prediction:_ adding parameter variants of the learners (`pool.variants`)
   keeps the same top two; if not, the strong set is a parameter accident.
1. **L1 is non-transitive at the margins.** _supported._ A cycle among the middle
   learners (`markov2_joint` > `period_detector` > `transition_matrix` ~
   `markov2_joint`), and `rotation_outcome`, last among the learners, is the only one
   that beats `period_detector` (+14 rounds per match). So no single L1 is best, and
   the level above has something to choose between.
1. **Unbeaten L1s are gaps, not ceilings.** _conjecture._ No L1 beats
   `pattern_memory`, and `geometry` and `transition_matrix` have at most one weak
   counter. Each is a deterministic rule of the history, so an L1 that computes the
   same rule from their seat and plays its beat should win by a wide margin.
   _Prediction:_ such a counter-L1 wins more than 40% of rounds vs its target (idea
   #65).
1. **Nash is the floor, not a strategy.** _supported._ `nash_v1` is beaten by noise
   only (-1 round per match overall): unexploitable, never exploiting. A learner's
   value is how far above it the learner stays vs every other L1.

## Open questions

- Which strategy families are missing at L1 (the kit signals with no species:
  backoff, longest and second match, rarest, relative, score state)? Idea #63.
- How much of each learner's strength is its parameters? The space files allow
  variants; the atlas used defaults only.
- What can no L1 do, that L2 must add? Candidate: knowing which of its predictions
  works against this opponent (L1 has no record of its own success).
