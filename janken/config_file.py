"""Line-preserving edits of a TOML configuration file.

`janken config set` changes one value without touching the rest of the file: its
comments, order and layout stay as they are. Only what this project's configuration
uses is supported: tables of scalar values and lists of strings, one key per line.
Reading is `tomllib`'s job; this module only rewrites lines.
"""

import json
import re

_HEADER = re.compile(r"^\s*\[([A-Za-z0-9_.]+)\]\s*(#.*)?$")


def literal(value: object) -> str:
    """`value` as a TOML literal.

    Raises:
        TypeError: a value the configuration can't hold.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value)  # a TOML basic string
    if isinstance(value, list | tuple) and all(isinstance(v, str) for v in value):
        return "[" + ", ".join(json.dumps(v) for v in value) + "]"
    raise TypeError(f"can't write {value!r} to the configuration")


def _split(key: str) -> tuple[str, str]:
    table, _, name = key.rpartition(".")
    if not table or not name:
        raise ValueError(f"a setting is TABLE.KEY, got {key!r}")
    return table, name


def _section(lines: list[str], table: str) -> tuple[int, int]:
    """The [start, end) line range of `table`'s body (-1, -1 when it's absent)."""
    start = -1
    for i, line in enumerate(lines):
        header = _HEADER.match(line)
        if header and start >= 0:
            return start, i
        if header and header.group(1) == table:
            start = i + 1
    return (start, len(lines)) if start >= 0 else (-1, -1)


def _key_line(lines: list[str], start: int, end: int, name: str) -> int:
    pattern = re.compile(rf"^\s*{re.escape(name)}\s*=")
    for i in range(start, end):
        if pattern.match(lines[i]):
            return i
    return -1


def set_value(text: str, key: str, value: object) -> str:
    """`text` with the setting `key` (TABLE.KEY) set to `value`.

    A key that's there is rewritten in place; a missing key goes at the end of its
    table; a missing table goes at the end of the file.
    """
    table, name = _split(key)
    lines = text.splitlines()
    line = f"{name} = {literal(value)}"
    start, end = _section(lines, table)
    if start < 0:
        lines += (["", f"[{table}]"] if lines else [f"[{table}]"]) + [line]
        return "\n".join(lines) + "\n"
    found = _key_line(lines, start, end, name)
    if found >= 0:
        lines[found] = line
    else:
        insert = end
        while insert > start and not lines[insert - 1].strip():
            insert -= 1
        lines.insert(insert, line)
    return "\n".join(lines) + "\n"


def unset_value(text: str, key: str) -> str:
    """`text` without the setting `key`; an emptied table goes too.

    Raises:
        KeyError: the file doesn't set `key`.
    """
    table, name = _split(key)
    lines = text.splitlines()
    start, end = _section(lines, table)
    found = _key_line(lines, start, end, name) if start >= 0 else -1
    if found < 0:
        raise KeyError(key)
    del lines[found]
    end -= 1
    body = [
        line
        for line in lines[start:end]
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not body:
        del lines[start - 1 : end]
    return "\n".join(lines).strip("\n") + "\n" if any(lines) else ""
