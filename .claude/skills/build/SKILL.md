---
name: build
description: Turn a janken lab idea into a bot - scaffold bots/<level>/<name>.yaml with `janken bot new`, write its blueprint from janken/kit stages (adding a new stage kind with tests when the idea needs one), and verify it with `janken bot check`. Use when the user asks for a new bot or variant, or `janken status` says build.
---

# Build a bot

Goal: a new `bots/<level>/<name>.yaml` that follows the bot rules (`.claude/CLAUDE.md`),
compiles, and is ready for `/evaluate`. Run every command as `uv run janken ...`.

## 1. Pick the idea and the starting point

```bash
uv run janken idea show <N>          # the idea and its motivation
uv run janken insight list           # build on what is known
uv run janken bot list               # candidates to start from
uv run janken bot show <bot>         # a starting point's blueprint and space
```

Name the bot after its idea (`bayes_combiner`, `geometry_stall`, …). The stem is its identity
and is never reused with different logic. Never give it a version (`_vN`): field bots are
`<species>_vN`, and versions are given only by `janken species classify` (`/classify`)
after a keep. Start from the current version of a species (`--from smartbot_v1`).

## 2. Scaffold and write it

```bash
uv run janken bot new <name> --from <bot> --idea <N> \
  --description "The idea in one line.\nWhat it combines and why; link the idea."
```

This copies the starting bot, sets the description, writes `spaces/<name>.yaml` when the
bot has defaults, and marks the idea in progress. Then edit the blueprint.

- **The catalogue** is `janken/kit/blueprint/` (one module per stage family; the core
  is a predictor tree: an L1's `Heuristic`, or an aggregator, `Bandit`, `Gate`,
  `NaiveBayes`, over other bots), with each stage's docstring. The YAML grammar is
  `janken/kit/declare.py`; [docs/writing-bots.md](../../../docs/writing-bots.md) has the
  table.
- **Levels decide the shape.** An L1 is a heuristic: `core: {Heuristic: {signal: ...,
  rotation: ...}}`, no Bandit, no Gate. Anything above aggregates bots, **named**: an L2
  is a Bandit or Gate over L1s, an L3 over L2s (and L1s), an L4 over L3s, and so on.
- **Build from bots.** An aggregator's arms are references:
  `{bot: <stem>, arms: N, space: {PARAM: [per arm] | shared}, rotations: [...], side: MY|OPP}`.
  The parameters are the named bot's `defaults` keys (an unknown one is an error). Name
  field versions (`smartbot_v1`, `iocaine_lite_v1`), the blocks of `bots/blocks/`
  (`frequency`, `ngram`, `longest_match`, `relative`, `geometry`, ...: every field a
  parameter), or retired bots. A bot that is another plus an overlay names it as its
  `core`; a gate names its `main`. A new bot is usually a new mix of named bots.
- **Knobs.** Every `defaults` key feeds a `$KNOB`, at most 8. Anything not worth tuning
  is a literal.
- **A new idea the catalogue can't express** becomes a new **stage kind**, never logic in
  the bot:
  1. a frozen dataclass in its `janken/kit/blueprint/` module and a code in `codes.py`
     (a new way of combining predictors is an aggregator in `composites.py`, flattened
     by `lowering.py`);
  1. its compiled branch in the stage module (`@kernel` functions, numba's `random`
     only);
  1. unit tests in `tests/test_stages.py`, and a grammar test in `tests/test_declare.py`
     if the YAML form is new, on hand-made histories, never on the lab's bots
     (`/write-tests`);
  1. its export in `bot.py` (and `declare.SYMBOLS` for a constant);
  1. for a new signal, a block in `bots/blocks/` exposing its fields as parameters, so
     aggregators can name it.

  Never change an existing stage's behaviour; add a kind or an option.
- **The space file.** Edit `spaces/<name>.yaml` into sensible ranges (`log: true` for
  rates) if you'll tune it.

## 3. Verify

```bash
uv run janken bot check <name>            # contract, compiles, smoke round robin
uv run janken bot audit                   # the field, its spaces and species.md agree
uv run pytest                             # seconds, JIT off
uv run pre-commit run --all-files
```

`bot check` stores nothing, and its smoke score proves nothing. Next comes `/evaluate`
with the bot it improves on as the baseline. A bot is committed together with its first
verdict, not alone.
