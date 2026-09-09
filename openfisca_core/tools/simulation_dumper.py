import os

import numpy

from openfisca_core.data_storage import OnDiskStorage
from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import DateUnit
from openfisca_core.simulations import Simulation


def dump_simulation(simulation, directory) -> None:
    """Write simulation data to directory, so that it can be restored later."""
    parent_directory = os.path.abspath(os.path.join(directory, os.pardir))
    if not os.path.isdir(parent_directory):  # To deal with reforms
        os.mkdir(parent_directory)
    if not os.path.isdir(directory):
        os.mkdir(directory)

    if os.listdir(directory):
        msg = f"Directory '{directory}' is not empty"
        raise ValueError(msg)

    entities_dump_dir = os.path.join(directory, "__entities__")
    os.mkdir(entities_dump_dir)

    for entity in simulation.populations.values():
        # Dump entity structure
        _dump_entity(entity, entities_dump_dir)

        # Dump variable values
        for holder in entity._holders.values():
            _dump_holder(holder, directory)


def restore_simulation(directory, tax_benefit_system, **kwargs):
    """Restore simulation from directory."""
    simulation = Simulation(
        tax_benefit_system,
        tax_benefit_system.instantiate_entities(),
    )

    entities_dump_dir = os.path.join(directory, "__entities__")
    for population in simulation.populations.values():
        _restore_entity(population, entities_dump_dir)

    variables_to_restore = (
        variable for variable in os.listdir(directory) if variable != "__entities__"
    )
    for variable in variables_to_restore:
        _restore_holder(simulation, variable, directory)

    return simulation


def _dump_holder(holder, directory) -> None:
    disk_storage = holder.create_disk_storage(directory, preserve=True)
    for period in holder.get_known_periods():
        value = holder.get_array(period)
        disk_storage.put(value, period)


def _dump_entity(population, directory) -> None:
    path = os.path.join(directory, population.entity.key)
    os.mkdir(path)
    numpy.save(os.path.join(path, "id.npy"), population.ids)

    if population.entity.is_person:
        return

    numpy.save(os.path.join(path, "members_position.npy"), population.members_position)
    numpy.save(
        os.path.join(path, "members_entity_id.npy"), population.members_entity_id
    )

    flattened_roles = population.entity.flattened_roles
    if len(flattened_roles) == 0:
        encoded_roles = numpy.int16(0)
    else:
        encoded_roles = numpy.select(
            [population.members_role == role for role in flattened_roles],
            [role.key for role in flattened_roles],
            default="",
        )
    numpy.save(os.path.join(path, "members_role.npy"), encoded_roles)


def _restore_entity(population, directory) -> None:
    path = os.path.join(directory, population.entity.key)

    population.ids = numpy.load(os.path.join(path, "id.npy"))
    # The number of entities cannot be inferred from the members mapping, as
    # a group entity may have no member at all: use the dumped ids instead.
    population.count = len(population.ids)

    if population.entity.is_person:
        return

    population.members_position = numpy.load(os.path.join(path, "members_position.npy"))
    population.members_entity_id = numpy.load(
        os.path.join(path, "members_entity_id.npy")
    )
    encoded_roles = numpy.load(os.path.join(path, "members_role.npy"))

    flattened_roles = population.entity.flattened_roles
    if len(flattened_roles) == 0:
        population.members_role = numpy.int16(0)
    else:
        population.members_role = numpy.select(
            [encoded_roles == role.key for role in flattened_roles],
            list(flattened_roles),
            default=None,
        )


def _restore_holder(simulation, variable_name, directory) -> None:
    storage_dir = os.path.join(directory, variable_name)

    holder = simulation.get_holder(variable_name)

    is_variable_eternal = holder.variable.definition_period == DateUnit.ETERNITY

    disk_storage = OnDiskStorage(
        storage_dir,
        is_eternal=is_variable_eternal,
        preserve_storage_dir=True,
        enums=(
            {storage_dir: holder.variable.possible_values}
            if holder.variable.value_type == Enum
            and holder.variable.possible_values is not None
            else {}
        ),
    )
    disk_storage.restore()

    for period in disk_storage.get_known_periods():
        value = disk_storage.get(period)
        holder.put_in_cache(value, period)
