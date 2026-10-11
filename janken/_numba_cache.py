"""Where numba caches compiled code: one directory per version of the bot library.

numba's on-disk cache only notices edits to the file a cached function lives in,
so a bot compiled against an older `janken/kit` would keep running stale code.
The cache directory is therefore named after a hash of the library and engine
sources: editing either starts a fresh cache. (Editing a bot is handled by its
own file's timestamp, plus the engine's dispatcher, whose name hashes the bot
sources; see engine/build.py.)

Only used when caching is on (janken/settings.py); janken/kit/jit.py calls
`configure` before decorating, because numba picks the cache location then. The
location is computed once per process, from $NUMBA_CACHE_DIR (or
~/.cache/janken-numba) plus the library hash, and handed to numba through
$NUMBA_CACHE_DIR.
"""

import functools
import hashlib
import os

import numba
import numba.core.config

_HERE = os.path.dirname(os.path.abspath(__file__))
_LIBRARY = ("kit", "engine")


@functools.cache
def digest() -> str:
    """A hash of numba's version and every source file of the kit and the engine."""
    h = hashlib.sha256(numba.__version__.encode())
    for package in _LIBRARY:
        root = os.path.join(_HERE, package)
        for folder, dirs, files in sorted(os.walk(root)):
            dirs.sort()
            for name in sorted(files):
                if name.endswith(".py"):
                    path = os.path.join(folder, name)
                    with open(path, "rb") as f:
                        rel = os.path.relpath(path, _HERE)
                        h.update(rel.encode() + b"\0" + f.read())
    return h.hexdigest()[:16]


@functools.cache
def cache_dir() -> str:
    """This library version's cache directory."""
    base = os.environ.get("NUMBA_CACHE_DIR") or os.path.join(
        os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"),
        "janken-numba",
    )
    return os.path.join(base, digest())


def configure() -> None:
    """Point numba's on-disk cache at this library version's directory."""
    target = cache_dir()
    if os.environ.get("NUMBA_CACHE_DIR") != target:
        os.environ["NUMBA_CACHE_DIR"] = target
        numba.core.config.reload_config()
