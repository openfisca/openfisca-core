# Simulations

The `policyengine_core.simulations` module contains the definition of `Simulation`, the singular most important class in the repo. `Simulations` combine the logic of a country package with data, and can use the country logic and parameters to calculate the values of unknown variables. The class `SimulationBuilder` can create `Simulation`s from a variety of inputs: JSON descriptions, or dataset arrays.

## Simulation

```{eval-rst}
.. autoclass:: policyengine_core.simulations.simulation.Simulation
    :members:
    :undoc-members:
    :inherited-members:
    :show-inheritance:
```

## WeightedSimulation

```{eval-rst}
.. autoclass:: policyengine_core.simulations.weighted_simulation.WeightedSimulation
    :members:
    :undoc-members:
    :inherited-members:
    :show-inheritance:
```

## SimulationBuilder

```{eval-rst}
.. autoclass:: policyengine_core.simulations.simulation_builder.SimulationBuilder
    :members:
    :undoc-members:
    :inherited-members:
    :show-inheritance:
```

