# Online learning candidates

Algorithms not in the kit that fit its shape (online, per round, stdlib-exportable),
with the arena's first evidence where we have it.

## Hedge (multiplicative weights) and EXP3

**What.** Keep a weight per arm, multiply it by exp(eta x score) each round, play an
arm (or the move) drawn from the normalised weights. Full information (our case):
Hedge, with a regret bound O(sqrt(T log K)) vs the best arm in hindsight.

**Fit.** A selector over a bandit's arms, in place of Greedy / Thompson; a new
`Selector` kind with an `eta` knob.

**Strengths.** A guaranteed mixed strategy: no worse than the best arm minus the
regret, and its draw can't be replayed exactly (only its distribution).

**Exploits.** Its distribution is replayable: an opponent replaying the weights plays
the best response to the mixture, which wins whenever the mixture is concentrated. A
slow eta lags switches; a fast one approaches greedy.

**Cost.** Same as Thompson.

## Context-tree weighting (CTW) and PPM

**What.** A Bayesian mixture over every context length up to D of the joint history,
each node a KT estimator, weighted so the posterior favours the context length that
predicts best (CTW); PPM blends orders by escape counts. The principled form of what
`Backoff` and `LongestMatch` approximate.

**Fit.** A new signal (a block and an L1 species), predicting the opponent's next
move.

**Strengths.** Near-optimal for any variable-order Markov source; it would
subsume `markov2_joint`, `backoff_ngram` and maybe the repeat followers' strength.

**Exploits.** Deterministic given the history: mirror-countered exactly like the
repeat followers (note 0062). Slow on sources that change (needs decay or a reset).

**Cost.** O(D) node updates per move; with D = 6 on a 9-symbol joint alphabet, a few
thousand nodes per 1000-round match: cheap.

**In the kit since 2026-10-13** (`CTW` signal, `bots/blocks/ctw.yaml`, species
`context_mixture_v1`, note 0071): at depth 3 on the joint history it ties
`pattern_memory` in an L1 pool (-4.7 pts [-10.5, +0.8]) and wins the most rounds
per match of any L1.

## Online logistic / cost-sensitive regression (VW-style)

**What.** A linear model per move over hashed features of the history (and the arms'
predictions), updated by SGD every round on what each move would have scored.

**Fit.** Tried in the experimental arena with Vowpal Wabbit (`janken lab arena`,
`--csoaa 3`): with history features alone it wins 36.7% of rounds vs strong L2-L4
variants, with six kit experts as features 37.7%, where `l5_hunter` wins 43.2%. As a
kit stage: a learned combiner of the arms (a calibrated `NaiveBayes`).

**Strengths.** Learns correlations between arms that naive Bayes double-counts, and
interactions (an arm is right only after a loss, say).

**Exploits.** Deterministic weights: replayable if the opponent knows the features;
SGD's lag after a switch; an opponent can feed it a pattern then break it.

**Cost.** Features x 3 multiply-adds per move: cheap in plain Python up to a few
thousand features.

## Ideas

- A CTW signal and block, then a CTW L1 species (diversify at L1).
- A Hedge selector, compared with Thompson in the same bandit.
- An online logistic combiner stage over a bandit's arms, compared with `NaiveBayes`.
