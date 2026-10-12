"""The predictor tree: every way of combining predictors is one composite structure.

A bot's core is a tree of predictors (the composite pattern):

    leaf        a signal: an opponent model or a generator (LastMove, NGram, ...)
    decorator   one predictor, seen differently: Heuristic (one predictor played
                with one rotation: an L1 bot's core), Sim (from the opponent's
                side), Rotated (with its own rotations), Replay (a whole bandit,
                from either side)
    composite   an aggregator, a higher-order predictor made of others: Bandit (a
                scorer and a selector over its predictors' arms), Gate (a
                gatekeeper between a main bandit and gated experts), NaiveBayes (a
                posterior over its inputs' symbols)

Every node answers `children()` and `level()`, so the bot's level (janken/kit/
levels.py) is the tree's, never re-derived per kind: a leaf is L1, a decorator its
child's level, and an aggregator always one layer above its highest child. So a
heuristic (no aggregator) is L1, an aggregator over L1s is L2, one over L2s (and
maybe L1s) is L3, and so on.
"""

import abc
from collections.abc import Iterator

LEAF_LEVEL = 1


class Predictor(abc.ABC):
    """A node of the predictor tree."""

    @abc.abstractmethod
    def children(self) -> tuple["Predictor", ...]:
        """The predictors this one is made of (none for a leaf)."""

    @abc.abstractmethod
    def level(self) -> int:
        """How many layers of meta-reasoning this predictor stacks (L1, L2, ...)."""

    def walk(self) -> Iterator["Predictor"]:
        """This predictor, then every predictor below it, depth first."""
        yield self
        for child in self.children():
            yield from child.walk()


class Leaf(Predictor):
    """A predictor of its own: level one."""

    def children(self) -> tuple[Predictor, ...]:
        return ()

    def level(self) -> int:
        return LEAF_LEVEL


class Decorator(Predictor):
    """One predictor seen differently: its level is its child's."""

    @abc.abstractmethod
    def child(self) -> Predictor:
        """The decorated predictor."""

    def children(self) -> tuple[Predictor, ...]:
        return (self.child(),)

    def level(self) -> int:
        return self.child().level()


class Composite(Predictor):
    """An aggregator, a higher-order predictor: one layer above its highest child."""

    def level(self) -> int:
        return max((child.level() for child in self.children()), default=LEAF_LEVEL) + 1
