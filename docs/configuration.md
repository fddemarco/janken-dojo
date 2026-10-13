# Configuration

Every default lives in **`janken.toml`** at the project root, one table per domain
concept. Nothing in the code carries a default of its own: each command-line option
takes its default from this file, and its `--help` names the setting (for example
`(config: match.rounds)`). The loader (`janken/settings.py`) requires every key, and
checks its type, its allowed values and its minimum.

| table | what it sets |
| --- | --- |
| `engine` | `jit`, and which commands keep numba's compiled code on disk (`cache_commands`) |
| `output` | `progress` bars, `format` (text or json), `quiet` |
| `workspace` | where the workspace (`dir`), the notebook, the bots and the spaces live |
| `execution` | `workers`; `flush_s`, how often the matches finished so far are logged and stored while a batch plays |
| `match` | `rounds` per match |
| `pool` | pool `size`, `allow_small`, `mocks`, `lists` (list files to draw pools from instead of the bots dir: hard opponents, say), and `variants` (the share of members played at a parameter variant drawn from their space file, so a bot tuned to the exact defaults shows it) |
| `effort` | the `default` effort, and the budgets `effort.quick` / `.standard` / `.thorough`: round robins, tuning round robins, trials, validation top K and round robins, predictor trials |
| `evaluation` | `mode` (full or candidates), `seed` (-1: fresh); sequential stopping: `sequential`, `looks`, `alpha`, `futility` |
| `tuning` | `sampler`, `prune`, `seed`, `sampler_seed`, `export_every`, `timeout_s` |
| `space` | how a space file is scaffolded: `spread`, `grid_points`, `weight` |
| `tournament` | `matches`, `games`, `league`, `batch_matches`, `seed` |
| `dataset` | the move dataset: `file`, `holdout`, `metric`, `chunks`, `batch_matches`, `matches`, `seed`, `split`, `tune_split` |
| `runs` | the runs database: `file`, `lock_timeout_s`, and `match_cache` (read back a match already played instead of replaying it) |
| `query` | `lab query`: `db`, `limit` |
| `status` | how much `status` lists |
| `export` | `bot export`: `dir`, `max_rounds`, and the screening rules `allowed_modules`, `banned_names` |
| `telemetry` | timing spans: `spans` on or off, their `file` and rotation size `max_mb`, and `slow_factor` |
| `profile` | `lab profile`: where profiles go, the profiler's `interval_s`, `top`, `jit`, `warmup`, and the optimization budget (`min_share`, `expected_cut`, `window_days`, `horizon_days`, `session_minutes`, `max_attempts`, `min_gain`, `repeats`, `cooldown_days`) |
| `gauntlet` | `lab gauntlet`: where logs go, `seeds` and `threshold` per opponent, `batch`, and sequential stopping (`sequential`, `min_seeds`, `stop_alpha`); the variants (`per_bot`, `draws`, `seed`, `probe_rounds`, `variation_probes`, `levels`, `exclude`); the Nash check (`nash_probes`, `nash_seeds`, `nash_skew`, `nash_decisive`); the fingerprint (`fingerprint_probes`, `fingerprint_aliases`, `fingerprint_nearest`) |
| `arena` | `lab arena` (research only): where logs go, `seeds` per opponent, and the experimental learner: `vw_args` (Vowpal Wabbit), `history`, `explore` and the kit `experts` whose moves are its features |
| `identify` | `lab identify` (research only): where logs go, `seeds` per opponent, the `hypotheses` and their `particles`, `eps` (the posterior's sharpness), `commit_round`, `checkpoint_every`, `prune_ratio`, `near`, the `probe` we play until the commit, `leave_one_out` and the particles' `seed`; `forget` (how much of the evidence so far the posterior keeps each round), `switch_decay` (the switch branch's records) and `components` (blocks read from both seats at every rotation) |

## The `config` commands

```bash
uv run janken config show              # every setting, its value and meaning
uv run janken config show effort.thorough
uv run janken config get match.rounds
uv run janken config set effort.standard.round_robins 20     # janken.toml
uv run janken config set --local execution.workers 4         # this machine
uv run janken config unset execution.workers                 # drop the override
uv run janken config path                                     # where the files are
uv run janken config check                                    # validate them
```

- **`set`** changes one line and keeps the file's comments and layout. It refuses a value
  that makes the configuration invalid, and then changes nothing.
  - Lists are comma-separated: `config set engine.cache_commands "evaluate, tune"`.
  - Switches take `on` / `off`.
- **`--local`** writes `janken.local.toml` (gitignored), whose keys override
  `janken.toml` on this machine only. `unset` removes a local override.
- **Committed changes:** changing `janken.toml` changes the defaults for everyone, so
  commit it with a reason. Experiments record their actual settings in their manifests,
  so stored runs stay interpretable either way.

## Precedence

1. `janken.toml`;
1. `janken.local.toml`;
1. the `--effort` budget, for round robins, trials and validation sizes;
1. an explicit command-line flag.

A few environment variables still exist, for process-wide switches read before any
command runs:

| variable | overrides |
| --- | --- |
| `JANKEN_JIT=on\|off` | `engine.jit` (the test suite runs with it off) |
| `JANKEN_NUMBA_CACHE=1\|0` | caching, which the CLI sets per command from `engine.cache_commands` and `--cache` |
| `JANKEN_PROGRESS=auto\|on\|off` | `output.progress` (the CLI sets it from `--progress`) |
| `JANKEN_CONFIG=PATH` | the configuration file, `janken.toml` (the test suite uses `tests/data/janken.toml`) |
| `JANKEN_LOCAL_CONFIG=PATH` | the local overrides, `janken.local.toml`; empty: none (the test suite's) |
