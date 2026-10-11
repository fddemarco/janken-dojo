"""A match's rules and its result."""

import dataclasses
import os

# Invalid moves a bot may return before it forfeits the match, counted over the
# whole match rather than consecutively. One is a slip and costs the round; three
# is a broken bot.
INVALID_MOVE_LIMIT = 3


@dataclasses.dataclass
class MatchResult:
    bot_a: str
    bot_b: str
    wins_a: int = 0
    wins_b: int = 0
    draws: int = 0
    forfeit_a: str | None = None  # reason bot_a forfeited, if it did
    forfeit_b: str | None = None
    # Every scored round, two characters each: bot_a's move then bot_b's,
    # "r" / "p" / "s", or "x" for an invalid move.
    moves: str = ""

    @property
    def winner(self) -> str | None:
        """Name of the winning bot, or None on a draw."""
        if self.forfeit_a and not self.forfeit_b:
            return self.bot_b
        if self.forfeit_b and not self.forfeit_a:
            return self.bot_a
        if self.forfeit_a and self.forfeit_b:
            return None
        if self.wins_a > self.wins_b:
            return self.bot_a
        if self.wins_b > self.wins_a:
            return self.bot_b
        return None

    @property
    def is_draw(self) -> bool:
        return self.winner is None


def bot_name(path: str) -> str:
    """A bot's name: its file's stem."""
    return os.path.splitext(os.path.basename(path))[0]
