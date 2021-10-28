from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence
from typing_extensions import TypedDict

from ._protocols import PeriodProtocol


class AxisSchema(TypedDict):
    """Data-schema of axes."""

    count: int
    index: int
    max: float
    min: float
    name: str
    period: str


class FrameSchema(TypedDict):
    """Data-schema of tracer stack frames."""

    name: str
    period: PeriodProtocol


class OptionsSchema(TypedDict, total = False):
    """Data-schema of ``openfisca test`` options."""

    ignore_variables: Optional[Sequence[str]]
    name_filter: Optional[str]
    only_variables: Optional[Sequence[str]]
    pdb: bool
    performance_graph: bool
    performance_tables: bool
    verbose: bool


class TestSchema(TypedDict, total = False):
    """Data-schema of ``openfisca test`` tests."""

    absolute_error_margin: float
    extensions: Sequence[str]
    input: Mapping[str, Mapping[str, Any]]
    keywords: Sequence[str]
    max_spiral_loops: int
    name: str
    output: Mapping[str, Mapping[str, Any]]
    period: str
    reforms: Sequence[str]
    relative_error_margin: float
