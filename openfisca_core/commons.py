# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


class Dummy(object):
    """A class that does nothing

    Used by function ``empty_clone`` to create an empty instance from an existing object.
    """
    pass


def empty_clone(original):
    """Create a new empty instance of the same class of the original object."""
    new = Dummy()
    new.__class__ = original.__class__
    return new


def stringify_array(array):
    """
        Generate a clean string representation of a NumPY array.
    """
    return '[{}]'.format(', '.join(
        str(cell)
        for cell in array
        )) if array is not None else 'None'


@dataclass(frozen = True)
class PartialArray:
    """
        Represents a value known for only a subset of a population.
        ``mask`` has the size of the super-population, and is ``True`` for the K individuals the value is known for.
        If ``mask`` is ``None``, the value is known for all individuals.
        ``value`` contains the K known values.
    """
    value: np.ndarray
    mask: Optional[np.ndarray[bool]] = None
