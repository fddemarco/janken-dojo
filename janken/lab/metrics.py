"""Multi-class metrics for predicting a player's next move (rock, paper, scissors).

A prediction is a move 0..2, or ABSTAIN when the predictor gave none; an
abstention counts as a miss and is in no class's column. Every metric is computed
from the 3x3 confusion matrix (rows: the true move, columns: the prediction):

    accuracy   hits / predictions                         chance: 1/3
    macro_f1   F1 of each move, averaged over the moves    chance: about 1/3
               that were played or predicted
    kappa      Cohen's kappa: accuracy over what the two   chance: 0
               marginals would score by luck alone
    edge       E[win - loss] when playing what beats the   chance: 0
               prediction: hits minus "the opponent played
               what beats the move we'd play"
"""

import dataclasses

import numpy as np

from .. import settings

N_MOVES = 3
ABSTAIN = -1
METRICS = settings.METRICS


@dataclasses.dataclass(frozen=True)
class Scores:
    """A predictor's scores over `n` predictions (`abstained` of them empty)."""

    n: int
    abstained: int
    accuracy: float
    macro_f1: float
    kappa: float
    edge: float

    def metric(self, name: str) -> float:
        """The value of the metric `name` (one of METRICS)."""
        if name not in METRICS:
            raise ValueError(f"unknown metric {name!r} (one of {', '.join(METRICS)})")
        return float(getattr(self, name))


def confusion(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """The int64[3, 3] confusion matrix; abstentions are left out of it."""
    made = y_pred != ABSTAIN
    flat = y_true[made] * N_MOVES + y_pred[made]
    counts = np.bincount(flat.astype(np.int64), minlength=N_MOVES * N_MOVES)
    return counts.reshape(N_MOVES, N_MOVES)


def scores(y_true: np.ndarray, y_pred: np.ndarray) -> Scores:
    """Every metric of `y_pred` (moves or ABSTAIN) against `y_true` (moves 0..2).

    Raises:
        ValueError: the arrays differ in length, or a value is out of range.
    """
    if y_true.shape != y_pred.shape:
        raise ValueError(f"{y_true.shape} targets but {y_pred.shape} predictions")
    if y_true.size and (y_true.min() < 0 or y_true.max() >= N_MOVES):
        raise ValueError("targets must be moves 0..2")
    if y_pred.size and (y_pred.min() < ABSTAIN or y_pred.max() >= N_MOVES):
        raise ValueError("predictions must be moves 0..2 or ABSTAIN")
    n = int(y_true.size)
    table = confusion(y_true, y_pred)
    actual = np.bincount(y_true.astype(np.int64), minlength=N_MOVES)
    return Scores(
        n=n,
        abstained=n - int(table.sum()),
        accuracy=_ratio(np.trace(table), n),
        macro_f1=_macro_f1(table, actual),
        kappa=_kappa(table, actual, n),
        edge=_ratio(np.trace(table) - _beaten(table), n),
    )


def _ratio(num: float, den: float) -> float:
    return float(num) / den if den else 0.0


def _macro_f1(table: np.ndarray, actual: np.ndarray) -> float:
    """The mean F1 of the moves played or predicted (`actual`: the true moves'
    counts, abstentions included), as 2 TP / (predicted + actual) = 2PR / (P + R)."""
    predicted = table.sum(axis=0)
    seen = [k for k in range(N_MOVES) if predicted[k] + actual[k]]
    if not seen:
        return 0.0
    return float(np.mean([2 * table[k, k] / (predicted[k] + actual[k]) for k in seen]))


def _kappa(table: np.ndarray, actual: np.ndarray, n: int) -> float:
    """Cohen's kappa over all `n` predictions (an abstention agrees with nothing)."""
    if not n:
        return 0.0
    observed = np.trace(table) / n
    by_luck = float(actual @ table.sum(axis=0)) / (n * n)
    return _ratio(observed - by_luck, 1.0 - by_luck)


def _beaten(table: np.ndarray) -> int:
    """Predictions where the true move beats the move that beats the prediction:
    true = prediction + 2 (mod 3), so playing on the prediction loses."""
    return int(sum(table[(k + 2) % N_MOVES, k] for k in range(N_MOVES)))


def by_group(
    y_true: np.ndarray, y_pred: np.ndarray, groups: np.ndarray, names: list[str]
) -> list[tuple[str, Scores]]:
    """Scores per group: `groups[j]` indexes `names` for prediction j. Groups with
    no prediction are left out."""
    return [
        (name, scores(y_true[groups == g], y_pred[groups == g]))
        for g, name in enumerate(names)
        if np.any(groups == g)
    ]
