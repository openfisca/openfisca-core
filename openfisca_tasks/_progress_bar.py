from typing import Sequence

import sys
import termcolor


WORK_ICON: str
WORK_ICON = termcolor.colored("[/]", "cyan")

PASS_ICON: str
PASS_ICON = termcolor.colored("[✓]", "green")

INFO_ICON: str
INFO_ICON = termcolor.colored("[i]", "cyan")

WARN_ICON: str
WARN_ICON = termcolor.colored("[i]", "yellow")

FAIL_ICON: str
FAIL_ICON = termcolor.colored("[!]", "red")

BAR_ICON: str
BAR_ICON = termcolor.colored("|", "green")

ACC_ICON: str
ACC_ICON = termcolor.colored("✓", "green")

ETA_ICON: str
ETA_ICON = termcolor.colored("·", "green")

BAR_SIZE: int
BAR_SIZE = 50


class ProgressBar:

    def init(self) -> None:
        sys.stdout.write(self._init_message())

    def push(self, count: int, total: int) -> None:
        done: int

        done = (count + 1) * 100 // total

        sys.stdout.write(self._push_message(done))

    def okay(self, message: str) -> None:
        sys.stdout.write(f"{PASS_ICON} {message}")

    def info(self, message: str) -> None:
        sys.stdout.write(f"{INFO_ICON} {message}")

    def warn(self, message: str) -> None:
        sys.stdout.write(f"{WARN_ICON} {message}")

    def fail(self) -> None:
        sys.stdout.write(f"\r{FAIL_ICON}")

    def next(self) -> None:
        sys.stdout.write("\n\r")

    def wipe(self) -> None:
        sys.stdout.write(self._wipe_message())

    def _init_message(self) -> str:
        return f"{WORK_ICON} 0%   {BAR_ICON}{ETA_ICON * BAR_SIZE}{BAR_ICON}\r"

    def _push_message(self, done: int) -> str:
        message: Sequence[str]
        spaces: str

        spaces = ""
        spaces += [' ', ''][done >= BAR_SIZE * 2]
        spaces += [' ', ''][done >= BAR_SIZE // 5]

        message = [
            f"{WORK_ICON} {done}% {spaces}{BAR_ICON}"
            f"{ACC_ICON * (done // 2)}"
            f"{ETA_ICON * (BAR_SIZE - done // 2)}"
            f"{BAR_ICON}\r"
            ]

        return "".join(message)

    def _wipe_message(self) -> str:
        return f"{' ' * BAR_SIZE * 2}\r"
