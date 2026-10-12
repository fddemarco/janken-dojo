# Research: the bot lab

This folder is the lab notebook. Results live in `experiments/` (gitignored, local); the
**conclusions** live here, so they survive and steer the next experiment.

## The loop

```
ideas.md ──► new bot (bots/l1/x.yaml) ──► evaluate / tune ──► verdict
   ▲                                                          │
   └──── insights.md ◄── experiments/NNNN-*.md (keep / drop / iterate)
```

Each step is one command (docs/cli.md), and each command keeps this notebook's books:

1. **Ask what's next:** `janken status` reads the notebook and the runs, and names the
   next step with its command.
1. **Pick or add an idea:** `janken idea add / start` (`/ideate`). Sources are the
   weakest matchups in recent reports, open items, and follow-ups in `insights.md`.
1. **Write the bot:** `janken bot new` then `janken bot check` (`/build`).
1. **Evaluate it:** `janken evaluate … --hypothesis …` (`/evaluate`). It writes the note
   with its hypothesis **before** the run, plays it, and writes the results in. Tune it
   if it has knobs: `janken tune` (`/tune`).
1. **Decide:** `janken verdict NNNN keep|drop|iterate --summary …`. This closes the note
   and sets its idea's status.
1. **Record insights** that hold up: `janken insight add --note NNNN …` (`/learn`). It
   refuses evidence below the bar.

`/lab-loop` runs this loop on its own, one commit per step.

## Files

| file | what |
|---|---|
| `rps_kaggle.md` | background: the Kaggle RPS competition, techniques, references |
| `sources/<slug>.md` | one card per external resource: summary, claims vs evidence, relevance, ideas spawned |
| `ideas.md` | the backlog: ideas with status, priority, and the evidence that motivated them |
| `insights.md` | findings that held up, each linked to the experiment(s) behind it |
| `experiments/NNNN-<slug>.md` | one note per experiment: hypothesis, command, run id, results, verdict |
| `experiments/TEMPLATE.md` | the note template |

## Bot rules

- **One anatomy.** Every bot is a blueprint of `janken/kit` stages, run by one
  pipeline: guards → valid-only view → track → signals → rotations → scorer + selector →
  overlays (`janken/kit/blueprint/`). The bot file is YAML: a `description`, its
  `defaults` and its `blueprint` (grammar in `janken/kit/declare.py`); `janken bot new`
  starts one from an existing bot.
- **No logic in bots.** A new idea that the catalogue can't express becomes a new stage
  kind in `janken/kit`, with unit tests, so every later bot can combine it.
- **Parameters**: each `defaults` key feeds a `$KNOB` in the blueprint (at most 8; see
  `janken/botfile.py`). A space file `spaces/<name>.yaml` (`janken lab space`, or written by
  `janken bot new` / `janken tune`)
  makes them tunable; it is not part of the bot.
- **Randomness**: only `random.random()`, `random.randrange(n)` and
  `random.gammavariate(a, 1.0)` inside compiled stages. The engine seeds them per match.
- **A stem's logic never changes** under its filename once it has results; a new idea gets
  a new file. The same goes for a stage kind: add a kind or an option, never change one.

### 2026-10-10: structure epoch 2 (the blueprint refactor)

All 33 bots were re-expressed as blueprints of a shared stage library, a one-time,
deliberate exception to the rule above. Their ideas are the same, but their code and
some details changed. Examples: staller's strategies no longer add word2janken's noise;
rps4_lite always uses orders 0–3 (its MAX_ORDER knob is gone); ties are broken by the
stages' shared rules. Runs from before it are **not comparable** with runs after it.
Manifests now record the kit/engine hash (`library`); older runs show as `pre-blueprint`
in `analyze --history`. The insights below still describe the old code until idea #21
re-baselines them.

### 2026-10-11: the field renamed and reorganised

The bots were renamed for clarity (for example `advanced_bot` → `smartbot_sims`,
`anti_advanced_bots` → `anti_smartbot_sims`, `replay_gate` → `gate_edge`), the legacy
bots moved to `bots/inactive/legacy/` and the fleet to `bots/inactive/fleets/`, duplicates were
removed, and the field was split into one folder per level (`bots/l1/` … `bots/oracle/`). The logic of every remaining bot is unchanged. The notes, ideas and insights
keep the names that were current when they were written, and so does the runs database
(`lab history` and `lab leaderboard` list the old and the new names separately). The
map from old names to new: [bots/README.md](../bots/README.md#renames) and
[bots/inactive/legacy/README.md](../bots/inactive/legacy/README.md).

## Experiment protocol

- **Pool:** each round robin draws **20 random bots** from `bots/`, excluding the
  candidates' own files, and plays a full round robin of pool ∪ candidates. Each round
  robin draws a fresh pool.
- **Knobs:** `--rounds` sets rounds per match (`match.rounds`, 200, the tournament
  standard). `--effort` sets how many pools to play: `standard` is 10 round robins, which
  gives each candidate 200 matches vs the pool; `thorough` is 40. `--round-robins`
  overrides it. Every default is in `janken.toml` (`janken config show`).
- **Common random numbers:** a candidate meets a given pool bot with the same match seed
  as every other candidate in that run. Testing several candidates **in one experiment**
  therefore gives a *paired* comparison that is far sharper than comparing two runs.
  Compare a new bot against its predecessor or a baseline inside the same run.
- **Seeds:** `--seed` makes a run fully reproducible. The default, `-1`, draws a fresh
  seed and records it in the run's manifest.
- **Metric:** the **match score** vs the pool, (W + ½D)/N, with a 95% Wilson CI. The
  tournament rates only match results, so the round margin is secondary. Glicko-2
  ratings are reported per round robin (mean ± SD).

### Reading results

- Two candidates differ only when the **paired comparison CI excludes 0**. Overlapping
  score CIs between separate runs mean "no evidence".
- 200 matches give a score CI of about ±6 points; for ±3 points, use 40 round robins.
- The zoo has many trivially exploitable bots, so headline scores saturate near 85–95%. The
  decisive information is in the **weakest matchups** table, against the strong bots
  (metabots, staller family, geometry, iocaine, rps4). Look there first.
- Matchups have only one match per round robin, so a per-opponent score needs many round
  robins before it means anything.

## Tuning

`janken tune bots/l1/x.yaml --hypothesis …` runs **Optuna** over the bot's space file
(`spaces/x.yaml`, scaffolded if missing; edit its ranges first), then validates and records
the best trials in the note. `janken lab study run` does the same without a note:

- **Several bots at once.** `tune spaces/a.yaml spaces/b.yaml ...` tunes the bots
  together: a trial sets every bot's parameters (`<stem>.<NAME>`), they play the pool and
  each other, and the objective is the weighted mean of their scores (`weight` in each
  space file). For a fleet, the champion weighs 1 and its supports 0.
- **TPE** sampler (multivariate). `--sampler grid` walks the `grid` lists of the space
  files (the product across bots), and `--sampler random` is the baseline.
- **Common random numbers.** Every trial plays the same pools with the same seeds, so
  trials differ only by their parameters.
- **Median pruning.** A trial gets cut after each round robin if it falls clearly behind.
- **SQLite storage** in `experiments/tuning/<study>.db`. A study resumes when re-run.
- **Parallel workers.** Start the same command in several terminals; leave
  `--sampler-seed` unset so the workers don't duplicate each other.
- **`--validate-top K`.** Replays the defaults plus the K best configurations as normal
  experiments on fresh pools and seeds (one run per configuration when several bots are
  tuned, all on the same seed). Tuning overfits its fixed pools, so only the
  validation run is evidence. Record that one.

Why Optuna/TPE: the objective is noisy and cheap (about 0.1–1s per trial on numba), and
the spaces mix ints, floats and categoricals with 1–8 dimensions. TPE handles mixed
spaces and noise well, and parallelises through shared storage. Pruning plus common
random numbers cut the noise and the cost. CMA-ES would need the `cmaes` package, which
is not a dependency.
