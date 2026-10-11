# Writing a bot

Submit **one `.yaml` file** in `bots/`. Its filename is your bot's name (`ada.yaml` -->
`ada`; files starting with `_` are skipped). Every bot has the same anatomy, run by one
compiled pipeline (`janken/kit/pipeline.py`):

```
guards -> valid-only view -> track -> signals -> rotations -> scorer + selector -> overlays
```

A bot file only declares it, as data: which stages, and which of their knobs read the
bot's parameters.

```yaml
# bots/beat_last.yaml
description: Plays what beats the opponent's last move.
defaults:            # the bot as submitted; at most 8, each feeds a $KNOB
  NOISE: 0.05
blueprint:
  guards:
    - Noise: {p: $NOISE}
    - Opening: {rounds: 1, move: ROCK}
  signals:
    - LastMove: {of: OPP}   # the opponent's last move ...
  rotations: [BEAT]         # ... and play what beats it
```

## The grammar

The grammar lives in `janken/kit/declare.py`.

- A stage is `Name` (no arguments), `{Name: {field: value}}` or `{Name: [values]}`.
  `Name` is a stage class of `janken/kit/blueprint.py` (the table below) or a preset of
  `janken/kit/presets.py` (`metabot`, `iocaine`, `rps4`, `staller`, `smartbot_sims`,
  `metabot_signals`, `sims`). A preset that returns signals is spliced into the list.
- `$NAME` is a knob read from the bot's `defaults`; an UPPER_CASE word is a constant
  (`OPP`, `MY`, `JOINT`, `BEAT`, `ROCK`, `TIES_FIRST`, `RA_SCORED`, `CHAMPION`,
  `ALL_ROTATIONS`, …).
- A bot built around a ready-made core uses `around:`:

```yaml
blueprint:
  around:
    smartbot_sims: {n: 10, arm_decay: $ARM_DECAY, table_decay: 0.9, max_match: 12}
  selector: Thompson
  overlays:
    - Team: {role: CHAMPION}
```

## The stages

| stage | what it does | kinds |
| --- | --- | --- |
| guards | answer the round first, in order | `Opening`, `Noise`, `OnInvalid` |
| view | models see only rounds where both moves are valid | (always) |
| signals | each proposes a symbol, or none | `LastMove`, `Frequency`, `NGram`, `Backoff`, `LongestMatch`, `SecondMatch`, `Relative`, `React`, `Geometry`, `NaiveBayes` (combines the others), `Constant`, `Cycle`, `Biased`, `WinStay`; models of us: `Sim(signal)`, `Replay(ensemble)` |
| rotations | each symbol becomes one arm per rotation | `COPY`, `BEAT`, `BEAT_BEAT` (per signal: `Rotated`) |
| scorer | every arm's record, counterfactually | `Dirichlet`, `DecayedNet`, `DropSwitch` (+ a random arm: `RA_SCORED` / `RA_PINNED`) |
| selector | the arm to play | `First`, `Greedy`, `Thompson`, `SampledVote`, `ChooseSelector` |
| overlays | transform the chosen move | `Stall`, `Team` (`fleet`: `ILIAD` / `ILIAD_V2`; `vigilant`: stop throwing at a teammate's first non-throw), `EmitInvalid` |

## Rules

- **Knobs** are literals or `$NAME`, read from the bot's parameters (`defaults` order, at
  most 8). Every `defaults` key must feed a knob. See
  [Parameters and spaces](parameters-and-spaces.md).
- **Shared cores** live in `janken/kit/presets.py`: smartbot's metabot, the "model of us"
  sims, iocaine, rps4, the staller.
- **New ideas** become new stage kinds in `janken/kit` (a dataclass in `blueprint.py` and
  its compiled half), never logic inside a bot file: a bot file holds no code.
- **Moves** are `0/1/2` = rock/paper/scissors (`janken.kit.moves`). A bot may return
  `INVALID`: that loses the round, and the opponent sees `INVALID` in its history. **Three
  in one match forfeit it.** `CRASH` forfeits at once. `EmitInvalid` spends at most two.
- **Randomness**: only `random.random()`, `random.randrange(n)` and
  `random.gammavariate(a, 1.0)` inside compiled stages. The engine seeds them per match,
  so a seeded match is reproducible.
- **A bot's logic never changes under its filename** once it has results: a new idea gets
  a new file (see `research/README.md`).
- Bots run in-process with no sandbox, so only run bots you trust.

Inside the research loop, the `/new-bot` skill writes a bot for you.
