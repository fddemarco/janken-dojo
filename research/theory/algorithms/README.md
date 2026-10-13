# Algorithm cards

One card per family of learning, statistical or ML algorithm the lab uses, or could
use, to build bot species: what it is, where it lives in the kit (or would), what it
is good at, **how an opponent exploits it**, and what it costs. The paradigm files
(`../01-l1-heuristics.md`, `../02-meta-strategies.md`) say which species use what;
these cards say what each algorithm can and can't do, so a new species starts from a
known strength and a known weakness.

| card | family | in the kit |
|---|---|---|
| [sequence-predictors.md](sequence-predictors.md) | counts, Markov / n-gram, back-off, repeat matching, periods, rotations, geometry | yes: the L1 signals |
| [bandits.md](bandits.md) | Thompson sampling over Dirichlet records, decayed net scores, greedy, drop-switch | yes: every L2+ `Bandit` |
| [gates.md](gates.md) | gatekeepers: EDGE, ANTI_FIRST, MAIN_FIRST, LEADER rules | yes: every `Gate` |
| [bayes-combiners.md](bayes-combiners.md) | naive Bayes over the arms' predictions (TPI-lite) | yes: `NaiveBayes` |
| [replays-and-level-k.md](replays-and-level-k.md) | replaying a bot from either seat, level-k reasoning, parameter identification | yes: `Replay`, `Sim`; research: `janken lab identify` |
| [online-learning.md](online-learning.md) | Hedge / EXP3, context-tree weighting and PPM, online logistic and cost-sensitive regression | candidates (VW tried in the arena) |
| [pretrained-models.md](pretrained-models.md) | small pre-trained models: lookup tables, MLPs, tiny RNNs, decision trees | candidates |
| [statistical-methods.md](statistical-methods.md) | change-point detection, sequential tests, randomness and predictability tests, model selection, multiple comparisons | evaluation: yes; inside bots: candidates |

## The size budget

An exported bot is one stdlib-only Python file, and the tournament accepts files up
to **200 MB**. Pre-trained weights are allowed when they fit in that file as Python
literals (`array.array` of floats, about 8 bytes per weight once written as text, or
denser as packed bytes): roughly **up to 10-20 M parameters** as text literals,
more if packed. Inference must stay fast in plain Python (no numpy in the export):
about 1 ms per move over 1000 rounds is fine, which caps a per-move forward pass at
a few hundred thousand multiply-adds.

The kit's rule still holds: a bot file holds no code, so a pre-trained model would be a
**stage kind** whose weights come from a data file the export inlines
(`pretrained-models.md`, Design).

## The card format

- **What it is**, in two or three lines.
- **In the kit**: the stage, block or command, or "candidate".
- **Strengths**: what it beats, with evidence where we have it.
- **Exploits**: how an opponent beats it, with the counter-species where one exists.
- **Cost**: per-move time and memory; for a model, its size in the export.
- **Ideas**: what to try, as backlog ideas.
