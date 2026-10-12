"""`janken bot ...`: the bots, as files to scaffold, check and inspect."""

import os
import random
from typing import Annotated, Any

import typer

from .. import settings
from .options import CFG, Lab, about, bot_path, fail, lab_command, shown

app = typer.Typer(
    help="The bots: scaffold, check and inspect them.", no_args_is_help=True
)


def _check_folder(lab: Lab, path: str) -> None:
    """Refuse a bot of the field that isn't in its level's folder, and a block
    that isn't a heuristic (L1, or an Oracle's research stand-in).

    Raises:
        typer.Exit: the bot is in the field but not in its level folder.
    """
    from .. import library, mocks
    from ..engine import registry
    from ..kit import levels

    folder_name = os.path.basename(os.path.dirname(os.path.normpath(path)))
    if folder_name == library.BLOCKS:
        level = mocks.path_level(path)
        if level not in (1, levels.ORACLE):
            raise fail(f"{path}: a block is a heuristic (L1), not an L{level}")
        return
    root = os.path.normpath(registry.field_root(path))
    if root != os.path.normpath(lab.bots_dir):
        return  # outside the field (bots/inactive/...): no level folder to be in
    folder = registry.expected_folder(path)
    if os.path.dirname(os.path.normpath(path)) != folder:
        raise fail(f"{path}: its level's folder is {folder}: move it there")


def _with_description(template: str, description: str) -> str:
    """The template's YAML with its top-level `description` block replaced."""
    lines = template.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.startswith("description:")), -1
    )
    body = [
        "description: |",
        *(f"  {line}" if line else "" for line in description.splitlines()),
    ]
    if start < 0:
        return "\n".join(body + lines) + "\n"
    end = start + 1
    while end < len(lines) and (not lines[end] or lines[end][0].isspace()):
        end += 1
    return "\n".join(lines[:start] + body + lines[end:]) + "\n"


@app.command()
@lab_command("bot new")
def new(
    lab: Lab,
    name: Annotated[
        str, typer.Argument(help="the new bot's stem: its identity, never reused")
    ],
    template: Annotated[
        str, typer.Option("--from", help="the bot to start from (a stem or a path)")
    ],
    description: Annotated[
        str,
        typer.Option(
            help="the idea in one line, then 2-4 lines: what and why (\\n separated)"
        ),
    ],
    idea: Annotated[
        int, typer.Option(help="the ideas.md number it implements; 0: none")
    ] = 0,
) -> None:
    """Scaffold bots/<level>/NAME.yaml from another bot (and its space file, if it has
    defaults), in the template's level folder.

    Edit the blueprint afterwards; `janken bot check NAME` verifies it, and refuses
    it until it sits in its new blueprint's level folder (move it there).
    """
    from .. import botfile, library, mocks
    from ..kit import levels
    from ..lab import space
    from ..notebook import ideas, species

    if not name.isidentifier():
        raise fail(f"a bot's stem is an identifier, got {name!r}")
    if species.is_versioned(name):
        raise fail(
            f"{name} names a version: versions are given by `janken species classify`"
            " after a keep; pick a plain stem"
        )
    taken = library.Library(lab.bots_dir).paths(name)
    if taken:
        raise fail(f"{taken[0]} exists: a stem's logic never changes; pick a new name")
    source = bot_path(lab, template)
    if not os.path.isfile(source):
        raise fail(f"no bot {source}")
    folder = os.path.join(lab.bots_dir, levels.folder(mocks.path_level(source)))
    os.makedirs(folder, exist_ok=True)
    target = os.path.join(folder, name + ".yaml")
    with open(source, encoding="utf-8") as f:
        text = _with_description(f.read(), description.replace("\\n", "\n"))
    with open(target, "w", encoding="utf-8") as f:
        f.write(text)
    made = [shown(target)]
    if botfile.defaults(target):
        made.append(
            shown(
                space.write(
                    space.scaffold(target, CFG.space.weight, CFG.space), lab.spaces_dir
                )
            )
        )
    if idea:
        backlog = ideas.load(lab.notebook)
        if backlog.get(idea).state == ideas.OPEN:
            ideas.save(lab.notebook, backlog.set_status(idea, ideas.IN_PROGRESS))
    lab.emit({"created": made}, "created " + ", ".join(made))


@app.command()
@lab_command("bot check")
def check(
    lab: Lab,
    names: Annotated[list[str], typer.Argument(help="bots to check (stems or paths)")],
) -> None:
    """Check bots: the file's contract, that it compiles, and a smoke round robin.

    The smoke run plays --pool-size random bots for --rounds rounds each, and stores
    nothing: it shows the bot runs, it proves nothing.
    """
    from .. import botfile
    from ..engine import play_pairs
    from ..engine.build import load_bot
    from ..engine.registry import P_MAX
    from ..lab.pool import sample_pool
    from ..match import bot_name
    from ..spec import make_spec

    rows = []
    for name in names:
        path = bot_path(lab, name)
        found = botfile.read(path)
        if not found.description:
            raise fail(f"{path}: a bot needs a description")
        if len(found.defaults) > P_MAX:
            raise fail(f"{path}: at most {P_MAX} defaults")
        _check_folder(lab, path)
        load_bot(path)
        seed = (
            random.SystemRandom().getrandbits(32)
            if lab.seed == settings.RANDOM_SEED
            else lab.seed
        )
        pool = sample_pool(
            lab.bots_dir,
            lab.pool_size,
            random.Random(seed),
            [bot_name(path)],
            allow_small=True,
            use_mocks=lab.use_mocks,
        )
        me = make_spec(path)
        results = play_pairs(
            [(me, p) for p in pool],
            lab.rounds,
            list(range(seed, seed + len(pool))),
            lab.workers or None,
        )
        score = sum(
            1.0 if m.winner == me.label else 0.5 if m.winner is None else 0.0
            for m in results
        )
        rows.append(
            {
                "bot": bot_name(path),
                "matches": len(results),
                "score": score / max(len(results), 1),
            }
        )
    lab.emit(
        rows,
        "\n".join(
            f"ok {r['bot']}: compiles; smoke {r['score']:.0%} over {r['matches']} matches"
            for r in rows
        ),
    )


@app.command()
@lab_command("bot export")
def export(
    lab: Lab,
    name: Annotated[
        str,
        typer.Argument(
            help="the bot to export (a stem or a path); a fleet's champion brings its"
            " supports"
        ),
    ],
    out: Annotated[str, typer.Option(help=about("export.dir"))] = CFG.export.dir,
    max_rounds: Annotated[
        int, typer.Option(help=about("export.max_rounds"))
    ] = CFG.export.max_rounds,
) -> None:
    """Export a bot, and its fleet's supports, as tournament submission scripts.

    Each bot becomes one self-contained OUT/NAME/<bot>.py: `play(my_moves, opp_moves)`
    over the kit's runtime as plain stdlib Python (no numpy, numba or `global`). A
    fleet's champion (a bot file with a `fleet` section) brings its supports: a
    fleet of N bots is N scripts, a support's the champion's plus a comment naming
    it and its role line. Every
    script passes the tournament's screening (export.allowed_modules /
    export.banned_names) before anything is written.
    """
    path = bot_path(lab, name)
    if not os.path.isfile(path):
        raise fail(f"no bot {path}")
    written = _export(path, out, max_rounds)
    lab.emit({"exported": written}, "exported " + ", ".join(written))


def _export(path: str, out: str, max_rounds: int) -> list[str]:
    """Write the scripts of the bot at `path` (and its fleet's), screened first.

    Returns:
        The scripts written, as shown paths.

    Raises:
        typer.Exit: the bot can't be exported, or a script fails the screening.
    """
    from .. import export as exporter
    from .. import sandbox
    from ..match import bot_name

    try:
        made = exporter.scripts(path, max_rounds)
    except exporter.ExportError as exc:
        raise fail(str(exc)) from exc
    rules = sandbox.Rules(CFG.export.allowed_modules, CFG.export.banned_names)
    for bot, source in made.items():
        broken = sandbox.scan(source, rules)
        if broken:
            raise fail(f"{bot}'s script fails the screening: {broken[0]}")
    folder = os.path.join(CFG.path(out), bot_name(path))
    os.makedirs(folder, exist_ok=True)
    written = []
    for bot, source in made.items():
        target = os.path.join(folder, bot + ".py")
        with open(target, "w", encoding="utf-8") as f:
            f.write(source)
        written.append(shown(target))
    return written


@app.command()
@lab_command("bot fleet")
def fleet(
    lab: Lab,
    base: Annotated[
        str, typer.Argument(help="the bot the fleet plays (a stem or a path)")
    ],
    champion: Annotated[
        str, typer.Argument(help="the champion's stem: the fleet's file and name")
    ],
    support: Annotated[
        list[str],
        typer.Option(
            help="a support's name, in order; repeatable, size - 1 of them"
            " (none: <champion>_support_K)",
            default_factory=list,
            show_default=False,
        ),
    ],
    size: Annotated[int, typer.Option(help=about("fleet.size"))] = CFG.fleet.size,
    handshake_length: Annotated[
        int, typer.Option(help=about("fleet.handshake_length"))
    ] = CFG.fleet.handshake_length,
    vigilant: Annotated[
        bool, typer.Option(help=about("fleet.vigilant"))
    ] = CFG.fleet.vigilant,
    description: Annotated[
        str,
        typer.Option(
            help="the fleet's description (\\n separated); empty: one written from"
            " the base bot's"
        ),
    ] = "",
    folder: Annotated[str, typer.Option(help=about("fleet.dir"))] = CFG.fleet.dir,
    export_scripts: Annotated[
        bool, typer.Option("--export/--no-export", help=about("fleet.export"))
    ] = CFG.fleet.export,
    out: Annotated[str, typer.Option(help=about("export.dir"))] = CFG.export.dir,
    max_rounds: Annotated[
        int, typer.Option(help=about("export.max_rounds"))
    ] = CFG.export.max_rounds,
) -> None:
    """Scaffold a fleet on a bot: <bots dir>/FOLDER/CHAMPION.yaml, whose core is BASE (its
    defaults bound through) and whose `fleet` section names the supports, the
    handshake and vigilance; then export its SIZE scripts (--no-export: don't).

    The handshake is HANDSHAKE_LENGTH moves drawn at random with --seed (-1: a
    fresh one). The file is checked by compiling it, and lives outside the field: a fleet
    never enters a pool.
    """
    from .. import botfile, library
    from .. import fleet as fleets
    from ..kit import blueprint as bp
    from ..match import bot_name

    if not champion.isidentifier():
        raise fail(f"a bot's stem is an identifier, got {champion!r}")
    taken = library.Library(lab.bots_dir).paths(champion)
    if taken:
        raise fail(f"{taken[0]} exists: a stem's logic never changes; pick a new name")
    source = bot_path(lab, base)
    if not os.path.isfile(source):
        raise fail(f"no bot {source}")
    if size < 2:
        raise fail(f"a fleet has 2 bots or more, got {size}")
    supports = tuple(support) or botfile.support_names(champion, size)
    if len(supports) != size - 1:
        raise fail(f"a fleet of {size} names {size - 1} supports, got {len(supports)}")
    seed = (
        random.SystemRandom().getrandbits(32)
        if lab.seed == settings.RANDOM_SEED
        else lab.seed
    )
    try:
        moves = fleets.draw_handshake(random.Random(seed), handshake_length)
    except fleets.FleetError as exc:
        raise fail(str(exc)) from exc
    found = botfile.read(source)
    crew = botfile.Fleet(supports, moves, vigilant)
    try:
        text = fleets.champion_file(
            bot_name(source),
            found,
            crew,
            description.replace("\\n", "\n")
            or fleets.default_description(
                bot_name(source), champion, crew, found.description
            ),
        )
    except fleets.FleetError as exc:
        raise fail(str(exc)) from exc
    target = os.path.join(lab.bots_dir, folder, champion + ".yaml")
    if os.path.exists(target):
        raise fail(f"{shown(target)} exists")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        library.read_blueprint(target).compile(botfile.defaults(target))
    except (bp.BlueprintError, botfile.BotFileError) as exc:
        os.remove(target)
        raise fail(f"the fleet doesn't compile: {exc}") from exc
    written = _export(target, out, max_rounds) if export_scripts else []
    lab.emit(
        {"created": shown(target), "handshake": moves, "exported": written},
        f"created {shown(target)} (handshake "
        + ",".join(fleets.MOVE_WORDS[m] for m in moves)
        + ")"
        + (f"; exported {', '.join(written)}" if written else ""),
    )


@app.command("list")
@lab_command("bot list")
def list_bots(lab: Lab) -> None:
    """Every bot: its level, one-line description, parameters, and whether it's
    tunable."""
    from .. import botfile, mocks
    from ..engine.registry import discover
    from ..kit import levels
    from ..match import bot_name

    rows: list[dict[str, Any]] = []
    for path in discover(lab.bots_dir):
        found = botfile.read(path)
        stem = bot_name(path)
        rows.append(
            {
                "bot": stem,
                "level": levels.name(mocks.path_level(path)),
                "description": found.description.splitlines()[0]
                if found.description
                else "",
                "params": list(found.defaults),
                "space": os.path.isfile(os.path.join(lab.spaces_dir, stem + ".yaml")),
            }
        )
    lab.emit(
        rows,
        "\n".join(
            f"{r['level']:<7}{r['bot']:<22} {'[space] ' if r['space'] else ''}"
            f"{r['description'][:84]}"
            for r in rows
        ),
    )


@app.command()
@lab_command("bot audit")
def audit(lab: Lab) -> None:
    """Check the whole field agrees with itself: every bot's contract and folder,
    the blocks, unique stems, the space files and research/species.md."""
    from .. import integrity

    problems = integrity.field_problems(lab.bots_dir, lab.spaces_dir, lab.notebook)
    if problems:
        raise fail("\n".join(problems))
    lab.emit({"problems": []}, "ok: the field, its spaces and species.md agree")


@app.command()
@lab_command("bot show")
def show(
    lab: Lab, name: Annotated[str, typer.Argument(help="a bot (stem or path)")]
) -> None:
    """A bot's level and file, and its space file if it has one."""
    from .. import mocks
    from ..kit import levels
    from ..match import bot_name

    path = bot_path(lab, name)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    space_path = os.path.join(lab.spaces_dir, bot_name(path) + ".yaml")
    space_text = ""
    if os.path.isfile(space_path):
        with open(space_path, encoding="utf-8") as f:
            space_text = f.read()
    level = levels.name(mocks.path_level(path))
    lab.emit(
        {"level": level, "bot": text, "space": space_text},
        f"# {shown(path)} ({level})\n{text}"
        + (f"\n# {shown(space_path)}\n{space_text}" if space_text else ""),
    )
