"""The flags every lab command shares, and the `Lab` they resolve into.

Every high-level command (and every low-level `lab` command) is declared with
`@lab_command(name)`: the decorator adds the common flags below to its signature, so
they are defined once, documented once, and named the same everywhere. Their defaults
come from janken.toml (janken/settings.py); none is written here.

    Workspace   --workspace --notebook --bots-dir --spaces-dir
    Evidence    --effort --rounds --round-robins --pool-size --seed --allow-small-pool
    Execution   --workers --cache --progress
    Output      --format --quiet

Precedence: an explicit flag, then the `--effort` budget, then the configuration.
"""

import dataclasses
import enum
import functools
import inspect
import json
import os
import sys
import typing
from collections.abc import Callable, Mapping
from typing import Annotated, Any, TypeVar

import typer

from .. import progress, settings, telemetry

CFG = settings.config()
F = TypeVar("F", bound=Callable[..., Any])


# The choices options take, as str enums so typer validates and lists them. Their
# values mirror the tuples in janken/settings.py (tests/test_cli.py checks they agree).


class Effort(enum.StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    THOROUGH = "thorough"


class Format(enum.StrEnum):
    TEXT = "text"
    JSON = "json"


class Progress(enum.StrEnum):
    AUTO = "auto"
    ON = "on"
    OFF = "off"


class Cache(enum.StrEnum):
    AUTO = "auto"
    ON = "on"
    OFF = "off"


class Sampler(enum.StrEnum):
    TPE = "tpe"
    GRID = "grid"
    RANDOM = "random"


class Mode(enum.StrEnum):
    FULL = "full"
    CANDIDATES = "candidates"


class Split(enum.StrEnum):
    TRAIN = "train"
    TEST = "test"
    ALL = "all"


class Metric(enum.StrEnum):
    ACCURACY = "accuracy"
    MACRO_F1 = "macro_f1"
    KAPPA = "kappa"
    EDGE = "edge"


class League(enum.StrEnum):
    NOVICE = "novice"
    CM = "cm"
    MASTER = "master"
    IM = "im"
    GM = "gm"
    ALL = "all"


class Db(enum.StrEnum):
    RUNS = "runs"
    DATASET = "dataset"


class Verdict(enum.StrEnum):
    KEEP = "keep"
    DROP = "drop"
    ITERATE = "iterate"


class Priority(enum.StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


ENUMS: dict[type[enum.StrEnum], tuple[str, ...]] = {
    Effort: settings.EFFORTS,
    Format: settings.FORMATS,
    Progress: settings.PROGRESS_MODES,
    Cache: tuple(f.value for f in settings.CacheFlag),
    Sampler: settings.SAMPLERS,
    Mode: settings.MODES,
    Split: settings.SPLITS,
    Metric: settings.METRICS,
    League: settings.LEAGUES,
}

# The configured choices, as the enum members typer options default to.
MODE = Mode(CFG.evaluation.mode)
SAMPLER = Sampler(CFG.tuning.sampler)
SPLIT = Split(CFG.dataset.split)
TUNE_SPLIT = Split(CFG.dataset.tune_split)
METRIC = Metric(CFG.dataset.metric)
LEAGUE = League(CFG.tournament.league)
FORMAT = Format(CFG.output.format)


def about(key: str, extra: str = "") -> str:
    """An option's help: the setting's own help, and where its default lives."""
    text = settings.help_for(key)
    return f"{text}{extra} (config: {key})"


def budget_help(text: str, field: str) -> str:
    """An effort-budgeted option's help: the default comes from the --effort budget."""
    return (
        f"{text}; default: the --effort budget"
        f" (config: effort.{CFG.effort.default}.{field})"
    )


def _default_budget() -> settings.Budget:
    return CFG.effort.budget(CFG.effort.default)


WORKSPACE, EVIDENCE, EXECUTION, OUTPUT = "Workspace", "Evidence", "Execution", "Output"

# (name, annotation, default): the common flags, in the order --help lists them.
COMMON: tuple[tuple[str, Any, Any], ...] = (
    (
        "workspace",
        Annotated[
            str, typer.Option(help=about("workspace.dir"), rich_help_panel=WORKSPACE)
        ],
        CFG.workspace.dir,
    ),
    (
        "notebook",
        Annotated[
            str,
            typer.Option(help=about("workspace.notebook"), rich_help_panel=WORKSPACE),
        ],
        CFG.workspace.notebook,
    ),
    (
        "bots_dir",
        Annotated[
            str,
            typer.Option(help=about("workspace.bots_dir"), rich_help_panel=WORKSPACE),
        ],
        CFG.workspace.bots_dir,
    ),
    (
        "spaces_dir",
        Annotated[
            str,
            typer.Option(help=about("workspace.spaces_dir"), rich_help_panel=WORKSPACE),
        ],
        CFG.workspace.spaces_dir,
    ),
    (
        "effort",
        Annotated[
            Effort,
            typer.Option(
                help=about("effort.default", "; flags below override its budget"),
                rich_help_panel=EVIDENCE,
            ),
        ],
        CFG.effort.default,
    ),
    (
        "rounds",
        Annotated[
            int, typer.Option(help=about("match.rounds"), rich_help_panel=EVIDENCE)
        ],
        CFG.match.rounds,
    ),
    (
        "round_robins",
        Annotated[
            int,
            typer.Option(
                help="pools played (tuning: per trial); default: the effort's budget"
                f" (config: effort.{CFG.effort.default}.round_robins)",
                rich_help_panel=EVIDENCE,
            ),
        ],
        _default_budget().round_robins,
    ),
    (
        "pool_size",
        Annotated[int, typer.Option(help=about("pool.size"), rich_help_panel=EVIDENCE)],
        CFG.pool.size,
    ),
    (
        "seed",
        Annotated[
            int,
            typer.Option(
                help=about("evaluation.seed", "; tuning uses tuning.seed"),
                rich_help_panel=EVIDENCE,
            ),
        ],
        CFG.evaluation.seed,
    ),
    (
        "allow_small_pool",
        Annotated[
            bool, typer.Option(help=about("pool.allow_small"), rich_help_panel=EVIDENCE)
        ],
        CFG.pool.allow_small,
    ),
    (
        "mocks",
        Annotated[
            bool, typer.Option(help=about("pool.mocks"), rich_help_panel=EVIDENCE)
        ],
        CFG.pool.mocks,
    ),
    (
        "workers",
        Annotated[
            int,
            typer.Option(help=about("execution.workers"), rich_help_panel=EXECUTION),
        ],
        CFG.execution.workers,
    ),
    (
        "cache",
        Annotated[
            Cache,
            typer.Option(
                help="keep numba's compiled code on disk: auto (per"
                " engine.cache_commands), on or off",
                rich_help_panel=EXECUTION,
            ),
        ],
        settings.CacheFlag.AUTO.value,
    ),
    (
        "progress",
        Annotated[
            Progress,
            typer.Option(help=about("output.progress"), rich_help_panel=EXECUTION),
        ],
        CFG.output.progress,
    ),
    (
        "format",
        Annotated[
            Format, typer.Option(help=about("output.format"), rich_help_panel=OUTPUT)
        ],
        CFG.output.format,
    ),
    (
        "quiet",
        Annotated[
            bool, typer.Option(help=about("output.quiet"), rich_help_panel=OUTPUT)
        ],
        CFG.output.quiet,
    ),
)
COMMON_NAMES = tuple(name for name, _, _ in COMMON)


@dataclasses.dataclass(frozen=True)
class Lab:
    """A command's common flags, resolved."""

    command: str
    workspace: str  # absolute paths from here on
    notebook: str
    bots_dir: str
    spaces_dir: str
    effort: str
    budget: settings.Budget
    rounds: int
    pool_size: int
    allow_small: bool
    use_mocks: bool
    workers: int
    format: str
    quiet: bool
    raw: Mapping[str, Any]  # every common flag's value as given
    passed: frozenset[str]  # every flag given explicitly (common or the command's)

    def pick(self, name: str, value: object, budget_field: str) -> Any:
        """An evidence value: the flag if given, else the effort's budget."""
        return value if name in self.passed else getattr(self.budget, budget_field)

    def given(self, name: str, fallback: object) -> Any:
        """A common flag's value if given explicitly, else `fallback`."""
        return self.raw[name] if name in self.passed else fallback

    @property
    def round_robins(self) -> int:
        return self.pick("round_robins", self.raw["round_robins"], "round_robins")

    @property
    def seed(self) -> int:
        return int(self.raw["seed"])

    def say(self, text: str) -> None:
        """Print a human-readable line (not with --quiet or --format json)."""
        if not self.quiet and self.format != "json":
            print(text, flush=True)  # progress shows when piped to a file

    def emit(self, data: object, text: str) -> None:
        """Print a result: `data` as JSON with --format json, else `text`."""
        if self.format == "json":
            print(json.dumps(data, indent=2, default=str))
        elif not self.quiet:
            print(text)


def shown(path: str) -> str:
    """A path for messages: relative inside the project, absolute outside it."""
    relative = os.path.relpath(path)
    return path if relative.startswith("..") else relative


def make_lab(command: str, raw: Mapping[str, Any], passed: frozenset[str]) -> Lab:
    """Resolve the common flags, and settle caching and progress for the process."""
    settings.apply(command, settings.CacheFlag(str(raw["cache"])), os.environ)
    os.environ[settings.PROGRESS_ENV] = str(raw["progress"])
    effort = str(raw["effort"])
    workspace = CFG.path(raw["workspace"])
    telemetry.configure(workspace, command)
    return Lab(
        command=command,
        workspace=workspace,
        notebook=CFG.path(raw["notebook"]),
        bots_dir=os.path.relpath(CFG.path(raw["bots_dir"])),
        spaces_dir=CFG.path(raw["spaces_dir"]),
        effort=effort,
        budget=CFG.effort.budget(effort),
        rounds=int(raw["rounds"]),
        pool_size=int(raw["pool_size"]),
        allow_small=bool(raw["allow_small_pool"]),
        use_mocks=bool(raw["mocks"]),
        workers=int(raw["workers"]),
        format=str(raw["format"]),
        quiet=bool(raw["quiet"]),
        raw=dict(raw),
        passed=passed,
    )


def _domain_errors() -> tuple[type[Exception], ...]:
    """The errors a command reports as a message rather than a traceback."""
    from ..botfile import BotFileError
    from ..lab.space import SpaceError
    from ..lab.workflows import WorkflowError
    from ..notebook.ideas import IdeaError
    from ..notebook.insights import InsightError
    from ..notebook.notes import NoteError

    return (
        WorkflowError,
        NoteError,
        IdeaError,
        InsightError,
        settings.ConfigError,
        SpaceError,
        BotFileError,
    )


def bot_path(lab: Lab, name: str) -> str:
    """A bot by path, or by stem (found in the bots dir's level folders, else
    anywhere in its library: blocks/, inactive/).

    Raises:
        typer.Exit: no bot, or more than one, has that stem.
    """
    if name.endswith(".yaml") or os.sep in name:
        return name
    from .. import library
    from ..engine import registry

    try:
        return registry.find(lab.bots_dir, name)
    except FileNotFoundError as error:
        found = library.Library(lab.bots_dir).paths(name)
        if len(found) == 1:
            return found[0]
        raise fail(str(error)) from error


def fail(message: str) -> typer.Exit:
    """Print `message` as an error; raise what this returns to stop with status 2."""
    print(f"error: {message}", file=sys.stderr)
    return typer.Exit(2)


def lab_command(command: str) -> Callable[[F], F]:
    """Declare a lab command: add the common flags to `fn`'s own, and call it with a
    `Lab` (its first parameter, `lab`) built from them.

    `command` names it for `engine.cache_commands` ("evaluate", "lab experiment", ...).
    """

    def wrap(fn: F) -> F:
        own = [
            p for name, p in inspect.signature(fn).parameters.items() if name != "lab"
        ]
        context = inspect.Parameter(
            "ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=typer.Context
        )
        common = [
            inspect.Parameter(
                name, inspect.Parameter.KEYWORD_ONLY, default=default, annotation=kind
            )
            for name, kind, default in COMMON
        ]

        @functools.wraps(fn)
        def wrapper(ctx: typer.Context, **kwargs: Any) -> Any:
            raw = {name: kwargs.pop(name) for name in COMMON_NAMES}
            passed = frozenset(
                name
                for name in ctx.params
                if (source := ctx.get_parameter_source(name)) is not None
                and source.name not in ("DEFAULT", "DEFAULT_MAP")
            )
            lab = make_lab(command, raw, passed)
            try:
                with telemetry.span("command", effort=lab.effort):
                    return fn(lab, **kwargs)
            except _domain_errors() as exc:
                raise fail(str(exc)) from None
            except (KeyboardInterrupt, SystemError) as exc:
                if not progress.interrupted(exc):
                    raise
                raise typer.Exit(130) from None  # what was finished is stored

        signature = inspect.Signature([context, *own, *common])
        wrapper.__dict__["__signature__"] = signature  # what inspect.signature reads
        wrapper.__annotations__ = {
            p.name: p.annotation for p in signature.parameters.values()
        }
        del wrapper.__wrapped__  # typer must read the new signature, not fn's
        return typing.cast(F, wrapper)

    return wrap
