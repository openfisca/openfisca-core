from __future__ import annotations

import typing

import numpy

from openfisca_core.parameters import (
    config,
    ParameterNodeAtInstant,
    VectorialParameterNodeAtInstant,
    )

if typing.TYPE_CHECKING:
    import numpy.typing

    from openfisca_core.tracers import FullTracer

    ParameterNode = typing.Union[
        VectorialParameterNodeAtInstant,
        ParameterNodeAtInstant,
        ]

    Child = typing.Union[ParameterNode, numpy.typing.ArrayLike]


class TracingParameterNodeAtInstant:

    def __init__(
            self,
            parameter_node_at_instant: ParameterNode,
            tracer: FullTracer,
            ) -> None:
        self.parameter_node_at_instant = parameter_node_at_instant
        self.tracer = tracer

    def __getattr__(
            self,
            key: str,
            ) -> typing.Union[TracingParameterNodeAtInstant, Child]:
        child = getattr(self.parameter_node_at_instant, key)
        return self.get_traced_child(child, key)

    def __getitem__(
            self,
            key: typing.Union[str, numpy.typing.ArrayLike],
            ) -> typing.Union[TracingParameterNodeAtInstant, Child]:
        child = self.parameter_node_at_instant[key]
        return self.get_traced_child(child, key)

    def get_traced_child(
            self,
            child: Child,
            key: typing.Union[str, numpy.typing.ArrayLike],
            ) -> typing.Union[TracingParameterNodeAtInstant, Child]:
        period = self.parameter_node_at_instant._instant_str

        if isinstance(
                child,
                (ParameterNodeAtInstant, VectorialParameterNodeAtInstant),
                ):
            return TracingParameterNodeAtInstant(child, self.tracer)

        if not isinstance(key, str) or \
            isinstance(
                self.parameter_node_at_instant,
                VectorialParameterNodeAtInstant,
                ):
            # In case of vectorization, we keep the parent node name as, for
            # instance, rate[status].zone1 is best described as the value of
            # "rate".
            name = self.parameter_node_at_instant._name

        else:
            name = '.'.join([self.parameter_node_at_instant._name, key])

        if isinstance(child, (numpy.ndarray,) + config.ALLOWED_PARAM_TYPES):
            self.tracer.record_parameter_access(name, period, child)

        return child
