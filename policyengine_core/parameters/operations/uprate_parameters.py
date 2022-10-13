from policyengine_core.parameters.parameter import Parameter
from policyengine_core.parameters.parameter_node import ParameterNode
from policyengine_core.parameters.parameter_scale import ParameterScale
from policyengine_core.parameters.parameter_at_instant import (
    ParameterAtInstant,
)
from policyengine_core.periods import instant, period
from numpy import ceil, floor
from policyengine_core.parameters.operations.get_parameter import get_parameter


def uprate_parameters(root: ParameterNode) -> ParameterNode:
    """Uprates parameters according to their metadata.

    Args:
        root (ParameterNode): The root of the parameter tree.

    Returns:
        ParameterNode: The same root, with uprating applied to descendants.
    """

    descendants = list(root.get_descendants())

    scales = list(filter(lambda p: isinstance(p, ParameterScale), descendants))
    for scale in scales:
        for bracket in scale.brackets:
            for allowed_key in bracket._allowed_keys:
                if hasattr(bracket, allowed_key):
                    descendants.append(getattr(bracket, allowed_key))

    for parameter in descendants:
        if isinstance(parameter, Parameter):
            if parameter.metadata.get("uprating", None) is not None:
                meta = parameter.metadata["uprating"]
                if meta == "self":
                    meta = dict(parameter="self")
                elif isinstance(meta, str):
                    meta = dict(parameter=meta)
                if meta["parameter"] == "self":
                    last_instant = instant(
                        parameter.values_list[0].instant_str
                    )
                    start_instant = instant(
                        meta.get(
                            "from",
                            last_instant.offset(
                                -1, meta.get("interval", "year")
                            ),
                        )
                    )
                    start = parameter(start_instant)
                    end_instant = instant(meta.get("to", last_instant))
                    end = parameter(end_instant)
                    increase = end / start
                    if "from" in meta:
                        # This won't work for non-year periods, which are more complicated
                        increase / (end_instant.year - start_instant.year)
                    data = {}
                    value = parameter.values_list[0].value
                    for i in range(meta.get("number", 10)):
                        data[
                            str(
                                last_instant.offset(
                                    i, meta.get("interval", "year")
                                )
                            )
                        ] = (value * increase)
                        value *= increase
                    uprating_parameter = Parameter("self", data=data)
                else:
                    uprating_parameter = get_parameter(root, meta["parameter"])
                # Start from the latest value
                if "start_instant" in meta:
                    last_instant = instant(meta["start_instant"])
                else:
                    last_instant = instant(
                        parameter.values_list[0].instant_str
                    )
                # For each defined instant in the uprating parameter
                for entry in uprating_parameter.values_list[::-1]:
                    entry_instant = instant(entry.instant_str)
                    # If the uprater instant is defined after the last parameter instant
                    if entry_instant > last_instant:
                        # Apply the uprater and add to the parameter
                        value_at_start = parameter(last_instant)
                        uprater_at_start = uprating_parameter(last_instant)
                        uprater_at_entry = uprating_parameter(entry_instant)
                        uprater_change = uprater_at_entry / uprater_at_start
                        uprated_value = value_at_start * uprater_change
                        if "rounding" in meta:
                            rounding_config = meta["rounding"]
                            if isinstance(rounding_config, float):
                                interval = rounding_config
                                rounding_fn = round
                            elif isinstance(rounding_config, dict):
                                interval = rounding_config["interval"]
                                rounding_fn = dict(
                                    nearest=round,
                                    upwards=ceil,
                                    downwards=floor,
                                )[rounding_config["type"]]
                            uprated_value = (
                                rounding_fn(uprated_value / interval)
                                * interval
                            )
                        parameter.values_list.append(
                            ParameterAtInstant(
                                parameter.name,
                                entry.instant_str,
                                data=uprated_value,
                            )
                        )
                parameter.values_list.sort(
                    key=lambda x: x.instant_str, reverse=True
                )
    return root
