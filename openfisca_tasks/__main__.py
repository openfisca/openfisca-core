import abc
import sys

from typing_extensions import Protocol

import openfisca_tasks as tasks


class HasExit(Protocol):
    exit: int

    @abc.abstractmethod
    def __call__(self) -> None:
        ...


if __name__ == "__main__":
    task: HasExit
    task = tasks.__getattribute__(sys.argv[1])()
    task()
    sys.exit(task.exit)
