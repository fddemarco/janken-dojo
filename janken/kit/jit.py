"""The decorators every compiled function in janken uses, bots included.

    @kernel            numba's njit
    @parallel_kernel   njit(parallel=True), for the referee's prange loop

Whether they compile, and whether numba keeps the compiled code on disk, comes from
janken/settings.py at decoration time: the JIT can be switched off (the test suite
runs everything as plain Python), and the on-disk cache is only used by the
compute-intensive commands. Nothing else in janken calls numba's decorators.
"""

import os
from collections.abc import Callable
from typing import TypeVar, cast

import numba

from .. import _numba_cache, settings

F = TypeVar("F", bound=Callable[..., object])


def _compile(fn: F, parallel: bool) -> F:
    current = settings.load(os.environ)
    if not current.jit:
        return fn
    if current.cache:
        _numba_cache.configure()
    return cast(F, numba.njit(cache=current.cache, parallel=parallel)(fn))


def kernel(fn: F) -> F:
    """`fn` compiled by numba, or `fn` itself when the JIT is off."""
    return _compile(fn, parallel=False)


def parallel_kernel(fn: F) -> F:
    """Like `kernel`, with numba's parallel loops (`numba.prange`) enabled."""
    return _compile(fn, parallel=True)
