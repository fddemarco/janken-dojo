# Replays, level-k reasoning and parameter identification

**What they are.** Running a known bot's algorithm on the shared history, from either
seat: from the opponent's seat it predicts their move if they are that bot; from ours
it predicts what that bot would play for us, which is what an opponent modelling that
bot expects. Every rotation of a replay covers one more level of "I know that you
know" (level-k). Identification goes further: a posterior over candidate bots and
their parameters, weighted by how well each replay named the opponent's moves.

**In the kit.** `Replay` (an L2+ bot replayed, its likely move by Thompson draws or
computed: `estimate NORMAL`), `Sim` (an L1 signal from the opponent's seat), named as
arms `{bot: X, side: OPP|MY, rotations: [...]}`. Identification is research only:
`janken/experimental/identify.py`, `janken lab identify`.

## Strengths

- **Exact vs the bot replayed:** a replay specialist beats its target by 100-220
  rounds per match (`anti_iocaine` vs `iocaine_lite`, L2 atlas; 96.8% of rounds for an
  impostor, note 0014).
- **Every rotation covers the counter-counters:** level-k by rotation, no fixed level
  to exploit (`level_k_gate`, note 0032).
- **NORMAL estimates** cost 10-15x less than 256 draws with the same play (insight of
  2026-10-13).
- **Identification inside known species:** the species is named by round 150 89% of
  the time, +12.5 pts over rounds 151-250.

## Exploits

- **Only the bot replayed:** a replay of one bot moves the pool score by about one
  pool slot (~1 pt); variants of it at other parameters escape it, and an unknown
  architecture defeats identification (-12.8 pts if trusted blindly).
- **Being replayed back:** a replay is itself a deterministic bot, so the next level
  replays it (the L5 gates beat the L4s they replay 82-83% of matches).
- **Randomisation:** a Thompson bot's draws can't be replayed, only its likeliest move:
  a ceiling near 45% of rounds vs Thompson metabots.

## Cost

A whole bot's step per replay, nested replays multiply it (at most three deep).

## Ideas

- Identification with the replay's move distribution as the likelihood, not its mode
  (idea #53's condition).
