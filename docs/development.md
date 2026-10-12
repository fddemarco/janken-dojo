# Development

Coding conventions, bot rules and the definition of done are in `.claude/CLAUDE.md`.

## Tests

```bash
uv run pytest
uv run pre-commit run --all-files   # mdformat, ruff, ty, pyrefly
uv run python -m janken.cli.reference   # after changing a command: regenerate docs/cli-reference.md
```

The suite runs with the JIT off (`tests/conftest.py`, which pytest loads before any test
module), so it takes seconds and compiles nothing. Tests are pytest style: plain `assert`,
fixtures, `pytest.mark.parametrize`.

| test module | covers |
| --- | --- |
| `test_stages`, `test_blueprint`, `test_declare` | the bot anatomy and its YAML grammar |
| `test_engine` | the referee (with tiny fixture bots), schedules, standings, ratings, `tournament` |
| `test_bots` | every bot's contract and every space file |
| `test_lab` | specs, pools, the runs database (batches, resume, import), analysis, tuning and recorded validations, on pools of light bots |
| `test_space` | space files and their scaffolding |
| `test_dataset` | the move dataset (chunked commits included), predictors, the prediction kernel, metrics, predictor tuning and its recorded validations |
| `test_settings` | `janken.toml`: the schema, local overrides, the environment, line-preserving edits |
| `test_notebook` | ideas, notes, insights (round-trips of the real files) and the loop's next step |
| `test_cli` | every command and parameter documented; no hard-coded defaults; the `config` commands; the lifecycle end to end; the docs and skills only name commands that exist; the reference is current |
| `test_progress` | progress bars, Ctrl-C detection, batched play |
| `test_telemetry`, `test_profiling` | timing spans and the code fingerprint; hotspots, buckets, profile records, span statistics and the budget rule |

## Adding a command

1. Put it in the module of its group under `janken/cli/`, decorated with
   `@lab_command("<name>")` so it gets the [common flags](cli.md#the-common-flags).
1. Document every parameter (`help=`). Take every default from `janken.toml`: add the
   setting to `janken/settings.py` (with its help) and to `janken.toml`, and use
   `about("<key>")` as the option's help. `test_cli` fails otherwise.
1. Keep the command thin. The work goes in `janken/lab/` (or `janken/notebook/`), with
   unit tests.
1. Regenerate `docs/cli-reference.md`, and mention the command in [docs/cli.md](cli.md).

## Layout

```
janken.toml        # every default (janken.local.toml: per-machine overrides)
janken/
├── __main__.py    # `python -m janken`: runs the CLI (`janken` is its pyproject.toml script)
├── cli/           # the typer CLI: options.py (common flags, Lab), lifecycle.py,
│                  #   notebook.py (idea, insight), bots.py, config.py, lab.py, reference.py
├── notebook/      # the research notebook as data: ideas, notes, insights, next step
├── settings.py    # janken.toml's schema and loader; the process-wide switches
├── config_file.py # line-preserving edits of janken.toml (config set / unset)
├── progress.py    # progress bars (tqdm) and Ctrl-C detection
├── match.py       # a match's rules and its MatchResult
├── tournament.py  # round-robin / balanced schedules, per-run standings
├── spec.py        # a bot file + parameter overrides + result label
├── report.py      # standings table, match lines, JSON dump
├── botfile.py     # a bot's YAML file: description, defaults, blueprint section
├── library.py     # bots read by stem: the arms an aggregator names, transitive hashes
├── glicko.py      # Glicko-2
├── rating.py      # titles, and rating one run in memory
├── engine/        # compiling bots and refereeing matches (numba)
├── kit/           # the bot anatomy: blueprint stages, YAML grammar, levels, pipeline
└── lab/           # experiments, the runs database (runs_db.py, DuckDB), analysis,
                   # space files, tuning, workflows.py (the lifecycle steps); the move
                   # dataset (DuckDB), predictors, their metrics and tuning
bots/              # the bots, one YAML file each (incl. the baseline zoo; blocks/: arms)
spaces/            # one space file per tunable bot
docs/              # this documentation (cli-reference.md is generated)
research/          # the lab notebook: protocol, ideas, insights, experiment notes
experiments/       # the workspace: runs.duckdb, dataset.duckdb, tuning studies (gitignored)
tests/
```

## Performance

Performance work is done only when something is slow, and only when it pays. The
`/profile` skill drives it; these are its tools.

**Timing spans.** Every lab command logs a `command` span, and its coarse steps their
own (`engine.compile`, `engine.play`, `experiment.round_robin`, `tune.trial`,
`tune.validate`, `predict_tune.trial`, `predict.evaluate`): one JSON line each, with
the command and the code's fingerprint, in the workspace's `logs/spans.jsonl`
(`janken/telemetry.py`, loguru, rotated at `telemetry.max_mb`). Nothing finer than a
batch of matches is timed. `janken lab profile spans` reads them: per operation and
command, runs, total, median, p95 and last seconds, and `slow` when the last run took
`telemetry.slow_factor` times the median. Add a span (`with telemetry.span("op"):`)
around any new step that costs seconds. The test suite turns spans off
(`$JANKEN_SPANS=off`).

**Profiles and benchmarks.** `janken lab profile run -- <command>` runs the command
under pyinstrument in a subprocess (the JIT is chosen at import: `--jit/--no-jit`),
after one unmeasured run that warms numba's disk cache, and stores the session, its
flame graph (`profile.html`) and a summary in the workspace's `profiles/`. Time is
split into buckets (`compile`, `import`, `janken`, `storage`, `optuna`, `other`) and
attributed to the innermost janken function on each stack: a compiled kernel shows as
its caller's time, so `--no-jit` is how to look inside one. `janken lab profile bench`
times a command `profile.repeats` times without the profiler (the fastest run counts);
with `--baseline ID` it says whether to keep a change. Profiled and benchmarked commands
log no spans.

**The budget** (`[profile]` in `janken.toml`):

1. **Share.** The top hotspot must hold `min_share` (10%) of the time: below that, even
   deleting it gains under ~11% (Amdahl).
1. **Payoff.** Removing `expected_cut` (half) of it, on every run of the command
   projected over `horizon_days` (90; its rate is its runs in the last `window_days`,
   30, of spans, or once a day without history) must save at least the session's cost,
   `session_minutes` (60). A 2-minute hotspot in a command run 5 times a week passes; a
   2-second one run twice a month never does.
1. **Spend.** At most `max_attempts` (3) changes and `session_minutes` per session;
   stop after two in a row below `min_gain`.
1. **Keep.** A change stays only if the bench shows at least `min_gain` (5%) less wall
   time, and every seeded output is unchanged.
1. **Don't repeat.** `lab profile run` refuses a command already profiled on the same
   code fingerprint (the code, the bots, `uv.lock`); and a command is profiled again
   only after `cooldown_days` (7), unless its spans flag it slow.
