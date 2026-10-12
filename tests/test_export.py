"""Exported submission scripts: they play exactly like the kit, fleets included."""

import difflib
import importlib.util
import os
import pathlib
import random
import types
from collections.abc import Sequence

import pytest

from janken import botfile, export, library, sandbox, settings
from janken.engine import registry
from janken.kit import bot
from janken.kit import codes as c
from janken.kit.moves import INVALID, PAPER, ROCK, SCISSORS
from tests import data
from tests.test_stages import Runner

R, P, S, X = ROCK, PAPER, SCISSORS, INVALID
NAMES = ("rock", "paper", "scissors", "invalid")
MAX_ROUNDS = 64
CFG = settings.config()
RULES = sandbox.Rules(CFG.export.allowed_modules, CFG.export.banned_names)


def load(source: str, folder: str, name: str) -> types.ModuleType:
    """An exported script, imported from `folder`."""
    path = os.path.join(folder, name + ".py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(source)
    spec = importlib.util.spec_from_file_location(f"exported_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def script_moves(
    module: types.ModuleType, my: Sequence[int], opp: Sequence[int]
) -> list[int]:
    """The script's move at every round 0..len(my), given these histories."""
    mine = [NAMES[m] for m in my]
    theirs = [NAMES[o] for o in opp]
    return [NAMES.index(module.play(mine[:n], theirs[:n])) for n in range(len(my) + 1)]


def bot_file(folder: str, name: str, overlays: str = "", fleet: str = "") -> str:
    """A test bot playing SCISSORS, with these overlays and fleet section."""
    path = os.path.join(folder, name + ".yaml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            f"description: {name}, a test fleet bot\n"
            + (f"fleet: {fleet}\n" if fleet else "")
            + "blueprint:\n"
            "  core:\n"
            "    Heuristic: {signal: {Constant: [SCISSORS]}, rotation: COPY}\n"
            f"  overlays: [{overlays}]\n"
        )
    return path


FLEET = "{size: 3, supports: [first, second], handshake: [ROCK, PAPER], vigilant: true}"


class TestExportedBots:
    @pytest.fixture(autouse=True)
    def _folder(self, tmp_path: pathlib.Path) -> None:
        self.tmp = str(tmp_path)

    def exported(self, path: str) -> dict[str, str]:
        return export.scripts(path, MAX_ROUNDS)

    @pytest.mark.parametrize(
        "stem, rounds, seed, invalid_at",
        [
            ("frequency_v1", 9, 1, -1),
            pytest.param("smartbot_sims_v1", 9, 2, 5, marks=pytest.mark.heavy),
            # replays, Thompson draws
            pytest.param("anti_smartbot_sims_v1", 6, 3, -1, marks=pytest.mark.heavy),
            pytest.param(
                "gate_edge_v1", 8, 4, 3, marks=pytest.mark.heavy
            ),  # Gatekeeper
        ],
    )
    def test_exported_bots_play_exactly_like_the_kit(
        self, stem: str, rounds: int, seed: int, invalid_at: int
    ) -> None:
        path = data.bot(stem)
        found = botfile.read(path)
        history = random.Random(seed)
        my = [history.randrange(3) for _ in range(rounds)]
        opp = [history.randrange(3) for _ in range(rounds)]
        if invalid_at >= 0:
            opp[invalid_at] = X  # an invalid move reaches both as INVALID
        runner = Runner(library.read_blueprint(path), found.defaults)
        random.seed(seed)
        expected = runner.moves(my, opp)
        module = load(self.exported(path)[stem], self.tmp, stem)
        random.seed(seed)
        assert script_moves(module, my, opp) == expected, stem

    def test_a_crash_guard_forfeits_by_raising(self) -> None:
        module = load(
            self.exported(data.bot("frequency_v1"))["frequency_v1"],
            self.tmp,
            "f",
        )
        module.play([], [])
        with pytest.raises(RuntimeError):  # frequency crashes on an invalid move
            module.play(["rock"], ["invalid"])

    def test_scripts_pass_the_screening_and_import_no_numpy(self) -> None:
        source = self.exported(data.bot("frequency_v1"))["frequency_v1"]
        assert sandbox.scan(source, RULES) == []
        assert "numpy" not in source
        assert "global " not in source

    def test_a_champion_brings_its_fleets_supports_as_replicas(self) -> None:
        folder = self.tmp
        made = self.exported(bot_file(folder, "chief", fleet=FLEET))
        assert list(made) == ["chief", "first", "second"]
        diff = [
            line
            for line in difflib.ndiff(
                made["chief"].splitlines(), made["first"].splitlines()
            )
            if line[:1] in "+-"
        ]
        assert diff == [
            f"- TEAM_ROLE = {c.CHAMPION}  # CHAMPION",
            "+ # first",
            f"+ TEAM_ROLE = {c.SUPPORT}  # SUPPORT",
        ]
        chief = load(made["chief"], folder, "chief")
        first = load(made["first"], folder, "first")
        mine: list[str] = []
        theirs: list[str] = []
        for _ in range(12):
            a, b = chief.play(mine, theirs), first.play(theirs, mine)
            mine.append(a)
            theirs.append(b)
        assert mine[-2:] == ["paper", "paper"]  # the support throws its match
        assert theirs[-2:] == ["rock", "rock"]

    def test_a_fleet_of_n_bots_is_n_scripts_named_after_the_champion(self) -> None:
        fleet = "{size: 4, handshake: [SCISSORS]}"
        made = self.exported(bot_file(self.tmp, "chief", fleet=fleet))
        assert list(made) == [
            "chief",
            "chief_support_1",
            "chief_support_2",
            "chief_support_3",
        ]

    def test_a_team_outside_a_fleet_section_is_not_exported(self) -> None:
        path = bot_file(self.tmp, "spy", "{Team: {role: IMPOSTOR, handshake: [ROCK]}}")
        with pytest.raises(export.ExportError):
            self.exported(path)

    def test_a_new_match_starts_from_fresh_state(self) -> None:
        folder = self.tmp
        chief = load(
            self.exported(bot_file(folder, "chief", fleet=FLEET))["chief"],
            folder,
            "chief",
        )
        opening = chief.play([], [])
        stranger = chief.play([opening], ["paper"])  # breaks the handshake
        assert stranger == "scissors"
        assert chief.play([], []) == opening  # a new match: the handshake again

    def test_a_match_longer_than_the_export_is_an_error(self) -> None:
        module = load(
            self.exported(data.bot("rock_v1"))["rock_v1"],
            self.tmp,
            "rock_v1",
        )
        with pytest.raises(ValueError):
            module.play(["rock"] * MAX_ROUNDS, ["rock"] * MAX_ROUNDS)

    def test_the_role_lives_in_the_team_overlays_record(self) -> None:
        compiled = bot.Blueprint(overlays=(bot.Team(bot.SUPPORT, (R,)),)).compile({})
        spec = [int(v) for v in compiled.spec]
        assert [spec[x] for x in export.team_role_cells(spec)] == [c.SUPPORT]
        prm = [float(v) for v in registry.param_vector(data.bot("rock_v1"))]
        with pytest.raises(export.ExportError):
            export.script(compiled, prm, [], [], MAX_ROUNDS)  # its role is missing


class TestRewrite:
    def test_numpy_and_kit_names_become_plain_python(self) -> None:
        out = export.rewrite_module(
            "demo",
            "import numpy as np\n"
            "from . import codes as c\n"
            "from .jit import kernel\n"
            "LIMIT = 3\n"
            "@kernel\n"
            "def make(n: int, x: np.ndarray) -> np.ndarray:\n"
            '    """Doc."""\n'
            "    out = np.zeros(n, np.int64)\n"
            "    out[0] = c.NO_MOVE + x.size + LIMIT\n"
            "    return out\n",
        )
        assert out.source == (
            "demo_LIMIT = 3\n\n"
            "def demo_make(n, x):\n"
            "    out = [0] * n\n"
            "    out[0] = codes_NO_MOVE + len(x) + demo_LIMIT\n"
            "    return out"
        )
        assert out.reads == {"codes_NO_MOVE", "demo_LIMIT"}

    @pytest.mark.parametrize(
        "source",
        [
            "import numpy as np\ndef f(n):\n    return np.ones(n)\n",
            "import os\n",
            "from .blueprint import Team\n",
            "X = 0\ndef f():\n    global X\n    X = 1\n",
        ],
    )
    def test_what_cant_be_exported_is_refused(self, source: str) -> None:
        with pytest.raises(export.ExportError):
            export.rewrite_module("demo", source)
