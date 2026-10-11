---
name: build
description: Turn a janken lab idea into a bot - scaffold bots/<name>.yaml with `janken bot new`, write its blueprint from janken/kit stages (adding a new stage kind with tests when the idea needs one), and verify it with `janken bot check`. Use when the user asks for a new bot or variant, or `janken status` says build.
---

# Build a bot

Goal: a new `bots/<name>.yaml` that follows the bot rules (`.claude/CLAUDE.md`),
compiles, and is ready for `/evaluate`. Run every command as `uv run janken ...`.

## 1. Pick the idea and the starting point

```bash
uv run janken idea show <N>          # the idea and its motivation
uv run janken insight list           # build on what is known
uv run janken bot list               # candidates to start from
uv run janken bot show <bot>         # a starting point's blueprint and space
```

Name the bot after its idea (`bayes_combiner`, `geometry_stall`, …). The stem is its identity
and is never reused with different logic.

## 2. Scaffold and write it

```bash
uv run janken bot new <name> --from <bot> --idea <N> \
  --description "The idea in one line.\nWhat it combines and why; link the idea."
```

This copies the starting bot, sets the description, writes `spaces/<name>.yaml` when the
bot has defaults, and marks the idea in progress. Then edit the blueprint.

- **The catalogue** is `janken/kit/blueprint/` (one module per stage family; the core
  is a predictor tree: signals combined by `Bandit`, `Gate`, `NaiveBayes`), with each
  stage's docstring. The YAML
  grammar is `janken/kit/declare.py`; [docs/writing-bots.md](../../../docs/writing-bots.md)
  has the table.
- **Shared cores** are presets in `janken/kit/presets.py`: `metabot`, `smartbot_sims`,
  `iocaine`, `rps4`, `staller`, `metabot_signals`, `sims`. A new bot is usually a preset
  plus a change, or a new mix of stages.
- **Knobs.** Every `defaults` key feeds a `$KNOB`, at most 8. Anything not worth tuning
  is a literal.
- **A new idea the catalogue can't express** becomes a new **stage kind**, never logic in
  the bot:
  1. a frozen dataclass in its `janken/kit/blueprint/` module and a code in `codes.py`
     (a new way of combining predictors is a composite in `composites.py`, flattened
     by `lowering.py`);
  1. its compiled branch in the stage module (`@kernel` functions, numba's `random`
     only);
  1. unit tests in `tests/test_stages.py`, and a grammar test in `tests/test_declare.py`
     if the YAML form is new;
  1. its export in `bot.py` (and `declare.PRESETS` / `declare.SYMBOLS` for a preset or
     constant).

  Never change an existing stage's behaviour; add a kind or an option.
- **The space file.** Edit `spaces/<name>.yaml` into sensible ranges (`log: true` for
  rates) if you'll tune it.

## 3. Verify

```bash
uv run janken bot check <name>            # contract, compiles, smoke round robin
uv run pytest                             # seconds, JIT off
uv run pre-commit run --all-files
```

`bot check` stores nothing, and its smoke score proves nothing. Next comes `/evaluate`
with the bot it improves on as the baseline. A bot is committed together with its first
verdict, not alone.
