"""Matches between a Python player and kit bots, played round by round.

The engine (janken/engine/) referees compiled bots only, all inside one numba
kernel. A learner here is a Python object, so the arena referees its matches
itself, stepping the opponent's compiled blueprint (janken/kit/pipeline.py) one
round at a time under the engine's rules: before a side moves it draws from its
own stream of the match seed (the player is side A, the kit bot side B); an
invalid move loses its round and the INVALID_MOVE_LIMIT-th forfeits the match
once scored; a crash forfeits at once, its round unplayed.

A match is scored like a gauntlet's (janken/lab/gauntlet.py): the shares of the
scheduled rounds the player won and lost.
"""

from collections.abc import Callable, Sequence
from typing import Protocol

import numpy as np

from .. import mocks
from ..engine import build, kernel, registry
from ..kit import pipeline
from ..kit.blueprint import Compiled
from ..kit.moves import CRASH, INVALID
from ..lab import gauntlet
from ..match import INVALID_MOVE_LIMIT
from ..spec import BotSpec, parse_spec

SIDE_A, SIDE_B = kernel.SIDE_A, kernel.SIDE_B


class ArenaError(ValueError):
    """A bot the arena can't play."""


class Player(Protocol):
    """One side of an arena match."""

    def reset(self, seed: int, rounds: int) -> None:
        """Start a match of `rounds` rounds, seeded with `seed`."""
        ...

    def move(self, my: np.ndarray, opp: np.ndarray, n: int) -> int:
        """The move for round n, given my[:n] and opp[:n]."""
        ...


class KitBot:
    """A kit bot (a spec: its file and parameter overrides), stepped round by
    round from one seat, drawing from that side's stream of the match seed."""

    def __init__(self, spec: BotSpec, side: int) -> None:
        if mocks.is_mock(spec.path):
            raise ArenaError(f"{spec.path} is a mock: the arena reveals no moves")
        loaded = build.load_bot(spec.path)
        if not isinstance(loaded, build.BlueprintBot):
            raise ArenaError(f"{spec.path}: the arena plays YAML bots only")
        self.side: int = side
        self.compiled: Compiled = loaded.compiled
        self.prm: np.ndarray = registry.param_vector(spec.path, spec.params)
        self.seed: int = 0
        self.f, self.i = self.compiled.new_state(1)

    def reset(self, seed: int, rounds: int) -> None:
        self.seed = seed
        self.f, self.i = self.compiled.new_state(rounds)

    def move(self, my: np.ndarray, opp: np.ndarray, n: int) -> int:
        kernel._seed_side(self.seed, self.side, n)  # the engine's own streams
        return int(
            pipeline.play(
                self.f,
                self.i,
                self.prm,
                my,
                opp,
                n,
                self.compiled.spec,
                self.compiled.knobs,
            )
        )


def play_match(a: Player, b: Player, rounds: int, seed: int) -> gauntlet.Played:
    """One match of `a` vs `b`: the shares of `rounds` won and lost by `a`."""
    a.reset(seed, rounds)
    b.reset(seed, rounds)
    ha = np.zeros(rounds, np.int64)
    hb = np.zeros(rounds, np.int64)
    won = lost = invalid_a = invalid_b = 0
    for r in range(rounds):
        ma = a.move(ha, hb, r)
        mb = b.move(hb, ha, r)
        if ma == CRASH or mb == CRASH:
            break
        ha[r], hb[r] = ma, mb
        invalid_a += ma == INVALID
        invalid_b += mb == INVALID
        outcome = score(ma, mb)
        won += outcome > 0
        lost += outcome < 0
        if invalid_a >= INVALID_MOVE_LIMIT or invalid_b >= INVALID_MOVE_LIMIT:
            break
    return gauntlet.Played(won / rounds, lost / rounds)


def score(mine: int, theirs: int) -> int:
    """+1 if `mine` wins the round, -1 if it loses, 0 on a draw (an invalid move
    loses to a valid one; two invalid moves draw)."""
    if mine == INVALID or theirs == INVALID:
        return (theirs == INVALID) - (mine == INVALID)
    return {0: 0, 1: 1, 2: -1}[(mine - theirs) % 3]


def run(
    player: Player,
    opponents: Sequence[str],
    seeds: Sequence[int],
    rounds: int,
    label: str,
    done: gauntlet.Log,
    on_done: Callable[[gauntlet.Job, gauntlet.Played], None],
) -> None:
    """Play `player` (logged as `label`) vs every opponent (a spec's text, as a
    gauntlet list holds it) on every seed, seed by seed, skipping the matches
    `done` holds; `on_done` gets each new match.

    Raises:
        ValueError: an opponent's text doesn't name a bot or its parameters.
        ArenaError: an opponent the arena can't play.
    """
    bots = {text: KitBot(parse_spec(text), SIDE_B) for text in opponents}
    for seed in seeds:
        for text, bot in bots.items():
            job = gauntlet.Job(label, text, seed)
            if job not in done:
                on_done(job, play_match(player, bot, rounds, seed))
