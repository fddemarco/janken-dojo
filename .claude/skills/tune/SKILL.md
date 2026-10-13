---
name: tune
description: Tune a janken bot (or a fleet - a champion with weight-0 supports) with `janken tune`, which runs an Optuna study over its space file, validates the best trials on fresh pools and records them in a note; then judge the validation and close the note with `janken verdict`. Use when a kept bot has tunable defaults, or the user asks to tune or optimize bots.
---

# Tune

Tuning overfits the pools it trains on, so only the **validation** counts. `janken tune`
runs both, and records every validated configuration with its paired difference from
the defaults. Run every command as `uv run janken ...`.

## 1. Check the space

```bash
uv run janken bot show <bot>     # its defaults and spaces/<bot>.yaml
```

`janken tune` scaffolds a missing space file (each default /2 ... x2). Before a real
study, edit the space into sensible bounds:

- `log: true` for rates;
- int ranges that matter;
- drop params not worth tuning.

The bot's file is never edited.

## 2. Run it

```bash
uv run janken tune bots/<level>/<bot>.yaml --hypothesis "..." --idea <N> --effort standard
uv run janken tune bots/l4/champion.yaml --support bots/l2/helper_a.yaml \
  --support bots/l2/helper_b.yaml --hypothesis "..."          # a fleet: supports at weight 0
```

- **Budget:**
  - `--effort` sets the trials, the pools per trial, and the validation's top K and
    pools;
  - `--trials`, `--round-robins`, `--validate-top` and `--validate-round-robins`
    override them;
  - aim for about 30 trials per param, and `--effort thorough` for small effects.
- **Other searches:** `--sampler grid` walks each param's grid; `random` is a baseline.
- **Resume:** `janken tune --note NNNN` resumes the study and revalidates.

## 3. Judge the validation, then decide

```bash
uv run janken lab study show <NNNN-slug>    # every recorded validation
```

- A tuned configuration is better only if its **vs defaults** CI excludes 0.
- A trial that won training but not validation is overfitting: don't adopt it.

```bash
uv run janken verdict NNNN keep|drop|iterate --summary "..." --analysis "..."
```

Keeping a tuned configuration means a **new bot** with those defaults, never an edit of
the tuned bot's defaults:

```bash
uv run janken bot new <bot>_tuned --from <bot> --description "..."
```

Then set the new bot's defaults, and `/evaluate` it against the original. A kept result
goes to `/learn` (its insight is tentative when no validated CI excludes 0).
