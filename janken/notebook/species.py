"""The field's species and their versions, `species.md`: one table row per species.

    | species | level | current | versions | variants |

A field bot's stem is `<species>_vN`: version N of its species. `versions` is the
lineage, `` `old_stem` (link) --> v1; ... --> v2 ``, and `variants` the bots that behaved like
the species without beating it. Rows are parsed from and rendered back to the table;
every other line of the file, and every row nobody changed, is kept byte for byte.
"""

import dataclasses
import os
import re

FILE = "species.md"
VERSIONED = re.compile(r"^(?P<species>[a-z][a-z0-9_]*?)_v(?P<number>[1-9][0-9]*)$")
NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_ROW = re.compile(r"^\|\s*`[a-z]")
_CELLS = 5


class SpeciesError(ValueError):
    """A species operation that can't be done."""


@dataclasses.dataclass(frozen=True)
class Version:
    """A versioned stem, read: its species and its version number."""

    species: str
    number: int

    @property
    def stem(self) -> str:
        return f"{self.species}_v{self.number}"


def is_versioned(stem: str) -> bool:
    """Whether `stem` names a version of a species (`<species>_vN`)."""
    return VERSIONED.match(stem) is not None


def parse_stem(stem: str) -> Version:
    """The species and version a stem names.

    Raises:
        SpeciesError: the stem has no `_vN` suffix.
    """
    found = VERSIONED.match(stem)
    if found is None:
        raise SpeciesError(f"{stem!r} is not a version: <species>_vN")
    return Version(found["species"], int(found["number"]))


def check_name(name: str) -> str:
    """A new species' name, checked: snake_case, without a version suffix.

    Raises:
        SpeciesError: the name doesn't qualify.
    """
    if not NAME.match(name) or is_versioned(name):
        raise SpeciesError(
            f"a species name is snake_case without a _vN suffix, not {name!r}"
        )
    return name


@dataclasses.dataclass(frozen=True)
class Species:
    """One row: a species, its level, its current version and its lineage."""

    name: str
    level: str  # "L1", "L2", ...
    current: str  # the current version's stem
    versions: str  # "`old` (link) --> v1; `old` (link) --> v2"
    variants: str  # "`stem` (link); ..." or ""

    def row(self) -> str:
        cells = [
            f"`{self.name}`",
            self.level,
            f"`{self.current}`",
            self.versions,
            self.variants,
        ]
        return "|" + "|".join(f" {c} " if c else " " for c in cells) + "|"

    @property
    def number(self) -> int:
        """The current version's number."""
        return parse_stem(self.current).number


def parse_row(line: str) -> Species:
    """A species from its table row.

    Raises:
        SpeciesError: the row doesn't have the table's five cells.
    """
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) != _CELLS:
        raise SpeciesError(
            f"a species row has {_CELLS} cells, got {len(cells)}: {line[:60]}"
        )
    name, level, current, versions, variants = cells
    return Species(name.strip("`"), level, current.strip("`"), versions, variants)


def _joined(cell: str, entry: str) -> str:
    return f"{cell}; {entry}" if cell else entry


def _entry(stem: str, link: str) -> str:
    return f"`{stem}` ({link})" if link else f"`{stem}`"


@dataclasses.dataclass(frozen=True)
class Registry:
    """species.md: its lines, and which of them are species rows."""

    lines: tuple[str, ...]

    @property
    def species(self) -> list[Species]:
        return [parse_row(line) for line in self.lines if _ROW.match(line)]

    def get(self, name: str) -> Species:
        for found in self.species:
            if found.name == name:
                return found
        raise SpeciesError(f"no species {name!r} in {FILE}")

    def of_stem(self, stem: str) -> Species:
        """The species whose current version is `stem`."""
        for found in self.species:
            if found.current == stem:
                return found
        raise SpeciesError(f"no species has {stem!r} as its current version")

    def _replace(self, species: Species) -> "Registry":
        lines = [
            species.row()
            if _ROW.match(line) and parse_row(line).name == species.name
            else line
            for line in self.lines
        ]
        return Registry(tuple(lines))

    def add(self, name: str, level: str, origin: str, link: str) -> "Registry":
        """The registry with a new species at version 1, after the last row.

        Args:
            name: the species' name.
            level: its level, e.g. "L2".
            origin: the stem the bot had before it became version 1.
            link: the note that decided it (markdown), or "".
        """
        check_name(name)
        if name in {s.name for s in self.species}:
            raise SpeciesError(f"species {name!r} exists; pick another name")
        rows = [i for i, line in enumerate(self.lines) if _ROW.match(line)]
        header = [i for i, line in enumerate(self.lines) if line.startswith("|---")]
        if not rows and not header:
            raise SpeciesError(f"{FILE} has no table to add to")
        species = Species(
            name, level, Version(name, 1).stem, f"{_entry(origin, link)} --> v1", ""
        )
        lines = list(self.lines)
        lines.insert((rows or header)[-1] + 1, species.row())
        return Registry(tuple(lines))

    def promote(self, name: str, origin: str, link: str) -> tuple["Registry", str]:
        """The registry with the species' next version, and that version's stem."""
        species = self.get(name)
        nxt = Version(name, species.number + 1)
        versions = _joined(
            species.versions, f"{_entry(origin, link)} --> v{nxt.number}"
        )
        promoted = dataclasses.replace(species, current=nxt.stem, versions=versions)
        return self._replace(promoted), nxt.stem

    def add_variant(self, name: str, stem: str, link: str) -> "Registry":
        """The registry with a variant recorded under its species."""
        species = self.get(name)
        variants = _joined(species.variants, _entry(stem, link))
        return self._replace(dataclasses.replace(species, variants=variants))

    def render(self) -> str:
        return "\n".join(self.lines) + "\n"


def path(notebook: str) -> str:
    return os.path.join(notebook, FILE)


def load(notebook: str) -> Registry:
    with open(path(notebook), encoding="utf-8") as f:
        return parse(f.read())


def parse(text: str) -> Registry:
    return Registry(tuple(text.splitlines()))


def save(notebook: str, registry: Registry) -> None:
    with open(path(notebook), "w", encoding="utf-8") as f:
        f.write(registry.render())
