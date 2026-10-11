"""The bot kit: every bot is a blueprint of these stages (see blueprint.py).

blueprint  the stage catalogue, as data, and its compiler (start here)
pipeline   runs a compiled blueprint for one round
guards / signals / bayes / ensemble / selectors / replay / overlays
           the compiled stages, in pipeline order
matching   the shared incremental match index behind LongestMatch / Geometry
presets    blueprint pieces shared by bot families (the metabot's 18 signals,
           the sims, the replays)
codes      the integer codes both halves share
moves      move codes and invalid-move helpers
jit        the decorators every compiled function uses
"""
