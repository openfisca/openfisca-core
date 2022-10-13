

from typing import List

from .reference import Reference


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
