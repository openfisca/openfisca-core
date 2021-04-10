import collections.abc

from .axis import Axis


class AxisArray(collections.abc.Container):
    """
    Simply a collection of :class:`Axis`.

    Axis expansion is a feature in :module:`openfisca_core` that allows us to
    parametrise some dimensions in order to create and to evaluate a range of
    values for others.

    The most typical use of axis expansion is evaluate different numerical
    values, starting from a :attr:`min_` and up to a :attr:`max_`, that could
    take any given :class:`openfisca_core.variables.Variable` for any given
    :class:`openfisca_core.periods.Period` for any given population (or a
    collection of :module:`openfisca_core.entities`).

    .. versionadded:: 3.4.0
    """

    def __contains__(self, axis: Axis) -> bool:
        pass
