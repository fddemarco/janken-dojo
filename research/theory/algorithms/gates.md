# Gates

**What they are.** A main bandit plays by default; gated experts (usually replays of
specific bots) take over when their own record leads by an edge after a warm-up. A
two-level decision: which expert, then which arm inside it.

**In the kit.** `Gate` (`janken/kit/blueprint/composites.py`), lowered with a
`Gatekeeper` selector; rules `EDGE`, `ANTI_FIRST`, `ANTI_FIRST_HOLD`, `MAIN_FIRST`,
`LEADER`, `LEADER_PRIORITY`, `BANDIT`; knobs `edge`, `decay`, `warmup`.

## Strengths

- **Specialists without dilution:** an expert plays only where its record says it
  wins, so a replay of one opponent costs little elsewhere. The best L4s
  (`replay_hunter_wide_v2`) are gates over 20+ replays.
- **The defaults are at the optimum:** no tuned EDGE, GATE_DECAY or WARMUP beats
  `replay_hunter_wide_v2`'s (note 0054).

## Exploits

- **Being replayed one level up:** the L5 gates replaying the L4 gates win 82-83% of
  their matches vs them (runs of 2026-10-13), and `double_bluff_gate` exploits a
  LEADER gate's slow handover by flipping its counter on and off.
- **A slow handover:** an undecayed LEADER record needs many rounds to switch; a
  decayed gate (0.85) fixes `double_bluff_gate` (33.6% --> 36.7% of rounds) but
  costs as much elsewhere (notes 0058, 0059).
- **False leads among near-copies,** as for bandits (note 0048).

## Cost

The main bandit plus every expert's step, every round: the field's L4/L5 gates are
the slowest bots.

## Ideas

- A per-expert decay (a fast one for experts that model flip-flopping opponents),
  idea #59.
- Change-point detection as the handover signal (`statistical-methods.md`).
