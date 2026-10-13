"""janken/lab/match_cache.py: a match already played is read back, never replayed,
and only while nothing that decides it changed."""

import os
import pathlib
import shutil

import pytest

from janken.lab import match_cache
from janken.lab.match_cache import MatchCache
from janken.lab.runs_db import RunStore
from janken.match import MatchResult
from janken.spec import BotSpec, make_spec
from tests import data

ROUNDS = 6


class Counted:
    """engine.play_pairs, counting the matches it plays."""

    def __init__(self) -> None:
        self.played = 0
        self.real = match_cache.play_pairs

    def __call__(self, pairs, rounds, seeds, workers, on_done, flush_s):
        self.played += len(pairs)
        return self.real(pairs, rounds, seeds, workers, on_done, flush_s)


@pytest.fixture
def counted(monkeypatch: pytest.MonkeyPatch) -> Counted:
    engine = Counted()
    monkeypatch.setattr(match_cache, "play_pairs", engine)
    return engine


@pytest.fixture
def bots(tmp_path: pathlib.Path) -> pathlib.Path:
    """Copies of two light bots, so a test may edit one."""
    level = tmp_path / "bots" / "l1"
    level.mkdir(parents=True)
    for stem in ("cycler_v1", "copycat_v1"):
        shutil.copy(os.path.join(data.BOTS_DIR, "l1", stem + ".yaml"), level)
    return level


def pairs(bots: pathlib.Path) -> list[tuple[BotSpec, BotSpec]]:
    cycler = make_spec(str(bots / "cycler_v1.yaml"))
    copycat = make_spec(str(bots / "copycat_v1.yaml"))
    return [(cycler, copycat), (copycat, cycler)]


def cache_in(tmp_path: pathlib.Path, enabled: bool = True) -> MatchCache:
    return MatchCache(RunStore.at(str(tmp_path / "ws")), enabled)


def test_a_match_played_again_is_read_back(
    tmp_path: pathlib.Path, bots: pathlib.Path, counted: Counted
) -> None:
    cache = cache_in(tmp_path)
    first = cache.play(pairs(bots), ROUNDS, [1, 2])
    reported: list[tuple[int, MatchResult]] = []
    again = cache.play(pairs(bots), ROUNDS, [1, 2], on_done=reported.extend)
    assert counted.played == 2
    assert again == first
    assert sorted(k for k, _ in reported) == [0, 1]


def test_only_the_matches_not_kept_are_played(
    tmp_path: pathlib.Path, bots: pathlib.Path, counted: Counted
) -> None:
    cache = cache_in(tmp_path)
    cache.play(pairs(bots)[:1], ROUNDS, [1])
    both = cache.play(pairs(bots), ROUNDS, [1, 2])
    assert counted.played == 2
    assert [m.bot_a for m in both] == ["cycler_v1", "copycat_v1"]


def test_another_seed_rounds_or_override_is_another_match(
    tmp_path: pathlib.Path, bots: pathlib.Path, counted: Counted
) -> None:
    cache = cache_in(tmp_path)
    (pair, _) = pairs(bots)
    cache.play([pair], ROUNDS, [1])
    cache.play([pair], ROUNDS, [2])
    cache.play([pair], ROUNDS + 1, [1])
    noisy = make_spec(pair[0].path, {"NOISE": 0.5})
    cache.play([(noisy, pair[1])], ROUNDS, [1])
    assert counted.played == 4


def test_an_edited_bot_is_played_again(
    tmp_path: pathlib.Path, bots: pathlib.Path, counted: Counted
) -> None:
    cache = cache_in(tmp_path)
    cache.play(pairs(bots), ROUNDS, [1, 2])
    path = bots / "cycler_v1.yaml"
    path.write_text(path.read_text() + "\n# edited\n")
    cache.play(pairs(bots), ROUNDS, [1, 2])
    assert counted.played == 4


def test_a_read_back_match_carries_the_labels_it_is_played_under(
    tmp_path: pathlib.Path, bots: pathlib.Path
) -> None:
    cache = cache_in(tmp_path)
    (a, b), _ = pairs(bots)
    cache.play([(a, b)], ROUNDS, [1])
    renamed = BotSpec(path=a.path, params=a.params, label="champion")
    (m,) = cache.play([(renamed, b)], ROUNDS, [1])
    assert m.bot_a == "champion"


def test_a_disabled_cache_plays_and_keeps_nothing(
    tmp_path: pathlib.Path, bots: pathlib.Path, counted: Counted
) -> None:
    cache = cache_in(tmp_path, enabled=False)
    cache.play(pairs(bots), ROUNDS, [1, 2])
    cache.play(pairs(bots), ROUNDS, [1, 2])
    assert counted.played == 4
    assert not RunStore.at(str(tmp_path / "ws")).exists()
