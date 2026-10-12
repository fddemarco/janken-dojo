"""The janken command line: `uv run janken COMMAND ...` (typer).

Two levels, in the lab's ubiquitous language (docs/cli.md):

* **High level**, one command per step of the self-improvement lifecycle; each keeps
  the research notebook's books:

      status    the research state and the next step
      idea      the backlog: add, list, show, start, drop
      bot       new, check, list, show
      evaluate  candidates vs random pools, with a note (hypothesis → results)
      tune      a bot or fleet's space → study → validation, with a note
      verdict   close a note: keep, drop or iterate
      species   a kept bot: new species, next version or variant; compare, census
      insight   add (only with evidence that meets the bar), list, supersede
      tournament  the whole field: standings, ratings, titles
      config    every default: show, get, set, unset, path, check

* **Low level**, `janken lab ...`: ad hoc experiments, studies, queries and reports,
  without the notebook; `janken lab profile ...` for performance.

Every lab command shares one set of flags (janken/cli/options.py), and every default
comes from janken.toml (janken/settings.py).
"""

import typer

from . import bots, config, lab, lifecycle, notebook, species

app = typer.Typer(
    name="janken",
    help="The janken (rock-paper-scissors) bot lab: build, test and analyze bots.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

app.command(rich_help_panel="Lifecycle")(lifecycle.status)
app.add_typer(notebook.idea_app, name="idea", rich_help_panel="Lifecycle")
app.add_typer(bots.app, name="bot", rich_help_panel="Lifecycle")
app.command(rich_help_panel="Lifecycle")(lifecycle.evaluate)
app.command(rich_help_panel="Lifecycle")(lifecycle.tune)
app.command(rich_help_panel="Lifecycle")(lifecycle.verdict)
app.add_typer(species.app, name="species", rich_help_panel="Lifecycle")
app.add_typer(notebook.insight_app, name="insight", rich_help_panel="Lifecycle")
app.command(rich_help_panel="Lifecycle")(lifecycle.tournament)
app.add_typer(config.app, name="config", rich_help_panel="Configuration")
app.add_typer(lab.app, name="lab", rich_help_panel="Low level")
