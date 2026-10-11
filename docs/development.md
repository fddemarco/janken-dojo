# Development

Coding conventions, bot rules and the definition of done are in `.claude/CLAUDE.md`.

## Tests

```bash
uv run python -m unittest discover -s tests -t .
uv run pre-commit run --all-files   # mdformat, ruff, ty, pyrefly
uv run python -m janken.cli.reference   # after changing a command: regenerate docs/cli-reference.md
```

The suite runs with the JIT off (`tests/__init__.py`, which `-t .` makes run first), so
it takes seconds and compiles nothing.

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
├── glicko.py      # Glicko-2
├── rating.py      # titles, and rating one run in memory
├── engine/        # compiling bots and refereeing matches (numba)
├── kit/           # the bot anatomy: blueprint stages, YAML grammar, pipeline, presets
└── lab/           # experiments, the runs database (runs_db.py, DuckDB), analysis,
                   # space files, tuning, workflows.py (the lifecycle steps); the move
                   # dataset (DuckDB), predictors, their metrics and tuning
bots/              # the bots, one YAML file each (incl. the baseline zoo)
spaces/            # one space file per tunable bot
docs/              # this documentation (cli-reference.md is generated)
research/          # the lab notebook: protocol, ideas, insights, experiment notes
experiments/       # the workspace: runs.duckdb, dataset.duckdb, tuning studies (gitignored)
tests/
```
