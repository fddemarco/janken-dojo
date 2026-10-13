# 0078: pretrained_light vs pretrained_context_v1

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #72
- **Candidates:** `bots/l1/pretrained_light.yaml`
- **Baselines:** `bots/l1/pretrained_context_v1.yaml`
- **Run:** `20261013-161451_0078-pretrained-light-vs-pretrained-context-v1`
- **Verdict:** keep
- **Species:** `pretrained_context_v2` (promoted over `pretrained_context_v1`)

## Hypothesis

A lighter prior (worth 1 observation per context) beats pretrained_context_v1 (worth 5) by >= 2 pts vs pools of parameter variants of the whole field, whose L3-L5 opponents the prior never trained on (pool.variants 1.0, 250 rounds; lab experiment: +11.0 pts [-0.5, +22.5])

## Command

```bash
uv run janken lab experiment bots/l1/pretrained_light.yaml bots/l1/pretrained_context_v1.yaml --rounds 250 --round-robins 32 --pool-size 20 --mode candidates --no-allow-small-pool --no-mocks --variants 1.0 --seed 1072619952 --name 0078-pretrained-light-vs-pretrained-context-v1
```

## Results

32 of 32 round robin(s), pool 20, 250 rounds/match, seed 1072619952, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| pretrained_light | 640 | 331-18-291 | 53.1% [49.3%, 57.0%] | +20.4 | 0 | 1550 +/- 97 |
| pretrained_context_v1 | 640 | 286-15-339 | 45.9% [42.0%, 49.7%] | +16.8 | 0 | 1441 +/- 109 |

Paired comparisons:

- `pretrained_light - pretrained_context_v1 = +7.3 pts [+3.3, +11.4]` over 640 shared matches: pretrained_light better

Weakest matchups of pretrained_light: leader_hunter_v2 0.0%, rps4_lite_v1 3.8%, repeat_mirror_v1 4.5%, gate_edge_v3 11.1%, naive_bayes_markov_v1 11.1%, smartbot_sims_v2 11.1%.

Weakest matchups of pretrained_context_v1: gate_leader_v1 0.0%, gate_main_first_v3 0.0%, gate_main_first_stationary_v3 0.0%, level_k_gate_v2 0.0%, anti_rps4_v1 0.0%, context_mixture_v1 7.7%.

## Analysis

Lab experiment prior-weight-whole-field (5 round robins): weight 1 59.0% of matches, 5 48.0%, 20 41.5%, context_mixture_v1 29.5%; weight 1 - 20 = +17.5 pts [+7.0, +28.0]. In L1 pools (note 0073) weight 5 was already better than CTW by +9.8; vs the whole field the lighter prior adds +7.3 more. A tuned configuration of the same mechanism: classified as pretrained_context's next version.

## Verdict

**keep**. A lighter prior generalises further: pretrained_light (the pre-trained context table worth 1 observation per context) - pretrained_context_v1 (worth 5) = +7.3 pts [+3.3, +11.4] over 640 paired matches vs pools of parameter variants of the whole field (32 round robins at the thorough budget, 250 rounds), 53.1% of matches vs 45.9%. The prior was trained on L1/L2 matches; against L3-L5 opponents it has to give way to the match's own counts sooner.

## Species

**promote**: its evaluation (run `20261013-161451_0078-pretrained-light-vs-pretrained-context-v1`) paired it with pretrained_context_v1: +7.3 pts [+3.3, +11.4]; better.

Closest species by core agreement (the dataset's histories):

| species (current version) | level | core agreement |
|---|---|---|
| `pretrained_context_v1` | L1 | 96.5% |
| `pattern_memory_v1` | L1 | 67.5% |
| `markov2_joint_v1` | L1 | 63.0% |
| `context_mixture_v1` | L1 | 62.2% |
| `rotation_outcome_v1` | L1 | 61.1% |
