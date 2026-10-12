"""Lowering: a bot's predictor tree as the one flat bandit the compiled pipeline plays.

The runtime (janken/kit/ensemble.py, selectors.py, bayes.py, replay.py) plays a
single bandit of arms, its replays aside, so the tree is flattened before it is
encoded (encoder.py):

* a Heuristic (an L1 core) is a bandit of its one arm, with no scorer: First
  plays it, or a random move when it has none (a Silent heuristic has no arm);
* a Gate is its main bandit with the gated experts appended as its last arms (an
  expert with several rotations is one gated arm per rotation, its prediction
  made once), under the Gatekeeper selector (the gate's rule, edge, decay and
  warmup, and the main bandit's Thompson sharpness);
* a Bandit is played as it is.

The shapes the runtime can't play are refused here, never approximated: a Gate
anywhere but at the bot's core, several gated arms outside the LEADER rules, a NaiveBayes
whose inputs aren't its bandit's other predictors.
"""

import dataclasses

from .base import BlueprintError, check
from .composites import Bandit, Gate, NaiveBayes, Replay, SignalLike, arm_count
from .heuristic import Heuristic, Silent
from .predictor import Predictor
from .selectors import Gatekeeper, Thompson
from .signals import Rotated, Signal, Sim


def lower(core: Predictor) -> Bandit:
    """The flat bandit that plays a bot's core.

    Raises:
        BlueprintError: the core is a shape the pipeline can't play.
    """
    flat = _flatten(core)
    for node in flat.walk():
        check(not isinstance(node, Gate), "a Gate compiles only as the bot's core")
    for bandit in _bandits(flat):
        _check_combiners(bandit)
    return flat


def _flatten(core: Predictor) -> Bandit:
    if isinstance(core, Heuristic):
        return _played(core)
    if isinstance(core, Gate):
        return _gated(core)
    if not isinstance(core, Bandit):
        raise BlueprintError(
            f"a bot's core is a Heuristic, a Bandit or a Gate, got {type(core).__name__}"
        )
    return core


def _played(heuristic: Heuristic) -> Bandit:
    """A Heuristic as a one-arm bandit with no scorer (no arm: random play)."""
    signal, rotation = heuristic.played()
    if isinstance(signal, Silent):
        return Bandit()
    return Bandit(predictors=(signal,), rotations=(rotation,))


def _gated(gate: Gate) -> Bandit:
    """A Gate as its main bandit plus the gated experts, last, under a Gatekeeper."""
    main = gate.main
    selector = main.selector
    if not isinstance(selector, Thompson):
        raise BlueprintError(
            "a Gate's main bandit samples by Thompson: use the Thompson selector"
        )
    check(main.arms() >= 1, "a Gate needs a main arm besides its gated experts")
    keeper = Gatekeeper(
        edge=gate.edge,
        decay=gate.decay,
        warmup=gate.warmup,
        sharp=selector.sharp,
        rule=gate.rule,
        experts=sum(arm_count(e, main.rotations) for e in gate.experts),
    )
    return dataclasses.replace(
        main, predictors=main.predictors + gate.experts, selector=keeper
    )


def _bandits(root: Bandit) -> list[Bandit]:
    """The root bandit and every bandit a replay below it plays."""
    return [root] + [n.bandit for n in root.walk() if isinstance(n, Replay)]


def _unrotated(predictor: SignalLike) -> Signal | Sim:
    return predictor.signal if isinstance(predictor, Rotated) else predictor


def _check_combiners(bandit: Bandit) -> None:
    """Each NaiveBayes combines exactly its bandit's other predictors (the other
    NaiveBayes aside), the one shape bayes.py plays."""
    others = tuple(
        p for p in bandit.predictors if not isinstance(_unrotated(p), NaiveBayes)
    )
    for predictor in bandit.predictors:
        inner = _unrotated(predictor)
        if isinstance(inner, NaiveBayes):
            check(
                inner.inputs == others,
                "a NaiveBayes combines its bandit's other predictors: list exactly"
                " those, in order, as its inputs",
            )
