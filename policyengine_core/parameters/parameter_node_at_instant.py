import os
import sys
from typing import TYPE_CHECKING, Iterable, Union

import numpy

from policyengine_core import parameters, tools
from policyengine_core.errors import ParameterNotFoundError
from policyengine_core.parameters import helpers

if TYPE_CHECKING:
    from policyengine_core.parameters.parameter_node import ParameterNode

from policyengine_core.parameters.vectorial_parameter_node_at_instant import (
    VectorialParameterNodeAtInstant,
)


class ParameterNodeAtInstant:
    """
    Parameter node of the legislation, at a given instant.
    """

    def __init__(self, name: str, node: "ParameterNode", instant_str: str):
        """
        :param name: Name of the node.
        :param node: Original :any:`ParameterNode` instance.
        :param instant_str: A date in the format `YYYY-MM-DD`.
        """

        # The "technical" attributes are hidden, so that the node children can be easily browsed with auto-completion without pollution
        self._name = name
        self._instant_str = instant_str
        self._children = {}

        for child_name, child in node.children.items():
            child_at_instant = child._get_at_instant(instant_str)
            if child_at_instant is not None:
                self.add_child(child_name, child_at_instant)

    def add_child(
        self, child_name: str, child_at_instant: "ParameterNodeAtInstant"
    ):
        self._children[child_name] = child_at_instant
        setattr(self, child_name, child_at_instant)

    def __getattr__(self, key: str):
        param_name = helpers._compose_name(self._name, item_name=key)
        raise ParameterNotFoundError(param_name, self._instant_str)

    def __getitem__(
        self, key: str
    ) -> Union["ParameterNodeAtInstant", VectorialParameterNodeAtInstant]:
        # If fancy indexing is used, cast to a vectorial node
        if isinstance(key, numpy.ndarray):
            return parameters.VectorialParameterNodeAtInstant.build_from_node(
                self
            )[key]
        return self._children[key]

    def __iter__(self) -> Iterable:
        return iter(self._children)

    def __repr__(self) -> str:
        result = os.linesep.join(
            [
                os.linesep.join(["{}:", "{}"]).format(
                    name, tools.indent(repr(value))
                )
                for name, value in self._children.items()
            ]
        )
        if sys.version_info < (3, 0):
            return result
        return result
