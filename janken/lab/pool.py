"""Opponent pools: random draws from the bots directory.

A pool is drawn from the bots dir, or from the specs of a list file
(`sample_listed`: a gauntlet list of hard opponents, say). A pool member plays at
its defaults (the bot as submitted), unless the pool is
varied (`vary`): then a share of its members play a parameter variant, drawn
uniformly from their space files, so a bot tuned to the field's exact defaults
can't win by knowing them. Candidates' own files are never in their pool, so a
variant doesn't meet its own default.
A pool holds either the mocks or the bots they mock, never both (janken/mocks.py).
"""

import os
import random
from collections.abc import Iterable, Sequence

from .. import mocks
from ..engine.registry import discover
from ..match import bot_name
from ..spec import BotSpec, make_spec, parse_spec
from . import gauntlet
from . import space as spaces

VARIANT_DRAWS = 8  # draws of a valid variant before a member keeps its defaults


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


def read_list(path: str) -> list[str]:
    """The specs of a list file (a gauntlet list: one spec per line, `#` comments)."""
    with open(path, encoding="utf-8") as lines:
        found = [line.split("#")[0].strip() for line in lines]
    return [f for f in found if f]


def sample_listed(
    texts: Sequence[str],
    size: int,
    rng: random.Random,
    exclude_stems: Iterable[str] = (),
    allow_small: bool = False,
) -> list[BotSpec]:
    """A pool drawn from the specs of a list (`read_list`), parameter overrides
    included, rather than from the bots dir: candidates' stems excluded.

    Raises:
        SystemExit: the list has fewer eligible specs than the pool needs, unless
            `allow_small`.
    """
    skip = set(exclude_stems)
    specs = [s for s in map(parse_spec, texts) if s.stem not in skip]
    if len(specs) < size:
        if not allow_small:
            raise SystemExit(
                f"pool needs {size} bots but the list has only {len(specs)} eligible"
                " (candidates excluded); pass --allow-small-pool"
            )
        size = len(specs)
    return sorted(rng.sample(specs, size), key=lambda s: s.label)


def vary(
    pool: Sequence[BotSpec], spaces_dir: str, share: float, rng: random.Random
) -> list[BotSpec]:
    """The pool with each member, with chance `share`, played at a variant drawn
    uniformly from its space file (one that has none plays its defaults)."""
    out = []
    for spec in pool:
        if rng.random() >= share:
            out.append(spec)
            continue
        path = os.path.join(spaces_dir, bot_name(spec.path) + ".yaml")
        drawn = _variant(spaces.load(path), rng) if os.path.isfile(path) else {}
        out.append(make_spec(spec.path, drawn) if drawn else spec)
    return out


def _variant(space: spaces.Space, rng: random.Random) -> dict[str, float | int]:
    """One valid point of the space, drawn uniformly ({} if none is found)."""
    for _ in range(VARIANT_DRAWS):
        values = {n: gauntlet.quantiles(p, 1, rng)[0] for n, p in space.params.items()}
        if gauntlet.is_valid(values):
            return values
    return {}
