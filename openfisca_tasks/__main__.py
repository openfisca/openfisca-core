import abc
import sys

from typing_extensions import Protocol

import openfisca_tasks as tasks


class HasExit(Protocol):
    exit: int

    @abc.abstractmethod
    def __call__(self) -> None:
        ...

    @abc.abstractmethod
    def __init_progress__(self) -> None:
        ...

    @abc.abstractmethod
    def __push_progress__(self) -> None:
        ...

    @abc.abstractmethod
    def __wipe_progress__(self) -> None:
        ...


if __name__ == "__main__":
    task: HasExit
    task = tasks.__getattribute__(sys.argv[1])()
    task()
    sys.exit(task.exit)
