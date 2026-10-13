# Opening probes: identifying an opponent's family from its replies

Study of 2026-10-13 (no lifecycle note: research code in
`janken/experimental/probe.py`). Question (the user's): can a scripted opening reveal
an opponent's family and species, and is it worth its rounds?

## Design

- **The probe:** 24 scripted moves, `R x6, (P S R) x2, P x3, S x3, (R P) x3`: a
  constant (frequency and reactive bots answer it differently), a cycle (pattern
  learners lock on), a switch (convergence speed), a period of 2.
- **The opponents:** the L1-L4 field and its parameter variants
  (`research/gauntlet/variations.txt`, retired paths dropped): 278 specs to train on
  (defaults and half the variants, seeds 1-3), 230 held-out variants to test on
  (seeds 4-5), 48 species.
- **Labels:** the species, a family (fixed, reactive, counting, L1 learner, replay
  counter, adaptive L2 bandit, L3 council, gate: the atlases' families), and a
  coarse class (simple rule, L1 learner, adaptive L2+).
- **The classifier:** naive Bayes over the opponent's reply in each probe round.
- **The control:** a fixed random opening of the same length.

## Results (held-out variants)

| opening | rounds | coarse (3) | family (8) | species (48) |
|---|---|---|---|---|
| probe | 24 | 80% | 42% | 32% |
| random | 24 | 59% | 37% | 30% |
| probe, twice | 48 | 85% | 52% | 43% |
| random | 48 | 74% | 45% | 35% |
| 10 random rounds, then the probe | 24 (probe) | 72% | 45% | 35% |

Majority class (coarse): 65%. Chance (species): about 2%.

- **The coarse class is identifiable by round 24**, at 80%, 21 pts above a random
  opening: the design matters. Delaying the probe past the opponents' openings (the
  user's suggestion) gains a little on family and species but loses 8 pts on the
  coarse class: the scripted constant at round 0 is itself what separates the simple
  rules from the learners, before the learners hold any state.
- **Family and species are far above chance but unreliable** (52% and 43% at 48
  rounds): bandits of different families look alike early, and many bots open with
  random moves. Gate type, flip-flopping and convergence time would need longer
  windows or features beyond per-round replies.
- **The cost:** the probe's own 24 rounds net -11.6% of rounds (about -2.8 rounds per
  match): it is exploited by L1 learners (-19.8%) and adaptive bandits (-18.4%), and
  exploits fixed (+11.4%) and reactive bots (+3.7%).

## Is it worth it?

On the same 230 held-out variants (seeds 4-5, 460 paired matches, 250 rounds, vs
`repeat_mirror_v1` for the whole match, net share of rounds):

| player | vs repeat_mirror | rounds per match |
|---|---|---|
| oracle: true family, probe then that family's counter | +5.0 +- 1.2 | +12.4 |
| oracle: true coarse class, probe then its counter | +4.1 +- 1.2 | +10.2 |
| probe, classify coarse, switch to its counter | +0.9 +- 1.7 | +2.2 |
| probe, classify family, switch | -1.5 +- 1.7 | -3.8 |
| probe, classify coarse, then a gate (counter vs repeat_mirror, decayed records) | +3.0 +- 1.1 | +7.5 |
| **no probe: a gate over repeat_mirror and every family's counter** | **+7.2 +- 1.3** | **+18.1** |

- **Knowing the family is worth a lot** (the oracle bounds), but a hard switch on the
  classifier's guess loses most of it to misclassification.
- **A counterfactual gate makes the probe safe** (+3.0), as it did for parameter
  identification (`janken lab identify`).
- **The probe adds nothing beyond the gate**: holding every family's natural counter
  and letting decayed records pick among them identifies the opponent implicitly, at
  no scripted cost, and gains the most (+7.2).
- **In the kit** that gate is an L3 bandit (`family_counters`, notes 0074, 0075): +12.2
  pts [+4.2, +20.2] over `repeat_mirror_v1` on whole-field variant pools, but -1.9
  [-10.9, +6.9] vs the field's L3 council `l2_council_v1`: the gain is the L3-over-L2
  effect, which the field already has. A scripted probe is not worth its rounds here;
  the families' counters are good arms for any council.
