from typing import List, Union

from .reference import Reference


class VariableBreakdown(str):
    """
    The name of a variable with Enum type, whose possible values form the child nodes in a parameter node.
    """


class DynamicBreakdown(str):
    """
    A Python expression that evaluates to a list of child nodes in a parameter node.
    """


class ParameterNodeMetadata:
    """A collection of related parameters."""

    name: str
    """The name identifying this parameter node and its children (unless overridden). Should be snake-case and Python-safe."""

    label: str
    """The display text to use for the parameter node and its children (unless overridden). Should be short and less than a full sentence."""

    reference: List[Reference]
    """A list of references that apply to all descendants of this node."""

    breakdown: List[Union[VariableBreakdown, DynamicBreakdown]]
    """The sets defining the children, grandchildren and further descendants of this node.

    For example:

    .. code-block:: yaml

        metadata:
            breakdown:
                - region # If `region` is an Enum-type variable with possible values `[ENGLAND, WALES]` then these children will be added.
                - range(1, 7) # This code is `eval`uated to produce the list `[1, 2, 3, 4, 5, 6]` which are then added as grandchildren.
                - [True, False] # This list is added as great-grandchildren (using the same `eval` method as above).
    
    """

    propagate_metadata_to_children: bool
    """Whether to propagate metadata to children of this node. This excludes `breakdown`."""
