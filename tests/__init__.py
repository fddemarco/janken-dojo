"""The test suite runs bots, stages and the referee as plain Python, on tiny inputs:
no numba compilation and no cache (see janken/settings.py). Run it from the
repository root with

    uv run python -m unittest discover -s tests -t .

so this package is imported (and the JIT switched off) before any test module.
Set JANKEN_JIT=on to run it compiled instead.
"""

import os

os.environ.setdefault("JANKEN_JIT", "off")
os.environ.setdefault("JANKEN_NUMBA_CACHE", "0")
