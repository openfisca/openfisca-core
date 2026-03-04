# Plan d'implémentation du système de lines

## Vue d'ensemble

### Ce qu'on a aujourd'hui dans country-template

| Entité | Type | Variables |
|---|---|---|
| `Person` | `is_person=True` | `birth`, `age`, `salary`, `capital_returns`, `income_tax`, `social_security_contribution`, `basic_income`, `pension` |
| `Household` | GroupEntity (rôles: `adult`, `child`) | `accommodation_size`, `rent`, `housing_occupancy_status`, `postal_code`, `housing_tax`, `housing_allowance`, `parenting_allowance`, `disposable_income`, `household_income`, `total_benefits`, `total_taxes` |

### Ce qu'on veut en PLUS pour tester les lines

| Line | Type | Exemple d'usage | Pourquoi |
|---|---|---|---|
| `person.mother` | Many2One (Person→Person) | `person.mother("salary", period)` | Tester les lines intra-entité |
| `person.father` | Many2One (Person→Person) | `person.father("age", period)` | Tester un 2ème line intra-entité |
| `person.spouse` | Many2One (Person→Person) | `person.spouse("salary", period)` | Tester un line symétrique |
| `person.children` | One2Many (Person→Person via `mother`/`father`) | `person.children.count()` | Tester le line inverse |
| `person.mother.household` | Chaîné | `person.mother.household("rent", period)` | Tester la composition de lines |

---

## Phase 0 : Préparation (1 jour)

**Objectif** : S'assurer que tout est vert avant de commencer.

### Étapes

1. **Vérifier les tests existants**
   ```bash
   cd /home/benjello/projects/openfisca-core
   pytest openfisca_core/ -x -q
   ```

2. **Créer une branche**
   ```bash
   git checkout -b add-links-system
   ```

3. **Vérifier que country-template tourne contre core local**
   ```bash
   cd /home/benjello/projects/country-template
   pip install -e ../openfisca-core
   pytest openfisca_country_template/ -x -q
   ```

### Critère de sortie
Tous les tests passent.

---

## Phase 1 : Classes Link de base (2-3 jours)

**Objectif** : Créer les classes `Link`, `Many2OneLink`, `One2ManyLink`
sans toucher au code existent.

### Fichiers à créer

```
openfisca_core/
  links/
    __init__.py
    _link.py           # classe abstraite Link
    _many2one_link.py   # Many2OneLink
    _one2many_link.py   # One2ManyLink
    _chained_link.py    # ChainedLink (composition)
    types.py
```

### Code à écrire

#### `_link.py`

```python
"""Base class for all links."""
from __future__ import annotations

import abc

import numpy


class Link(abc.ABC):
    """A relationship between two entity populations.

    A link is defined by:
    - name: human-readable name (e.g. "mother", "household")
    - field: the array storing the link IDs (e.g. mother_id)
    - source: the entity where the link lives (e.g. Person)
    - target: the entity being pointed to (e.g. Person, Household)
    """

    name: str
    field: str
    source: str   # entity key
    target: str   # entity key

    def __init__(self, name: str, field: str, target: str) -> None:
        self.name = name
        self.field = field
        self.target = target
        self.source = None  # Set when attached to a Population

    @abc.abstractmethod
    def get(self, source_population, target_population, variable_name, period):
        """Follow the link and get target values."""
        ...
```

#### `_many2one_link.py`

```python
"""Many-to-one link (e.g. person → household, person → mother)."""
from __future__ import annotations

import numpy

from ._link import Link


class Many2OneLink(Link):
    """A link where many source entities point to one target entity.

    Examples: person.household, person.mother, person.employer
    """

    role: str | None   # Optional: role in a GroupEntity

    def __init__(self, name, field, target, role=None):
        super().__init__(name, field, target)
        self.role = role

    def get(self, source_population, target_population,
            variable_name, period):
        """Follow the link: get target variable for each source entity.

        Implementation: fancy indexing O(N).
        source_population.get_holder(self.field) → link_ids
        target_values[link_ids]
        """
        # Get the link IDs array
        link_ids = source_population.get_holder(self.field).get_array(period)
        if link_ids is None:
            link_ids = source_population.get_holder(self.field).get_array()
        # Get the target values
        target_values = target_population.simulation.calculate(
            variable_name, period)
        # Handle missing links (-1)
        valid = link_ids >= 0
        result = numpy.zeros(len(link_ids), dtype=target_values.dtype)
        if target_population._dynamic:
            # Use id_to_rownum for dynamic populations
            rownum = target_population._id_to_rownum[link_ids[valid]]
        else:
            rownum = link_ids[valid]
        result[valid] = target_values[rownum]
        return result
```

#### `_one2many_link.py`

```python
"""One-to-many link (e.g. household → members, person → children)."""
from __future__ import annotations

import numpy

from ._link import Link


class One2ManyLink(Link):
    """A link where one source entity has many target entities.

    This is the inverse of a Many2OneLink.
    Examples: household.members, person.children
    """

    def __init__(self, name, field, target):
        super().__init__(name, field, target)

    def sum(self, source_population, target_population, array, role=None):
        """Sum values across linked entities. O(N) via bincount."""
        link_ids = target_population.get_holder(self.field).get_array()
        if role is not None:
            role_filter = target_population.members_role == role
            return numpy.bincount(
                link_ids[role_filter],
                weights=array[role_filter],
                minlength=source_population.count,
            )
        return numpy.bincount(
            link_ids, weights=array,
            minlength=source_population.count,
        )

    def count(self, source_population, target_population, role=None):
        """Count linked entities. O(N) via bincount."""
        link_ids = target_population.get_holder(self.field).get_array()
        if role is not None:
            role_filter = target_population.members_role == role
            link_ids = link_ids[role_filter]
        return numpy.bincount(link_ids, minlength=source_population.count)
```

### Tests Phase 1

```python
# tests/test_links_basic.py
import numpy as np
from openfisca_core.links import Many2OneLink, One2ManyLink


class TestMany2OneLink:
    def test_creation(self):
        link = Many2OneLink("mother", field="mother_id", target="person")
        assert link.name == "mother"
        assert link.field == "mother_id"
        assert link.target == "person"

    def test_get_follows_ids(self):
        """Verify that get() does fancy indexing correctly."""
        link = Many2OneLink("mother", field="mother_id", target="person")
        # mother_id = [2, 2, -1, 0, 0]
        # target salary = [3000, 2000, 1500, ...]
        # result should be [1500, 1500, 0, 3000, 3000]
        ...


class TestOne2ManyLink:
    def test_count(self):
        """Verify that count() uses bincount correctly."""
        ...

    def test_sum(self):
        """Verify that sum() uses bincount with weights."""
        ...
```

### Critère de sortie
Les classes Link existent, leurs tests unitaires passent,
**aucun test existent ne casse** (les Link ne sont pas encore branchés).

---

## Phase 2 : Enrichir country-template (1-2 jours)

**Objectif** : Ajouter des variables et des données de test qui utilisent
des lines intra-entité (mère, père, conjoint).

### Fichiers à créer/modifier dans country-template

#### 1. Nouvelles variables d'input : `variables/family_links.py`

```python
"""Variables defining family links between persons."""
from openfisca_core.periods import ETERNITY
from openfisca_core.variables import Variable

from openfisca_country_template.entities import Person


class mother_id(Variable):
    """ID of the person's mother (-1 if unknown)."""
    value_type = int
    default_value = -1
    entity = Person
    definition_period = ETERNITY
    label = "ID of the person's mother"


class father_id(Variable):
    """ID of the person's father (-1 if unknown)."""
    value_type = int
    default_value = -1
    entity = Person
    definition_period = ETERNITY
    label = "ID of the person's father"


class spouse_id(Variable):
    """ID of the person's spouse (-1 if not married)."""
    value_type = int
    default_value = -1
    entity = Person
    definition_period = ETERNITY
    label = "ID of the person's spouse"
```

#### 2. Enregistrer les lines : `entities.py` (modifié)

```python
from openfisca_core.entities import build_entity
from openfisca_core.links import Many2OneLink   # ← NOUVEAU

Household = build_entity(
    key="household",
    # ... inchangé ...
)

Person = build_entity(
    key="person",
    plural="persons",
    label="An individual.",
    is_person=True,
)

# ← NOUVEAU : déclarer les lines intra-entité
Person.add_link(Many2OneLink("mother", field="mother_id", target="person"))
Person.add_link(Many2OneLink("father", field="father_id", target="person"))
Person.add_link(Many2OneLink("spouse", field="spouse_id", target="person"))

entities = [Household, Person]
```

#### 3. Variables utilisant les lines : `variables/family_benefits.py`

```python
"""Variables that use family links."""
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_country_template.entities import Person


class mother_salary(Variable):
    """Salary of the person's mother."""
    value_type = float
    entity = Person
    definition_period = MONTH
    label = "Salary of the person's mother"

    def formula(person, period, _parameters):
        return person.mother("salary", period)


class parents_total_salary(Variable):
    """Combined salary of both parents."""
    value_type = float
    entity = Person
    definition_period = MONTH
    label = "Total salary of both parents"

    def formula(person, period, _parameters):
        mother_sal = person.mother("salary", period)
        father_sal = person.father("salary", period)
        return mother_sal + father_sal


class spouse_income_tax(Variable):
    """Income tax of the person's spouse."""
    value_type = float
    entity = Person
    definition_period = MONTH
    label = "Income tax paid by the person's spouse"

    def formula(person, period, _parameters):
        return person.spouse("income_tax", period)
```

#### 4. Tests YAML : `tests/family_links.yaml`

```yaml
- name: "Mother's salary"
  period: 2024-01
  input:
    persons:
      Alice:
        salary: 3000
      Bob:
        salary: 2000
      Charlie:
        mother_id: 0  # Alice
      Diana:
        mother_id: 0  # Alice
    households:
      h1:
        adults: [Alice, Bob]
        children: [Charlie, Diana]
  output:
    persons:
      Charlie:
        mother_salary: 3000
      Diana:
        mother_salary: 3000
      Alice:
        mother_salary: 0  # mother_id = -1 → 0

- name: "Parents total salary"
  period: 2024-01
  input:
    persons:
      Alice:
        salary: 3000
      Bob:
        salary: 2000
      Charlie:
        mother_id: 0
        father_id: 1
    households:
      h1:
        adults: [Alice, Bob]
        children: [Charlie]
  output:
    persons:
      Charlie:
        parents_total_salary: 5000

- name: "Spouse income tax"
  period: 2024-01
  input:
    persons:
      Alice:
        salary: 5000
        spouse_id: 1
      Bob:
        salary: 3000
        spouse_id: 0
    households:
      h1:
        adults: [Alice, Bob]
  output:
    persons:
      Alice:
        spouse_income_tax: 840  # Bob's tax = 3000 * 0.28
      Bob:
        spouse_income_tax: 1400  # Alice's tax = 5000 * 0.28
```

### Critère de sortie
Les variables `mother_id`, `father_id`, `spouse_id` existent comme inputs,
les variables `mother_salary`, `parents_total_salary`, `spouse_income_tax`
sont déclarées (mais ne fonctionnent pas encore — `person.mother` n'est
pas encore câblé).

---

## Phase 3 : Brancher les lines sur Population (2-3 jours)

**Objectif** : Faire fonctionner `person.mother("salary", period)` en
câblant les Link sur le mécanisme `__getattr__` de Population.

### Fichiers à modifier dans openfisca-core

#### 1. `entities/entity.py` — ajouter `add_link()`

```python
class Entity:
    _links: dict[str, Link] = {}

    def add_link(self, link):
        """Register a link on this entity."""
        link.source = self.key
        self._links[link.name] = link
```

#### 2. `populations/_core_population.py` — câbler `__getattr__`

```python
class CorePopulation:
    def __getattr__(self, name):
        # Vérifier si c'est un line déclaré
        link = self.entity._links.get(name)
        if link is not None:
            return LinkAccessor(link, self)
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
```

#### 3. `links/_accessor.py` — le proxy qui rend `person.mother(...)` possible

```python
class LinkAccessor:
    """Proxy returned by person.mother — makes person.mother("salary", p) work.

    Also supports chaining: person.mother.household("rent", p)
    """

    def __init__(self, link, source_population):
        self._link = link
        self._source_population = source_population

    def __call__(self, variable_name, period, **kwargs):
        """person.mother("salary", period) → follow the link."""
        target_population = self._source_population.simulation.populations[
            self._link.target]
        return self._link.get(
            self._source_population, target_population,
            variable_name, period,
        )

    def __getattr__(self, name):
        """person.mother.household → chain to another link/projector."""
        target_population = self._source_population.simulation.populations[
            self._link.target]
        # Delegate to the target population's attribute resolution
        target_attr = getattr(target_population, name)
        if isinstance(target_attr, LinkAccessor):
            # Chaîner les lines
            return ChainedLinkAccessor(self, target_attr)
        # C'est un projector existent (person.mother.household)
        # → il faut d'abord résoudre le line, puis projeter
        return RemappedProjector(self._link, self._source_population,
                                  target_attr)
```

### Ordre d'implémentation dans la phase

1. **`Entity.add_link()`** — simple dict, aucun risque
2. **`LinkAccessor.__call__`** — fait marcher `person.mother("salary", p)`
3. **Tests** — vérifier que les tests YAML de la Phase 2 passent
4. **`LinkAccessor.__getattr__`** — fait marcher le chaînage
5. **Tests chaînage** — `person.mother.household("rent", p)`

### Critère de sortie

```bash
# Les tests country-template passent TOUS
cd /home/benjello/projects/country-template
pytest openfisca_country_template/tests/ -x -q

# Y compris les nouveaux tests de lines
pytest openfisca_country_template/tests/family_links.yaml -v
```

---

## Phase 4 : Auto-génération des lines depuis GroupEntity (1-2 jours)

**Objectif** : Les lines `person.household` (actuellement via les
projectors) sont aussi générés automatiquement comme des `Link`.

### Ce qu'il faut faire

Lors de `build_entity()`, si c'est un `GroupEntity`, générer
automatiquement :
- Un `Many2OneLink("household", field="household_id", target="household")`
  sur Person
- Un `One2ManyLink("members", field="household_id", target="person")`
  sur Household

```python
# entities/helpers.py (modification de build_entity)
def build_entity(key, plural, label, ..., roles=None, is_person=False):
    if roles:
        entity = GroupEntity(key, plural, label, roles=roles)
        # Auto-generate links on the person entity → fait plus tard
        # quand le TBS est construit et qu'on connaît toutes les entités
    else:
        entity = Entity(key, plural, label, is_person=is_person)
    return entity
```

L'auto-génération se fait dans `TaxBenefitSystem.__init__()` quand
toutes les entités sont connues :

```python
# taxbenefitsystems/tax_benefit_system.py
class TaxBenefitSystem:
    def __init__(self, entities):
        # ... existent ...
        self._auto_generate_links()

    def _auto_generate_links(self):
        for entity in self.group_entities:
            # Sur Person : line Many2One vers le groupe
            self.person_entity.add_link(
                Many2OneLink(
                    name=entity.key,
                    field=f"{entity.key}_id",
                    target=entity.key,
                )
            )
            # Sur le groupe : line One2Many vers Person
            entity.add_link(
                One2ManyLink(
                    name="members",
                    field=f"{entity.key}_id",
                    target=self.person_entity.key,
                )
            )
```

### Critère de sortie

Les projectors existants continuent de fonctionner ET les nouvelles
variables utilisant la syntax line fonctionnent aussi :

```python
# Ces deux écritures donnent le même résultat :
household.sum(household.members("salary", p))  # ancien (projector)
household.links.members.sum("salary", p)       # nouveau (link)
```

---

## Phase 5 : Projectors comme façades (2-3 jours)

**Objectif** : Les projectors existants délèguent en interne aux Link,
sans casser l'API existante.

### Principe

```python
# EntityToPersonProjector (person.household) délègue à :
# → Many2OneLink("household").get(...)

class EntityToPersonProjector(Projector):
    def transform(self, result):
        # AVANT : self.reference_entity.project(result)
        # APRÈS : utilise le line sous-jacent
        link = self._find_link()
        if link:
            return link.project(result)
        return self.reference_entity.project(result)  # fallback
```

### Critère de sortie

1. **Tous les tests existants passent** (non-régression absolute)
2. Les projectors utilisent les lines en interne
3. L'API externe est identique

---

## Phase 6 : Tests d'intégration completes (1-2 jours)

### Scénarios de test

```python
# test_links_integration.py

class TestLinksIntegration:
    def test_mother_salary(self):
        """person.mother("salary", p) returns mother's salary."""

    def test_father_age(self):
        """person.father("age", p) returns father's age."""

    def test_spouse_symmetric(self):
        """person.spouse("salary") and reverse give consistent results."""

    def test_chained_mother_household(self):
        """person.mother.household("rent", p) chains two links."""

    def test_unknown_mother(self):
        """mother_id = -1 → default value (0)."""

    def test_projectors_unchanged(self):
        """Existing projector syntax gives same results as before."""

    def test_autogenerated_links(self):
        """Links auto-generated from GroupEntity work correctly."""

    def test_link_with_role_filter(self):
        """household.members.sum(salary, role=ADULT)."""

    def test_no_regression_country_template(self):
        """ALL existing country-template tests still pass."""
```

---

## Ordre optimal et dépendances

```
Phase 0 (préparation)
  │
  ▼
Phase 1 (classes Link)        Phase 2 (enrichir country-template)
  │                              │
  │   ← pas de dépendance →     │
  │                              │
  ▼                              ▼
Phase 3 (brancher sur Population)
  │   ← dépend de Phase 1 + 2
  ▼
Phase 4 (auto-génération)
  │   ← dépend de Phase 3
  ▼
Phase 5 (projectors = façades)
  │   ← dépend de Phase 4
  ▼
Phase 6 (tests d'intégration)
```

**Les Phases 1 et 2 sont indépendantes** : on peut travailler sur les
classes Link dans core ET enrichir country-template en parallèle.

## Estimation de l'effort

| Phase | Effort | Risque | Dépendance |
|---|---|---|---|
| Phase 0 : Préparation | 0.5 jour | Faible | — |
| Phase 1 : Classes Link | 2-3 jours | Faible (code isolé) | — |
| Phase 2 : Enrichir country-template | 1-2 jours | Faible | — |
| Phase 3 : Brancher sur Population | 2-3 jours | **Moyen** (`__getattr__`) | Phase 1+2 |
| Phase 4 : Auto-génération | 1-2 jours | Moyen | Phase 3 |
| Phase 5 : Projectors façades | 2-3 jours | **Élevé** (régression) | Phase 4 |
| Phase 6 : Tests intégration | 1-2 jours | Faible | Phase 5 |
| **Total** | **~10-16 jours** | | |

## Considérations importantes

### 1. Non-régression absolute

Chaque phase doit maintenir **100% des tests existants** verts.
Le risque principal est dans la Phase 5 (modification des projectors).
Pour minimiser ce risque :
- Les projectors font un **fallback** sur l'ancien code si le line
  n'est pas trouvé
- Les tests existants sont lancés à chaque commit

### 2. `__getattr__` est délicat

Le câblage `person.mother` via `__getattr__` sur `CorePopulation`
doit être soigneusement ordonné :
1. D'abord chercher dans les attributes normaux
2. Puis dans les lines déclarés
3. Puis dans les projectors existants
4. Sinon `AttributeError`

Le risque est de casser l'accès à des attributes qui fonctionnaient
avec les projectors. Il faut vérifier que le mécanisme existent
(`Projector.__getattr__`) passe en premier.

### 3. Le SimulationBuilder doit comprendre les `link_ids`

Quand on écrit un test YAML avec `mother_id: 0`, le
`SimulationBuilder` doit savoir qu'il faut mettre cette valeur
dans le Holder de `mother_id`. C'est déjà le cas car `mother_id`
est une Variable normal (int). Aucun changement nécessaire.

### 4. Les IDs dans les tests YAML

Dans les tests YAML, les personnes sont identifiées par leur position
(0, 1, 2...). Quand on écrit `mother_id: 0`, cela signifie
"la première personne déclarée". C'est cohérent avec le fonctionnement
actuel d'OpenFisca où les IDs sont les indices de position.

### 5. Enrichissements futurs de country-template

Après les lines familiaux de base, on pourra enrichir avec :
- `employer_id` → line person.employer (prépare les simulations firmes)
- formulas plus complexes utilisant les lines chaînés
- tests de scénarios avec des familles recomposées
