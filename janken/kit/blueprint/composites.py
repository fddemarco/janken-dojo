"""Predictors made of predictors: the aggregators (the bandit, the gate, the
naive-Bayes combiner) and the replay of a whole bandit (see predictor.py for the
tree they make).

    Bandit      its predictors' arms (each predictor x each of its rotations, plus
                an optional random arm), every arm's record (a scorer) and the arm
                to play (a selector): smartbot, iocaine, a scoreboard
    Gate        a gatekeeper between a main Bandit (Thompson sampling over its arms)
                and gated experts, one arm each, by their own records
    NaiveBayes  a posterior over the opponent's move from its inputs' symbols
    Replay      a whole Bandit, run from the opponent's side (its likely move) or
                from ours (its own move): how a bot of level 2 or more becomes an
                arm of another

In a bot file, an aggregator's arms are bots, named (declare.py, refs.py). The
compiled pipeline plays one flat bandit, so lowering.py flattens a Gate into one
and checks the shapes it can play.
"""

import dataclasses
from typing import ClassVar

from .. import codes as c
from .base import Value, check
from .predictor import Composite, Decorator, Predictor
from .scorers import Dirichlet, NoScore, Scorer
from .selectors import ChooseSelector, First, Selector
from .signals import Rotated, Signal, Sim


@dataclasses.dataclass(frozen=True)
class Replay(Decorator, Signal):
    """A whole bot core (`bandit`) replayed on the shared history, from `side`: OPP
    (the default), the opponent's side, as a model of us; MY, ours, as a nested
    bot. The symbol is its most likely move, read from its arms' records (its own
    selector isn't run): the arm with the best score, or, with `draws` > 0, the move
    Thompson sampling picks most often in that many draws of every arm's Dirichlet
    (a scored random arm counts for each move). Bot files name it as an arm
    (refs.py), never directly."""

    kind: ClassVar[int] = c.S_REPLAY
    declarable: ClassVar[bool] = False
    bandit: "Bandit"
    draws: int = 0
    side: int = c.OPP

    def child(self) -> Predictor:
        return self.bandit

    def params(self) -> tuple[int, ...]:
        return (self.draws,)

    def validate(self) -> None:
        check(self.draws >= 0, "Replay draws must be >= 0")
        check(self.side in (c.OPP, c.MY), "a Replay's side is OPP or MY")
        check(
            self.draws == 0 or isinstance(self.bandit.scorer, Dirichlet),
            "Replay draws sample a Dirichlet: use the Dirichlet scorer",
        )


@dataclasses.dataclass(frozen=True)
class NaiveBayes(Composite, Signal):
    """TPI-lite (rps_kaggle section 6): a naive-Bayes combiner of `inputs`, which are its
    bandit's other predictors (the one shape the pipeline combines: lowering.py
    checks it). Per input it keeps counts, decayed by `decay`, of its symbol
    (NO_MOVE included) against the opponent's real move; the posterior over the
    opponent's next move multiplies those likelihoods with a decayed prior. The
    symbol is the opponent move that our expected-score-best move beats, so play
    it with BEAT."""

    kind: ClassVar[int] = c.S_BAYES
    inputs: tuple["SignalLike", ...] = ()  # a bot file leaves them out: declare.py
    decay: Value = 0.95

    def children(self) -> tuple[Predictor, ...]:
        return self.inputs

    def knobs(self) -> tuple[Value, ...]:
        return (self.decay,)


def bayes_size(inputs: int) -> int:
    """NaiveBayes's f block over a bandit of `inputs` signals: the prior, then per
    signal a (symbol or NO_MOVE) x (opponent move) count table."""
    return 3 + inputs * 4 * 3


SignalLike = Signal | Sim | Rotated


def arm_count(predictor: SignalLike, rotations: tuple[int, ...]) -> int:
    """How many arms `predictor` makes in a bandit of these rotations."""
    return (
        len(predictor.rotations) if isinstance(predictor, Rotated) else len(rotations)
    )


@dataclasses.dataclass(frozen=True)
class Bandit(Composite):
    """A multi-armed bandit over its predictors: each predictor x each rotation is
    an arm, plus an optional random arm; the scorer keeps every arm's record and
    the selector picks the arm to play. Like every aggregator it adds a level."""

    predictors: tuple[SignalLike, ...] = ()
    rotations: tuple[int, ...] = (c.BEAT,)
    scorer: Scorer = NoScore()
    random_arm: int = c.RA_NONE
    selector: Selector | ChooseSelector = First()

    def children(self) -> tuple[Predictor, ...]:
        return self.predictors

    def arms(self) -> int:
        """Its arms, the random arm aside."""
        return sum(arm_count(p, self.rotations) for p in self.predictors)


@dataclasses.dataclass(frozen=True)
class Gate(Composite):
    """Two kinds of expert under a gatekeeper: the `main` bandit (Thompson
    sampling over its arms) and the gated `experts`, played after the main
    bandit's arms: one gated arm per rotation of each (an expert's prediction is
    made once, however many rotations it has). The gatekeeper keeps the gated experts' own Dirichlet
    records, decayed by `decay`, every round, played or not, and with `rule`:

    EDGE        from round `warmup` on, the gated expert plays while its posterior
                mean P(win) - P(loss) is above `edge`, else the main bandit;
    ANTI_FIRST  the gated expert plays unless, from round `warmup` on, the main
                bandit's record (its proposal, kept every round too) beats it
                by more than `edge`;
    BANDIT      Thompson sampling (the main bandit's sharpness) between the two
                records;
    ANTI_FIRST_HOLD  ANTI_FIRST, but once on the main bandit it stays there
                until the gated expert leads it by more than `edge` (hysteresis);
    MAIN_FIRST  the main bandit first; from round `warmup` on, the gated expert
                once it leads the main bandit by more than `edge`, kept until
                the main bandit leads it by more than `edge` (hysteresis);
    LEADER      MAIN_FIRST over the main bandit and every gated expert: the
                best-scored one takes over once it leads the current one by
                more than `edge`;
    LEADER_PRIORITY  LEADER, but from a gated expert only the main bandit or
                the last gated expert (e.g. the anti expert) can take over.

    Only the LEADER rules gate more than one arm (an expert of several rotations
    is several arms).
    """

    main: Bandit
    experts: tuple[SignalLike, ...]
    rule: int = c.EDGE
    edge: Value = 0.05
    decay: Value = 1.0
    warmup: Value = 20

    def children(self) -> tuple[Predictor, ...]:
        return (self.main, *self.experts)
