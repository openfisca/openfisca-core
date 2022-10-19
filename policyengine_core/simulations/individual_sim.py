"""
IndividualSim and any other interfaces to intialising and running simulations on hypothetical situations. Deprecated.
"""
from functools import partial
from typing import Dict, List

import numpy as np

from policyengine_core.entities.entity import Entity
from policyengine_core.periods import period
from policyengine_core.reforms import Reform, set_parameter
from policyengine_core.simulations import SimulationBuilder
from policyengine_core.taxbenefitsystems.tax_benefit_system import (
    TaxBenefitSystem,
)


class IndividualSim:
    """The IndividualSim class creates a simulation of tax-benefit policy
    on individually-specified entities.
    """

    tax_benefit_system: TaxBenefitSystem

    def __init__(
        self,
        reform: Reform = (),
        year: int = 2022,
        tax_benefit_system: TaxBenefitSystem = None,
    ) -> None:
        """Initialises a hypothetical simulation.

        Args:
            reform (ReformType, optional): The reform to apply. Defaults to ().
            year (int, optional): The default year input. Defaults to 2022.
        """
        self.year = year
        self.reform = reform
        self.system = tax_benefit_system or self.tax_benefit_system()
        self.sim_builder = SimulationBuilder()
        self.parametric_vary = False
        self.entities = {var.key: var for var in self.system.entities}
        self.situation_data = {
            entity.plural: {} for entity in self.system.entities
        }
        self.varying = False
        self.num_points = None
        self.group_entity_names = [
            entity.key
            for entity in self.system.entities
            if not entity.is_person
        ]

        # Add add_entity functions

        for entity in self.entities:
            setattr(
                self, f"add_{entity}", partial(self.add_data, entity=entity)
            )

    def build(self):
        if self.required_entities is not None:
            # Check for missing entities
            entities = {entity.key: entity for entity in self.system.entities}
            person_entity = list(
                filter(lambda x: x.is_person, entities.values())
            )[0]
            for entity in self.required_entities:
                entity_metadata = entities[entity]
                roles = {role.key: role for role in entities[entity].roles}
                default_role = roles[self.default_roles[entity]]
                no_entity_plural = (
                    entity_metadata.plural not in self.situation_data
                )
                if (
                    no_entity_plural
                    or len(self.situation_data[entity_metadata.plural]) == 0
                ):
                    self.situation_data[entity_metadata.plural] = {entity: {}}
                    members = []
                    for person in self.situation_data[person_entity.plural]:
                        members += [person]
                    self.situation_data[entity_metadata.plural][entity][
                        default_role.plural
                    ] = members
            # Add missing entities with specified default roles
        self.simulation = self.sim_builder.build_from_entities(
            self.system, self.situation_data
        )
        self.simulation.trace = True
        self.sim = self.simulation

    def add_data(
        self,
        entity: str = None,
        name: str = None,
        input_period: str = None,
        auto_period: str = True,
        **kwargs: dict,
    ) -> None:
        """Add an entity to the situation data.

        Args:
            entity (str, optional): The entity name. Defaults to "person".
            name (str, optional): The name of the entity instance. Defaults to None.
            input_period (str, optional): The input period for the values. Defaults to None.
            auto_period (str, optional): Whether to automatically repeat inputs onto subperiods. Defaults to True.
            kwargs (dict): A dictionary of (variable, value).
        """
        input_period = input_period or self.year
        entity_plural = self.entities[entity].plural
        if name is None:
            name = (
                entity + "_" + str(len(self.situation_data[entity_plural]) + 1)
            )
        if auto_period:
            data = {}
            for var, value in kwargs.items():
                try:
                    def_period = self.system.get_variable(
                        var
                    ).definition_period
                    if def_period in ["eternity", "year"]:
                        input_periods = [input_period]
                    else:
                        input_periods = period(input_period).get_subperiods(
                            def_period
                        )
                    data[var] = {
                        str(subperiod): value for subperiod in input_periods
                    }
                except:
                    data[var] = value
        self.situation_data[entity_plural][name] = data

    def get_entity(self, name: str) -> Entity:
        """Gets the entity type of the entity with a given name.

        Args:
            name (str): The name of the entity.

        Returns:
            Entity: The type of the entity.
        """
        entity_type = [
            entity
            for entity in self.entities.values()
            if name in self.situation_data[entity.plural]
        ][0]
        return entity_type

    def map_to(
        self, arr: np.array, entity: str, target_entity: str, how: str = None
    ):
        """Maps values from one entity to another.

        Args:
            arr (np.array): The values in their original position.
            entity (str): The source entity.
            target_entity (str): The target entity.
            how (str, optional): A function to use when mapping. Defaults to None.

        Raises:
            ValueError: If an invalid (dis)aggregation function is passed.

        Returns:
            np.array: The mapped values.
        """
        entity_pop = self.simulation.populations[entity]
        target_pop = self.simulation.populations[target_entity]
        if entity == "person" and target_entity in self.group_entity_names:
            if how and how not in (
                "sum",
                "any",
                "min",
                "max",
                "all",
                "value_from_first_person",
            ):
                raise ValueError("Not a valid function.")
            return target_pop.__getattribute__(how or "sum")(arr)
        elif entity in self.group_entity_names and target_entity == "person":
            if not how:
                return entity_pop.project(arr)
            if how == "mean":
                return entity_pop.project(arr / entity_pop.nb_persons())
        elif entity == target_entity:
            return arr
        else:
            return self.map_to(
                self.map_to(arr, entity, "person", how="mean"),
                "person",
                target_entity,
                how="sum",
            )

    def get_group(self, entity: str, name: str) -> str:
        """Gets the name of the containing entity for a named entity and group type.

        Args:
            entity (str): The group type, e.g. "household".
            name (str): The name of the entity, e.g. "person1".

        Returns:
            str: The containing entity, e.g. "household1".
        """
        containing_entity = [
            group
            for group in self.situation_data[entity.plural]
            if name in self.situation_data[entity.plural][group]["adults"]
            or name in self.situation_data[entity.plural][group]["children"]
        ][0]
        return containing_entity

    def calc(
        self,
        var: str,
        period: int = None,
        target: str = None,
        index: int = None,
        map_to: str = None,
        reform: Reform = None,
    ) -> np.array:
        """Calculates the value of a variable, executing any required formulas.

        Args:
            var (str): The variable to calculate.
            period (int, optional): The time period to calculate for. Defaults to None.
            target (str, optional): The target entity if not all entities are required. Defaults to None.
            index (int, optional): The numerical index of the target entity. Defaults to None.
            reform (reform, optional): The reform to apply. Defaults to None.

        Returns:
            np.array: The resulting values.
        """
        if not hasattr(self, "simulation"):
            self.build()

        if self.parametric_vary and reform is None:
            results = [
                self.calc(
                    var,
                    period=period,
                    target=target,
                    index=index,
                    map_to=map_to,
                    reform=reform,
                )
                for reform in self.parametric_reforms
            ]
            return np.array(results)

        if reform is not None:
            reform.apply(self)

        period = period or self.year
        entity = self.system.variables[var].entity
        try:
            result = self.simulation.calculate(var, period)
        except:
            try:
                result = self.sim.calculate_add(var, period)
            except:
                result = self.simulation.calculate_divide(var, period)
        if (
            target is not None
            and target not in self.situation_data[entity.plural]
        ):
            map_to = self.get_entity(target).key
        if map_to is not None:
            result = self.map_to(result, entity.key, map_to)
            entity = self.entities[map_to]
        if self.varying:
            result = result.reshape(
                (self.num_points, len(self.situation_data[entity.plural]))
            ).transpose()
        members = list(self.situation_data[entity.plural])
        if index is not None:
            index = min(len(members) - 1, index)
        if target is not None:
            index = members.index(target)
        if target is not None or index is not None:
            return result[index]
        return result

    def deriv(
        self,
        var: str,
        wrt: str = "employment_income",
        period: int = None,
        var_target: str = None,
        wrt_target: str = None,
    ):
        """Calculates the derivative of one variable with respect to another.

        Args:
            var (str): The target variable.
            wrt (str, optional): The varying variable. Defaults to "employment_income".
            period (int, optional): The time period to calculate over. Defaults to None.
            var_target (str, optional): The target name. Defaults to None.
            wrt_target (str, optional): The source name. Defaults to None.

        Returns:
            np.array: The derivatives as the source variable varies.
        """
        period = period or self.year
        y = self.calc(var, period=period, target=var_target)
        x = self.calc(wrt, period=period, target=wrt_target)
        try:
            y = y.squeeze()
        except:
            pass
        try:
            x = x.squeeze()
        except:
            pass
        x = x.astype(np.float32)
        y = y.astype(np.float32)
        assert (
            len(y) > 1 and len(x) > 1
        ), "Simulation must vary on an axis to calculate derivatives."
        deriv = (y[1:] - y[:-1]) / (x[1:] - x[:-1])
        deriv = np.append(deriv, deriv[-1])
        return deriv

    def reset_vary(self) -> None:
        """Removes an axis from the simulation."""
        del self.situation_data["axes"]
        self.varying = False
        self.num_points = None

    def vary(
        self,
        var: str = None,
        parameter: str = None,
        min: float = 0,
        max: float = 200000,
        step: float = 100,
        index: int = 0,
        period: int = None,
    ) -> None:
        """Adds an axis to the situation, varying one variable.

        Args:
            var (str, optional): The variable to change.
            parameter (str, optional): The parameter to vary. Defaults to None.
            min (float, optional): The minimum value. Defaults to 0.
            max (float, optional): The maximum value. Defaults to 200000.
            step (float, optional): The step size. Defaults to 100.
            index (int, optional): The specific entity index to target. Defaults to 0.
            period (int, optional): The time period. Defaults to None.
        """
        count = int((max - min) / step) + 1
        if var is not None:
            period = period or self.year
            if "axes" not in self.situation_data:
                self.situation_data["axes"] = [[]]
            self.situation_data["axes"][0] += [
                {
                    "count": count,
                    "name": var,
                    "min": min,
                    "max": max,
                    "period": period,
                    "index": index,
                }
            ]
            self.build()
            self.varying = True

            self.num_points = count
        if parameter is not None:
            # Parametric vary
            self.parametric_vary = True
            parameter_values = np.linspace(min, max, count)
            self.parametric_reforms = [
                set_parameter(parameter, value, period or "year:2022:10")
                for value in parameter_values
            ]
