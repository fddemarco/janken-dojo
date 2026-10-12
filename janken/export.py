"""Bots as tournament submissions: one stdlib-only Python script per bot.

A submission is one `.py` file whose `play(my_moves, opp_moves)` returns "rock",
"paper" or "scissors" (an opponent's invalid move arrives as "invalid"), importing
only the standard library (janken/sandbox.py screens it). A script here holds:

* the kit's runtime (the compiled stages of janken/kit, which run as plain Python
  when the JIT is off), rewritten into one namespace: numpy's few uses become lists,
  `array` and `memoryview` (whose slices are views, like numpy's), every module's
  top-level name becomes `<module>_<name>`, and decorators, annotations and
  docstrings go;
* the bot's compiled blueprint, as literals (`SPEC`, `KNOBS`, `PRM`), and a `play`
  that keeps the match's state in a module-level dict, never rebound (no `global`).

A fleet's champion brings its supports: the size - 1 bots its file's `fleet`
section names (janken/botfile.py), one script each. A support's script is the
champion's, plus a comment naming the support and its role line (`TEAM_ROLE`).
"""

import ast
import dataclasses
import functools
import importlib
import os
from collections.abc import Iterator, Mapping, Sequence

from . import botfile, library, match, mocks
from .engine import registry
from .kit import blueprint as bp
from .kit import codes as c

# The kit's runtime modules, in the order their module-level statements need.
RUNTIME = (
    "codes",
    "moves",
    "matching",
    "oracle",
    "signals",
    "bayes",
    "ensemble",
    "replay",
    "selectors",
    "guards",
    "overlays",
    "pipeline",
)
KIT_PACKAGE = "janken.kit"
STDLIB_IMPORTS = ("array", "math", "random")
DECORATORS = ("kernel",)  # dropped: the script runs as plain Python
NUMPY_INT_DTYPES = ("int64",)
NUMPY_DTYPES = ("int64", "float64")
ROLE_NAMES: Mapping[int, str] = {c.CHAMPION: "CHAMPION", c.SUPPORT: "SUPPORT"}
NUMBERS_PER_LINE = 16


class ExportError(ValueError):
    """A bot (or the kit's runtime) that can't be exported as a submission."""


def global_name(module: str, name: str) -> str:
    """A runtime module's top-level name, as the bundled script names it."""
    return f"{module}_{name}"


# --- the kit's runtime, as one stdlib module ------------------------------------


@dataclasses.dataclass
class _Imports:
    """What one module's imports bind: kit module aliases, kit names, constants."""

    numpy: set[str] = dataclasses.field(default_factory=set)
    modules: dict[str, str] = dataclasses.field(default_factory=dict)
    names: dict[str, str] = dataclasses.field(default_factory=dict)
    constants: dict[str, int | float | str | bool] = dataclasses.field(
        default_factory=dict
    )


def _kit_module(level: int, module: str, where: str) -> str:
    """The kit module a relative import names ('' for the kit package itself)."""
    if level != 1:
        raise ExportError(f"{where}: only the kit's own modules are bundled")
    return module


def _read_imports(tree: ast.Module, where: str) -> _Imports:
    """Classify a module's imports, and drop them from its body."""
    found = _Imports()
    body: list[ast.stmt] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "numpy":
                    found.numpy.add(alias.asname or alias.name)
                elif alias.name not in STDLIB_IMPORTS:
                    raise ExportError(f"{where}: import of {alias.name!r}")
        elif isinstance(node, ast.ImportFrom):
            _read_import_from(node, found, where)
        else:
            body.append(node)
    tree.body = body
    return found


def _read_import_from(node: ast.ImportFrom, found: _Imports, where: str) -> None:
    module = node.module or ""
    if node.level == 2:  # outside the kit: only literal constants are inlined
        source = importlib.import_module(f"janken.{module}")
        for alias in node.names:
            value = vars(source)[alias.name]
            if not isinstance(value, int | float | str | bool):
                raise ExportError(f"{where}: {module}.{alias.name} is not a literal")
            found.constants[alias.asname or alias.name] = value
        return
    package = _kit_module(node.level, module, where)
    for alias in node.names:
        bound = alias.asname or alias.name
        if package == "":
            if alias.name not in RUNTIME:
                raise ExportError(f"{where}: kit module {alias.name!r} isn't bundled")
            found.modules[bound] = alias.name
        elif package == "jit":
            if alias.name not in DECORATORS:
                raise ExportError(f"{where}: jit.{alias.name} can't be exported")
        elif package in RUNTIME:
            found.names[bound] = global_name(package, alias.name)
        else:
            raise ExportError(f"{where}: kit module {package!r} isn't bundled")


def _top_level_names(tree: ast.Module) -> set[str]:
    """The names a module defines at its top level."""
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign | ast.AnnAssign | ast.AugAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                names.update(n.id for n in ast.walk(target) if isinstance(n, ast.Name))
    return names


def _local_names(fn: ast.FunctionDef) -> set[str]:
    """A function's parameters and the names it assigns."""
    args = fn.args
    params = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    params += [a for a in (args.vararg, args.kwarg) if a is not None]
    names = {a.arg for a in params}
    for node in ast.walk(fn):
        if isinstance(node, ast.Global | ast.Nonlocal):
            raise ExportError(f"{fn.name}: `global` / `nonlocal` can't be exported")
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
    return names


def _is_docstring(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


class _Rewriter(ast.NodeTransformer):
    """One runtime module's body, rewritten into the bundle's namespace."""

    def __init__(self, module: str, imports: _Imports, own: set[str]) -> None:
        self.module = module
        self.imports = imports
        self.renames: dict[str, str] = {
            **imports.names,
            **{name: global_name(module, name) for name in own},
        }
        self.local: set[str] = set()
        self.used: set[str] = set()  # bundle names this module reads

    def where(self, node: ast.AST) -> str:
        return f"janken/kit/{self.module}.py:{getattr(node, 'lineno', 0)}"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        for decorator in node.decorator_list:
            if not (isinstance(decorator, ast.Name) and decorator.id in DECORATORS):
                raise ExportError(f"{self.where(node)}: unknown decorator")
        node.decorator_list = []
        node.returns = None
        args = node.args
        for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
            arg.annotation = None
        self.local = _local_names(node)
        node.body = [s for s in node.body if not _is_docstring(s)] or [ast.Pass()]
        node.name = self.renames[node.name]
        self.generic_visit(node)
        self.local = set()
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | None:
        if node.value is None:
            return None
        return self.visit(ast.Assign(targets=[node.target], value=node.value))

    def visit_Expr(self, node: ast.Expr) -> ast.AST | None:
        return None if _is_docstring(node) else self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id in self.local:
            return node
        if node.id in self.imports.numpy:
            raise ExportError(f"{self.where(node)}: numpy can't be exported here")
        if node.id in self.imports.constants:
            return ast.Constant(self.imports.constants[node.id])
        if node.id in self.renames:
            self.used.add(self.renames[node.id])
            return ast.Name(self.renames[node.id], node.ctx)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        target = node.value
        if (
            isinstance(target, ast.Name)
            and target.id not in self.local
            and target.id in self.imports.modules
        ):
            name = global_name(self.imports.modules[target.id], node.attr)
            self.used.add(name)
            return ast.Name(name, node.ctx)
        if node.attr == "size":  # a numpy array's length
            return ast.Call(ast.Name("len", ast.Load()), [self.visit(target)], [])
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        fn = node.func
        if (
            isinstance(fn, ast.Attribute)
            and isinstance(fn.value, ast.Name)
            and fn.value.id in self.imports.numpy
        ):
            return self._numpy_call(fn.attr, node)
        return self.generic_visit(node)

    def _numpy_call(self, name: str, node: ast.Call) -> ast.AST:
        """np.zeros / np.empty: a list of zeros; np.array: its (list) literal."""
        dtypes = [*node.args[1:], *(k.value for k in node.keywords)]
        for dtype in dtypes:
            if not (isinstance(dtype, ast.Attribute) and dtype.attr in NUMPY_DTYPES):
                raise ExportError(f"{self.where(node)}: unknown numpy dtype")
        if name == "array" and node.args:
            return self.visit(node.args[0])
        if name in ("zeros", "empty") and node.args:
            ints = any(
                isinstance(d, ast.Attribute) and d.attr in NUMPY_INT_DTYPES
                for d in dtypes
            )
            zero = ast.List([ast.Constant(0 if ints else 0.0)], ast.Load())
            return ast.BinOp(zero, ast.Mult(), self.visit(node.args[0]))
        raise ExportError(f"{self.where(node)}: numpy's {name} can't be exported")


@dataclasses.dataclass(frozen=True)
class Rewritten:
    """A runtime module, rewritten: its source, and the bundle names it defines
    and reads."""

    source: str
    defines: frozenset[str]
    reads: frozenset[str]
    locals_: frozenset[str]


def rewrite_module(module: str, source: str) -> Rewritten:
    """One kit runtime module as plain stdlib Python in the bundle's namespace.

    Raises:
        ExportError: it uses something the rewrite doesn't know how to export.
    """
    tree = ast.parse(source)
    where = f"janken/kit/{module}.py"
    imports = _read_imports(tree, where)
    own = _top_level_names(tree)
    locals_: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            locals_ |= _local_names(node)
    rewriter = _Rewriter(module, imports, own)
    rewritten = ast.fix_missing_locations(rewriter.visit(tree))
    return Rewritten(
        source=ast.unparse(rewritten),
        defines=frozenset(global_name(module, name) for name in own),
        reads=frozenset(rewriter.used),
        locals_=frozenset(locals_),
    )


def _runtime_path(module: str) -> str:
    package = importlib.import_module(KIT_PACKAGE)
    return os.path.join(os.path.dirname(str(package.__file__)), module + ".py")


@functools.cache
def runtime_source() -> str:
    """The kit's whole runtime, as one stdlib-only module body.

    Raises:
        ExportError: a module can't be exported, or the bundle's names collide.
    """
    parts: list[Rewritten] = []
    for module in RUNTIME:
        with open(_runtime_path(module), encoding="utf-8") as f:
            parts.append(rewrite_module(module, f.read()))
    defined = frozenset().union(*(p.defines for p in parts))
    missing = frozenset().union(*(p.reads for p in parts)) - defined
    if missing:
        raise ExportError(f"the bundle reads undefined names: {sorted(missing)}")
    shadowed = defined & frozenset().union(*(p.locals_ for p in parts))
    if shadowed:
        raise ExportError(f"local names shadow bundle names: {sorted(shadowed)}")
    return "\n\n".join(
        f"# --- janken/kit/{module}.py ---\n{part.source}"
        for module, part in zip(RUNTIME, parts, strict=True)
    )


# --- fleets ----------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Fleet:
    """An exported bot (`champion`) and the supports its scripts are made for."""

    champion: str
    supports: tuple[str, ...] = ()


def _blueprint(path: str) -> bp.Blueprint:
    return library.read_blueprint(path)


def fleet_of(path: str) -> Fleet:
    """The bot at `path` and, when it leads a fleet (its file's `fleet` section),
    the supports that section names, in order.

    Raises:
        ExportError: the bot plays a Team overlay outside a fleet section (an
            impostor, or a bot posing as a fleet's member): research only.
    """
    name = match.bot_name(path)
    fleet = botfile.read(path).fleet
    if fleet.declared:
        return Fleet(name, fleet.supports)
    if any(isinstance(o, bp.Team) for o in _blueprint(path).overlays):
        raise ExportError(
            f"{name} plays a Team outside a fleet section: export a fleet's champion"
        )
    return Fleet(name)


# --- the scripts -----------------------------------------------------------------


def team_role_cells(spec: Sequence[int]) -> list[int]:
    """The spec cells holding a Team overlay's role (one per Team overlay)."""
    first = int(spec[c.H_OVER_AT])
    records = (first + k * c.REC for k in range(int(spec[c.H_NOVER])))
    return [r + c.R_A for r in records if int(spec[r + c.R_KIND]) == c.O_TEAM]


def _literal_lines(name: str, values: Sequence[float | int]) -> Iterator[str]:
    """`name = [...]`, a few numbers a line."""
    if not values:
        yield f"{name} = []"
        return
    yield f"{name} = ["
    for at in range(0, len(values), NUMBERS_PER_LINE):
        chunk = values[at : at + NUMBERS_PER_LINE]
        yield "    " + ", ".join(repr(v) for v in chunk) + ","
    yield "]"


def _role_lines(role: int, comment: str) -> list[str]:
    lines = [f"# {comment}"] if comment else []
    return [*lines, f"TEAM_ROLE = {role}  # {ROLE_NAMES[role]}"]


def _bot_lines(
    compiled: bp.Compiled, prm: Sequence[float], cells: list[int]
) -> list[str]:
    f_size, i_size, per_round = compiled.state
    spec = [int(v) for v in compiled.spec]
    return [
        "# --- the bot: its compiled blueprint (janken/kit/blueprint/) ---",
        *_literal_lines("SPEC", spec),
        *_literal_lines("KNOBS", [float(v) for v in compiled.knobs]),
        *_literal_lines("PRM", [float(v) for v in prm]),
        f"F_SIZE = {f_size}",
        f"I_SIZE = {i_size}",
        f"PER_ROUND_SLOTS = {per_round}",
        *(f"SPEC[{cell}] = TEAM_ROLE" for cell in cells),
    ]


def _play_source(max_rounds: int) -> str:
    """`play` and the match state it keeps (Compiled.new_state's allocation)."""
    invalid = global_name("moves", "INVALID")
    crash = global_name("moves", "CRASH")
    rounds_i = global_name("codes", "H_ROUNDS_I")
    play = global_name("pipeline", "play")
    return f"""\
# --- the submission's entry point ---
MAX_ROUNDS = {max_rounds}
MOVE_NAMES = ("rock", "paper", "scissors", "invalid")
MOVE_CODES = {{"rock": 0, "paper": 1, "scissors": 2}}
_MATCH = {{}}  # this match's state: mutated, never rebound


def _new_match():
    stride = MAX_ROUNDS + 1
    i = array.array("q", [0]) * (I_SIZE + PER_ROUND_SLOTS * stride)
    at = SPEC[{rounds_i}]
    i[at] = stride
    i[at + 1] = I_SIZE
    _MATCH["f"] = memoryview(array.array("d", [0.0]) * F_SIZE)
    _MATCH["i"] = memoryview(i)
    _MATCH["my"] = [0] * stride
    _MATCH["opp"] = [0] * stride
    _MATCH["seen"] = 0


def play(my_moves, opp_moves):
    n = len(opp_moves)
    if n == 0 or not _MATCH or n < _MATCH["seen"]:
        _new_match()
    if n >= MAX_ROUNDS:
        raise ValueError("this export plays at most %d rounds" % MAX_ROUNDS)
    my = _MATCH["my"]
    opp = _MATCH["opp"]
    for t in range(_MATCH["seen"], n):
        my[t] = MOVE_CODES.get(my_moves[t], {invalid})
        opp[t] = MOVE_CODES.get(opp_moves[t], {invalid})
    _MATCH["seen"] = n
    move = {play}(_MATCH["f"], _MATCH["i"], PRM, my, opp, n, SPEC, KNOBS)
    if move == {crash}:
        raise RuntimeError("the bot forfeits (an OnInvalid guard)")
    return MOVE_NAMES[move]
"""


def script(
    compiled: bp.Compiled,
    prm: Sequence[float],
    header: Sequence[str],
    role_lines: Sequence[str],
    max_rounds: int,
) -> str:
    """A submission script: header comments, the role, the runtime, the bot, play.

    Args:
        compiled: the bot's compiled blueprint.
        prm: its parameter vector (its defaults).
        header: comment lines (without '#') heading the script.
        role_lines: its Team role lines; empty for a bot without a Team overlay.
        max_rounds: the longest match it can play.

    Raises:
        ExportError: the bot has a Team overlay but no role lines, or the reverse.
    """
    cells = team_role_cells([int(v) for v in compiled.spec])
    if bool(cells) != bool(role_lines):
        raise ExportError("a Team overlay's script needs its role, and only it")
    lines = [
        *(f"# {line}".rstrip() for line in header),
        *role_lines,
        "",
        *(f"import {module}" for module in STDLIB_IMPORTS),
        "",
        runtime_source(),
        "",
        *_bot_lines(compiled, prm, cells),
        "",
        _play_source(max_rounds),
    ]
    return "\n".join(lines)


def _header(path: str, description: str) -> list[str]:
    return [
        f"{match.bot_name(path)}: exported by `janken bot export` from {path}",
        "(the janken kit's runtime as plain stdlib Python, and the bot's compiled",
        "blueprint; edit the bot, not this file).",
        "",
        *description.splitlines(),
    ]


def scripts(path: str, max_rounds: int) -> dict[str, str]:
    """The submission scripts of the bot at `path` and of its fleet's supports, by
    bot name: a fleet of N bots makes N scripts. A support's script is the
    champion's, plus a comment naming the support and its role line.

    Raises:
        ExportError: the bot can't be exported (see fleet_of, rewrite_module), or
            it is a mock: it cheats, so it is research only (janken/mocks.py).
    """
    if mocks.is_mock(path):
        raise ExportError(f"{path} is a mock (an Oracle cheats): research only")
    fleet = fleet_of(path)
    found = botfile.read(path)
    compiled = _blueprint(path).compile(found.defaults)
    prm = [float(v) for v in registry.param_vector(path)]
    header = _header(path, found.description)
    if not team_role_cells([int(v) for v in compiled.spec]):
        return {fleet.champion: script(compiled, prm, header, [], max_rounds)}
    out = {
        fleet.champion: script(
            compiled, prm, header, _role_lines(c.CHAMPION, ""), max_rounds
        )
    }
    for support in fleet.supports:
        role = _role_lines(c.SUPPORT, support)
        out[support] = script(compiled, prm, header, role, max_rounds)
    return out
