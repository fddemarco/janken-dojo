---
name: learn
description: Promote a confirmed janken lab finding into research/insights.md with `janken insight add` (which refuses evidence below the bar), strike insights that later results contradict, and turn implications into new ideas. Use after a keep verdict, when `janken status` says learn, or when the user says "write this down".
---

# Learn

`research/insights.md` is the lab's long-term memory. Every design starts from it, so it
stays **true** and **short**. Run every command as `uv run janken ...`.

## The bar

`janken insight add` writes the evidence line from the note's stored numbers. It refuses
a note unless one of these has a **95% CI that excludes 0**:

- a paired comparison in its run;
- for a tuning note, a validated difference from the defaults.

Even then, an insight must be **general enough to steer future bots**:

- not an insight: "bot X with DECAY 0.8 scored 91%";
- an insight: "sampling from confidence-scaled probabilities beats argmax against the
  metabots".

When the evidence is suggestive but short of the bar, add a confirming idea instead
(`janken idea add`, citing the note).

## Record it

```bash
uv run janken insight add --note NNNN \
  --finding "the general claim, one line" \
  --mechanism "why we think it works (say if it's a hypothesis)" \
  --implication "what to build or try next"
uv run janken idea add "**Follow-up**: ..." --priority P1 \
  --motivation "insight of YYYY-MM-DD, [NNNN](experiments/NNNN-x.md)"
```

When a new result contradicts an old insight, strike it. Never delete it:

```bash
uv run janken insight supersede "<unique part of its title>" \
  --by "[NNNN](experiments/NNNN-x.md)"
```

If a technique from `research/rps_kaggle.md` turned out not to work here, say so in the
insight, so it isn't retried. Under `/lab-loop`, commit as `insight: <finding>`.
