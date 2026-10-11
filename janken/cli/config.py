"""`janken config`: read and change the configuration (janken.toml)."""

import json
import os
from typing import Annotated

import typer

from .. import config_file, settings
from .options import FORMAT, Format, about, fail

app = typer.Typer(
    help="Read and change every default: janken.toml, or janken.local.toml with --local.",
    no_args_is_help=True,
)

LOCAL_HELP = (
    "edit janken.local.toml (this machine only, gitignored) instead of janken.toml"
)


def _show(value: object) -> str:
    return config_file.literal(list(value) if isinstance(value, tuple) else value)


@app.command()
def show(
    table: Annotated[
        str, typer.Argument(help="only the settings under this table, e.g. tuning")
    ] = "",
    output: Annotated[
        Format, typer.Option("--format", help=about("output.format"))
    ] = FORMAT,
) -> None:
    """List settings with their values and what they mean."""
    found = [e for e in settings.entries(settings.config()) if e.key.startswith(table)]
    if not found:
        raise fail(f"no setting under {table!r}")
    if output == "json":
        print(json.dumps({e.key: e.value for e in found}, indent=2, default=list))
        return
    width = max(len(e.key) for e in found)
    for e in found:
        extra = f" ({' | '.join(e.choices)})" if e.choices else ""
        print(f"{e.key:<{width}} = {_show(e.value)}    # {e.help}{extra}")


@app.command()
def get(
    key: Annotated[str, typer.Argument(help="a dotted setting, e.g. match.rounds")],
) -> None:
    """Print one setting's value."""
    try:
        print(_show(settings.entry(key, settings.config()).value))
    except settings.ConfigError as exc:
        raise fail(str(exc)) from None


def _target(local: bool) -> str:
    return settings.LOCAL_FILE if local else settings.CONFIG_FILE


def _write_checked(path: str, text: str) -> None:
    """Write `text` to `path` only if the configuration it makes is valid."""
    import tomllib

    try:
        new = tomllib.loads(text)
        if path == settings.LOCAL_FILE:
            merged = settings.merge(settings.read_toml(settings.CONFIG_FILE), new)
        else:
            merged = settings.merge(new, settings.read_toml(settings.LOCAL_FILE))
        settings.parse_config(merged)
    except (tomllib.TOMLDecodeError, settings.ConfigError) as exc:
        raise fail(f"not changed: {exc}") from None
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    settings.reload()


@app.command("set")
def set_(
    key: Annotated[
        str, typer.Argument(help="a dotted setting, e.g. effort.standard.trials")
    ],
    value: Annotated[
        str,
        typer.Argument(help="its new value (lists: comma-separated; switches: on/off)"),
    ],
    local: Annotated[bool, typer.Option(help=LOCAL_HELP)] = False,
) -> None:
    """Change one setting, keeping the file's comments and layout."""
    try:
        found = settings.entry(key, settings.config())
        parsed = settings.parse_text(found, value)
    except settings.ConfigError as exc:
        raise fail(str(exc)) from None
    path = _target(local)
    text = ""
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            text = f.read()
    _write_checked(path, config_file.set_value(text, key, parsed))
    print(f"{key} = {config_file.literal(parsed)}  ({os.path.basename(path)})")


@app.command()
def unset(
    key: Annotated[
        str, typer.Argument(help="a dotted setting janken.local.toml overrides")
    ],
) -> None:
    """Drop a local override, so janken.toml's value applies again."""
    if not os.path.isfile(settings.LOCAL_FILE):
        raise fail("there is no janken.local.toml")
    with open(settings.LOCAL_FILE, encoding="utf-8") as f:
        text = f.read()
    try:
        changed = config_file.unset_value(text, key)
    except KeyError:
        raise fail(f"janken.local.toml doesn't set {key}") from None
    _write_checked(settings.LOCAL_FILE, changed)
    print(
        f"{key} = {_show(settings.entry(key, settings.config()).value)}  (janken.toml)"
    )


@app.command()
def path() -> None:
    """Print where the configuration files are."""
    print(settings.CONFIG_FILE)
    print(
        f"{settings.LOCAL_FILE}{'' if os.path.isfile(settings.LOCAL_FILE) else ' (absent)'}"
    )


@app.command()
def check() -> None:
    """Validate the configuration files: every key present, every value allowed."""
    try:
        settings.reload()
    except settings.ConfigError as exc:
        raise fail(str(exc)) from None
    print(f"ok: {sum(1 for _ in settings.entries(settings.config()))} settings")
