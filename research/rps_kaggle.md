# Kaggle "Rock, Paper, Scissors" (2020-21): notes for our bots

Research notes on the Kaggle RPS simulation competition (Nov 2, 2020 - Feb 22, 2021;
~1,660 teams, ~48k submissions), with an eye to improving the bots in `bots/`.

Sources are listed at the end. Where a Kaggle page could not be read directly
(Kaggle renders writeups with JavaScript), the claim is marked *(from search summary)*.

______________________________________________________________________

## 1. The competition in one paragraph

- Episodes were **1000 rounds**, and a match counted as a **win only when the margin was > 20**.
  Anything closer was a draw.
- The leaderboard used a Gaussian skill rating (mu/sigma) updated from episodes against
  similarly rated bots. It was **very noisy**: the winner says they could never build a
  local evaluation that matched it, and they resubmitted the same agent when it had an
  unlucky start.
- Uniform random play (Nash) has expected score 0 against anything. So it draws almost
  every match and **can never climb**. Rank came entirely from *exploiting* non-random bots
  while not getting exploited yourself.
- The field was full of public notebooks (Markov, decision trees, MAB, ports of
  rpscontest.com bots). A large share of the leaderboard ran known, beatable code. That
  made "beat the public agents" a winning strategy in itself.

## 2. The 1st-place solution ("Where is my bag", by Bow)

**TL;DR:** a multi-armed bandit (MAB) over a list of agents. The agents are rpscontest
bots, a decision-tree bot, and `rfind`, each run as *regular*, *1-step-ahead* and
*2-steps-ahead* variants. The bandit picks an agent by **sampling from a Dirichlet**
distribution.

### Agent pool of the top submission

| Agent | Regular | 1-step | 2-step |
|---|:-:|:-:|:-:|
| DTC (decision-tree classifier) | | o | |
| rfind (history matcher) | o | o | o |
| rpscontest #02, #03, #04, #05, #27, #33, #36 | o | o | o |
| rpscontest #01, #06, #10, #11, #24, #49 | | o | o |

So the pool is about 40 arms. Note that several base agents appear **only** as their
beater variants. Bow thought the regular versions were useless or harmful against the
field, while the beaters were useful.

### Definitions

- **1-step-ahead ("beater")** of agent A: simulate A from *our* point of view, which
  predicts how a copy of A playing against us would move. Then play the move that beats
  A's move. This kills anyone running A.
- **2-steps-ahead**: the beater of the beater. This kills anyone running "beat A".
- This gives a cycle: 1-step beats regular, 2-step beats 1-step, regular beats 2-step.

### The two core ideas (Bow's words)

1. **"To achieve a higher rank, the agent should beat as many public agents as possible."**
   This motivated the beater arms. Adding a 1-step DTC alone took Bow from mid-table
   to the **top 5%**.
1. **"A good agent cannot easily beat itself."** This motivated the 2-step arms. If a
   copy of you (or a beater of you) wins against you, the bandit has nothing to switch to.

### Lessons from the journey

- **Phase I:** hand-written "clever" ideas (reactionary, counter-reactionary, Markov
  variants) did poorly.
- **Phase II:** tuning MAB decay and reward barely moved the score. *Which arms are in the
  pool* mattered far more than bandit hyperparameters.
- **Phase III:** adding old rpscontest.com bots gave a clear jump. These bots were
  battle-tested over years.
- **Phase IV, the key bug:** the transformed agents first performed badly because
  **"the input action for each agent was wrong."** Each sub-agent must be fed a history
  that is consistent with its own point of view. When you simulate the opponent running
  agent A, A's "my moves" are the opponent's moves and A's "opponent moves" are *our*
  moves. When you simulate the regular agent, it needs our actual history, not the
  moves the bandit picked for other arms. Get this wrong and every transformed arm is
  noise.
- **Phase V:** Bow **deleted all the hand-written if-else rules for picking agents** and
  kept only Thompson sampling with a Beta distribution. *"Surprisingly, it dominated over
  all of my previous agents."* Switching from Beta (win vs loss) to a **Dirichlet over
  (win, tie, loss)** improved it further. That became the final top submission.
- **Phase VI:** stacking two MABs (one picks the agent, one picks the "strategy") did well
  until the public **Geometry** agent appeared, which the stacked design couldn't handle.
  The simpler Phase V bots held up better at the end.

### Local evaluation

Bow ran 20 games against each benchmark, about 3,000 games a day on an 8+ CPU machine.
The benchmarks were DTC, a random forest bot, rpscontest #4, Geometry, a previous strong
submission, and replays of two episodes Bow had lost. Bow still found local results
unreliable as a predictor of the leaderboard.

## 3. Agent catalogue (ihelon's "Agents Comparison" + friends)

ihelon's notebook collects the popular public agents and plays them round-robin
(1000 steps). Short descriptions, and **what beats each one**:

| Agent | How it works | Beaten by |
|---|---|---|
| rock / paper / scissors | constant | any frequency counter |
| hit_the_last_own_action | cycles R-->P-->S | n-gram on own or opp history |
| copy_opponent | plays opp's last move | "beat my own last move" |
| reactionary | beats opp's last move (keeps it after a win) | "beat what beats my last move" |
| counter_reactionary | after a win, shifts; else beats opp's last | order-1/2 Markov on joint history |
| statistical | beats opp's most frequent move | anti-frequency (beat the beater of my mode) |
| nash_equilibrium | uniform random | nothing (draws everything) |
| markov_agent ("(Not so) Markov") | order-2 joint-history table, argmax --> sampled after step 500 --> **inverted after step 900** | 1-step beater on joint history |
| memory_patterns | stores length-3 joint patterns, re-evaluates every ~100 steps | pattern matcher with faster adaptation |
| multi_armed_bandit (ilialar) | Beta-Thompson over mirror+/-shift, self+/-shift, popular-beater, transition matrix/tensor (deterministic and sampled, with decay), pattern matching | Geometry, rpscontest metas |
| opponent_transition_matrix | order-1 opp-only transition, sampled | order-1 beater |
| decision_tree_classifier (DTC) | sklearn tree on features: step mod 2/3/5, last k=5 steps of both players' moves, global action frequencies. Retrained every move after ~30 random warm-up moves | **its 1-step beater** (Bow's first big win) |
| statistical_prediction | predicts the opponent's **rotation** (opp move minus their last move), three chained weighted guesses, randomness ramps up to 50% by the end | patterns in rotations |
| high_performance_rps_dojo | hashes depth 1-3 contexts of (opp, me, score) histories; random "jitter" moves | - |
| **geometry** (superant) | see section 4.4: longest history match + learned complex offset, then **sample** from the distribution | strongest public agent late in the competition |

Pattern worth noticing: every simple deterministic agent loses to "predict it, then
beat it". The ones that stayed strong (Geometry, the rpscontest metas) either **randomize
in proportion to their confidence** or **pick among their own counter-strategies by
measured performance**.

## 4. Key techniques in implementable detail

### 4.1 Rotation (relative-move) encoding

Instead of predicting the opponent's absolute move, predict
`d = (opp_next - anchor) mod 3` where the anchor is their last move, our last move, or
the result of the last round. This makes one table cover "always beat my last move",
"always repeat", "cycle" and so on, regardless of which concrete move started it.
Statistical Prediction, the rpscontest metas and our `rel_*` predictors all do this.
**Rotations conditioned on the last outcome** (win/tie/loss --> rotation) capture
"win-stay, lose-shift" humans and bots very cheaply.

### 4.2 History matching ("DNA") and multi-window n-grams

The rpscontest favourites (`rfind`, dllu's *Testing Please Ignore*, *DNA Polymerase*,
*Centrifugal Bumblepuppy*) all start the same way:

- Keep three history strings: **joint** (`my+opp` pairs), **opp-only**, **my-only**.

- For each one, find the **longest suffix (up to ~10-20) that occurred before** and read
  off what came next. That is the "DNA" prediction: one candidate for the opponent's
  move and one for ours.

- Testing Please Ignore (81.7% win rate on rpscontest) adds a **second-order match**: it
  looks up the pattern that followed the matched pattern. Then it combines everything
  **multiplicatively, like naive Bayes**:

  - `probs[hand] *= P(opp plays hand | DNA prediction)`, using count tables keyed by
    the predicted move;
  - times `P(outcome class | hand vs predicted)`, learned per predictor, which captures
    whether this predictor is usually right, usually beaten, or usually ceded;
  - times transition counts of "which of the 6 candidate strategies (pred, beat(pred),
    cede(pred) for opp-pred and my-pred) the opponent has been consistent with".

  It then plays the **expected-value maximiser** `argmax_h sum_p score(h,p)*probs[p]`
  rather than "beat the argmax".

- The 10th-place Kaggle solution, "Layered Multi-window Counting", used an n-gram tree
  over several window lengths, with each base strategy paired with **two counter
  strategies**, and the author deliberately kept it simple *(from search summary)*.

### 4.3 Sicilian reasoning / meta-strategies (Iocaine Powder --> rpscontest #4)

From Iocaine Powder (1999 RoShamBo winner). For each predictor P that outputs a predicted
opponent move `p`, consider **6 strategies**:

- P0 = beat p, P1 = beat beat p, P2 = beat beat beat p (= play p). These three cover
  "the opponent is predictable", "the opponent predicts that I predict them", and the
  next level up.
- The same three applied to **P run on my own history**, i.e. what a predictor would
  expect *me* to play. These beat opponents who model me.

rpscontest **#4** (one of Bow's base agents, and one of his benchmarks) is a compact
example of this:

- 1 random arm plus Markov orders 0-6 on the joint history. Each order predicts both
  opp's and my next move, picked with an *expected-win* rule (`s[beat(beat(i))] - s[beat(i)]`), and each prediction expands into 3 rotations. That makes 43 arms.
- Each arm keeps a **decayed score** `score = 0.85*score + weight*result`. Its `weight`
  slowly grows or shrinks (alpha=0.01) with its long-run accuracy.
- The bot plays the arm with the highest score (a greedy pick, ties broken at random).
  The **random arm's score is pinned to 0**. This is a neat safety net: when every model
  is net losing, random wins the argmax automatically.

### 4.4 Geometry: continuous prediction, and **sample, don't argmax**

superant's Geometry agent maps each move to a cube root of unity, `z = e^{2*pi*i*k/3}`. A
probability vector `p` becomes `z = p*basis`, and back via `p_k = (2*Re(z*conj(basis_k))+1)/3`
followed by clipping and renormalising.

- Feature `x`: the opponent's move that followed the **longest past match of the joint
  history** (max length 20), normalised.
- Learned offset `a = (1-alpha)*a + alpha*(y*conj(x_prev))`, with alpha = 0.01, where `y` is the move
  that would have beaten the opponent's last move. Multiplying by a complex unit means
  rotating the prediction, so `a` learns "the opponent tends to play rotation r relative
  to what history-match suggests". The magnitude |a| shrinks automatically when the
  rotation is inconsistent.
- Prediction `y_hat = x*a`. Convert it to probabilities and **sample the move from them**.

Author's own takeaway: the important part is `sample_from_z`. When the bot is confident
(|a| near 1), it plays almost deterministically and farms weak bots. When it has no
pattern, |a|-->0, and it plays almost uniformly, so **there is nothing to exploit**. This
one-predictor agent sat in silver on the leaderboard and was the agent the 1st-place
stacked MAB couldn't beat. The 66th/67th-place writeup built on it, adding fixed "twists"
on top of an rpscontest bot and a **"ratchet" that rotates the output after losses**
*(from search summary)*.

### 4.5 Bandit choices

- **Beta(wins+1, losses+1)** Thompson sampling: the ilialar baseline, and Bow's Phase V.
- **Dirichlet(wins+1, ties+1, losses+1)**: sample `(pw, pt, pl)` and pick the arm with the
  largest `pw - pl`. This was Bow's final choice. A tie is information too: it means
  "predicted one off".
- **Decayed scores with greedy selection** (rpscontest #4, decay 0.85) adapt faster than
  counts but are deterministic, so they can be exploited.
- Arms must be scored **counterfactually** against what the opponent actually played,
  every round, not only when chosen. Otherwise unchosen arms never learn.
- **Decay matters less than the pool** (Bow, Phase II). But decay controls how fast you
  notice that an opponent has switched strategy, which matters more the shorter the match.

### 4.6 Defensive randomness

Good bots fall back towards uniform play when:

- no model beats chance (a random arm, or a random-arm floor at score 0);
- the bot is being out-predicted (drawdown triggers);
- the bot is far enough ahead that variance is the only risk (lead lock). This matters
  most under a "win the match" scoring rule;
- the match is late and the opponent might switch. "(Not so) Markov" inverts its play
  after step 900, and Statistical Prediction ramps towards 50% randomness.

## 5. How *our* tournament differs from Kaggle

| | Kaggle | janken (this repo) |
|---|---|---|
| Rounds per match | 1000 | **200** by default (`--rounds`, `$JANKEN_ROUNDS`) |
| Match result | win only if margin > 20, else draw | **any margin wins** (`MatchResult.winner` in `janken/match.py`) |
| Rating | TrueSkill-like mu/sigma over many episodes | one Glicko-2 period over match results (1 / 0.5 / 0) |
| Opponents | thousands of public and private bots | a **small known pool** (`bots/`) |
| Illegal move | - | 3 invalid moves forfeit; exceptions forfeit |

Consequences:

- **Warm-up cost is 5x larger relative to the match.** DTC's ~30 random warm-up moves
  are 15% of a 200-round match. Long n-grams and order-6 Markov rarely see their context
  twice. Prefer short contexts, rotations, and fast-decaying tables early. Longest-match
  lookups degrade gracefully because they use whatever length exists.
- **Any margin wins, so match-level variance is the enemy and the friend.** Against an
  equal opponent, the result of a 200-round match is close to a coin flip. A small
  per-round edge (+0.05 per round, i.e. +10 over the match against an SD of about 11.5)
  already gives a big match-win advantage. Locking in a lead by going random is worth
  more here than on Kaggle, where a draw band of +/-20 already absorbed noise.
  `smart_staller.py` already exploits this.
- **Ratings come only from who won the match.** Crushing a weak bot by 100 is worth the
  same as winning by 1. Spend modelling effort on the close matchups.
- **The pool is small and visible.** Bow's rule 1 ("beat the public agents") becomes
  literal: we can build 1-step beaters of *specific bots in `bots/`*. Rule 2 ("cannot
  beat itself") matters a lot, because the metabots share code and meet near-copies of
  themselves.
- **`run-fast` needs numba ports.** Any new bot or changed bot file must get a port in
  `janken/fast/` and an entry in `PORTS` (`janken/fast/engine.py`), and must pass
  `tests/test_fast_equivalence.py`. Keep new techniques port-friendly: fixed-size arrays,
  no dicts of tuples, random calls only through `fast/rng.py`.

## 6. Where our bots stand vs the Kaggle state of the art

`smartbot.py`, `meta_smartbot.py` and `smart_staller.py` already implement the Phase V
recipe. Each has 18 predictors (frequency, opp/joint/my n-grams, longest match on 3
histories, three rotation models) x {beat p, beat-beat p, play p}, plus a random arm.
Arms are scored counterfactually with a decayed Dirichlet(win, tie, loss), and the bandit
uses Thompson sampling on `pw - pl`. The staller adds drawdown and lead-lock stalling.

What they **don't** have yet, roughly in order of expected value:

1. **Calibrated sampling instead of argmax predictions.** Every predictor returns
   `argmax` and every arm plays a deterministic move. The only randomness comes from the
   Thompson draw and the random arm. A Geometry-style arm, which samples from a
   confidence-scaled distribution, is both an exploiter and hard to exploit.
1. **A naive-Bayes / expected-value combiner** like Testing Please Ignore, as one extra
   *arm*. It multiplies evidence from all predictors into one distribution and plays
   `argmax_h E[score]`. This is the strongest single-bot design from rpscontest, and it
   is different in kind from a bandit choosing one predictor.
1. **Second-order history matching**, i.e. the pattern after the matched pattern. Its
   benefit is easy to measure.
1. **Outcome-conditioned rotations.** `rel_opp_out` conditions on the outcome of the last
   round. Adding the same for our rotation (`rel_my` given the outcome), and order-2
   outcome contexts, is cheap.
1. **Bot-specific beaters.** For each bot in `bots/` (word2janken, staller, the metabots),
   run a faithful simulation of it from the opponent's side and add its 1-step and 2-step
   arms. This is Bow's single biggest jump, and our opponent pool is known.
1. **Bandit decay tuned for 200 rounds**, plus a check of the "tie" handling. Decay 0.95
   ~ 20-round memory and 0.6 ~ 2.5 rounds; both values exist in the repo. Try a
   scored-greedy variant with a random arm pinned at 0 (rpscontest #4) as a comparison.
1. **The input-action check (Bow's Phase IV bug).** Make sure the "my"-history predictors
   see moves we actually played. Ours use `my_moves` from the engine, which is correct.
   Any simulated opponent-side agent added later must get swapped histories.

## 7. Actionable experiment checklist

- [ ] Add a `geometry` predictor to the metabot: longest joint match --> feature, learned
  complex offset with alpha ~ 0.02-0.05 (200 rounds instead of 1000), arm plays a
  **sampled** move. Also try it standalone as `bots/geometry.py`.
- [ ] Add a "TPI-lite" naive-Bayes combiner arm over the existing predictors' outputs,
  playing expected-value-max.
- [ ] Add second-order DNA matching to the `match` predictors.
- [ ] Write `bots/<x>_beater.py` experiments that simulate each existing bot and play its
  1-step / 2-step counters. Keep them only if they don't lose to the field.
- [ ] Grid the bandit decay (0.7-0.97) and table decay at `--rounds 200`. Report match
  win rate, not round differential.
- [ ] Self-play test: every candidate vs a copy of itself and vs its own 1-step beater.
  A good bot should be ~50% in both (rule 2).
- [ ] Evaluate with many seeds, because one run is noise. For example
  `python -m janken run-fast bots/ --rounds 200 --matches 50 --seed S` for several S,
  or `--games N` for large balanced schedules. Compare ratings across seeds before
  believing an improvement. Bow's main complaint was a noisy leaderboard; we can
  afford thousands of matches.
- [ ] Remember the port: new logic in `bots/` needs a matching `janken/fast/` port and
  equivalence tests before `run-fast` will play it.

## 8. References

- 1st place writeup (Kaggle; JS-rendered, read through the GitHub mirror):
  https://www.kaggle.com/competitions/rock-paper-scissors/writeups/where-is-my-bag-1st-place-solution-where-is-my-bag
- 1st place repo (full writeup + agent table): https://github.com/thisisbowen/RPS-Kaggle-1st-Place-Solution
- ihelon, *Rock Paper Scissors - Agents Comparison* (source read through the Kaggle kernels API):
  https://www.kaggle.com/code/ihelon/rock-paper-scissors-agents-comparison
- superant, *RPS Geometry* (source read through the API): https://www.kaggle.com/code/superant/rps-geometry-silver-rank-by-minimal-logic
- ilialar, *Multi-armed bandit vs deterministic agents*: https://www.kaggle.com/code/ilialar/multi-armed-bandit-vs-deterministic-agents
- purplepuppy, *Running rpscontest bots* (includes the full Testing Please Ignore source):
  https://www.kaggle.com/code/purplepuppy/running-rpscontest-bots
- alexandersamarin, *Decision Tree Classifier*: https://www.kaggle.com/alexandersamarin/decision-tree-classifier
- rpscontest.com leaderboard (archived; the top bots are IO2_fightinguuu, dllu1, RPS_Meta_Fix,
  meta-...-markov, Testing Please Ignore): https://web.archive.org/web/20200521083624/http://www.rpscontest.com/leaderboard
- rpscontest #4 source (archived): https://web.archive.org/web/20200812073700/http://www.rpscontest.com/entry/5728994095792128
- 10th place, *Layered Multi-window Counting* (JS-rendered, not read directly):
  https://kaggle.com/competitions/rock-paper-scissors/discussion/221512
- 67th place, *The Voyage to 67th Place* (JS-rendered, not read directly):
  https://www.kaggle.com/competitions/rock-paper-scissors/discussion/222411
- 37th place repo (0Zeta): https://github.com/0Zeta/RockPaperScissors
