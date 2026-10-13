# The engine

`janken/engine/` compiles the bots and referees every match inside one numba kernel:

- `build.py` reads every bot in the directories involved, compiles each blueprint into
  the arrays the pipeline reads, and generates a dispatcher (`step(code, ...)` /
  `new_state(code)` if-chains, each bot's arrays as globals) into a copy of `kernel.py`,
  named after a hash of the bots' sources. (A `.py` module with its own `@kernel step` is
  also accepted: the referee's test fixtures use that.)
- Every match, each bot gets fresh state arrays, sized for the match's rounds: a
  per-match workspace holds its valid-only history and one incremental match index per
  history stream (`janken/kit/matching.py`), which every history matcher of the bot
  shares, so no round is rescanned and matching costs O(1) per query.
- `kernel.py` plays whole matches, both bots and the referee, and `prange` spreads a
  schedule across cores. Each side of a match draws from its own random stream: before a
  bot moves, the kernel reseeds numba's generator from (match seed, side, round). Results
  don't depend on thread count, and neither bot's draws depend on the other's (a shared
  stream would let a bot replay its opponent's randomness).
- `result.py` turns raw moves into `MatchResult`s; `registry.py` finds bot files and
  builds each bot's `prm` vector.

## Compilation and the cache

Compiling takes about a minute. The commands listed in `engine.cache_commands`
(`janken.toml`) keep the compiled code in
`~/.cache/janken-numba/<hash of janken/kit + engine>`, so their later runs start in about
a second. Other commands compile in memory.

- `--cache on|off` (any lab command), or `$JANKEN_NUMBA_CACHE`, overrides that for one
  command.
- `JANKEN_JIT=off` (or `engine.jit = false`) runs everything as plain Python, which is
  what the tests do.
- Editing a bot recompiles the engine; editing `janken/kit` starts a fresh cache.

Ctrl-C stops any command cleanly (exit status 130): whatever it already committed (round
robins, dataset chunks, trials) stays stored.

Every other setting is in [Configuration](configuration.md).
