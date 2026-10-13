# Probing (black-box fingerprinting)

**What it is.** Learning what kind of bot an opponent is from how it scores against
designed inputs, not from its moves: scripted probes whose final scores each read one
property (how far back the opponent looks, how fast it forgets), and a nearest-neighbour
match of that score vector against the lab's bots. Also the in-match version: a
scripted opening whose replies a classifier reads (research/probe_study.md).

**In the kit.** The `Script` signal (a fixed move sequence) and the probe bots in
`bots/inactive/probes/`; `janken lab gauntlet fingerprint` reads tournament exports
(research/probes.md). In-match probing: research only (`janken/experimental/probe.py`).

## Strengths

- Works from final scores alone, the only data the tournament gives.
- De Bruijn scripts make each probe a sharp test: a context shorter than the order
  predicts nothing, a longer one predicts everything, so a family's margin is near 0
  or near +200, rarely between.
- Cheap: five bots, no change to the fleet; every fleet core beats every probe.

## Exploits and limits

- **A probe that ignores its opponent can't see whether the opponent reads us**
  (replays, level-k): the property that matters most above L2 (theory 02).
- **Families, not species:** bots of one family differ by less than a match's noise.
- **A bot can recognise a probe** (a script is easy to detect) and play differently
  against it, though nothing in the tournament rewards that.
- In-match probing costs rounds (about 2.8 per match for a 24-round opening) and its
  classifier's mistakes cost more than records do (notes 0074, 0075).

## Cost

Five extra tournament entries, which lose nearly every match; one lab gauntlet (the
probes vs the field, about 1600 matches) per change of the field.

## Ideas

- A probe that plays one of our fleet cores' public components with a known exact
  counter, to see which tournament bots hold that counter (whether they read us).
