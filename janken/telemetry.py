"""Timing spans: how long each coarse operation takes, logged as JSON lines (loguru).

Every lab command logs a `command` span (janken/cli/options.py), and the costly steps
inside it log their own: compiling and playing (janken/engine), a round robin, a
tuning trial, a dataset batch. Nothing finer: a span per match or per round would
cost more than it tells. The lines go to `telemetry.file` in the workspace, rotated
at `telemetry.max_mb`; `janken lab profile spans` reads them (janken/lab/profiling.py).

    {"ts": "...", "op": "engine.play", "seconds": 1.93, "ok": true, "pid": 4242,
     "command": "lab experiment", "fingerprint": "...", "matches": 420, "rounds": 200}

Spans are off when `telemetry.spans` is false or $JANKEN_SPANS=off (the test suite,
and every command `lab profile` runs, so the profiler's overhead never enters the
analytics). Until `configure` adds a sink, `span` only times the block.
"""

import contextlib
import datetime
import hashlib
import json
import os
import time
from collections.abc import Generator, Iterator

import loguru

from . import settings

KIND = "span"
# What a code fingerprint covers, under the project root: the code, the bots, and the
# locked dependencies.
FINGERPRINT_SOURCES: tuple[tuple[str, str], ...] = (
    ("janken", ".py"),
    ("bots", ".yaml"),
)
FINGERPRINT_FILES: tuple[str, ...] = ("uv.lock",)


def _keep(record: "loguru.Record") -> bool:
    return record["extra"].get("kind") == KIND


class Spans:
    """The process's span sinks (one per file) and the context every span carries."""

    def __init__(self) -> None:
        self._sinks: dict[str, int] = {}
        self._context: dict[str, object] = {}
        self._default_removed: bool = False

    @property
    def active(self) -> bool:
        """Whether spans are written anywhere."""
        return bool(self._sinks)

    @property
    def files(self) -> list[str]:
        """The files spans are written to."""
        return sorted(self._sinks)

    def configure(self, path: str, max_mb: int, context: dict[str, object]) -> None:
        """Write spans to `path` (once per path), each carrying `context`."""
        self._context = dict(context)
        if path in self._sinks:
            return
        if not self._default_removed:
            loguru.logger.remove()  # loguru's stderr handler: spans are data, not chatter
            self._default_removed = True
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._sinks[path] = loguru.logger.add(
            path,
            format="{extra[line]}",
            filter=_keep,
            rotation=f"{max_mb} MB",
            level="INFO",
            catch=True,
        )

    def close(self) -> None:
        """Stop writing spans (every sink this object added is removed)."""
        for sink in self._sinks.values():
            loguru.logger.remove(sink)
        self._sinks.clear()
        self._context = {}

    def write(self, op: str, seconds: float, ok: bool, fields: dict[str, object]) -> None:
        """Log one span, if any sink is configured."""
        if not self._sinks:
            return
        payload = {
            "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "op": op,
            "seconds": round(seconds, 6),
            "ok": ok,
            "pid": os.getpid(),
            **self._context,
            **fields,
        }
        line = json.dumps(payload, default=str)
        loguru.logger.bind(kind=KIND, line=line).info(op)


SPANS = Spans()


def configure(workspace: str, command: str) -> None:
    """Log the spans of `command` to the workspace's spans file, if spans are on;
    every span carries the command and the code's fingerprint."""
    if not settings.spans_enabled(os.environ):
        SPANS.close()
        return
    cfg = settings.config().telemetry
    context: dict[str, object] = {
        "command": command,
        "fingerprint": code_fingerprint(),
    }
    SPANS.configure(os.path.join(workspace, cfg.file), cfg.max_mb, context)


@contextlib.contextmanager
def span(op: str, **fields: object) -> Generator[None]:
    """Time the block and log it as span `op` (with `fields`), even if it raises."""
    started = time.perf_counter()
    ok = False
    try:
        yield
        ok = True
    finally:
        SPANS.write(op, time.perf_counter() - started, ok, fields)


def _sources(root: str) -> Iterator[str]:
    for folder, suffix in FINGERPRINT_SOURCES:
        for parent, dirs, names in os.walk(os.path.join(root, folder)):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            yield from (
                os.path.join(parent, n) for n in sorted(names) if n.endswith(suffix)
            )
    for name in FINGERPRINT_FILES:
        path = os.path.join(root, name)
        if os.path.isfile(path):
            yield path


def code_fingerprint(root: str = settings.ROOT) -> str:
    """A short hash of the code, the bots and the locked dependencies under `root`:
    equal fingerprints mean nothing that sets the speed has changed."""
    digest = hashlib.sha256()
    for path in _sources(root):
        digest.update(os.path.relpath(path, root).encode())
        with open(path, "rb") as f:
            digest.update(f.read())
    return digest.hexdigest()[:16]
