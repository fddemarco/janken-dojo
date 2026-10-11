"""Where the lab keeps its data: the workspace (`workspace.dir` in janken.toml).

runs.duckdb       experiment runs, their matches, reports, validations
                  (runs_db.py)
dataset.duckdb    the move dataset (dataset.py)
tuning/           Optuna studies (tune.py, predict_tune.py)
"""

import os
import subprocess

from .. import settings

ROOT = settings.ROOT
EXPERIMENTS = settings.config().path(settings.config().workspace.dir)


def tuning_dir(root: str | None = None) -> str:
    return os.path.join(root or EXPERIMENTS, "tuning")


def git_info() -> dict:
    def git(*args):
        return subprocess.run(
            ("git",) + args, cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()

    try:
        return {
            "commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain")),
        }
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}
