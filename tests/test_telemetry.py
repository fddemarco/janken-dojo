"""janken/telemetry.py: timing spans as JSON lines, and the code fingerprint."""

import json
import os
import pathlib
from collections.abc import Iterator

import pytest

from janken import settings, telemetry


def lines(path: pathlib.Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


@pytest.fixture
def spans_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv(settings.SPANS_ENV, "on")
    yield
    telemetry.SPANS.close()


def spans_file(workspace: pathlib.Path) -> pathlib.Path:
    return workspace / settings.config().telemetry.file


def test_a_span_is_one_json_line_with_its_context(tmp_path: pathlib.Path) -> None:
    spans = telemetry.Spans()
    path = tmp_path / "spans.jsonl"
    spans.configure(str(path), 1, {"command": "lab x"})
    spans.write("engine.play", 1.5, True, {"matches": 3})
    spans.close()
    (line,) = lines(path)
    assert line["op"] == "engine.play"
    assert line["seconds"] == 1.5
    assert line["ok"] is True
    assert line["command"] == "lab x"
    assert line["matches"] == 3
    assert line["pid"] == os.getpid()


@pytest.mark.usefixtures("spans_on")
def test_a_failed_block_is_logged_as_not_ok(tmp_path: pathlib.Path) -> None:
    telemetry.configure(str(tmp_path), "lab x")
    with pytest.raises(RuntimeError), telemetry.span("boom"):
        raise RuntimeError("stop")
    telemetry.SPANS.close()
    (line,) = lines(spans_file(tmp_path))
    assert line["op"] == "boom"
    assert line["ok"] is False
    assert line["command"] == "lab x"
    assert isinstance(line["fingerprint"], str)


@pytest.mark.usefixtures("spans_on")
def test_configuring_twice_writes_each_span_once(tmp_path: pathlib.Path) -> None:
    telemetry.configure(str(tmp_path), "lab x")
    telemetry.configure(str(tmp_path), "lab y")
    with telemetry.span("op"):
        pass
    assert telemetry.SPANS.files == [str(spans_file(tmp_path))]
    telemetry.SPANS.close()
    (line,) = lines(spans_file(tmp_path))
    assert line["command"] == "lab y"


def test_spans_off_write_nothing(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(settings.SPANS_ENV, "off")
    telemetry.configure(str(tmp_path), "lab x")
    with telemetry.span("op"):
        pass
    assert not telemetry.SPANS.active
    assert lines(spans_file(tmp_path)) == []


def test_the_fingerprint_follows_the_code_and_the_bots(tmp_path: pathlib.Path) -> None:
    (tmp_path / "janken" / "__pycache__").mkdir(parents=True)
    (tmp_path / "bots").mkdir()
    code = tmp_path / "janken" / "a.py"
    code.write_text("x = 1\n")
    (tmp_path / "bots" / "b.yaml").write_text("description: b\n")
    before = telemetry.code_fingerprint(str(tmp_path))
    (tmp_path / "janken" / "__pycache__" / "a.pyc").write_bytes(b"\0")
    (tmp_path / "janken" / "notes.txt").write_text("ignored\n")
    assert telemetry.code_fingerprint(str(tmp_path)) == before
    code.write_text("x = 2\n")
    assert telemetry.code_fingerprint(str(tmp_path)) != before
