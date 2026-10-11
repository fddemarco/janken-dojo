"""The research notebook (`workspace.notebook`, research/ by default), as data.

The notebook stays markdown that people read and commit; these modules read and write
its fixed formats so the CLI can do the bookkeeping:

    ideas.py     ideas.md: the backlog table
    notes.py     experiments/NNNN-<slug>.md: one note per experiment or study
    insights.py  insights.md: confirmed findings
    state.py     the research state, and the next step of the lab's loop

Nothing here plays matches or reads the runs database: callers pass that in.
"""
