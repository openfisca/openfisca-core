from __future__ import annotations

from typing import Dict, Type

import collections

from openfisca_core import types

FilePath = str
PossibleValues = Type[types.Enum]


class Enums(collections.UserDict):
    """Dictionary of an Enum's possible values by file path.

    Examples:
        >>> from openfisca_core import indexed_enums as enums

        >>> class Enum(enums.Enum):
        ...     A = "a"
        ...     B = "b"

        >>> path = "path/to/file.py"
        >>> possible_values = tuple(Enum)

        >>> Enums({path: possible_values})
        {'path/to/file.py': (<Enum.A: 'a'>, <Enum.B: 'b'>)}

    .. versionadded:: 36.0.1

    """

    data: Dict[FilePath, PossibleValues]
