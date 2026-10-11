"""The predictor tree: every way of combining predictors is one composite structure.

A bot's core is a tree of predictors (the composite pattern):

    leaf        a signal: an opponent model or a generator (LastMove, NGram, ...)
    decorator   one predictor, seen differently: Sim (from the opponent's side),
                Rotated (with its own rotations), Replay (a whole bandit from the
                opponent's side)
    composite   a higher-order predictor made of others: Bandit (a scorer and a
                selector over its predictors' arms), Gate (a gatekeeper between a
                main bandit and gated experts), NaiveBayes (a posterior over its
                inputs' symbols)

Every node answers `children()` and `level()`, so the bot's level (janken/kit/
levels.py) is the tree's, never re-derived per kind: a leaf is L1, a decorator its
child's level, and a composite one layer above its highest child (a Bandit only
when it really is one: a scorer over two arms or more).
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
    """A higher-order predictor: one layer above its highest child."""

    def stacks_level(self) -> bool:
        """Whether combining the children adds a layer (it does unless overridden)."""
        return True

    def level(self) -> int:
        top = max((child.level() for child in self.children()), default=LEAF_LEVEL)
        return top + 1 if self.stacks_level() else top
