from typing import Sequence

import sys
import termcolor


class ProgressBar:
    """Provides a progress bar for tasks.

    Attributes:
        work_icon: An icon to show when working.
        info_icon: An icon to show when displaying information.
        warn_icon: An icon to show when warning the user of something.
        okay_icon: An icon to show when something succeeded.
        fail_icon: An icon to show when something failed.
        bar_icon: The borders of progress bar.
        acc_icon: The accumulated progress icon.
        eta_icon: The remaining work to finish icon.
        bar_size: The size of the progress bar.


    .. versionadded:: 36.1.0

    """

    work_icon: str = termcolor.colored("[/]", "cyan")
    info_icon: str = termcolor.colored("[i]", "cyan")
    warn_icon: str = termcolor.colored("[!]", "yellow")
    okay_icon: str = termcolor.colored("[✓]", "green")
    fail_icon: str = termcolor.colored("[x]", "red")

    bar_icon: str = termcolor.colored("|", "green")
    acc_icon: str = termcolor.colored("✓", "green")
    eta_icon: str = termcolor.colored("·", "green")

    bar_size: int = 50

    def init(self) -> None:
        """Initialises the progress bar."""

        sys.stdout.write(self._init_message())

    def push(self, count: int, total: int) -> None:
        """Pushes progress to the ``stdout``."""

        done: int = (count + 1) * 100 // total
        sys.stdout.write(self._push_message(done))

    def okay(self, message: str) -> None:
        """Prints an okay ``message``."""

        sys.stdout.write(f"{self.okay_icon} {message}")

    def info(self, message: str) -> None:
        """Prints an info ``message``."""

        sys.stdout.write(f"{self.info_icon} {message}")

    def warn(self, message: str) -> None:
        """Prints a warn ``message``."""

        sys.stdout.write(f"{self.warn_icon} {message}")

    def fail(self) -> None:
        """Marks last printed message as failing."""

        sys.stdout.write(f"\r{self.fail_icon}")

    def then(self) -> None:
        """Prints a new line and resets the cursor position."""

        sys.stdout.write("\n\r")

    def wipe(self) -> None:
        """Cleans last printed message."""

        sys.stdout.write(self._wipe_message())

    def _init_message(self) -> str:
        message: Sequence[str]
        message = [
            f"{self.work_icon} 0%   {self.bar_icon}",
            f"{self.eta_icon * self.bar_size}{self.bar_icon}\r",
            ]

        return "".join(message)

    def _push_message(self, done: int) -> str:
        message: Sequence[str]
        spaces: str

        spaces = ""
        spaces += [" ", ""][done >= self.bar_size * 2]
        spaces += [" ", ""][done >= self.bar_size // 5]

        message = [
            f"{self.work_icon} {done}% {spaces}{self.bar_icon}"
            f"{self.acc_icon * (done // 2)}"
            f"{self.eta_icon * (self.bar_size - done // 2)}"
            f"{self.bar_icon}\r"
            ]

        return "".join(message)

    def _wipe_message(self) -> str:
        return f"{' ' * self.bar_size * 2}\r"
