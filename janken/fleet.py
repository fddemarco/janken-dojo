"""Fleets, scaffolded: a champion's bot file built on another bot.

A fleet is one file, its champion's (janken/botfile.py, the `fleet` section): it
names the base bot as its core, copies the base's guards and overlays (a core
reference carries only the core), takes the base's defaults as its own (so a
space file can tune it), and its supports are the same bot with role SUPPORT.

    draw_handshake(rng, length)    a random handshake
    champion_file(...)             the champion's YAML text
"""

import random
from collections.abc import Mapping, Sequence

import yaml

from . import botfile
from .kit.moves import PAPER, ROCK, SCISSORS

MOVE_WORDS: Mapping[int, str] = {ROCK: "ROCK", PAPER: "PAPER", SCISSORS: "SCISSORS"}
WRAP = 84  # a description line's width


class FleetError(ValueError):
    """A fleet that can't be scaffolded."""


def draw_handshake(rng: random.Random, length: int) -> tuple[int, ...]:
    """`length` moves drawn at random."""
    if length < 1:
        raise FleetError("a handshake needs at least one move")
    return tuple(rng.randrange(len(MOVE_WORDS)) for _ in range(length))


def default_description(
    base: str, champion: str, fleet: botfile.Fleet, base_description: str
) -> str:
    """What the fleet is: its bots, its handshake, and the base bot's own line."""
    summary = base_description.splitlines()[0] if base_description else base
    vigilance = (
        " Vigilant: at the first round a teammate doesn't throw, it plays on, so an"
        " impostor wins one round, not the match."
        if fleet.vigilant
        else ""
    )
    return (
        f"Fleet of {fleet.size}: {champion}, the champion, and its supports"
        f" ({', '.join(fleet.supports)}), which throw their matches to it.\n\n"
        f"Opens with the fleet's own handshake, then plays {base} ({summary})"
        f" against anyone outside the fleet, and support vs support.{vigilance}"
    )


def _wrapped(text: str) -> list[str]:
    """The description's lines, each paragraph wrapped, indented as a block."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            if line and len(line) + 1 + len(word) > WRAP:
                lines.append(f"  {line}")
                line = word
            else:
                line = f"{line} {word}" if line else word
        lines.append(f"  {line}" if line else "")
    return lines


def _flow(items: Sequence[str]) -> str:
    return "[" + ", ".join(items) + "]"


def _stages(name: str, stages: object) -> list[str]:
    """A copied blueprint section (`guards` or `overlays`), one stage a line."""
    if not stages:
        return []
    if not isinstance(stages, list):
        raise FleetError(f"the base's {name} must be a list of stages")
    if any(isinstance(s, dict) and "Team" in s for s in stages):
        raise FleetError("the base plays a Team of its own: a fleet's comes from it")
    dumped = (yaml.safe_dump(s, default_flow_style=True, width=1000) for s in stages)
    return [f"  {name}:", *(f"    - {s.strip()}" for s in dumped)]


def champion_file(
    base: str,
    found: botfile.BotFile,
    fleet: botfile.Fleet,
    description: str,
) -> str:
    """The champion's bot file: the base bot (read as `found`) as its core with
    its defaults bound through, its guards and overlays copied, and the fleet
    section.

    Raises:
        FleetError: the base's blueprint can't be copied (it plays a Team).
    """
    defaults = found.defaults
    section = found.blueprint if isinstance(found.blueprint, dict) else {}
    lines = ["description: |", *_wrapped(description)]
    if defaults:
        lines.append("defaults:")
        lines += [f"  {name}: {value!r}" for name, value in defaults.items()]
    lines += [
        "fleet:",
        f"  size: {fleet.size}",
        f"  supports: {_flow(fleet.supports)}",
        f"  handshake: {_flow([MOVE_WORDS[m] for m in fleet.handshake])}",
        f"  vigilant: {str(fleet.vigilant).lower()}",
        "blueprint:",
        "  core:",
        f"    bot: {base}",
    ]
    if defaults:
        space = ", ".join(f"{name}: ${name}" for name in defaults)
        lines.append(f"    space: {{{space}}}")
    lines += _stages("guards", section.get("guards"))
    lines += _stages("overlays", section.get("overlays"))
    return "\n".join(lines) + "\n"
