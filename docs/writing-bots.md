# Writing a bot

Submit **one `.yaml` file** in `bots/`. Its filename is your bot's name (`ada.yaml` -->
`ada`; files starting with `_` are skipped). Every bot has the same anatomy, run by one
compiled pipeline (`janken/kit/pipeline.py`):

```
guards -> valid-only view -> track -> signals -> rotations -> scorer + selector -> overlays
```

A bot file only declares it, as data: which stages, and which of their knobs read the
bot's parameters.

## Levels

A bot's level is how many layers of aggregation it stacks (`janken/kit/levels.py`). It is
computed from the blueprint, never written down, and the bot lives in its level's folder
(`bots/l1/`, `bots/l2/`, ...):

| level | what it is | may hold |
| --- | --- | --- |
| **L1** | a **heuristic**: one signal played with one rotation | no Bandit, no Gate |
| **L2** | a **meta-heuristic**: a Bandit or a Gate over L1s | L1s |
| **L3** | a meta-meta-heuristic: a Bandit or a Gate over L2s | L2s, and L1s |
| **L4** | a Bandit or a Gate over L3s | L3s, and L2s and L1s |
| L*n* | ... one level above the highest bot it aggregates | any lower level |

Every aggregator (`Bandit`, `Gate`, `NaiveBayes`) adds one level above its highest arm,
whatever its scorer or its number of arms. A bot that plays another bot straight, with no
aggregator of its own (a `Heuristic` over a replay), is at that bot's level.

## An L1: a heuristic

```yaml
# bots/l1/beat_last.yaml
description: Plays what beats the opponent's last move.
defaults:            # the bot as submitted, and its parameter interface (at most 8)
  NOISE: 0.05
blueprint:
  guards:
    - Noise: {p: $NOISE}
    - Opening: {rounds: 1, move: ROCK}
  core:
    Heuristic:
      signal: {LastMove: {of: OPP}}   # the opponent's last move ...
      rotation: BEAT                  # ... and play what beats it
```

A `Heuristic` is one signal and one rotation (`COPY` it, `BEAT` it, `BEAT_BEAT` it). With
no signal (`blueprint: {}`) the bot plays at random (nash).

## An L2 and above: aggregators over named bots

An aggregator's arms are **bots, named**. Each reference names a bot by stem and gives
the parameters of every arm it makes of it:

```yaml
# bots/l2/smartbot_v1.yaml (abridged)
defaults: {ARM_DECAY: 0.95, TABLE_DECAY: 0.9, MAX_MATCH: 12}
blueprint:
  core:
    Bandit:
      predictors:
        - {bot: frequency, arms: 2, space: {DECAY: [1.0, 0.9]}, rotations: [COPY, BEAT, BEAT_BEAT]}
        - bot: ngram
          arms: 10
          space:
            ORDER: [1, 2, 3, 4, 1, 2, 3, 1, 2, 3]
            CTX: [OPP, OPP, OPP, OPP, JOINT, JOINT, JOINT, MY, MY, MY]
            DECAY: $TABLE_DECAY          # one value for every arm: here, our own knob
          rotations: [COPY, BEAT, BEAT_BEAT]
        # ...
      scorer: {Dirichlet: {decay: $ARM_DECAY}}
      random_arm: RA_SCORED
      selector: Thompson
```

A reference is a mapping with a `bot` key (`janken/kit/blueprint/refs.py`):

| key | meaning (default) |
| --- | --- |
| `bot` | the referenced bot's stem: a versioned one (`frequency_v1`) or a block (`frequency`) |
| `arms` | how many instances of it (1) |
| `space` | per parameter, **one value per arm** (a list of length `arms`) or one value they all share: a number, a constant (`OPP`) or a `$KNOB` of this bot. Its keys are the referenced bot's `defaults` keys, in any case (`p_rock` is `P_ROCK`); an unknown one is an error that lists them. Unset parameters keep the referenced bot's defaults. |
| `rotations` | the arms each instance makes, relative to that bot's own move: `COPY` plays it, `BEAT` beats it, `BEAT_BEAT` beats the move that beats it (`[COPY]`; from the opponent's side `[BEAT]`) |
| `side` | `MY`: the bot plays for us (`MY`); `OPP`: the bot as the opponent would play it, a model of us |
| `draws` | a bot of level 2+: its move by that many Thompson draws (0: its best-scored arm) |
| `random_arm` | a bot of level 2+: its random arm replaced (`RA_NONE`, ...) |

An arm is the referenced bot's **core**, its knobs bound to the arm's values; its guards
and overlays are left out, since they are about playing the game, not about predicting. An
L1 becomes its signal, rotated (a `Sim` from the opponent's side). A bot of level 2 or
more becomes a `Replay` of its whole bandit, from either side: from ours its symbol is its
own move, from theirs their likely move.

A reference also stands for a whole core: a blueprint's `core` (the bot is another one,
plus its own guards and overlays, at the same level) or a Gate's `main` bandit. A
`Heuristic` may play one named bot straight:

```yaml
# bots/l2/smartbot_staller_v1.yaml: smartbot, plus stalling
blueprint:
  core: {bot: smartbot_v1, space: {ARM_DECAY: $ARM_DECAY, TABLE_DECAY: $TABLE_DECAY, MAX_MATCH: $MAX_MATCH}}
  overlays: [{Stall: {...}}]

# bots/l4/gate_main_first_v1.yaml: smartbot_sims, and its replay as a gated expert
blueprint:
  core:
    Gate:
      main: {bot: smartbot_sims_v1}
      experts:
        - {bot: smartbot_sims_v1, side: OPP, draws: 256, rotations: [BEAT]}
      rule: MAIN_FIRST
      edge: $EDGE

# bots/l3/anti_smartbot_sims_v1.yaml: beats smartbot_sims' likeliest move (L3)
blueprint:
  core:
    Heuristic: {signal: {bot: smartbot_sims_v1, side: OPP, draws: 256}}
```

The aggregators:

- **`Bandit`**: every arm of its `predictors` (plus an optional `random_arm`); a `scorer`
  keeps every arm's record and a `selector` picks the arm to play. With no scorer
  (`First`), it plays its first arm with a move.
- **`Gate`**: a gatekeeper between a `main` Bandit (Thompson sampling) and gated `experts`
  (one gated arm per rotation, the expert's prediction made once), switching by their own
  records and a `rule` (`EDGE`, `ANTI_FIRST`, `ANTI_FIRST_HOLD`, `BANDIT`, `MAIN_FIRST`,
  `LEADER`, `LEADER_PRIORITY`; only the LEADER rules gate more than one arm).
- **No repeated arms**: an aggregator never names the same bot twice with the same
  parameters and side (it would be the same predictor, computed twice): one entry, with
  all its rotations.
- **`NaiveBayes`**: listed among a Bandit's predictors with no `inputs`, a posterior over
  the opponent's move from the bandit's other arms.

### Blocks

`bots/blocks/` holds L1 heuristics that exist to be named as arms, with every field of
their signal exposed as a parameter: `frequency`, `ngram`, `backoff`, `longest_match`,
`second_match`, `relative`, `geometry`, `rarest`, `period`, `score_state`, and
`oracle_expert` (research only). They are
never in a pool, a tournament or the species book. Any bot can be named, though: the
field's versions, the blocks, and the retired bots of `bots/inactive/`. Stems are unique
across all of them.

### Structural parameters

Some fields shape the compiled bot (an n-gram's `order`, the history `ctx` a matcher reads,
whether a signal samples). They take a `$KNOB` too, but it is bound when the bot is
compiled (from its defaults) or named as an arm (from the arm's values), never at run
time. So an arm's structural parameter takes literals, not this bot's `$KNOB`, and a space
file can't tune one (`janken/kit/blueprint/binding.py`).

## The grammar

The grammar lives in `janken/kit/declare.py`.

- A stage is `Name` (no arguments), `{Name: {field: value}}` or `{Name: [values]}`.
  `Name` is a stage or predictor class of `janken/kit/blueprint/` (the table below).
- A mapping with a `bot` key is a bot reference (above). An aggregator's arms take nothing
  else, but a `NaiveBayes`.
- `$NAME` is a knob read from the bot's `defaults`; an UPPER_CASE word is a constant
  (`OPP`, `MY`, `JOINT`, `BEAT`, `ROCK`, `TIES_FIRST`, `RA_SCORED`, `CHAMPION`,
  `ALL_ROTATIONS`, ...). A default may be a constant too (`CTX: OPP`).

## The stages

| stage | what it does | kinds |
| --- | --- | --- |
| guards | answer the round first, in order | `Opening`, `Noise`, `OnInvalid` |
| view | models see only rounds where both moves are valid | (always) |
| signals | each proposes a symbol, or none (an L1's `Heuristic` plays one) | `LastMove`, `Frequency`, `NGram`, `Backoff`, `LongestMatch`, `SecondMatch`, `Relative`, `React`, `Geometry`, `Rarest`, `Period`, `ScoreState`, `Constant`, `Cycle`, `Biased`, `WinStay` |
| aggregators | bots made of bots, named | `Bandit` (scorer + selector over arms), `Gate` (main bandit vs gated experts), `NaiveBayes` (over the other arms) |
| rotations | each arm plays its bot's move turned | `COPY`, `BEAT`, `BEAT_BEAT` |
| scorer | every arm's record, counterfactually | `Dirichlet`, `DecayedNet`, `DropSwitch` (+ a random arm: `RA_SCORED` / `RA_PINNED`) |
| selector | a Bandit's arm to play | `First`, `Greedy`, `Thompson`, `SampledVote`, `ChooseSelector` |
| overlays | transform the chosen move | `Stall`, `Team` (`handshake`: the fleet's opening moves; `vigilant`: stop throwing at a teammate's first non-throw; a fleet's champion gets it from its file's `fleet` section, below), `EmitInvalid` |

## Fleets

A fleet is one file, its champion's. Its `fleet` section adds the champion's `Team`
overlay; each support is the same bot with role SUPPORT and has no file of its own.
`janken bot export CHAMPION` writes one script per bot of the fleet.

```yaml
fleet:
  size: 5                                      # bots, the champion included
  supports: [achilles_v4, ajax_v4, hector_v4, odysseus_v4]   # optional: <champion>_support_K
  handshake: [PAPER, PAPER, SCISSORS, ROCK, PAPER, SCISSORS, PAPER, PAPER]
  vigilant: true
blueprint:
  core: {bot: replay_hunter_wide_v1, space: {EDGE: $EDGE, ...}}
```

`janken bot fleet BASE CHAMPION` writes such a file on any bot (with a random
handshake of `fleet.handshake_length` moves) and exports it.

## Rules

- **Knobs** are literals or `$NAME`, read from the bot's parameters (`defaults` order, at
  most 8). Every `defaults` key must feed a knob. See
  [Parameters and spaces](parameters-and-spaces.md).
- **Reuse bots, not code**: a new aggregator names the bots it combines. What several bots
  share is a bot they all name (a block, or a field version).
- **New ideas** become new stage kinds in `janken/kit` (a dataclass in its
  `janken/kit/blueprint/` module and its compiled half), never logic inside a bot file: a
  bot file holds no code. A new signal is usually best exposed as a block too. A new way
  of combining predictors is a new aggregator (`janken/kit/blueprint/composites.py`),
  lowered to what the pipeline plays (`lowering.py`).
- **Moves** are `0/1/2` = rock/paper/scissors (`janken.kit.moves`). A bot may return
  `INVALID`: that loses the round, and the opponent sees `INVALID` in its history. **Three
  in one match forfeit it.** `CRASH` forfeits at once. `EmitInvalid` spends at most two.
- **Randomness**: only `random.random()`, `random.randrange(n)` and
  `random.gammavariate(a, 1.0)` inside compiled stages. The engine gives each side of a
  match its own stream of the match seed, so a seeded match is reproducible and a bot can't
  see its opponent's draws.
- **A bot's logic never changes under its filename** once it has results: a new idea gets
  a new file (see `research/README.md`). That holds for the bots it names too, so
  references name exact stems, and a bot's identity (its source hash) covers the bots it
  names.
- Replays nest at most three deep: an L5 over an L4 over an L3 over an L2 compiles, one
  more layer of replays doesn't.
- Bots run in-process with no sandbox, so only run bots you trust.

Inside the research loop, the `/build` skill writes a bot for you.
