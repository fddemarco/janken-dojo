"""Opponent pools: random draws from the bots directory.

A pool member always plays at its defaults (the bot as submitted). Candidates'
own files are never in their pool, so a variant doesn't meet its own default.
A pool holds either the mocks or the bots they mock, never both (janken/mocks.py).
"""

import random
from collections.abc import Iterable

from .. import mocks
from ..engine.registry import discover
from ..match import bot_name
from ..spec import BotSpec, make_spec


def eligible(
    bots_dir: str, exclude_stems: Iterable[str] = (), use_mocks: bool = False
) -> list[str]:
    """Every bot file in bots_dir whose stem is not in exclude_stems, with either
    the mocks (`use_mocks`) or the bots they mock."""
    found = discover(bots_dir)
    skip = set(exclude_stems) | mocks.pool_excluded(found, use_mocks)
    return [p for p in found if bot_name(p) not in skip]


def sample_pool(
    bots_dir: str,
    size: int,
    rng: random.Random,
    exclude_stems: Iterable[str] = (),
    allow_small: bool = False,
    use_mocks: bool = False,
) -> list[BotSpec]:
    paths = eligible(bots_dir, exclude_stems, use_mocks)
    if len(paths) < size:
        if not allow_small:
            raise SystemExit(
                f"pool needs {size} bots but {bots_dir} has only {len(paths)} eligible"
                " (candidates excluded); add bots or pass --allow-small-pool"
            )
        size = len(paths)
    return [make_spec(p) for p in sorted(rng.sample(paths, size))]
