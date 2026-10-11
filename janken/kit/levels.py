"""Bot levels: how many layers of meta-reasoning a blueprint stacks.

    L1      a heuristic: signals played without a bandit (copycat, an n-gram, rock)
    L2      a bandit over L1 arms (smartbot, iocaine, a scoreboard of rotations)
    L3      a bandit whose arms include an L2 (a replay of smartbot: smartbot_sims)
    L4 ...  one more layer per bandit over arms of the level below
    ORACLE  a bot holding an Oracle (research only: janken/mocks.py)

One rule, computed from the blueprint, never written down: a plain signal or a
Sim of one is L1, a Replay is its ensemble's level, a NaiveBayes combiner is one
above the ensemble's other signals; an ensemble is its highest signal's level,
plus one when it is a bandit (a scorer over two or more arms). Guards and
overlays add nothing.
"""

from . import blueprint as bp

ORACLE = 0  # a level of its own, below every real one in sort order


def name(level: int) -> str:
    """A level as shown: "L1", "L2", ..., or "Oracle"."""
    return "Oracle" if level == ORACLE else f"L{level}"


def has_oracle(blueprint: bp.Blueprint) -> bool:
    return any(isinstance(_unwrap(s), bp.Oracle) for s in blueprint.signals)


def level(blueprint: bp.Blueprint) -> int:
    """The blueprint's level (ORACLE for a bot holding an Oracle)."""
    if has_oracle(blueprint):
        return ORACLE
    return ensemble_level(blueprint.core)


def ensemble_level(ensemble: bp.Ensemble) -> int:
    """The highest level among the ensemble's signals, plus one for a bandit."""
    signals = [_unwrap(s) for s in ensemble.signals]
    plain = [_signal_level(s) for s in signals if not isinstance(s, bp.NaiveBayes)]
    top = max(plain, default=1)
    if any(isinstance(s, bp.NaiveBayes) for s in signals):
        top += 1  # a combiner over the others
    return top + 1 if _is_bandit(ensemble) else top


def _signal_level(signal: bp.Signal) -> int:
    if isinstance(signal, bp.Replay):
        return ensemble_level(signal.ensemble)
    return 1


def _is_bandit(ensemble: bp.Ensemble) -> bool:
    if isinstance(ensemble.scorer, bp.NoScore):
        return False
    arms = sum(
        len(item.rotations if isinstance(item, bp.Rotated) else ensemble.rotations)
        for item in ensemble.signals
    )
    return arms >= 2


def _unwrap(item: bp.SignalLike) -> bp.Signal:
    """The signal inside a Rotated / Sim wrapper."""
    signal = item.signal if isinstance(item, bp.Rotated) else item
    return signal.signal if isinstance(signal, bp.Sim) else signal
