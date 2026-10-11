"""janken/settings.py and janken/config_file.py: the configuration and its editing."""

import copy
import os
import tempfile
import tomllib
import unittest
from typing import Any

from janken import config_file, settings


def project_tables() -> dict[str, Any]:
    return settings.read_toml(settings.CONFIG_FILE)


class ConfigTest(unittest.TestCase):
    def test_the_project_file_holds_every_setting_with_help(self) -> None:
        config = settings.config()
        found = list(settings.entries(config))
        self.assertGreater(len(found), 50)
        for entry in found:
            with self.subTest(key=entry.key):
                self.assertTrue(entry.help)
        self.assertEqual(
            settings.entry("match.rounds", config).value, config.match.rounds
        )
        self.assertEqual(config.effort.budget("quick"), config.effort.quick)

    def test_every_key_is_required_and_unknown_keys_are_refused(self) -> None:
        tables = project_tables()
        missing = copy.deepcopy(tables)
        del missing["match"]["rounds"]
        with self.assertRaisesRegex(settings.ConfigError, "match.rounds"):
            settings.parse_config(missing)
        extra = copy.deepcopy(tables)
        extra["pool"]["colour"] = "blue"
        with self.assertRaisesRegex(settings.ConfigError, "colour"):
            settings.parse_config(extra)

    def test_bad_values_are_refused(self) -> None:
        bad: list[tuple[str, str, object]] = [
            ("match", "rounds", 0),
            ("match", "rounds", 2.5),
            ("engine", "jit", "maybe"),
            ("output", "progress", "loud"),
            ("tuning", "sampler", "cmaes"),
            ("engine", "cache_commands", "evaluate"),
            ("runs", "lock_timeout_s", -1),
            ("dataset", "metric", "f2"),
        ]
        for table, key, value in bad:
            with self.subTest(key=f"{table}.{key}", value=value):
                tables = copy.deepcopy(project_tables())
                tables[table][key] = value
                with self.assertRaises(settings.ConfigError):
                    settings.parse_config(tables)

    def test_a_local_file_overrides_the_project_file(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            local = os.path.join(d, "janken.local.toml")
            with open(local, "w") as f:
                f.write("[match]\nrounds = 7\n[effort.quick]\ntrials = 3\n")
            config = settings.load_files(settings.CONFIG_FILE, local)
        self.assertEqual(config.match.rounds, 7)
        self.assertEqual(config.effort.quick.trials, 3)
        self.assertEqual(config.pool, settings.config().pool)

    def test_a_missing_file_is_an_error(self) -> None:
        with (
            tempfile.TemporaryDirectory() as d,
            self.assertRaises(settings.ConfigError),
        ):
            settings.load_files(os.path.join(d, "janken.toml"), "")

    def test_command_line_text_parses_by_the_setting_type(self) -> None:
        config = settings.config()
        self.assertEqual(
            settings.parse_text(settings.entry("match.rounds", config), "50"), 50
        )
        self.assertIs(
            settings.parse_text(settings.entry("engine.jit", config), "off"), False
        )
        cache = settings.entry("engine.cache_commands", config)
        self.assertEqual(
            settings.parse_text(cache, "evaluate, tune"), ["evaluate", "tune"]
        )
        with self.assertRaises(settings.ConfigError):
            settings.parse_text(settings.entry("match.rounds", config), "many")
        with self.assertRaises(settings.ConfigError):
            settings.entry("match.colour", config)


class EditTest(unittest.TestCase):
    TEXT = (
        "# the header\n\n[match]\n# rounds per match\nrounds = 200\n\n"
        "[effort.quick]\ntrials = 10  # few\n"
    )

    def test_set_rewrites_one_line_and_keeps_the_comments(self) -> None:
        changed = config_file.set_value(self.TEXT, "match.rounds", 50)
        self.assertEqual(changed, self.TEXT.replace("rounds = 200", "rounds = 50"))
        self.assertEqual(tomllib.loads(changed)["match"]["rounds"], 50)

    def test_set_adds_missing_keys_and_tables(self) -> None:
        changed = config_file.set_value(self.TEXT, "match.extra", "x")
        self.assertEqual(tomllib.loads(changed)["match"]["extra"], "x")
        changed = config_file.set_value(changed, "pool.size", 5)
        self.assertEqual(tomllib.loads(changed)["pool"]["size"], 5)
        self.assertIn("# rounds per match", changed)
        fresh = config_file.set_value("", "effort.quick.trials", 3)
        self.assertEqual(tomllib.loads(fresh), {"effort": {"quick": {"trials": 3}}})

    def test_unset_removes_a_key_and_an_emptied_table(self) -> None:
        text = config_file.set_value("", "match.rounds", 9)
        text = config_file.set_value(text, "pool.size", 3)
        text = config_file.unset_value(text, "match.rounds")
        self.assertEqual(tomllib.loads(text), {"pool": {"size": 3}})
        with self.assertRaises(KeyError):
            config_file.unset_value(text, "match.rounds")

    def test_literals(self) -> None:
        self.assertEqual(config_file.literal(True), "true")
        self.assertEqual(config_file.literal(2.0), "2.0")
        self.assertEqual(config_file.literal(("a", "b")), '["a", "b"]')
        self.assertEqual(config_file.literal('say "hi"'), '"say \\"hi\\""')
        with self.assertRaises(TypeError):
            config_file.literal({"a": 1})


class LoadTest(unittest.TestCase):
    def test_environment_overrides_the_config(self) -> None:
        self.assertFalse(settings.load({settings.JIT_ENV: "off"}).jit)
        self.assertTrue(settings.load({settings.JIT_ENV: "on"}).jit)

    def test_caching_is_off_unless_turned_on(self) -> None:
        self.assertFalse(settings.load({settings.JIT_ENV: "on"}).cache)
        on = {settings.JIT_ENV: "on", settings.CACHE_ENV: "1"}
        self.assertTrue(settings.load(on).cache)

    def test_no_cache_without_the_jit(self) -> None:
        env = {settings.JIT_ENV: "off", settings.CACHE_ENV: "1"}
        self.assertFalse(settings.load(env).cache)

    def test_progress_shows_on_a_terminal_unless_overridden(self) -> None:
        env = settings.PROGRESS_ENV
        self.assertTrue(settings.progress_enabled({env: "auto"}, interactive=True))
        self.assertFalse(settings.progress_enabled({env: "auto"}, interactive=False))
        self.assertTrue(settings.progress_enabled({env: "on"}, interactive=False))
        self.assertFalse(settings.progress_enabled({env: "off"}, interactive=True))
        with self.assertRaises(ValueError):
            settings.progress_enabled({env: "loud"}, interactive=True)


class ApplyTest(unittest.TestCase):
    def test_cache_commands_cache_and_others_do_not(self) -> None:
        auto = settings.CacheFlag.AUTO
        for command in settings.config().engine.cache_commands:
            self.assertTrue(settings.wants_cache(command, auto, {}), command)
        self.assertFalse(settings.wants_cache("status", auto, {}))
        self.assertFalse(settings.wants_cache("lab report", auto, {}))

    def test_the_flag_beats_the_environment_which_beats_the_config(self) -> None:
        env = {settings.CACHE_ENV: "0"}
        self.assertFalse(settings.wants_cache("evaluate", settings.CacheFlag.AUTO, env))
        self.assertTrue(settings.wants_cache("status", settings.CacheFlag.ON, env))
        self.assertFalse(settings.wants_cache("tune", settings.CacheFlag.OFF, {}))

    def test_apply_writes_the_decision_to_the_environment(self) -> None:
        env = {settings.JIT_ENV: "on"}
        current = settings.apply("evaluate", settings.CacheFlag.AUTO, env)
        self.assertEqual(env[settings.CACHE_ENV], "1")
        self.assertEqual(current, settings.Settings(jit=True, cache=True))


if __name__ == "__main__":
    unittest.main()
