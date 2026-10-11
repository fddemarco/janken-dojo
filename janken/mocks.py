"""Oracles: research-only stand-ins for bots of any level, and the rules around them.

An Oracle (janken/kit/blueprint/) wins with a set chance vs each opponent level
(janken/kit/levels.py); the referee reveals the opponent's move and level to it.
A bot holding one is level ORACLE, and is of one of two kinds:

    PURE  the blueprint is only an Oracle: the referee never runs its pipeline, it
          plays the drawn outcome. A cheap stand-in for an expensive opponent; its
          file names the bot it stands in for (`mocks: <stem>`), and its win chances
          come from `janken lab calibrate <stem>`.
    ARM   an Oracle among other signals: a research candidate whose expensive
          expert is mocked (e.g. a gatekeeper's anti expert).

Pools draw the PURE Oracles in place of the bots they mock with `pool.mocks`,
otherwise no Oracle; never an ARM. Oracles draw each other by default (their
knobs vs the ORACLE level; two ARMs, which can't be told each other's move, both
play PAPER). They never enter a tournament or an export.
"""

from collections.abc import Sequence

from . import botfile
from .kit import blueprint as bp
from .kit import codes as c
from .kit import declare, levels
from .match import bot_name


def kind(blueprint: bp.Blueprint) -> int:
    """ORACLE_NONE, ORACLE_PURE (only an Oracle) or ORACLE_ARM."""
    if not levels.has_oracle(blueprint):
        return c.ORACLE_NONE
    core = blueprint.core
    alone = (
        isinstance(core, bp.Bandit)
        and len(core.predictors) == 1
        and not blueprint.guards
        and not blueprint.overlays
    )
    return c.ORACLE_PURE if alone else c.ORACLE_ARM


def oracle_cell(compiled: bp.Compiled) -> int:
    """The i offset of the compiled bot's Oracle state, or -1."""
    spec = compiled.spec
    core = int(spec[c.H_CORE])
    first = int(spec[core + c.E_SIG_AT])
    for s in range(int(spec[core + c.E_NSIG])):
        r = first + s * c.REC
        if spec[r + c.R_KIND] == c.S_ORACLE:
            return int(spec[r + c.R_I])
    return -1


def read_blueprint(path: str) -> bp.Blueprint:
    """A bot file's blueprint (a kernel module has an empty one)."""
    return declare.blueprint_from_data(botfile.read(path).blueprint)


def path_level(path: str) -> int:
    """The level of the bot at `path` (janken/kit/levels.py; a kernel module: 1)."""
    if botfile.is_kernel_module(path):
        return 1
    return levels.level(read_blueprint(path))


def path_kind(path: str) -> int:
    """The kind of the bot at `path` (an unreadable file is not an Oracle: loading
    it reports its error)."""
    try:
        return kind(read_blueprint(path))
    except (botfile.BotFileError, bp.BlueprintError):
        return c.ORACLE_NONE


def is_mock(path: str) -> bool:
    return path_kind(path) != c.ORACLE_NONE


def pool_excluded(paths: Sequence[str], use_mocks: bool) -> set[str]:
    """The stems a pool never draws: every ARM; the bots the PURE Oracles mock
    (`use_mocks`), else every Oracle."""
    kinds = {bot_name(p): path_kind(p) for p in paths}
    if not use_mocks:
        return {s for s, k in kinds.items() if k != c.ORACLE_NONE}
    arms = {s for s, k in kinds.items() if k == c.ORACLE_ARM}
    mocked = {
        botfile.read(p).mocks for p in paths if kinds[bot_name(p)] == c.ORACLE_PURE
    }
    return arms | (mocked - {""})
