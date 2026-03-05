# Feature: Generic Entity Links (LIAM2-inspired)

## Context & Motivation

OpenFisca's traditional entity model has historically been strictly hierarchical and bipartite: individuals belong to groups (households, families, tax units), and groups contain individuals. This rigid structure works well for static tax-benefit systems but struggles with complex, real-world socioeconomic models, such as:
- **Intra-entity relationships**: Kinship graphs (person $\rightarrow$ mother, person $\rightarrow$ spouse).
- **Arbitrary inter-entity networks**: Employment networks (person $\rightarrow$ employer), geographical mobility, or ad-hoc associations.
- **Deep chaining**: Navigating multiple relationship hops (e.g., "the region of the household of the mother of the person").

To solve this, we drew inspiration from [LIAM2's linking system](https://liam2.plan.be/) and adapted it to OpenFisca's unique architecture (specifically integrating with our `Role` semantics and vectorized execution).

## What we did

This PR introduces a generic, highly performant, and **100% backward-compatible** Entity Linking system.

### 1. Core Link Classes (`openfisca_core/links`)
- **`Many2OneLink`**: Resolves *N* source members to *1* target entity (e.g., `person.mother`, `person.employer`). Supports fetching values (`.get()`) and dynamic chaining (`.mother.household.rent`).
- **`One2ManyLink`**: Aggregates from *N* target members back to *1* source entity. Supports a wide suite of vectorized aggregations (`sum`, `count`, `any`, `all`, `min`, `max`, `avg`) along with filtering by `role` or an arbitrary boolean `condition` mask.

### 2. Implicit Links & Backward Compatibility
A major design goal was to avoid breaking existing country packages (`openfisca-france`, `openfisca-tunisia`, etc.).
- Links are strictly **additive**.
- During `Simulation` initialization, OpenFisca now automatically reads the existing `GroupEntity` structure and injects **Implicit Links**:
  - `ImplicitMany2OneLink`: Automatically adds `person.household`, mapping directly to the high-performance `GroupPopulation.members_entity_id` array.
  - `ImplicitOne2ManyLink`: Automatically adds `household.persons`, replacing the need for verbose legacy aggregations.
- `Population.__getattr__` was carefully patched to first check `self.links["..."]` before natively falling back to the legacy `get_projector_from_shortcut()` route. *Everything keeps working identically.*

### 3. Syntax Sugar & Chaining
The new API allows natural, pythonic data fetching:
```python
# Old projector way (still works!):
rents = sim.persons.household("rent", "2024")

# New explicit link definition (e.g., for arbitrary networks)
mother_link = Many2OneLink(name="mother", link_field="mother_id", target_entity_key="person")
person_entity.add_link(mother_link)

# New chaining syntax:
mother_household_rents = sim.persons.mother.household.get("rent", "2024")

# New declarative aggregations:
female_salaries = sim.households.persons.sum("salary", "2024", condition=is_female)
```

## Performance
Performance is a critical constraint for OpenFisca simulations. We added `pytest-benchmark` tests validating the new mechanics.
- `.get()` resolutions (Many-to-One) perform identically to legacy Projectors (~118μs on 15,000 entities).
- Aggregations (`One2Many.sum()`) introduce a negligible setup overhead (< 1ms) but execute fully vectorized `numpy.bincount` and `numpy.maximum.at` operations under the hood.

## Associated Documentation
We've added guides to help framework users model new relationships:
- `docs/implementation/links-api.md`: Reference for creating and querying `Many2OneLink` and `One2ManyLink`.
- `docs/implementation/transition-guide.md`: Migration guide demonstrating how to gradually adopt Links over Legacy Projectors.

## Builder & test clarity
- **`build_default_simulation(..., group_members=...)`**: Optional `group_members` dict (e.g. `{"household": [0,0,1,1]}`) sets group structure at build time so tests no longer patch private attributes.
- **`GroupPopulation.set_members_entity_id(array)`**: Public API to set group structure and clear internal caches; tests use this instead of touching `_members_position` / `_ordered_members_map`.

## Testing
- 12 new, comprehensive tests covering unit mechanics, system integrations, filtering, chaining, and OpenFisca core lifecycle (`_resolve_links`).
- All 158 core tests and existing Country Template tests continue to pass locally (`make test-code`).
