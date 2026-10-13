"""The blueprint compiler: lays out every stage's state and writes the spec."""

import math
from collections.abc import Iterable, Mapping

import numpy as np

from .. import codes as c
from .base import MAX_REPLAY_DEPTH, ROTATIONS, Knob, Stage, Value, check, check_side
from .compiled import Compiled
from .composites import Bandit, NaiveBayes, Replay, SignalLike, bayes_size
from .guards import Guard, OnInvalid
from .overlays import EmitInvalid, Overlay
from .scorers import Dirichlet, NoScore
from .selectors import ChooseSelector, First, Gatekeeper, Selector, Thompson
from .signals import Geometry, LongestMatch, Oracle, Rotated, SecondMatch, Signal, Sim


def _unwrap(signal: SignalLike) -> tuple[Signal, bool, tuple[int, ...]]:
    """(the signal, whether it's a sim, its own rotations or ())."""
    rotations: tuple[int, ...] = ()
    if isinstance(signal, Rotated):
        rotations = signal.rotations
        signal = signal.signal
    if isinstance(signal, Sim):
        return signal.signal, True, rotations
    return signal, False, rotations


def _stream(signal: Signal, swapped: bool) -> int:
    """The history stream a matcher reads (STREAM_*), or -1 for other signals.

    A swapped view (a sim, a replay) reads OPP as MY and back; JOINT's repeats are
    the same rounds either way."""
    if isinstance(signal, Geometry):
        return c.STREAM_JOINT
    if not isinstance(signal, LongestMatch):
        return -1
    if signal.ctx == c.JOINT:
        return c.STREAM_JOINT
    mine = (signal.ctx == c.MY) != swapped
    return c.STREAM_MY if mine else c.STREAM_OPP


def _selector_options(selector: Selector | ChooseSelector) -> tuple[Selector, ...]:
    if isinstance(selector, ChooseSelector):
        return selector.options
    return (selector,)


class Encoder:
    """Lays out state and writes the spec, one stage at a time."""

    def __init__(
        self, defaults: Mapping[str, float | int], fixed: Iterable[str] = ()
    ) -> None:
        """`fixed`: the structural parameters, already bound (binding.py)."""
        self.names = list(defaults)
        self.defaults = dict(defaults)
        self.used: set[str] = set(fixed)
        self.spec: list[int] = [0] * c.HEADER
        self.knob_values: list[float] = []
        self.knob_binds: list[int] = []
        self.f_size = 0
        self.i_size = 0
        self.per_round = 0
        self.streams: dict[int, int] = {}  # stream -> its match index's number

    def alloc(self, f_size: int, i_size: int) -> tuple[int, int]:
        at = self.f_size, self.i_size
        self.f_size += f_size
        self.i_size += i_size
        return at

    def alloc_rounds(self, slots: int) -> int:
        """`slots` per-round slots of the workspace; returns the first one."""
        at = self.per_round
        self.per_round += slots
        return at

    def index_for(self, stream: int) -> int:
        """The number of the bot's match index over `stream` (one per stream)."""
        return self.streams.setdefault(stream, len(self.streams))

    def knob(self, value: Value) -> int:
        """A new knob slot holding `value` (a literal, or a bound parameter)."""
        if isinstance(value, Knob):
            check(
                value.name in self.defaults,
                "Knob({!r}) is not in the defaults ({})".format(
                    value.name, ", ".join(self.names) or "none"
                ),
            )
            self.used.add(value.name)
            self.knob_values.append(float(self.defaults[value.name]))
            self.knob_binds.append(self.names.index(value.name))
        else:
            check(math.isfinite(float(value)), "knob values must be finite")
            self.knob_values.append(float(value))
            self.knob_binds.append(-1)
        return len(self.knob_values) - 1

    def record(self, stage: Stage) -> list[int]:
        """A stage's record, with its state allocated and its knobs slotted."""
        stage.validate()
        rec = [0] * c.REC
        rec[c.R_KIND] = stage.kind
        rec[c.R_F], rec[c.R_I] = self.alloc(*stage.state())
        slots = [self.knob(v) for v in stage.knobs()]
        rec[c.R_K] = slots[0] if slots else -1
        for k, p in enumerate(stage.params()):
            rec[c.R_A + k] = p
        return rec

    def encode(
        self,
        guards: tuple[Guard, ...],
        core: Bandit,
        overlays: tuple[Overlay, ...],
    ) -> Compiled:
        """The compiled bot: its guards, its core (a flat bandit: see lowering.py)
        and its overlays."""
        check(
            not (
                any(isinstance(o, EmitInvalid) for o in overlays)
                and any(isinstance(g, OnInvalid) and g.side == c.BOTH for g in guards)
            ),
            "EmitInvalid would trip the bot's own OnInvalid(side=BOTH)",
        )
        cursor_i = self.alloc(0, 1)[1]
        view_i = self.alloc(0, c.VIEW_CELLS)[1]
        self.alloc_rounds(2)  # VIEW_MY_SLOT, VIEW_OPP_SLOT
        guard_records = [self.record(g) for g in guards]
        overlay_records = [self.record(o) for o in overlays]
        options = _selector_options(core.selector)
        self._check_selectors(core, options)
        choice = (
            self.knob(core.selector.index)
            if isinstance(core.selector, ChooseSelector)
            else -1
        )
        selectors = [self.record(s) for s in options]
        core_records, core_header, replays = self.bandit(core, 0, swapped=False)

        header = self.spec
        header[c.H_CURSOR_I] = cursor_i
        header[c.H_VIEW_I] = view_i
        header[c.H_NGUARD] = len(guard_records)
        header[c.H_GUARD_AT] = self.append(guard_records)
        header[c.H_NOVER] = len(overlay_records)
        header[c.H_OVER_AT] = self.append(overlay_records)
        header[c.H_NSEL] = len(selectors)
        header[c.H_SEL_AT] = self.append(selectors)
        header[c.H_SEL_K] = choice
        header[c.H_CORE], sig_at = self.place(core_records, core_header)
        self.place_replays(sig_at, replays, depth=1, swapped=False)

        header[c.H_NIDX] = len(self.streams)
        header[c.H_IDX_AT] = len(self.spec)
        for stream in self.streams:  # in index order
            fixed = self.alloc(0, c.X_FIXED)[1]
            slot = self.alloc_rounds(c.X_SLOTS)
            self.spec.extend([stream, fixed, slot, 0])
        header[c.H_ROUNDS_I] = self.alloc(0, 2)[1]

        unused = [n for n in self.names if n not in self.used]
        check(not unused, "defaults not used by any Knob: {}".format(", ".join(unused)))
        knob_f = self.alloc(len(self.knob_values), 0)[0]
        header[c.H_KNOB_F] = knob_f
        header[c.H_NKNOB] = len(self.knob_values)
        header[c.H_BIND_AT] = len(self.spec)
        self.spec.extend(self.knob_binds)
        return Compiled(
            state=(self.f_size, self.i_size, self.per_round),
            spec=np.array(self.spec, np.int64),
            knobs=np.array(self.knob_values, np.float64),
        )

    def _check_selectors(self, core: Bandit, options: tuple[Selector, ...]) -> None:
        check(len(options) >= 1, "ChooseSelector needs at least one option")
        scored = not isinstance(core.scorer, NoScore)
        for s in options:
            if isinstance(s, First):
                check(
                    not scored and core.random_arm == c.RA_NONE,
                    "First reads no scores: use NoScore and no random arm",
                )
            else:
                check(scored, f"{type(s).__name__} needs a scorer")
            if isinstance(s, Thompson | Gatekeeper):
                check(
                    isinstance(core.scorer, Dirichlet),
                    "Thompson samples a Dirichlet: use the Dirichlet scorer",
                )
                check(
                    core.random_arm != c.RA_PINNED,
                    "Thompson needs a scored random arm, not a pinned one",
                )

    def place_replays(
        self, sig_at: int, replays: list[tuple[int, Replay]], depth: int, swapped: bool
    ) -> None:
        """Encode each replayed bandit (at `depth`, 1: replayed from the top
        bandit; `swapped`: whether the bandit holding it sees the history swapped)
        and its own replays, and point its record at it."""
        for k, replay in replays:
            inside = swapped != (replay.side == c.OPP)
            sub_records, sub_header, inner = self.bandit(replay.bandit, depth, inside)
            at, sub_sig_at = self.place(sub_records, sub_header)
            self.spec[sig_at + k * c.REC + c.R_SUB] = at
            keeper = replay.bandit.selector
            if isinstance(keeper, Gatekeeper):  # a replayed Gate runs its gatekeeper
                self.spec[sig_at + k * c.REC + c.R_B] = self.append(
                    [self.record(keeper)]
                )
            self.place_replays(sub_sig_at, inner, depth + 1, inside)

    def bandit(
        self, ens: Bandit, depth: int, swapped: bool
    ) -> tuple[list[list[int]], list[int], list[tuple[int, Replay]]]:
        """A bandit's signal records, its header, and its replays as (index of
        the replay's record, the replay). `depth` counts the replays it is nested
        in; `swapped`: whether it sees the history swapped (an odd number of them
        replays it from the opponent's side)."""
        self._check_rotations(ens.rotations)
        records: list[list[int]] = []
        replays: list[tuple[int, Replay]] = []
        bayes: list[list[int]] = []
        oracles = 0
        arm = 0
        for item in ens.predictors:
            signal, swap, rotations = _unwrap(item)
            rotations = rotations or ens.rotations
            self._check_rotations(rotations)
            rec = self.record(signal)
            rec[c.R_SWAP] = int(swap)
            stream = _stream(signal, swap != swapped)
            if stream >= 0:
                rec[c.R_IDX] = self.index_for(stream)
            rec[c.R_ARM] = arm
            rec[c.R_NROT] = len(rotations)
            for k, r in enumerate(rotations):
                rec[c.R_ROT + k] = r
            arm += len(rotations)
            if isinstance(signal, SecondMatch):
                rec[c.R_C] = self.alloc_rounds(1)
            if isinstance(signal, Oracle):
                check(
                    depth == 0 and not swap,
                    "an Oracle mocks the bot's own expert: not in a Sim or a Replay",
                )
                oracles += 1
                check(oracles <= 1, "a bot holds at most one Oracle")
            if isinstance(signal, NaiveBayes):
                check(not swap, "a NaiveBayes combines its bandit: no Sim of it")
                bayes.append(rec)
            if isinstance(signal, Replay):
                check(
                    depth < MAX_REPLAY_DEPTH,
                    f"replays (bots of level 2+ as arms) nest at most"
                    f" {MAX_REPLAY_DEPTH} deep",
                )
                check(not swap, "a Replay picks its side itself: no Sim of it")
                check(
                    not isinstance(signal.bandit.scorer, NoScore),
                    "a Replay's bandit needs a scorer to pick its best arm",
                )
                rec[c.R_SWAP] = int(signal.side == c.OPP)
                replays.append((len(records), signal))
            records.append(rec)
        for rec in bayes:
            rec[c.R_F] = self.alloc(bayes_size(len(records)), 0)[0]
        header = [0] * c.ENS
        header[c.E_NSIG] = len(records)
        header[c.E_NARMS] = arm
        header[c.E_RANDOM] = ens.random_arm
        scorer = self.record(ens.scorer)
        header[c.E_SCORER] = scorer[c.R_KIND]
        header[c.E_SCORER_K] = scorer[c.R_K]
        header[c.E_SCORE_F] = self.alloc((arm + 1) * 3, 0)[0]
        header[c.E_PEND_I] = self.alloc(0, arm + 2)[1]
        header[c.E_SYM_I] = self.alloc(0, len(records))[1]
        return records, header, replays

    def place(self, records: list[list[int]], header: list[int]) -> tuple[int, int]:
        """Append a bandit's signal records, then its header.
        Returns (the header's offset, the first record's offset)."""
        sig_at = self.append(records)
        header[c.E_SIG_AT] = sig_at
        at = len(self.spec)
        self.spec.extend(header)
        return at, sig_at

    def append(self, records: list[list[int]]) -> int:
        at = len(self.spec)
        for rec in records:
            self.spec.extend(rec)
        return at

    @staticmethod
    def _check_rotations(rotations: tuple[int, ...]) -> None:
        check(1 <= len(rotations) <= 3, "1 to 3 rotations")
        check(len(set(rotations)) == len(rotations), "rotations must be distinct")
        for r in rotations:
            check_side(r, ROTATIONS, "a rotation")
