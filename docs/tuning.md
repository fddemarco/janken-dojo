# Tuning bots

Tuning searches a bot's parameters with [Optuna](https://optuna.org) over its
[space file](parameters-and-spaces.md). Each **trial** (one choice of parameters) plays
random pools of bots. The best trials are then **validated** on fresh pools, and only
that validation is evidence.

## With a note: `janken tune`

```bash
uv run janken tune bots/smartbot_sims.yaml --hypothesis "decays tuned at 200 rounds gain >= 1 pt"
uv run janken tune bots/fleets/iliad_v3/agamemnon_v3.yaml --support bots/fleets/iliad_v3/achilles_v3.yaml \
  --support bots/fleets/iliad_v3/ajax_v3.yaml --hypothesis "..."          # a fleet: supports at weight 0
uv run janken tune --note 0009              # resume the note's study, revalidate
uv run janken verdict 0009 drop --summary "best +0.4 pts [-1.2, +2.0] vs defaults"
```

`tune` does four things:

1. writes the note;
1. scaffolds any missing space file (the champion at `space.weight`, supports at 0);
1. runs the study, named after the note (`NNNN-<name>`);
1. validates the top K, and writes the recorded validations into the note.

## Without a note: `janken lab study …`

```bash
uv run janken lab space bots/x.yaml                 # scaffold spaces/x.yaml, then edit it
uv run janken lab study run spaces/x.yaml --study x-v1 --effort thorough
uv run janken lab study run spaces/a.yaml spaces/b.yaml --study fleet-v1
uv run janken lab study show x-v1                   # its recorded validations
uv run janken lab study list
```

## How a trial is scored

1. Before the first trial, the tuner draws the pools: `--round-robins` pools (per trial)
   of `--pool-size` bots, leaving out the tuned bots. `tuning.seed` (or `--seed`) fixes
   the pools and every match seed.
1. Each trial picks a value for every param in every space file.
1. The tuned bots play every pool bot and each other for `--rounds` rounds. Pool bots
   don't play each other, since those matches can't move the tuned bots' score.
1. A bot's score is `(wins + ½ draws) / matches`. The objective is the weighted mean over
   the tuned bots (their space files' `weight`s).

Every trial plays the **same pools with the same seeds** (common random numbers), so
trials differ only by their parameters.

The **median pruner** (`tuning.prune`) stops a trial clearly below the median at the
same step. It starts after 8 trials and is off below 3 round robins per trial.

The first trial of a new study is the bot's defaults (except with the grid sampler).

## The budget

| flag | default |
| --- | --- |
| `--trials` | the `--effort` budget (`quick` 10, `standard` 100, `thorough` 300) |
| `--round-robins` | pools per trial: `effort.<e>.tune_round_robins` (2 / 5 / 10) |
| `--validate-top` | best trials replayed on fresh pools (1 / 5 / 5) |
| `--validate-round-robins` | pools of each validation (2 / 10 / 40) |
| `--sampler` | `tuning.sampler`: `tpe` (default), `grid` (each param's grid list; trials default to the whole grid), `random` (a baseline) |
| `--timeout` | `tuning.timeout_s` (0: none) |

- **Trials:** aim for about 30 × the number of params (summed over the space files).
- **Overfitting:** too few round robins per trial and TPE overfits those pools, which is
  what validation catches.
- **Fixed setup:** a study keeps its setup (rounds, round robins, pool size, seed, the
  space files). Resuming it under a different setup is refused, so use a new name.

## Validation

Validation replays the defaults and the K best trials as ordinary runs, on **fresh**
pools and a fresh seed:

- **one tuned bot:** one run with every configuration as a candidate (paired);
- **a fleet:** one run per configuration, all on the same seed, so one trial's fleet
  never meets another's.

Every validated configuration is **recorded** in the runs database's `tune_validations`
table. Each row holds:

- the study and the run;
- the trial it came from (−1 for the defaults) and its training score;
- the champion's score vs the pool, with its 95% CI;
- its **paired difference from the defaults' champion**, with a bootstrap CI (paired
  across a fleet's runs too, since they share pools and seeds).

The study also lists its validation runs (an Optuna user attribute, `validations`).
`janken lab study show NAME` prints them.

A tuned configuration is a real improvement only if its difference from the defaults has
a CI that excludes 0.

## Progress and output

A bar counts the session's trials and shows the best value and the pruned count. Ctrl-C
stops cleanly, since every finished trial is already stored. The files:

- `experiments/tuning/<study>.db`: the Optuna study (SQLite). It stores every trial as it
  finishes, resumes, and takes parallel workers. For parallel workers, start the same
  `lab study run` in several terminals, with `--validate-top 0` and the sampler unseeded,
  then validate once with `--trials 0`.
- `experiments/tuning/<study>/trials.parquet`: the trials, re-exported every
  `tuning.export_every` trials.

## Keeping a winner

A bot's logic never changes under its filename, and its `defaults` are part of that
logic. So:

- keep a tuned configuration as a **variant** (`bots/x.yaml:NAME=value,...`), which works
  anywhere a bot spec does; or
- make it a **new bot**: `janken bot new x_tuned --from x`, then set its defaults, then
  `janken evaluate` it against `x`.
