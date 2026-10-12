"""Bot blueprints: what a bot is made of, declared as data and compiled for the pipeline.

Every bot has the same anatomy (janken/kit/pipeline.py runs it, in this order):

1. guards     answer the round before any model does: an opening, a noise floor,
              what to do once the history holds an invalid move.
2. view       the models only ever see rounds where both moves are valid.
3. track      every stateful stage folds in the rounds it hasn't seen, and the
              arms proposed last round are scored against what really happened.
4. signals    each proposes a symbol (usually the opponent's predicted move), or
              none: opponent models, generators, sims of the opponent's model of us.
5. move choice  each signal's symbol becomes one arm per rotation: COPY it, BEAT it,
              or BEAT_BEAT it (beat the move that beats it). An optional random arm
              is the defence when nothing works.
6. select     a scorer keeps each arm's record and a selector picks the arm to play.

Signals, rotations, scorer and selector make the bot's core: a tree of predictors
(predictor.py). Its leaves are signals; composites combine predictors into a
higher-order one, all the same way: a Bandit (scorer + selector over its
predictors' arms), a Gate (a gatekeeper between a main bandit and gated experts),
a NaiveBayes (a posterior over its inputs). The bot's level is the tree's.
7. overlays   transform the chosen move: stalling, a team handshake, spending the
              invalid moves the rules allow.

A bot file (bots/<level>/<name>.yaml) declares a blueprint plus its defaults; declare.py
turns its YAML into these dataclasses. A stage knob is either a literal or a
`Knob("NAME")` (`$NAME` in YAML) read from the bot's parameters, so tuning and
variants work on any stage:

    blueprint = Blueprint(
        guards=(Noise(Knob("NOISE")), Opening(1, ROCK), OnInvalid(CRASH_ACTION, LAST, OPP)),
        core=Bandit(predictors=(LastMove(OPP),), rotations=(BEAT,)),
    )
    state, spec, knobs = blueprint.compile({"NOISE": 0.05})

`compile` flattens the core into the one bandit the pipeline plays (lowering.py),
validates it, lays out the state every stage needs in the
bot's `f` / `i` arrays and encodes it all as the arrays the pipeline reads (see
codes.py). A new idea is a new stage class in the module of its stage plus its
compiled half in janken/kit.

The package, one module per part of the anatomy (each declares a stage family; its
compiled half lives in janken/kit):

    base        knobs, the Stage base class, validation helpers, shared constants
    predictor   the predictor tree: Predictor, Leaf, Decorator, Composite
    guards      1. Opening, Noise, OnInvalid
    signals     4. the opponent models and generators (leaves), Sim and Rotated
    composites  predictors made of predictors: Bandit, Gate, NaiveBayes, Replay
    scorers     6. the arms' records
    selectors   6. the arm to play
    overlays    7. Stall, Team, EmitInvalid
    anatomy     Blueprint, the whole bot
    lowering    the predictor tree as the flat bandit the pipeline plays
    encoder     the compiler: state layout and the spec
    compiled    Compiled, what `compile` returns
"""

from .anatomy import (
    Blueprint,
)
from .base import (
    ALL_ROTATIONS,
    MAX_NGRAM_ORDER,
    MAX_REPLAY_DEPTH,
    MOVES,
    ROTATIONS,
    BlueprintError,
    Knob,
    Stage,
    Value,
)
from .compiled import (
    Compiled,
)
from .composites import (
    Bandit,
    Gate,
    NaiveBayes,
    Replay,
    SignalLike,
    arm_count,
    bayes_size,
)
from .guards import (
    Guard,
    Noise,
    OnInvalid,
    Opening,
)
from .overlays import (
    EmitInvalid,
    Overlay,
    Stall,
    Team,
)
from .predictor import (
    Composite,
    Decorator,
    Leaf,
    Predictor,
)
from .scorers import (
    DecayedNet,
    Dirichlet,
    DropSwitch,
    NoScore,
    Scorer,
)
from .selectors import (
    ChooseSelector,
    First,
    Gatekeeper,
    Greedy,
    SampledVote,
    Selector,
    Thompson,
)
from .signals import (
    Backoff,
    Biased,
    Constant,
    Cycle,
    Frequency,
    Geometry,
    LastMove,
    LongestMatch,
    NGram,
    Oracle,
    React,
    Relative,
    Rotated,
    SecondMatch,
    Signal,
    Sim,
    WinStay,
)

__all__ = [
    "ALL_ROTATIONS",
    "MAX_NGRAM_ORDER",
    "MAX_REPLAY_DEPTH",
    "MOVES",
    "ROTATIONS",
    "Backoff",
    "Bandit",
    "Biased",
    "Blueprint",
    "BlueprintError",
    "ChooseSelector",
    "Compiled",
    "Composite",
    "Constant",
    "Cycle",
    "DecayedNet",
    "Decorator",
    "Dirichlet",
    "DropSwitch",
    "EmitInvalid",
    "First",
    "Frequency",
    "Gate",
    "Gatekeeper",
    "Geometry",
    "Greedy",
    "Guard",
    "Knob",
    "LastMove",
    "Leaf",
    "LongestMatch",
    "NGram",
    "NaiveBayes",
    "NoScore",
    "Noise",
    "OnInvalid",
    "Opening",
    "Oracle",
    "Overlay",
    "Predictor",
    "React",
    "Relative",
    "Replay",
    "Rotated",
    "SampledVote",
    "Scorer",
    "SecondMatch",
    "Selector",
    "Signal",
    "SignalLike",
    "Sim",
    "Stage",
    "Stall",
    "Team",
    "Thompson",
    "Value",
    "WinStay",
    "arm_count",
    "bayes_size",
]
