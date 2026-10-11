# The move dataset: bots as predictors

Besides playing, a bot can be read as a **predictor**: given the moves so far, which move
will the opponent play next? The move dataset stores real matches round by round, so
predictors can be scored and tuned offline, without playing new matches.

## The task

Predict a player's next move from both players' moves so far. Every stored match is
replayed from both sides, so one match gives two prediction sequences.

A bot's core (signals, rotations, scorer, selector; not its guards or overlays) is
replayed over the stored rounds. The move it would play implies its prediction: the
opponent move that move beats. A parameter that only guards or overlays read can't change
a prediction, so `predict` refuses it and `predict-tune` drops it. One compiled kernel
(`janken/lab/predict_kernel.py`) takes any bot's compiled blueprint as arrays, so new bots
and parameters never recompile.

**Metrics** (`janken/lab/metrics.py`):

- **accuracy**: share of correct predictions (chance: 1/3).
- **macro F1**: F1 averaged over rock, paper and scissors, so a predictor that always says
  "rock" doesn't look good.
- **kappa** (Cohen's): accuracy corrected for chance (chance: 0).
- **edge**: expected wins minus losses per round when playing what beats the prediction
  (chance: 0). The closest to what matters in a match.

## Storage

The dataset is a DuckDB file in the workspace, `experiments/dataset.duckdb` (settings
under `dataset` in `janken.toml`). Two tables:

- `matches`: one row per match: `match_id`, `batch_id`, `played_at`, `rounds`,
  `rounds_played`, the match `seed` and its batch's, each player's `label`, `stem`,
  `path`, resolved `params`, `overrides` and file `sha256`, the outcome, forfeits, the
  library hash, git commit and the command line, and a `holdout_key`.
- `rounds`: one row per round played: `match_id`, `round`, `p1_move`, `p2_move` (0/1/2
  rock/paper/scissors, 3 invalid).

The dataset is **append-only**: nothing updates or deletes a row.

- **Chunks.** A batch is committed in chunks of `dataset.batch_matches` matches. Each
  chunk is one transaction, under the batch's id and match ids that continue the stored
  ones.
- **Interruptions.** An interrupted `lab dataset add` keeps the chunks it committed: a
  complete prefix of its batch. Chunking never changes the data, because every match's
  seed and holdout key are drawn from the batch seed up front.
- **Splits.** Each match draws its `holdout_key` once. Below `dataset.holdout` (0.2) the
  match is in the **test** split forever, otherwise in **train**. So tuning on train and
  validating on test stays honest as the dataset grows.

## Commands

All of them are low level (`janken lab …`) and take the [common flags](cli.md#the-common-flags).
`--workspace` picks the dataset.

```bash
# Grow it: every bot vs every bot, 5 matches per pair (dataset.matches by default).
uv run janken lab dataset add bots/ --matches 5
uv run janken lab dataset add bots/smartbot.yaml bots/smartbot_sims.yaml:ARM_DECAY=0.8 \
  --matches 10 --rounds 1000

# What's in it: matches, rounds, batches, the test split; --players lists every player.
uv run janken lab dataset info --players

# Score predictors (on dataset.split, test by default), per predicted player too.
uv run janken lab predict bots/smartbot.yaml bots/iocaine_lite.yaml --players

# Tune one predictor for edge (on dataset.tune_split), validating on the test split.
uv run janken lab predict-tune spaces/iocaine_lite.yaml --study ioc-pred-v1 --metric edge

# AutoML: pick the best predictor, and its params, among three.
uv run janken lab predict-tune spaces/smartbot.yaml spaces/iocaine_lite.yaml \
  spaces/markov2_joint.yaml --study automl-v1 --effort thorough
```

### `lab predict-tune`

It reuses the [space files](parameters-and-spaces.md).

- **One space file** tunes that predictor.
- **Several space files** make it **AutoML**: each trial first picks the predictor (a
  param named `predictor`), then that predictor's params.

How a study runs:

- **Budget.** `--trials` and `--validate-top` default to the `--effort` budget
  (`predict_trials`, `validate_top`).
- **Pruning.** Each trial is scored in `dataset.chunks` steps, so the median pruner can
  stop it early.
- **A fixed snapshot.** A study pins the newest match id when it starts, so it keeps
  scoring the same matches as the dataset grows.
- **Storage.** Studies live in `experiments/tuning/predict/`.
- **Recorded validation.** The scores on the test split of the best trials and of every
  predictor's defaults go to the `predict_validations` table of `experiments/runs.duckdb`:
  study, predictor, trial (−1: defaults), training value, split and the four metrics.
  `janken lab study show NAME` lists them.
