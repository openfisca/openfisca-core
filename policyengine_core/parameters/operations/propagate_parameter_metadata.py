from policyengine_core.parameters.parameter import Parameter
from policyengine_core.parameters.parameter_node import ParameterNode


def propagate_parameter_metadata(root: ParameterNode) -> ParameterNode:
    """Passes parameter metadata to descendents where this is specified.

    Breakdown metadata is ignored.

    Args:
        root (ParameterNode): The root node.

    Returns:
        ParameterNode: The edited parameter root.
    """

    UNPROPAGAGED_METADATA = ["breakdown"]

    for parameter in root.get_descendants():
        if parameter.metadata.get("propagate_metadata_to_children"):
            for descendant in parameter.get_descendants():
                descendant.metadata.update(
                    {
                        key: value
                        for key, value in parameter.metadata.items()
                        if key not in UNPROPAGAGED_METADATA
                    }
                )

    return root
