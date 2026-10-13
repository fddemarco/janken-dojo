"""Bot levels: how many layers of aggregation a blueprint stacks.

    L1      a heuristic: one signal played with one rotation, no Bandit and no Gate
            (copycat, an n-gram, rock)
    L2      a meta-heuristic: a Bandit or a Gate over L1s (smartbot, iocaine, a
            scoreboard)
    L3      a Bandit or a Gate over L2s, and maybe L1s (smartbot_sims: L1s and
            replays of L2s)
    L4 ...  one more layer per aggregator: over L3s, and maybe L2s and L1s
    ORACLE  a bot holding an Oracle (research only: janken/mocks.py)

The level is the core predictor tree's (janken/kit/blueprint/predictor.py), never
written down: a signal is L1; a Heuristic, Sim, Rotated or Replay its child's level;
an aggregator (a Bandit, a Gate, a NaiveBayes) always one above its highest child.
Guards and overlays add nothing. A bot of the field lives in its level's folder of
the bots dir (bots/l1, bots/l2, ..., bots/oracle).
"""

from . import blueprint as bp

ORACLE = 0  # a level of its own, below every real one in sort order


def name(level: int) -> str:
    """A level as shown: "L1", "L2", ..., or "Oracle"."""
    return "Oracle" if level == ORACLE else f"L{level}"


def folder(level: int) -> str:
    """The folder of the bots dir a bot of this level lives in: "l1", ..., "oracle"."""
    return name(level).lower()


def is_level_folder(folder_name: str) -> bool:
    """Whether `folder_name` is a level's folder ("l1", "l2", ..., "oracle")."""
    if folder_name == folder(ORACLE):
        return True
    return folder_name.startswith("l") and folder_name[1:].isdigit()


def has_oracle(blueprint: bp.Blueprint) -> bool:
    return any(isinstance(node, bp.Oracle) for node in blueprint.core.walk())


def level(blueprint: bp.Blueprint) -> int:
    """The blueprint's level (ORACLE for a bot holding an Oracle)."""
    if has_oracle(blueprint):
        return ORACLE
    return blueprint.core.level()
