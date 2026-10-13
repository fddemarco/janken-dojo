# Bayesian combiners (naive Bayes, TPI-lite)

**What it is.** Instead of picking one arm, combine every arm's prediction into one
posterior over the opponent's next move: per arm, decayed counts of its predicted
symbol against the move that followed (a likelihood table), multiplied under a naive
independence assumption, times a decayed prior; play the move with the best expected
score.

**In the kit.** `NaiveBayes` (`janken/kit/blueprint/composites.py`), an arm of a
bandit over its sibling predictors (rps_kaggle section 6, "TPI").

## Strengths

- Uses every arm's information every round, including arms that are informative but
  never the single best (a predictor that is wrong in a consistent way).
- The expected-score move hedges between likely opponent moves instead of betting
  on one.

## Exploits

- **Correlated arms are double-counted.** Many arms built on the same signal (one
  predictor at three rotations) are far from independent; the posterior grows
  overconfident and swings with them.
- **Deterministic, so replayable** like any bandit (`bandits.md`).
- **Slow likelihoods:** decayed counts per (arm, symbol, move) need many rounds; an
  opponent switching often leaves the tables stale.

## Cost

Per arm a 4 x 3 table and a multiply per move: cheap.

## Ideas

- Online logistic regression over the same features as a calibrated replacement
  that learns the correlations (`online-learning.md`).
