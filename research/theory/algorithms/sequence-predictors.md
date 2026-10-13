# Sequence predictors (the L1 signals)

**What they are.** Rules that predict the opponent's next move from the history,
each with one inductive bias: what was frequent, what followed this context, what
followed the last repeat of the recent history, what came one period back, how the
opponent rotates relative to our last move, a geometric model of the recent mix.

**In the kit.** The signals of `janken/kit/blueprint/signals.py`, exposed as blocks
(`bots/blocks/`) and as L1 species: `Frequency`, `Rarest`, `NGram` (Markov of order
k on our, their or the joint history), `Backoff`, `LongestMatch`, `SecondMatch`,
`Period`, `Relative` (rotations, optionally given the outcome), `ScoreState`,
`Geometry`, `React`, `Cycle`, `Constant`, `Biased`, `WinStay`.

## Strengths

- **Repeat matching** (`LongestMatch`, `SecondMatch`) is the strongest L1 family: it
  adapts its context length to the opponent, so it beats fixed-order Markov models
  by 31-33 rounds per match (L1 atlas; insight of 2026-10-13).
- **Rotation models** (`Relative` given the outcome: `rotation_outcome`) beat every
  reactive rule of the last round by 220+ rounds per match: one model covers the
  whole reactive family.
- **Counts** beat fixed and biased play, and nothing else.

## Exploits

- **Deterministic given the history, so mirror-countered.** Any of them computed on
  our own moves (`of: MY`) and played BEAT_BEAT names the move it will beat, and
  beats it: about 95% of rounds vs `pattern_memory` and `second_repeat` (note 0062).
  Iocaine-style bots exploit this at L2 by reading every predictor from both seats.
- **Lag.** A count or a long context adapts slowly; an opponent that switches
  strategy every few dozen rounds is ahead of it until the evidence turns. Decayed
  counts trade this against noise.
- **Poisoning.** A bot that plays a pattern long enough for a matcher to lock on, then
  breaks it once, wins the round the matcher bets on (the `Stall` / `EmitInvalid`
  overlays and the dodge of the longest match that `second_repeat` captures).
- **Noise.** Against random or near-random play (`nash_v1`) they gain nothing and lose
  nothing on average: their value is only against structure.

## Cost

Constant to linear in the history per move (repeat matching keeps an index:
`janken/kit/matching.py`); exported as plain Python, well under a millisecond.

## Ideas

- Families with no signal yet: lag-k copy, reactions to our last move given the
  outcome (theory, L1 open questions).
- Context-tree weighting as one principled mixture of all context lengths
  (`online-learning.md`).
