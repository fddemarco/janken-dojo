---
name: write-tests
description: Write or change tests in the janken repo - isolated unit tests of the package's logic on synthetic data (never the lab's real bots, spaces, notebook, config or runs), in pytest style, as fast as possible, with JIT off and heavy tests behind the `heavy` marker. Use whenever a task adds or edits a file under tests/, adds a stage kind (/build), or a test fails and the question is whether the test or the code is wrong.
---

# Write tests

The suite tests the **package** (`janken/`), nothing else. It must pass on a fresh
clone with `bots/`, `spaces/`, `research/`, `experiments/` and `janken.local.toml`
deleted, and give the same result whatever they hold.

## Isolation: the rule

A test depends only on the code under test and data it builds itself:

- **Never read the lab's state.** No test opens `bots/`, `spaces/`, `research/`,
  `experiments/` (runs, studies, the dataset, logs) or `exports/`. Those change every
  day; a test that reads them fails when a bot is retired, renamed or tuned, not when
  the code breaks.
- **Never read the real configuration.** `tests/conftest.py` points `$JANKEN_CONFIG`
  at `tests/data/janken.toml` with no local overrides. Build a `Config` or a
  sub-config (`dataclasses.replace`) when a test needs specific values; don't assert
  on what janken.toml happens to say.
- **Never depend on history or the machine.** No current date or time unless pinned,
  no numba cache, no timing, no network, no ordering of directory listings or of
  earlier tests, no absolute or cwd-relative path shapes in messages.
- **Test rules on parsed objects.** Check logic against what parsing returns (a
  `Blueprint`, a `Space`, a `Species` row, `integrity.BotFacts`), built in the test
  with `janken/kit/bot.py` or the dataclasses. Parsing gets its own tests (YAML
  grammar: `tests/test_declare.py`), on strings written in the test.
- **The field's own consistency is not a unit test.** That every real bot compiles,
  sits in its level folder, has a fitting space, agrees with species.md is checked by
  `janken bot audit` (janken/integrity.py), run by pre-commit. The real config's
  validity is `janken config check`; the CLI reference's freshness is
  `python -m janken.cli.reference --check`. Add new repo-consistency rules there, as
  pure functions with unit tests on synthetic data.

When a test needs bot **files** (the engine, the dataset, the CLI take paths), write
them under `tmp_path` from strings in the test, or use the frozen test library
(`from tests import data`: `data.bot(stem)`, `data.BOTS_DIR`, `data.SPACES_DIR`,
`data.RESEARCH`). Never copy from `bots/` at test time. Change `tests/data/` only to
test something new, never to follow an edit to the lab's own bots.

## Speed

Tests are as fast as possible: the default run takes seconds and must stay under 60 s.

- Unit tests of logic only: no stress, load, benchmark or compute-intensive tests.
  Nothing compiles: conftest switches the JIT off, so bots, stages and the referee run
  as plain Python.
- Playing rounds is integration testing: do it only when the logic needs a match, with
  a few fast bots (L1 heuristics or hand-written kernel modules, never L3+ replays),
  **fewer than 10 rounds**, the smallest pool and trial count that shows the behaviour,
  and fixed seeds. Prefer calling the function under test on a hand-made history.
- A test still heavy after that (over ~1 s, a full CLI loop, an Optuna study, a replay
  of an L3+ bot) gets `@pytest.mark.heavy`: `uv run pytest` deselects it, and it runs
  only to validate a change it covers (`uv run pytest -m heavy`). Check with
  `uv run pytest --durations=15` that no unmarked test is heavy.

## Shape

- pytest style: plain `assert`, `pytest.raises`, fixtures (`tmp_path`, `monkeypatch`)
  for setup, `pytest.mark.parametrize` for cases that are data (`subtests` where they
  aren't). No `unittest.TestCase`. Type hints on every signature, as in `janken/`.
- A test that writes passes its own temporary `--workspace`, `--bots-dir`,
  `--spaces-dir` and `--notebook`; the test config's defaults point nowhere real.
- Never loosen a test to make it pass. If it reads lab state or config, rewrite it on
  synthetic data; if it caught a real inconsistency, fix the code or the data.

## Verify

```bash
uv run pytest                  # seconds, JIT off, heavy tests deselected
uv run pytest -m heavy         # only when a change touches what they cover
```

A new test that only passes with the lab's current files present is wrong: run it
mentally against an empty `bots/` and an unusual `janken.local.toml`.
