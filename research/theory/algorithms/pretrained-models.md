# Pre-trained small models

**What.** A model trained offline on the move dataset (`janken lab dataset`: every
round of every match the lab has played) and frozen into the bot: it maps the recent
history (and possibly the arms' predictions) to a distribution over the opponent's
next move, or directly to our move.

## Candidates, by size

| model | inputs | parameters | export size (as text literals) | per-move cost |
|---|---|---|---|---|
| lookup table on the last k joint moves | 9^k contexts x 3 | k = 5: 177 k | ~1.5 MB | one index |
| logistic regression on hashed features | 2^16 features x 3 | 197 k | ~1.6 MB | features x 3 |
| MLP, 2 layers of 256 on a one-hot window of 16 rounds | 144 x 256 + 256 x 256 + 256 x 3 | ~103 k | ~1 MB | ~100 k multiply-adds |
| tiny GRU, hidden 64, over the joint move stream | 3 x (9 x 64 + 64 x 64 + 64) | ~14 k | ~0.1 MB | ~13 k per move |
| gradient-boosted trees, 500 trees of depth 6 | the arms' predictions and counts | ~32 k nodes | ~0.5 MB | 3000 comparisons |

All of these sit far under the **200 MB** export cap (`README.md`, The size budget);
the binding limit is the plain-Python inference time, not the size. A model of
10-20 M parameters would fit as literals but cost seconds per move in pure Python, so
**the practical ceiling is about 100-300 k parameters per forward pass**.

## Strengths

- **A prior over opponents before the match starts:** most L1-L3 bots are the same
  few algorithms, so a model trained on the field's matches recognises them from a
  few rounds of evidence, where an online learner starts from nothing.
- **Learned features:** interactions a hand-made signal doesn't encode.

## Exploits

- **Distribution shift:** trained on the lab's field, it is confidently wrong against
  bots unlike the field (the identification study's lesson: -12.8 pts vs unknown
  architectures when trusted blindly). It needs an online check (a gate or a bandit
  arm, never the only voice).
- **Frozen, so replayable:** a published model is a deterministic function of the
  history; an opponent who has it beats it like any replay. It has to be one arm among
  adaptive ones.
- **Overfitting the training opponents' parameters:** train on parameter variants
  (`pool.variants`), not defaults only.

## Design (how the kit would host it)

- A new stage kind (a signal, say `Pretrained`) whose weights are a data file under
  `bots/models/` (the bot file names it, holds no code), loaded at compile time.
- `janken bot export` inlines the weights as `array.array` literals; the script's
  inference is the stage's compiled code, rewritten to plain Python like every stage.
- Training is research code (`janken/experimental/`, third-party libraries allowed);
  only the frozen weights cross into the kit.

## First probe (2026-10-13)

`janken/experimental/pretrained.py`: a k = 3 joint-context table trained on the
grown move dataset (2811 matches, both seats, training split), refined online. On
93 held-out parameter variants of the L1/L2 field (3 seeds x 250 rounds, paired),
a prior worth 5 observations per context adds +6.6 pts of net rounds +- 1.6 over the
same table learned online from zero (+20.8% vs +14.3% net), which puts a plain table
level with `context_mixture_v1` (+20.8%); a prior worth 20 adds less (+2.6 +- 1.8),
since it must give way to the match's own evidence. The prior generalises to
parameters it never saw. Ideas #72, #74, #75 build on it.

## In the kit (2026-10-13)

The `PriorTable` signal carries the trained table in the bot's knobs (export inlines
it). As an L1 (`pretrained_context_v1`) it beats `context_mixture_v1` by +9.8 pts
[+5.6, +14.4] on parameter variants it never saw (notes 0072, 0073). As one more arm
of `repeat_mirror` it adds nothing measurable (+1.1 pts [-4.5, +7.0], note 0077):
**pre-training pays where the learner starts weak**, not beside strong online arms
that learn the same contexts within the match.

## Ideas

- A k = 5 lookup table of the opponent's next move given the joint context, trained
  on the dataset, as an arm beside the repeat followers: the cheapest test of a
  pre-trained prior.
- A tiny GRU next-move model, trained on L1-L3 matches with parameter variants,
  judged as a bandit arm on pools of L1-L3.
