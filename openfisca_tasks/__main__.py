from __future__ import annotations

import sys

import openfisca_tasks as tasks

from openfisca_tasks import Bar, SupportsProgress

from ._types import HasExit


if __name__ == "__main__":
    bar: SupportsProgress = Bar()
    task: HasExit = tasks.__getattribute__(sys.argv[1])(bar)
    task()
    sys.exit(task.exit.index)
