# Transition Guide: Moving to the New Entity Links

With the release of the **Generic Entity Links** API, OpenFisca-core gains the ability to map complex, graph-like relational structures natively.

This guide explains the primary differences between the legacy `GroupEntity` + `Projectors` approach and the flexible, modern `Many2OneLink` and `One2ManyLink` models, and how you should think about migration.

---

## 1. Why Transition? The "Strict Hierarchy" Problem

Historically, OpenFisca rigidly structured populations into two classes: `SingleEntity` (Persons) and `GroupEntity` (Households, Families, Tax Units).

In this model, **every person must belong to exactly one entity of each group type.**
This handles standard socio-tax models efficiently, but prohibits features like:
- **Intra-entity (horizontal) relations**: Modeling a mother/child bond, marriages, or kinship networks. *Persons couldn't map to other Persons.*
- **Unbounded inter-entity relations**: Employment networks where one `company` controls multiple `persons`, or geographical relations (people living in specific arbitrary administrative districts).

**The Solution:** The new Entity Links system is purely arbitrary and structural. You can declare `Many2OneLink` (N source members to 1 target entity) or `One2ManyLink` (aggregating 1 target back to N source members) linking *any population type to any other population type.*

---

## 2. You don’t *have* to migrate existing simple groups.

**Backward Compatibility is 100% Guaranteed.**

If you have a traditional `GroupEntity` defined for households, those work exactly as they always have. In fact, OpenFisca now silently powers them using the new Linking engine gracefully:
- The legacy `person.household(...)` projector maps to a new automatically injected `ImplicitMany2OneLink`.
- The legacy `household.sum(person_salaries)` maps logically to `household.persons.sum()`.

No code change is required in any existing variable formulas!

---

## 3. From Projectors to Links: The New Syntax

If you previously dealt with `Projectors`, you may have found chaining difficult or buggy. The new system standardizes data lookup through `link.get()` and properties filtering.

### Before: Projectors
If you wanted the value of `rent` for the household of a person:
```python
# Projector syntax
rents = person.household("rent", period)
```

### After: Link Syntax
The same syntax continues to work (it actually calls `.get()` internally now on the implicitly generated link!), but you can explicitly specify `.get()`:
```python
# New link syntax
rents = person.household.get("rent", period)
```

**Where the new syntax shines:** Deep chaining.
You can now continuously resolve attributes down a deep relationship chain effortlessly:
```python
# Imagine a link: `person -> mother_person -> mother_household -> region`
chain = person.mother.household.get("region", period)
```

---

## 4. Transitioning Aggregations: `sum`, `count`, `min`, `max`

Previously, aggregating members relied rigidly on passing entire pre-computed arrays to a heavy `GroupPopulation.sum()` handler.

### Before: Legacy GroupPopulation
```python
# Fetch array of all persons in simulation
salaries = persons("salary", period)
# Pass to the group entity (e.g. household) to aggregate and collapse
total_household_incomes = households.sum(salaries, role=Household.PARENT)
```

### After: Declarative Links
```python
# The logic operates directly on the `One2ManyLink` bridging the two entities.
total_household_incomes = households.persons.sum("salary", period, role=Household.PARENT)
```
Notice how declarative and explicit this is. `persons` is the plural of `person`, which the new system automatically exposed as a `One2ManyLink` on your household.

### Conditional Aggregations
A newly-available feature explicitly unlocked by the Link system is masking by arbitrary properties! You are no longer restricted strictly to OpenFisca Roles:
```python
is_female = persons("is_female", period)
# Sum salaries, but only for members who are `is_female`
female_incomes = households.persons.sum("salary", period, condition=is_female)
```

---

## 5. Summary Checklist for Country Packages
- [ ] You **do not** need to rewrite `GroupEntity` logic for entities whose only purpose is traditional demographic grouping (like core households).
- [ ] You **can** start using `households.persons.sum()`, `households.persons.any()`, `households.persons.avg()` for highly readable aggregations in new variables.
- [ ] You **should** use `Many2OneLink` immediately if your simulation model attempts to relate `persons` to specific entities beyond openfisca-standard hierarchical groups (like a `mother_id` linking to another row in the `persons` dataframe).

Please see the full `links-api.md` file in this directory to see exactly how to declare explicit `Many2OneLink` models inside your `TaxBenefitSystem`.
