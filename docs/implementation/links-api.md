# Entity Links API

OpenFisca Core now includes a generic Entity Link system. Links allow variables computed on one entity to be queried and aggregated from another, or even within the same entity.

## Declaring Links

Links are declared on `Entity` objects, typically when building the `TaxBenefitSystem`.

### 1. Many-to-One Links
A `Many2OneLink` resolves many source members (e.g., persons) to one target entity (e.g., a household, an employer, or another person).

```python
from openfisca_core.links import Many2OneLink

# Example: Intra-entity link (person to mother)
# The `mother_id` variable must be defined on `person` and contain the ID of the mother.
mother_link = Many2OneLink(
    name="mother",
    link_field="mother_id",
    target_entity_key="person",
)
person_entity.add_link(mother_link)

# Usage in a variable formula:
# persons.mother.get("age", period)
# or chained: persons.mother.household.get("rent", period)
```

### 2. One-to-Many Links
A `One2ManyLink` resolves one source entity to many target members. By default, OpenFisca implicitly creates a `One2ManyLink` for every GroupEntity pointing to its members (e.g., `household.persons`).

```python
from openfisca_core.links import One2ManyLink

# Example: Inter-entity link (employer to employees)
# The `employer_id` variable must be defined on `person` and contain the employer ID.
employees_link = One2ManyLink(
    name="employees",
    link_field="employer_id",
    target_entity_key="person", # the target returned
)
employer_entity.add_link(employees_link)

# Usage in a variable formula:
# employers.employees.sum("salary", period)
```

## Using Links in Formulas

When a link is declared on a population, it is exposed as an attribute matching the link's `name`.

### Many2One Methods

*   **`link.get(variable_name, period)`**: Returns the target variable values mapped to each source member. Unmapped members receive the default value of the variable.
*   **Syntactic sugar**: `link(variable_name, period)` is equivalent to `link.get(variable_name, period)`.
*   **Chaining**: `<source>.link1.link2` returns an intermediate chained getter, so `.link1.link2.get(variable, period)` fetches the target variable across two link jumps.

### One2Many Methods

All One2Many aggregation methods return an array sized to the **source** entity. They all take `(variable_name, period)` + optional keyword arguments `role` and `condition` to filter the targets before aggregation.

*   `link.sum(...)`
*   `link.count(...)`
*   `link.any(...)`
*   `link.all(...)`
*   `link.min(...)`
*   `link.max(...)`
*   `link.avg(...)`
