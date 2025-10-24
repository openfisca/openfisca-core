from __future__ import annotations

import typing
from typing import Union

import numpy

from openfisca_core import parameters

ParameterNode = Union[
    parameters.VectorialParameterNodeAtInstant,
    parameters.ParameterNodeAtInstant,
]

if typing.TYPE_CHECKING:
    from numpy.typing import ArrayLike

    from openfisca_core import tracers

    Child = Union[ParameterNode, ArrayLike]


class TracingParameterNodeAtInstant:
    def __init__(
        self,
        parameter_node_at_instant: ParameterNode,
        tracer: tracers.FullTracer,
    ) -> None:
        self.parameter_node_at_instant = parameter_node_at_instant
        self.tracer = tracer

    def __getattr__(
        self,
        key: str,
    ) -> TracingParameterNodeAtInstant | Child:
        child = getattr(self.parameter_node_at_instant, key)
        return self.get_traced_child(child, key)

    def __contains__(self, key) -> bool:
        return key in self.parameter_node_at_instant

    def __iter__(self):
        return iter(self.parameter_node_at_instant)

    def __getitem__(
        self,
        key: str | ArrayLike,
    ) -> TracingParameterNodeAtInstant | Child:
        child = self.parameter_node_at_instant[key]
        return self.get_traced_child(child, key)

    def get_traced_child(
        self,
        child: Child,
        key: str | ArrayLike,
    ) -> TracingParameterNodeAtInstant | Child:
        period = self.parameter_node_at_instant._instant_str

        if isinstance(
            child,
            (
                parameters.ParameterNodeAtInstant,
                parameters.VectorialParameterNodeAtInstant,
            ),
        ):
            return TracingParameterNodeAtInstant(child, self.tracer)

        if not isinstance(key, str) or isinstance(
            self.parameter_node_at_instant,
            parameters.VectorialParameterNodeAtInstant,
        ):
            # In case of vectorization, we keep the parent node name as, for
            # instance, rate[status].zone1 is best described as the value of
            # "rate".
            name = self.parameter_node_at_instant._name

        else:
            name = f"{self.parameter_node_at_instant._name}.{key}"

        if isinstance(child, (numpy.ndarray, *parameters.ALLOWED_PARAM_TYPES)):
            self.tracer.record_parameter_access(name, period, child)

        return child
