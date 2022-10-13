# Writing parameters

**Parameters** are values that can change over time (but are the same for an entire country package, i.e. they can't be different for different entities). The `parameters/` folder of a country package contains the **parameter tree**, a tree of parameter nodes (objects that hold parameters as children) containing parameters or subnodes. A parameter node can be represented either as a folder, or a YAML file. Parameters are stored in parameter files. For example, a parameter tree might have the following structure in a country repo:

```{eval-rst}
.. code:: none

   parameters/
   ├── child_benefit/
   │   ├── basic.yaml
   │   ├── child.yaml
   |   ├── family.yaml
   │   └── index.yaml # Contains metadata for the child_benefit node.
   ├── income_tax/
   │   ├── basic.yaml
   │   ├── personal.yaml
   │   └── thresholds.yaml
   ├── national_insurance/
   │   ├── basic.yaml
   │   ├── employee.yaml
   │   └── thresholds.yaml
   └── universal_credit/
       ├── basic.yaml
       ├── child.yaml
       └── family.yaml
```

## Parameter values

Parameters are defined as a function of time, and are evaluated at a given instant. To achieve this, parameters must be defined with a **value history**: a set of time-dated values (where the value at a given instant is the last-set value before that instant). For example, the `child_benefit.basic.amount` parameter might have the following value history:

```yaml
values:
   2019-04-01: 20.00
   2019-04-02: 21.00
   2019-04-03: 22.00
   2019-04-04: 23.00
   2019-04-05: 24.00

```

## Metadata

Each parameter (or parameter node) can also set **metadata**: data that describes the parameter, such as its name, description, and units. While the metadata for each parameter and node is freeform, using the schemas defined in `policyengine_core.data_structures` will ensure consistency between country packages, and better maintainability.

Here's an example metadata specification for the `child_benefit.basic.amount` parameter:

```yaml
metadata:
    name: child_benefit
    label: Child Benefit
    description: The amount of Child Benefit paid per child.
    unit: currency-GBP
    reference: 
        - label: GOV.UK | Child Benefit
          href: https://www.gov.uk/government/publications/child-benefit-rates-and-thresholds/child-benefit-rates-and-thresholds
```

### Metadata for parameters

```{eval-rst}
.. autoclass:: policyengine_core.data_structures.ParameterMetadata
    :members:
```

### Metadata for parameter nodes

```{eval-rst}
.. autoclass:: policyengine_core.data_structures.ParameterNodeMetadata
    :members:
```

## Specifying references

```{eval-rst}
.. autoclass:: policyengine_core.data_structures.Reference
    :members:
```

## Units

```{eval-rst}
.. autoclass:: policyengine_core.data_structures.Unit
    :members:
```

## Other specifications

```{eval-rst}
.. automodule:: policyengine_core.data_structures.parameter_metadata
    :members:
    :show-inheritance:
    :exclude-members: ParameterMetadata, Reference, Unit

.. automodule:: policyengine_core.data_structures.parameter_node_metadata
    :members:
    :show-inheritance:
    :exclude-members: ParameterNodeMetadata
```
