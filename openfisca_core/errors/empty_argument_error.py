import typing

import os
import traceback

import numpy


class EmptyArgumentError(IndexError):
    """Exception raised when a method is called with an empty argument."""

    message: str

    def __init__(
        self,
        class_name: str,
        method_name: str,
        arg_name: str,
        arg_value: typing.Union[list, numpy.ndarray],
    ) -> None:
        message = [
            f"'{class_name}.{method_name}' can't be run with an empty '{arg_name}':\n",
            f">>> {arg_name}",
            f"{arg_value}\n",
            "Here are some hints to help you get this working:\n",
            f"- Check that '{class_name}' isn't empty (see '{class_name}.add_bracket')",
            f"- Check that '{arg_name}' is being properly assigned "
            f"('{arg_name}' should be a non empty '{type(arg_value).__name__}')\n",
            "For further support, please do not hesitate to:\n",
            "- Take a look at the official documentation https://openfisca.org/doc",
            "- Open an issue on https://github.com/openfisca/openfisca-core/issues/new",
            "- Mention us via https://twitter.com/openfisca",
            "- Drop us a line to contact@openfisca.org\n",
            "😃",
        ]
        stacktrace = os.linesep.join(traceback.format_stack())
        self.message = os.linesep.join([f"  {line}" for line in message])
        self.message = os.linesep.join([stacktrace, self.message])
        super().__init__(self.message)
