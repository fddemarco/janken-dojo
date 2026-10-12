# Parameters and spaces

## Parameters

A bot's parameters are its `defaults`; the engine hands them to the pipeline as the `prm`
vector, in `defaults` order. Each one feeds a `$KNOB` in the blueprint (see
[Writing a bot](writing-bots.md)).

A **variant** is the same bot file with other values: `bots/l1/x.yaml:DECAY=0.8` (several:
`bots/l1/x.yaml:DECAY=0.8,MAX_LEN=6`). It works anywhere a bot spec is accepted
(`evaluate`, `lab experiment`, `lab dataset add`, `lab predict`, …). In results, a variant is labelled
`x@<hash of its overrides>`.

## Space files

What a bot is tuned over is not part of the bot: it lives in a **space file**, one per
bot, in `spaces/<bot>.yaml`. [`janken tune`](tuning.md) and
[`lab predict-tune`](dataset.md#lab-predict-tune) read them.

```yaml
bot: bots/l2/iocaine_lite.yaml
weight: 1.0          # its share of a multi-bot study's objective
params:              # a subset of the defaults; the rest stay fixed
  DECAY: {type: float, low: 0.5, high: 1.0, grid: [0.7, 0.8, 0.9, 0.95]}
  MAX_LEN: {type: int, low: 1, high: 20, grid: [4, 8, 12, 16]}
```

- `bot`: the bot file, relative to the repository root.
- `weight`: how much this bot's score counts when several space files tune together.
  `1` for the bot you're optimising, `0` for a fleet's support (it then counts only
  through what it does for the others).
- `params`: the parameters to search. A param left out stays at its default.
  - `float` / `int`: `low`, `high`, optional `step`, optional `log: true` (search on a log
    scale: for rates, α, anything where 0.01 → 0.1 matters as much as 0.1 → 1).
  - `categorical`: `choices: [...]`.
  - `grid`: the values `--sampler grid` tries.
  - The range must contain the default.

## Scaffolding space files

`janken bot new` and `janken tune` write a missing space file themselves. To write one
directly:

```bash
uv run janken lab space BOT [BOT ...] [--weight W] [--force] [--spaces-dir DIR]
```

| option | default (`janken.toml`) | what it does |
| --- | --- | --- |
| `--weight W` | `space.weight` (1.0) | the `weight` written in each file (`0` for a fleet's supports) |
| `--spaces-dir DIR` | `workspace.spaces_dir` | where to write |
| `--force` | off | overwrite existing files (otherwise they're never overwritten) |

Each range runs from default ÷ `space.spread` to default × `space.spread` (a float
default in (0, 1\] stops at 1), with `space.grid_points` grid points. That's a starting
point, not a design: before tuning, make the bounds sensible, use `log: true` where it
fits, and drop params not worth searching.

```bash
uv run janken lab space bots/inactive/fleets/iliad_v3/agamemnon_v3.yaml                     # weight 1
uv run janken lab space bots/inactive/fleets/iliad_v3/achilles_v3.yaml bots/inactive/fleets/iliad_v3/ajax_v3.yaml --weight 0
```
