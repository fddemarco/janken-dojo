"""Progress bars for long commands, on stderr.

Whether they show is `[tool.janken] progress` (auto: only on an interactive
terminal), overridden by $JANKEN_PROGRESS (janken/settings.py). Log lines printed
while a bar is open go through `log`, so they don't tear the bar. `interrupted`
tells a Ctrl-C apart from a real error.
"""

import os
import sys

import tqdm

from . import settings


def enabled() -> bool:
    """Whether bars show right now (stderr is read at call time)."""
    return settings.progress_enabled(os.environ, sys.stderr.isatty())


def bar(total: int, desc: str, unit: str) -> tqdm.tqdm:
    """A bar of `total` steps (0: open-ended), hidden when progress is off."""
    return tqdm.tqdm(
        total=total or None,  # tqdm's API: None means an unknown total
        desc=desc,
        unit=unit,
        file=sys.stderr,
        disable=not enabled(),
        dynamic_ncols=True,
    )


def log(text: str) -> None:
    """Print a line to stderr above any open bar."""
    tqdm.tqdm.write(text, file=sys.stderr)


def interrupted(exc: BaseException) -> bool:
    """Whether `exc` is Ctrl-C, or an error raised because of one (numba wraps a
    KeyboardInterrupt raised inside a compiled call in a SystemError)."""
    seen: BaseException | None = exc  # the chain ends in None
    while seen is not None:
        if isinstance(seen, KeyboardInterrupt):
            return True
        seen = seen.__cause__ or seen.__context__
    return False
