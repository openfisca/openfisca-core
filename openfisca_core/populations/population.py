from __future__ import annotations

from typing import Dict, NamedTuple, Optional, Sequence, Union
from typing_extensions import TypedDict

import traceback

import numpy

from openfisca_core import periods, projectors
from openfisca_core.holders import Holder
from openfisca_core.projectors import Projector
from openfisca_core.types import Array, Entity, Period, Role, Simulation

from . import config


class Population:

    simulation: Optional[Simulation]
    entity: Entity
    _holders: Dict[str, Holder]
    count: int
    ids: Array[str]

    def __init__(self, entity: Entity) -> None:
        self.simulation = None
        self.entity = entity
        self._holders = {}
        self.count = 0
        self.ids = []

    def clone(self, simulation: Simulation) -> Population:
        result = Population(self.entity)
        result.simulation = simulation
        result._holders = {variable: holder.clone(result) for (variable, holder) in self._holders.items()}
        result.count = self.count
        result.ids = self.ids
        return result

    def empty_array(self) -> Array[float]:
        return numpy.zeros(self.count)

    def filled_array(
            self,
            value: Union[float, bool],
            dtype: Optional[numpy.dtype] = None,
            ) -> Union[Array[float], Array[bool]]:
        return numpy.full(self.count, value, dtype)

    def __getattr__(self, attribute: str) -> Projector:
        projector: Optional[Projector]
        projector = projectors.get_projector_from_shortcut(self, attribute)

        if isinstance(projector, Projector):
            return projector

        raise AttributeError("You tried to use the '{}' of '{}' but that is not a known attribute.".format(attribute, self.entity.key))

    def get_index(self, id: str) -> int:
        return self.ids.index(id)

    # Calculations

    def check_array_compatible_with_entity(
            self,
            array: Array[float],
            ) -> None:
        if self.count == array.size:
            return None

        raise ValueError("Input {} is not a valid value for the entity {} (size = {} != {} = count)".format(
            array, self.entity.key, array.size, self.count))

    def check_period_validity(
            self,
            variable_name: str,
            period: Optional[Union[int, str, Period]],
            ) -> None:
        if isinstance(period, (int, str, Period)):
            return None

        stack = traceback.extract_stack()
        filename, line_number, function_name, line_of_code = stack[-3]
        raise ValueError('''
You requested computation of variable "{}", but you did not specify on which period in "{}:{}":
    {}
When you request the computation of a variable within a formula, you must always specify the period as the second parameter. The convention is to call this parameter "period". For example:
    computed_salary = person('salary', period).
See more information at <https://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-in-variable-definition>.
'''.format(variable_name, filename, line_number, line_of_code))

    def __call__(
            self,
            variable_name: str,
            period: Optional[Union[int, str, Period]] = None,
            options: Optional[Sequence[str]] = None,
            ) -> Optional[Array[float]]:
        """
            Calculate the variable ``variable_name`` for the entity and the period ``period``, using the variable formula if it exists.

            Example:

            >>> person('salary', '2017-04')
            >>> array([300.])

            :returns: A numpy array containing the result of the calculation
        """
        if self.simulation is None:
            return None

        calculate: Calculate = Calculate(
            variable = variable_name,
            period = periods.period(period),
            option = options,
            )

        self.entity.check_variable_defined_for_entity(calculate.variable)
        self.check_period_validity(calculate.variable, calculate.period)

        if not isinstance(calculate.option, Sequence):
            return self.simulation.calculate(
                calculate.variable,
                calculate.period,
                )

        if config.ADD in calculate.option:
            return self.simulation.calculate_add(
                calculate.variable,
                calculate.period,
                )

        if config.DIVIDE in calculate.option:
            return self.simulation.calculate_divide(
                calculate.variable,
                calculate.period,
                )

        raise ValueError('Options config.ADD and config.DIVIDE are incompatible (trying to compute variable {})'.format(variable_name).encode('utf-8'))

    # Helpers

    def get_holder(self, variable_name: str) -> Holder:
        self.entity.check_variable_defined_for_entity(variable_name)
        holder = self._holders.get(variable_name)
        if holder:
            return holder
        variable = self.entity.get_variable(variable_name)
        self._holders[variable_name] = holder = Holder(variable, self)
        return holder

    def get_memory_usage(
            self,
            variables: Optional[Sequence[str]] = None,
            ) -> MemoryUsageByVariable:
        holders_memory_usage = {
            variable_name: holder.get_memory_usage()
            for variable_name, holder in self._holders.items()
            if variables is None or variable_name in variables
            }

        total_memory_usage = sum(
            holder_memory_usage['total_nb_bytes'] for holder_memory_usage in holders_memory_usage.values()
            )

        return MemoryUsageByVariable({
            "total_nb_bytes": total_memory_usage,
            "by_variable": holders_memory_usage,
            })

    @projectors.projectable
    def has_role(self, role: Role) -> Optional[Array[bool]]:
        """
            Check if a person has a given role within its `GroupEntity`

            Example:

            >>> person.has_role(Household.CHILD)
            >>> array([False])
        """

        if self.simulation is None:
            return None

        self.entity.check_role_validity(role)

        group_population = self.simulation.get_population(role.entity.plural)

        if role.subroles:
            return numpy.logical_or.reduce([group_population.members_role == subrole for subrole in role.subroles])

        else:
            return group_population.members_role == role

    @projectors.projectable
    def value_from_partner(
            self,
            array: Array[float],
            entity: Projector,
            role: Role,
            ) -> Optional[Array[float]]:
        self.check_array_compatible_with_entity(array)
        self.entity.check_role_validity(role)

        if not role.subroles or not len(role.subroles) == 2:
            raise Exception('Projection to partner is only implemented for roles having exactly two subroles.')

        [subrole_1, subrole_2] = role.subroles
        value_subrole_1 = entity.value_from_person(array, subrole_1)
        value_subrole_2 = entity.value_from_person(array, subrole_2)

        return numpy.select(
            [self.has_role(subrole_1), self.has_role(subrole_2)],
            [value_subrole_2, value_subrole_1],
            )

    @projectors.projectable
    def get_rank(
            self,
            entity: Population,
            criteria: Array[float],
            condition: bool = True,
            ) -> Array[int]:
        """
        Get the rank of a person within an entity according to a criteria.
        The person with rank 0 has the minimum value of criteria.
        If condition is specified, then the persons who don't respect it are not taken into account and their rank is -1.

        Example:

        >>> age = person('age', period)  # e.g [32, 34, 2, 8, 1]
        >>> person.get_rank(household, age)
        >>> [3, 4, 0, 2, 1]

        >>> is_child = person.has_role(Household.CHILD)  # [False, False, True, True, True]
        >>> person.get_rank(household, - age, condition = is_child)  # Sort in reverse order so that the eldest child gets the rank 0.
        >>> [-1, -1, 1, 0, 2]
        """

        # If entity is for instance 'person.household', we get the reference entity 'household' behind the projector
        entity = entity if not isinstance(entity, Projector) else entity.reference_entity

        positions = entity.members_position
        biggest_entity_size = numpy.max(positions) + 1
        filtered_criteria = numpy.where(condition, criteria, numpy.inf)
        ids = entity.members_entity_id

        # Matrix: the value in line i and column j is the value of criteria for the jth person of the ith entity
        matrix = numpy.asarray([
            entity.value_nth_person(k, filtered_criteria, default = numpy.inf)
            for k in range(biggest_entity_size)
            ]).transpose()

        # We double-argsort all lines of the matrix.
        # Double-argsorting gets the rank of each value once sorted
        # For instance, if x = [3,1,6,4,0], y =  numpy.argsort(x) is [4, 1, 0, 3, 2] (because the value with index 4 is the smallest one, the value with index 1 the second smallest, etc.) and z =  numpy.argsort(y) is [2, 1, 4, 3, 0], the rank of each value.
        sorted_matrix = numpy.argsort(numpy.argsort(matrix))

        # Build the result vector by taking for each person the value in the right line (corresponding to its household id) and the right column (corresponding to its position)
        result = sorted_matrix[ids, positions]

        # Return -1 for the persons who don't respect the condition
        return numpy.where(condition, result, -1)


class Calculate(NamedTuple):
    variable: str
    period: Period
    option: Optional[Sequence[str]]


class MemoryUsageByVariable(TypedDict, total = False):
    by_variable: Dict[str, MemoryUsage]
    total_nb_bytes: int


class MemoryUsage(TypedDict, total = False):
    cell_size: int
    dtype: numpy.dtype
    nb_arrays: int
    nb_cells_by_array: int
    total_nb_bytes: int
