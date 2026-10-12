# Janken Bot Championship

A rock-paper-scissors bot tournament. Each bot is one declarative YAML file, compiled
with **numba**; a tournament plays them against each other for N rounds per match, rates
the run with **Glicko-2**, and gives each bot a chess title (**Novice --> Candidate
Master --> Master --> International Master --> Grandmaster**) from its rating.

Around it sits a self-improving research lab. Ideas become bots, bots are evaluated
against random pools and tuned, verdicts and insights are kept in a notebook, and the
lab's skills drive that loop.

## Setup

```bash
uv sync                       # creates .venv and installs the `janken` command
uv run janken --help          # the command line (or `janken --help` in the activated venv:
                              # source .venv/bin/activate)
```

## The lifecycle at a glance

```bash
uv run janken status                         # the research state and the next step
uv run janken idea add "**Idea**: ..." --priority P1 --motivation "..."
uv run janken bot new my_bot --from smartbot_sims_v1 --idea 22 --description "..."
uv run janken bot check my_bot
uv run janken evaluate bots/l2/my_bot.yaml --baseline bots/l3/smartbot_sims_v1.yaml \
  --hypothesis "beats sims3 by >= 2 pts" --idea 22     # note + run + results
uv run janken verdict 0007 keep --summary "..."
uv run janken species classify 0007          # new species, next version, or variant
uv run janken insight add --note 0007 --finding "..." --mechanism "..." --implication "..."
uv run janken tune bots/l2/my_bot.yaml --hypothesis "..."   # study + validation, with a note
uv run janken tournament                     # the whole field: standings, titles
uv run janken lab ...                        # the low level: ad hoc runs, queries
uv run janken config show                    # every default (janken.toml)
```

## Documentation

| page | read it to... |
| --- | --- |
| [The command line](docs/cli.md) | learn the two levels, the lab's language, the common flags, and one iteration end to end |
| [CLI reference](docs/cli-reference.md) | look up any command or parameter (generated) |
| [Configuration](docs/configuration.md) | read and change every default: `janken.toml` and `janken config` |
| [Writing a bot](docs/writing-bots.md) | write `bots/<level>/<name>.yaml`: the anatomy, the YAML grammar, the stages and the rules |
| [Experiments and analysis](docs/experiments.md) | evaluate bots against random pools, read results, and see where runs are stored |
| [Parameters and spaces](docs/parameters-and-spaces.md) | understand `defaults`, variants and space files |
| [Tuning bots](docs/tuning.md) | optimise a bot or a fleet with Optuna, and validate the result |
| [Running a tournament](docs/tournaments.md) | play a field, and read ratings and titles |
| [The move dataset](docs/dataset.md) | store matches, and score and tune bots as predictors |
| [The engine](docs/engine.md) | see how bots are compiled and refereed, and the numba cache |
| [Development](docs/development.md) | run tests and checks, add a command, find your way around the source |

## Repository map

| path | what |
| --- | --- |
| `bots/` | the field: one YAML file per bot, in its level's folder (`l1/` ... `l4/`, `oracle/`; `blocks/`: L1 arms for aggregators), indexed in [bots/README.md](bots/README.md) (levels, what each does, old names) |
| `bots/inactive/` | bots out of the field (never in a pool): |
| `bots/inactive/fleets/` | the fleets (`janken bot fleet`): one champion file each, its `fleet` section naming the supports and the handshake |
| `bots/inactive/legacy/` | retired bots, kept for the research record ([README](bots/inactive/legacy/README.md)) |
| `spaces/` | one tuning space per tunable bot of the field |
| `janken/engine/` | compiles bots (numba) and referees matches |
| `janken/kit/` | the bot anatomy: stage catalogue (`blueprint/`), YAML grammar (`declare.py`), compiled stages, levels |
| `janken/lab/` | experiments, runs database, analysis, Optuna tuning, Oracle calibration, move dataset and predictors |
| `janken/notebook/` | the research notebook as data: ideas, notes, insights, the next step |
| `janken/cli/` | the `janken` command (typer); `reference.py` generates the CLI reference |
| `janken/*.py` | bot files, settings, Glicko-2 rating, tournaments, exports, mocks (Oracles) |
| `tests/` | the unit tests (JIT off, a few seconds) |
| `docs/` | the documentation (table above) |
| `research/` | the notebook: protocol, ideas, insights, experiment notes, source cards |
| `.claude/skills/` | the lab's skills (`/lab-loop` and the lifecycle steps) |
| `janken.toml` | every default (`janken config`) |
| `experiments/`, `exports/` | local data, gitignored: runs, dataset, studies; exported submissions |

`research/README.md` describes the research loop and its protocol. The skills in
`.claude/skills/` (`/lab-loop`, `/ideate`, `/build`, `/evaluate`, `/tune`, `/learn`)
drive it; `/profile` finds and fixes a bottleneck when one slows the loop down.
