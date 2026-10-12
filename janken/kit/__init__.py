"""The bot kit: every bot is a blueprint of these stages (see blueprint/).

blueprint  the stage catalogue, as data, and its compiler (start here): guards,
           a core predictor tree (an L1's Heuristic, or an aggregator, a Bandit,
           Gate or NaiveBayes, over other bots) and overlays
pipeline   runs a compiled blueprint for one round
guards / signals / bayes / ensemble / selectors / replay / overlays
           the compiled stages, in pipeline order
matching   the shared incremental match index behind LongestMatch / Geometry
declare    the YAML grammar of a bot file's blueprint
levels     a bot's level: L1 heuristics, L2 aggregators over L1s, ...
codes      the integer codes both halves share
moves      move codes and invalid-move helpers
jit        the decorators every compiled function uses
"""
