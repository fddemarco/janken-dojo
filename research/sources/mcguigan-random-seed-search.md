# Source card: James McGuigan, "Random Seed Search Nash Equilibrium Opening Book" (Kaggle, 2021)

## Source

- URL: https://www.kaggle.com/code/jamesmcguigan/random-seed-search-nash-equilibrium-opening-book?scriptVersionId=53294911
- Read: 2026-10-10, through the Kaggle kernels API. The API returns the latest notebook
  version (v86), not the linked scriptVersionId, so details may differ slightly.

## Summary

An attempt to beat "random" Kaggle bots by recognising the seeded Python RNG behind them,
used as an opening book. When nothing is recognised, the bot falls back to a fixed
irrational-digit sequence (see [mcguigan-irrational-agent.md](mcguigan-irrational-agent.md)).
It also looks for opponents playing well-known irrational constants.

## Claims vs evidence

- **Against bots that seed with a small, explicit integer:** the approach plausibly works,
  because such a bot's sequence is effectively public.
- **Against unseeded bots** (`random.seed(None)`, which reads `os.urandom`), the author
  reports short partial matches early in a game and calls them "hash collisions". These are
  almost certainly chance. With a huge candidate set, some short sequence always matches,
  and what follows it is uniform. The author never saw a large score against an unseeded
  agent, and the notebook itself says "TODO: verify the statistics".
- The leaderboard gain (~915 vs ~685 for the π bot) most plausibly came from beating seeded
  and fixed-sequence bots, not from true random ones.

## Relevance to janken

**Timing (the user's question):** in our engine, bots playing at almost the same moment
does not shrink any search space, because no seed comes from the clock:

- The kernel (`janken/engine/kernel.py`, `play_batch`) seeds each match with a 32-bit
  seed drawn from a master stream (`janken/tournament.py`, `janken/lab/experiment.py`).
  The master seed comes from `SystemRandom` when none is given.
- Bots may only call numba's `random.random/randrange/gammavariate`, so none can seed
  itself from the time.
- The bots don't run concurrently: in each round, bot a moves, then bot b, in one process.

Clock timing only matters against an opponent that seeds itself from the clock, which our
rules don't allow.

**The real weakness is the shared stream.** Both bots in a match draw from the one RNG
stream the engine seeds. That is the setup the notebook calls the "localhost cheat" (on
Kaggle the agents ran in separate processes). In principle, one bot's draws carry
information about the other's. We treat this as a **harness integrity issue to close**, not
as a strategy. Since the refactor to a numba-only engine, nothing technical stands in the
way (the equivalence tests that used to make it impractical are gone), so it should be
fixed at the engine level: idea #17.

**Lessons for our bots:**

- Fixed or publicly known sequences lose to anyone who knows them. Our bots should only get
  randomness from the engine's stream, as the rules already require.
- Small per-round edges matter more here than on Kaggle, because any margin wins
  (`rps_kaggle.md` §5). Even so, an edge has to be measured with paired runs before we
  believe it. This notebook is a cautionary example of an unverified edge.

## Ideas spawned

- [ideas.md](../ideas.md) #17: engine hardening, one independent RNG stream per bot.
