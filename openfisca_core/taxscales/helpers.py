from __future__ import annotations

import typing

import logging

from openfisca_core import taxscales

log = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from openfisca_core.parameters import ParameterNodeAtInstant

    TaxScales = typing.Optional[taxscales.MarginalRateTaxScale]


def combine_tax_scales(
    node: ParameterNodeAtInstant,
    combined_tax_scales: TaxScales = None,
) -> TaxScales:
    """Combine all the MarginalRateTaxScales in the node into a single
    MarginalRateTaxScale.
    """
    name = next(iter(node or []), None)

    if name is None:
        return combined_tax_scales

    if combined_tax_scales is None:
        combined_tax_scales = taxscales.MarginalRateTaxScale(name=name)
        combined_tax_scales.add_bracket(0, 0)

    for child_name in node:
        child = node[child_name]

        if isinstance(child, taxscales.MarginalRateTaxScale):
            combined_tax_scales.add_tax_scale(child)

        else:
            log.info(
                f"Skipping {child_name} with value {child} "
                "because it is not a marginal rate tax scale",
            )

    return combined_tax_scales
