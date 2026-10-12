"""Test-owned data: a frozen bot library, its space files and a sample notebook.

The tests never read the lab's own bots/, spaces/ or research/, so editing,
retiring or renaming a bot there never breaks one. These files are a snapshot:
change them only to test something new. The space files name their bots relative
to the repository root, where the suite runs (tests/conftest.py).
"""

import os

from janken.engine import registry

DATA = os.path.relpath(os.path.dirname(os.path.abspath(__file__)))
BOTS_DIR = os.path.join(DATA, "bots")
SPACES_DIR = os.path.join(DATA, "spaces")
RESEARCH = os.path.join(DATA, "research")


def bot(stem: str) -> str:
    """The test library's bot file named `stem`."""
    return registry.find(BOTS_DIR, stem)
