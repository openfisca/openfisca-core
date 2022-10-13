from policyengine_core.parameters.parameter import Parameter
from policyengine_core.parameters.parameter_node import ParameterNode


def get_parameter(root: ParameterNode, parameter: str) -> Parameter:
    """Gets a parameter from the tree by name.

    Args:
        root (ParameterNode): The root of the parameter tree.
        parameter (str): The name of the parameter to get.

    Returns:
        Parameter: The parameter.
    """
    node = root
    for name in parameter.split("."):
        try:
            if "[" not in name:
                node = node.children[name]
            else:
                try:
                    name, index = name.split("[")
                    index = int(index[:-1])
                    node = node.children[name].brackets[index]
                except:
                    raise ValueError(
                        "Invalid bracket syntax (should be e.g. tax.brackets[3].rate"
                    )
        except:
            raise ValueError(
                f"Could not find the parameter (failed at {name})."
            )
    return node
