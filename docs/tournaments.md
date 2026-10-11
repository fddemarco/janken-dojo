# Running a tournament

`janken tournament` plays every bot in the bots dir against every other and prints the
standings. It's the quick way to see a field; to decide whether a bot is better, use an
[experiment](experiments.md), which repeats this over many random pools.

```bash
uv run janken tournament [options]
```

Besides the [common flags](cli.md#the-common-flags) (`--bots-dir`, `--rounds`, `--seed`,
`--workers`, …), it takes:

| option | default (`janken.toml`) | what it does |
| --- | --- | --- |
| `--matches N` | `tournament.matches` (1) | matches per pair in the round robin |
| `--games N` | `tournament.games` (0: a round robin) | a balanced random schedule where each bot plays about N games |
| `--league TITLE` | `tournament.league` (all) | list only bots finishing with that title: `novice`, `cm`, `master`, `im`, `gm` |
| `--json-out FILE` | none | also write standings, ratings and every match transcript |
| `--verbose` | off | print every match |

- **Seed.** The seed is `tournament.seed` unless `--seed` is given; `-1` draws a fresh
  one.
- **Batches.** Matches are played in batches of `tournament.batch_matches` behind a
  progress bar; the first batch also compiles the bots.
- **Nothing is stored:** use `--json-out` (or `--format json`) to keep the results.

## Use cases

```bash
# The whole zoo, reproducibly, 3 matches per pair.
uv run janken tournament --matches 3 --seed 1

# A big field, quickly: ~50 games per bot instead of every pair.
uv run janken tournament --games 50

# Only the grandmasters, and save everything for later inspection.
uv run janken tournament --matches 3 --league gm --json-out gm.json

# Watch every match of a small field.
uv run janken tournament --bots-dir my_bots/ --verbose
```

## Ratings and titles

Nothing persists between runs. Every bot enters at **1500**, and the whole run is **one
Glicko-2 rating period**: every match is scored against the ratings the bots brought in,
so the order matches finish in can't change the result. Matches are scored on **who won
the match** (1 / ½ / 0); a forfeit is a loss. The standings rank by rating, and the run's
points (3 a win, 1 a draw) break ties.

A title is read off the rating; each one is the bot's "league":

| Title | Rating |
| --- | --- |
| Novice | start |
| Candidate Master | 1600 |
| Master | 1700 |
| International Master | 1900 |
| Grandmaster | 2100 |
