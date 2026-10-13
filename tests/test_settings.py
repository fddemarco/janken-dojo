"""janken/settings.py and janken/config_file.py: the configuration and its editing."""

import copy
import pathlib
import tomllib
from typing import Any

import pytest

from janken import config_file, settings


def project_tables() -> dict[str, Any]:
    return settings.read_toml(settings.CONFIG_FILE)


class TestConfig:
    def test_the_project_file_holds_every_setting_with_help(
        self, subtests: pytest.Subtests
    ) -> None:
        config = settings.config()
        found = list(settings.entries(config))
        assert len(found) > 50
        for entry in found:
            with subtests.test(key=entry.key):
                assert entry.help
        assert settings.entry("match.rounds", config).value == config.match.rounds
        assert config.effort.budget("quick") == config.effort.quick

    def test_every_key_is_required_and_unknown_keys_are_refused(self) -> None:
        tables = project_tables()
        missing = copy.deepcopy(tables)
        del missing["match"]["rounds"]
        with pytest.raises(settings.ConfigError, match="match.rounds"):
            settings.parse_config(missing)
        extra = copy.deepcopy(tables)
        extra["pool"]["colour"] = "blue"
        with pytest.raises(settings.ConfigError, match="colour"):
            settings.parse_config(extra)

    @pytest.mark.parametrize(
        "table, key, value",
        [
            ("match", "rounds", 0),
            ("match", "rounds", 2.5),
            ("engine", "jit", "maybe"),
            ("output", "progress", "loud"),
            ("tuning", "sampler", "cmaes"),
            ("engine", "cache_commands", "evaluate"),
            ("runs", "lock_timeout_s", -1),
            ("dataset", "metric", "f2"),
        ],
    )
    def test_bad_values_are_refused(self, table: str, key: str, value: object) -> None:
        tables = copy.deepcopy(project_tables())
        tables[table][key] = value
        with pytest.raises(settings.ConfigError):
            settings.parse_config(tables)

    def test_a_local_file_overrides_the_project_file(
        self, tmp_path: pathlib.Path
    ) -> None:
        local = str(tmp_path / "janken.local.toml")
        with open(local, "w") as f:
            f.write("[match]\nrounds = 7\n[effort.quick]\ntrials = 3\n")
        config = settings.load_files(settings.CONFIG_FILE, local)
        assert config.match.rounds == 7
        assert config.effort.quick.trials == 3
        assert config.pool == settings.config().pool

    def test_a_missing_file_is_an_error(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(settings.ConfigError):
            settings.load_files(str(tmp_path / "janken.toml"), "")

    def test_command_line_text_parses_by_the_setting_type(self) -> None:
        config = settings.config()
        assert settings.parse_text(settings.entry("match.rounds", config), "50") == 50
        assert settings.parse_text(settings.entry("engine.jit", config), "off") is False
        cache = settings.entry("engine.cache_commands", config)
        assert settings.parse_text(cache, "evaluate, tune") == ["evaluate", "tune"]
        with pytest.raises(settings.ConfigError):
            settings.parse_text(settings.entry("match.rounds", config), "many")
        with pytest.raises(settings.ConfigError):
            settings.entry("match.colour", config)


class TestEdit:
    TEXT = (
        "# the header\n\n[match]\n# rounds per match\nrounds = 200\n\n"
        "[effort.quick]\ntrials = 10  # few\n"
    )

    def test_set_rewrites_one_line_and_keeps_the_comments(self) -> None:
        changed = config_file.set_value(self.TEXT, "match.rounds", 50)
        assert changed == self.TEXT.replace("rounds = 200", "rounds = 50")
        assert tomllib.loads(changed)["match"]["rounds"] == 50

    def test_set_adds_missing_keys_and_tables(self) -> None:
        changed = config_file.set_value(self.TEXT, "match.extra", "x")
        assert tomllib.loads(changed)["match"]["extra"] == "x"
        changed = config_file.set_value(changed, "pool.size", 5)
        assert tomllib.loads(changed)["pool"]["size"] == 5
        assert "# rounds per match" in changed
        fresh = config_file.set_value("", "effort.quick.trials", 3)
        assert tomllib.loads(fresh) == {"effort": {"quick": {"trials": 3}}}

    def test_unset_removes_a_key_and_an_emptied_table(self) -> None:
        text = config_file.set_value("", "match.rounds", 9)
        text = config_file.set_value(text, "pool.size", 3)
        text = config_file.unset_value(text, "match.rounds")
        assert tomllib.loads(text) == {"pool": {"size": 3}}
        with pytest.raises(KeyError):
            config_file.unset_value(text, "match.rounds")

    def test_literals(self) -> None:
        assert config_file.literal(True) == "true"
        assert config_file.literal(2.0) == "2.0"
        assert config_file.literal(("a", "b")) == '["a", "b"]'
        assert config_file.literal('say "hi"') == '"say \\"hi\\""'
        with pytest.raises(TypeError):
            config_file.literal({"a": 1})


class TestLoad:
    def test_environment_overrides_the_config(self) -> None:
        assert not settings.load({settings.JIT_ENV: "off"}).jit
        assert settings.load({settings.JIT_ENV: "on"}).jit

    def test_caching_is_off_unless_turned_on(self) -> None:
        assert not settings.load({settings.JIT_ENV: "on"}).cache
        on = {settings.JIT_ENV: "on", settings.CACHE_ENV: "1"}
        assert settings.load(on).cache

    def test_no_cache_without_the_jit(self) -> None:
        env = {settings.JIT_ENV: "off", settings.CACHE_ENV: "1"}
        assert not settings.load(env).cache

    def test_progress_shows_on_a_terminal_unless_overridden(self) -> None:
        env = settings.PROGRESS_ENV
        assert settings.progress_enabled({env: "auto"}, interactive=True)
        assert not settings.progress_enabled({env: "auto"}, interactive=False)
        assert settings.progress_enabled({env: "on"}, interactive=False)
        assert not settings.progress_enabled({env: "off"}, interactive=True)
        with pytest.raises(ValueError):
            settings.progress_enabled({env: "loud"}, interactive=True)


class TestApply:
    def test_cache_commands_cache_and_others_do_not(self) -> None:
        auto = settings.CacheFlag.AUTO
        for command in settings.config().engine.cache_commands:
            assert settings.wants_cache(command, auto, {}), command
        assert not settings.wants_cache("status", auto, {})
        assert not settings.wants_cache("lab report", auto, {})

    def test_the_flag_beats_the_environment_which_beats_the_config(self) -> None:
        env = {settings.CACHE_ENV: "0"}
        assert not settings.wants_cache("evaluate", settings.CacheFlag.AUTO, env)
        assert settings.wants_cache("status", settings.CacheFlag.ON, env)
        assert not settings.wants_cache("tune", settings.CacheFlag.OFF, {})

    def test_apply_writes_the_decision_to_the_environment(self) -> None:
        env = {settings.JIT_ENV: "on"}
        current = settings.apply("evaluate", settings.CacheFlag.AUTO, env)
        assert env[settings.CACHE_ENV] == "1"
        assert current == settings.Settings(jit=True, cache=True)
