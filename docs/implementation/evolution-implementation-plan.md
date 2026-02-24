# Plan d'implémentation des populations dynamiques (évolution)

## Vue d'ensemble

### Ce qu'on veut pouvoir écrire

```python
from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_core.simulations import SimulationBuilder

tbs = CountryTaxBenefitSystem()
sim = SimulationBuilder().build_default_simulation(tbs, count=1000, dynamic=True)

# Charger les données initiales (2020)
sim.set_input("salary", "2020-01", initial_salaries)
sim.set_input("birth", "2020-01", initial_births)

# Calculer 2020
disposable_2020 = sim.calculate("disposable_income", "2020-01")

# --- Évoluer vers 2021 ---
sim.evolve("2021-01")

# Naissances : ajouter 50 personnes
sim.add_persons(50, data={
    "birth": dates_2021,
    "salary": numpy.zeros(50),
})
# Assigner les nouveaux-nés à des ménages
sim.set_members("household", new_person_ids, household_ids, role="child")

# Décès : retirer 30 personnes
sim.remove_persons(deceased_ids)

# Évolution salariale
old_salaries = sim.calculate("salary", "2020-01")
sim.set_input("salary", "2021-01", old_salaries * 1.03)

# Calculer 2021 (population modifiée)
disposable_2021 = sim.calculate("disposable_income", "2021-01")
```

### Ce qu'on a aujourd'hui dans country-template

| Élément | Existe ? | Suffisant pour tester ? |
|---|---|---|
| `Person` (is_person) | ✅ | ✅ |
| `Household` (Group, rôles adult/child) | ✅ | ✅ |
| `birth` (date, ETERNITY) | ✅ | ✅ |
| `age` (formule dépendant de birth) | ✅ | ✅ Parfait pour tester que les formules marchent après mutation |
| `salary` (input, MONTH) | ✅ | ✅ |
| `income_tax` (formule) | ✅ | ✅ |
| `disposable_income` (formule Household) | ✅ | ✅ Parfait pour tester les agrégations après mutation |
| `pension` (dépend de age) | ✅ | ✅ |
| `parenting_allowance` (dépend de nb_persons, ages) | ✅ | ✅ Parfait pour tester les mutations de composition |

**Le country-template est déjà suffisant** pour tester les fonctionnalités
de base. Mais il faut l'enrichir pour couvrir les scénarios dynamiques.

---

## Ce qu'il faut enrichir dans country-template

### 1. Variables d'évolution : `variables/evolution.py`

```python
"""Variables that model demographic evolution."""
from numpy import where
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_country_template.entities import Person, Household


class is_alive(Variable):
    """Whether the person is alive."""
    value_type = bool
    default_value = True
    entity = Person
    definition_period = MONTH
    label = "Whether the person is alive"


class salary_growth_rate(Variable):
    """Annual growth rate of salary."""
    value_type = float
    default_value = 0.02  # 2% par an
    entity = Person
    definition_period = MONTH
    label = "Annual salary growth rate"


class projected_salary(Variable):
    """Salary projected from the previous year with growth."""
    value_type = float
    entity = Person
    definition_period = MONTH
    label = "Projected salary based on previous period"

    def formula(person, period, parameters):
        previous_salary = person("salary", period.last_month)
        growth_rate = person("salary_growth_rate", period)
        monthly_rate = (1 + growth_rate) ** (1/12) - 1
        return previous_salary * (1 + monthly_rate)


class nb_children_in_household(Variable):
    """Number of children in the household."""
    value_type = int
    entity = Household
    definition_period = MONTH
    label = "Number of children in the household"

    def formula(household, period, _parameters):
        return household.nb_persons(Household.CHILD)


class child_benefit(Variable):
    """Benefit per child in household."""
    value_type = float
    entity = Household
    definition_period = MONTH
    label = "Benefit per child"

    def formula(household, period, parameters):
        nb_children = household("nb_children_in_household", period)
        # 100€ par enfant par mois
        return nb_children * parameters(period).benefits.child_benefit_amount
```

### 2. Paramètre : `parameters/benefits/child_benefit_amount.yaml`

```yaml
description: Amount of child benefit per child per month
values:
  2015-01-01:
    value: 100
metadata:
  unit: currency-EUR
```

### 3. Scénarios de test : `tests/evolution/`

```yaml
# tests/evolution/birth.yaml
- name: "Child benefit increases when a child is born"
  period: 2024-01
  description: >
    A household with 1 child gets 100€. After a birth (tested via
    dynamic mutation), it should get 200€.
  input:
    persons:
      Alice:
        birth: 1990-01-01
        salary: 3000
      Bob:
        birth: 1988-06-15
        salary: 2000
      Charlie:
        birth: 2020-03-01
    households:
      h1:
        adults: [Alice, Bob]
        children: [Charlie]
  output:
    households:
      h1:
        nb_children_in_household: 1
        child_benefit: 100
```

```yaml
# tests/evolution/salary_growth.yaml
- name: "Salary grows from one month to the next"
  period: 2024-02
  input:
    persons:
      Alice:
        salary:
          2024-01: 3000
        salary_growth_rate: 0.12  # 12% annual → ~1% monthly
    households:
      h1:
        adults: [Alice]
  output:
    persons:
      Alice:
        projected_salary: 3028.44  # 3000 * (1.12)^(1/12) ≈ 3028.44
```

---

## Phases d'implémentation dans openfisca-core

### Phase 0 : flag `dynamic=True` + frontière temporelle (1 jour)

**Objectif** : Ajouter le mode dynamique sans rien casser.

#### Fichiers à modifier

**`simulations/simulation.py`**

```python
class Simulation:
    def __init__(self, tax_benefit_system, populations, dynamic=False):
        # ... existant inchangé ...
        self._dynamic = dynamic
        self._settled_up_to = None  # frontière temporelle

    def calculate(self, variable_name, period):
        # Hook pour le déterminisme
        if self._dynamic:
            p = periods.period(period)
            if self._settled_up_to is None or p > self._settled_up_to:
                self._settled_up_to = p
        return self._calculate(variable_name, period)
```

**`errors.py`**

```python
class DeterminismError(Exception):
    """Raised when a population mutation would break calculation determinism."""
    pass
```

#### Tests

```python
def test_dynamic_flag_default_false():
    sim = Simulation(tbs, populations)
    assert sim._dynamic is False

def test_dynamic_flag_true():
    sim = Simulation(tbs, populations, dynamic=True)
    assert sim._dynamic is True
    assert sim._settled_up_to is None

def test_settled_frontier_advances():
    sim = Simulation(tbs, populations, dynamic=True)
    sim.calculate("salary", "2024-01")
    assert sim._settled_up_to == periods.period("2024-01")
    sim.calculate("salary", "2024-06")
    assert sim._settled_up_to == periods.period("2024-06")
```

#### Critère de sortie
- Tous les tests existants passent (le flag `dynamic=False` ne change rien)
- Le flag est accepté, la frontière avance

---

### Phase 1 : `evolve()` + vérification de déterminisme (1-2 jours)

**Objectif** : Implémenter `simulation.evolve(period)` avec le check
de déterminisme O(1).

#### Code

```python
class Simulation:
    def evolve(self, period):
        """Advance the simulation to a new period.

        Must be called BEFORE calculating variables for this period.
        Raises DeterminismError if calculations have already been done
        for this or a later period.
        """
        if not self._dynamic:
            raise ValueError("evolve() requires dynamic=True")

        p = periods.period(period)

        # Vérification O(1)
        if self._settled_up_to is not None and p <= self._settled_up_to:
            raise DeterminismError(
                f"Cannot evolve at {p}: calculations already done "
                f"up to {self._settled_up_to}. Call evolve() BEFORE "
                f"calculating variables for that period."
            )

        self._current_period = p

        # Snapshot la composition des groupes
        for pop in self.populations.values():
            if hasattr(pop, '_snapshot_composition'):
                pop._snapshot_composition(p)
```

#### Tests

```python
def test_evolve_before_calculate():
    """evolve() then calculate() works."""
    sim = build_dynamic_sim()
    sim.evolve("2024-01")
    result = sim.calculate("salary", "2024-01")
    assert result is not None

def test_calculate_then_evolve_same_period_fails():
    """calculate() then evolve() for same period raises."""
    sim = build_dynamic_sim()
    sim.calculate("salary", "2024-01")
    with pytest.raises(DeterminismError):
        sim.evolve("2024-01")

def test_calculate_then_evolve_earlier_fails():
    """calculate() for 2024-06 then evolve() for 2024-01 raises."""
    sim = build_dynamic_sim()
    sim.calculate("salary", "2024-06")
    with pytest.raises(DeterminismError):
        sim.evolve("2024-01")

def test_evolve_forward_works():
    """evolve() to strictly later period works."""
    sim = build_dynamic_sim()
    sim.calculate("salary", "2024-01")
    sim.evolve("2024-02")  # OK: 2024-02 > 2024-01
```

---

### Phase 2 : `add_persons()` + `remove_persons()` (3-4 jours)

**Objectif** : Pouvoir ajouter et retirer des individus de la simulation.

C'est la phase la plus complexe — elle touche aux arrays de toutes les
populations.

#### Code principal

**`populations/_core_population.py`**

```python
class CorePopulation:
    def add_persons(self, count, data=None):
        """Add persons to the population.

        Args:
            count: number of persons to add
            data: dict[variable_name, array] of initial values

        Returns:
            ndarray: IDs of the new persons
        """
        old_count = self.count
        new_count = old_count + count
        new_ids = numpy.arange(old_count, new_count)

        # Agrandir tous les holders
        for variable_name, holder in self._holders.items():
            holder._extend(count)

        # Mettre à jour le count
        self._count = new_count

        # Assigner les valeurs initiales
        if data:
            for var_name, values in data.items():
                self.simulation.get_holder(var_name).set_input(
                    self.simulation._current_period, values,
                    offset=old_count,
                )

        # Mettre à jour id_to_rownum
        self._update_id_to_rownum()

        return new_ids

    def remove_persons(self, ids):
        """Remove persons from the population.

        Args:
            ids: array of person IDs to remove
        """
        mask = numpy.ones(self.count, dtype=bool)
        mask[ids] = False

        # Filtrer tous les holders
        for variable_name, holder in self._holders.items():
            holder._filter(mask)

        # Mettre à jour le count
        self._count = mask.sum()

        # Mettre à jour id_to_rownum
        self._update_id_to_rownum()
```

**`holders/holder.py`**

```python
class Holder:
    def _extend(self, count):
        """Extend all stored arrays by count elements."""
        for period, array in self._storage._arrays.items():
            extended = numpy.zeros(len(array) + count, dtype=array.dtype)
            extended[:len(array)] = array
            self._storage._arrays[period] = extended

    def _filter(self, mask):
        """Keep only elements where mask is True."""
        for period, array in self._storage._arrays.items():
            self._storage._arrays[period] = array[mask]
```

**`populations/group_population.py`**

```python
class GroupPopulation:
    def set_members(self, new_person_ids, group_ids, role):
        """Assign persons to groups with a given role.

        Args:
            new_person_ids: IDs of persons to assign
            group_ids: IDs of groups to assign to
            role: role within the group
        """
        self._members_entity_id[new_person_ids] = group_ids
        role_obj = self.get_role(role) if isinstance(role, str) else role
        self._members_role[new_person_ids] = role_obj
        # Invalider le cache de members_position
        self._members_position = None
        self._ordered_members_map = None

    def _snapshot_composition(self, period):
        """Save composition for this period (for determinism)."""
        if not hasattr(self, '_composition_history'):
            self._composition_history = {}
        self._composition_history[period] = {
            'entity_id': self._members_entity_id.copy(),
            'role': self._members_role.copy(),
        }
```

#### Tests avec country-template

```python
class TestAddPersons:
    def test_add_persons_increases_count(self):
        sim = build_dynamic_sim(count=100)
        sim.evolve("2024-01")
        new_ids = sim.persons.add_persons(10)
        assert sim.persons.count == 110
        assert len(new_ids) == 10

    def test_add_persons_with_data(self):
        sim = build_dynamic_sim(count=100)
        sim.evolve("2024-01")
        births = numpy.full(10, numpy.datetime64("2024-01-01"))
        sim.persons.add_persons(10, data={"birth": births})
        ages = sim.calculate("age", "2024-06")
        assert ages[-10:].max() <= 1  # newborns are 0-1 year old

    def test_add_child_to_household(self):
        """Add a child → nb_children_in_household increases."""
        sim = build_2_adult_1_child_sim()
        sim.evolve("2024-02")
        new_ids = sim.persons.add_persons(1, data={
            "birth": [numpy.datetime64("2024-02-01")],
        })
        sim.populations["household"].set_members(
            new_ids, [0], role="child")
        nb = sim.calculate("nb_children_in_household", "2024-02")
        assert nb[0] == 2  # was 1, now 2

    def test_child_benefit_after_birth(self):
        """child_benefit increases after adding a child."""
        sim = build_2_adult_1_child_sim()
        benefit_before = sim.calculate("child_benefit", "2024-01")
        sim.evolve("2024-02")
        new_ids = sim.persons.add_persons(1, data={
            "birth": [numpy.datetime64("2024-02-01")],
        })
        sim.populations["household"].set_members(
            new_ids, [0], role="child")
        benefit_after = sim.calculate("child_benefit", "2024-02")
        assert benefit_after[0] == benefit_before[0] + 100


class TestRemovePersons:
    def test_remove_persons_decreases_count(self):
        sim = build_dynamic_sim(count=100)
        sim.evolve("2024-01")
        sim.persons.remove_persons([0, 1, 2])
        assert sim.persons.count == 97

    def test_death_removes_from_household(self):
        """Removing a person updates household composition."""
        sim = build_2_adult_1_child_sim()
        sim.evolve("2024-02")
        # Remove child (person 2)
        sim.persons.remove_persons([2])
        nb = sim.calculate("nb_children_in_household", "2024-02")
        assert nb[0] == 0  # child removed

    def test_pension_after_death(self):
        """After removing a retiree, pension is no longer counted."""
        sim = build_sim_with_retiree()
        total_pension_before = sim.calculate("pension", "2024-01").sum()
        sim.evolve("2024-02")
        sim.persons.remove_persons([retiree_id])
        total_pension_after = sim.calculate("pension", "2024-02").sum()
        assert total_pension_after < total_pension_before
```

#### Critère de sortie
- `add_persons` et `remove_persons` fonctionnent
- Les formules (y compris les agrégations ménage) donnent les bons résultats après mutation
- Tous les tests existants passent

---

### Phase 3 : Boucle multi-période (1-2 jours)

**Objectif** : Pouvoir exécuter une boucle complète evolve → mutate → calculate.

#### Helper dans country-template : `helpers/evolution_runner.py`

```python
"""Helper to run multi-period dynamic simulations."""

def run_evolution(simulation, start_year, end_year, evolution_fn):
    """Run a multi-period simulation with evolution.

    Args:
        simulation: a dynamic Simulation
        start_year: first year (e.g. 2020)
        end_year: last year (e.g. 2050)
        evolution_fn: function(sim, period) → applies mutations

    Returns:
        dict[period, dict[variable, array]]: results per period
    """
    results = {}
    for year in range(start_year, end_year + 1):
        period = f"{year}-01"

        if year > start_year:
            simulation.evolve(period)
            evolution_fn(simulation, period)

        results[period] = {
            "disposable_income": simulation.calculate(
                "disposable_income", period),
            "income_tax": simulation.calculate("income_tax", period),
            "population_count": simulation.persons.count,
        }

    return results
```

#### Test bout en bout

```python
def test_30_year_simulation():
    """Run a 30-year dynamic simulation."""
    tbs = CountryTaxBenefitSystem()
    sim = SimulationBuilder().build_default_simulation(
        tbs, count=1000, dynamic=True)
    sim.set_input("salary", "2020-01", numpy.random.uniform(1000, 5000, 1000))
    sim.set_input("birth", "2020-01", random_births(1000))

    def evolve_fn(sim, period):
        year = int(period[:4])
        # 1% salary growth
        old = sim.calculate("salary", f"{year-1}-01")
        sim.set_input("salary", period, old * 1.02)
        # 1% births
        n_births = sim.persons.count // 100
        if n_births > 0:
            new_ids = sim.persons.add_persons(n_births)
            # Assign to random households
            hh_ids = numpy.random.randint(0, 400, n_births)
            sim.populations["household"].set_members(
                new_ids, hh_ids, role="child")
        # 0.5% deaths (oldest first)
        ages = sim.calculate("age", period)
        n_deaths = sim.persons.count // 200
        oldest = numpy.argsort(ages)[-n_deaths:]
        sim.persons.remove_persons(oldest)

    results = run_evolution(sim, 2020, 2050, evolve_fn)

    # La population a évolué
    assert results["2050-01"]["population_count"] != 1000
    # Le revenu disponible total a changé
    assert (results["2050-01"]["disposable_income"].sum() !=
            results["2020-01"]["disposable_income"].sum())
```

---

### Phase 4 : Mémoire — éviction basique (1-2 jours)

**Objectif** : Pouvoir libérer les variables des périodes passées.

#### Code

```python
class Simulation:
    def gc_period(self, period, keep=None):
        """Free memory for variables at a given period.

        Args:
            period: the period to free
            keep: optional set of variable names to keep
        """
        keep = keep or set()
        for variable_name, holder in self.persons._holders.items():
            if variable_name not in keep:
                holder.delete(period)
        for pop in self.populations.values():
            for variable_name, holder in pop._holders.items():
                if variable_name not in keep:
                    holder.delete(period)
```

#### Test

```python
def test_gc_frees_memory():
    sim = build_dynamic_sim(count=100_000)
    sim.calculate("salary", "2024-01")
    mem_before = sim.get_memory_usage()["total_nb_bytes"]
    sim.gc_period("2024-01", keep={"salary"})
    mem_after = sim.get_memory_usage()["total_nb_bytes"]
    assert mem_after < mem_before
```

---

## Ordre optimal et dépendances

```
Phase 0 (1j)
flag dynamic + frontière
    │
    ▼
Phase 1 (1-2j)
evolve() + DeterminismError
    │
    ▼
Phase 2 (3-4j)                   Enrichir country-template (1-2j)
add/remove persons                  evolution.py, child_benefit,
    │                               tests/evolution/
    │     ← en parallèle →          │
    ▼                               ▼
Phase 3 (1-2j)
Boucle multi-période + test bout en bout
    │
    ▼
Phase 4 (1-2j)
GC / éviction mémoire
```

## Estimation de l'effort

| Phase | Effort | Risque | Ce qui est testé |
|---|---|---|---|
| Enrichir country-template | 1-2 jours | Faible | Variables d'évolution, child_benefit |
| Phase 0 : flag + frontière | 1 jour | Faible | dynamic=True, _settled_up_to |
| Phase 1 : evolve() + déterminisme | 1-2 jours | Faible | DeterminismError, workflow temporel |
| Phase 2 : add/remove persons | 3-4 jours | **Élevé** | Mutation arrays, reindexation |
| Phase 3 : boucle multi-période | 1-2 jours | Moyen | 30 ans bout en bout |
| Phase 4 : GC mémoire | 1-2 jours | Faible | gc_period(), memory_usage |
| **Total** | **~8-13 jours** | | |

## Considérations importantes

### 1. Le country-template est presque suffisant

Les variables existantes (`age`, `salary`, `income_tax`, `disposable_income`,
`parenting_allowance`, `nb_persons`) couvrent **tous les cas de test fondamentaux** :
- `age` teste que les formules fonctionnent après mutation (dépend de `birth`)
- `disposable_income` teste les agrégations ménage après mutation
- `parenting_allowance` teste les conditions sur `nb_persons` et `ages`

On n'a besoin de rajouter que :
- `is_alive` et `projected_salary` (variables d'évolution)
- `nb_children_in_household` et `child_benefit` (vérifier les mutations de composition)

### 2. L'ordre Phase 0 → 1 → 2 est strict

Il ne faut **pas** implémenter `add_persons` avant le mécanisme de
déterminisme, sinon on ne pourra pas détecter les violations.

### 3. La Phase 2 est la plus risquée

`add_persons` et `remove_persons` modifient la **taille** de tous les
arrays de la simulation. Les pièges :
- Les holders qui ont déjà des valeurs en cache pour d'autres périodes
  → il faut les étendre/filtrer aussi
- `members_entity_id`, `members_role`, `members_position` dans les
  GroupPopulation → il faut les mettre à jour
- `members_position` doit être recalculé (invalidation du cache)
- Les formules qui utilisent `period.last_month` ou `ADD` → les arrays
  de périodes précédentes ont une taille différente !

### 4. Taille variable des arrays entre périodes

C'est le problème le plus subtil : si on calcule `salary` en 2024
(1M personnes) puis en 2025 (1.05M personnes), l'ADD `salary("2024", ADD)`
appelé depuis 2025 retournera un array de taille 1M, pas 1.05M.

**Solution** : les nouvelles personnes (nées en 2025) n'avaient pas de
salaire en 2024, donc on remplit avec la `default_value`. Le holder doit
gérer le padding :

```python
def get_array(self, period):
    array = self._storage.get(period)
    if array is not None and len(array) < self.population.count:
        # Padding pour les nouvelles personnes
        padded = numpy.full(self.population.count, self.variable.default_value,
                             dtype=array.dtype)
        padded[:len(array)] = array
        return padded
    return array
```

### 5. Relation avec le plan des liens

Les populations dynamiques et les liens sont **complémentaires** :
- Les liens (`mother_id`) permettent de modéliser les relations familiales
- Les mutations dynamiques permettent de les faire **évoluer** :
  - Naissance → `add_persons` + `set mother_id`
  - Mariage → `set spouse_id`
  - Divorce → `remove spouse_id`, potentiellement `create new household`

L'idéal est d'implémenter les liens (Phase 1-3 du plan liens) AVANT
les populations dynamiques, car les mutations dynamiques manipulent
des liens.

### 6. Priorité recommandée entre les deux plans

```
1. Liens Phase 1-3 (classes Link + country-template + branchement)
   → 6-8 jours
2. Évolution Phase 0-1 (flag + evolve + déterminisme)
   → 2-3 jours
3. Évolution Phase 2 (add/remove persons)
   → 3-4 jours
4. Liens Phase 4-5 (auto-génération + façades)
   → 3-5 jours
5. Évolution Phase 3-4 (boucle multi-période + GC)
   → 2-4 jours
```

**Total combiné : ~16-24 jours** pour les deux fonctionnalités.
