"""Knobs bound to values: a bot's parameters fixed in its blueprint.

A Knob in a blueprint is a parameter of the bot, read at run time from its `prm`
vector, so tuning never recompiles. A few fields can't be read at run time,
because they shape the compiled state (an n-gram's order, the history a matcher
reads, whether a signal samples): their type takes no Knob. A Knob there is a
**structural** parameter, bound to a literal when the bot is compiled (from its
defaults) or named as an arm (from the arm's values, refs.py), never tuned.

    knob_names(node)           every parameter a blueprint (or a part of it) reads
    structural_names(node)     those read where only a literal fits
    bind(node, values)         every Knob named in `values` replaced by its value
"""

import dataclasses
import functools
import types
import typing
from collections.abc import Mapping

from .base import Knob, Value

if typing.TYPE_CHECKING:
    from _typeshed import DataclassInstance


def knob_names(node: object) -> set[str]:
    """The parameter names read by every Knob in `node` (a blueprint or any part)."""
    if isinstance(node, Knob):
        return {node.name}
    if isinstance(node, tuple):
        return set().union(*(knob_names(x) for x in node))
    if _is_node(node):
        return set().union(
            *(knob_names(getattr(node, f.name)) for f in dataclasses.fields(node))
        )
    return set()


def structural_names(node: object) -> set[str]:
    """The parameter names read by a Knob in a field whose type takes no Knob."""
    if isinstance(node, tuple):
        return set().union(*(structural_names(x) for x in node))
    if not _is_node(node):
        return set()
    found: set[str] = set()
    hints = _hints(type(node))
    for f in dataclasses.fields(node):
        field_value = getattr(node, f.name)
        if not _takes_knob(hints[f.name]):
            found |= _knobs_here(field_value)
        found |= structural_names(field_value)
    return found


def bind(node: object, values: Mapping[str, Value]) -> typing.Any:
    """`node` with every Knob named in `values` replaced by its value."""
    if isinstance(node, Knob):
        return values.get(node.name, node)
    if isinstance(node, tuple):
        return tuple(bind(x, values) for x in node)
    if _is_node(node):
        changes = {f.name: bind(getattr(node, f.name), values) for f in _fields(node)}
        return dataclasses.replace(node, **changes)
    return node


def _is_node(node: object) -> "typing.TypeGuard[DataclassInstance]":
    return dataclasses.is_dataclass(node) and not isinstance(node, type)


def _fields(node: "DataclassInstance") -> tuple[dataclasses.Field, ...]:
    """The fields `dataclasses.replace` can set (its init fields)."""
    return tuple(f for f in dataclasses.fields(node) if f.init)


def _knobs_here(value: object) -> set[str]:
    """The Knobs a field holds itself (directly or in a tuple), not in sub-nodes."""
    if isinstance(value, Knob):
        return {value.name}
    if isinstance(value, tuple):
        return set().union(*(_knobs_here(x) for x in value))
    return set()


@functools.cache
def _hints(cls: type) -> dict[str, object]:
    return typing.get_type_hints(cls)


def _takes_knob(hint: object) -> bool:
    """Whether a field of this type may hold a Knob (Value, or a tuple of them)."""
    if hint is Knob:
        return True
    if isinstance(hint, types.UnionType) or typing.get_origin(hint) is not None:
        return any(_takes_knob(arg) for arg in typing.get_args(hint))
    return False
