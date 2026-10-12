"""Head to head on a seed ladder: bot A vs bot B, A's share of rounds won.

    uv run python .claude/skills/evaluate/scripts/head_to_head.py A B \\
        --threshold 0.36 --rounds 250

A and B are bot files (with overrides, like `janken lab match`). Plays A vs B on
seeds 1..n for n = 10, 25, 50, 100, adding only the new seeds at each step, and
stops at the first step where the 95% CI of A's per-match share of rounds won is
clear of the threshold (above or below it): more seeds only for an inconclusive
result, never past 100. Prints one line per step. Nothing is stored.
"""

import argparse
import dataclasses
import math

from janken import settings
from janken.engine import play_pairs
from janken.lab.workflows import specs

LADDER = (10, 25, 50, 100)  # seeds per step, cumulative
Z95 = 1.96
CHANCE = 1 / 3  # the share of rounds a random move wins


@dataclasses.dataclass(frozen=True)
class Step:
    """One step of the ladder: A's per-match shares of rounds won and lost."""

    wins: tuple[float, ...]
    losses: tuple[float, ...]

    @property
    def mean(self) -> float:
        return sum(self.wins) / len(self.wins)

    @property
    def half_width(self) -> float:
        """Half the 95% CI of the mean share won (normal approximation)."""
        n = len(self.wins)
        var = sum((x - self.mean) ** 2 for x in self.wins) / (n - 1)
        return Z95 * math.sqrt(var / n)

    def clear_of(self, threshold: float) -> bool:
        """Whether the CI lies wholly above or below `threshold`."""
        return abs(self.mean - threshold) > self.half_width

    def line(self, threshold: float) -> str:
        n = len(self.wins)
        won = sum(w > lo for w, lo in zip(self.wins, self.losses, strict=True))
        lost = sum(w < lo for w, lo in zip(self.wins, self.losses, strict=True))
        verdict = "conclusive" if self.clear_of(threshold) else "inconclusive"
        return (
            f"{n} seeds: rounds won {self.mean:.1%}"
            f" [{self.mean - self.half_width:.1%}, {self.mean + self.half_width:.1%}],"
            f" lost {sum(self.losses) / n:.1%}, worst match {min(self.wins):.1%};"
            f" matches W{won} L{lost} D{n - won - lost};"
            f" vs {threshold:.0%}: {verdict}"
        )


def ladder(a: str, b: str, rounds: int, threshold: float) -> list[Step]:
    """Play the ladder until a step is clear of `threshold`; every step played."""
    pair = tuple(specs([a, b]))
    wins: list[float] = []
    losses: list[float] = []
    steps: list[Step] = []
    for n in LADDER:
        seeds = list(range(len(wins) + 1, n + 1))
        for result in play_pairs([pair] * len(seeds), rounds, seeds):
            wins.append(result.wins_a / rounds)
            losses.append(result.wins_b / rounds)
        steps.append(Step(tuple(wins), tuple(losses)))
        print(steps[-1].line(threshold), flush=True)
        if steps[-1].clear_of(threshold):
            break
    return steps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("a", help="the bot under test (a bot file)")
    parser.add_argument("b", help="its opponent (a bot file)")
    parser.add_argument(
        "--threshold",
        type=float,
        default=CHANCE,
        help="the share of rounds won the claim is about (default 1/3, chance)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=settings.config().match.rounds,
        help="rounds per match (default: match.rounds)",
    )
    args = parser.parse_args()
    ladder(args.a, args.b, args.rounds, args.threshold)


if __name__ == "__main__":
    main()
