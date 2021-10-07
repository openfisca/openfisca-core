from __future__ import annotations

import typing
from typing import Dict, Optional, Union

import numpy

from openfisca_core import tracers
from openfisca_core.indexed_enums import EnumArray

if typing.TYPE_CHECKING:
    from numpy.typing import ArrayLike

    Array = Union[EnumArray, ArrayLike]
    Trace = Dict[str, dict]


class FlatTrace:

    _full_tracer: tracers.FullTracer

    def __init__(self, full_tracer: tracers.FullTracer) -> None:
        self._full_tracer = full_tracer

    def key(self, node: tracers.TraceNode) -> str:
        name = node.name
        period = node.period
        return f"{name}<{period}>"

    def get_trace(self) -> dict:
        trace = {}

        for node in self._full_tracer.browse_trace():
            # We don't want cache read to overwrite data about the initial
            # calculation.
            #
            # We therefore use a non-overwriting update.
            trace.update({
                key: node_trace
                for key, node_trace in self._get_flat_trace(node).items()
                if key not in trace
                })

        return trace

    def get_serialized_trace(self) -> dict:
        return {
            key: {
                **flat_trace,
                'value': self.serialize(flat_trace['value'])
                }
            for key, flat_trace in self.get_trace().items()
            }

    def serialize(
            self,
            value: Optional[Array],
            ) -> Union[Optional[Array], list]:
        if isinstance(value, EnumArray):
            value = value.decode_to_str()

        if isinstance(value, numpy.ndarray) and \
           numpy.issubdtype(value.dtype, numpy.dtype(bytes)):
            value = value.astype(numpy.dtype(str))

        if isinstance(value, numpy.ndarray):
            value = value.tolist()

        return value

    def _get_flat_trace(
            self,
            node: tracers.TraceNode,
            ) -> Trace:
        key = self.key(node)

        node_trace = {
            key: {
                'dependencies': [
                    self.key(child) for child in node.children
                    ],
                'parameters': {
                    self.key(parameter):
                        self.serialize(parameter.value)
                        for parameter
                        in node.parameters
                    },
                'value': node.value,
                'calculation_time': node.calculation_time(),
                'formula_time': node.formula_time(),
                },
            }

        return node_trace
