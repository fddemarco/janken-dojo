"""Hyperparameter tuning of one or more bots' spaces with Optuna.

Design (see research/README.md, "Tuning"):

* Spaces: one space file per tuned bot (janken/lab/space.py). Several bots are
  tuned together in one study (a fleet: a champion and its supports), each trial
  choosing every bot's parameters at once. Optuna names a parameter
  `<stem>.<NAME>`.
* Objective: each tuned bot's match score, (W + ½D) / N, over its matches against
  the pool and against the other tuned bots, combined as a weighted mean with the
  space files' weights. A fleet's supports take weight 0: they are tuned only for
  what they do to the champion.
* Common random numbers: every trial plays the *same* pools with the *same*
  match seeds (fixed by --seed), so trials differ only by their parameters.
  Noise is still there, but it is shared, so the ranking of trials is far
  sharper than independent draws would give.
* Cheap schedule: tuned bots vs pool and each other only (pool-vs-pool can't
  move their ratings; every bot enters fresh).
* Sampler: TPE (multivariate, grouped, constant liar for parallel workers);
  `grid` uses the params' "grid" lists; `random` is the honest baseline.
* MedianPruner: after each round robin a trial reports its running objective; a
  trial clearly below the median at the same step is stopped early.
* Storage: SQLite under experiments/tuning/, so a study resumes where it
  stopped, and several `tune` processes on the same --study share the work.
* Overfitting check: --validate-top K replays the K best configurations (plus
  the defaults) as normal full experiments on fresh seeds and pools. Each
  configuration's result (the champion's score vs the pool, and its paired
  difference from the defaults) is recorded in the runs database's
  `tune_validations` table, and the study lists its validation runs.
* Progress: a bar over the session's trials; trials.parquet is re-exported every
  `[tool.janken.tuning] export_every` trials.
"""

import dataclasses
import datetime
import json
import math
import os
import random
import sys
import time
from collections.abc import Callable, Mapping, Sequence

import optuna
import polars as pl
import tqdm

from .. import botfile, progress, settings
from ..engine import play_pairs
from ..match import MatchResult
from ..spec import BotSpec, format_spec, make_spec
from . import analyze, store
from .experiment import build_schedule, run_experiment
from .runs_db import RunStore
from .space import Number, Param, Space, check_unique_stems

SAMPLERS = ("tpe", "grid", "random")
SEP = "."  # between a bot's stem and its parameter in Optuna's names

Params = dict[str, dict[str, Number]]  # stem -> {NAME: value}


@dataclasses.dataclass(frozen=True)
class Setup:
    """How every trial of a study is played."""

    rounds: int
    round_robins: int
    pool_size: int
    seed: int
    bots_dir: str
    workers: int = 0  # 0: numba's default
    allow_small: bool = False
    use_mocks: bool = False  # pools draw the mocks (janken/mocks.py)
    root: str = ""  # "": the default experiments directory


@dataclasses.dataclass(frozen=True)
class Search:
    """How a session explores: sampler, budget, pruning, validation."""

    sampler: str = "tpe"
    sampler_seed: int = -1  # -1: unseeded (parallel workers)
    trials: int = -1  # -1: not given (grid: the whole grid; else until the timeout)
    timeout: float = 0.0  # 0: none
    prune: bool = True
    validate_top: int = 0
    validate_round_robins: int = dataclasses.field(
        default_factory=lambda: settings.config().effort.standard.validate_round_robins
    )


@dataclasses.dataclass
class Tally:
    """One bot's matches in a trial."""

    n: int = 0
    w: int = 0
    d: int = 0
    l: int = 0
    diff: int = 0

    def add(self, mine: int, theirs: int, outcome: float) -> None:
        self.n += 1
        self.diff += mine - theirs
        self.w += outcome == 1.0
        self.d += outcome == 0.5
        self.l += outcome == 0.0

    @property
    def score(self) -> float:
        return (self.w + 0.5 * self.d) / self.n if self.n else 0.0

    def attrs(self) -> dict[str, float]:
        return {
            "n": self.n,
            "W": self.w,
            "D": self.d,
            "L": self.l,
            "diff": self.diff / max(self.n, 1),
            "score": self.score,
        }


def param_key(stem: str, name: str) -> str:
    return f"{stem}{SEP}{name}"


def split_params(flat: Mapping[str, object], spaces: Sequence[Space]) -> Params:
    """Optuna's `{stem.NAME: value}` as `{stem: {NAME: value}}`, for every space."""
    out: Params = {s.stem: {} for s in spaces}
    for key, value in flat.items():
        stem, _, name = key.partition(SEP)
        if isinstance(value, int | float) and stem in out:
            out[stem][name] = value
    return out


def suggest(trial: optuna.Trial, spaces: Sequence[Space]) -> Params:
    return {
        s.stem: {
            name: suggest_param(trial, param_key(s.stem, name), p)
            for name, p in s.params.items()
        }
        for s in spaces
    }


def suggest_param(trial: optuna.Trial, key: str, p: Param) -> Number:
    if p.type == "float":
        return trial.suggest_float(
            key, p.low, p.high, log=p.log, step=p.step if p.step else None
        )
    if p.type == "int":
        return trial.suggest_int(
            key, int(p.low), int(p.high), step=int(p.step or 1), log=p.log
        )
    choice = trial.suggest_categorical(key, list(p.choices))
    if not isinstance(choice, int | float):
        raise TypeError(f"{key}: categorical choice {choice!r} is not a number")
    return choice


def grid_space(spaces: Sequence[Space]) -> dict[str, list[Number]]:
    """{stem.NAME: [values]} for GridSampler, across every space."""
    grid: dict[str, list[Number]] = {}
    for s in spaces:
        for name, p in s.params.items():
            values = p.grid_values()
            if not values:
                raise SystemExit(
                    f"{s.stem}: param {name!r} has no 'grid' list; add one for"
                    " --sampler grid"
                )
            grid[param_key(s.stem, name)] = list(values)
    return grid


def baseline(spaces: Sequence[Space]) -> dict[str, Number]:
    """Every tuned bot at its defaults, as one trial's parameters."""
    return {
        param_key(s.stem, name): value
        for s in spaces
        for name, value in s.defaults().items()
    }


def make_sampler(
    kind: str, spaces: Sequence[Space], sampler_seed: int
) -> optuna.samplers.BaseSampler:
    seed = sampler_seed if sampler_seed >= 0 else None
    if kind == "grid":
        return optuna.samplers.GridSampler(grid_space(spaces), seed=seed)
    if kind == "random":
        return optuna.samplers.RandomSampler(seed=seed)
    n_params = sum(len(s.params) for s in spaces)
    return optuna.samplers.TPESampler(
        seed=seed,
        multivariate=True,
        group=True,
        constant_liar=True,
        n_startup_trials=max(10, 3 * n_params),
    )


def _pct(x: float) -> str:
    return "%.1f%%" % (100 * x)


def objective_value(tallies: Mapping[str, Tally], spaces: Sequence[Space]) -> float:
    """The weighted mean of the tuned bots' scores."""
    total = sum(s.weight for s in spaces)
    return sum(s.weight * tallies[s.stem].score for s in spaces) / total


def tally_match(
    tallies: dict[str, Tally], a: BotSpec, b: BotSpec, m: MatchResult
) -> None:
    """Credit a match to whichever of its bots are tuned."""
    if m.winner is None:
        outcome_a = 0.5
    else:
        outcome_a = 1.0 if m.winner == m.bot_a else 0.0
    if a.stem in tallies:
        tallies[a.stem].add(m.wins_a, m.wins_b, outcome_a)
    if b.stem in tallies:
        tallies[b.stem].add(m.wins_b, m.wins_a, 1.0 - outcome_a)


def specs_for(spaces: Sequence[Space], params: Params) -> list[BotSpec]:
    return [make_spec(s.bot, params.get(s.stem, {})) for s in spaces]


def study_config(spaces: Sequence[Space], setup: Setup) -> dict[str, object]:
    return {
        "spaces": [s.to_data() for s in spaces],
        "rounds": setup.rounds,
        "round_robins": setup.round_robins,
        "pool_size": setup.pool_size,
        "seed": setup.seed,
        "bots_dir": setup.bots_dir,
    }


def _open_study(
    spaces: Sequence[Space], setup: Setup, search: Search, study_name: str
) -> optuna.Study:
    """Create or resume the study, refusing to resume under a different setup."""
    tdir = store.tuning_dir(setup.root or None)
    os.makedirs(tdir, exist_ok=True)
    storage = "sqlite:///{}".format(os.path.join(tdir, f"{study_name}.db"))
    study = optuna.create_study(
        study_name=study_name,
        storage=storage,
        direction="maximize",
        load_if_exists=True,
        sampler=make_sampler(search.sampler, spaces, search.sampler_seed),
        pruner=(
            optuna.pruners.MedianPruner(
                n_startup_trials=8, n_warmup_steps=max(1, setup.round_robins // 3)
            )
            if search.prune and setup.round_robins >= 3
            else optuna.pruners.NopPruner()
        ),
    )
    config = study_config(spaces, setup)
    hashes = {s.stem: botfile.source_hash(s.bot) for s in spaces}
    stored = study.user_attrs.get("config")
    if stored is None:
        study.set_user_attr("config", config)
        study.set_user_attr("bot_sha256", hashes)
        if search.sampler != "grid":
            study.enqueue_trial(baseline(spaces))  # the baseline first
    elif stored != json.loads(json.dumps(config)):
        raise SystemExit(
            f"study {study_name!r} was created with a different setup:\n"
            f"  stored  {json.dumps(stored)}\n  now     {json.dumps(config)}\n"
            "use a new --study name"
        )
    elif study.user_attrs.get("bot_sha256") != hashes:
        print(
            f"warning: a tuned bot changed since study {study_name!r} started; old"
            " trials scored the previous code",
            file=sys.stderr,
        )
    return study


def run_tune(
    spaces: Sequence[Space],
    study_name: str,
    setup: Setup,
    search: Search,
) -> optuna.Study:
    """Tune `spaces` (one per bot) together in the study `study_name`."""
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    check_unique_stems(spaces)
    if not spaces or not any(s.params for s in spaces):
        raise SystemExit("the space files declare no params; nothing to tune")
    if sum(s.weight for s in spaces) <= 0:
        raise SystemExit("every space has weight 0: give at least one bot a weight")
    study = _open_study(spaces, setup, search, study_name)
    bases = [make_spec(s.bot) for s in spaces]
    schedule = build_schedule(
        bases,
        setup.bots_dir,
        setup.pool_size,
        setup.round_robins,
        setup.seed,
        mode="candidates",
        allow_small=setup.allow_small,
        use_mocks=setup.use_mocks,
    )
    labels = ", ".join(b.label for b in bases)
    print(
        f"tuning {labels}: {sum(len(s.params) for s in spaces)} params,"
        f" {search.sampler} sampler, {setup.round_robins} round robin(s) x"
        f" {len(schedule[0]['pool'])} pool bots x {setup.rounds} rounds per trial;"
        f" study {study_name}",
        file=sys.stderr,
    )

    def objective(trial: optuna.Trial) -> float:
        params = suggest(trial, spaces)
        tuned = {s.stem: spec for s, spec in zip(spaces, specs_for(spaces, params))}
        tallies = {s.stem: Tally() for s in spaces}
        for step, rr in enumerate(schedule):
            pairs = [
                (tuned.get(a.stem, a), tuned.get(b.stem, b)) for a, b in rr["pairs"]
            ]
            results = play_pairs(
                pairs, setup.rounds, rr["seeds"], setup.workers or None
            )
            for (a, b), m in zip(pairs, results):
                tally_match(tallies, a, b, m)
            trial.report(objective_value(tallies, spaces), step)
            if trial.should_prune():
                raise optuna.TrialPruned()
        trial.set_user_attr(
            "bots",
            {
                stem: {"label": tuned[stem].label, **t.attrs()}
                for stem, t in tallies.items()
            },
        )
        return objective_value(tallies, spaces)

    n_trials = search.trials if search.trials >= 0 else None
    if search.sampler == "grid" and n_trials is None:
        n_trials = math.prod(len(v) for v in grid_space(spaces).values())
    tdir = store.tuning_dir(setup.root or None)
    export = os.path.join(tdir, study_name, "trials.parquet")
    started = time.perf_counter()
    with progress.bar(n_trials or 0, "trials", "trial") as bar:
        callback = TrialProgress(
            bar,
            _pct,
            lambda s: export_trials(s, export),
            settings.config().tuning.export_every,
        )
        try:
            study.optimize(
                objective,
                n_trials=n_trials,
                timeout=search.timeout or None,
                callbacks=[callback],
                gc_after_trial=False,
            )
        except (KeyboardInterrupt, SystemError) as exc:
            if not progress.interrupted(exc):
                raise
            progress.log("interrupted; the study keeps every finished trial")
    export_trials(study, export)
    print(
        f"\n{len(study.trials)} trials in {time.perf_counter() - started:.0f}s this"
        f" session; all trials -> {os.path.relpath(export)}"
    )
    report(study, spaces, 10)
    if search.validate_top:
        validate(study, spaces, setup, search, study_name)
    return study


def _no_export(study: optuna.Study) -> None:
    """A study that keeps no trials table."""


class TrialProgress:
    """An Optuna callback: one bar step and one log line per finished trial, and
    the trials table re-exported every `export_every` trials."""

    def __init__(
        self,
        bar: tqdm.tqdm,
        show: Callable[[float], str],
        export: Callable[[optuna.Study], None] = _no_export,
        export_every: int = 1,
    ) -> None:
        self.bar: tqdm.tqdm = bar
        self.show: Callable[[float], str] = show
        self.export: Callable[[optuna.Study], None] = export
        self.export_every: int = export_every
        self.finished: int = 0
        self.pruned: int = 0

    def __call__(self, study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
        self.finished += 1
        done = [t for t in study.trials if t.value is not None]
        best = study.best_trial if done else None
        best_text = self.show(best.value) if best and best.value is not None else "—"
        if trial.state == optuna.trial.TrialState.PRUNED:
            self.pruned += 1
            state = "pruned"
        elif trial.value is not None:
            state = self.show(trial.value)
        else:
            state = trial.state.name.lower()
        progress.log(
            f"trial {trial.number:4d}  {state:<8s} best {best_text} (#{best.number if best else -1:d})  {params_text(trial.params)}"
        )
        self.bar.set_postfix(best=best_text, pruned=self.pruned)
        self.bar.update(1)
        if self.finished % self.export_every == 0:
            self.export(study)


def export_trials(study: optuna.Study, path: str) -> None:
    rows = [
        {
            "number": t.number,
            "state": t.state.name,
            "value": t.value,
            "params": json.dumps(t.params, sort_keys=True),
            "bots": json.dumps(t.user_attrs.get("bots", {}), sort_keys=True),
            "steps": len(t.intermediate_values),
            "seconds": t.duration.total_seconds() if t.duration else None,
        }
        for t in study.trials
    ]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pl.DataFrame(rows, infer_schema_length=None).write_parquet(path)


def top_trials(study: optuna.Study, k: int) -> list[optuna.trial.FrozenTrial]:
    done = [
        t
        for t in study.trials
        if t.state == optuna.trial.TrialState.COMPLETE and t.value is not None
    ]
    return sorted(done, key=lambda t: t.value or 0.0, reverse=True)[:k]


def _fmt(v: object) -> str:
    return f"{v:.4g}" if isinstance(v, float) else str(v)


def params_text(params: Mapping[str, object]) -> str:
    return " ".join(f"{k}={_fmt(v)}" for k, v in params.items())


def report(study: optuna.Study, spaces: Sequence[Space], k: int = 10) -> None:
    best = top_trials(study, k)
    if not best:
        print("no completed trials yet")
        return
    rows = [[t.number, _pct(t.value or 0.0), params_text(t.params)] for t in best]
    print(analyze._md_table(["trial", "objective", "params"], rows))
    specs = specs_for(spaces, split_params(best[0].params, spaces))
    command = " ".join(json.dumps(format_spec(s)) for s in specs)
    print(
        f"\nbest: {', '.join(s.label for s in specs)}\n"
        f"  uv run janken evaluate {command} --hypothesis ..."
    )


def champion_index(spaces: Sequence[Space]) -> int:
    """The bot a validation judges: the heaviest-weighted (the first among ties)."""
    return max(range(len(spaces)), key=lambda i: (spaces[i].weight, -i))


@dataclasses.dataclass(frozen=True)
class ValidationConfig:
    """A configuration to validate: where it came from, and its bots."""

    trial: int  # -1: the defaults
    train_value: float  # nan: the defaults never ran as a trial
    specs: list[BotSpec]

    @property
    def key(self) -> str:
        return "+".join(s.label for s in self.specs)


def validation_configs(
    study: optuna.Study, spaces: Sequence[Space], k: int
) -> list[ValidationConfig]:
    """The defaults, then the `k` best other trials, without repeats."""
    base = baseline(spaces)
    trained = [
        t
        for t in study.trials
        if t.params == base and t.state == optuna.trial.TrialState.COMPLETE
    ]
    value = trained[0].value if trained else None  # Optuna's: None when unscored
    configs = [
        ValidationConfig(
            -1, value if value is not None else math.nan, specs_for(spaces, {})
        )
    ]
    configs += [
        ValidationConfig(
            t.number, t.value or 0.0, specs_for(spaces, split_params(t.params, spaces))
        )
        for t in top_trials(study, k + len(trained))
        if t.params != base  # the baseline trial is the defaults, row -1
    ][:k]
    unique: dict[str, ValidationConfig] = {}
    for c in configs:
        unique.setdefault(c.key, c)
    return list(unique.values())


def validate(
    study: optuna.Study,
    spaces: Sequence[Space],
    setup: Setup,
    search: Search,
    study_name: str,
) -> list[str]:
    """Replay the defaults and the best trials on fresh pools and seeds, record
    every configuration's result, and return the validation run ids.

    One bot: a single run with every configuration as a candidate (paired
    comparisons). Several bots: one run per configuration, all on the same seed,
    so one trial's fleet never meets another's and every run sees the same pools.
    """
    configs = validation_configs(study, spaces, search.validate_top)
    trials = {c.key: {"number": c.trial, "value": c.train_value} for c in configs[1:]}
    fresh = random.Random(f"validate:{study_name}:{setup.seed}").getrandbits(32)
    print(
        f"\nvalidating defaults + top {len(configs) - 1} on fresh pools"
        f" (seed {fresh})..."
    )
    if len(spaces) == 1:
        plan = [("validate-" + study_name, configs)]
    else:
        plan = [(f"validate-{study_name}-{k}", [c]) for k, c in enumerate(configs)]
    played: dict[str, str] = {}  # config key -> its run id
    for name, group in plan:
        run_id = run_experiment(
            [c.specs[0] for c in group] if len(spaces) == 1 else group[0].specs,
            bots_dir=setup.bots_dir,
            pool_size=setup.pool_size,
            rounds=setup.rounds,
            round_robins=search.validate_round_robins,
            seed=fresh,
            mode="full",
            name=name,
            workers=setup.workers or None,
            allow_small=setup.allow_small,
            use_mocks=setup.use_mocks,
            root=setup.root or None,
            extra={"tuning": {"study": study_name, "trials": trials}},
        )
        print(analyze.render(analyze.analyze_run(run_id, setup.root or None)))
        played.update({c.key: run_id for c in group})
    rows = validation_rows(configs, played, champion_index(spaces), study_name, setup)
    RunStore.at(setup.root).add_validations(
        "tune_validations", [dataclasses.asdict(r) for r in rows]
    )
    history = list(study.user_attrs.get("validations", []))
    history.append(
        {
            "at": datetime.datetime.now().isoformat(timespec="seconds"),
            "runs": sorted(set(played.values())),
        }
    )
    study.set_user_attr("validations", history)
    print("\n## Validation (recorded in tune_validations)\n")
    print(
        analyze._md_table(
            [
                "config",
                "trial",
                "train",
                "score vs pool [95% CI]",
                "vs defaults [95% CI]",
            ],
            [
                [
                    r.champion,
                    r.trial,
                    "—" if math.isnan(r.train_value) else _pct(r.train_value),
                    f"{_pct(r.score)} [{_pct(r.ci_lo)}, {_pct(r.ci_hi)}]",
                    f"{100 * r.vs_defaults:+.1f} pts [{100 * r.vs_defaults_lo:+.1f}, {100 * r.vs_defaults_hi:+.1f}]",
                ]
                for r in rows
            ],
        )
    )
    return sorted(set(played.values()))


@dataclasses.dataclass(frozen=True)
class TuneValidation:
    """One `tune_validations` row: a configuration's champion on fresh pools."""

    study: str
    run_id: str
    config: str  # the configuration's labels, +-joined
    champion: str  # the champion's label
    trial: int  # -1: the defaults
    train_value: float  # nan: the defaults never ran as a trial
    n: int  # matches vs the pool
    score: float
    ci_lo: float
    ci_hi: float
    vs_defaults: float  # paired score difference from the defaults' champion
    vs_defaults_lo: float
    vs_defaults_hi: float
    params: str  # JSON: {stem: {NAME: value}}


def validation_rows(
    configs: Sequence[ValidationConfig],
    played: Mapping[str, str],
    champion: int,
    study_name: str,
    setup: Setup,
) -> list[TuneValidation]:
    """One tune_validations row per configuration: its champion's score vs the
    pool, and the paired difference from the defaults' champion (same pools and
    seeds, so paired even across a fleet's separate runs)."""
    runs = RunStore.at(setup.root)
    long = {
        run_id: analyze.long_form(runs.matches(run_id))
        for run_id in set(played.values())
    }

    def side(config: ValidationConfig, as_label: str) -> pl.DataFrame:
        lf = long[played[config.key]]
        mine = lf.filter(pl.col("bot") == config.specs[champion].label)
        return mine.with_columns(pl.lit(as_label).alias("bot"))

    defaults = configs[0]
    rows = []
    for c in configs:
        lf = long[played[c.key]]
        label = c.specs[champion].label
        vs_pool = lf.filter(
            (pl.col("bot") == label) & pl.col("is_cand") & ~pl.col("opp_cand")
        )
        n = vs_pool.height
        score = float(vs_pool["result"].to_numpy().mean()) if n else math.nan
        lo, hi = analyze.wilson(score, n)
        cmp = analyze.paired_diff(
            pl.concat([side(c, "config"), side(defaults, "defaults")]),
            "config",
            "defaults",
        )
        rows.append(
            TuneValidation(
                study=study_name,
                run_id=played[c.key],
                config=c.key,
                champion=label,
                trial=c.trial,
                train_value=float(c.train_value),
                n=n,
                score=score,
                ci_lo=lo,
                ci_hi=hi,
                vs_defaults=cmp["mean"] if cmp else math.nan,
                vs_defaults_lo=cmp["ci_lo"] if cmp else math.nan,
                vs_defaults_hi=cmp["ci_hi"] if cmp else math.nan,
                params=json.dumps({s.stem: s.params for s in c.specs}, sort_keys=True),
            )
        )
    return rows
