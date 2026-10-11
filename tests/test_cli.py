"""janken/cli: the command line, its documentation, its defaults, and the lifecycle."""

import json
import os
import re
import shutil
import tempfile
import tomllib
import unittest
from collections.abc import Iterator
from typing import Any

import typer.main
from typer.testing import CliRunner, Result

from janken import settings
from janken.cli import app, options
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


class DocumentationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = typer.main.get_command(app)

    def test_every_command_and_parameter_is_documented(self) -> None:
        found = list(commands(self.tree))
        self.assertGreater(len(found), 30)
        for name, command in found:
            with self.subTest(command=name):
                self.assertTrue(command.help, f"{name} has no docstring")
            for param in command.params:
                if param.name == "help":
                    continue
                with self.subTest(command=name, param=param.name):
                    self.assertTrue(getattr(param, "help", ""), "undocumented")

    def test_no_default_is_hard_coded(self) -> None:
        """A default is the setting its help names, or a neutral 'none / off'."""
        config = settings.config()
        for name, command in commands(self.tree):
            for param in command.params:
                default = param.default
                if param.name == "help" or callable(default):
                    continue  # a list's empty factory
                with self.subTest(command=name, param=param.name):
                    key = CONFIG_KEY.search(getattr(param, "help", "") or "")
                    if key:
                        value = settings.entry(key.group(1), config).value
                        self.assertEqual(str(default), str(value))
                    else:
                        self.assertIn(default, NEUTRAL)

    def test_the_cli_enums_match_the_settings(self) -> None:
        for enum_type, values in options.ENUMS.items():
            with self.subTest(enum=enum_type.__name__):
                self.assertEqual(tuple(e.value for e in enum_type), values)

    def test_every_lab_command_has_the_common_flags(self) -> None:
        for name, command in commands(self.tree):
            if name.startswith("config"):
                continue
            with self.subTest(command=name):
                have = {p.name for p in command.params}
                self.assertLessEqual(set(options.COMMON_NAMES), have)


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


class DocsTest(unittest.TestCase):
    def test_the_docs_and_skills_only_name_commands_that_exist(self) -> None:
        tree = typer.main.get_command(app)
        for path in documents():
            with open(path, encoding="utf-8") as f:
                code = " ".join(CODE.findall(f.read()))
            for words in COMMAND.findall(code):
                with self.subTest(
                    doc=os.path.relpath(path, ROOT), command=words.strip()
                ):
                    node: Any = tree
                    for i, word in enumerate(words.split()):
                        children = getattr(node, "commands", {})
                        if word not in children:
                            self.assertGreater(i, 0, f"no command `janken {word}`")
                            break
                        node = children[word]

    @unittest.skipIf(
        os.path.isfile(settings.LOCAL_FILE), "janken.local.toml changes the defaults"
    )
    def test_the_reference_is_current(self) -> None:
        from janken.cli import reference

        with open(reference.PATH, encoding="utf-8") as f:
            self.assertEqual(
                f.read(),
                reference.render(),
                "regenerate it: uv run python -m janken.cli.reference",
            )


class ConfigCommandTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.mkdtemp()
        self.saved = (settings.CONFIG_FILE, settings.LOCAL_FILE)
        settings.CONFIG_FILE = os.path.join(self.dir, "janken.toml")
        settings.LOCAL_FILE = os.path.join(self.dir, "janken.local.toml")
        shutil.copy(self.saved[0], settings.CONFIG_FILE)
        settings.reload()
        self.runner = CliRunner()

    def tearDown(self) -> None:
        settings.CONFIG_FILE, settings.LOCAL_FILE = self.saved
        settings.reload()
        shutil.rmtree(self.dir)

    def invoke(self, *args: str) -> Result:
        return self.runner.invoke(app, ["config", *args])

    def test_set_get_and_check(self) -> None:
        with open(settings.CONFIG_FILE) as f:
            before = f.read()
        self.assertEqual(self.invoke("set", "match.rounds", "50").exit_code, 0)
        with open(settings.CONFIG_FILE) as f:
            after = f.read()
        self.assertEqual(after, before.replace("rounds = 200", "rounds = 50"))
        self.assertEqual(self.invoke("get", "match.rounds").output.strip(), "50")
        self.assertEqual(self.invoke("check").exit_code, 0)

    def test_bad_values_change_nothing(self) -> None:
        with open(settings.CONFIG_FILE) as f:
            before = f.read()
        for args in (
            ("match.rounds", "0"),
            ("match.rounds", "x"),
            ("match.colour", "1"),
        ):
            with self.subTest(args=args):
                self.assertEqual(self.invoke("set", *args).exit_code, 2)
        with open(settings.CONFIG_FILE) as f:
            self.assertEqual(f.read(), before)

    def test_local_overrides_and_unset(self) -> None:
        self.assertEqual(
            self.invoke("set", "--local", "effort.quick.trials", "3").exit_code, 0
        )
        with open(settings.LOCAL_FILE, "rb") as f:
            self.assertEqual(tomllib.load(f), {"effort": {"quick": {"trials": 3}}})
        self.assertEqual(settings.config().effort.quick.trials, 3)
        self.assertEqual(self.invoke("unset", "effort.quick.trials").exit_code, 0)
        self.assertEqual(settings.config().effort.quick.trials, 10)
        self.assertEqual(self.invoke("unset", "effort.quick.trials").exit_code, 2)

    def test_show_lists_values_and_help(self) -> None:
        shown = self.invoke("show", "tuning").output
        self.assertIn("tuning.sampler", shown)
        self.assertIn("# how trials are chosen", shown)
        data = json.loads(self.invoke("show", "match", "--format", "json").output)
        self.assertEqual(data, {"match.rounds": 200})


class LifecycleTest(unittest.TestCase):
    """The high-level loop and the low level, end to end, on light bots (JIT off)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tempfile.mkdtemp()
        cls.bots = os.path.join(cls.root, "bots")
        cls.notebook = os.path.join(cls.root, "research")
        os.makedirs(cls.bots)
        os.makedirs(cls.notebook)
        for stem in LIGHT_BOTS:
            shutil.copy(os.path.join(ROOT, "bots", stem + ".yaml"), cls.bots)
        for name in ("ideas.md", "insights.md"):
            shutil.copy(os.path.join(ROOT, "research", name), cls.notebook)
        cls.runner = CliRunner()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.root)

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
        self.assertEqual(
            result.exit_code, 0, f"{args}: {result.output}{result.exception!r}"
        )
        return result.output

    def bot(self, stem: str) -> str:
        return os.path.join(self.bots, stem + ".yaml")

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
        self.assertIn("spaces", made)  # cycler has defaults, so a space file too
        self.assertEqual(ideas.load(self.notebook).get(number).state, ideas.IN_PROGRESS)
        self.assertIn("ok twin", self.run_ok("bot", "check", "twin"))
        self.assertIn("twin", self.run_ok("bot", "list"))
        self.assertIn("A cycler twin.", self.run_ok("bot", "show", "twin"))

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
        self.assertIn("Paired comparisons", out)
        note = notes.find(self.notebook, "1")
        self.assertEqual(note.status, notes.RUN)
        self.assertTrue(note.run_ids)
        self.assertIn("lab experiment", note.section("Command"))

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
        self.assertEqual(refused.exit_code, 2)  # identical bots: the CI is [0, 0]

        self.run_ok("verdict", "1", "drop", "--summary", "identical, as expected")
        self.assertEqual(notes.find(self.notebook, "1").status, notes.ANALYZED)
        self.assertEqual(ideas.load(self.notebook).get(number).state, ideas.DROPPED)
        self.assertIn("Next step", self.run_ok("status"))

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
        self.assertEqual((tuned.kind, tuned.status), (notes.TUNING, notes.RUN))
        self.assertIn("Validations", tuned.section("Results"))
        self.assertIn(tuned.study, self.run_ok("lab", "study", "list"))
        self.assertIn("vs defaults", self.run_ok("lab", "study", "show", tuned.study))

    def test_the_low_level(self) -> None:
        out = self.run_ok(
            "lab", "experiment", self.bot("cycler"), self.bot("wsls"), "--name", "adhoc"
        )
        run_id = out.strip().splitlines()[-1].split()[-1]
        self.assertIn(run_id, self.run_ok("lab", "runs"))
        self.assertIn("Candidates vs pool", self.run_ok("lab", "report", run_id))
        self.assertIn("cycler", self.run_ok("lab", "history", "cycler"))
        self.assertIn("wsls", self.run_ok("lab", "leaderboard"))
        self.assertIn(
            "seed", self.run_ok("lab", "match", self.bot("rock"), self.bot("cycler"))
        )
        counted = self.run_ok(
            "lab",
            "query",
            "SELECT count(*) AS n FROM runs WHERE run_id = '" + run_id + "'",
        )
        self.assertIn("| 1 |", counted)
        self.assertIn("run id", self.run_ok("lab", "resume", run_id))
        nowhere = [*self.common(), "--workspace", os.path.join(self.root, "none")]
        result = self.runner.invoke(app, ["lab", "study", "list", *nowhere])
        self.assertIn("(no studies yet)", result.output)

    def test_errors_are_messages_not_tracebacks(self) -> None:
        result = self.runner.invoke(
            app, ["verdict", "999", "keep", "--summary", "x", *self.common()]
        )
        self.assertEqual(result.exit_code, 2)
        self.assertIsInstance(result.exception, SystemExit)
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
        self.assertEqual(result.exit_code, 2)  # a stem is never reused


if __name__ == "__main__":
    unittest.main()
