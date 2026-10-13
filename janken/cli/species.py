"""`janken species ...`: the field's species and their versions.

classify   a kept note's candidate: a new species, the next version, or a variant
compare    a bot against the field's species, by core agreement (read-only)
variants   which parameter variants of field bots behave like no species (read-only)
census     the field's most alike species pairs, and species per level (read-only)
list       research/species.md: every species, its current version and lineage
"""

import dataclasses
import os
from collections import Counter
from typing import Annotated

import typer

from .lifecycle import plan_for
from .options import CFG, Lab, Split, about, bot_path, lab_command, shown

app = typer.Typer(
    help="Species and versions: one bot per species in the field (research/species.md).",
    no_args_is_help=True,
)

SPECIES_SPLIT = Split(CFG.species.split)
SPLIT_HELP = about("species.split")


def _histories(lab: Lab, split: str):
    from ..lab import workflows

    return workflows.histories(
        os.path.join(lab.workspace, CFG.dataset.file),
        split,
        CFG.dataset.holdout,
        CFG.species.matches,
    )


@app.command()
@lab_command("species classify")
def classify(
    lab: Lab,
    note: Annotated[
        str, typer.Argument(help="the kept note (number or NNNN-name) to classify")
    ],
    name: Annotated[
        str,
        typer.Option(
            help="a new species' name (snake_case, no _vN); only for a new species"
        ),
    ] = "",
    split: Annotated[Split, typer.Option(help=SPLIT_HELP)] = SPECIES_SPLIT,
) -> None:
    """Classify a kept bot: a new species (v1), the next version, or a variant.

    Compares its core with every species of its level on the move dataset; when one
    is alike, plays a paired run against its current version (species.round_robins,
    unless --round-robins or --effort is given). Renames or retires the bot files,
    records the lineage in research/species.md and writes the note's Species section.
    """
    from ..lab import workflows

    how = plan_for(lab, CFG.evaluation.mode)
    if not {"round_robins", "effort"} & lab.passed:
        how = dataclasses.replace(how, round_robins=CFG.species.round_robins)
    done = workflows.classify_note(
        lab.notebook,
        note,
        name,
        how,
        lab.spaces_dir,
        CFG.species,
        _histories(lab, str(split)),
    )
    lab.emit(
        {
            "note": shown(done.note.path),
            "outcome": done.decision.outcome,
            "reasons": list(done.decision.reasons),
            "stem": done.stem,
            "path": shown(done.path),
            "incumbent": done.incumbent,
            "run": done.run_id,
            "speedup": done.speedup,
        },
        f"{done.decision.outcome}: {shown(done.path)}\n\n"
        + workflows.render_classification(done)
        + f"\n\nnote: {shown(done.note.path)}; species: research/species.md",
    )


@app.command()
@lab_command("species compare")
def compare(
    lab: Lab,
    bot: Annotated[str, typer.Argument(help="the bot: a stem or a path")],
    split: Annotated[Split, typer.Option(help=SPLIT_HELP)] = SPECIES_SPLIT,
) -> None:
    """Rank the field's species by how alike their cores are to a bot's."""
    from ..lab import workflows

    path = bot_path(lab, bot)
    seqs = _histories(lab, str(split))
    cache = workflows.core_cache(lab.workspace, CFG.species)
    field = workflows.read_field(workflows.species_paths(lab.bots_dir), seqs, cache)
    kin = workflows.compare(path, field, seqs, cache)
    level = workflows.bot_level(path)
    lab.emit(
        {
            "bot": bot,
            "level": level,
            "species": [k.__dict__ for k in kin],
        },
        f"{bot} ({level}); alike at >= {CFG.species.agreement:.0%} core agreement,"
        " and only a species of its own level can take it as a version\n\n"
        + workflows.render_kin(kin),
    )


@app.command()
@lab_command("species variants")
def variants(
    lab: Lab,
    bots: Annotated[
        str,
        typer.Argument(
            help="a file of bot specs, one per line (bots/l1/x.yaml:NAME=value,...);"
            " plain bot files are skipped"
        ),
    ],
    out: Annotated[str, typer.Argument(help="the markdown table to write")],
    split: Annotated[Split, typer.Option(help=SPLIT_HELP)] = SPECIES_SPLIT,
) -> None:
    """Which parameter variants behave like no species of their level: new bots."""
    from ..lab import workflows

    with open(bots) as lines:
        texts = [t.split("#")[0].strip() for t in lines]
    texts = [t for t in texts if ":" in t]
    seqs = _histories(lab, str(split))
    cache = workflows.core_cache(lab.workspace, CFG.species)
    field = workflows.read_field(workflows.species_paths(lab.bots_dir), seqs, cache)
    bar = CFG.species.agreement
    rows = [
        (
            f"A variant agreeing with no species of its level on >= {bar:.0%} of the"
            " moves (core agreement) is a new bot by the species rule."
        ),
        "",
        "| variant | level | closest species | core agreement | new bot |",
        "|---|---|---|---|---|",
    ]
    new_bots = []
    for text in texts:
        kin = workflows.variant_kin(text, field, seqs, cache)
        top = kin[0]
        is_new = top.agreement < bar
        if is_new:
            new_bots.append(text)
        rows.append(
            f"| `{text}` | {top.level} | `{top.stem}` | {top.agreement:.1%}"
            f" | {'yes' if is_new else 'no'} |"
        )
        lab.say(rows[-1])
    with open(out, "w") as sink:
        sink.write("\n".join(rows) + "\n")
    lab.emit(
        {"new": new_bots, "checked": len(texts)},
        f"{len(new_bots)} of {len(texts)} variants are new bots (table: {out})",
    )


@app.command()
@lab_command("species census")
def census(
    lab: Lab,
    split: Annotated[Split, typer.Option(help=SPLIT_HELP)] = SPECIES_SPLIT,
) -> None:
    """The field's diversity: species per level, and the most alike pairs."""
    from ..lab import classify as kinship
    from ..lab import workflows

    seqs = _histories(lab, str(split))
    field = workflows.read_field(
        workflows.species_paths(lab.bots_dir),
        seqs,
        workflows.core_cache(lab.workspace, CFG.species),
    )
    per_level = Counter(field.levels.values())
    found = kinship.pairs(field.cores)
    alike = [p for p in found if p[2] >= CFG.species.agreement]
    rows = [
        f"| `{a}` | {field.levels[a]} | `{b}` | {field.levels[b]} | {x:.1%} |"
        for a, b, x in alike
    ]
    text = [
        "## Species per level",
        "",
        "\n".join(f"- {lvl}: {n}" for lvl, n in sorted(per_level.items())),
        "",
        f"## Alike pairs (core agreement >= {CFG.species.agreement:.0%})",
        "",
        "\n".join(
            [
                "| species | level | species | level | agreement |",
                "|---|---|---|---|---|",
                *rows,
            ]
        )
        if rows
        else "(none: every species is distinct)",
    ]
    lab.emit(
        {
            "levels": dict(per_level),
            "pairs": [{"a": a, "b": b, "agreement": x} for a, b, x in found],
        },
        "\n".join(text),
    )


@app.command("list")
@lab_command("species list")
def list_species(lab: Lab) -> None:
    """Every species: its level, current version, lineage and variants."""
    from ..notebook import species

    found = species.load(lab.notebook).species
    lab.emit(
        [s.__dict__ for s in found],
        "\n".join(
            [
                "| species | level | current | versions | variants |",
                "|---|---|---|---|---|",
                *(s.row() for s in found),
            ]
        ),
    )
