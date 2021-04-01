import typing

import numpy

from openfisca_core import indexed_enums, tracers


class FlatTrace:

    def __init__(self, full_tracer):
        self._full_tracer = full_tracer

    def key(self, node: tracers.TraceNode) -> str:
        name = node.name
        period = node.period
        return f"{name}<{period}>"

    def get_trace(self):
        trace = {}
        for node in self._full_tracer.browse_trace():
            trace.update({  # We don't want cache read to overwrite data about the initial calculation. We therefore use a non-overwriting update.
                key: node_trace
                for key, node_trace in self._get_flat_trace(node).items()
                if key not in trace
                })
        return trace

    def get_serialized_trace(self):
        return {
            key: {
                **flat_trace,
                'value': self.serialize(flat_trace['value'])
                }
            for key, flat_trace in self.get_trace().items()
            }

    def serialize(self, value: numpy.ndarray) -> typing.List:
        if isinstance(value, indexed_enums.EnumArray):
            value = value.decode_to_str()
        if isinstance(value, numpy.ndarray) and numpy.issubdtype(value.dtype, numpy.dtype(bytes)):
            value = value.astype(numpy.dtype(str))
        if isinstance(value, numpy.ndarray):
            value = value.tolist()
        return value

    def _get_flat_trace(self, node: tracers.TraceNode) -> typing.Dict[str, typing.Dict]:
        key = self.key(node)

        node_trace = {
            key: {
                'dependencies': [
                    self.key(child) for child in node.children
                    ],
                'parameters': {
                    self.key(parameter): self.serialize(parameter.value) for parameter in node.parameters
                    },
                'value': node.value,
                'calculation_time': node.calculation_time(),
                'formula_time': node.formula_time(),
                },
            }
        return node_trace
