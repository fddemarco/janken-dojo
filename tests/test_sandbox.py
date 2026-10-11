"""The tournament's screening of a submission script."""

import unittest

from janken import sandbox

RULES = sandbox.Rules(allowed_modules=("math", "random"), banned_names=("open", "eval"))
PLAY = "def play(my_moves, opp_moves):\n    return 'rock'\n"


def messages(source: str) -> list[str]:
    return [v.message for v in sandbox.scan(source, RULES)]


class ScanTest(unittest.TestCase):
    def test_a_clean_bot_passes(self) -> None:
        source = "import math\nfrom random import random\nSTATE = {}\n" + PLAY
        self.assertEqual(messages(source), [])

    def test_imports_outside_the_allowlist_are_refused(self) -> None:
        self.assertEqual(
            messages("import os\nfrom sys import argv\nfrom . import x\n" + PLAY),
            [
                "import of 'os' is not allowed",
                "import from 'sys' is not allowed",
                "relative imports are not allowed",
            ],
        )

    def test_banned_names_and_dunders_are_refused(self) -> None:
        source = (
            PLAY + "eval('1')\nx = __builtins__\ny = play.__code__\nz = '__class__'\n"
        )
        self.assertEqual(
            messages(source),
            [
                "use of 'eval' is not allowed",
                "reference to '__builtins__' is not allowed",
                "dunder attribute access '.__code__' is not allowed",
                "string literal contains dunder '__class__'",
            ],
        )

    def test_the_main_guard_is_allowed(self) -> None:
        self.assertEqual(messages(PLAY + "if __name__ == '__main__':\n    pass\n"), [])

    def test_global_and_nonlocal_are_refused(self) -> None:
        source = PLAY + "N = 0\ndef bump():\n    global N\n    N += 1\n"
        self.assertEqual(messages(source), ["the `global` keyword is not allowed"])
        nested = (
            PLAY + "def outer():\n    n = 0\n    def inner():\n        nonlocal n\n"
        )
        self.assertEqual(messages(nested), ["the `nonlocal` keyword is not allowed"])

    def test_a_bot_needs_play_and_valid_syntax(self) -> None:
        self.assertEqual(messages("x = 1\n"), ["no top-level `play` function"])
        self.assertEqual(len(messages("def play(:\n")), 1)


if __name__ == "__main__":
    unittest.main()
