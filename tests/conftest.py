"""The test suite runs bots, stages and the referee as plain Python, on tiny inputs:
no numba compilation and no cache (see janken/settings.py). Run it from the
repository root with

    uv run pytest

Heavy tests (`@pytest.mark.heavy`) are deselected by default (pyproject.toml); run
them with `uv run pytest -m heavy`.

pytest loads this file before it imports any test module, so the JIT is off by
then. Set JANKEN_JIT=on to run it compiled instead. Timing spans are off too
(janken/telemetry.py): its tests turn them on themselves.

The suite depends on the package only, never on the lab's state: its configuration
is tests/data/janken.toml (never janken.toml or janken.local.toml), and its bots,
spaces and notebook are tests/data's (tests/data/__init__.py).
"""

import os

os.environ.setdefault("JANKEN_JIT", "off")
os.environ.setdefault("JANKEN_NUMBA_CACHE", "0")
os.environ.setdefault("JANKEN_SPANS", "off")
# Before janken.settings is imported; subprocesses (the profiler's) inherit them.
os.environ["JANKEN_CONFIG"] = os.path.join(
    os.path.dirname(__file__), "data", "janken.toml"
)
os.environ["JANKEN_LOCAL_CONFIG"] = ""  # no local overrides
