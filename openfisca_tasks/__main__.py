from __future__ import annotations

import sys

import openfisca_tasks as tasks

from ._progress_bar import ProgressBar
from ._protocols import HasExit


if __name__ == "__main__":
    task: HasExit
    task = tasks.__getattribute__(sys.argv[1])()

    progress: ProgressBar
    progress = ProgressBar()

    task(progress)
    sys.exit(task.exit.index)
