# 0019: Gatekeeper rules, thorough (mocked)

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #32
- **Candidates:** `bots/mock_gate_anti_first.yaml`, `bots/mock_gate_bandit.yaml`
- **Baselines:** `bots/mock_replay_gate.yaml`
- **Run:** `20261010-193841_0019-gatekeeper-rules-thorough-mocked`
- **Verdict:** keep

## Hypothesis

Follow-up of 0018 at 40 round robins (CI about +-3 pts): ANTI_FIRST and BANDIT each beat EDGE (mock_replay_gate) by >= 3 pts with a CI excluding 0 (0018: +4.0 [-0.5, +8.5] and +3.0 [-1.8, +7.8]); ANTI_FIRST vs BANDIT stays unresolved (0018: +1.0 [-3.0, +5.0]). Covers ideas #32 and #33.

## Command

```bash
uv run janken lab experiment bots/mock_gate_anti_first.yaml bots/mock_gate_bandit.yaml bots/mock_replay_gate.yaml --rounds 200 --round-robins 40 --pool-size 20 --seed 2144222104 --name 0019-gatekeeper-rules-thorough-mocked
```

## Results

40 of 40 round robin(s) · pool 20 · 200 rounds/match · seed 2144222104 · mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating ± sd |
|---|---|---|---|---|---|---|
| mock_gate_anti_first | 800 | 708-30-62 | 90.4% [88.1%, 92.2%] | +70.6 | 0 | 1847 ± 54 |
| mock_gate_bandit | 800 | 700-31-69 | 89.4% [87.1%, 91.4%] | +69.9 | 0 | 1838 ± 58 |
| mock_replay_gate | 800 | 676-40-84 | 87.0% [84.5%, 89.2%] | +56.3 | 0 | 1818 ± 52 |

Paired comparisons:

- `mock_gate_anti_first − mock_gate_bandit = +0.9 pts [-1.6, +3.4]` over 800 shared matches: no significant difference
- `mock_gate_anti_first − mock_replay_gate = +3.4 pts [+0.8, +6.0]` over 800 shared matches: mock_gate_anti_first better
- `mock_gate_bandit − mock_replay_gate = +2.4 pts [-0.1, +5.1]` over 800 shared matches: no significant difference

Weakest matchups of mock_gate_anti_first: nash 36.4%, transition_matrix 47.9%, mock_anti_advanced 50.0%, geometry 60.0%, smart_staller 71.4%, biased 80.0%.

Weakest matchups of mock_gate_bandit: nash 43.2%, mock_anti_advanced 50.0%, transition_matrix 54.2%, meta_smartbot 66.7%, geometry 70.0%, biased 72.0%.

Weakest matchups of mock_replay_gate: nash 36.4%, mock_anti_advanced 50.0%, geometry 62.0%, sims3_staller 68.2%, meta_smartbot 68.8%, tpi_lite 70.5%.

## Analysis

Per class (matches won / rounds won / margin per match): vs advanced bots ANTI_FIRST 94.1% / 44.4% / +32.5, BANDIT 91.1% / 43.5% / +30.0, EDGE 84.5% / 41.4% / +23.2: starting on the anti expert stops losing the opening rounds EDGE spends waiting for the replay's edge. Vs the zoo ANTI_FIRST 89.6% / 69.8% / +109.5, BANDIT 90.4% / 70.1% / +110.4, EDGE 91.6% / 63.1% / +89.7: the first WARMUP rounds on the anti expert cost a few zoo matches, but once the advanced arms lead, the gate never reopens on noise, so margins grow (EDGE's false openings vs the zoo, seen in 0016 and overstated by the mock in 0017, disappear). Mocks draw each other on PAPER (26 matches each, all draws). Weakest matchups of ANTI_FIRST: nash 36%, transition_matrix 48%, geometry 60%. Cost: 9,300 mocked matches in seconds. Next: tune ANTI_FIRST (EDGE, GATE_DECAY, WARMUP), then confirm a real twin (the Replay instead of the Oracle) vs replay_gate with mocks off.

## Verdict

**keep**. ANTI_FIRST beats EDGE: mock_gate_anti_first (play the anti expert by default, switch to the advanced arms once their counterfactual record leads by 0.05 from round 10) scores 90.4% vs mock_replay_gate's 87.0%, +3.4 pts [+0.8, +6.0] over 800 paired matches (40 round robins, anti expert mocked, mocks in the pools). BANDIT (Thompson between the two experts' records) is borderline: +2.4 pts [-0.1, +5.1]; ANTI_FIRST - BANDIT +0.9 [-1.6, +3.4].
