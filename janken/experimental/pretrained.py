"""A pre-trained context table as an arena player (research only).

The opponent's next move given the last `k` joint moves, counted over the move
dataset (janken/lab/dataset.py: every round of every stored match, read from both
seats), then refined online during the match. The prior's weight says how much the
dataset counts against the match's own evidence: 0 is a purely online table, the
control that isolates what pre-training adds.

    train     the dataset's counts, one row of 3 per joint context
    Table     the player: prior x weight + the match's counts, beat the argmax
"""

import random

import duckdb
import numpy as np

from ..kit.moves import INVALID

JOINT = 9  # joint symbols: our move x 3 + theirs
ROUNDS = """
SELECT r.match_id, r.round, r.p1_move, r.p2_move
FROM rounds r JOIN matches m USING (match_id)
WHERE m.holdout_key >= ?
ORDER BY r.match_id, r.round
"""


def context(my: np.ndarray, opp: np.ndarray, end: int, k: int) -> int:
    """The row of the last k joint moves before `end` (base-9 digits)."""
    key = 0
    for t in range(end - k, end):
        key = key * JOINT + int(my[t]) * 3 + int(opp[t])
    return key


def train(path: str, k: int, holdout: float) -> np.ndarray:
    """Counts of the next move after every joint context of length k, over the
    dataset's training matches (holdout key at least `holdout`), both seats."""
    table = np.zeros((JOINT**k, 3))
    with duckdb.connect(path, read_only=True) as db:
        rows = db.execute(ROUNDS, [holdout]).fetchall()
    by_match: dict[int, list[tuple[int, int]]] = {}
    for match, _, a, b in rows:
        by_match.setdefault(match, []).append((a, b))
    for moves in by_match.values():
        a = np.array([m[0] for m in moves])
        b = np.array([m[1] for m in moves])
        for mine, theirs in ((a, b), (b, a)):
            _count(table, mine, theirs, k)
    return table


def _count(table: np.ndarray, my: np.ndarray, opp: np.ndarray, k: int) -> None:
    for t in range(k, len(opp)):
        seen = (my[t - k : t] == INVALID).any() or (opp[t - k : t] == INVALID).any()
        if seen or opp[t] == INVALID:
            continue
        table[context(my, opp, t, k), opp[t]] += 1.0


def write_block(table: np.ndarray, k: int, weight: float, path: str) -> None:
    """The table as a kit block (bots/blocks/): a PriorTable signal whose prior is
    its rows, normalised (an unseen row is uniform), played BEAT."""
    totals = table.sum(axis=1, keepdims=True)
    probs = np.where(totals > 0, table / np.maximum(totals, 1.0), 1.0 / 3.0)
    flat = ", ".join(f"{p:.4f}" for p in probs.ravel())
    with open(path, "w", encoding="utf-8") as out:
        out.write(
            "description: |\n"
            f"  Block: beats the opponent's next move after the last {k} joint moves by a\n"
            "  table trained on the move dataset (janken/experimental/pretrained.py),\n"
            "  WEIGHT observations' worth per context, plus this match's counts.\n"
            f"defaults:\n  WEIGHT: {weight}\n"
            "blueprint:\n  core:\n    Heuristic:\n"
            f"      signal: {{PriorTable: {{order: {k}, weight: $WEIGHT, prior: [{flat}]}}}}\n"
            "      rotation: BEAT\n"
        )


class Table:
    """Beats the opponent's likeliest next move by the table: a pre-trained
    prior (rows normalised, times `weight`) plus this match's counts."""

    def __init__(self, prior: np.ndarray, k: int, weight: float) -> None:
        totals = prior.sum(axis=1, keepdims=True)
        self.prior: np.ndarray = np.divide(
            prior, totals, out=np.zeros_like(prior), where=totals > 0
        )
        self.k: int = k
        self.weight: float = weight
        self.counts: np.ndarray = np.zeros_like(prior)
        self.rng: random.Random = random.Random()

    def reset(self, seed: int, rounds: int) -> None:
        del rounds
        self.counts[:] = 0.0
        self.rng = random.Random(seed)

    def move(self, my: np.ndarray, opp: np.ndarray, n: int) -> int:
        if n > self.k and opp[n - 1] != INVALID and my[n - 1] != INVALID:
            self.counts[context(my, opp, n - 1, self.k), opp[n - 1]] += 1.0
        if n < self.k:
            return self.rng.randrange(3)
        row = context(my, opp, n, self.k)
        belief = self.weight * self.prior[row] + self.counts[row]
        if belief.sum() <= 0:
            return self.rng.randrange(3)
        return (int(np.argmax(belief)) + 1) % 3
