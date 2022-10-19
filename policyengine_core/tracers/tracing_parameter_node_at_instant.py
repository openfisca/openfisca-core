from __future__ import annotations

import typing
from typing import Union

import numpy

from policyengine_core import parameters

from .. import tracers

ParameterNode = Union[
    parameters.VectorialParameterNodeAtInstant,
    parameters.ParameterNodeAtInstant,
]

if typing.TYPE_CHECKING:
    from numpy.typing import ArrayLike

    Child = Union[ParameterNode, ArrayLike]


class TracingParameterNodeAtInstant:
    def __init__(
        self,
        parameter_node_at_instant: ParameterNode,
        tracer: tracers.FullTracer,
        branch_name: str,
    ) -> None:
        self.parameter_node_at_instant = parameter_node_at_instant
        self.tracer = tracer
        self.branch_name = branch_name

    def __getattr__(
        self,
        key: str,
    ) -> Union[TracingParameterNodeAtInstant, Child]:
        child = getattr(self.parameter_node_at_instant, key)
        return self.get_traced_child(child, key)

    def __getitem__(
        self,
        key: Union[str, ArrayLike],
    ) -> Union[TracingParameterNodeAtInstant, Child]:
        child = self.parameter_node_at_instant[key]
        return self.get_traced_child(child, key)

    def get_traced_child(
        self,
        child: Child,
        key: Union[str, ArrayLike],
    ) -> Union[TracingParameterNodeAtInstant, Child]:
        period = self.parameter_node_at_instant._instant_str

        if isinstance(
            child,
            (
                parameters.ParameterNodeAtInstant,
                parameters.VectorialParameterNodeAtInstant,
            ),
        ):
            return TracingParameterNodeAtInstant(
                child, self.tracer, self.branch_name
            )

        if not isinstance(key, str) or isinstance(
            self.parameter_node_at_instant,
            parameters.VectorialParameterNodeAtInstant,
        ):
            # In case of vectorization, we keep the parent node name as, for
            # instance, rate[status].zone1 is best described as the value of
            # "rate".
            name = self.parameter_node_at_instant._name

        else:
            name = ".".join([self.parameter_node_at_instant._name, key])

        if isinstance(
            child, (numpy.ndarray,) + parameters.ALLOWED_PARAM_TYPES
        ):
            self.tracer.record_parameter_access(
                name, period, self.branch_name, child
            )

        return child
