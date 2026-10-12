# Source card: Daniel Lawrence Lu, "Rock Paper Scissors Algorithms" (2011)

## Source

- URL: https://daniel.lawrence.lu/blog/2011-01-01-rock-paper-scissors-algorithms/
- Read: 2026-10-10, directly (static page).
- Author: dllu, author of several rpscontest.com top entries (*Testing Please Ignore*, dllu1;
  see `rps_kaggle.md` section 4.2).

## Summary

A survey of the ideas behind strong rpscontest bots, organised as layers. At the bottom are
basic predictors. Each one turns into six meta-strategies (Iocaine Powder style). A
*selector* picks among those by past performance, and a *selector of selectors* picks among
the selection rules. A random predictor in the pool is the defence. The post reports no
benchmarks and no tuned values; the numbers in it are examples.

Its premise matches ours: random play guarantees a draw on average, so anything above that
comes from exploiting non-random opponents. If one bot in ten always plays rock, always
playing paper already wins 55% instead of 50%.

## Key techniques

### Basic predictors (roughly increasing strength)

1. **Fixed move.** Trivially exploitable.
1. **Frequency counting.** Count each opponent move and play the beat of the most frequent
   one. The **Boltzmann counter** variant decays the counts so recent moves weigh more, and
   when the opponent plays X it also *decrements the move that X beats*. So rock --> paper's
   score goes up and scissors' score goes down.
1. **Rotation.** With moves as Z3, rotation 0 = same move, +1 = the move that beats it,
   +2 = the move that loses to it. *Beat Last Input* plays rotation +1 of the opponent's
   last move.
1. **Anti-rotation.** Infer which rotation took the opponent from their second-to-last move
   to their last move, then counter the continuation (play rotation +2 relative to our own
   last move).
1. **History string matching** (PPM-like). Find the most recent earlier occurrence of the
   current history suffix (`str.rfind`), predict the move that followed it, and play its
   beat. Variants match the opponent's history, ours, or the joint one, and use the earliest
   match or all matches.

### Six meta-strategies per predictor

- **P0**: play the predictor's beat.
- **P'0**: swap roles. Run the predictor on *our* history as if we were the opponent, and
  beat what a copy of it would expect from us.
- **P1, P'1, P2, P'2**: rotate the previous level by +2 each time, so each level counters an
  opponent who counters the one below. P0 beats P'2 and the cycle closes.

### Metastrategy selection (scoring the arms)

| rule | update | trait |
|---|---|---|
| naive | +1 win, -1 loss, play the max | slow to notice a switch |
| decayed | all scores x ~0.9 each round, then +/-1 | fades old evidence |
| **drop-switch** | +/-1, but **any loss resets the score to 0** | adapts at once to a switching opponent, but noise breaks it (e.g. an opponent that plays one random move in ten) |
| **random drop-switch** | reset on a loss only with probability ~0.5 | a compromise between the two above |
| other | reset on any non-win (draws too), or a small penalty for draws | |

Frequency counting is the same thing as "fixed-move predictors + naive scoring".

### Selector selection

A layer above that scores the *selection rules themselves* with the same machinery and uses
the best one. The post's examples are Centrifugal Bumblepuppy 13 and switching18.

### Defence

Put a random predictor among the candidates. When every model loses, their scores go
negative while the random one stays near 0, so the selector falls back to random play by
itself.

## Claims vs evidence

- "The author's bots rank near the top of rpscontest" is backed by the leaderboard
  (`rps_kaggle.md` section 8). The post itself has **no ablations**, so it can't tell us which layer
  matters most.
- Drop-switch's weakness to noise is argued, not measured.

## Relevance to janken

| item | where we stand |
|---|---|
| basic predictors: frequency, rotations, rfind matching on 3 histories | in `smartbot*` (18 predictors) |
| Boltzmann "decrement the losing move" | not as such. Our decayed counts only add |
| P0/P1/P2 rotations | in `smartbot*` ({beat p, beat-beat p, play p}) |
| P' (swap roles) | in the sims family (`smartbot_sims*`). Confirmed: +9.1 pts, [0003](../experiments/0003-smartbot-sims.md) |
| decayed scoring | yes (Dirichlet with decay), and greedy decay in `smartbot_bandit`, which was dropped in [0006](../experiments/0006-smartbot-bandit.md) |
| **drop-switch / random drop-switch** | **missing** |
| **selector selection** | **missing**: one bandit with one rule |
| random arm as defence | yes (`RANDOM_ARM`) |

Why the gaps matter here: matches are only 200 rounds, and the toughest opponents (the
metabots and stallers) switch behaviour mid-match. A rule that drops a losing arm at once
reacts in about 1 round instead of the ~10-20 rounds a 0.9-0.95 decay takes. A selector over
rules hedges that bet: drop-switch against switchers, decayed or Thompson against noisy
bots.

## Ideas spawned

- [ideas.md](../ideas.md) #15: drop-switch / random-drop-switch arm scoring.
- [ideas.md](../ideas.md) #16: selector-of-selectors over scoring rules.
