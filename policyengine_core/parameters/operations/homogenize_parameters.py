from policyengine_core.variables import Variable
from policyengine_core.enums import Enum
from typing import Any, Dict, List, Type
from policyengine_core.parameters.parameter import Parameter
from policyengine_core.parameters.parameter_node import ParameterNode
import logging


def homogenize_parameter_structures(
    root: ParameterNode, variables: Dict[str, Variable], default_value: Any = 0
) -> ParameterNode:
    """
    Homogenize the structure of a parameter tree to match the structure of the variables.

    Args:
        root (ParameterNode): The root of the parameter tree.
        variables (Dict[str, Variable]): The variables to match the structure to.
        default_value (Any, optional): The default value to use for missing parameters. Defaults to 0.

    Returns:
        ParameterNode: The root of the homogenized parameter tree.
    """
    for node in root.get_descendants():
        if isinstance(node, ParameterNode):
            breakdown = get_breakdown_variables(node)
            node = homogenize_parameter_node(
                node, breakdown, variables, default_value
            )
    return root


def get_breakdown_variables(node: ParameterNode) -> List[str]:
    """
    Returns the list of variables that are used to break down the parameter.
    """
    breakdown = node.metadata.get("breakdown")
    if breakdown is not None:
        if isinstance(breakdown, str):
            # Single element, cast to list.
            breakdown = [breakdown]
        if not isinstance(breakdown, list):
            # Not a list, skip process and warn.
            logging.warning(
                f"Invalid breakdown metadata for parameter {node.name}: {type(breakdown)}"
            )
            return None
        return breakdown
    else:
        return None


def homogenize_parameter_node(
    node: ParameterNode,
    breakdown: List[str],
    variables: Dict[str, Variable],
    default_value: Any,
) -> ParameterNode:
    if breakdown is None:
        return node
    first_breakdown = breakdown[0]
    if isinstance(first_breakdown, list):
        possible_values = first_breakdown
    elif first_breakdown in variables:
        dtype = variables[first_breakdown].value_type
        if dtype == Enum:
            possible_values = list(
                map(
                    lambda enum: enum.name,
                    variables[first_breakdown].possible_values,
                )
            )
        elif dtype == bool:
            possible_values = [True, False]
    else:
        # Try to execute the breakdown as Python code
        possible_values = list(eval(first_breakdown))
    if not hasattr(node, "children"):
        node = ParameterNode(
            node.name,
            data={
                child: {"2000-01-01": default_value}
                for child in possible_values
            },
        )
    missing_values = set(possible_values) - set(node.children)
    further_breakdown = len(breakdown) > 1
    for value in missing_values:
        if str(value) not in node.children:
            # Integers behave strangely, this fixes it.
            node.add_child(
                str(value),
                Parameter(
                    node.name + "." + str(value), {"2000-01-01": default_value}
                ),
            )
    for child in node.children:
        if child.split(".")[-1] not in possible_values:
            try:
                int(child)
                is_int = True
            except:
                is_int = False
            if not is_int or str(child) not in node.children:
                logging.warning(
                    f"Parameter {node.name} has a child {child} that is not in the possible values of {first_breakdown}, ignoring."
                )
        if further_breakdown:
            node.children[child] = homogenize_parameter_node(
                node.children[child], breakdown[1:], variables, default_value
            )
    return node
