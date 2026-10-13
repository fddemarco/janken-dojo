# The command line

```bash
uv run janken COMMAND ...      # every command takes --help
```

The CLI speaks the lab's language and comes in two levels:

- **High level:** one command per step of the self-improvement lifecycle. These commands
  keep the research notebook's books, so a step is one command.
- **Low level** (`janken lab ...`): ad hoc runs, queries and reports that never touch the
  notebook.

Every parameter is listed in the [CLI reference](cli-reference.md), and every default
lives in [`janken.toml`](configuration.md).

## The language

| word | meaning |
| --- | --- |
| **bot** | a YAML file in `bots/`; its stem is its identity ([Writing a bot](writing-bots.md)) |
| **variant** | a bot with parameter overrides: `bots/l1/x.yaml:NAME=value,NAME=value` |
| **candidate** | a bot under test |
| **baseline** | a bot a candidate must beat, played in the same run, so the comparison is paired |
| **pool** | the random opponents a round robin draws from the bots dir (candidates excluded) |
| **round robin** | one pool played against the candidates |
| **run** | a stored experiment: every match of its round robins |
| **effort** | a named evidence budget: `quick`, `standard`, `thorough` |
| **space** | what a bot is tuned over (`spaces/<bot>.yaml`) |
| **fleet** | a champion and its supports, tuned together (supports at weight 0) |
| **study** | a tuning search, made of **trials** |
| **validation** | replaying a study's best trials on fresh pools: the only evidence a study gives |
| **note** | an experiment's or a study's record: hypothesis --> results --> verdict |
| **verdict** | `keep`, `drop` or `iterate` |
| **idea** | a backlog item (`research/ideas.md`) |
| **insight** | a confirmed, general finding (`research/insights.md`) |
| **dataset**, **predictor** | the stored moves of many matches, and a bot read as a next-move predictor |
| **species**, **version** | a family of alike bots of one level, and its current bot in the field: `<species>_vN` ([Species](experiments.md#species)) |

## The lifecycle (high level)

```
status --> idea --> bot new / check --> evaluate --> verdict --> species classify --> insight
   ^                                    +--> tune -+                                     |
   +-------------------------------------------------------------------------------------+
```

| command | does |
| --- | --- |
| `janken status` | the research state, and the **next step** with its command |
| `janken idea add / list / show / start / done / drop` | the backlog (`done` and `drop` close an idea without a note: `--reason` says what realised or refuted it) |
| `janken bot new NAME --from BOT` | scaffold a bot (and its space file); then edit its blueprint |
| `janken bot check / list / show` | verify a bot (contract, compile, smoke run); inspect bots |
| `janken bot export NAME` | a bot (a champion: with its fleet's supports) as tournament submission scripts: stdlib-only `play(my_moves, opp_moves)` files in `exports/NAME/`, one per fleet bot |
| `janken bot fleet BASE CHAMPION` | a fleet on a bot: `bots/inactive/fleets/CHAMPION.yaml` (`--folder`, under the bots dir) (core BASE, a `fleet` section with `--size`, `--support` names and a random handshake of `--handshake-length` moves), then exported (`--no-export`: not) |
| `janken evaluate CANDIDATE... --baseline BOT --hypothesis ...` | a new note, the experiment, its results written into the note |
| `janken tune BOT... [--support BOT...] --hypothesis ...` | a new note, the study, its validation written into the note |
| `janken species classify NOTE [--name NAME]` | a kept bot: a new species (`<name>_v1`), the next version of its level's closest species (the old one retires), or a variant (it retires) |
| `janken species compare BOT / census / list` | how alike a bot's core is to each species; the field's alike pairs and species per level; the lineage (`research/species.md`) |
| `janken species variants LIST OUT` | which parameter variants of field bots (a list of specs) agree with no species of their level: new bots by the species rule |
| `janken verdict NOTE keep\|drop\|iterate --summary ...` | close the note; its idea becomes done, dropped or stays open |
| `janken insight add --note NOTE [--note NOTE ...] ...` | record an insight citing the notes' stored results (tentative when no 95% CI excludes 0; a note with no stored result is refused) |
| `janken insight list / supersede` | read, or strike a contradicted insight |
| `janken tournament` | the whole field: standings, Glicko-2 ratings, titles |
| `janken config show / get / set / unset / path / check` | every default ([Configuration](configuration.md)) |

### One iteration, end to end

```bash
uv run janken status
uv run janken idea add "**TPI-lite**: one naive-Bayes arm over every predictor" \
  --priority P1 --motivation "rps_kaggle section 4.2"
uv run janken bot new bayes_combiner --from smartbot_sims_v1 --idea 22 \
  --description "TPI-lite: a naive-Bayes combiner arm.\nMultiplies every predictor's evidence."
# ... edit bots/l2/bayes_combiner.yaml ...
uv run janken bot check bayes_combiner
uv run janken evaluate bots/l2/bayes_combiner.yaml --baseline bots/l3/smartbot_sims_v1.yaml \
  --hypothesis "beats smartbot_sims by >= 2 pts, mostly vs the metabots" --idea 22
uv run janken verdict 0007 keep --summary "+3.1 pts [+0.8, +5.4] vs sims3 ..."
uv run janken species classify 0007 --name bayes_combiner   # a new species: bayes_combiner_v1
uv run janken insight add --note 0007 --finding "..." --mechanism "..." \
  --implication "..."
```

- **Interrupted runs:** if Ctrl-C (or a crash) cuts an evaluation, the finished matches
  stay stored and `status` says so. `janken evaluate --note 0007` finishes the run.
- **Sequential evaluation:** with `--sequential` (`evaluation.sequential`, on by default)
  and a baseline, a new note's run plays its round robins in `evaluation.looks` steps.
  It stops at the first step where the candidate vs the first baseline is clear of 0
  (each step spends part of `evaluation.alpha`), or where going on is futile: even if
  the effect seen so far is the true one, clearing the last step is unlikely
  (`evaluation.futility`).
- **Tuning:** `janken tune --note NNNN` resumes a study.

## The common flags

Every lab command, high and low level, takes the same flags. They are defined once in
`janken/cli/options.py`.

| group | flags |
| --- | --- |
| Workspace | `--workspace` (runs, studies, dataset), `--notebook` (`research/`), `--bots-dir`, `--spaces-dir` |
| Evidence | `--effort quick\|standard\|thorough`, `--rounds`, `--round-robins`, `--pool-size`, `--seed`, `--allow-small-pool`, `--mocks`, `--variants SHARE` (pool members played at parameter variants), `--pool-list FILE` (pools drawn from a list of specs, repeatable) |
| Execution | `--workers`, `--cache auto\|on\|off`, `--progress auto\|on\|off` |
| Output | `--format text\|json`, `--quiet` |

**Precedence** (later overrides earlier):

1. `janken.toml`;
1. `janken.local.toml` (`config set --local`);
1. the `--effort` budget, for round robins, trials and validation sizes;
1. an explicit flag.

So `--effort thorough` plays 40 round robins, and `--effort thorough --round-robins 30`
plays 30.

Where flags apply differently:

- **Commands that don't play matches** take the evidence flags too. `status` and
  `lab leaderboard` use `--rounds` to keep only runs of that length.
- **Tuning** reads `--round-robins` as the pools *per trial*. Its seed comes from
  `tuning.seed` unless `--seed` is given.
- **`--format json`** prints machine-readable results, for scripts and agents. Use it
  with `status`, `idea list`, `lab runs`, `lab query`, and so on.

## The low level: `janken lab ...`

| command | does |
| --- | --- |
| `lab experiment CANDIDATE...` | candidates vs fresh random pools, stored as a run (no note) |
| `lab resume RUN` | play the round robins an interrupted run is missing |
| `lab report RUN...` | a run's full report: scores, ratings, paired comparisons, every matchup |
| `lab runs` | every stored run, with its status |
| `lab history STEM` / `lab leaderboard` | a bot across runs, or every candidate pooled |
| `lab match A B` | one match and its transcript (nothing stored) |
| `lab query "SELECT ..." [--db runs\|dataset]` | read-only SQL over the runs database or the move dataset |
| `lab space BOT...` | scaffold space files |
| `lab study run SPACE... --study NAME` / `lab study show NAME` / `lab study list` | Optuna studies without a note |
| `lab dataset add BOTS...` / `lab dataset info` | grow or summarise the move dataset |
| `lab predict BOT...` / `lab predict-tune SPACE... --study NAME` | bots as next-move predictors |
| `lab profile run -- COMMAND...` / `lab profile bench -- COMMAND...` | a command's hotspots and whether fixing them pays; its wall time, vs a `--baseline` |
| `lab profile list` / `lab profile show ID` / `lab profile spans` | stored profiles; the timing spans every command logs, slow ones flagged |
| `lab gauntlet variations OUT` | the field's bots and up to `gauntlet.per_bot` parameter variants of each (drawn from its space file, kept only if they change its play), one spec per line |
| `lab gauntlet nash LIST OUT --name LOG` | which bots of a list are Nash "with extra steps": no probe L1 (`gauntlet.nash_probes`) skews their results either way; with `--sequential`, a bot one probe skews by `gauntlet.nash_decisive` in its first match is settled at once |
| `lab gauntlet run LIST --cand BOT... --name LOG` | candidates vs every opponent of a list, up to `gauntlet.seeds` seeds each; the opponents under `gauntlet.threshold` of rounds won (logged per match in the workspace, so it resumes). With `--sequential`, a pairing stops once its share is clear of the threshold (after `gauntlet.min_seeds`, at `gauntlet.stop_alpha` spent over the seeds) |
| `lab arena LIST --name LOG` | research only: an experimental learner (`janken/experimental/`, Vowpal Wabbit learning online from the match's history and from what the `arena.experts` would play from either seat) vs every opponent of a gauntlet list, `arena.seeds` seeds each, logged and reported like `lab gauntlet run` so a kit bot's gauntlet on the same list compares directly |
| `lab identify LIST --name LOG` | research only: can an opponent bandit's parameters be told from its moves in time? A particle posterior over `identify.hypotheses` (each bot's parameter vectors drawn from its space file, replayed from the opponent's seat), scored every `identify.checkpoint_every` rounds; the rounds after `identify.commit_round` played four ways (exploit the posterior, keep the `identify.probe`, the oracle, and switch: whichever of exploit and keep has the better decayed counterfactual record). `--component BLOCK`: blocks read from both seats at every rotation join the particles. `--leave-one-out`: the opponent's species is never a hypothesis (an unknown architecture). Run it with `--rounds 250` for 250-round matches |

```bash
uv run janken lab query "SELECT bot_a, bot_b, wins_a, wins_b FROM matches
  WHERE run_id LIKE '%0007%' AND (stem_a = 'geometry' OR stem_b = 'geometry')"
uv run janken lab match bots/l2/bayes_combiner.yaml bots/l1/geometry_v1.yaml --rounds 200 --seed 3
```

## Errors and exit status

- **A refused step** prints `error: ...` and exits with status 2. Examples: a missing note,
  a reused bot stem, an insight citing a note with no stored result, a bad config value.
- **Ctrl-C** exits with status 130; whatever was already committed stays stored.
