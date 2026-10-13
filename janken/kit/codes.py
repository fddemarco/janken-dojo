"""Integer codes shared by janken/kit/blueprint/ (Python) and the compiled stages.

A blueprint compiles into one int64 `spec` array: a header, the knob bindings,
then fixed-width records (one per guard, signal, selector and overlay) and
ensemble headers. The stages read it through the field indices below.
"""

# Sequences a signal reads or predicts.
OPP, MY, JOINT = 0, 1, 2
# OnInvalid: whose history is checked.
BOTH = 2

# Rotations: the move played relative to a signal's symbol (+0, +1, +2 mod 3).
COPY, BEAT, BEAT_BEAT = 0, 1, 2

# Move sentinels (real moves are 0..2, INVALID 3, CRASH -1; see moves.py).
NO_MOVE = -1  # a signal has no prediction
RANDOM_MOVE = -2  # a parameter meaning "a uniformly random move"
PASS = -9  # a guard lets the round through

# Guards.
G_OPENING, G_NOISE, G_ON_INVALID = 0, 1, 2
LAST, ANY = 0, 1  # OnInvalid scope
CRASH_ACTION, RANDOM_ACTION = 0, 1  # OnInvalid action

# Signals.
(
    S_LAST,
    S_FREQ,
    S_NGRAM,
    S_BACKOFF,
    S_MATCH,
    S_RELATIVE,
    S_REACT,
    S_CONSTANT,
    S_CYCLE,
    S_BIASED,
    S_WIN_STAY,
    S_GEOMETRY,
    S_REPLAY,
    S_BAYES,
    S_MATCH2,
    S_ORACLE,
    S_RAREST,
    S_PERIOD,
    S_SCORE_STATE,
    S_CTW,
) = range(20)
CTW_NODE = 4  # a CTW context's floats: three KT counts, then its log mixing ratio
CTW_RATIO_CAP = 50.0  # the log mixing ratio is kept within +-CTW_RATIO_CAP

# Oracles (research only, janken/mocks.py): none, a pure Oracle bot, an Oracle arm;
# the level the referee reveals for an Oracle opponent (janken/kit/levels.py).
ORACLE_NONE, ORACLE_PURE, ORACLE_ARM = 0, 1, 2
LEVEL_ORACLE = 0

# Arm scorers.
SC_NONE, SC_DIRICHLET, SC_DECAYED, SC_DROP_SWITCH = 0, 1, 2, 3
# The random arm: absent, scored like any arm, or pinned at a score of 0.
RA_NONE, RA_SCORED, RA_PINNED = 0, 1, 2

# Selectors.
SEL_FIRST, SEL_GREEDY, SEL_THOMPSON, SEL_VOTE, SEL_KEEPER = 0, 1, 2, 3, 4
TIES_FIRST, TIES_RANDOM = 0, 1
# Gatekeeper rules: the gated arm while it clears an edge; the gated arm unless the
# main expert beats it by an edge; a two-armed bandit over the two experts; ANTI_FIRST
# that keeps the main expert until the gated arm leads it by the edge; the main expert
# first, the gated arm only while it leads by the edge (with hysteresis); the main
# expert first, then whichever of it and K gated experts leads the current one by the edge;
# LEADER where only the last gated expert can take over from another gated expert.
EDGE, ANTI_FIRST, BANDIT, ANTI_FIRST_HOLD, MAIN_FIRST, LEADER, LEADER_PRIORITY = range(
    7
)

# How a replay names a Thompson bandit's likely move: by Monte Carlo draws, or
# computed from a normal approximation of each arm's draw (janken/kit/replay.py).
EST_DRAWS, EST_NORMAL = 0, 1

# Overlays.
O_STALL, O_TEAM, O_EMIT_INVALID = 0, 1, 2
CHAMPION, SUPPORT, IMPOSTOR = 0, 1, 2  # Team roles

# Record fields (every record is REC wide).
REC = 16
R_KIND = 0
R_F = 1  # offset of the stage's float state in f
R_I = 2  # offset of its int state in i
R_K = 3  # slot of its first knob
R_A, R_B, R_C, R_D = 4, 5, 6, 7  # literal integer parameters
R_SWAP = 8  # signals: 1 when evaluated from the opponent's side (a sim)
R_ARM = 9  # signals: index of the signal's first arm
R_NROT = 10  # signals: how many rotations
R_ROT = 11  # signals: the rotations, R_ROT .. R_ROT + 2
R_SUB = 14  # replay signals: offset of the replayed ensemble's header
R_IDX = 15  # history matchers: the number of their stream's match index

# Ensemble header fields (ENS wide).
ENS = 16
E_NSIG = 0
E_SIG_AT = 1  # offset of its first signal record
E_NARMS = 2  # arms, not counting the random arm
E_RANDOM = 3  # RA_* mode
E_SCORER = 4
E_SCORER_K = 5  # knob slot of the scorer's first knob
E_SCORE_F = 6  # offset of the arm scores in f (3 per arm, random arm last)
E_PEND_I = 7  # offset in i: [stamp, pending move per arm, random arm last]
E_SYM_I = 8  # offset in i of this round's symbol per signal (scratch)

# Spec header fields (HEADER wide).
HEADER = 16
H_NGUARD = 0
H_GUARD_AT = 1
H_NOVER = 2
H_OVER_AT = 3
H_CORE = 4  # offset of the core ensemble's header
H_NSEL = 5  # selector options (more than one: chosen by a knob)
H_SEL_AT = 6
H_SEL_K = 7  # knob slot choosing among the options, or -1
H_CURSOR_I = 8  # offset in i of the round cursor
H_KNOB_F = 9  # offset in f of the resolved knobs
H_NKNOB = 10
H_BIND_AT = 11  # per knob: index into prm, or -1 for a literal
H_ROUNDS_I = 12  # offset in i of [stride, base] of the per-round region
H_VIEW_I = 13  # offset in i of [valid rounds, rounds scanned, opp / my invalid moves]
H_NIDX = 14  # match indexes (one per history stream a matcher reads)
H_IDX_AT = 15  # offset of the first match index record

# The per-match workspace: i is [fixed state][per-round slots], each slot `stride`
# (= rounds + 1) wide from `base`. Slots 0 and 1 hold the valid-only history.
VIEW_MY_SLOT, VIEW_OPP_SLOT = 0, 1
VIEW_CELLS = 4

# History streams a match index covers (janken/kit/matching.py).
STREAM_OPP, STREAM_MY, STREAM_JOINT = 0, 1, 2

# Match index records (IDX wide).
IDX = 4
X_STREAM = 0
X_FIXED_I = 1  # offset in i of [head per symbol (9), filled]
X_SLOT = 2  # first of its per-round slots: mval, stamp, prev, best
X_FIXED = 10
X_SLOTS = 4
