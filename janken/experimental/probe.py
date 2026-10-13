"""Opening probes: can a scripted opening tell an opponent's family and species?

We play a fixed opening, the probe, and record the opponent's replies; a naive
Bayes classifier, trained on the replies of known bots (parameter variants of the
field), names the family and the species of a held-out variant from its replies.
A random opening of the same length is the control: the probe is worth its
rounds only if it identifies more than chance replies do.

    PROBE       the scripted opening: a constant, a cycle, a switch, a period
    replies     the opponent's moves to an opening (played by the arena)
    family      a bot's family by its stem and level (the atlases' families)
    NaiveBayes  per round, a smoothed table of the reply given the class
"""

import math
import random
from collections.abc import Mapping, Sequence

import numpy as np

from ..kit.moves import CRASH, INVALID, PAPER, ROCK, SCISSORS
from ..spec import BotSpec
from .arena import SIDE_B, KitBot

R, P, S = ROCK, PAPER, SCISSORS
# A constant (frequency and reactive bots answer it differently), a cycle
# (pattern learners lock on), a switch (convergence speed), a period of 2.
PROBE: tuple[int, ...] = (R,) * 6 + (P, S, R) * 2 + (P,) * 3 + (S,) * 3 + (R, P) * 3
REPLIES = 4  # a reply is R, P, S, or invalid
SMOOTHING = 0.5

FIXED = frozenset({"rock", "biased", "nash"})
REACTIVE = frozenset(
    {"copycat", "reactionary", "counter_reactionary", "self_beater", "wsls", "cycler"}
)
COUNTING = frozenset({"frequency", "anti_frequency", "balancer_hunter", "score_reader"})


def species(stem: str) -> str:
    """A stem's species: the stem without its version."""
    head, _, tail = stem.rpartition("_v")
    return head if head and tail.isdigit() else stem


def family(path: str) -> str:
    """A bot's family, from its level folder and its species (the atlases)."""
    level = path.split("/")[-2]
    name = species(path.split("/")[-1].removesuffix(".yaml"))
    if level == "l1":
        if name in FIXED:
            return "fixed"
        if name in REACTIVE:
            return "reactive"
        return "counting" if name in COUNTING else "l1_learner"
    if level == "l2":
        return "replay_counter" if name.startswith("anti_") else "adaptive_bandit"
    return "gate" if "gate" in name or "hunter" in name else "l3_council"


def replies(spec: BotSpec, opening: Sequence[int], seed: int) -> list[int]:
    """The opponent's moves to our opening (a crash reads as an invalid move)."""
    bot = KitBot.of(spec, SIDE_B)
    n = len(opening)
    bot.reset(seed, n)
    mine = np.zeros(n, np.int64)
    theirs = np.zeros(n, np.int64)
    out = []
    for t in range(n):
        move = bot.move(theirs, mine, t)
        move = INVALID if move == CRASH else move
        mine[t], theirs[t] = opening[t], move
        out.append(move)
    return out


def random_opening(length: int, seed: int) -> tuple[int, ...]:
    """A uniformly random opening (the control)."""
    rng = random.Random(seed)
    return tuple(rng.randrange(3) for _ in range(length))


class NaiveBayes:
    """Per round, a smoothed table of the reply given the class; predicts the
    class whose tables make the replies likeliest."""

    def __init__(self, rounds: int) -> None:
        self.rounds: int = rounds
        self.counts: dict[str, np.ndarray] = {}

    def fit(self, examples: Sequence[tuple[Sequence[int], str]]) -> "NaiveBayes":
        for reply, label in examples:
            table = self.counts.setdefault(label, np.zeros((self.rounds, REPLIES)))
            for t in range(self.rounds):
                table[t, reply[t]] += 1.0
        return self

    def predict(self, reply: Sequence[int]) -> str:
        best, best_label = -math.inf, ""
        for label, table in self.counts.items():
            total = table.sum(axis=1) + SMOOTHING * REPLIES
            score = sum(
                math.log((table[t, reply[t]] + SMOOTHING) / total[t])
                for t in range(self.rounds)
            )
            if score > best:
                best, best_label = score, label
        return best_label


def accuracy(
    train: Sequence[tuple[Sequence[int], Mapping[str, str]]],
    test: Sequence[tuple[Sequence[int], Mapping[str, str]]],
    rounds: int,
    key: str,
) -> float:
    """The share of test replies whose `key` label (family or species) the
    classifier trained on `train`'s first `rounds` replies names right."""
    model = NaiveBayes(rounds).fit([(r[:rounds], lab[key]) for r, lab in train])
    hits = [model.predict(r[:rounds]) == lab[key] for r, lab in test]
    return sum(hits) / len(hits) if hits else 0.0
