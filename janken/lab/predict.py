"""Score predictors on the move dataset.

    uv run janken lab predict bots/x.yaml [bots/y.yaml:NAME=value ...] --split test

Every stored match is replayed from both sides (predict_kernel.py), so each round
gives two predictions: p1's move, made from p2's side, and p2's. A round where the
predicted move is invalid has no class and is left out.
"""

import dataclasses

import numpy as np

from ..kit.moves import INVALID
from . import metrics
from .dataset import Sequences
from .predict_kernel import predict_batch
from .predictor import Predictor


@dataclasses.dataclass(frozen=True)
class Targets:
    """Every scored prediction's true move, and whose move it was (an index into
    the dataset's labels); `keep` selects the valid moves of the stacked rows."""

    y_true: np.ndarray
    player: np.ndarray
    keep: np.ndarray


@dataclasses.dataclass(frozen=True)
class Evaluation:
    """A predictor's scores on a dataset, overall and per predicted player."""

    label: str
    scores: metrics.Scores
    by_player: list[tuple[str, metrics.Scores]]


def match_seeds(seqs: Sequences) -> np.ndarray:
    """One seed per match side, from the match's own seed: every predictor and
    every trial draws the same random numbers on the same match side."""
    sides = np.stack([seqs.seeds * 2, seqs.seeds * 2 + 1], axis=1).reshape(-1)
    return (sides & 0xFFFFFFFF).astype(np.int64)


def predictions(predictor: Predictor, seqs: Sequences) -> np.ndarray:
    """int64[2, rounds]: predictions of p1's moves (row 0) and of p2's (row 1)."""
    return predict_batch(
        predictor.compiled.spec,
        predictor.compiled.knobs,
        predictor.state,
        predictor.prm,
        seqs.p1,
        seqs.p2,
        seqs.starts,
        match_seeds(seqs),
    )


def targets(seqs: Sequences) -> Targets:
    """The true moves, stacked as the rows of `predictions` (p1's, then p2's)."""
    lengths = np.diff(seqs.starts)
    stacked = np.concatenate([seqs.p1, seqs.p2])
    player = np.concatenate(
        [np.repeat(seqs.p1_index, lengths), np.repeat(seqs.p2_index, lengths)]
    )
    keep = stacked != INVALID
    return Targets(y_true=stacked[keep], player=player[keep], keep=keep)


def evaluate(predictor: Predictor, seqs: Sequences) -> Evaluation:
    """The predictor's scores, overall and per predicted player."""
    truth = targets(seqs)
    y_pred = predictions(predictor, seqs).reshape(-1)[truth.keep]
    return Evaluation(
        label=predictor.label,
        scores=metrics.scores(truth.y_true, y_pred),
        by_player=metrics.by_group(truth.y_true, y_pred, truth.player, seqs.labels),
    )


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def table(headers: list[str], rows: list[list[str]]) -> str:
    """A markdown table."""
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in rows])


def score_row(name: str, s: metrics.Scores) -> list[str]:
    """A markdown row of every metric."""
    return [
        name,
        str(s.n),
        _pct(s.accuracy),
        f"{s.macro_f1:.3f}",
        f"{s.kappa:+.3f}",
        f"{s.edge:+.3f}",
    ]


SCORE_HEADERS = ["predictor", "n", "accuracy", "macro F1", "kappa", "edge"]


def render(evaluations: list[Evaluation], players: bool) -> str:
    """The predictors' scores, best accuracy first; per predicted player too."""
    ranked = sorted(evaluations, key=lambda e: e.scores.accuracy, reverse=True)
    out = [table(SCORE_HEADERS, [score_row(e.label, e.scores) for e in ranked])]
    if players:
        for e in ranked:
            rows = sorted(e.by_player, key=lambda p: p[1].accuracy, reverse=True)
            out.append(f"\n### {e.label}, per predicted player\n")
            out.append(
                table(
                    ["player"] + SCORE_HEADERS[1:],
                    [score_row(name, s) for name, s in rows],
                )
            )
    return "\n".join(out)
