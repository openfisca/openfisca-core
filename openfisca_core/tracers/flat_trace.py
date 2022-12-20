from __future__ import annotations

from typing import Any, Dict

import numpy

from openfisca_core import indexed_enums as enums, types


class FlatTrace:
    _full_tracer: types.FullTracer

    def __init__(self, full_tracer: types.FullTracer) -> None:
        self._full_tracer = full_tracer

    def key(self, node: types.TraceNode) -> str:
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

    def serialize(self, value: Any) -> Any:
        if not isinstance(value, numpy.ndarray):
            return value

        if isinstance(value, enums.EnumArray):
            return value.decode_to_str().tolist()

        if numpy.issubdtype(value.dtype, numpy.dtype(bytes)):
            return value.astype(numpy.dtype(str)).tolist()

        return value.tolist()

    def _get_flat_trace(self, node: types.TraceNode) -> Dict[str, dict]:
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
