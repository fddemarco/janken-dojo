"""Bot levels: how many layers of meta-reasoning a blueprint stacks.

    L1      a heuristic: signals played without a bandit (copycat, an n-gram, rock)
    L2      a bandit over L1 arms (smartbot, iocaine, a scoreboard of rotations)
    L3      a bandit whose arms include an L2 (a replay of smartbot: smartbot_sims)
    L4 ...  one more layer per composite over predictors of the level below
    ORACLE  a bot holding an Oracle (research only: janken/mocks.py)

The level is the core predictor tree's (janken/kit/blueprint/predictor.py), never
written down: a signal is L1, a Sim, Rotated or Replay its child's level, and a
composite (a Bandit that really is one, a Gate, a NaiveBayes) one above its highest
child. Guards and overlays add nothing.
"""

from . import blueprint as bp

ORACLE = 0  # a level of its own, below every real one in sort order


def name(level: int) -> str:
    """A level as shown: "L1", "L2", ..., or "Oracle"."""
    return "Oracle" if level == ORACLE else f"L{level}"


def has_oracle(blueprint: bp.Blueprint) -> bool:
    return any(isinstance(node, bp.Oracle) for node in blueprint.core.walk())


def level(blueprint: bp.Blueprint) -> int:
    """The blueprint's level (ORACLE for a bot holding an Oracle)."""
    if has_oracle(blueprint):
        return ORACLE
    return blueprint.core.level()
