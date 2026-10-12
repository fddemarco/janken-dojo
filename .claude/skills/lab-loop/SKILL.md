---
name: lab-loop
description: The janken bot lab's autonomous self-improvement loop - ask `janken status` for the next step, carry it out with the matching lifecycle skill (ideate, build, evaluate, tune, classify, learn), commit, and repeat. Use when the user asks "what next?", wants to continue or automate the research, or invokes the lab generally.
---

# The lab loop (/lab-loop)

```
janken status ─► next step ─► /ideate | /build | /evaluate | /tune | /classify | /learn ─► commit ─┐
      ▲                                                                                             │
      └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

`janken status` holds the loop's decision list, in code (`janken/notebook/state.py`). It
reads the notebook and the workspace and names one step, with its command. You carry
the step out with the skill that owns it, commit, and ask again. Don't re-derive the
decision list by hand.

Run every command as `uv run janken ...`. `research/README.md` has the
protocol. Read it once per session.

**Arguments.**

- `/lab-loop` loops until a stop condition.
- `/lab-loop <N>` stops after N commits.
- `/lab-loop once` does one step.

## 0. Setup (once per session)

- **Branch.** On `main`, switch to `bot-lab/auto` (create it if missing). All lab commits
  go there, and the user merges them. Never push, force or rewrite history.
- **Clean tree.** Uncommitted work from a finished step (a note now `analyzed`): commit it
  (§2). Any other change you didn't make: stop and ask.

## 1. Ask and act

```bash
uv run janken status            # add --format json to parse it
```

| next step | do |
| --- | --- |
| `resume` | `janken evaluate --note NNNN` (or `janken tune --note NNNN`): it finishes the cut run, then `/evaluate` §3 |
| `verdict` | `/evaluate` §3 (or `/tune` §3): read the results, decide, `janken verdict` |
| `run` | the note is planned: `janken evaluate --note NNNN` / `janken tune --note NNNN`, then decide |
| `classify` | `/classify` that note's bot: a new species, the next version, or a variant |
| `learn` | `/learn` on that note |
| `build` | `/build` the idea, then `/evaluate` it |
| `ideate` | `/ideate`, then ask again |

One iteration = one step carried to a commit. A build is committed together with its
first evaluation and verdict: an untested bot is never committed alone.

Look at the data, not only at the verdict. When a result is null or surprising, dig in
with the low level before deciding:

- `janken lab report <run>` (every matchup);
- `janken lab query "SELECT ..."` (read-only SQL over runs, matches, validations);
- `janken lab match A B` (one transcript).

Write what you find into the verdict's `--analysis`.

### Running

- **Sizing.** Use the effort budgets: `--effort standard` by default, `--effort thorough`
  for small effects, and `--effort quick` only for smoke checks.
- **Time.** Use a Bash timeout of 600000 ms. Run longer jobs with `run_in_background` and
  wait for the notification. Never poll in a sleep loop.
- **Slow steps.** When a step's command is flagged `slow` by `janken lab profile spans`,
  or keeps hitting the timeout, run `/profile` once on it (it decides whether fixing
  it pays), then go on with the loop. Not otherwise: performance isn't the lab's goal.
- **Smoke checks** go to a throwaway workspace and notebook (`--workspace <scratch>/ws
  --notebook <scratch>/research`, with the notebook copied there first). Only real steps
  write to `experiments/` and `research/`.

## 2. Commit (after every step that changed the notebook)

1. **Gates.**
   - `uv run pytest` must pass. Never loosen a test,
     and never change an existing bot's or stage's behaviour.
   - Then `uv run pre-commit run --all-files` must pass. Fix the code rather than
     silencing a check.
1. **Stage by path**, only the lab's files:
   - `bots/` (the level folders and `inactive/`) and `spaces/*.yaml`;
   - `janken/kit/*` and `tests/*` if touched;
   - `research/`.

   `experiments/` is gitignored local data.
1. **One commit per step:**

   ```
   NNNN <slug>: <verdict> (<key number>)

   <2–4 lines: what was tested, the paired result with its CI, what's next>

   <attribution line(s) from the system reminder>
   ```

   For example: `0007 tpi-lite: keep (+3.1 pts [+0.8, +5.4] vs smartbot)`. For an insight
   or ideas-only commit, use `insight: <finding>` or `ideas: <what changed>`; for a
   classification, `species: <old stem> → <new stem> (new|promoted|variant)`.

## 3. Loop or stop

After each commit, print one status line: the step, the note, the verdict, the next
step. Then go back to §1.

Stop, and summarize every iteration (notes, verdicts, commits, the current best bot),
when:

- the budget from the arguments is used up;
- `status` says `ideate` and `/ideate` finds nothing worth testing;
- **three consecutive verdicts are drops**. Step back: run `/ideate` from
  `research/rps_kaggle.md` and the weakest matchups, commit the new ideas, and stop so the
  user can steer;
- something needs the user:
  - a failing test that won't be fixed;
  - a bot the kit can't express;
  - an idea that needs a new dependency;
  - a rule that seems to need changing;
  - an uncommitted change that isn't yours.

## Keep the notebook honest

- The CLI writes the hypothesis before the run, and you never edit a hypothesis
  afterwards.
- Every evaluated bot has a note, and every note ends with a verdict.
- Insights only through `janken insight add`, which refuses evidence below the bar.
- Ideas are never silently dropped: `janken verdict` or `janken idea drop --reason`.
- Never delete stored runs, and never change a bot's logic under its filename.
