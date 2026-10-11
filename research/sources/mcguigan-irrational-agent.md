# Source card: James McGuigan, "Rock Paper Scissors - Irrational Agent" (Kaggle, 2021)

## Source

- URL: https://www.kaggle.com/code/jamesmcguigan/rock-paper-scissors-irrational-agent
- Read: 2026-10-10, through the Kaggle kernels API (latest version, v3).

## Summary

A "truly random" bot that plays a fixed sequence derived from the digits of an irrational
number instead of a PRNG. It takes the decimal digits, drops the 0s, and plays `digit % 3`.
The digits 1–9 give exactly three per class, so the encoding is unbiased. Named constants
(π, φ, e, √2, √5, γ, Catalan, Apéry) are built in. A "secure" mode builds a fresh number
each game from the system clock.

## Key ideas

- **No in-game pattern:** the digits of an irrational look statistically random, so
  history matchers, n-grams and frequency counters find nothing to exploit.
- **The "password attack":** the whole sequence is fixed in advance, so anyone who guesses
  the constant beats it in every round. They just play the sequence shifted by +1. That bot
  is in turn beaten by a +2 shift (the "Anti-Anti-π" bot). The author notes that forks
  clustered on π, so a popular constant is a weak password.
- **The "secure" mode is seeded from the clock** (`time.monotonic_ns()`). That swaps a
  guessable name for a guessable time. It's the one place in these sources where the timing
  between bots could matter.

## Claims vs evidence

- "The true Nash equilibrium solution": only for an opponent who doesn't know the sequence.
  Against one who does, it is the most exploitable bot possible.
- Stats: irrational vs irrational, 100 games of 1000 rounds, gave about +4.5 extra wins per
  game. Against a per-game SD of about 25, that is noise, as the theory says it should be.

## Relevance to janken

- **True randomness is out of bounds here.** The rules require all randomness to go through
  the engine's seeded numba `random` calls, so that matches are reproducible and
  fingerprints hold. `os.urandom`, `secrets` and the clock are not allowed.
- **`nash.py` is already our Nash baseline**, and it draws from the engine's stream.
- **A fixed-digit bot is deterministic.** It would be a useful sanity baseline: our
  predictors should do no better than chance against it (≈ the same as against `nash`). A
  much better score would mean a predictor leaks information or has a bug. Nothing in our
  pool should know its sequence, so it should also score ≈50% against everything.

## Ideas spawned

- [ideas.md](../ideas.md) #18: a π-digit sanity baseline bot.
