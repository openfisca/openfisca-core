import sys

import openfisca_tasks as tasks

if __name__ == "__main__":
    task = tasks.__getattribute__(sys.argv[1])()
    task()
    sys.exit(task.exit)
