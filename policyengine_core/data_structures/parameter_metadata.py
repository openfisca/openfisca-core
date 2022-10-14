from typing import List, Union

from .reference import Reference


class UpratingIndex(str):
    """
    The name of a parameter whose values are used to uprate a parameter node.
    """


class SelfUprating(UpratingIndex):
    """
    A special value ("self") that indicates that the parameter node should be uprated based on the fixed rate increase between two points in its history.
    """


class UpratingRoundingConfig(dict):
    type: str
    """Either 'nearest', 'upwards' or 'downwards'."""

    interval: float
    """The interval to round to."""


class UpratingSchema(dict):
    """
    A schema for uprating a parameter node.
    """

    parameter: UpratingIndex
    """
    The name of the parameter whose values are used to uprate the parameter node.
    """

    start_instant: int
    """
    The instant to add uprated values after.
    """

    type: UpratingRoundingConfig
    """
    The rounding configuration to use when uprating.
    """


class ParameterMetadata:
    """A single legislative value that can change over time."""

    name: str
    """The name identifying this parameter. Should be snake-case and Python-safe."""

    label: str
    """The display text to use for the parameter. Should be short and less than a full sentence."""

    description: str
    """A longer description of the parameter."""

    documentation: str
    """Any relevant information about the parameter's *implementation* (not its legislative meaning- use the description for that field)."""

    reference: List[Reference]
    """A list of references to legislation or other documents that define this parameter."""

    unit: str
    """The real-world meaning of a particular value."""

    uprating: Union[UpratingIndex, UpratingSchema]
    """The schema for uprating this parameter.

    The process for uprating parameter $X$ based on parameter $Y$ is as follows:
    
    1. Look at $X$ and $Y$ at the same time, and move forward in history.

    2. If $Y$ increases by $z$%, then increase $X$ by $z$%.
    """
