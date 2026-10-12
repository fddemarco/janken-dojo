"""janken/cli: the command line, its documentation, its defaults, and the lifecycle."""

import json
import os
import pathlib
import re
import shutil
import tomllib
from collections.abc import Iterator
from typing import Any

import pytest
import typer.main
from typer.testing import CliRunner, Result

from janken import settings
from janken.cli import app, options
from janken.engine import registry
from janken.notebook import ideas, notes

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
LIGHT_BOTS = ("rock", "nash", "cycler", "wsls", "copycat", "reactionary", "biased")
CONFIG_KEY = re.compile(r"\(config: ([a-z_.]+)\)")
# Defaults that mean "none" or "off" rather than a value someone chose.
NEUTRAL: tuple[object, ...] = ("", 0, False, None, "auto")


def commands(group: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[str, Any]]:
    """Every leaf command of the click tree, with its full name."""
    for name, command in sorted(group.commands.items()):
        if hasattr(command, "commands"):
            yield from commands(command, (*path, name))
        else:
            yield " ".join((*path, name)), command


COMMANDS: list[tuple[str, Any]] = list(commands(typer.main.get_command(app)))
PARAMS: list[tuple[str, Any]] = [
    (name, param)
    for name, command in COMMANDS
    for param in command.params
    if param.name != "help"
]


def _param_id(case: tuple[str, Any]) -> str:
    return f"{case[0]}:{case[1].name}"


def test_there_are_commands() -> None:
    assert len(COMMANDS) > 30


@pytest.mark.parametrize("name, command", COMMANDS, ids=[n for n, _ in COMMANDS])
def test_every_command_is_documented(name: str, command: Any) -> None:
    assert command.help, f"{name} has no docstring"


@pytest.mark.parametrize("case", PARAMS, ids=_param_id)
def test_every_parameter_is_documented(case: tuple[str, Any]) -> None:
    assert getattr(case[1], "help", ""), "undocumented"


@pytest.mark.parametrize("case", PARAMS, ids=_param_id)
def test_no_default_is_hard_coded(case: tuple[str, Any]) -> None:
    """A default is the setting its help names, or a neutral 'none / off'."""
    param = case[1]
    default = param.default
    if callable(default):
        return  # a list's empty factory
    key = CONFIG_KEY.search(getattr(param, "help", "") or "")
    if key:
        value = settings.entry(key.group(1), settings.config()).value
        assert str(default) == str(value)
    else:
        assert default in NEUTRAL


@pytest.mark.parametrize(
    "enum_type", list(options.ENUMS), ids=lambda enum_type: enum_type.__name__
)
def test_the_cli_enums_match_the_settings(enum_type: Any) -> None:
    assert tuple(e.value for e in enum_type) == options.ENUMS[enum_type]


@pytest.mark.parametrize(
    "name, command",
    [(n, c) for n, c in COMMANDS if not n.startswith("config")],
    ids=[n for n, _ in COMMANDS if not n.startswith("config")],
)
def test_every_lab_command_has_the_common_flags(name: str, command: Any) -> None:
    have = {p.name for p in command.params}
    assert set(options.COMMON_NAMES) <= have


DOCS = (
    "README.md",
    "research/README.md",
    "research/experiments/TEMPLATE.md",
    ".claude/CLAUDE.md",
)
CODE = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)
COMMAND = re.compile(r"\bjanken((?: [a-z][a-z-]*)+)")


def documents() -> list[str]:
    """Every doc and skill that names commands (the generated reference aside)."""
    found = [os.path.join(ROOT, p) for p in DOCS]
    found += [
        os.path.join(ROOT, "docs", n)
        for n in sorted(os.listdir(os.path.join(ROOT, "docs")))
        if n.endswith(".md") and n != "cli-reference.md"
    ]
    skills = os.path.join(ROOT, ".claude", "skills")
    found += [os.path.join(skills, d, "SKILL.md") for d in sorted(os.listdir(skills))]
    return found


@pytest.mark.parametrize(
    "path", documents(), ids=lambda path: os.path.relpath(path, ROOT)
)
def test_the_docs_and_skills_only_name_commands_that_exist(
    path: str, subtests: pytest.Subtests
) -> None:
    tree = typer.main.get_command(app)
    with open(path, encoding="utf-8") as f:
        code = " ".join(CODE.findall(f.read()))
    for words in COMMAND.findall(code):
        with subtests.test(command=words.strip()):
            node: Any = tree
            for i, word in enumerate(words.split()):
                children = getattr(node, "commands", {})
                if word not in children:
                    assert i > 0, f"no command `janken {word}`"
                    break
                node = children[word]


@pytest.mark.skipif(
    os.path.isfile(settings.LOCAL_FILE), reason="janken.local.toml changes the defaults"
)
def test_the_reference_is_current() -> None:
    from janken.cli import reference

    with open(reference.PATH, encoding="utf-8") as f:
        assert f.read() == reference.render(), (
            "regenerate it: uv run python -m janken.cli.reference"
        )


class TestConfigCommand:
    @pytest.fixture(autouse=True)
    def _config_copy(self, tmp_path: pathlib.Path) -> Iterator[None]:
        """A copy of janken.toml (and no local file) for each test."""
        saved = (settings.CONFIG_FILE, settings.LOCAL_FILE)
        settings.CONFIG_FILE = str(tmp_path / "janken.toml")
        settings.LOCAL_FILE = str(tmp_path / "janken.local.toml")
        shutil.copy(saved[0], settings.CONFIG_FILE)
        settings.reload()
        self.runner = CliRunner()
        yield
        settings.CONFIG_FILE, settings.LOCAL_FILE = saved
        settings.reload()

    def invoke(self, *args: str) -> Result:
        return self.runner.invoke(app, ["config", *args])

    def test_set_get_and_check(self) -> None:
        with open(settings.CONFIG_FILE) as f:
            before = f.read()
        assert self.invoke("set", "match.rounds", "50").exit_code == 0
        with open(settings.CONFIG_FILE) as f:
            after = f.read()
        assert after == before.replace("rounds = 200", "rounds = 50")
        assert self.invoke("get", "match.rounds").output.strip() == "50"
        assert self.invoke("check").exit_code == 0

    @pytest.mark.parametrize(
        "args",
        [("match.rounds", "0"), ("match.rounds", "x"), ("match.colour", "1")],
    )
    def test_bad_values_change_nothing(self, args: tuple[str, str]) -> None:
        with open(settings.CONFIG_FILE) as f:
            before = f.read()
        assert self.invoke("set", *args).exit_code == 2
        with open(settings.CONFIG_FILE) as f:
            assert f.read() == before

    def test_local_overrides_and_unset(self) -> None:
        assert self.invoke("set", "--local", "effort.quick.trials", "3").exit_code == 0
        with open(settings.LOCAL_FILE, "rb") as f:
            assert tomllib.load(f) == {"effort": {"quick": {"trials": 3}}}
        assert settings.config().effort.quick.trials == 3
        assert self.invoke("unset", "effort.quick.trials").exit_code == 0
        assert settings.config().effort.quick.trials == 10
        assert self.invoke("unset", "effort.quick.trials").exit_code == 2

    def test_show_lists_values_and_help(self) -> None:
        shown = self.invoke("show", "tuning").output
        assert "tuning.sampler" in shown
        assert "# how trials are chosen" in shown
        data = json.loads(self.invoke("show", "match", "--format", "json").output)
        assert data == {"match.rounds": 200}


@pytest.fixture(scope="class")
def lifecycle_lab(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """One lab for the whole class: light bots and a copy of the notebook."""
    cls = request.cls
    cls.root = str(tmp_path_factory.mktemp("lifecycle"))
    cls.bots = os.path.join(cls.root, "bots")
    cls.notebook = os.path.join(cls.root, "research")
    os.makedirs(cls.bots)
    os.makedirs(cls.notebook)
    for stem in LIGHT_BOTS:
        shutil.copy(registry.find(os.path.join(ROOT, "bots"), stem), cls.bots)
    for name in ("ideas.md", "insights.md"):
        shutil.copy(os.path.join(ROOT, "research", name), cls.notebook)
    cls.runner = CliRunner()


@pytest.mark.usefixtures("lifecycle_lab")
class TestLifecycle:
    """The high-level loop and the low level, end to end, on light bots (JIT off)."""

    root: str
    bots: str
    notebook: str
    runner: CliRunner

    def common(self) -> list[str]:
        return [
            "--workspace",
            os.path.join(self.root, "experiments"),
            "--notebook",
            self.notebook,
            "--bots-dir",
            self.bots,
            "--spaces-dir",
            os.path.join(self.root, "spaces"),
            "--effort",
            "quick",
            "--rounds",
            "10",
            "--pool-size",
            "3",
            "--seed",
            "1",
            "--cache",
            "off",
            "--progress",
            "off",
        ]

    def run_ok(self, *args: str) -> str:
        result = self.runner.invoke(app, [*args, *self.common()])
        assert result.exit_code == 0, f"{args}: {result.output}{result.exception!r}"
        return result.output

    def bot(self, stem: str) -> str:
        return registry.find(self.bots, stem)

    def test_the_loop(self) -> None:
        added = json.loads(
            self.run_ok(
                "idea",
                "add",
                "Twin cycler",
                "--priority",
                "P2",
                "--motivation",
                "a test",
                "--format",
                "json",
            )
        )
        number = added["number"]
        made = self.run_ok(
            "bot",
            "new",
            "twin",
            "--from",
            "cycler",
            "--description",
            "A cycler twin.",
            "--idea",
            str(number),
        )
        assert "spaces" in made  # cycler has defaults, so a space file too
        assert ideas.load(self.notebook).get(number).state == ideas.IN_PROGRESS
        assert os.path.dirname(self.bot("twin")) == os.path.join(self.bots, "l1")
        assert "ok twin" in self.run_ok("bot", "check", "twin")
        assert "twin" in self.run_ok("bot", "list")
        assert "A cycler twin." in self.run_ok("bot", "show", "twin")

        out = self.run_ok(
            "evaluate",
            self.bot("twin"),
            "--baseline",
            self.bot("cycler"),
            "--hypothesis",
            "the twin plays exactly like cycler",
            "--idea",
            str(number),
        )
        assert "Paired comparisons" in out
        note = notes.find(self.notebook, "1")
        assert note.status == notes.RUN
        assert note.run_ids
        assert "lab experiment" in note.section("Command")

        refused = self.runner.invoke(
            app,
            [
                "insight",
                "add",
                "--note",
                "1",
                "--finding",
                "f",
                "--mechanism",
                "m",
                "--implication",
                "i",
                *self.common(),
            ],
        )
        assert refused.exit_code == 2  # identical bots: the CI is [0, 0]

        self.run_ok("verdict", "1", "drop", "--summary", "identical, as expected")
        assert notes.find(self.notebook, "1").status == notes.ANALYZED
        assert ideas.load(self.notebook).get(number).state == ideas.DROPPED
        assert "Next step" in self.run_ok("status")

        self.run_ok(
            "tune",
            self.bot("twin"),
            "--hypothesis",
            "tuning finds nothing on a twin",
            "--trials",
            "2",
            "--validate-top",
            "1",
            "--validate-round-robins",
            "1",
        )
        tuned = notes.find(self.notebook, "2")
        assert (tuned.kind, tuned.status) == (notes.TUNING, notes.RUN)
        assert "Validations" in tuned.section("Results")
        assert tuned.study in self.run_ok("lab", "study", "list")
        assert "vs defaults" in self.run_ok("lab", "study", "show", tuned.study)

    def test_the_low_level(self) -> None:
        out = self.run_ok(
            "lab", "experiment", self.bot("cycler"), self.bot("wsls"), "--name", "adhoc"
        )
        run_id = out.strip().splitlines()[-1].split()[-1]
        assert run_id in self.run_ok("lab", "runs")
        assert "Candidates vs pool" in self.run_ok("lab", "report", run_id)
        assert "cycler" in self.run_ok("lab", "history", "cycler")
        assert "wsls" in self.run_ok("lab", "leaderboard")
        assert "seed" in self.run_ok(
            "lab", "match", self.bot("rock"), self.bot("cycler")
        )
        counted = self.run_ok(
            "lab",
            "query",
            "SELECT count(*) AS n FROM runs WHERE run_id = '" + run_id + "'",
        )
        assert "| 1 |" in counted
        assert "run id" in self.run_ok("lab", "resume", run_id)
        nowhere = [*self.common(), "--workspace", os.path.join(self.root, "none")]
        result = self.runner.invoke(app, ["lab", "study", "list", *nowhere])
        assert "(no studies yet)" in result.output

    def test_errors_are_messages_not_tracebacks(self) -> None:
        result = self.runner.invoke(
            app, ["verdict", "999", "keep", "--summary", "x", *self.common()]
        )
        assert result.exit_code == 2
        assert isinstance(result.exception, SystemExit)
        result = self.runner.invoke(
            app,
            [
                "bot",
                "new",
                "rock",
                "--from",
                "nash",
                "--description",
                "x",
                *self.common(),
            ],
        )
        assert result.exit_code == 2  # a stem is never reused
