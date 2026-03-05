"""Many-to-one link: N source members → 1 target entity."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy

from .link import Link

if TYPE_CHECKING:
    pass


def _calculate_with_options(simulation, variable_name, period, options):
    """Dispatch to calculate / calculate_add / calculate_divide like CorePopulation."""
    from openfisca_core.populations import types as t
    from openfisca_core.populations._errors import (
        IncompatibleOptionsError,
        InvalidOptionError,
    )

    if options is None or not isinstance(options, Sequence):
        return simulation.calculate(variable_name, period)
    if t.Option.ADD in options and t.Option.DIVIDE in options:
        raise IncompatibleOptionsError(variable_name)
    if t.Option.ADD in options:
        return simulation.calculate_add(variable_name, period)
    if t.Option.DIVIDE in options:
        return simulation.calculate_divide(variable_name, period)
    raise InvalidOptionError(options[0], variable_name)


class Many2OneLink(Link):
    """Navigate from many source members to one target entity.

    Example: ``person.household`` (each person belongs to one household),
    or ``person.mother`` (each person has one mother).

    The resolution follows the LIAM2 pattern::

        target_ids = source_pop(link_field)     # e.g. [0, 0, 1, 2, 0]
        target_values = target_pop(variable)    # e.g. [800, 650, 900]
        result = target_values[target_ids]      # e.g. [800, 800, 650, 900, 800]
    """

    def get(
        self,
        variable_name: str,
        period,
        options: None | Sequence = None,
    ) -> numpy.ndarray:
        """Get a target variable's value for each source member.

        Parameters
        ----------
        variable_name : str
            Name of the variable defined on the target entity.
        period : Period
            The period for which to compute the variable.
        options : sequence, optional
            Options for the calculation (e.g. ADD, DIVIDE).

        Returns
        -------
        numpy.ndarray
            Array of shape ``(n_source,)`` containing the target variable
            value for each source member.  Members with an invalid link
            (target_id < 0) receive the variable's default value.
        """
        source_pop = self._source_population
        simulation = source_pop.simulation

        # 1. Target IDs for each source member
        target_ids = self._get_target_ids(period)

        # 2. Variable values on the target entity
        target_values = _calculate_with_options(
            simulation, variable_name, period, options
        )

        # 3. Resolve IDs to row positions (handles id_to_rownum if needed)
        target_rows = self._resolve_ids(target_ids)

        # 4. Gather with missing-value handling
        variable = simulation.tax_benefit_system.get_variable(variable_name)
        default = variable.default_value if variable else 0

        from openfisca_core.indexed_enums import Enum, EnumArray

        if isinstance(default, Enum):
            default = default.index

        result = numpy.full(
            source_pop.count,
            default,
            dtype=target_values.dtype,
        )
        valid = target_rows >= 0
        result[valid] = target_values[target_rows[valid]]

        if isinstance(target_values, EnumArray):
            result = EnumArray(result, target_values.possible_values)

        return result

    # -- syntactic sugar ----------------------------------------------------

    def __call__(
        self,
        variable_name: str,
        period,
        *,
        options=None,
        **kwargs,
    ) -> numpy.ndarray:
        """Shorthand: ``person.mother("age", period)`` or with options."""
        return self.get(variable_name, period, options=options)

    def __getattr__(self, name: str):
        """Chain links: ``person.mother.household``."""
        if name.startswith("_"):
            raise AttributeError(name)

        target_pop = self._target_population
        if target_pop is None:
            raise AttributeError("Link is not bound to a simulation")

        if hasattr(target_pop, "links") and name in target_pop.links:
            target_link = target_pop.links[name]
            return _ChainedGetter(self, target_link)

        target_attr = getattr(target_pop, name, None)
        if target_attr is not None:
            if hasattr(target_attr, "projectable"):

                def projector_function(*args, **kwargs):
                    result = target_attr(*args, **kwargs)
                    return self._project_result(result)

                return projector_function
            return target_attr

        target_entity = target_pop.entity
        msg = f"Entity '{target_entity.key}' has no link named '{name}'"
        raise AttributeError(msg)

    def _project_result(self, result: numpy.ndarray) -> numpy.ndarray:
        if hasattr(self, "_project_implicit"):
            return self._project_implicit(result)
        msg = "Chained method calls computing arrays on explicit links are not supported because the period cannot be inferred."
        raise NotImplementedError(msg)

    # -- role helpers -------------------------------------------------------

    @property
    def role(self) -> numpy.ndarray | None:
        """Role of each source member, if ``role_field`` is set."""
        if self.role_field is None:
            return None
        return self._source_population.simulation.calculate(
            self.role_field,
            "eternity",
        )

    def has_role(self, role_value) -> numpy.ndarray:
        """Boolean mask: does each source member have the given role?

        The ``role`` array may contain raw values (ints, strings) or
        ``Role`` objects depending on how the population was built.  When
        ``role_value`` is a string we compare against the ``key`` of each
        element to make the API ergonomic for callers such as
        ``link.has_role("parent")`` or ``link.get_by_role(..., role_value="foo")``.
        """
        r = self.role
        if r is None:
            msg = f"Link '{self.name}' has no role_field"
            raise ValueError(msg)

        # if array holds object references, convert to their keys
        if r.dtype == object:
            try:
                keys = numpy.fromiter(
                    (getattr(x, "key", x) for x in r),
                    dtype=object,
                )
            except Exception:
                # fallback to direct comparison
                return r == role_value
            return keys == role_value

        # numpy will perform elementwise comparison for numeric or string
        return r == role_value

    # -- role-based access --------------------------------------------------

    def get_by_role(
        self,
        variable_name: str,
        period,
        *,
        role_value,
    ) -> numpy.ndarray:
        """Fetch a variable on the target only for members with a given role.

        Parameters
        ----------
        variable_name : str
            Name of the variable defined on the target entity.
        period : Period
            Period for which to calculate the variable.
        role_value : object
            The role to filter on (e.g. ``"parent"``).

        Returns
        -------
        numpy.ndarray
            Array of shape ``(n_source,)`` where only members whose
            ``has_role(role_value)`` return ``True`` keep their computed
            value; all others receive the variable's default (usually 0).
        """
        mask = self.has_role(role_value)
        result = self.get(variable_name, period, options=None)
        # zero out non-matching rows using dtype-preserving fill
        if not mask.all():
            # create a copy to avoid mutating cached results
            result = result.copy()
            result[~mask] = 0
        return result

    # -- ID resolution ------------------------------------------------------

    def _get_target_ids(self, period) -> numpy.ndarray:
        """Fetch the target IDs from the link_field variable."""
        return self._source_population.simulation.calculate(
            self.link_field,
            period,
        )

    def _resolve_ids(self, target_ids: numpy.ndarray) -> numpy.ndarray:
        """Convert target IDs to row indices.

        If the target population has an ``_id_to_rownum`` mapping
        (e.g. for intra-entity links where IDs ≠ row positions), use it.
        Otherwise treat IDs as direct row indices (the OpenFisca convention
        for GroupPopulation.members_entity_id).
        """
        target_pop = self._target_population
        rows = numpy.full_like(target_ids, -1, dtype=numpy.intp)

        if (
            hasattr(target_pop, "_id_to_rownum")
            and target_pop._id_to_rownum is not None
        ):
            id_to_rownum = target_pop._id_to_rownum
            valid = (target_ids >= 0) & (target_ids < len(id_to_rownum))
            rows[valid] = id_to_rownum[target_ids[valid]]
        else:
            valid = (target_ids >= 0) & (target_ids < target_pop.count)
            rows[valid] = target_ids[valid]

        return rows

    # -- ranking -----------------------------------------------------------

    def rank(self, variable_name: str, period) -> numpy.ndarray:
        """Rank each source member within its group by a variable value.

        The rank is computed among all members sharing the same target
        entity, sorted by the value of ``variable_name`` evaluated on the
        *source* population.  The lowest value receives rank ``0``.

        This is essentially a thin wrapper around
        :meth:`~openfisca_core.populations.Population.get_rank`:

        >>> person = simulation.persons
        >>> person.links['household'].rank('age', period)
        array([...])
        """
        source_pop = self._source_population
        # criteria on source population
        criteria = source_pop.simulation.calculate(variable_name, period)
        # let Population.get_rank handle grouping and sorting
        return source_pop.get_rank(self, criteria)


# ---------------------------------------------------------------------------
# Chained link getter
# ---------------------------------------------------------------------------


class _ChainedGetter:
    """Intermediate object for link chaining: ``person.mother.household``."""

    def __init__(self, outer_link: Many2OneLink, inner_link: Link) -> None:
        self._outer = outer_link
        self._inner = inner_link

    def get(
        self,
        variable_name: str,
        period,
        options=None,
    ) -> numpy.ndarray:
        """Resolve ``person.mother.household.get("rent", period)``."""
        # 1. Resolve inner link value on inner entity
        inner_values = self._inner.get(variable_name, period, options=options)

        # 2. Map back through outer link
        target_ids = self._outer._source_population.simulation.calculate(
            self._outer.link_field,
            period,
        )
        target_rows = self._outer._resolve_ids(target_ids)

        result = numpy.full(
            self._outer._source_population.count,
            0,
            dtype=inner_values.dtype,
        )
        valid = target_rows >= 0
        result[valid] = inner_values[target_rows[valid]]
        return result

    def __call__(
        self,
        variable_name: str,
        period,
        *,
        options=None,
        **kwargs,
    ) -> numpy.ndarray:
        """Shorthand for get(): ``person.mother.household("rent", period)``."""
        return self.get(variable_name, period, options=options)

    def __getattr__(self, name: str):
        """Continue chaining: ``person.mother.household.region``."""
        if name.startswith("_"):
            raise AttributeError(name)

        target_pop = self._inner._target_population
        if target_pop is None:
            raise AttributeError("Link is not bound to a simulation")

        if hasattr(target_pop, "links") and name in target_pop.links:
            next_link = target_pop.links[name]
            return _ChainedGetter(self._outer, next_link)

        target_entity = target_pop.entity
        raise AttributeError(f"Entity '{target_entity.key}' has no link named '{name}'")

    def rank(self, variable_name: str, period) -> numpy.ndarray:
        # forward to outer link so that chaining keeps semantics
        return self._outer.rank(variable_name, period)


__all__ = ["Many2OneLink"]
