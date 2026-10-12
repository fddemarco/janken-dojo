---
name: profile
description: Find and fix a performance bottleneck that is slowing janken lab iteration - read the timing spans (`janken lab profile spans`), profile one representative command (`janken lab profile run`), check the optimization budget it prints, and keep only changes a benchmark (`janken lab profile bench --baseline`) proves worth it, with seeded outputs unchanged. Use sparingly - when spans flag a command slow, a lab step or the test suite is clearly too slow, or the user asks. Not on every commit, and never again on code that was already profiled.
---

# Profile (/profile)

Performance work is only worth what it buys back. This skill finds where a slow lab
command spends its time, decides with numbers whether fixing it pays, and keeps a
change only if it measurably helps without changing any result. Run every command as
`uv run janken ...`. The budget's knobs are the `[profile]` table of `janken.toml`
(`janken config show profile`); docs/development.md (Performance) explains them.

## 0. Gate: should this run at all?

Stop early, and say which rule stopped you, when any of these holds:

- **No observed bottleneck.** Something must have been slow: `janken lab profile spans`
  flags a command `slow` (its last run took `telemetry.slow_factor` x its median), a lab
  step kept hitting the Bash timeout, `uv run pytest` went over its 60 s, or the user
  asked. "It could be faster" is not a reason.
- **Already profiled on this code.** `janken lab profile list` shows a `current` profile
  of the command (same code fingerprint): read it (`janken lab profile show <id>`)
  rather than profiling again. `lab profile run` refuses it anyway (`--force` exists for
  a profiler setting change, not for a second opinion).
- **Cooldown.** The command was profiled less than `profile.cooldown_days` ago and its
  spans don't flag it slow.

## 1. Pick the target

```bash
uv run janken lab profile spans              # per op and command: n, total, median, p95, last, slow
uv run janken lab profile spans --op command # whole commands only
```

Take the command costing the most **total** time in the window (frequency x duration),
not the slowest single run. Make a representative but small invocation: the same
command and bots, `--effort quick` (or fewer `--round-robins`/`--trials`), a fixed
`--seed`, and a scratch `--workspace <scratch>/ws` (and `--notebook`, copied, for
high-level commands) so nothing real is written. Keep its shape: a smoke run with 2
bots may hide what a 20-bot pool costs.

## 2. Profile

```bash
uv run janken lab profile run -- lab experiment bots/l2/x.yaml --effort quick --seed 1 --workspace <scratch>/ws
```

The flags before `--` belong to the profiler (its `--workspace` stores the profile);
after `--` is the command, verbatim. It warms numba's cache with one unmeasured run
(`profile.warmup`), then profiles a second in a subprocess, and prints the buckets,
the hotspots (janken functions, with the library time they cause) and the budget
verdict. The flame graph is the `profile.html` it names.

Read the buckets before the hotspots:

| bucket | means | look at |
| --- | --- | --- |
| `compile` | numba compiling | is the disk cache hit (`engine.cache_commands`)? fewer distinct signatures, fewer recompiles per process |
| `import` | module imports | heavy imports at module top where a command doesn't need them |
| `janken` | our Python, **and with the JIT on every compiled kernel it calls** | `--no-jit` to see inside the kernels |
| `storage` | duckdb / polars / pyarrow | query shape, round trips, rows fetched one by one, commits per batch |
| `optuna` | the sampler and its storage | sampler cost per trial, storage writes |
| `other` | stdlib, numpy, typer | the hotspot's own code |

A compiled kernel is opaque to the profiler. When a `janken` hotspot is a call into a
kernel (`play_pairs`, `predict_batch`), profile again with `--no-jit` to see which
stage inside it costs most: plain Python exaggerates per-call costs, so treat its
proportions as a hint and confirm every gain with a JIT-on bench.

## 3. Budget

`lab profile run` ends with **worth optimizing** or **not worth optimizing**, and why:

1. the top hotspot holds at least `profile.min_share` of the time (less gains under ~11%
   even if removed whole);
1. removing `profile.expected_cut` of it, on every run of the command projected over
   `profile.horizon_days` (its rate over `profile.window_days` of spans), saves at least
   the session's own cost, `profile.session_minutes`.

Not worth it: stop, and report the finding in one line (command, top hotspot, share,
why not). Don't look for a smaller hotspot to justify the session.

## 4. Baseline

```bash
uv run janken lab profile bench -- <the same command>          # note its id
```

Also save the command's **seeded outputs** to compare later: `--format json` output of
the target, and `janken lab match A B --seed S --rounds 200` transcripts for the bots
involved. An optimization never changes a result.

## 5. Attempts

At most `profile.max_attempts` changes, within `profile.session_minutes`; stop after two
in a row that don't reach `profile.min_gain`. For each:

1. one focused change at the hotspot (small steps; the coding conventions in
   `.claude/CLAUDE.md` hold: numba only through `kernel`/`parallel_kernel`, no new
   dependencies, no magic numbers);
1. `uv run pytest`;
1. the seeded outputs are byte-identical. Bots' behaviour, a stage's logic and the
   order of random draws must not change: a stem's logic never changes once it has
   results;
1. `uv run janken lab profile bench --baseline <id> -- <the same command>`: it prints
   **keep** or **revert**. Revert means `git checkout` the change.

Kept changes stack: the next attempt's baseline is the last kept bench.

## 6. Finish

- `uv run pytest` and `uv run pre-commit run --all-files` pass.
- Under `/lab-loop`: commit the kept changes on their own (`perf: ...`, with the gain
  and the profile ids in the body) on `bot-lab/auto`, then go back to the loop.
- Standalone: leave the changes uncommitted and report: the target, the profile and
  bench ids, the verdict, each attempt and its gain, and what was kept.
