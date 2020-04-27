# -*- coding: utf-8 -*-


import os

import numpy as np

from openfisca_core.simulations import Simulation
from openfisca_core.data_storage import OnDiskStorage
from openfisca_core.periods import ETERNITY


def dump_simulation(simulation, directory):
    """
        Write simulation data to directory, so that it can be restored later.
    """
    parent_directory = os.path.abspath(os.path.join(directory, os.pardir))
    if not os.path.isdir(parent_directory):  # To deal with reforms
        os.mkdir(parent_directory)
    if not os.path.isdir(directory):
        os.mkdir(directory)

    if os.listdir(directory):
        raise ValueError("Directory '{}' is not empty".format(directory))

    entities_dump_dir = os.path.join(directory, "__entities__")
    os.mkdir(entities_dump_dir)

    for entity in simulation.populations.values():
        # Dump entity structure
        _dump_entity(entity, entities_dump_dir)

        # Dump variable values
        for holder in entity._holders.values():
            _dump_holder(holder, directory)


def restore_simulation(directory, tax_benefit_system, **kwargs):
    """
        Restore simulation from directory
    """
    simulation = Simulation(tax_benefit_system, tax_benefit_system.instantiate_entities())

    entities_dump_dir = os.path.join(directory, "__entities__")
    for population in simulation.populations.values():
        if population.entity.is_person:
            continue
        person_count = _restore_entity(population, entities_dump_dir)

    for population in simulation.populations.values():
        if not population.entity.is_person:
            continue
        _restore_entity(population, entities_dump_dir)
        population.count = person_count

    variables_to_restore = (variable for variable in os.listdir(directory) if variable != "__entities__")
    for variable in variables_to_restore:
        _restore_holder(simulation, variable, directory)

    return simulation


def _dump_holder(holder, directory):
    disk_storage = holder.create_disk_storage(directory, preserve = True)
    for period in holder.get_known_periods():
        value = holder.get_array(period)
        disk_storage.put(value, period)


def _dump_entity(population, directory):
    path = os.path.join(directory, population.entity.key)
    os.mkdir(path)
    np.save(os.path.join(path, "id.npy"), population.ids)

    if population.entity.is_person:
        return

    np.save(os.path.join(path, "members_position.npy"), population.members_position)
    np.save(os.path.join(path, "members_entity_id.npy"), population.members_entity_id)

    flattened_roles = population.entity.flattened_roles
    if len(flattened_roles) == 0:
        encoded_roles = np.int64(0)
    else:
        encoded_roles = np.select(
            [population.members_role == role for role in population.entity.flattened_roles],
            [role.key for role in population.entity.flattened_roles],
            )
    np.save(os.path.join(path, "members_role.npy"), encoded_roles)


def _restore_entity(population, directory):
    path = os.path.join(directory, population.entity.key)

    population.ids = np.load(os.path.join(path, "id.npy"))

    if population.entity.is_person:
        return

    population.members_position = np.load(os.path.join(path, "members_position.npy"))
    population.members_entity_id = np.load(os.path.join(path, "members_entity_id.npy"))
    encoded_roles = np.load(os.path.join(path, "members_role.npy"))
    population.members_role = np.select(
        [encoded_roles == role.key for role in population.entity.flattened_roles],
        [role for role in population.entity.flattened_roles],
        )
    person_count = len(population.members_entity_id)
    population.count = max(population.members_entity_id) + 1
    return person_count


def _restore_holder(simulation, variable, directory):
    storage_dir = os.path.join(directory, variable)
    is_variable_eternal = simulation.tax_benefit_system.get_variable(variable).definition_period == ETERNITY
    disk_storage = OnDiskStorage(
        storage_dir,
        is_eternal = is_variable_eternal,
        preserve_storage_dir = True
        )
    disk_storage.restore()

    holder = simulation.get_holder(variable)

    for period in disk_storage.get_known_periods():
        value = disk_storage.get(period)
        holder.put_in_cache(value, period)
