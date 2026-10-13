"""Identifying an opponent bandit's parameters from its moves (research only).

A counterfactually scored bandit's state is a function of the public history and
its parameters: only its final pick is random. So a candidate (a hypothesis bot,
its parameters set) replayed from the opponent's seat names the move the opponent
would most likely play if it were that candidate, and the moves it actually plays
weigh the candidates: a particle posterior over (species, parameters).

    particles   per hypothesis bot, parameter vectors drawn from its space file
                (gauntlet.candidates), restricted to what its core reads (a
                replay leaves out guards and overlays, and the parameters only
                they read); each compiled as a Heuristic over a Replay of the
                bot from the opponent's side (estimate NORMAL, no draws)
    posterior   a particle's weight is (1 - eps) per round it names the
                opponent's move and eps / 2 per miss: the ranking is by hits,
                eps only sets how sharp it is; particles far behind the best one
                are pruned at each checkpoint
    branches    every match is played three times on one seed: we play the probe
                bot until the commit round, then (exploit) the move that beats the
                posterior's vote, (keep) the probe still, or (oracle) the move that
                beats the true opponent's replay. Both sides draw from the
                engine's streams, so the three agree up to the commit round, and
                the rounds after it compare the three policies directly. A
                fourth, (switch), plays whichever of exploit and keep has the
                better decayed record so far, both scored counterfactually from
                round 0: it should never fall far below keep.

A study's verdict is in the rounds after the commit: exploit vs keep says whether
identification pays, oracle says how much more it could.
"""

import dataclasses
import functools
import math
import os
from collections.abc import Mapping, Sequence

import numpy as np

from .. import botfile, library, mocks
from ..engine import registry
from ..kit import blueprint as bp
from ..kit import declare
from ..kit.moves import INVALID
from ..lab import gauntlet
from ..lab import space as spaces
from ..lab.predictor import predictor_params
from ..match import bot_name
from ..spec import BotSpec, parse_spec
from .arena import SIDE_A, SIDE_B, KitBot, Player, outcomes, score, shares

Number = int | float
BRANCHES = ("exploit", "keep", "oracle", "switch")
COMPONENT_SIDES = ("OPP", "MY")
COMPONENT_ROTATIONS = ("COPY", "BEAT", "BEAT_BEAT")


@dataclasses.dataclass(frozen=True)
class Hypothesis:
    """A candidate opponent: a bot, the parameters its core reads, and how its
    move is read: from the opponent's seat as is (a whole bot), or, for a
    component (a block), from either seat (`side`) turned by `rotation`."""

    stem: str
    params: Mapping[str, Number]
    rotation: str = "COPY"
    side: str = "OPP"


def particle_data(hypothesis: Hypothesis, estimate: bool) -> dict[str, object]:
    """The blueprint section of a particle: the hypothesis replayed from the
    opponent's seat, its likely move played as is (a prediction, not a reply).
    With `estimate`, a bandit's likely move is computed (estimate NORMAL, which
    needs a Dirichlet scorer); otherwise its best arm plays."""
    signal: dict[str, object] = {
        "bot": hypothesis.stem,
        "side": hypothesis.side,
        "rotations": [hypothesis.rotation],
    }
    if hypothesis.params:
        signal["space"] = dict(hypothesis.params)
    if estimate:
        signal["estimate"] = "NORMAL"
    return {"core": {"Heuristic": {"signal": signal, "rotation": "COPY"}}}


def particle(hypothesis: Hypothesis, path: str) -> KitBot:
    """A hypothesis compiled as a particle (`path`: its bot's file). A bandit
    whose scorer isn't a Dirichlet can't be estimated: its best arm plays."""
    lib = library.Library(library.library_root(path))
    where = f"particle {hypothesis.stem}"
    try:
        data = particle_data(hypothesis, mocks.path_level(path) > 1)
        compiled = declare.blueprint_from_data(data, lib, where).compile({})
    except bp.BlueprintError:
        data = particle_data(hypothesis, False)
        compiled = declare.blueprint_from_data(data, lib, where).compile({})
    return KitBot(compiled, np.zeros(registry.P_MAX), SIDE_A)


def components(path: str) -> list[Hypothesis]:
    """A component (a block, at its defaults) read every way: from both seats,
    at every rotation, so no whole architecture is assumed."""
    stem = bot_name(path)
    return [
        Hypothesis(stem, {}, rotation, side)
        for side in COMPONENT_SIDES
        for rotation in COMPONENT_ROTATIONS
    ]


def core_space(path: str, space: spaces.Space) -> spaces.Space:
    """A space restricted to the parameters the bot's core reads."""
    core = set(predictor_params(path))
    kept = {n: p for n, p in space.params.items() if n in core}
    return dataclasses.replace(space, params=kept)


def hypotheses(path: str, space: spaces.Space, n: int, seed: int) -> list[Hypothesis]:
    """Up to n parameter vectors of the bot at `path`, drawn from its space's
    core parameters (one hypothesis, its defaults, when it has none)."""
    stem = bot_name(path)
    core = core_space(path, space)
    if not core.params:
        return [Hypothesis(stem, {})]
    texts = gauntlet.candidates(path, core, n, 1, seed)
    return [Hypothesis(stem, numbers(parse_spec(t).params)) for t in texts]


def truth(spec: BotSpec) -> Hypothesis:
    """The opponent as a hypothesis: its core parameters, defaults overlaid with
    the spec's overrides."""
    values = {**botfile.defaults(spec.path), **spec.params}
    core = predictor_params(spec.path)
    return Hypothesis(bot_name(spec.path), numbers({n: values[n] for n in core}))


def numbers(values: Mapping[str, object]) -> dict[str, Number]:
    """Parameter values, checked to be numbers.

    Raises:
        TypeError: a value isn't a number.
    """
    out: dict[str, Number] = {}
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise TypeError(f"parameter {name} must be a number, got {value!r}")
        out[name] = value
    return out


def distance(param: spaces.Param, a: object, b: object) -> float:
    """How far apart two values are, as a share of the param's range (a
    categorical's: 0 or 1)."""
    if param.type == "categorical":
        return float(a != b)
    width = float(param.high) - float(param.low)
    if width <= 0 or not isinstance(a, int | float) or not isinstance(b, int | float):
        return 0.0
    return abs(float(a) - float(b)) / width


def errors(
    estimate: Hypothesis, true: Hypothesis, space: spaces.Space
) -> dict[str, float]:
    """Each parameter's distance from the truth (those the space knows)."""
    return {
        n: distance(p, estimate.params.get(n), true.params.get(n))
        for n, p in space.params.items()
        if n in true.params
    }


class Posterior:
    """Particles and their log weights, updated round by round."""

    def __init__(
        self,
        hypotheses: Sequence[Hypothesis],
        bots: Sequence[Player],
        eps: float,
        forget: float,
    ) -> None:
        if len(hypotheses) != len(bots) or not bots:
            raise ValueError("a posterior has one bot per hypothesis, and some")
        if not 0 < eps < 1:
            raise ValueError(f"eps must be in (0, 1), got {eps}")
        self.hypotheses: tuple[Hypothesis, ...] = tuple(hypotheses)
        self.bots: tuple[Player, ...] = tuple(bots)
        self.forget: float = forget  # each round's weight on the evidence so far
        self.hit: float = math.log(1 - eps)
        self.miss: float = math.log(eps / 2)
        self.logw: np.ndarray = np.zeros(len(bots))
        self.alive: np.ndarray = np.ones(len(bots), bool)
        self.predicted: np.ndarray = np.zeros(len(bots), np.int64)

    def reset(self, seed: int, rounds: int, excluded: str) -> None:
        """A new match: equal weights, every particle alive but those of the
        species `excluded` ('' for none)."""
        self.logw[:] = 0.0
        self.alive[:] = [h.stem != excluded for h in self.hypotheses]
        if not self.alive.any():
            raise ValueError(f"no hypothesis is left once {excluded} is excluded")
        for bot in self.bots:
            bot.reset(seed, rounds)

    def step(self, my: np.ndarray, opp: np.ndarray, n: int) -> None:
        """Every living particle's prediction of the opponent's move in round n."""
        for k in np.flatnonzero(self.alive):
            self.predicted[k] = self.bots[k].move(my, opp, n)

    def observe(self, theirs: int) -> None:
        """Weigh the last predictions by the opponent's actual move."""
        hits = self.predicted == theirs
        self.logw *= self.forget
        self.logw += np.where(hits, self.hit, self.miss) * self.alive

    def weights(self) -> np.ndarray:
        """The normalised weights (0 for a pruned particle)."""
        shifted = np.where(self.alive, self.logw - self.logw[self.alive].max(), -np.inf)
        w = np.exp(shifted)
        return w / w.sum()

    def vote(self) -> int:
        """The opponent's likeliest move: the predictions, weighted."""
        named = self.alive & (self.predicted >= 0) & (self.predicted < 3)
        mass = np.bincount(self.predicted[named], self.weights()[named], 3)
        return int(np.argmax(mass))

    def best(self) -> Hypothesis:
        """The most probable particle (the MAP estimate)."""
        return self.hypotheses[int(np.argmax(self.weights()))]

    def prune(self, ratio: float) -> None:
        """Drop the particles under `ratio` of the best one's weight."""
        if ratio > 0:
            self.alive &= self.weights() >= ratio * self.weights().max()


@dataclasses.dataclass(frozen=True)
class Judge:
    """What a checkpoint scores the posterior against: the truth and the spaces
    its parameters are measured in."""

    true: Hypothesis
    spaces: Mapping[str, spaces.Space]  # by stem: each hypothesis' core space
    near: float

    def score(self, n: int, posterior: Posterior, hits: int, seen: int) -> dict:
        """The posterior after n rounds (hits of its vote in its last `seen`)."""
        w = posterior.weights()
        best = posterior.best()
        ours = [
            k for k, h in enumerate(posterior.hypotheses) if h.stem == self.true.stem
        ]
        space = self.spaces.get(self.true.stem)
        near = 0.0
        row: dict[str, object] = {
            "round": n,
            "map": best.stem,
            "correct": best.stem == self.true.stem,
            "species_mass": float(w[ours].sum()) if ours else 0.0,
            "hit": hits / seen if seen else 0.0,
            "alive": int(posterior.alive.sum()),
        }
        if space is not None:
            for k in ours:
                far = errors(posterior.hypotheses[k], self.true, space).values()
                near += float(w[k]) * all(d <= self.near for d in far)
            if best.stem == self.true.stem:
                found = errors(best, self.true, space)
                row["param_error"] = sum(found.values()) / max(1, len(found))
        row["near_mass"] = near
        return row


class PosteriorPlayer:
    """Plays the move that beats the posterior's vote, scoring the posterior
    every `every` rounds (then pruning it)."""

    def __init__(
        self,
        posterior: Posterior,
        judge: Judge,
        every: int,
        prune_ratio: float,
        excluded: str,
    ) -> None:
        self.posterior: Posterior = posterior
        self.judge: Judge = judge
        self.every: int = every
        self.prune_ratio: float = prune_ratio
        self.excluded: str = excluded
        self.checkpoints: list[dict] = []
        self.guess: int = 0
        self.hits: int = 0
        self.seen: int = 0

    def reset(self, seed: int, rounds: int) -> None:
        self.posterior.reset(seed, rounds, self.excluded)
        self.checkpoints = []
        self.hits = self.seen = 0

    def move(self, my: np.ndarray, opp: np.ndarray, n: int) -> int:
        if n > 0 and opp[n - 1] != INVALID:
            self.posterior.observe(int(opp[n - 1]))
            self.hits += int(self.guess == opp[n - 1])
            self.seen += 1
        if n > 0 and n % self.every == 0:
            row = self.judge.score(n, self.posterior, self.hits, self.seen)
            self.checkpoints.append(row)
            self.hits = self.seen = 0
            self.posterior.prune(self.prune_ratio)
        self.posterior.step(my, opp, n)
        self.guess = self.posterior.vote()
        return (self.guess + 1) % 3  # what beats it


class Committed:
    """The probe until round `commit`, then `after`; `after` sees every round."""

    def __init__(self, probe: Player, after: PosteriorPlayer, commit: int) -> None:
        self.probe: Player = probe
        self.after: PosteriorPlayer = after
        self.commit: int = commit

    def reset(self, seed: int, rounds: int) -> None:
        self.probe.reset(seed, rounds)
        self.after.reset(seed, rounds)

    def move(self, my: np.ndarray, opp: np.ndarray, n: int) -> int:
        theirs = self.after.move(my, opp, n)
        return self.probe.move(my, opp, n) if n < self.commit else theirs


class Switch:
    """Keep's move or exploit's, whichever has the better decayed record: both
    are played every round and scored on what their move would have won (a
    counterfactual two-armed bandit). Before round `commit`, keep always plays."""

    def __init__(
        self, probe: Player, after: PosteriorPlayer, commit: int, decay: float
    ) -> None:
        self.probe: Player = probe
        self.after: PosteriorPlayer = after
        self.commit: int = commit
        self.decay: float = decay
        self.scores: list[float] = [0.0, 0.0]  # keep, exploit
        self.last: tuple[int, int] = (0, 0)

    def reset(self, seed: int, rounds: int) -> None:
        self.probe.reset(seed, rounds)
        self.after.reset(seed, rounds)
        self.scores = [0.0, 0.0]

    def move(self, my: np.ndarray, opp: np.ndarray, n: int) -> int:
        if n > 0 and opp[n - 1] != INVALID:
            for k, mine in enumerate(self.last):
                self.scores[k] = self.decay * self.scores[k] + score(
                    mine, int(opp[n - 1])
                )
        theirs = self.after.move(my, opp, n)
        ours = self.probe.move(my, opp, n)
        self.last = (ours, theirs)
        if n < self.commit or self.scores[0] >= self.scores[1]:
            return ours
        return theirs


@dataclasses.dataclass(frozen=True)
class Setup:
    """Everything a study's match depends on but its opponent and seed."""

    hypotheses: tuple[str, ...]  # bot files
    spaces_dir: str
    particles: int
    sampler_seed: int
    eps: float
    commit: int
    every: int
    prune_ratio: float
    near: float
    probe: str  # a bot file
    rounds: int
    leave_one_out: bool
    forget: float
    switch_decay: float
    components: tuple[str, ...]  # bot files (blocks), read every way


@dataclasses.dataclass(frozen=True)
class Field:
    """A setup's particles, compiled once, and the spaces they were drawn from."""

    hypotheses: tuple[Hypothesis, ...]
    bots: tuple[KitBot, ...]
    spaces: Mapping[str, spaces.Space]


def space_of(path: str, spaces_dir: str) -> spaces.Space:
    """The core space of the bot at `path`, from its space file."""
    found = spaces.load(os.path.join(spaces_dir, bot_name(path) + ".yaml"))
    return core_space(path, found)


@functools.cache
def field(setup: Setup) -> Field:
    """The setup's particles (built once per process, reused by every match)."""
    found: list[Hypothesis] = []
    bots: list[KitBot] = []
    by_stem: dict[str, spaces.Space] = {}
    for path in setup.hypotheses:
        space = space_of(path, setup.spaces_dir)
        by_stem[bot_name(path)] = space
        for h in hypotheses(path, space, setup.particles, setup.sampler_seed):
            found.append(h)
            bots.append(particle(h, path))
    for path in setup.components:
        for h in components(path):
            found.append(h)
            bots.append(particle(h, path))
    return Field(tuple(found), tuple(bots), by_stem)


def study(setup: Setup, opponent: str, seed: int) -> dict:
    """One opponent (a spec's text) on one seed: the posterior's checkpoints,
    and each branch's shares of the rounds after the commit."""
    spec = parse_spec(opponent)
    true = truth(spec)
    built = field(setup)
    spaces_by_stem = dict(built.spaces)
    own = os.path.join(setup.spaces_dir, true.stem + ".yaml")
    if true.stem not in spaces_by_stem and os.path.isfile(own):
        spaces_by_stem[true.stem] = space_of(spec.path, setup.spaces_dir)
    judge = Judge(true, spaces_by_stem, setup.near)
    excluded = true.stem if setup.leave_one_out else ""
    probe = KitBot.of(parse_spec(setup.probe), SIDE_A)
    bot = KitBot.of(spec, SIDE_B)

    def player(posterior: Posterior, out: str) -> PosteriorPlayer:
        return PosteriorPlayer(posterior, judge, setup.every, setup.prune_ratio, out)

    def ours() -> Posterior:
        return Posterior(built.hypotheses, built.bots, setup.eps, setup.forget)

    exploiting = player(ours(), excluded)
    exploit = outcomes(
        Committed(probe, exploiting, setup.commit), bot, setup.rounds, seed
    )
    checkpoints = exploiting.checkpoints
    known = Posterior([true], [particle(true, spec.path)], setup.eps, setup.forget)
    oracle = outcomes(
        Committed(probe, player(known, ""), setup.commit), bot, setup.rounds, seed
    )
    keep = outcomes(probe, bot, setup.rounds, seed)
    switching = Switch(
        probe, player(ours(), excluded), setup.commit, setup.switch_decay
    )
    switch = outcomes(switching, bot, setup.rounds, seed)
    after = setup.rounds - setup.commit
    row: dict[str, object] = {
        "opponent": opponent,
        "seed": seed,
        "species": true.stem,
        "checkpoints": checkpoints,
        "prefix_agrees": exploit[: setup.commit]
        == keep[: setup.commit]
        == oracle[: setup.commit]
        == switch[: setup.commit],
    }
    for name, played in zip(BRANCHES, (exploit, keep, oracle, switch), strict=True):
        got = shares(played[setup.commit :], after)
        row[name] = {"won": got.won, "lost": got.lost}
    return row


# --- reading a study -------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Curve:
    """The posterior at one checkpoint round, averaged over matches."""

    round: int
    correct: float
    species_mass: float
    near_mass: float
    param_error: float  # over the matches whose MAP species is right (nan: none)
    hit: float
    alive: float
    matches: int


def curve(rows: Sequence[Mapping]) -> list[Curve]:
    """The checkpoints of many matches, averaged round by round."""
    by_round: dict[int, list[Mapping]] = {}
    for row in rows:
        for point in row["checkpoints"]:
            by_round.setdefault(int(point["round"]), []).append(point)
    out = []
    for n, points in sorted(by_round.items()):
        errors_ = [float(p["param_error"]) for p in points if "param_error" in p]
        out.append(
            Curve(
                round=n,
                correct=_mean([float(p["correct"]) for p in points]),
                species_mass=_mean([float(p["species_mass"]) for p in points]),
                near_mass=_mean([float(p["near_mass"]) for p in points]),
                param_error=_mean(errors_) if errors_ else math.nan,
                hit=_mean([float(p["hit"]) for p in points]),
                alive=_mean([float(p["alive"]) for p in points]),
                matches=len(points),
            )
        )
    return out


def net(row: Mapping, branch: str) -> float:
    """A branch's rounds won minus lost after the commit, as a share."""
    return float(row[branch]["won"]) - float(row[branch]["lost"])


@dataclasses.dataclass(frozen=True)
class Gain:
    """A branch's mean net share after the commit, minus keep's, with its 95%
    CI half-width (paired by match)."""

    branch: str
    mean: float
    vs_keep: float
    half_width: float
    matches: int


def gains(rows: Sequence[Mapping]) -> list[Gain]:
    """Each branch's net share after the commit, and its paired gain over keep."""
    out = []
    for branch in BRANCHES:
        diffs = [net(r, branch) - net(r, "keep") for r in rows]
        n = len(diffs)
        mean = _mean(diffs)
        var = sum((d - mean) ** 2 for d in diffs) / (n - 1) if n > 1 else 0.0
        out.append(
            Gain(
                branch=branch,
                mean=_mean([net(r, branch) for r in rows]),
                vs_keep=mean,
                half_width=gauntlet.Z95 * math.sqrt(var / n) if n else 0.0,
                matches=n,
            )
        )
    return out


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else math.nan
