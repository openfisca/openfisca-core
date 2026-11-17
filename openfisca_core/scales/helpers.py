from __future__ import annotations

import logging
import typing

from openfisca_core import scales

log = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from openfisca_core.parameters import ParameterNodeAtInstant

    Scales = scales.MarginalRateScale | None


def combine_scales(
    node: ParameterNodeAtInstant,
    combined_scales: Scales = None,
) -> Scales:
    """Combine all the MarginalRateScales in the node into a single
    MarginalRateScale.
    """
    name = next(iter(node or []), None)

    if name is None:
        return combined_scales

    if combined_scales is None:
        combined_scales = scales.MarginalRateScale(name=name)
        combined_scales.add_bracket(0, 0)

    for child_name in node:
        child = node[child_name]

        if isinstance(child, scales.MarginalRateScale):
            combined_scales.add_scale(child)

        else:
            log.info(
                f"Skipping {child_name} with value {child} "
                "because it is not a marginal rate scale",
            )

    return combined_scales
