# 0089: replay_hunter_wide_v2, replay_hunter_wide_v2, replay_hunter_wide_v2 vs replay_hunter_wide_v2

- **Date:** 2026-10-13
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** -
- **Candidates:** `bots/l4/replay_hunter_wide_v2.yaml:GATE_DECAY=0.97`, `bots/l4/replay_hunter_wide_v2.yaml:GATE_DECAY=0.93`, `bots/l4/replay_hunter_wide_v2.yaml:GATE_DECAY=0.85`
- **Baselines:** `bots/l4/replay_hunter_wide_v2.yaml`
- **Run:** `20261013-183414_0089-hunter-gate-decay-vs-hard-l3-l4`
- **Verdict:** drop

## Hypothesis

The hard L3-L4s are fast adapters (sharp Thompson councils, gates); a gate that forgets (GATE_DECAY 0.85-0.97) follows them and gains at least 4 rounds per match over the undecayed gate on pools of the ten hardest, as parameter variants (note 0054 found no gain on random pools)

## Command

```bash
uv run janken lab experiment bots/l4/replay_hunter_wide_v2.yaml:GATE_DECAY=0.97 bots/l4/replay_hunter_wide_v2.yaml:GATE_DECAY=0.93 bots/l4/replay_hunter_wide_v2.yaml:GATE_DECAY=0.85 bots/l4/replay_hunter_wide_v2.yaml --rounds 250 --round-robins 30 --pool-size 10 --mode candidates --no-allow-small-pool --no-mocks --variants 1.0 --pool-list research/gauntlet/hard_l3_l4.txt --seed 3306068197 --name 0089-hunter-gate-decay-vs-hard-l3-l4
```

## Results

30 of 30 round robin(s), pool 10, 250 rounds/match, seed 3306068197, mode candidates

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_hunter_wide_v2@5e5ca3 | 300 | 205-5-90 | 69.2% [63.7%, 74.1%] | +8.5 | 0 | 1650 +/- 119 |
| replay_hunter_wide_v2@c7742b | 300 | 202-7-91 | 68.5% [63.0%, 73.5%] | +8.6 | 0 | 1617 +/- 107 |
| replay_hunter_wide_v2@32240b | 300 | 197-11-92 | 67.5% [62.0%, 72.5%] | +7.6 | 0 | 1622 +/- 138 |
| replay_hunter_wide_v2 | 300 | 196-10-94 | 67.0% [61.5%, 72.1%] | +7.2 | 0 | 1604 +/- 101 |

Paired comparisons:

- `replay_hunter_wide_v2@32240b - replay_hunter_wide_v2@c7742b = -1.0 pts [-7.8, +5.8]` over 300 shared matches: no significant difference
- `replay_hunter_wide_v2@32240b - replay_hunter_wide_v2@5e5ca3 = -1.7 pts [-8.8, +5.2]` over 300 shared matches: no significant difference
- `replay_hunter_wide_v2@32240b - replay_hunter_wide_v2 = +0.5 pts [-6.5, +7.3]` over 300 shared matches: no significant difference
- `replay_hunter_wide_v2@c7742b - replay_hunter_wide_v2@5e5ca3 = -0.7 pts [-7.8, +6.7]` over 300 shared matches: no significant difference
- `replay_hunter_wide_v2@c7742b - replay_hunter_wide_v2 = +1.5 pts [-5.3, +8.3]` over 300 shared matches: no significant difference
- `replay_hunter_wide_v2@5e5ca3 - replay_hunter_wide_v2 = +2.2 pts [-4.7, +9.2]` over 300 shared matches: no significant difference

Weakest matchups of replay_hunter_wide_v2@32240b: multiscale_council_v1 40.0%, replay_hunter_gate_v2 40.0%, sicilian_meta_v1 58.3%, counter_council_v1 60.0%, level_k_gate_v2 68.3%, l2_council_v1 70.0%.

Weakest matchups of replay_hunter_wide_v2@c7742b: replay_hunter_gate_v2 50.0%, counter_council_v1 53.3%, l2_council_v1 56.7%, sicilian_meta_v1 56.7%, multiscale_council_v1 60.0%, level_k_gate_v2 71.7%.

Weakest matchups of replay_hunter_wide_v2@5e5ca3: counter_council_v1 46.7%, multiscale_council_v1 58.3%, sicilian_meta_v1 61.7%, l2_council_v1 63.3%, double_bluff_gate_v2 66.7%, gate_main_first_backoff_v1 75.0%.

Weakest matchups of replay_hunter_wide_v2: multiscale_council_v1 40.0%, level_k_gate_v2 60.0%, replay_hunter_gate_v2 61.7%, counter_council_v1 65.0%, gate_edge_v3 66.7%, l2_council_v1 70.0%.

## Analysis

-

## Verdict

**drop**. Gate decay doesn't matter vs the ten hardest L3-L4s as parameter variants either: GATE_DECAY 0.85 +2.2 pts, the other two within 1 pt of the undecayed gate, all CIs about +-7 over 300 paired matches (30 round robins of 10-bot pools); 67-69% of matches, +7 to +9 rounds. The hard pool doesn't separate what random pools tied (note 0054).
