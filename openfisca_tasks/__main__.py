from __future__ import annotations

import sys

import openfisca_tasks as tasks

from ._progress_bar import ProgressBar
from ._protocols import HasExit, SupportsProgress


if __name__ == "__main__":
    progress: SupportsProgress = ProgressBar()
    task: HasExit = tasks.__getattribute__(sys.argv[1])(progress)
    task()
    sys.exit(task.exit.index)
