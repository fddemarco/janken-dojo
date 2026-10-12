# Janken bot lab

A rock-paper-scissors bot tournament (see `README.md`, an index of `docs/`) plus a
self-improving research loop: ideas → bots → evaluation and tuning against random pools →
verdicts → insights → ideas.

## The CLI and the skills

`uv run janken ...` (typer, `janken/cli/`; docs/cli.md). It has two levels:

- **High level:** one command per lifecycle step, each keeping the notebook's books.
  - `status` (the next step), `idea`, `bot new | check | list | show | export`;
  - `evaluate` (note → run → results), `tune` (note → study → validation);
  - `verdict`, `insight`, `tournament`, `config`.
- **Low level:** `janken lab ...`, ad hoc and without the notebook.
  - `experiment`, `resume`, `report`, `runs`, `history`, `leaderboard`, `match`;
  - `query` (read-only SQL), `space`, `study run | show | list`;
  - `dataset add | info`, `predict`, `predict-tune`.

Every lab command shares the same flags (workspace, evidence, execution, output).

The skills drive the self-improvement loop through the high-level commands:

- `/lab-loop`: the autonomous loop. It asks `janken status` for the next step, carries it
  out with the skill that owns it, and commits (start here).
- `/ideate`: new, well-motivated ideas (`janken idea add`).
- `/build`: an idea becomes a bot, or a new kit stage (`janken bot new | check`).
- `/evaluate`: hypothesis, run, reading, verdict (`janken evaluate`, `janken verdict`).
- `/tune`: a bot's or fleet's study and its validated verdict (`janken tune`).
- `/learn`: insights that meet the bar, and follow-up ideas (`janken insight add`).

**The lifecycle skills run experiments and tuning themselves** (into `experiments/`, with
the notebook in `research/`). **Only `/lab-loop` commits**, after every step, on the
`bot-lab/auto` branch.

- Smoke checks go to a throwaway `--workspace <tmp>/ws --notebook <tmp>/research`, with
  the notebook copied there first.
- Read-only commands are always safe to run: `status`, `idea list | show`, `bot list | show`,
  `insight list`, `config show | get | path | check`, `lab report | runs | history | leaderboard | query | study show | study list | dataset info | predict`.

## Bot rules (enforced by review, the engine and the tests)

- Every bot has the same anatomy (`janken/kit/blueprint/`): guards → valid-only view →
  track → signals → move choice (rotations) → select (scorer + selector) → overlays.
- A blueprint is `guards`, a `core` and `overlays`. The core is a predictor tree
  (composite pattern, `janken/kit/blueprint/predictor.py`): signals are leaves; `Sim`,
  `Rotated`, `Replay` decorate one predictor; `Bandit`, `Gate`, `NaiveBayes` combine
  several into a higher-order one. Every way of combining predictors is a composite,
  and a bot's level is the tree's. `lowering.py` flattens the tree into the one bandit
  the compiled pipeline plays, and refuses the shapes it can't.
- One YAML file per bot, `bots/<level>/<name>.yaml`: a `description`, its `defaults` (at most 8,
  the bot as submitted) and a `blueprint` of kit stages whose knobs are literals or
  `$NAME` (grammar in `janken/kit/declare.py`; copy any bot in `bots/`). Stems are
  unique across levels. A bot file holds
  no Python.
- What a bot is tuned over lives outside it, in one space file per bot,
  `spaces/<name>.yaml` (`janken/lab/space.py`): `bot`, `weight` and `params`.
  `janken bot new` and `janken tune` scaffold a missing one (`janken lab space` writes one
  directly); edit it before tuning. `janken tune BOT --support BOT ...` tunes a fleet
  (champion weight 1, supports 0).
- A bot holds no logic of its own. A new idea is a new stage kind in `janken/kit`
  (dataclass in its `janken/kit/blueprint/` module, compiled half in its stage module,
  unit tests in
  `tests/test_stages.py`), and then any bot can use it (`declare.py` finds stage classes
  by their `kind`; a new preset or constant is added to its registries). Shared cores go
  in `presets.py`.
- Randomness only via `random.random/randrange/gammavariate` inside compiled stages, in a
  deterministic order.
- A stem's logic never changes under the same filename once it has results; a new idea
  gets a new file. Nothing pins this automatically: it is enforced by review.

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
- Defaults (paths, rounds, round robins, seeds, tuning budgets…) live in **`janken.toml`**,
  read in one place (`janken/settings.py`: a typed schema whose fields carry their help),
  and are changed with `janken config set` (`--local`: `janken.local.toml`, gitignored).
  No magic numbers in the code. Every CLI option takes its default from the config,
  and its help names the key (`about("<key>")`); `tests/test_cli.py` enforces it. A
  bot's `defaults` is the exception: it's part of the bot's behaviour and stays in the
  bot's YAML file.
- Every CLI command and parameter is documented (`help=`), and `docs/cli-reference.md`
  is regenerated after a CLI change: `uv run python -m janken.cli.reference`.
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
  explicitly; it was already installed through optuna and pre-commit.)
- Numba's on-disk cache is opt-in, set by `engine.cache_commands` in `janken.toml`: only
  the compute-intensive commands use it. `--cache on|off` or `$JANKEN_NUMBA_CACHE`
  override it, and `$JANKEN_JIT=off` runs everything as plain Python
  (`janken/settings.py`).

## Tests

- Unit tests for the logic only: no stress, load, benchmark, or other compute-intensive
  tests. Nothing in the suite compiles: `tests/conftest.py` switches the JIT off, so bots,
  stages and the referee run as plain Python.
- pytest style: plain `assert`, `pytest.raises`, fixtures (`tmp_path`, `monkeypatch`)
  for setup, `pytest.mark.parametrize` for cases that are data (the `subtests` fixture
  where they aren't). No `unittest.TestCase`.
- Run it as `uv run pytest`. It must stay under 60 s; it takes about 20 s. Use small
  inputs (a few rounds, pools of light bots) and fixed seeds.
- Never loosen a test to make it pass.

## Definition of done

Every task that touches code finishes with:

1. the relevant tests passing (full suite if anything under `janken/` changed);
1. `uv run pre-commit run --all-files` passing (mdformat, ruff check/format, ty, pyrefly).

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
  one folder per level: `bots/l1/`, `bots/l2/`, …, `bots/oracle/`. A bot sits in the
  folder of its computed level (`janken bot check` and `tests/test_bots.py` enforce it).
  `bots/inactive/` holds the bots out of the field: `fleets/` and `legacy/` (discovery
  reads only the level folders, so they never enter a pool). `spaces/` holds one space file per tunable
  bot of the field.
- `research/` holds `README.md` (protocol), `ideas.md`, `insights.md`, `sources/` (one card per external resource), `experiments/NNNN-*.md`
  and `rps_kaggle.md`.
- `janken/engine/` compiles bots and referees matches. `janken/kit/` holds the bot
  anatomy: `blueprint/` (the stage catalogue, the predictor tree and its compiler: one
  module per stage family), `declare.py` (the YAML
  grammar), `pipeline.py` and the compiled stages, `presets.py` (shared cores), and
  `bot.py` (the whole vocabulary in Python, for tests).
- `janken.toml` holds every default; `janken/settings.py` is its schema and loader, and
  `janken/config_file.py` edits it line by line.
- Tests: `uv run pytest` (about 20 s, JIT off).
