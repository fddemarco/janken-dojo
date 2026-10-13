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
1. **A Bayesian mixture of context lengths joins the strong tier.** _supported._
   Context-tree weighting (`context_mixture_v1`, a new stage kind) ties
   `pattern_memory` in an L1 pool (-4.7 pts [-10.5, +0.8]) and wins the most rounds
   per match of any L1 (+121 vs +112), with 74% core agreement: a new species (note
   0071). Like the repeat followers it loses to `geometry` and plays a deterministic
   choice, so it should fall to its mirror counter. _Prediction:_ CTW on our moves,
   BEAT_BEAT, wins > 40% of rounds vs it. Forgetting helps it vs the field: KT counts
   decayed by 0.81 beat undecayed ones by +8.2 pts [+4.7, +11.8] (notes 0082, 0083:
   `context_mixture_v2`). A second tuning down to 0.5 found a lead at 0.72 that
   didn't confirm (-1.4 pts, notes 0084, 0085): the optimum is near 0.8.
1. **A pre-trained prior generalises across parameters.** _supported._ A k=3
   joint-context table trained on the move dataset's default-parameter matches and
   refined online (`pretrained_context_v1`, stage `PriorTable`) beats
   `context_mixture_v1` by +9.8 pts [+5.6, +14.4] in L1 pools of parameter variants
   it never saw, confirmed on fresh seeds (notes 0072, 0073). It wins more matches
   but by fewer rounds: the prior names the field's habits from the first rounds.
   It still loses to `pattern_memory` and `geometry`. A lighter prior generalises
   further: worth 1 observation per context instead of 5, it gains +7.3 pts
   [+3.3, +11.4] vs pools of the whole field's variants, whose L3-L5 bots the prior
   never saw (note 0078: `pretrained_context_v2`). Wider training data (L1-L4
   matches) adds nothing at that weight (-0.3 pts, note 0079): the weight was the
   lever, not the data's breadth. Weights 0.25, 0.5 and 1 play identically (lab
   experiment prior-weight-sweep: 56.5% of matches each, weight 2 52.0%): at or
   below 1 a single count outweighs the prior, so **the prior's value is a cold
   start**, the guess for contexts the match hasn't shown yet, and its ties. And a
   longer context is a sharper cold start: k = 1, 2, 3 win 19%, 22.5%, 44.5% of
   matches vs whole-field variants, and k = 4 beats k = 3 by +7.9 pts [+3.4, +12.3]
   on fresh seeds (note 0080: `pretrained_context_v3`).
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
   theirs) is distinct but weak: -12.4 pts vs `markov2_joint` (note 0070). So is a
   model of their own sequence alone, even a deep CTW (-11.0 pts vs joint CTW, note
   0081): **the information is in the joint history**, how they answer us.
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
