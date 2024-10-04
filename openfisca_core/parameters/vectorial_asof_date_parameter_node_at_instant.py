import numpy

from openfisca_core.parameters.parameter_node_at_instant import ParameterNodeAtInstant
from openfisca_core.parameters.vectorial_parameter_node_at_instant import (
    VectorialParameterNodeAtInstant,
)


class VectorialAsofDateParameterNodeAtInstant(VectorialParameterNodeAtInstant):
    """Parameter node of the legislation at a given instant which has been vectorized along some date.
    Vectorized parameters allow requests such as parameters.housing_benefit[date], where date is a numpy.datetime64 type vector.
    """

    @staticmethod
    def build_from_node(node):
        VectorialParameterNodeAtInstant.check_node_vectorisable(node)
        subnodes_name = node._children.keys()
        # Recursively vectorize the children of the node
        vectorial_subnodes = tuple(
            [
                (
                    VectorialAsofDateParameterNodeAtInstant.build_from_node(
                        node[subnode_name],
                    ).vector
                    if isinstance(node[subnode_name], ParameterNodeAtInstant)
                    else node[subnode_name]
                )
                for subnode_name in subnodes_name
            ],
        )
        # A vectorial node is a wrapper around a numpy recarray
        # We first build the recarray
        recarray = numpy.array(
            [vectorial_subnodes],
            dtype=[
                (
                    subnode_name,
                    subnode.dtype if isinstance(subnode, numpy.recarray) else "float",
                )
                for (subnode_name, subnode) in zip(subnodes_name, vectorial_subnodes)
            ],
        )
        return VectorialAsofDateParameterNodeAtInstant(
            node._name,
            recarray.view(numpy.recarray),
            node._instant_str,
        )

    def __getitem__(self, key):
        # If the key is a string, just get the subnode
        if isinstance(key, str):
            key = numpy.array([key], dtype="datetime64[D]")
            return self.__getattr__(key)
        # If the key is a vector, e.g. ['1990-11-25', '1983-04-17', '1969-09-09']
        if isinstance(key, numpy.ndarray):
            assert numpy.issubdtype(key.dtype, numpy.datetime64)
            names = list(
                self.dtype.names,
            )  # Get all the names of the subnodes, e.g. ['before_X', 'after_X', 'after_Y']
            values = numpy.asarray(list(self.vector[0]))
            names = [name for name in names if not name.startswith("before")]
            names = [
                numpy.datetime64("-".join(name[len("after_") :].split("_")))
                for name in names
            ]
            conditions = sum([name <= key for name in names])
            result = values[conditions]

            # If the result is not a leaf, wrap the result in a vectorial node.
            if numpy.issubdtype(result.dtype, numpy.record) or numpy.issubdtype(
                result.dtype,
                numpy.void,
            ):
                return VectorialAsofDateParameterNodeAtInstant(
                    self._name,
                    result.view(numpy.recarray),
                    self._instant_str,
                )

            return result
        return None
