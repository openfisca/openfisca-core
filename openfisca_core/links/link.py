"""Base Link class for entity relationships."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy


class Link:
    """A named, directed relationship between two entity populations.

    A Link is defined by:
    - A *name* used to access the link from formulas (e.g. "mother", "household").
    - A *link_field*: the name of the Variable (on the source entity) that holds
      the target entity IDs.
    - A *target_entity_key*: the entity key of the target population.
    - Optionally, a *role_field* and *position_field* to attach OpenFisca-style
      role and position metadata to the relationship.

    Sub-classes ``Many2OneLink`` and ``One2ManyLink`` add resolution logic.

    Parameters
    ----------
    name : str
        Human-readable name of the link (e.g. ``"mother"``).
    link_field : str
        Variable name on the **source** entity that holds IDs pointing to
        the target entity.
    target_entity_key : str
        The ``Entity.key`` of the target entity.
    role_field : str or None
        Optional variable name holding the role of each source member
        within the target group.
    position_field : str or None
        Optional variable name holding the positional index of each
        source member within the target group.
    """

    def __init__(
        self,
        name: str,
        link_field: str,
        target_entity_key: str,
        *,
        role_field: str | None = None,
        position_field: str | None = None,
    ) -> None:
        self.name = name
        self.link_field = link_field
        self.target_entity_key = target_entity_key
        self.role_field = role_field
        self.position_field = position_field

        # Resolved after simulation setup
        self._source_population = None
        self._target_population = None

    # -- lifecycle ----------------------------------------------------------

    def attach(self, source_population) -> None:
        """Bind this link to its source population."""
        self._source_population = source_population

    def resolve(self, populations: dict) -> None:
        """Resolve ``target_entity_key`` to an actual population object.

        Parameters
        ----------
        populations : dict[str, Population]
            All populations in the simulation, keyed by entity key.
        """
        if self.target_entity_key not in populations:
            msg = (
                f"Link '{self.name}': target entity "
                f"'{self.target_entity_key}' not found in populations "
                f"{list(populations.keys())}"
            )
            raise KeyError(msg)
        self._target_population = populations[self.target_entity_key]

    # -- helpers ------------------------------------------------------------

    @property
    def is_resolved(self) -> bool:
        return (
            self._source_population is not None and self._target_population is not None
        )

    def _get_link_ids(self, period) -> numpy.ndarray:
        """Return the array of target IDs for every source member.

        This reads the ``link_field`` variable from the source population.
        """
        return self._source_population(self.link_field, period)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"link_field={self.link_field!r}, "
            f"target={self.target_entity_key!r})"
        )


__all__ = ["Link"]
