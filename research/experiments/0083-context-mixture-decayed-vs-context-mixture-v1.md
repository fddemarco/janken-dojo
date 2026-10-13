# 0083: context_mixture_decayed vs context_mixture_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #82
- **Candidates:** `bots/l1/context_mixture_decayed.yaml`
- **Baselines:** `bots/l1/context_mixture_v1.yaml`
- **Run:** `20261013-164709_0083-context-mixture-decayed-vs-context-mixture-v1`
- **Verdict:** keep
- **Species:** `context_mixture_v2` (promoted over `context_mixture_v1`)

## Hypothesis

context_mixture with DECAY 0.81 beats context_mixture_v1 (undecayed) by >= 2 pts vs random pools of the field on fresh seeds (tuning note 0082: +6.0 pts [+1.0, +10.8] validated)

## Command

```bash
uv run janken lab experiment bots/l1/context_mixture_decayed.yaml bots/l1/context_mixture_v1.yaml --rounds 200 --round-robins 24 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --seed 2282094594 --name 0083-context-mixture-decayed-vs-context-mixture-v1
```

## Results

24 of 24 round robin(s), pool 20, 200 rounds/match, seed 2282094594, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| context_mixture_decayed | 480 | 179-9-292 | 38.2% [34.0%, 42.7%] | +5.5 | 0 | 1417 +/- 70 |
| context_mixture_v1 | 480 | 142-4-334 | 30.0% [26.1%, 34.2%] | +2.9 | 0 | 1299 +/- 73 |

Paired comparisons:

- `context_mixture_decayed - context_mixture_v1 = +8.2 pts [+4.7, +11.8]` over 480 shared matches: context_mixture_decayed better

Weakest matchups of context_mixture_decayed: bayes_predators_v1 0.0%, level_k_gate_v2 0.0%, mirror_bandit_v1 0.0%, replay_hunter_gate_v2 0.0%, iocaine_lite_v1 0.0%, l5_wide_hunter 0.0%.

Weakest matchups of context_mixture_v1: bayes_predators_v1 0.0%, rps4_lite_v1 0.0%, vote_council_v1 0.0%, mirror_bandit_v1 0.0%, l5_wide_hunter 0.0%, replay_hunter_wide_v2 0.0%.

## Analysis

Forgetting lets the mixture follow the field's adaptive bots (most pool members are L2+, which change as they learn us); the validated optimum sat at the space's lower bound, so a lower decay may pay more (a follow-up tuning with the space down to 0.5).

## Verdict

**keep**. Confirmed on fresh seeds: context_mixture with KT counts decayed by 0.81 - context_mixture_v1 (undecayed) = +8.2 pts [+4.7, +11.8] over 480 paired matches vs random pools of the field (24 round robins at the thorough budget, 200 rounds), 38.2% of matches vs 30.0%: the tuning of note 0082 holds.

## Species

**promote**: its evaluation (run `20261013-164709_0083-context-mixture-decayed-vs-context-mixture-v1`) paired it with context_mixture_v1: +8.2 pts [+4.7, +11.8]; better.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `pattern_memory_v1` | L1 | 79.8% |
| `context_mixture_v1` | L1 | 78.5% |
| `markov2_joint_v1` | L1 | 72.2% |
| `rotation_outcome_v1` | L1 | 63.7% |
| `second_repeat_v1` | L1 | 60.5% |
