# L1: single heuristics

An L1 bot plays one signal turned by one rotation: no memory of how its prediction
fared, no choice between ideas. Data: research/l1_atlas.md (20 species, every pair;
the species and their natural counters).

Phase: **specialise** (2026-10-13). Done: the atlas, the counter map, one new species
(`second_repeat_v1`, note 0060), and an exact mirror counter for each strong repeat
follower (note 0062). The strong set is small and each member has a counter, so the
next step is to specialise one level up: an L2 that holds the strong L1s and their
counters. Still open at L1: the families with no signal, and a counter of `geometry`.

## Claims

1. **Four families, each with a natural counter.** _supported._ Fixed strategies
   (`rock`, `biased`) fall to a frequency count; reactive ones (fixed rules of the
   last round: `copycat`, `reactionary`, `counter_reactionary`, `self_beater`,
   `wsls`, `cycler`) all fall to one model of the rotation, `rotation_outcome`
   (+224 to +248 rounds per match); frequency rules form a chain where each counting
   rule beats the one below (`frequency` < `anti_frequency` < `balancer_hunter`) and
   any learner beats them all; learners counter each other weakly. _Evidence:_ the
   atlas's counter map (20 matches per pair). _Prediction:_ a new reactive L1 (any
   fixed rule of the last round) loses to `rotation_outcome` by 200+ rounds per match.
1. **Two tiers.** _supported._ Learners, which model the opponent's moves from the
   history, win 72-87% of their matches; the fixed, reactive and frequency
   strategies are prey, each beaten by 8-14 L1s by more than 5 rounds per match.
1. **The strong set is small: the repeat followers and geometry.** _supported._
   `second_repeat`, `pattern_memory` and `geometry` (84-87% of matches) have no L1
   counter above +6 rounds per match; the other learners have one (`pattern_memory`
   beats `rotation_outcome` by 60 and `markov2_joint` by 31). _Prediction:_ adding
   parameter variants of the learners (`pool.variants`) keeps the same top three; if
   not, the strong set is a parameter accident.
1. **Following a repeat beats fixed-order models.** _supported._ The longest-repeat
   follower beats the order-2 Markov model by 31-33 rounds per match (100 matches per
   pair), and following the second-longest repeat is as strong (note 0060: +6.3 pts
   [+0.3, +12.9] over `markov2_joint` in an L1 pool). A fixed context is a special
   case of the longest repeat; a variable-order n-gram (`backoff_ngram`, note 0061)
   only re-derives the longest repeat (83% core agreement).
1. **L1 is non-transitive at the margins.** _supported._ A cycle among the middle
   learners (`markov2_joint` > `period_detector` > `transition_matrix` ~
   `markov2_joint`), and `rotation_outcome`, last among the learners, is the only one
   that beats `period_detector` (+14 rounds per match).
1. ~~**The strong set's counters are not at L1.**~~ _refuted_ (note 0062). We
   conjectured that countering a top learner needs a replay (an L2+ arm). It
   doesn't: the learner's own rule computed on our moves (`of: MY`) and played
   BEAT_BEAT is an L1, and it wins about 95% of rounds vs its target.
1. **Each strong L1 has an exact L1 counter, useless elsewhere.** _supported._
   `anti_pattern` wins 94.7% of rounds vs `pattern_memory`, `anti_second_repeat`
   95.0% vs `second_repeat` (10 of 10 matches each), but they score 27 pts below
   `pattern_memory` in an L1 pool, draw or lose vs the other strong L1s, and fall to
   `geometry` (note 0062). So the strong set is countered one by one, by specialists.
   _Prediction:_ an L2 holding the strong L1s and their mirror counters as arms beats
   an L2 holding the strong L1s alone vs a pool of L1s and L2s. _Unresolved:_ +2.8
   pts [-4.0, +9.5] (note 0063).
1. **Reactions to us and rotations are one family.** _supported._ A rotation model
   conditioned on the last outcome is the same from either reference: once the
   outcome is known, our last move and theirs determine each other, so `Relative`
   with `ref: MY` agrees 100% with `rotation_outcome` (`ref: OPP`). A reply model on
   our moves alone (`response_markov`, an order-2 n-gram of our moves predicting
   theirs) is distinct but weak: -12.4 pts vs `markov2_joint` (note 0070).
1. **Nash is the floor, not a strategy.** _supported._ `nash_v1` wins 50% of its
   matches at +0 rounds: unexploitable, never exploiting.

## Open questions

- Which strategy families are still missing at L1? Kit signals with no species:
  rarest, score state (their nearest species exist: `balancer_hunter`,
  `score_reader`); reactions to us are covered by rotations (claim above); families
  with no signal yet: lag-k copy,
  reactions to our last move given the outcome.
- How much of each learner's strength is its parameters? The atlas used defaults.
- What can no L1 do that L2 must add? Two candidates: knowing which of its
  predictions works against this opponent, and countering the strong set.
