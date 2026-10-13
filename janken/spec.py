"""BotSpec: a bot file plus parameter overrides, under one result label.

    bots/l1/geometry_v1.yaml                        -> label "geometry_v1" (its defaults)
    bots/l1/geometry_v1.yaml:ALPHA=0.1,MAX_LEN=12   -> label "geometry_v1@1f3a9c"

The label is the name the bot carries in match results. A variant's label is
the stem plus a short hash of its overrides, so variants of one file can share
an experiment and stay apart in the results.
"""

import ast
import dataclasses
import hashlib
import json
import os
from collections.abc import Mapping

from . import botfile, library
from .match import bot_name


def params_hash(params: dict[str, object]) -> str:
    blob = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:6]


@dataclasses.dataclass(frozen=True)
class BotSpec:
    path: str
    params: dict[str, object] = dataclasses.field(default_factory=dict, hash=False)
    label: str = ""

    @property
    def stem(self) -> str:
        return bot_name(self.path)


def make_spec(
    path: str, params: Mapping[str, object] | None = None, label: str | None = None
) -> BotSpec:
    """A validated BotSpec; unknown parameter names are an error."""
    path = os.path.normpath(path)
    if not os.path.isfile(path):
        raise ValueError(f"no bot file {path!r}")
    params = dict(params or {})
    botfile.check_params(path, params)
    if label is None:
        label = (
            bot_name(path) if not params else f"{bot_name(path)}@{params_hash(params)}"
        )
    return BotSpec(path=path, params=params, label=label)


def _value(text: str):
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return text


def parse_spec(text: str) -> BotSpec:
    """`path` or `path:NAME=value,NAME=value` -> BotSpec."""
    path, _, rest = text.partition(":")
    params = {}
    for item in filter(None, (s.strip() for s in rest.split(","))):
        name, eq, value = item.partition("=")
        if not eq:
            raise ValueError(f"bad parameter {item!r} in {text!r} (want NAME=value)")
        params[name.strip()] = _value(value.strip())
    return make_spec(path, params)


def format_spec(spec: BotSpec) -> str:
    """The command-line form of a spec (inverse of parse_spec)."""
    if not spec.params:
        return spec.path
    return (
        spec.path
        + ":"
        + ",".join("{}={!r}".format(*kv) for kv in sorted(spec.params.items()))
    )


def to_dict(spec: BotSpec) -> dict:
    return {
        "label": spec.label,
        "stem": spec.stem,
        "path": spec.path,
        "params": spec.params,
        "sha256": library.source_hash(spec.path),
    }
