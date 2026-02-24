# Entity Links — Implementation Plan

## Branch: `feat/entity-links`

Based on: `master` (3114a8f)

## Objective

Add a generic link system to openfisca-core that:
1. **Preserves 100% backward compatibility** — all existing formulas,
   projectors, and tests continue working unchanged
2. **Enables new capabilities** — intra-entity links (person→person),
   custom named links (person→employer), link chaining
3. **Coexists with the current system** — can be activated per-entity,
   the old GroupEntity/Projector path keeps working as fallback

## Architecture

```
NEW module: openfisca_core/links/
├── __init__.py         ✅ created
├── link.py             ✅ created — base Link class
├── many2one.py         ✅ created — Many2OneLink (N→1 with roles)
├── one2many.py         ✅ created — One2ManyLink (1→N with aggregations)
└── tests/
    └── __init__.py     ✅ created — tests for Link

MODIFIED (Phase 2+):
├── entities/_core_entity.py     — add _links dict
├── entities/group_entity.py     — auto-generate links from roles
├── simulations/simulation.py    — resolve links at init
└── projectors/                  — delegate to links (Phase 4)
```

## Phases

### Phase 1: Core link classes ✅ (done)

- [x] `Link` base class with attach/resolve lifecycle
- [x] `Many2OneLink.get()` — value lookup via link_field
- [x] `Many2OneLink` chaining via `__getattr__`
- [x] `Many2OneLink` role helpers (role, has_role)
- [x] `One2ManyLink` aggregations (sum, count, any, all, min, max, avg)
- [x] `One2ManyLink` role and condition filtering
- [x] ID resolution (direct positions + id_to_rownum)
- [x] Unit tests for Link base class

### Phase 2: Entity integration

- [ ] Add `_links: dict[str, Link]` to `CoreEntity`
- [ ] Add `add_link(link)` and `get_link(name)` methods
- [ ] In Simulation.__init__, call `link.attach()` and `link.resolve()`
- [ ] Tests: entity with custom links, resolution

### Phase 3: Auto-generate links from GroupEntity

- [ ] In Simulation, auto-create Many2OneLink (person→group) and
  One2ManyLink (group→persons) from existing GroupEntity structure
- [ ] Use `members_entity_id` as the implicit link_field
- [ ] Use `members_role` as the implicit role_field
- [ ] Tests: verify auto-generated links produce same results as
  current GroupPopulation methods

### Phase 4: Projectors as facades (optional)

- [ ] Reimplement EntityToPersonProjector.transform() via Many2OneLink.get()
- [ ] Reimplement UniqueRoleToEntityProjector via One2ManyLink.get_by_role()
- [ ] Reimplement FirstPersonToEntityProjector via One2ManyLink.nth()
- [ ] Non-regression: all existing tests pass with delegated projectors

### Phase 5: Country package API

- [ ] Allow country packages to declare custom links on entities
- [ ] Example: mother/children intra-entity links
- [ ] Example: employer inter-entity link
- [ ] documentation

### Phase 6: Integration tests

- [ ] Full simulation with intra-entity links (person.mother.age)
- [ ] Full simulation with link chaining (person.mother.household.rent)
- [ ] Performance benchmark: links vs current projectors
- [ ] Non-regression: openfisca-country-template tests all pass

## Key design decisions

1. **Links live on Entity, not Population**: Link definitions are
   structural (like roles), so they belong on the entity definition.
   At simulation time, `attach()` and `resolve()` bind them to
   actual populations.

2. **link_field is a Variable name**: The field holding target IDs
   is a regular Variable (e.g. `mother_id`). This means it can be
   an input, computed by a formula, or even an AsOfVariable.

3. **Backward compatibility via fallback**: If a link is not defined,
   the existing GroupPopulation/Projector code path is used. Links
   are opt-in.

4. **id_to_rownum for intra-entity links**: Person→person links need
   to map person IDs to row positions. This uses the LIAM2
   `id_to_rownum` pattern, which is a simple numpy array where
   `id_to_rownum[person_id] = row_index`.

## Files created

| File | Lines | Purpose |
|---|---|---|
| `links/__init__.py` | 36 | Package init |
| `links/link.py` | 109 | Base Link class |
| `links/many2one.py` | 189 | Many2OneLink |
| `links/one2many.py` | 223 | One2ManyLink |
| `links/tests/__init__.py` | 59 | Unit tests |
| `IMPLEMENTATION_PLAN.md` | this file | Plan |
