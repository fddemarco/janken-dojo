# Bandits over predictors

**What they are.** Every L2+ bot's core: several arms (a predictor turned by a
rotation) each keep a record of how its move would have scored, counterfactually,
every round, and a selector picks the arm to play. This is a full-information
experts problem (we see what every arm would have scored), not a true bandit.

**In the kit.** `Bandit` (`janken/kit/blueprint/composites.py`) with a scorer
(`Dirichlet`: decayed win/tie/loss counts, a posterior per arm; `DecayedNet`: a
decayed net score; `DropSwitch`: a net score that resets on a loss with probability
`p_reset`) and a selector (`Greedy`, `Thompson` with a sharpening factor,
`SampledVote`, `First`). `random_arm` adds a random arm as a floor.

## Strengths

- **Coverage:** with every rotation of every arm, the bandit holds the counters of
  its own predictors and the counters of those counters (level-k by rotation).
- **Building from the strong set below wins:** `repeat_mirror_v1`, a greedy
  decayed-net bandit over L1's strong set, beats `iocaine_lite_v1` by +7.3 pts
  (note 0064).
- **Thompson sampling** randomises among near-tied arms, which makes the bot harder to
  model than a greedy argmax.
- **Decay** (0.85-0.95) follows an opponent that switches within a few rounds (notes
  0032, 0055).

## Exploits

- **Replay.** A bandit's records are a deterministic function of the public history;
  an opponent that replays it (`anti_smartbot`, `anti_iocaine`, `anti_rps4`) knows
  which arm leads and beats its move: `anti_smartbot_v2` beats most adaptive L2s by
  18-59 rounds per match (L2 atlas). Thompson only blurs this: a replay naming the
  likeliest arm (`estimate NORMAL`) still wins about 45% of rounds vs a Thompson
  metabot (insights of 2026-10-10).
- **Greedy is fully predictable** once replayed; sharpened Thompson nearly so.
- **Record lag.** An undecayed record trails a switch; a fast decay chases noise. An
  opponent alternating two strategies on a period near the decay's memory keeps it
  wrong-footed.
- **Many near-copies make false leads.** The max of many noisy records is inflated:
  32 near-identical arms cost 10 pts (note 0048).

## Cost

Linear in the arms per move; each replayed arm costs a whole bot's step.

## Ideas

- Hedge / EXP3 weights instead of argmax or Thompson: a regret bound vs the best arm,
  and a mixed strategy a replay can't name (`online-learning.md`).
- A change-point reset of the records instead of a fixed decay
  (`statistical-methods.md`).
