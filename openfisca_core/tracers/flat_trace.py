from __future__ import annotations

import numpy

from openfisca_core import types as t
from openfisca_core.indexed_enums import EnumArray


class FlatTrace:
    _full_tracer: t.FullTracer

    def __init__(self, full_tracer: t.FullTracer) -> None:
        self._full_tracer = full_tracer

    def get_trace(self) -> t.FlatNodeMap:
        trace: t.FlatNodeMap = {}

        for node in self._full_tracer.browse_trace():
            # We don't want cache read to overwrite data about the initial
            # calculation.
            #
            # We therefore use a non-overwriting update.
            trace.update(
                {
                    key: node_trace
                    for key, node_trace in self._get_flat_trace(node).items()
                    if key not in trace
                },
            )

        return trace

    def get_serialized_trace(self) -> t.SerializedNodeMap:
        return {
            key: {**flat_trace, "value": self.serialize(flat_trace["value"])}
            for key, flat_trace in self.get_trace().items()
        }

    def _get_flat_trace(
        self,
        node: t.TraceNode,
    ) -> t.FlatNodeMap:
        key = self.key(node)

        return {
            key: {
                "dependencies": [self.key(child) for child in node.children],
                "parameters": {
                    self.key(parameter): self.serialize(parameter.value)
                    for parameter in node.parameters
                },
                "value": node.value,
                "calculation_time": node.calculation_time(),
                "formula_time": node.formula_time(),
            },
        }

    @staticmethod
    def key(node: t.TraceNode) -> t.NodeKey:
        """Return the key of a node."""
        name = node.name
        period = node.period
        return t.NodeKey(f"{name}<{period}>")

    @staticmethod
    def serialize(
        value: None | t.VarArray | t.ArrayLike[object],
    ) -> None | t.ArrayLike[object]:
        if value is None:
            return None

        if isinstance(value, EnumArray):
            return value.decode_to_str().tolist()

        if isinstance(value, numpy.ndarray) and numpy.issubdtype(
            value.dtype,
            numpy.dtype(bytes),
        ):
            return value.astype(numpy.dtype(str)).tolist()

        if isinstance(value, numpy.ndarray):
            return value.tolist()

        return value


__all__ = ["FlatTrace"]
