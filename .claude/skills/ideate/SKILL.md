---
name: ideate
description: Find what to try next in the janken bot lab - read the insights, the weakest matchups of the best bots, the Kaggle RPS notes and the source cards, and add well-motivated ideas to the backlog with `janken idea add`. Use when the backlog is empty or stale, after a run of dropped verdicts, or when the user asks for new ideas.
---

# Ideate

An idea is worth adding when it names **what to build**, **why it should win** and **the
evidence or source** behind that. Everything here is read-only except `janken idea add`.
Run every command as `uv run janken ...`.

## 1. Read the state

```bash
uv run janken status                       # next step, open ideas, leaderboard
uv run janken insight list                 # what is known
uv run janken idea list --all              # what was tried (done / dropped)
uv run janken lab leaderboard --rounds 200 # the current best candidates
uv run janken lab report <best bot's latest run>   # its weakest matchups
```

Then the background: `research/rps_kaggle.md` (techniques, §4–7) and `research/sources/`
(one card per external resource: claims vs evidence, ideas spawned).

## 2. Look for leverage

- **Weakest matchups** of the best bot, against the strong opponents (metabots, the
  staller family, geometry, iocaine, rps4). Headline scores saturate near 85–95%, so the
  decisive information is there. Dig in:
  `janken lab query "SELECT ... FROM matches WHERE ..."` and `janken lab match A B` for
  transcripts.
- **Insight implications** not yet in the backlog.
- **Dropped ideas** whose verdict suggested a variant.
- **Techniques** from `rps_kaggle.md` / `sources/` the kit can express (or that need one
  new stage kind).

## 3. Add them

```bash
uv run janken idea add "**Name**: what to build, in one line" \
  --priority P1 --motivation "the evidence: note/insight/source link"
```

- **Priority.** P1 is a likely big win with direct evidence. P2 is plausible. P3 is a
  curiosity.
- **Motivation.** It cites a note (`[0005](experiments/0005-x.md)`), an insight or a
  source card. An idea without one isn't added.
- **One line**, without `|`.
- **No duplicates:** check `idea list --all` first, and extend an existing idea's
  thinking instead of re-adding it.

Hand back the new idea numbers. Under `/lab-loop`, commit them as `ideas: <what changed>`.
