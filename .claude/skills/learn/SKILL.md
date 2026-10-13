---
name: learn
description: Record a janken lab finding in research/insights.md with `janken insight add` (citing one or more notes' stored results, marked tentative when no CI excludes 0), strike insights that later results contradict, and turn implications into new ideas. Use after a keep verdict, when `janken status` says learn, or when the user says "write this down".
---

# Learn

`research/insights.md` is the lab's long-term memory. Every design starts from it, so it
stays **true** and **short**. Run every command as `uv run janken ...`.

## The evidence

`janken insight add` writes the evidence line from the cited notes' stored numbers:
each note's paired comparisons (for a tuning note, its validated differences from the
defaults) whose **95% CI excludes 0**, or, when none does, all of them marked
**tentative**. A note whose run is no longer in the workspace is read from the
comparisons its text records. A note with no result at all can't be cited.

- **Significant** (a CI excludes 0): the insight stands on it.
- **Tentative** (every CI includes 0): still worth recording when it steers future bots,
  for example "equal and N times cheaper", or one finding repeated across several notes.
  Say so in the finding ("about as good as", "no worse than"), and add a confirming idea
  when it matters (`janken idea add`, citing the note).
- **One finding, several notes:** repeat `--note` (`--note 0035 --note 0036 ...`), so
  the insight cites them all, and `janken status` stops asking about each.

Either way, an insight must be **general enough to steer future bots**:

- not an insight: "bot X with DECAY 0.8 scored 91%";
- an insight: "sampling from confidence-scaled probabilities beats argmax against the
  metabots".

## Record it

```bash
uv run janken insight add --note NNNN [--note MMMM ...] \
  --finding "the general claim, one line" \
  --mechanism "why we think it works (say if it's a hypothesis)" \
  --implication "what to build or try next"
uv run janken idea add "**Follow-up**: ..." --priority P1 \
  --motivation "insight of YYYY-MM-DD, [NNNN](experiments/NNNN-x.md)"
```

Then update `research/theory/`: the claim the insight supports, refutes or opens in
its paradigm's file (status, evidence, prediction), and a journal line in
`theory/README.md` when a paradigm changes phase.

When a new result contradicts an old insight, strike it. Never delete it:

```bash
uv run janken insight supersede "<unique part of its title>" \
  --by "[NNNN](experiments/NNNN-x.md)"
```

If a technique from `research/rps_kaggle.md` turned out not to work here, say so in the
insight, so it isn't retried. Under `/lab-loop`, commit as `insight: <finding>`.
