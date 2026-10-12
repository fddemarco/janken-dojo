# 0006: which bandit? Thompson vs sharper/softer Thompson vs greedy

- **Date:** 2026-10-10
- **Status:** analyzed
- **Idea:** ideas.md #7 (greedy decayed scores with a random arm pinned at 0), plus a
  Thompson sharpness check
- **Bots:** `bots/smartbot_bandit.py` (new; at its DEFAULTS it is smartbot_sims3 exactly,
  the control), variants `SHARP=3` and `SHARP=0.33` (Thompson counts x3 / x1/3) and
  `SELECT=1` (greedy on decayed w - l, random arm pinned at 0)

## Hypothesis

After [0005](0005-smartbot-sims3.md) the remaining matchups are mostly coin flips against
adaptive bots, so how the bandit commits may matter. Two competing effects: committing
harder (greedy, SHARP 3) exploits the deterministic and biased bots more surely (biased is
at 87-92%), but makes our own output more predictable to the metabots and to the sims of
us. Exploring more (SHARP 0.33) does the opposite.

Expectation: no variant differs from the control by more than +/-2 pts. A variant that
beats it with a paired CI excluding 0 gets kept. If greedy loses, the loss should show in
the metabot / geometry matchups.

## Command

```bash
uv run python -m janken experiment bots/smartbot_bandit.py bots/smartbot_bandit.py:SHARP=3 bots/smartbot_bandit.py:SHARP=0.33 bots/smartbot_bandit.py:SELECT=1 --rounds 200 --round-robins 150 --mode candidates --name 0006-smartbot-bandit
```

Run id: `20261010-001847_0006-smartbot-bandit` (seed 2916842378, 150 round robins, mode
candidates, 12900 matches on numba, 0 forfeits). Labels: `@0eca6f` = SHARP 3,
`@77b3f2` = SHARP 0.33, `@83ebcf` = SELECT 1 (greedy).

## Results

| variant | score vs pool [95% CI] | rounds +/- per match |
|---|---|---|
| Thompson, SHARP 1 (control = sims3) | 84.2% [82.8, 85.4] | +80.7 |
| greedy (SELECT 1) | 83.8% [82.4, 85.1] | +86.4 |
| Thompson, SHARP 0.33 | 83.3% [81.9, 84.6] | +70.5 |
| Thompson, SHARP 3 | 82.8% [81.4, 84.1] | +83.9 |

Paired vs the control (3000 shared matches each): greedy -0.4 pts [-1.9, +1.1],
SHARP 0.33 -0.9 pts [-2.4, +0.7], SHARP 3 -1.4 pts [-2.9, +0.1]. **No variant differs
significantly**, and none of the six pairs does. (The pool now contains smartbot_sims,
sims2 and sims3, so scores are ~3 pts below 0005's.)

Per opponent, the variants trade matchups in a consistent way (paired, 98-124 matches):

- **Greedy** wins more round margin against everything deterministic (word2janken +175
  vs +155, iocaine_lite +164 vs +149, rps4_lite +60 vs +33, biased +5.7 pts), but it is
  **crushed by smartbot_sims3: 15.9% vs 46.4% (-30.5 pts), margin -17.2 vs -1.1**. Its
  choice is a deterministic function of the decayed arm scores, which is exactly what
  sims3's metabot replay (same base predictors, same counts) reconstructs, so sims3 reads
  it almost every round. Against the other sims bots it also loses (sims2 -8.5).
- **SHARP 0.33** (more exploration) gives up margin everywhere (iocaine_lite +89 vs
  +149, word2janken +120 vs +155) and loses smartbot -11.4, biased -8.0.
- **SHARP 3** loses the sims family and the metabots (-9...-11 pts each), gains biased +5.2
  and transition_matrix +6.4.

## Verdict

**drop** (all three variants; smartbot_sims3's Thompson at SHARP 1 stays). Bandit
sharpness is a trade-off between exploiting static bots and being readable by adaptive
ones, and in this pool the two cancel. The striking per-opponent finding is that a greedy
bandit becomes a near-deterministic target for a replay of its own arm scores (-30.5 pts
vs smartbot_sims3): the predictability protection of Thompson sampling matters once the
field contains sims. Idea #10 (sampling the final move) now has a sharper motivation:
it could keep greedy's commitment against static bots without its readability.
