# Janken bot lab

A rock-paper-scissors bot tournament (see `README.md`, an index of `docs/`) plus a
self-improving research loop: ideas --> bots --> evaluation and tuning against random pools -->
verdicts --> insights --> ideas.

## These instructions: progressive disclosure

- Keep this file lean: only what nearly every task needs. A rule that matters for one
  kind of task (writing tests, building a bot, profiling) goes in the skill that owns
  that task, and this file points to it in one line.
- Keep skills lean too. `SKILL.md` holds the workflow and the rules; when a skill grows
  past ~500 lines, move detail out to load on demand: `references/` (long docs,
  catalogues, examples), `scripts/` (code the skill runs), `assets/` (templates, data).
  `SKILL.md` names each file and when to read it.

## Writing style

Everything written for people (docs, notes, descriptions, commit messages, replies) reads
like a person typed it:

- Only characters a standard laptop keyboard types: no emojis, no typographic symbols
  (curly quotes, long dashes, a minus sign other than `-`, unicode arrows, a times
  sign other than `x`, a `>=` drawn as one character).
- Arrows are written `-->`.
- Backticks are for code, commands, paths and bot stems; don't wrap ordinary words or
  numbers in them.

## The CLI and the skills

`uv run janken ...` (typer, `janken/cli/`; docs/cli.md). It has two levels:

- **High level:** one command per lifecycle step, each keeping the notebook's books.
  - `status` (the next step), `idea`, `bot new | check | list | show | export`;
  - `evaluate` (note --> run --> results), `tune` (note --> study --> validation);
  - `verdict`, `species classify | compare | census | list`, `insight`, `tournament`,
    `config`.
- **Low level:** `janken lab ...`, ad hoc and without the notebook.
  - `experiment`, `resume`, `report`, `runs`, `history`, `leaderboard`, `match`;
  - `query` (read-only SQL), `space`, `study run | show | list`;
  - `dataset add | info`, `predict`, `predict-tune`;
  - `profile run | bench | list | show | spans` (hotspots, benchmarks, timing spans);
  - `gauntlet variations | nash | run`, and, research only, `arena` (an experimental
    learner vs a gauntlet's list) and `identify` (telling opponents' parameters
    from their moves).

Every lab command shares the same flags (workspace, evidence, execution, output).

The skills drive the self-improvement loop through the high-level commands:

- `/lab-loop`: the autonomous loop. It asks `janken status` for the next step, carries it
  out with the skill that owns it, and commits (start here).
- `/ideate`: new, well-motivated ideas (`janken idea add`).
- `/build`: an idea becomes a bot, or a new kit stage (`janken bot new | check`).
- `/evaluate`: hypothesis, run, reading, verdict (`janken evaluate`, `janken verdict`).
- `/tune`: a bot's or fleet's study and its validated verdict (`janken tune`).
- `/classify`: a kept bot becomes a new species, the next version of one, or a variant
  (`janken species classify`).
- `/learn`: insights citing the notes behind them (tentative when no CI excludes 0),
  and follow-up ideas (`janken insight add`).
- `/profile`: a bottleneck slowing the loop is profiled, judged against the optimization
  budget, and fixed only if a benchmark proves it (`janken lab profile`). Sparingly: only
  when something is slow, and never twice on unchanged code.
- `/write-tests`: isolated unit tests of the package on synthetic data, never the lab's
  bots, notebook, config or runs.

**The lifecycle skills run experiments and tuning themselves** (into `experiments/`, with
the notebook in `research/`). **Only `/lab-loop` commits**, after every step, on the
`bot-lab/auto` branch.

- Smoke checks go to a throwaway `--workspace <tmp>/ws --notebook <tmp>/research`, with
  the notebook copied there first.
- Read-only commands are always safe to run: `status`, `idea list | show`, `bot list | show | audit`,
  `insight list`, `species compare | census | list`, `config show | get | path | check`, `lab report | runs | history | leaderboard | query | study show | study list | dataset info | predict | profile list | profile show | profile spans`.

## Bot rules (enforced by review, the engine and the tests)

- Every bot has the same anatomy (`janken/kit/blueprint/`): guards --> valid-only view -->
  track --> signals --> move choice (rotations) --> select (scorer + selector) --> overlays.
- A blueprint is `guards`, a `core` and `overlays`. The core is a predictor tree
  (composite pattern, `janken/kit/blueprint/predictor.py`): signals are leaves;
  `Heuristic`, `Sim`, `Rotated`, `Replay` decorate one predictor; the aggregators
  `Bandit`, `Gate`, `NaiveBayes` combine several into a higher-order one. Every way of
  combining predictors is an aggregator. `lowering.py` flattens the tree into the one
  bandit the compiled pipeline plays, and refuses the shapes it can't.
- **Levels** (`janken/kit/levels.py`) are the tree's: **L1** is a heuristic (a
  `Heuristic` core, one signal and one rotation; no Bandit, no Gate); **L2** a Bandit or
  Gate over L1s; **L3** over L2s (and L1s); **L4** over L3s (and L2s, L1s); and so on.
  Every aggregator adds one level above its highest arm.
- An aggregator's arms are **bots, named** (`janken/kit/blueprint/refs.py`):
  `{bot: <stem>, arms: N, space: {PARAM: [one value per arm] | shared}, rotations: [...], side: MY|OPP}`. A bot's `defaults` are its parameter interface: an unknown parameter is
  an error. An L1 arm is its signal; an L2+ arm is a `Replay` of its bandit (from our
  side its move, from theirs their likely move). A blueprint's `core` or a Gate's `main`
  may name a bot too. Bots are read by stem through `janken/library.py`.
- One YAML file per bot, `bots/<level>/<name>.yaml`: a `description`, its `defaults` (at most 8,
  the bot as submitted) and a `blueprint` of kit stages whose knobs are literals or
  `$NAME` (grammar in `janken/kit/declare.py`; copy any bot in `bots/`). Stems are
  unique across all of `bots/` (levels, `blocks/`, `inactive/`). A bot file holds
  no Python.
- The field holds one bot per **species**, its current version `<species>_vN`
  (lineage: `research/species.md`; rules: docs/experiments.md, Species). A new bot gets
  a plain stem; only `janken species classify` gives versions, after a keep. Versions
  never cross levels; retired versions and variants go to `bots/inactive/legacy/`.
- What a bot is tuned over lives outside it, in one space file per bot,
  `spaces/<name>.yaml` (`janken/lab/space.py`): `bot`, `weight` and `params`.
  `janken bot new` and `janken tune` scaffold a missing one (`janken lab space` writes one
  directly); edit it before tuning. `janken tune BOT --support BOT ...` tunes a fleet
  (champion weight 1, supports 0).
- A bot holds no logic of its own. A new idea is a new stage kind in `janken/kit`
  (dataclass in its `janken/kit/blueprint/` module, compiled half in its stage module,
  unit tests in
  `tests/test_stages.py`), and then any bot can use it (`declare.py` finds stage classes
  by their `kind`; a new constant is added to its registry). A new signal usually gets
  a block too (`bots/blocks/`, every field a parameter). What bots share is a bot they
  all name, never copied arms.
- Randomness only via `random.random/randrange/gammavariate` inside compiled stages, in a
  deterministic order.
- A stem's logic never changes under the same filename once it has results; a new idea
  gets a new file. Nothing pins this automatically: it is enforced by review.
- `experimental: true` in a bot file marks it research only: `janken bot export` refuses
  it and every bot that names it, directly or not. Use it for bots that only exist to
  test an idea; a bot meant for production never carries it or names one that does.

## Experiments with other libraries (`janken/experimental/`)

- An idea may be tried first with a third-party library (Vowpal Wabbit so far) in
  `janken/experimental/`, played with `janken lab arena` against a gauntlet list (the
  field's bots and their parameter variants) and compared with a kit bot's
  `janken lab gauntlet run` on the same list.
- Those libraries live in the `experimental` dependency group of `pyproject.toml`, and
  only `janken/experimental/` and the command that runs it (`janken/cli/arena.py`,
  importing it inside the command) may import them or the package;
  `tests/test_experimental.py` enforces it. Adding one to that group is allowed when an
  experiment needs it: say so in the hand-off.
- Nothing from there ships. An idea that wins in the arena is rebuilt from scratch as a
  kit stage (`/build`), then evaluated and exported like any bot.

## Coding conventions (all Python: `janken/`, `tests/`)

- Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html):
  naming, Google-style docstrings, imports of modules rather than names (except `typing`),
  no mutable default arguments, short focused functions.
- Type hints on every function signature, attribute and non-obvious variable, including
  tests. The code must type-check under `ty` and `pyrefly`.
- Avoid `None`: no `Optional` parameters or returns used as a "missing" sentinel. Prefer
  required arguments, defaults from configuration, empty collections, a dedicated value
  object, or raising an exception. Use `None` only where a third-party API forces it, and
  keep it at that boundary.
- The `global` keyword is not allowed. Pass state explicitly or hold it in an object.
- Defaults (paths, rounds, round robins, seeds, tuning budgets...) live in **`janken.toml`**,
  read in one place (`janken/settings.py`: a typed schema whose fields carry their help),
  and are changed with `janken config set` (`--local`: `janken.local.toml`, gitignored).
  No magic numbers in the code. Every CLI option takes its default from the config,
  and its help names the key (`about("<key>")`); `tests/test_cli.py` enforces it. A
  bot's `defaults` is the exception: it's part of the bot's behaviour and stays in the
  bot's YAML file.
- Every CLI command and parameter is documented (`help=`), and `docs/cli-reference.md`
  is regenerated after a CLI change: `uv run python -m janken.cli.reference` (pre-commit
  checks it is current).
- Layout: src layout (`src/<package>/`) is the target. New packages go there; migrate
  existing ones only as a dedicated change, never as a side effect of another task.
- Design: follow Martin Fowler (refactoring, small steps, remove smells), Dave Farley
  (testability, fast feedback, small incremental changes) and Bob Martin (Clean Code,
  SOLID). Keep code DRY, readable and composable: small pure functions, dependencies passed
  in rather than reached for, one responsibility per module/class, reuse `janken/kit` and
  existing helpers before writing new ones.
- Acceleration: use numba for hot paths, always through the `kernel` / `parallel_kernel`
  decorators of `janken/kit/jit.py` (never `numba.njit` directly). No new dependencies of
  any kind (runtime or dev); solve it with the stdlib, `numpy`, `numba` and what
  `pyproject.toml` already lists. (`pyyaml`, for bot and space files, was declared
  explicitly; it was already installed through optuna and pre-commit.) The one
  exception is the `experimental` dependency group, for `janken/experimental/` only
  (above).
- Numba's on-disk cache is opt-in, set by `engine.cache_commands` in `janken.toml`: only
  the compute-intensive commands use it. `--cache on|off` or `$JANKEN_NUMBA_CACHE`
  override it, and `$JANKEN_JIT=off` runs everything as plain Python
  (`janken/settings.py`).

## Tests

`uv run pytest`: seconds (about 12 s), JIT off; `uv run pytest -m heavy` adds the heavy
ones, run only to validate a change they cover. Tests are fast, isolated unit tests of
`janken/` on synthetic data: they never read the lab's bots, spaces, notebook, config
or runs, and never get loosened to pass. Writing them: `/write-tests`.

## Definition of done

Every task that touches code finishes with:

1. the relevant tests passing (full suite if anything under `janken/` changed, plus
   `-m heavy` when the change touches what the heavy tests cover);
1. `uv run pre-commit run --all-files` passing (mdformat, ruff check/format, ty, pyrefly,
   `janken bot audit`, `janken config check`, the CLI reference check).

Fix the code rather than silencing a check. If a rule genuinely can't be met, configure it
in `pyproject.toml` (per-file ignores, tool settings) with a short reason, and only as a
last resort use an inline `# noqa` / `# type: ignore` comment. Say so in the hand-off.

## Where things are

- `janken/cli/` is the typer CLI:
  - `options.py`: the common flags and the `Lab` they resolve into;
  - one module per command group;
  - `reference.py`, which generates `docs/cli-reference.md`.
- `janken/notebook/` is the research notebook as data: ideas, notes, insights, and the
  loop's next step.
- `janken/lab/` holds:
  - the experiment runner;
  - storage: one DuckDB file, `runs.duckdb`, each round robin committed as it's played
    (`runs_db.py`);
  - analysis (duckdb/polars) and the tuner (Optuna);
  - `workflows.py`, the lifecycle steps the high-level commands run;
  - the move dataset (`dataset.py`, DuckDB, append-only; `collect.py` grows it);
  - bots read as predictors (`predictor.py`, `predict_kernel.py`, `predict.py`), their
    metrics (`metrics.py`) and their Optuna/AutoML tuning (`predict_tune.py`).
- `experiments/` (the workspace) holds the runs, the move dataset and the tuning studies.
  It's gitignored, local data.
- `bots/` holds the field (YAML, indexed in `bots/README.md`, with the map of old names),
  one folder per level: `bots/l1/`, `bots/l2/`, ..., `bots/oracle/`. A bot sits in the
  folder of its computed level (`janken bot check`, and `janken bot audit` in pre-commit, enforce it).
  `bots/blocks/` holds L1 heuristics that exist to be named as arms, and
  `bots/inactive/` the bots out of the field: `fleets/` and `legacy/` (discovery reads
  only the level folders, so neither ever enters a pool). `spaces/` holds one space file per tunable
  bot of the field.
- `research/` holds `README.md` (protocol), `ideas.md`, `insights.md`, `theory/` (the model
  the insights add up to, paradigm by paradigm), `species.md`, `sources/` (one card per external resource), `experiments/NNNN-*.md`
  and `rps_kaggle.md`.
- `janken/engine/` compiles bots and referees matches. `janken/kit/` holds the bot
  anatomy: `blueprint/` (the stage catalogue, the predictor tree and its compiler: one
  module per stage family), `declare.py` (the YAML
  grammar), `levels.py`, `pipeline.py` and the compiled stages, and `bot.py` (the whole
  vocabulary in Python, for tests). `janken/library.py` reads bots by stem (references,
  their transitive source hash).
- `janken/experimental/` holds the research-only learners (third-party libraries
  allowed) and the arena that referees them against kit bots, round by round.
- `janken/telemetry.py` logs timing spans (loguru, JSON lines in the workspace's
  `logs/`): every lab command and its coarse steps. `janken/lab/profiling.py` profiles
  (pyinstrument, in a subprocess) and benchmarks commands into the workspace's
  `profiles/`, and holds the optimization budget rule.
- `janken.toml` holds every default; `janken/settings.py` is its schema and loader, and
  `janken/config_file.py` edits it line by line.
- Tests: `tests/`, with their own bots, notebook and config in `tests/data/`.
