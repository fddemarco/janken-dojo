"""The lab's configuration: every default, read from `janken.toml`, in one place.

`janken.toml` (at the project root, committed) holds **every** setting, one table per
domain concept; `janken.local.toml` (gitignored, optional) overrides any of them on
one machine. `janken config ...` reads and edits both (janken/config_file.py). Nothing
else in the code carries a default: command-line options take theirs from here.

Each setting is a field of a frozen dataclass below, whose metadata holds its help
text (shown by `janken config show` and reused by the CLI's option help) and its
constraints. The loader checks types, choices and minimums, and requires every key.

A few process-wide switches can also come from the environment, because numba reads
them when a function is decorated (janken/kit/jit.py), before any command runs:

    $JANKEN_JIT = on | off            overrides engine.jit
    $JANKEN_NUMBA_CACHE = 1 | 0       set by `apply` for the running command
    $JANKEN_PROGRESS = auto | on | off   overrides output.progress
    $JANKEN_SPANS = on | off          overrides telemetry.spans
"""

import dataclasses
import enum
import functools
import math
import os
import tomllib
import typing
from collections.abc import Iterator, Mapping, MutableMapping

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# $JANKEN_CONFIG / $JANKEN_LOCAL_CONFIG choose other files (the test suite's own,
# with no local overrides; subprocesses inherit them). An empty path means none.
CONFIG_ENV = "JANKEN_CONFIG"
LOCAL_CONFIG_ENV = "JANKEN_LOCAL_CONFIG"
CONFIG_FILE = os.environ.get(CONFIG_ENV, os.path.join(ROOT, "janken.toml"))
LOCAL_FILE = os.environ.get(LOCAL_CONFIG_ENV, os.path.join(ROOT, "janken.local.toml"))
JIT_ENV = "JANKEN_JIT"
CACHE_ENV = "JANKEN_NUMBA_CACHE"
PROGRESS_ENV = "JANKEN_PROGRESS"
SPANS_ENV = "JANKEN_SPANS"
PROGRESS_MODES = ("auto", "on", "off")
FORMATS = ("text", "json")
EFFORTS = ("quick", "standard", "thorough")
SAMPLERS = ("tpe", "grid", "random")
MODES = ("full", "candidates")
SPLITS = ("train", "test", "all")
LEAGUES = ("novice", "cm", "master", "im", "gm", "all")
# The metrics a predictor is scored on (janken/lab/metrics.py); any can be tuned.
METRICS = ("accuracy", "macro_f1", "kappa", "edge")
RANDOM_SEED = -1  # a seed setting of -1 draws a fresh seed (and records it)
_ON = ("1", "on", "true", "yes")
_OFF = ("0", "off", "false", "no")


class ConfigError(ValueError):
    """A configuration file that doesn't match the schema."""


def setting(
    help: str, choices: tuple[str, ...] = (), minimum: float = -math.inf
) -> typing.Any:
    """A setting: a required dataclass field with its help text and constraints."""
    return dataclasses.field(
        metadata={"help": help, "choices": choices, "minimum": minimum}
    )


# --- the schema ------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class EngineConfig:
    """How bots are compiled."""

    jit: bool = setting("compile bots and the referee with numba (off: plain Python)")
    cache_commands: tuple[str, ...] = setting(
        "commands that keep numba's compiled code on disk"
    )


@dataclasses.dataclass(frozen=True)
class OutputConfig:
    """What commands print."""

    progress: str = setting(
        "progress bars: auto (only on a terminal), on or off", PROGRESS_MODES
    )
    format: str = setting("how results print: text (markdown tables) or json", FORMATS)
    quiet: bool = setting("print only what a command must (its ids and errors)")


@dataclasses.dataclass(frozen=True)
class WorkspaceConfig:
    """Where things live, relative to the project root."""

    dir: str = setting("the workspace: runs, studies and the move dataset")
    notebook: str = setting("the research notebook: ideas, notes, insights")
    bots_dir: str = setting("the bots, one YAML file each; pools are drawn from it")
    spaces_dir: str = setting("the space files, one per tunable bot")


@dataclasses.dataclass(frozen=True)
class ExecutionConfig:
    """How matches are played."""

    workers: int = setting("threads playing matches (0: every core)", minimum=0)
    flush_s: float = setting(
        "seconds between flushes of the matches finished while a batch plays"
        " (logged and stored as they end; 0: once, at the batch's end)",
        minimum=0,
    )


@dataclasses.dataclass(frozen=True)
class MatchConfig:
    """One match."""

    rounds: int = setting("rounds per match", minimum=1)


@dataclasses.dataclass(frozen=True)
class PoolConfig:
    """The random opponents a candidate plays."""

    size: int = setting("bots drawn into each pool", minimum=1)
    allow_small: bool = setting(
        "use every eligible bot when fewer than the pool size exist"
    )
    mocks: bool = setting(
        "draw the mocks (research-only stand-ins) instead of the bots they mock"
    )
    variants: float = setting(
        "the share of pool members that play a parameter variant drawn from their"
        " space file (0: every member at its defaults)",
        minimum=0,
    )
    lists: tuple[str, ...] = setting(
        "list files of specs (one per line, gauntlet lists) to draw pools from"
        " instead of the bots dir (none: the bots dir)"
    )


@dataclasses.dataclass(frozen=True)
class CalibrationConfig:
    """How a mock's expert is measured (janken lab calibrate)."""

    seeds: int = setting("matches the expert plays vs each opponent", minimum=1)


@dataclasses.dataclass(frozen=True)
class Budget:
    """How much evidence one effort level buys."""

    round_robins: int = setting("pools an evaluation plays", minimum=1)
    tune_round_robins: int = setting("pools every tuning trial plays", minimum=1)
    trials: int = setting("trials a tuning session runs", minimum=0)
    validate_top: int = setting("best trials replayed on fresh pools", minimum=0)
    validate_round_robins: int = setting("pools each validation plays", minimum=1)
    predict_trials: int = setting("trials a predictor-tuning session runs", minimum=0)


@dataclasses.dataclass(frozen=True)
class EffortConfig:
    """Named evidence budgets; `--effort` picks one, explicit flags override it."""

    default: str = setting("the effort used when none is given", EFFORTS)
    quick: Budget = setting("a smoke-sized budget: fast, noisy")
    standard: Budget = setting("the usual budget")
    thorough: Budget = setting("a budget for small effects")

    def budget(self, name: str) -> Budget:
        if name not in EFFORTS:
            raise ConfigError(f"unknown effort {name!r} (one of {', '.join(EFFORTS)})")
        found: Budget = getattr(self, name)
        return found


@dataclasses.dataclass(frozen=True)
class EvaluationConfig:
    """Experiments: candidates against random pools."""

    mode: str = setting(
        "full: every pair plays; candidates: only matches with a candidate", MODES
    )
    seed: int = setting("pools and match seeds (-1: a fresh, recorded seed)")
    sequential: bool = setting(
        "evaluate plays its round robins in looks, stopping once the paired"
        " comparison is clear (or futile): janken/lab/sequential.py"
    )
    looks: int = setting("looks spread over the planned round robins", minimum=1)
    alpha: float = setting(
        "the paired comparison's error rate, spent over the looks (O'Brien-Fleming)",
        minimum=0,
    )
    futility: float = setting(
        "stop when the chance of clearing the last look, if the effect seen so far"
        " is the true one, falls under this (0: never)",
        minimum=0,
    )


@dataclasses.dataclass(frozen=True)
class TuningConfig:
    """Optuna studies."""

    sampler: str = setting("how trials are chosen", SAMPLERS)
    prune: bool = setting("stop trials clearly below the median early")
    seed: int = setting("the pools and match seeds every trial plays")
    sampler_seed: int = setting(
        "the sampler's seed (-1: unseeded; leave it so for parallel workers)"
    )
    export_every: int = setting(
        "trials between re-exports of a study's trials.parquet", minimum=1
    )
    timeout_s: float = setting(
        "stop starting trials after this many seconds (0: no limit)", minimum=0
    )


@dataclasses.dataclass(frozen=True)
class SpaceConfig:
    """How `space` scaffolds a bot's space file from its defaults.

    A scaffolded range runs from default / spread to default * spread (an int range is
    rounded; a float default in (0, 1] keeps its high end at most 1), with
    `grid_points` evenly spaced grid values plus the default.
    """

    spread: float = setting("a scaffolded range: default / spread .. default * spread")
    grid_points: int = setting("grid values a scaffolded param gets", minimum=2)
    weight: float = setting(
        "a scaffolded space's weight in a multi-bot study (0: a fleet's support)",
        minimum=0,
    )


@dataclasses.dataclass(frozen=True)
class TournamentConfig:
    """`tournament`: the whole field plays."""

    matches: int = setting("matches per pair in the round robin", minimum=1)
    games: int = setting(
        "a balanced random schedule of ~N games per bot (0: a round robin)", minimum=0
    )
    league: str = setting("list only bots finishing with this title", LEAGUES)
    batch_matches: int = setting("matches per batch (one progress step)", minimum=1)
    seed: int = setting("the schedule and every match (-1: a fresh seed)")


@dataclasses.dataclass(frozen=True)
class DatasetConfig:
    """The move dataset and how predictors are scored on it.

    `file` is the DuckDB file in the workspace. A match whose stored holdout key is
    below `holdout` belongs to the test split. `predict-tune` maximises `metric`,
    scoring each trial in `chunks` steps so the pruner can stop it early. `dataset add`
    commits every `batch_matches` matches in their own transaction.
    """

    file: str = setting("the dataset's DuckDB file, in the workspace")
    holdout: float = setting("the share of matches held out as the test split")
    metric: str = setting("what predictor tuning maximises", METRICS)
    chunks: int = setting("steps a predictor-tuning trial is scored in", minimum=1)
    batch_matches: int = setting("matches per committed chunk", minimum=1)
    matches: int = setting("matches per pair a `dataset add` plays", minimum=1)
    seed: int = setting("a batch's seed (-1: a fresh, stored seed)")
    split: str = setting("the split predictors are scored on", SPLITS)
    tune_split: str = setting("the split predictor tuning trains on", SPLITS)


@dataclasses.dataclass(frozen=True)
class RunsConfig:
    """The runs database.

    `file` is the DuckDB file in the workspace. A process that finds it locked by
    another retries for up to `lock_timeout_s` seconds.
    """

    file: str = setting("the runs database's DuckDB file, in the workspace")
    lock_timeout_s: float = setting(
        "seconds to wait for a runs database another process holds", minimum=0
    )
    match_cache: bool = setting(
        "read back a match already played (same bots, overrides, seed, rounds and"
        " code) instead of replaying it (janken/lab/match_cache.py)"
    )


@dataclasses.dataclass(frozen=True)
class QueryConfig:
    """`lab query`: ad hoc read-only SQL."""

    db: str = setting("the database queried: runs or dataset", ("runs", "dataset"))
    limit: int = setting("rows printed at most", minimum=1)


@dataclasses.dataclass(frozen=True)
class StatusConfig:
    """What `status` shows."""

    recent_runs: int = setting("recent runs listed", minimum=0)
    ideas: int = setting("open ideas listed, by priority", minimum=0)
    leaderboard: int = setting("leaderboard rows listed", minimum=0)


@dataclasses.dataclass(frozen=True)
class ExportConfig:
    """`bot export`: bots as tournament submission scripts.

    A script is screened by the tournament's rules before it is written: it may only
    import `allowed_modules` and never name `banned_names`.
    """

    dir: str = setting("where exported scripts go (a folder per exported bot)")
    max_rounds: int = setting("the longest match an exported bot can play", minimum=1)
    allowed_modules: tuple[str, ...] = setting(
        "the modules a submission may import (the tournament's allowlist)"
    )
    banned_names: tuple[str, ...] = setting(
        "the builtins a submission may not name (the tournament's screening)"
    )


@dataclasses.dataclass(frozen=True)
class FleetConfig:
    """`bot fleet`: a fleet scaffolded on a bot (a champion and its supports).

    Its handshake is `handshake_length` moves drawn at random.
    """

    dir: str = setting("where a new fleet's champion file goes, under the bots dir")
    size: int = setting("bots in a new fleet, the champion included", minimum=2)
    handshake_length: int = setting(
        "moves in a new fleet's random handshake", minimum=1
    )
    vigilant: bool = setting(
        "a new fleet's bots stop throwing at a teammate's first non-throw"
    )
    export: bool = setting("export a new fleet's scripts as soon as it is made")


@dataclasses.dataclass(frozen=True)
class SpeciesConfig:
    """Species and versions: how a kept bot is classified (`janken species`).

    Two bots behave alike when their cores agree on at least `agreement` of the moves
    they predict on the dataset's `split`, and their per-opponent scores in a paired
    run correlate at least `profile_correlation`. A challenger replaces its species'
    current version when no matchup's 95% CI is below 0 and at least one is above 0 at
    the Bonferroni level `alpha` / matchups. Matchups with fewer than
    `min_matchup_matches` paired matches are left out. A challenger worse on no
    matchup and better on none still replaces the incumbent when it plays at least
    `speed_factor` times faster (self-play, timed `speed_repeats` times).
    """

    agreement: float = setting(
        "the share of predicted moves two bots' cores must agree on to be alike",
        minimum=0,
    )
    profile_correlation: float = setting(
        "the correlation two bots' per-opponent scores must reach to be alike",
        minimum=-1,
    )
    round_robins: int = setting(
        "round robins of the paired run against the species' current version",
        minimum=1,
    )
    sequential: bool = setting(
        "the paired run grows in looks and stops once the challenger is a variant"
        " (worse on a matchup at the alpha a look spends)"
    )
    looks: int = setting("looks spread over the paired run's round robins", minimum=1)
    mode: str = setting(
        "the paired run's mode: candidates (classify reads only the two candidates'"
        " matches) or full (pool vs pool too)",
        MODES,
    )
    promote_on_evaluation: bool = setting(
        "a kept bot whose evaluation's baseline was its level's species' current"
        " version is decided from that evaluation: the next version when not worse"
        " there and better or speed_factor times faster (no agreement bar, no run)"
    )
    min_matchup_matches: int = setting(
        "paired matches a matchup needs to count in the dominance test", minimum=2
    )
    alpha: float = setting(
        "the family-wise error of 'better on at least one matchup' (Bonferroni)",
        minimum=0,
    )
    split: str = setting("the dataset split the cores are compared on", SPLITS)
    matches: int = setting(
        "dataset matches the cores are compared on, evenly spread over the split",
        minimum=1,
    )
    speed_factor: float = setting(
        "a challenger as good as the incumbent replaces it when more than this many"
        " times faster",
        minimum=1,
    )
    speed_matches: int = setting(
        "self-play matches each bot plays when the two are timed", minimum=1
    )
    speed_repeats: int = setting(
        "times the timing is repeated (the fastest repeat counts)", minimum=1
    )
    legacy_dir: str = setting(
        "where retired versions and variants go, relative to the bots dir"
    )
    cores_dir: str = setting(
        "where computed cores are kept (one file per bot, code and histories),"
        " in the workspace"
    )


@dataclasses.dataclass(frozen=True)
class TelemetryConfig:
    """Timing spans: one JSON line per coarse operation, in the workspace.

    Every lab command logs a `command` span, and the costly steps inside it (compiling,
    playing, a round robin, a trial) log their own, so where the time goes can be read
    over weeks (`janken lab profile spans`). A command whose last run took
    `slow_factor` times its median is flagged slow.
    """

    spans: bool = setting("log timing spans ($JANKEN_SPANS overrides)")
    file: str = setting("the spans' JSON-lines file, in the workspace")
    max_mb: int = setting("size at which the spans file is rotated, in MB", minimum=1)
    slow_factor: float = setting(
        "a command's last run this many times its median is flagged slow", minimum=1
    )


@dataclasses.dataclass(frozen=True)
class ProfileConfig:
    """`lab profile`: hotspots, benchmarks and the optimization budget.

    A hotspot is worth an optimization session only when it holds at least
    `min_share` of the wall time, and removing `expected_cut` of it, on every use of
    the command projected over `horizon_days` (its rate from the last `window_days`
    of spans), saves at least the session's own `session_minutes`. A session tries
    at most `max_attempts` changes, and keeps one only if it cuts the fastest of
    `repeats` timed runs by at least `min_gain`.
    """

    dir: str = setting("where profiles and benchmarks go, in the workspace")
    interval_s: float = setting("the profiler's sampling interval, in seconds")
    top: int = setting("hotspots listed", minimum=1)
    jit: bool = setting("profile compiled code (off: plain Python, inside kernels)")
    warmup: bool = setting(
        "run the command once first, unmeasured (fills numba's on-disk cache)"
    )
    min_share: float = setting("the smallest share of wall time worth optimizing")
    expected_cut: float = setting("the share of a hotspot an optimization removes")
    window_days: int = setting("days of spans that estimate a command's use", minimum=1)
    horizon_days: int = setting("days of use a saving is projected over", minimum=1)
    session_minutes: int = setting(
        "an optimization session's cost cap, and the saving it must pay back",
        minimum=1,
    )
    max_attempts: int = setting("changes one session tries at most", minimum=1)
    min_gain: float = setting("the wall-time cut a change must show to be kept")
    repeats: int = setting("timed runs per benchmark (the fastest counts)", minimum=1)
    cooldown_days: int = setting(
        "days before a command is profiled again (unless its spans flag it slow)",
        minimum=0,
    )


@dataclasses.dataclass(frozen=True)
class GauntletConfig:
    """`lab gauntlet`: candidates vs every opponent of a list, variations included.

    `variations` draws `per_bot` variants of each field bot from its space file
    (`draws` Latin hypercubes at most), keeping those whose moves differ from the
    default's vs `variation_probes`; `exclude` names the bots it skips. `nash`
    calls a bot Nash-like when vs every one of `nash_probes` its rounds won minus
    lost stay under `nash_skew`. `run` plays `seeds` matches per opponent and
    reports those under `threshold`; with `sequential`, a pairing stops once its
    share is clear of the threshold (after `min_seeds`, at `stop_alpha` spent
    over the seeds: janken/lab/sequential.py). `nash` settles a bot after one
    match when a probe already skews it by `nash_decisive`. `fingerprint` reads
    tournament exports for each bot's margins over `fingerprint_probes` (scripted
    probes, research/probes.md, also read under their `fingerprint_aliases`) and
    names the `fingerprint_nearest` lab bots with
    the closest margins.
    """

    dir: str = setting("where gauntlet logs go, in the workspace")
    seeds: int = setting("matches per opponent (seeds 1..n)", minimum=1)
    threshold: float = setting("the share of rounds won a candidate must reach")
    sequential: bool = setting(
        "stop a pairing once its share won is clear of the threshold"
    )
    min_seeds: int = setting(
        "matches a pairing plays before it may stop (a spread needs two)", minimum=2
    )
    stop_alpha: float = setting(
        "the chance of stopping a pairing on the wrong side of the threshold, spent"
        " over its seeds (O'Brien-Fleming)",
        minimum=0,
    )
    batch: int = setting("matches per batch (one log write)", minimum=1)
    per_bot: int = setting("variants drawn per field bot", minimum=1)
    draws: int = setting("Latin hypercubes drawn per bot at most", minimum=1)
    seed: int = setting("the variants' sampler seed")
    probe_rounds: int = setting("rounds of a match that checks a variant", minimum=1)
    variation_probes: tuple[str, ...] = setting(
        "bots a variant is checked against: its moves must differ from the default's"
    )
    levels: tuple[str, ...] = setting("the level folders whose bots get variants")
    exclude: tuple[str, ...] = setting("field bots that get no variants (Nash-like)")
    nash_probes: tuple[str, ...] = setting("the simple bots a Nash check plays")
    nash_seeds: int = setting("matches per probe in a Nash check", minimum=1)
    nash_skew: float = setting(
        "rounds won minus lost a probe must reach for a bot not to be Nash-like"
    )
    nash_decisive: float = setting(
        "rounds won minus lost in one match vs a probe that settles a bot as not"
        " Nash-like at once (a Nash-like bot's match is about 0.05 off, one sd)"
    )
    fingerprint_probes: tuple[str, ...] = setting(
        "the scripted probes a fingerprint reads (lab paths; a tournament bot is a"
        " probe when its name contains a probe's stem)"
    )
    fingerprint_aliases: tuple[str, ...] = setting(
        "the names the probes are submitted under, NAME=STEM, so other players can't"
        " tell them from their names (a name matches whole, ignoring case and"
        " punctuation)"
    )
    fingerprint_nearest: int = setting(
        "lab bots listed per fingerprinted bot, closest first", minimum=1
    )


@dataclasses.dataclass(frozen=True)
class ArenaConfig:
    """`lab arena`: an experimental learner (janken/experimental/, research only)
    vs every opponent of a gauntlet list, logged and scored like a gauntlet.

    The learner is Vowpal Wabbit run with `vw_args`, learning online each round
    which move pays, from the last `history` rounds and from the moves the
    `experts` (kit bots, by stem) would play from either seat. It plays a random
    move with chance `explore`.
    """

    dir: str = setting("where arena logs go, in the workspace")
    seeds: int = setting("matches per opponent (seeds 1..n)", minimum=1)
    vw_args: str = setting("the learner's Vowpal Wabbit arguments (cost-sensitive)")
    history: int = setting("rounds of history the learner's features read", minimum=1)
    explore: float = setting("the chance the learner plays a random move", minimum=0)
    experts: tuple[str, ...] = setting(
        "kit bots (stems) whose moves, from either seat, are the learner's features"
    )


@dataclasses.dataclass(frozen=True)
class IdentifyConfig:
    """`lab identify`: can an opponent bandit's parameters be told from its moves?
    (janken/experimental/identify.py, research only).

    Each of the `hypotheses` (bots, by stem) gets `particles` parameter vectors
    drawn from its space file (seeded by `seed`), each replayed from the
    opponent's seat; a particle's weight is (1 - eps) for every round it names the
    opponent's move, eps / 2 for every round it misses. Every `checkpoint_every`
    rounds the posterior is scored and the particles under `prune_ratio` of the
    best one's weight are dropped. We play `probe` until `commit_round`, then the
    move that beats the posterior's vote; a parameter is "near" the truth within
    `near` of its space range. With `leave_one_out`, the opponent's own species
    is never a hypothesis (its architecture is unknown).
    """

    dir: str = setting("where identification logs go, in the workspace")
    seeds: int = setting("matches per opponent (seeds 1..n)", minimum=1)
    hypotheses: tuple[str, ...] = setting(
        "the bots (stems) whose parameter vectors are the particles"
    )
    particles: int = setting("parameter vectors drawn per hypothesis", minimum=1)
    eps: float = setting(
        "a particle's chance of missing the opponent's move (sets the posterior's"
        " sharpness)",
        minimum=0,
    )
    commit_round: int = setting(
        "the round from which we exploit the posterior", minimum=1
    )
    checkpoint_every: int = setting(
        "rounds between scorings of the posterior (and prunings)", minimum=1
    )
    prune_ratio: float = setting(
        "a particle under this share of the best one's weight is dropped", minimum=0
    )
    near: float = setting(
        "the share of a parameter's range within which an estimate counts as near",
        minimum=0,
    )
    probe: str = setting("the bot (stem) we play until the commit round")
    leave_one_out: bool = setting(
        "never count the opponent's own species among the hypotheses"
    )
    seed: int = setting("the particles' sampler seed")
    forget: float = setting(
        "each round, the posterior's weight on the evidence so far (1: none forgotten)",
        minimum=0,
    )
    switch_decay: float = setting(
        "the decay of the switch branch's records of keep and exploit", minimum=0
    )
    components: tuple[str, ...] = setting(
        "blocks (stems) whose moves from either seat, at every rotation, are"
        " particles too (no whole architecture assumed)"
    )


@dataclasses.dataclass(frozen=True)
class Config:
    """The whole of `janken.toml`."""

    engine: EngineConfig = setting("how bots are compiled")
    output: OutputConfig = setting("what commands print")
    workspace: WorkspaceConfig = setting("where things live")
    execution: ExecutionConfig = setting("how matches are played")
    match: MatchConfig = setting("one match")
    pool: PoolConfig = setting("the random opponents")
    calibration: CalibrationConfig = setting("the mocks' calibrations")
    effort: EffortConfig = setting("evidence budgets")
    evaluation: EvaluationConfig = setting("experiments")
    tuning: TuningConfig = setting("tuning studies")
    space: SpaceConfig = setting("space scaffolding")
    tournament: TournamentConfig = setting("tournaments")
    dataset: DatasetConfig = setting("the move dataset and predictors")
    runs: RunsConfig = setting("the runs database")
    query: QueryConfig = setting("ad hoc queries")
    status: StatusConfig = setting("the status report")
    export: ExportConfig = setting("submission scripts")
    fleet: FleetConfig = setting("fleets")
    species: SpeciesConfig = setting("species and versions")
    telemetry: TelemetryConfig = setting("timing spans")
    profile: ProfileConfig = setting("profiling and the optimization budget")
    gauntlet: GauntletConfig = setting("gauntlets: every opponent on its own")
    arena: ArenaConfig = setting("experimental learners vs a gauntlet's opponents")
    identify: IdentifyConfig = setting("identifying opponents' parameters")

    def path(self, relative: str) -> str:
        """A configured path, resolved against the project root."""
        return relative if os.path.isabs(relative) else os.path.join(ROOT, relative)


# --- parsing ---------------------------------------------------------------------


def parse_switch(value: str, name: str) -> bool:
    """`value` as a boolean switch, or ValueError naming `name`."""
    lowered = value.strip().lower()
    if lowered in _ON:
        return True
    if lowered in _OFF:
        return False
    raise ValueError(f"{name} must be on or off, got {value!r}")


def _hints(cls: type) -> dict[str, typing.Any]:
    return typing.get_type_hints(cls)


def is_table(kind: object) -> bool:
    """Whether a field's type is a nested table (a dataclass)."""
    return isinstance(kind, type) and dataclasses.is_dataclass(kind)


def parse_table(cls: type, table: Mapping[str, object], where: str) -> typing.Any:
    """An instance of the dataclass `cls` from a TOML table, every key required.

    Raises:
        ConfigError: a missing or unknown key, or a value of the wrong type.
    """
    hints = _hints(cls)
    unknown = sorted(set(table) - set(hints))
    if unknown:
        raise ConfigError(f"[{where}] has unknown key(s): {', '.join(unknown)}")
    values: dict[str, object] = {}
    for field in dataclasses.fields(typing.cast(typing.Any, cls)):
        key = f"{where}.{field.name}" if where else field.name
        if field.name not in table:
            raise ConfigError(f"missing setting {key}")
        values[field.name] = parse_value(
            hints[field.name], table[field.name], field, key
        )
    return cls(**values)


def parse_value(
    kind: object, value: object, field: dataclasses.Field, key: str
) -> object:
    """One setting's value, checked against its type and constraints."""
    if is_table(kind):
        if not isinstance(value, dict):
            raise ConfigError(f"[{key}] must be a table")
        return parse_table(typing.cast(type, kind), value, key)
    meta = field.metadata
    if kind is bool:
        if not isinstance(value, bool):
            raise ConfigError(f"{key} must be true or false")
        return value
    if kind is int or kind is float:
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ConfigError(f"{key} must be a number")
        if kind is int and not isinstance(value, int):
            raise ConfigError(f"{key} must be an integer")
        if value < meta["minimum"]:
            raise ConfigError(f"{key} must be >= {meta['minimum']:g}")
        return kind(value)
    if kind is str:
        if not isinstance(value, str) or not value:
            raise ConfigError(f"{key} must be a non-empty string")
        if meta["choices"] and value not in meta["choices"]:
            raise ConfigError(f"{key} must be one of {', '.join(meta['choices'])}")
        return value
    if typing.get_origin(kind) is tuple:
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ConfigError(f"{key} must be a list of strings")
        return tuple(value)
    raise ConfigError(f"{key}: unsupported setting type {kind!r}")


def merge(base: Mapping[str, object], over: Mapping[str, object]) -> dict[str, object]:
    """`base` with `over`'s keys replacing its own, table by table."""
    out = dict(base)
    for key, value in over.items():
        below = out.get(key)
        if isinstance(value, dict) and isinstance(below, dict):
            out[key] = merge(below, value)
        else:
            out[key] = value
    return out


def read_toml(path: str) -> dict[str, object]:
    """A TOML file's tables ({} when the file doesn't exist)."""
    if not os.path.isfile(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def parse_config(table: Mapping[str, object]) -> Config:
    """A Config from the merged tables of the configuration files."""
    config: Config = parse_table(Config, table, "")
    return config


def config() -> Config:
    """The project's Config: janken.toml, overridden by janken.local.toml.

    Raises:
        ConfigError: the files don't hold a complete, valid configuration.
    """
    return load_files(CONFIG_FILE, LOCAL_FILE)


@functools.cache
def load_files(path: str, local: str) -> Config:
    """The Config of the file `path`, overridden by the file `local` (if any)."""
    if not os.path.isfile(path):
        raise ConfigError(f"no configuration file at {path}")
    return parse_config(merge(read_toml(path), read_toml(local)))


def reload() -> Config:
    """Forget the cached configuration (after `config set`) and read it again."""
    load_files.cache_clear()
    return config()


# --- introspection (config show / get, option help) ------------------------------


@dataclasses.dataclass(frozen=True)
class Entry:
    """One setting: its dotted key, value, help text and allowed values."""

    key: str
    value: object
    help: str
    choices: tuple[str, ...]
    kind: object


def entries(node: object, prefix: str = "") -> Iterator[Entry]:
    """Every setting of `node` (a Config or one of its tables), in file order."""
    hints = _hints(type(node))
    for field in dataclasses.fields(typing.cast(typing.Any, node)):
        key = f"{prefix}{field.name}"
        value = getattr(node, field.name)
        if is_table(hints[field.name]):
            yield from entries(value, key + ".")
        else:
            yield Entry(
                key,
                value,
                field.metadata["help"],
                field.metadata["choices"],
                hints[field.name],
            )


def entry(key: str, current: Config) -> Entry:
    """The setting `key` (dotted).

    Raises:
        ConfigError: no such setting.
    """
    for found in entries(current):
        if found.key == key:
            return found
    raise ConfigError(f"no setting {key!r} (see `janken config show`)")


def help_for(key: str) -> str:
    """A setting's help text, for a command-line option that defaults to it."""
    return entry(key, config()).help


def parse_text(found: Entry, text: str) -> object:
    """A command-line string as a value for the setting `found`.

    Raises:
        ConfigError: the text isn't a value of the setting's type.
    """
    kind = found.kind
    try:
        if kind is bool:
            return parse_switch(text, found.key)
        if kind is int:
            return int(text)
        if kind is float:
            return float(text)
    except ValueError as exc:
        raise ConfigError(f"{found.key}: {exc}") from exc
    if typing.get_origin(kind) is tuple:
        return [part.strip() for part in text.split(",") if part.strip()]
    return text


# --- the process-wide switches -----------------------------------------------------


class CacheFlag(enum.Enum):
    """A command line's say on caching: follow the configuration, or force it."""

    AUTO = "auto"
    ON = "on"
    OFF = "off"


@dataclasses.dataclass(frozen=True)
class Settings:
    """What the decorators in janken/kit/jit.py do."""

    jit: bool
    cache: bool


def load(environ: Mapping[str, str]) -> Settings:
    """The settings in force: the configuration, overridden by the environment.

    Caching is off unless $JANKEN_NUMBA_CACHE turns it on (which `apply` does for the
    commands in `engine.cache_commands`); caching without the JIT means nothing.
    """
    jit = config().engine.jit
    if JIT_ENV in environ:
        jit = parse_switch(environ[JIT_ENV], JIT_ENV)
    cache = CACHE_ENV in environ and parse_switch(environ[CACHE_ENV], CACHE_ENV)
    return Settings(jit=jit, cache=jit and cache)


def progress_enabled(environ: Mapping[str, str], interactive: bool) -> bool:
    """Whether progress bars show: $JANKEN_PROGRESS, else the config; "auto" shows
    them only on an interactive terminal."""
    mode = environ.get(PROGRESS_ENV, config().output.progress).strip().lower()
    if mode not in PROGRESS_MODES:
        raise ValueError(
            f"{PROGRESS_ENV} must be one of {PROGRESS_MODES}, got {mode!r}"
        )
    return interactive if mode == "auto" else mode == "on"


def spans_enabled(environ: Mapping[str, str]) -> bool:
    """Whether timing spans are logged: $JANKEN_SPANS, else the config."""
    if SPANS_ENV in environ:
        return parse_switch(environ[SPANS_ENV], SPANS_ENV)
    return config().telemetry.spans


def wants_cache(command: str, flag: CacheFlag, environ: Mapping[str, str]) -> bool:
    """Whether `command` caches: the flag, else the environment, else the config."""
    if flag is not CacheFlag.AUTO:
        return flag is CacheFlag.ON
    if CACHE_ENV in environ:
        return parse_switch(environ[CACHE_ENV], CACHE_ENV)
    return command in config().engine.cache_commands


def apply(command: str, flag: CacheFlag, environ: MutableMapping[str, str]) -> Settings:
    """Settle caching for `command` (before anything is compiled) and return the
    settings in force."""
    environ[CACHE_ENV] = "1" if wants_cache(command, flag, environ) else "0"
    return load(environ)
