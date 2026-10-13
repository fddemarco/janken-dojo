# Statistical methods

Two uses: **judging bots** (the lab's evaluation, which decides what we believe) and
**inside bots** (a bot that tests hypotheses about its opponent while it plays).

## In the lab's evaluation (in use)

- **Paired comparisons with a 95% CI** (`janken/lab/analyze.py`): two candidates on
  the same pools and seeds; a difference counts only when its CI excludes 0.
- **Group-sequential tests** (`janken/lab/sequential.py`, O'Brien-Fleming alpha
  spending): an evaluation stops early once it is clear or futile; the gauntlet stops a
  pairing once its share is clear of the threshold.
- **Bonferroni** over matchups when classifying a version (`janken species classify`).
- **The winner's curse** (insight of 2026-10-13): leads selected at a 10-round-robin
  cap shrink on fresh seeds (+6.0 --> +1.9, +4.0 --> +1.9, +4.5 --> -0.2), so a lead
  that didn't clear its CI gets a confirming run before it counts.

## Candidates for the lab

- **Hard-opponent pools** (idea #60): a stratified design, drawing pools where strong
  bots differ, raises the power for the effects that matter; the gauntlet on
  `research/gauntlet/hard_l4.txt` resolved +5.2 and +8.5 pts that random pools tied.
- **Bootstrap CIs over matches** for statistics with no closed form (share of rounds
  per opponent, rating differences).
- **Hierarchical (empirical Bayes) estimates of per-opponent effects:** shrink each
  matchup's estimate toward the bot's mean, so the weakest-matchup lists stop
  chasing noise.

## Inside bots (candidates)

- **Change-point detection** (CUSUM, Page-Hinkley, Bayesian online change-point):
  test, round by round, whether the opponent's behaviour just changed (an arm's
  record drops, the move distribution shifts) and reset the records then, instead of
  forgetting at a fixed decay. Fits as a scorer option or a gate's handover signal.
  _Exploit:_ an opponent that switches just under the detection threshold, or
  triggers false alarms to make us forget a model that was right.
- **Randomness / predictability tests:** the entropy of the opponent's moves given
  short contexts, a chi-square test of its transition table, a runs test. A bot that
  measures how predictable its opponent is can stop exploiting (and play near-Nash,
  conceding nothing) against an unpredictable one, and commit harder against a
  predictable one (idea #30, complexity-gated experts). _Exploit:_ an opponent that
  looks random on the tested statistics while keeping structure elsewhere.
- **Sequential probability ratio tests** between two hypotheses about the opponent
  ("it is bot X" vs "it isn't"), the cheap cousin of the identification posterior:
  commit to a replay only once the evidence ratio crosses a bound.
- **Model selection** (BIC, Bayesian evidence) between predictors of different
  complexity, the statistical form of choosing a context length (CTW does it
  exactly: `online-learning.md`).
- **Safe exploitation:** mix the exploit with Nash in proportion to the evidence (an
  epsilon that falls as the opponent model's record grows), so a wrong model costs
  at most epsilon per round; the `Noise` guard is the fixed-epsilon version.

## Ideas

- A change-point scorer option (reset an arm's record on a CUSUM alarm), compared
  with a fixed decay in the same bandit, head to head vs level-switching opponents
  and in pools.
- A predictability gate: near-Nash play when the opponent's conditional entropy stays
  near log 3, the exploit otherwise.
