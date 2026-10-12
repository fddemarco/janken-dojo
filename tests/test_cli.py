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

from janken import botfile, settings
from janken.cli import app, options
from janken.engine import registry
from janken.notebook import ideas, notes
from tests import data

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
LIGHT_BOTS = (
    "rock_v1",
    "nash_v1",
    "cycler_v1",
    "wsls_v1",
    "copycat_v1",
    "reactionary_v1",
    "biased_v1",
)
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


def test_the_reference_renders_every_command(tmp_path: pathlib.Path) -> None:
    from janken.cli import reference

    text = reference.render()
    for name, _ in COMMANDS:
        assert f"`uv run janken {name}`" in text, name


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
    """One lab for the whole class: light bots and a copy of the sample notebook."""
    cls = request.cls
    cls.root = str(tmp_path_factory.mktemp("lifecycle"))
    cls.bots = os.path.join(cls.root, "bots")
    cls.notebook = os.path.join(cls.root, "research")
    os.makedirs(cls.bots)
    os.makedirs(cls.notebook)
    for stem in LIGHT_BOTS:
        shutil.copy(data.bot(stem), cls.bots)
    for name in ("ideas.md", "insights.md"):
        shutil.copy(os.path.join(data.RESEARCH, name), cls.notebook)
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
            "6",
            "--pool-size",
            "3",
            "--seed",
            "1",
            "--cache",
            "off",
            "--progress",
            "off",
        ]

    def bot(self, stem: str) -> str:
        return registry.find(self.bots, stem)

    @pytest.mark.heavy
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
            "cycler_v1",
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
            self.bot("cycler_v1"),
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
        assert "--mode full" in note.section("Command")  # the run, reproduced

        self.run_ok("evaluate", "--note", "1", "--round-robins", "3")  # grows its run
        grown = notes.find(self.notebook, "1")
        assert grown.run_ids == note.run_ids
        assert "3 of 3 round robin(s)" in grown.section("Results")

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

    @pytest.mark.heavy
    def test_the_low_level(self) -> None:
        out = self.run_ok(
            "lab",
            "experiment",
            self.bot("cycler_v1"),
            self.bot("wsls_v1"),
            "--name",
            "adhoc",
        )
        run_id = out.strip().splitlines()[-1].split()[-1]
        assert run_id in self.run_ok("lab", "runs")
        assert "Candidates vs pool" in self.run_ok("lab", "report", run_id)
        assert "cycler_v1" in self.run_ok("lab", "history", "cycler_v1")
        assert "wsls" in self.run_ok("lab", "leaderboard")
        assert "seed" in self.run_ok(
            "lab", "match", self.bot("rock_v1"), self.bot("cycler_v1")
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

    @pytest.mark.heavy
    def test_profiling(self) -> None:
        target = [
            "--",
            "lab",
            "match",
            self.bot("rock_v1"),
            self.bot("cycler_v1"),
            "--rounds",
            "5",
            "--workspace",
            os.path.join(self.root, "target"),
        ]
        flags = ["--no-jit", "--no-warmup"]
        profiled = self.run_ok("lab", "profile", "run", *flags, *target)
        assert "| hotspot |" in profiled
        assert "worth optimizing" in profiled
        again = self.run_ok("lab", "profile", "run", *flags, *target)
        assert "already profiled" in again  # nothing changed: not profiled again
        timed = self.run_ok(
            "lab", "profile", "bench", *flags, "--repeats", "1", *target
        )
        assert "bench" in timed
        assert "current" in self.run_ok("lab", "profile", "list")
        assert "flame graph" in self.run_ok("lab", "profile", "show", "profile")

    def run_ok(self, *args: str) -> str:
        """Run a command with the common flags (before any `--` target)."""
        cut = args.index("--") if "--" in args else len(args)
        result = self.runner.invoke(app, [*args[:cut], *self.common(), *args[cut:]])
        assert result.exit_code == 0, f"{args}: {result.output}{result.exception!r}"
        return result.output

    def test_a_fleet_is_scaffolded_on_a_bot_and_exported(self) -> None:
        os.makedirs(os.path.join(self.bots, "blocks"))  # the library's root
        out = os.path.join(self.root, "exports")
        flags = ("--folder", "inactive/fleets", "--out", out, "--size", "3")
        made = self.run_ok("bot", "fleet", "cycler_v1", "chief", *flags)
        found = botfile.read(os.path.join(self.bots, "inactive/fleets", "chief.yaml"))
        assert found.fleet.supports == ("chief_support_1", "chief_support_2")
        assert len(found.fleet.handshake) == settings.config().fleet.handshake_length
        assert sorted(os.listdir(os.path.join(out, "chief"))) == [
            "chief.py",
            "chief_support_1.py",
            "chief_support_2.py",
        ]
        assert "created" in made
        refused = self.runner.invoke(
            app,
            ["bot", "fleet", "cycler_v1", "other", *flags, "--support", "a"],
        )
        assert refused.exit_code == 2  # a fleet of 3 names 2 supports

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
                "rock_v1",
                "--from",
                "nash_v1",
                "--description",
                "x",
                *self.common(),
            ],
        )
        assert result.exit_code == 2  # a stem is never reused


SPECIES_FIELD = ("rock_v1", "cycler_v1", "wsls_v1", "copycat_v1", "reactionary_v1")
SPECIES_TABLE = """# Species

| species | level | current | versions | variants |
|---|---|---|---|---|
""" + "".join(
    f"| `{s[:-3]}` | L1 | `{s}` | `{s[:-3]}` --> v1 | |\n" for s in SPECIES_FIELD
)


class TestSpeciesLifecycle:
    """A kept bot classified end to end: a variant, then a new species (JIT off)."""

    @pytest.fixture(autouse=True)
    def _lab(self, tmp_path: pathlib.Path) -> None:
        self.root = str(tmp_path)
        self.bots = os.path.join(self.root, "bots")
        self.notebook = os.path.join(self.root, "research")
        self.spaces = os.path.join(self.root, "spaces")
        os.makedirs(os.path.join(self.bots, "l1"))
        os.makedirs(self.notebook)
        for stem in SPECIES_FIELD:
            shutil.copy(
                data.bot(stem),
                os.path.join(self.bots, "l1"),
            )
        for name in ("ideas.md", "insights.md"):
            shutil.copy(os.path.join(data.RESEARCH, name), self.notebook)
        with open(os.path.join(self.notebook, "species.md"), "w") as f:
            f.write(SPECIES_TABLE)
        self.runner = CliRunner()

    def common(self) -> list[str]:
        return [
            "--workspace",
            os.path.join(self.root, "experiments"),
            "--notebook",
            self.notebook,
            "--bots-dir",
            self.bots,
            "--spaces-dir",
            self.spaces,
            "--effort",
            "quick",
            "--rounds",
            "6",
            "--pool-size",
            "3",
            "--seed",
            "1",
            "--cache",
            "off",
            "--progress",
            "off",
        ]

    def invoke(self, *args: str) -> Result:
        return self.runner.invoke(app, [*args, *self.common()])

    def run_ok(self, *args: str) -> str:
        result = self.invoke(*args)
        assert result.exit_code == 0, f"{args}: {result.output}{result.exception!r}"
        return result.output

    def json_of(self, *args: str) -> Any:
        result = self.invoke(*args, "--format", "json")
        assert result.exit_code == 0, f"{args}: {result.output}{result.exception!r}"
        return json.loads(result.stdout)

    def keep(self, stem: str, template: str) -> str:
        """A new bot from `template`, evaluated and kept; its note's number."""
        self.run_ok("bot", "new", stem, "--from", template, "--description", "A test.")
        self.run_ok(
            "evaluate",
            registry.find(self.bots, stem),
            "--hypothesis",
            "it holds its own",
        )
        number = f"{notes.all_notes(self.notebook)[-1].number:04d}"
        self.run_ok("verdict", number, "keep", "--summary", "kept for the test")
        return number

    @pytest.mark.heavy
    def test_a_twin_is_a_variant_and_a_stranger_a_new_species(self) -> None:
        stems = [registry.find(self.bots, s) for s in SPECIES_FIELD]
        self.run_ok("lab", "dataset", "add", *stems)
        ranked = self.run_ok("species", "compare", "cycler_v1", "--split", "all")
        assert "| `rock_v1` | L1 |" in ranked
        assert "`cycler_v1` |" not in ranked  # the bot itself is left out
        assert "## Alike pairs" in self.run_ok("species", "census", "--split", "all")
        refused = self.invoke("bot", "new", "cycler_v2", "--from", "cycler_v1")
        assert refused.exit_code == 2  # versions come from classify only

        twin = self.keep("twin", "cycler_v1")
        status = self.json_of("status")
        assert status["next"]["action"] == "classify"
        out = self.json_of("species", "classify", twin, "--split", "all")
        assert out["outcome"] == "variant"  # alike cycler_v1, and no better
        assert out["incumbent"] == "cycler_v1"
        assert os.path.isfile(
            os.path.join(self.bots, "inactive", "legacy", "twin.yaml")
        )
        assert not os.path.exists(os.path.join(self.spaces, "twin.yaml"))
        assert "`twin`" in self.run_ok("species", "list")
        assert notes.find(self.notebook, twin).species.startswith("`twin` (variant")
        assert self.json_of("status")["next"]["action"] != "classify"

        coin = self.keep("coin", data.bot("nash_v1"))
        unnamed = self.invoke("species", "classify", coin, "--split", "all")
        assert unnamed.exit_code == 2  # a new species needs a name
        assert "--name" in unnamed.output
        self.run_ok("species", "classify", coin, "--split", "all", "--name", "coin")
        assert registry.find(self.bots, "coin_v1").endswith(
            os.path.join("l1", "coin_v1.yaml")
        )
        found = {s["name"]: s for s in self.json_of("species", "list")}
        assert found["coin"]["current"] == "coin_v1"
        assert found["coin"]["versions"].startswith("`coin` ([")
        assert found["coin"]["versions"].endswith(") --> v1")
