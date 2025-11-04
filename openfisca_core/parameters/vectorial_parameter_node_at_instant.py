from typing import NoReturn

import numpy

from openfisca_core import parameters
from openfisca_core.indexed_enums import Enum, EnumArray


class VectorialParameterNodeAtInstant:
    def __init__(self, vector, name, instant_str) -> None:
        self.vector = vector
        self._name = name
        self._instant_str = instant_str

    @staticmethod
    def _get_appropriate_subnode_function(k):
        if isinstance(k, str):
            return VectorialParameterNodeAtInstant._get_appropriate_subnode_key_string
        if isinstance(k, Enum):
            return VectorialParameterNodeAtInstant._get_appropriate_subnode_key_enum
        if isinstance(k, numpy.integer):
            return VectorialParameterNodeAtInstant._get_appropriate_subnode_key_integer
        return VectorialParameterNodeAtInstant._get_appropriate_subnode_key_date

    @staticmethod
    def _get_appropriate_subnode_key_string(node, k):
        return k

    @staticmethod
    def _get_appropriate_subnode_key_enum(node, k):
        return k.name

    @staticmethod
    def _get_appropriate_subnode_key_integer(node, k):
        return str(k)

    @staticmethod
    def _get_appropriate_subnode_key_date(node, k):
        subnodes_name = list(node._children.keys())
        names = [name for name in subnodes_name if not name.startswith("before")]
        points_in_time = [
            numpy.datetime64("-".join(name[len("after_") :].split("_")))
            for name in names
        ]
        index = sum([name <= k for name in points_in_time])
        return subnodes_name[index]

    def _get_appropriate_keys(key):
        if isinstance(key, EnumArray):
            enum = key.possible_values
            return numpy.select(
                [key == item.index for item in enum],
                [item.name for item in enum],
            )
        if key.dtype == object and issubclass(type(key[0]), Enum):
            return key
        return key

    @staticmethod
    def build_from_node_name(node, key):
        VectorialParameterNodeAtInstant.check_node_vectorisable(node)
        keys = VectorialParameterNodeAtInstant._get_appropriate_keys(key)
        get_subnode_key = (
            VectorialParameterNodeAtInstant._get_appropriate_subnode_function(keys[0])
        )
        nodes = [node[get_subnode_key(node, key)] for key in keys]
        return VectorialParameterNodeAtInstant.build_from_nodes(node, nodes)

    @staticmethod
    def build_from_nodes(node, nodes):
        if isinstance(nodes[0], parameters.ParameterNodeAtInstant):
            return VectorialParameterNodeAtInstant(nodes, node._name, node._instant_str)
        return numpy.array(nodes)

    def __getattr__(self, attribute):
        return self[attribute]

    def __getitem__(self, key):
        if isinstance(key, str):
            keys = [key for v in self.vector]
        elif isinstance(key[0], Enum):
            keys = [k.name for k in key]
        elif isinstance(key, EnumArray):
            keys = [key.possible_values.names[v] for v in key]
        else:
            keys = key

        nodes = [v[a] for (v, a) in zip(self.vector, keys)]
        return VectorialParameterNodeAtInstant.build_from_nodes(self, nodes)

    @staticmethod
    def check_node_vectorisable(node) -> None:
        """Check that a node can be casted to a vectorial node, in order to be able to use fancy indexing."""
        MESSAGE_PART_1 = "Cannot use fancy indexing on parameter node '{}', as"
        MESSAGE_PART_3 = (
            "To use fancy indexing on parameter node, its children must be homogeneous."
        )
        MESSAGE_PART_4 = "See more at <https://openfisca.org/doc/coding-the-legislation/legislation_parameters#computing-a-parameter-that-depends-on-a-variable-fancy-indexing>."

        def raise_key_inhomogeneity_error(
            node_with_key, node_without_key, missing_key
        ) -> NoReturn:
            message = f"{MESSAGE_PART_1} '{{}}' exists, but '{{}}' doesn't. {MESSAGE_PART_3} {MESSAGE_PART_4}".format(
                node._name,
                f"{node_with_key}.{missing_key}",
                f"{node_without_key}.{missing_key}",
            )

            raise ValueError(message)

        def raise_type_inhomogeneity_error(node_name, non_node_name) -> NoReturn:
            message = f"{MESSAGE_PART_1} '{{}}' is a node, but '{{}}' is not. {MESSAGE_PART_3} {MESSAGE_PART_4}".format(
                node._name,
                node_name,
                non_node_name,
            )

            raise ValueError(message)

        def raise_not_implemented(node_name, node_type) -> NoReturn:
            message = f"{MESSAGE_PART_1} '{{}}' is a '{{}}', and fancy indexing has not been implemented yet on this kind of parameters. {MESSAGE_PART_4}".format(
                node._name,
                node_name,
                node_type,
            )
            raise NotImplementedError(message)

        def extract_named_children(node):
            return {
                f"{node._name}.{key}": value for key, value in node._children.items()
            }

        def check_nodes_homogeneous(named_nodes) -> None:
            """Check than several nodes (or parameters, or baremes) have the same structure."""
            names = list(named_nodes.keys())
            nodes = list(named_nodes.values())
            first_node = nodes[0]
            first_name = names[0]
            if isinstance(first_node, parameters.ParameterNodeAtInstant):
                children = extract_named_children(first_node)
                for node, name in list(zip(nodes, names))[1:]:
                    if not isinstance(node, parameters.ParameterNodeAtInstant):
                        raise_type_inhomogeneity_error(first_name, name)
                    first_node_keys = first_node._children.keys()
                    node_keys = node._children.keys()
                    if first_node_keys != node_keys:
                        missing_keys = set(first_node_keys).difference(node_keys)
                        if missing_keys:  # If the first_node has a key that node hasn't
                            raise_key_inhomogeneity_error(
                                first_name,
                                name,
                                missing_keys.pop(),
                            )
                        else:  # If If the node has a key that first_node doesn't have
                            missing_key = (
                                set(node_keys).difference(first_node_keys).pop()
                            )
                            raise_key_inhomogeneity_error(name, first_name, missing_key)
                    children.update(extract_named_children(node))
                check_nodes_homogeneous(children)
            elif isinstance(first_node, (float, int, str)):
                for node, name in list(zip(nodes, names))[1:]:
                    if isinstance(node, (int, float, str)):
                        pass
                    elif isinstance(node, parameters.ParameterNodeAtInstant):
                        raise_type_inhomogeneity_error(name, first_name)
                    else:
                        raise_not_implemented(name, type(node).__name__)
            else:
                raise_not_implemented(first_name, type(first_node).__name__)

        check_nodes_homogeneous(extract_named_children(node))
