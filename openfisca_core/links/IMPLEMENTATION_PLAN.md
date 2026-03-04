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

### Phase 2: Entity integration ✅ (done)

- [x] Add `_links: dict[str, Link]` to `CoreEntity`
- [x] Add `add_link(link)`, `get_link(name)`, `links` property
- [x] In `Simulation.__init__`, call `_resolve_links()` → attach + resolve
- [x] Tests: entity registration, simulation resolution, backward compat
- [x] 14 tests pass (5 unit + 9 integration), 147 total

### Phase 3: Auto-generate Implicit Links (✅ Completed)
- [x] Create `openfisca_core/links/implicit.py` with `ImplicitMany2OneLink` and `ImplicitOne2ManyLink`.
- [x] Have them map to `GroupPopulation.members_entity_id`/`members_role` instead of explicit link fields.
- [x] Automatically inject these links on populations when the `Simulation` object is built (`_resolve_links`).
- [x] Test person->group and group->persons lookups using only `SimulationBuilder` group dictionaries.
- [x] Make sure all links are bound to `population.links` instead of remaining unbound on `entity.links`.

### Phase 4: Projectors as facades (✅ Skipped)

- [x] Obsoleted by Phase 3: the `__getattr__` overload on `CorePopulation` natively maps known shortcut properties to their automatically generated links (e.g. `person.household`, `household.persons`). Existing projectors remain untouched as fallbacks.
- [ ] Reimplement UniqueRoleToEntityProjector via One2ManyLink.get_by_role()
- [ ] Reimplement FirstPersonToEntityProjector via One2ManyLink.nth()
- [ ] Non-regression: all existing tests pass with delegated projectors

### Phase 5: Country package API (✅ Completed)

- [x] Allow country packages to declare custom links on entities (`entity.add_link()`)
- [x] Example: mother/children intra-entity links validated in integration tests
- [x] Example: employer inter-entity link supported via explicit fields
- [x] Documentation written in `docs/implementation/links-api.md`

### Phase 6: Integration tests (✅ Completed)

- [x] Full simulation with intra-entity links (person.mother.age)
- [x] Full simulation with link chaining (person.mother.household.rent)
- [x] Performance benchmark: links vs current projectors (performance is ~identical for get, slightly slower for aggregations but <1ms in overhead)
- [x] Non-regression: openfisca-core and openfisca-country-template tests all pass

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
