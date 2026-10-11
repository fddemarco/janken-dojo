"""The tournament's screening of a submitted bot script, before it ever runs.

A port of the organiser's static scan (the original janken/safety.py): imports
outside a stdlib allowlist, banned builtins (file access, dynamic code,
introspection), dunder names and attributes, and dunders hidden in string
literals. Two more rules hold for an exported bot: no `global` / `nonlocal`
(module-level state is mutated, never rebound), and a top-level `play`.
The allowlist and the banned names are settings (`export.*` in janken.toml).
"""

import ast
import dataclasses
import re
from collections.abc import Collection

ALLOWED_DUNDER_NAMES = frozenset({"__name__"})
ALLOWED_DUNDER_STRINGS = frozenset({"__main__"})
ENTRY_POINT = "play"
_DUNDER = re.compile(r"__\w+__")


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


@dataclasses.dataclass(frozen=True)
class Violation:
    """One rule a script breaks, at a line."""

    line: int
    message: str

    def __str__(self) -> str:
        return f"line {self.line}: {self.message}"


@dataclasses.dataclass(frozen=True)
class Rules:
    """What a script may import and which builtins it may not name."""

    allowed_modules: Collection[str]
    banned_names: Collection[str]


def _import_violations(node: ast.AST, rules: Rules) -> list[str]:
    if isinstance(node, ast.Import):
        roots = [alias.name.split(".")[0] for alias in node.names]
        return [
            f"import of {r!r} is not allowed"
            for r in roots
            if r not in rules.allowed_modules
        ]
    if isinstance(node, ast.ImportFrom):
        if node.level:
            return ["relative imports are not allowed"]
        root = (node.module or "").split(".")[0]
        if root not in rules.allowed_modules:
            return [f"import from {root!r} is not allowed"]
    return []


def _name_violations(node: ast.AST, rules: Rules) -> list[str]:
    if isinstance(node, ast.Name):
        if node.id in rules.banned_names:
            return [f"use of {node.id!r} is not allowed"]
        if _is_dunder(node.id) and node.id not in ALLOWED_DUNDER_NAMES:
            return [f"reference to {node.id!r} is not allowed"]
    if isinstance(node, ast.Attribute) and _is_dunder(node.attr):
        return [f"dunder attribute access '.{node.attr}' is not allowed"]
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        hidden = [
            d for d in _DUNDER.findall(node.value) if d not in ALLOWED_DUNDER_STRINGS
        ]
        if hidden:
            return [f"string literal contains dunder {hidden[0]!r}"]
    return []


def _scope_violations(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Global):
        return ["the `global` keyword is not allowed"]
    if isinstance(node, ast.Nonlocal):
        return ["the `nonlocal` keyword is not allowed"]
    return []


def scan(source: str, rules: Rules) -> list[Violation]:
    """Every rule `source` breaks, by line (empty: it passes the screening)."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [Violation(exc.lineno or 0, f"syntax error: {exc.msg}")]
    found: list[Violation] = []
    for node in ast.walk(tree):
        line = int(getattr(node, "lineno", 0))
        for message in (
            _import_violations(node, rules)
            + _name_violations(node, rules)
            + _scope_violations(node)
        ):
            found.append(Violation(line, message))
    if not any(
        isinstance(node, ast.FunctionDef) and node.name == ENTRY_POINT
        for node in tree.body
    ):
        found.append(Violation(0, f"no top-level `{ENTRY_POINT}` function"))
    return sorted(found, key=lambda v: v.line)
