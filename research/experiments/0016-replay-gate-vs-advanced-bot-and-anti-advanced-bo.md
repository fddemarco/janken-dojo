# 0016: replay_gate vs advanced_bot and anti_advanced_bots

- **Date:** 2026-10-10
- **Status:** analyzed
- **Kind:** evaluation
- **Idea:** #30
- **Candidates:** `bots/replay_gate.yaml`
- **Baselines:** `bots/advanced_bot.yaml`, `bots/anti_advanced_bots.yaml`
- **Run:** `20261010-185932_0016-replay-gate-vs-advanced-bot-and-anti-advanced-bo`
- **Verdict:** keep

## Hypothesis

replay_gate (advanced_bot's arms + anti_advanced_bots' replay as a gated last arm, EDGE 0.06, WARMUP 20) keeps advanced_bot's zoo and anti_advanced_bots' smartbot family, so it beats both vs the pool by >= 5 pts (paired CI excluding 0); an 8-seed head-to-head sweep gave 94% of zoo matches and 87% of family matches, vs 93%/49% (advanced_bot) and 49%/91% (anti_advanced_bots). Expected costs: staller and iocaine_lite margins shrink (the gate opens falsely), and anti_advanced_bots still beats it (it replays advanced_bot, which replay_gate plays while the gate is shut).

## Command

```bash
uv run janken lab experiment bots/replay_gate.yaml bots/advanced_bot.yaml bots/anti_advanced_bots.yaml --rounds 200 --round-robins 10 --pool-size 20 --seed 3219431378 --name 0016-replay-gate-vs-advanced-bot-and-anti-advanced-bo
```

## Results

10 of 10 round robin(s), pool 20, 200 rounds/match, seed 3219431378, mode full

| bot | n | W-D-L | score vs pool [95% CI] | rounds +/- | forfeits | rating +/- sd |
|---|---|---|---|---|---|---|
| replay_gate | 200 | 178-2-20 | 89.5% [84.5%, 93.0%] | +65.4 | 0 | 1835 +/- 34 |
| advanced_bot | 200 | 155-3-42 | 78.2% [72.0%, 83.4%] | +68.0 | 0 | 1704 +/- 54 |
| anti_advanced_bots | 200 | 141-1-58 | 70.8% [64.1%, 76.6%] | +11.0 | 0 | 1721 +/- 86 |

Paired comparisons:

- `replay_gate - advanced_bot = +11.2 pts [+5.2, +17.5]` over 200 shared matches: replay_gate better
- `replay_gate - anti_advanced_bots = +18.8 pts [+11.2, +26.2]` over 200 shared matches: replay_gate better
- `advanced_bot - anti_advanced_bots = +7.5 pts [-2.2, +17.0]` over 200 shared matches: no significant difference

Weakest matchups of replay_gate: meta_smartbot 33.3%, transition_matrix 50.0%, smartbot 71.4%, sinon 71.4%, geometry 75.0%, nash 75.0%.

Weakest matchups of advanced_bot: smartbot 21.4%, geometry 25.0%, sinon 28.6%, tpi_lite 33.3%, self_sim 33.3%, smartbot_bandit 40.0%.

Weakest matchups of anti_advanced_bots: self_beater 14.3%, transition_matrix 16.7%, biased 25.0%, markov2_joint 33.3%, staller 37.5%, cycler 40.0%.

## Analysis

Idea #30 asked to route by the opponent's simplicity. A plain-Python check first (advanced_bot and anti_advanced_bots vs every bot, 4 seeds, 200 rounds) showed noisiness can't do it: the trivial zoo (copycat, reactionary, wsls, rock, cycler, self_beater, counter_reactionary, frequency) is separable (H(opp | last joint move) \<= 0.4 bits, a cheap predictor right 75-100%), but word2janken, pattern_memory, staller, markov2_joint, transition_matrix and biased look exactly like the metabots (~1.3 bits, ~40% hits), and those are the bots advanced_bot beats and the replay doesn't. What separates them is the replay's own edge (w - l) / (n + 3), undecayed: +0.10 to +0.20 vs the family, ~0 vs the zoo (8 seeds), with staller the outlier (+0.08). So the gate reads the replay's record: a new Gate selector (janken/kit/selectors.py), Thompson over every other arm while shut. Per group in this run: zoo 94.8% of matches / 69.1% of rounds (advanced_bot 95.7% / 73.6%, anti_advanced_bots 49.0% / 33.3%); family 83.7% / 39.6% (anti 94.7% / 41.3%, advanced 58.9% / 36.9%). Costs: rounds lost to false openings vs the zoo (margin +108 vs +120 per match; staller 53% of rounds vs advanced_bot's 78% in the 8-seed sweep, iocaine_lite 53% vs 80%, still won); weakest matchups meta_smartbot 33%, transition_matrix 50%, smartbot / sinon 71%. Head to head: replay_gate beats advanced_bot 9/10 (+25.0 rounds), but anti_advanced_bots beats it 10/10 (-19.8): anti replays advanced_bot, and replay_gate plays advanced_bot's arms while its own replay (of advanced_bot, not of anti) has no edge vs anti. Next: tune EDGE / GATE_DECAY / WARMUP (spaces/replay_gate.yaml), and a third expert or gate vs replays of us.

## Verdict

**keep**. replay_gate (advanced_bot's arms plus anti_advanced_bots' replay as a gated last arm; a Gate selector plays the replay while its own undecayed record clears P(win) - P(loss) > 0.06 from round 20) beats both experts vs the pool: +11.2 pts [+5.2, +17.5] vs advanced_bot and +18.8 pts [+11.2, +26.2] vs anti_advanced_bots over 200 paired matches (89.5% vs 78.2% and 70.8%; rating 1835 vs 1704 and 1721). It keeps the zoo (94.8% of matches vs advanced_bot's 95.7%; anti_advanced_bots 49.0%, i.e. chance) and most of the smartbot family (83.7% vs anti_advanced_bots' 94.7%; advanced_bot 58.9%).
