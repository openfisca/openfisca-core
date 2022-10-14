from policyengine_core.parameters.parameter import Parameter
from policyengine_core.parameters.parameter_node import ParameterNode
from policyengine_core.parameters.parameter_at_instant import (
    ParameterAtInstant,
)
from policyengine_core.periods import instant


def interpolate_parameters(root: ParameterNode) -> ParameterNode:
    """Interpolates parameters according to their metadata.

    Args:
        root (ParameterNode): The root of the parameter tree.

    Returns:
        ParameterNode: The same root, with interpolation applied to descendants.
    """
    for parameter in root.get_descendants():
        if isinstance(parameter, Parameter):
            if (
                "interpolation" in parameter.metadata
                and not parameter.metadata["interpolation"].get(
                    "completed", False
                )
            ):
                interpolated_entries = []
                for i in range(len(parameter.values_list) - 1):
                    # For each gap in parameter values
                    start = instant(parameter.values_list[::-1][i].instant_str)
                    num_intervals = 1
                    # Find the number of intervals to fill
                    interval_size = parameter.metadata["interpolation"][
                        "interval"
                    ]
                    parameter_dates = [
                        at_instant.instant_str
                        for at_instant in parameter.values_list
                    ]
                    while (
                        str(start.offset(num_intervals, interval_size))
                        < parameter_dates[0]
                    ):
                        num_intervals += 1
                    # Interpolate in each interval
                    for j in range(1, num_intervals):
                        start_str = str(
                            start.offset(
                                j,
                                parameter.metadata["interpolation"][
                                    "interval"
                                ],
                            )
                        )
                        start_value = parameter.values_list[::-1][i].value
                        end_value = parameter.values_list[::-1][i + 1].value
                        new_value = (
                            start_value
                            + (end_value - start_value) * j / num_intervals
                        )
                        interpolated_entries += [
                            ParameterAtInstant(
                                parameter.name, start_str, data=new_value
                            )
                        ]
                for entry in interpolated_entries:
                    parameter.values_list.append(entry)
                parameter.values_list.sort(
                    key=lambda x: x.instant_str, reverse=True
                )
                parameter.metadata["interpolation"]["completed"] = True
    return root
