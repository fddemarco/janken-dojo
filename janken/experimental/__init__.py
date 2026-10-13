"""Experiments that need other libraries: research only, never a bot.

The kit (janken/kit/) builds every bot from scratch, with the stdlib, numpy and
numba, so that `janken bot export` can turn it into a stdlib-only submission. This
package is where an idea is tried first with whatever library makes it quick (the
`experimental` dependency group of pyproject.toml: Vowpal Wabbit so far):

    arena.py     matches between a Python player and kit bots, round by round
    features.py  what a learner sees of a match: history tokens, experts' moves
    vw.py        an online Vowpal Wabbit learner as a player
    identify.py  a particle posterior over opponents' parameters, and its study

`janken lab arena` plays a learner against a gauntlet's opponents (the field's
bots and their parameter variants) and scores it like `janken lab gauntlet run`,
so a learner and a kit bot compare on the same list.

The rules:

* Only this package and the CLI command that runs it (lazily, inside the command)
  import it or its libraries; the kit, the engine and the export never do
  (tests/test_experimental.py checks it).
* Nothing here is ever submitted. An idea that wins here is rebuilt from scratch
  as a kit stage (`/build`), and that bot is what gets evaluated and exported.
* A bot that only exists for these experiments is marked `experimental: true` in
  its file (janken/botfile.py): export refuses it and every bot naming it.
"""
