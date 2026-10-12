---
name: classify
description: Classify a kept janken bot into the field's species with `janken species classify` - a new species (named, v1), the next version of its level's closest species (it is no worse on any matchup and better on one, or as good and more than 2x faster; the old version retires), or a variant (it retires). Keeps the field one bot per species, so pools stay diverse. Use after a keep verdict, when `janken status` says classify, or when the user asks how alike bots are or how diverse the field is.
---

# Classify (/classify)

The field holds **one bot per species**: its current version, `bots/<level>/<species>_vN.yaml`.
Near-copies crowd the 20-bot pools and tilt every experiment toward one family, so each
kept bot is classified before anything else is built on it. Run every command as
`uv run janken ...`. The lineage lives in `research/species.md`; the rules in
`docs/experiments.md` (Species).

```
kept note --> species compare --> species classify NNNN -+--> new species   --> <name>_v1
                                                         +--> next version  --> <species>_v{N+1}, old one retires
                                                         +--> variant       --> retires to bots/inactive/legacy/
```

## 1. Look first

```bash
uv run janken species compare <bot>     # the field's species by core agreement
uv run janken species census            # alike pairs and species per level (read-only)
```

Both replay the bots' cores on the move dataset (`species.matches` matches of
`species.split`). No dataset, or an empty split: grow it first,
`janken lab dataset add bots/l1 bots/l2 ...`.

**Versions never cross levels.** Only a species of the bot's own level can take it as
its next version or variant; a bot alike a species of another level is a new species.

## 2. Classify

```bash
uv run janken species classify NNNN
```

- **No species of its level is alike** (core agreement below `species.agreement`):
  it's a **new species**, and the command stops and asks for a name.
- **One is alike:** a paired run against that species' current version
  (`species.round_robins`, 40 by default; `--effort` / `--round-robins` override it, but
  `quick` proves nothing). Then:
  - profile correlation below `species.profile_correlation`: a **new species** after
    all (alike moves, different results);
  - worse on no matchup and better on at least one (Bonferroni over the matchups): the
    **next version**;
  - worse on none and better on none, but **more than `species.speed_factor` (2x) faster**
    in self-play: the **next version**;
  - otherwise a **variant**.

The command moves the files, records the lineage in `species.md`, and writes the note's
`Species` field and section. It never reruns a stored `species-NNNN` run, so a rerun
(with `--name`, or after a cut run) is cheap.

## 3. Name a new species

```bash
uv run janken species classify NNNN --name <name>
```

The name describes the **mechanism**, not the lineage or the result: snake_case, short,
not taken in `species.md`, with no level, version or `new`/`better` in it. Good:
`bayes_combiner`, `outcome_rotation`, `staller`. Bad: `smartbot2`, `l2_best`, `new_gate`.

## 4. Tidy the books

- `bots/README.md`, "The field" table: the bot's row under its new stem (a new species
  gets a one-line "what it does"; a promotion replaces the old version's row; a variant
  has no row).
- A retired version or a variant: a row in `bots/inactive/legacy/README.md` (bot, level,
  why it left, the note).
- **Superseded bots leave their dependents too.** When a bot retires (an old version
  or a variant), no field bot may keep naming it: find them with
  `grep -rln "<stem>" bots/l*/`, transitively (a bot naming one that changes changes
  too). Drop the arm, or point it at the species' current version when that arm is the
  bot's whole idea. A dependent with no results yet is edited in place; one with
  results keeps its stem (a stem's logic never changes) and gets its next version,
  `<species>_v{N+1}` (its lineage entry names the removed arm and the date; the old version goes to
  `inactive/legacy/`). Re-check each edited bot with `janken bot check` and
  `species compare`. `inactive/` and the Oracles (calibrated on what they mock) are left
  as they are.
- A new species that `census` shows thinning a level, or a variant that nearly won: say
  so in the note's `--analysis` next time, or as an idea (`/ideate`).

Under `/lab-loop`, commit as
`species: <old stem> --> <new stem> (new|promoted|variant)`, staging `bots/`, `spaces/` and
`research/`.
