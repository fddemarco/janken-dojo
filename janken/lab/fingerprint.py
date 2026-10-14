"""Fingerprints: what scripted probes reveal about bots we only see scores of.

A probe plays a fixed script, whatever its opponent does (the `Script` signal;
bots/inactive/probes/). Against a script an opponent's final score depends only on
what kind of learner it is: how far back it looks, how fast it forgets. So a bot's
margins over the probes are its fingerprint, readable from final scores alone,
which is all a tournament's match export gives (research/probes.md).

    read_export   a tournament export (CSV): every match's two bots and rounds won
    aliases       the names the probes are submitted under (NAME=STEM)
    competition   each tournament bot's mean margin over every probe it met
    lab           each lab bot's margin over every probe, from a gauntlet log in
                  which the probes were the candidates
    nearest       the lab bots whose fingerprints are closest to one bot's

The functions are pure but for `read_export`; janken/cli/gauntlet.py wires them to
`janken lab gauntlet fingerprint`.
"""

import csv
import dataclasses
import math
import re
from collections.abc import Mapping, Sequence

from . import gauntlet

PAUSED = "⏸ "  # the export marks a paused bot's name with a pause sign
SCORE_SEPARATORS = "–-"  # an export's score: wins of A, an en dash, wins of B

# probe --> the bot's mean margin over it: (rounds won - lost) / rounds played, so
# fingerprints of matches of any length compare.
Fingerprint = dict[str, float]


@dataclasses.dataclass(frozen=True)
class Match:
    """One tournament match: rounds won by each of its two bots, and drawn, and
    when it was played (the export's text, which sorts in time order)."""

    a: str
    b: str
    wins_a: int
    wins_b: int
    draws: int
    when: str = ""

    @property
    def rounds(self) -> int:
        return self.wins_a + self.wins_b + self.draws


def read_export(path: str) -> list[Match]:
    """The matches of a tournament export (columns `Bot A`, `Bot B`, `Score`,
    `Draws`)."""
    with open(path, encoding="utf-8-sig") as source:
        return [_match(row) for row in csv.DictReader(source)]


def _match(row: Mapping[str, str]) -> Match:
    wins_a, wins_b = re.split(f"[{SCORE_SEPARATORS}]", row["Score"].strip(), maxsplit=1)
    return Match(
        _name(row["Bot A"]),
        _name(row["Bot B"]),
        int(wins_a),
        int(wins_b),
        int(row["Draws"]),
        row.get("When", "").strip(),
    )


def _name(text: str) -> str:
    return text.strip().removeprefix(PAUSED).strip()


def key(text: str) -> str:
    """A name reduced to its lowercase letters and digits, for matching."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


Aliases = dict[str, str]  # a tournament name's key --> the probe stem it stands for


def aliases(entries: Sequence[str], probes: Sequence[str]) -> Aliases:
    """`NAME=STEM` entries as aliases: the names the probes are submitted under,
    so other players can't tell them from their names.

    Raises:
        ValueError: an entry isn't NAME=STEM, or its stem isn't one of the probes.
    """
    stems = {stem(p) for p in probes}
    found: Aliases = {}
    for entry in entries:
        name, sep, target = entry.partition("=")
        if not sep or not key(name) or target.strip() not in stems:
            raise ValueError(f"alias {entry!r}: expected NAME=STEM, STEM a probe")
        found[key(name)] = target.strip()
    return found


def probe_of(name: str, probes: Sequence[str], known: Aliases) -> str:
    """The probe (a lab path) a tournament bot's name stands for: the one its
    alias names (the whole name, compared by key), else the one whose stem's key
    its key contains (`Probe_Cycle3` --> .../probe_cycle3.yaml); empty when it
    names none."""
    aliased = known.get(key(name), "")
    found = [
        p
        for p in probes
        if (stem(p) == aliased if aliased else key(stem(p)) in key(name))
    ]
    return max(found, key=lambda p: len(key(stem(p))), default="")


def stem(path: str) -> str:
    """A bot spec's stem: its file name without folder, extension or overrides."""
    name = path.split(gauntlet.OVERRIDES)[0].rsplit("/", 1)[-1]
    return name.removesuffix(".yaml")


def competition(
    matches: Sequence[Match], probes: Sequence[str], known: Aliases
) -> dict[str, Fingerprint]:
    """Each tournament bot's mean margin over every probe it met (matches that
    ended before a round was played are skipped); the probes are left out."""
    margins: dict[str, dict[str, list[float]]] = {}
    for m in (m for m in matches if m.rounds > 0):
        for bot, rival, mine, theirs in (
            (m.a, m.b, m.wins_a, m.wins_b),
            (m.b, m.a, m.wins_b, m.wins_a),
        ):
            probe = probe_of(rival, probes, known)
            if probe and not probe_of(bot, probes, known):
                by_probe = margins.setdefault(bot, {})
                by_probe.setdefault(probe, []).append((mine - theirs) / m.rounds)
    return {
        bot: {p: sum(v) / len(v) for p, v in by_probe.items()}
        for bot, by_probe in margins.items()
    }


def lab(done: gauntlet.Log, probes: Sequence[str]) -> dict[str, Fingerprint]:
    """Each lab bot's mean margin over every probe, from a gauntlet log whose
    candidates were the probes (a probe's share lost is its opponent's won)."""
    margins: dict[str, dict[str, list[float]]] = {}
    for job, played in done.items():
        if job.a in probes:
            by_probe = margins.setdefault(job.b, {})
            by_probe.setdefault(job.a, []).append(played.lost - played.won)
    return {
        bot: {p: sum(v) / len(v) for p, v in by_probe.items()}
        for bot, by_probe in margins.items()
    }


def distance(a: Fingerprint, b: Fingerprint) -> float:
    """The root mean square difference over the probes both met (inf: none)."""
    shared = [p for p in a if p in b]
    if not shared:
        return math.inf
    return math.sqrt(sum((a[p] - b[p]) ** 2 for p in shared) / len(shared))


def nearest(
    target: Fingerprint, library: Mapping[str, Fingerprint], k: int
) -> list[tuple[str, float]]:
    """The k lab bots closest to `target`, with their distances, closest first."""
    ranked = sorted((distance(target, fp), bot) for bot, fp in library.items())
    return [(bot, d) for d, bot in ranked[:k] if math.isfinite(d)]
