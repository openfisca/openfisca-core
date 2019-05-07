# -*- coding: utf-8 -*-

from __future__ import annotations

import abc
import typing
from typing import Optional

import numpy as np

if typing.TYPE_CHECKING:
    from openfisca_core.populations import GroupPopulation, Population


class Projector(abc.ABC):
    reference_population: Population
    parent: Optional[Projector]

    def __getattr__(self, attribute):
        projector = self.get_projector(attribute)
        if projector:
            return projector

        reference_attr = getattr(self.reference_population, attribute)
        if not hasattr(reference_attr, 'projectable'):
            return reference_attr

        def projector_function(*args, **kwargs):
            result = reference_attr(*args, **kwargs)
            return self.transform_and_bubble_up(result)

        return projector_function

    def __call__(self, *args, **kwargs):
        result = self.reference_population(*args, **kwargs)
        return self.transform_and_bubble_up(result)

    def transform_and_bubble_up(self, result):
        transformed_result = self.transform(result)
        if self.parent is None:
            return transformed_result
        else:
            return self.parent.transform_and_bubble_up(transformed_result)

    @abc.abstractmethod
    def transform(self, result):
        pass

    def get_projector(self, attribute: str):
        projector = self.reference_population.get_projector(attribute)
        if not projector:
            return
        projector.parent = self
        return projector

    @property
    def ids(self):
        return self.transform_and_bubble_up(self.reference_population.ids)


# For instance person.family
class EntityToPersonProjector(Projector):

    def __init__(self, group_population, parent = None):
        self.reference_population = group_population
        self.parent = parent

    def transform(self, result):
        return self.reference_population.project(result)


# For instance famille.first_person
class FirstPersonToEntityProjector(Projector):

    def __init__(self, group_population, parent = None):
        self.target_population = group_population
        self.reference_population = group_population.members
        self.parent = parent

    def transform(self, result):
        return self.target_population.value_from_first_person(result)


# For instance famille.declarant_principal
class UniqueRoleToEntityProjector(Projector):

    def __init__(self, group_population, role, parent = None):
        self.target_population = group_population
        self.reference_population = group_population.members
        self.parent = parent
        self.role = role

    def transform(self, result):
        return self.target_population.value_from_person(result, self.role)


# For instance person.family, where person is a sub-population
class EntityToSubPopulationProjector(Projector):

    def __init__(self, group_population: GroupPopulation, condition: np.ndarray[bool], parent: Projector = None):
        self.reference_population = group_population.get_subpopulation(
            group_population.any(condition)
            )  # we'll run calculations only on a sub-population of the groups
        self.parent = parent
        self.condition = condition

    def transform(self, result):
        result = self.reference_population.project(result)  # projected on all members of the group subpopulation, but that's more than what we need
        relative_condition = self.condition[self.reference_population.members_condition]  # condition to find the original subpopulation within the group sup-population members

        return result[relative_condition]
