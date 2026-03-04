# Analyse détaillée des codebases : OpenFisca-core et LIAM2

> Document de référence pour le PoC « populations dynamiques ».
> Contient les chemins exacts, structures de classes, numéros de ligne
> et extraits de code pertinents des deux projects.
>
> **Date d'analyse** : 2026-02-22
> **Projects analysés** :
> - OpenFisca-core : `/home/benjello/projects/openfisca-core`
> - LIAM2 : `/home/benjello/projects/liam2`

---

## Table des matières

1. [OpenFisca-core : Architecture des populations](#1-openfisca-core--architecture-des-populations)
2. [OpenFisca-core : Simulation et calcul](#2-openfisca-core--simulation-et-calcul)
3. [OpenFisca-core : Stockage des données (Holders)](#3-openfisca-core--stockage-des-données-holders)
4. [LIAM2 : Architecture des entités](#4-liam2--architecture-des-entités)
5. [LIAM2 : Système d'indexation id_to_rownum](#5-liam2--système-dindexation-id_to_rownum)
6. [LIAM2 : Opérations dynamiques (ajout/suppression)](#6-liam2--opérations-dynamiques-ajoutsuppression)
7. [LIAM2 : Boucle temporelle](#7-liam2--boucle-temporelle)
8. [Cartographie des dépendances pour le PoC](#8-cartographie-des-dépendances-pour-le-poc)

---

## 1. OpenFisca-core : Architecture des populations

### 1.1 Hiérarchie de classes

```
CorePopulation         (_core_population.py)
├── Population         (population.py)        — entités « personne » (SingleEntity)
└── GroupPopulation    (group_population.py)   — entités groupe (ménage, foyer fiscal, etc.)
        ↑ hérite de Population

CoreEntity             (_core_entity.py)
├── Entity             (entity.py)            — alias SingleEntity, is_person=True
└── GroupEntity         (group_entity.py)      — is_person=False, possède des rôles
```

### 1.2 `CorePopulation` — `/openfisca_core/populations/_core_population.py`

**Total : 456 lignes**

#### Attributes clés (lignes 34-48)
```python
class CorePopulation:
    count: int = 0                          # L35 — FIXE, taille de la population
    entity: t.CoreEntity                    # L38
    ids: Sequence[str] = []                 # L41 — FIXE, identifiants
    simulation: None | t.Simulation = None  # L44

    def __init__(self, entity, *__args, **__kwds):  # L46-48
        self.entity = entity
        self._holders: t.HolderByVariable = {}
```

#### Méthodes importantes

| Méthode | Lignes | Rôle | Impact PoC |
|---|---|---|---|
| `__call__()` | 50-169 | Calcule une variable pour une période | ⚠️ Utilise `check_period_validity` |
| `empty_array()` | 171-193 | `numpy.zeros(self.count)` | 🔴 Dépend de `count` fixe |
| `filled_array()` | 195-230 | `numpy.full(self.count, value)` | 🔴 Dépend de `count` fixe |
| `get_index(id)` | 232-258 | `self.ids.index(id)` | ⚠️ Recherche linéaire dans ids |
| `check_array_compatible_with_entity()` | 262-293 | Vérifie `array.size == self.count` | 🔴 **Bloquant** pour populations dynamiques |
| `get_holder()` | 337-389 | Récupère/crée un Holder pour une variable | ✅ OK |
| `get_memory_usage()` | 391-452 | Statistiques mémoire | ✅ OK |

### 1.3 `Population` — `/openfisca_core/populations/population.py`

**Total : 143 lignes** — Pour les entités « personne »

#### Méthodes importantes

| Méthode | Lignes | Rôle | Impact PoC |
|---|---|---|---|
| `__init__()` | 12-13 | Appelle `super().__init__(entity)` | ✅ |
| `clone()` | 15-24 | Copie la population pour une nouvelle simulation. **Copie `count` et `ids`** | ⚠️ Devra copier aussi les structures dynamiques |
| `__getattr__()` | 26-36 | Résolution des projectors (ex: `person.household`) | ✅ |
| `has_role()` | 40-61 | Vérifie le rôle d'une personne dans un GroupEntity | ✅ |
| `value_from_partner()` | 63-86 | Valeur du partenaire | ✅ |
| `get_rank()` | 88-142 | Rang dans l'entité selon un critère | ⚠️ Utilise `members_position`, `members_entity_id` |

### 1.4 `GroupPopulation` — `/openfisca_core/populations/group_population.py`

**Total : 320 lignes** — Pour les entités groupe (ménage, etc.)

#### Attributes clés (lignes 14-20)
```python
class GroupPopulation(Population):
    def __init__(self, entity: t.GroupEntity, members: t.Members):
        super().__init__(entity)
        self.members = members                     # L16 — Référence vers Population des personnes
        self._members_entity_id = None             # L17 — Mapping personne → entité groupe
        self._members_role = None                  # L18 — Rôle de chaque personne
        self._members_position = None              # L19 — Position dans l'entité
        self._ordered_members_map = None           # L20 — Cache pour argsort
```

#### Propriétés de mapping (lignes 36-82)

- **`members_position`** (L36-53) : Calculé paresseusement depuis `members_entity_id`. Compteur par entité.
- **`members_entity_id`** (L55-61) : Getter/setter simple.
- **`members_role`** (L63-73) : Si None, initialise avec le premier rôle. Setter convertit en numpy array.
- **`ordered_members_map`** (L75-82) : `numpy.argsort(self.members_entity_id)` — utilisé par `value_nth_person`.

#### Méthodes d'agrégation (lignes 94-319)

| Méthode | Lignes | Rôle | Dépendances |
|---|---|---|---|
| `sum()` | 94-119 | Some par entité via `bincount` | `members_entity_id`, `self.count` |
| `any()` | 121-138 | Vrai si au moins un membre vérifie | `sum()` |
| `reduce()` | 140-160 | Réduction générique | `members_position`, `value_nth_person()` |
| `all()` | 162-183 | Vrai si tous les membres vérifient | `reduce()` |
| `max()` | 185-206 | Maximum par entité | `reduce()` |
| `min()` | 208-233 | Minimum par entité | `reduce()` |
| `nb_persons()` | 235-249 | Nombre de personnes par entité | `members_entity_id`, `members_role` |
| `value_from_person()` | 253-279 | Valeur d'un rôle unique | `ordered_members_map`, `has_role()` |
| `value_nth_person()` | 281-305 | Valeur de la n-ème personne | `ordered_members_map`, `members_position` |
| `value_from_first_person()` | 307-309 | Alias pour `value_nth_person(0, ...)` | |
| `project()` | 313-319 | Projection entité → personne via `array[members_entity_id]` | `members_entity_id` |

**Point critique** : `sum()` utilise `numpy.bincount(self.members_entity_id, weights=array)` sans `minlength`. En mode dynamique, il faudra ajouter `minlength=self.count`.

### 1.5 `Entity` (SingleEntity) — `/openfisca_core/entities/entity.py`

**Total : 62 lignes**

```python
class Entity(CoreEntity):
    is_person: ClassVar[bool] = True

    def __init__(self, key, plural, label, doc):
        self.key = t.EntityKey(key)          # ex: "person"
        self.plural = t.EntityPlural(plural)  # ex: "persons"
        self.label = label
        self.doc = textwrap.dedent(doc)
```

### 1.6 `GroupEntity` — `/openfisca_core/entities/group_entity.py`

**À explorer si besoin** — Contient la définition des rôles (PARENT, CHILD, etc.)

### 1.7 Projectors — `/openfisca_core/projectors/`

Fichiers :
- `entity_to_person_projector.py` — Projection entité → personne
- `first_person_to_entity_projector.py` — Première personne → entité
- `unique_role_to_entity_projector.py` — Rôle unique → entité

Ces projectors sont utilisés via `person.household`, etc. Ils dépendent de `GroupPopulation` et sont **transparents** pour le PoC (ils utilisent les méthodes de GroupPopulation qui seront adaptées).

---

## 2. OpenFisca-core : Simulation et calcul

### 2.1 `Simulation` — `/openfisca_core/simulations/simulation.py`

**Total : 617 lignes**

#### `__init__()` (lignes 34-62)
```python
def __init__(self, tax_benefit_system, populations):
    self.tax_benefit_system = tax_benefit_system
    self.populations = populations
    self.persons = self.populations[tax_benefit_system.person_entity.key]
    self.link_to_entities_instances()   # L76-78 : met simulation sur chaque population
    self.create_shortcuts()             # L80-83 : simulation.person = populations["person"]
    self.invalidated_caches = set()
    self.debug = False
    self.trace = False
    self.tracer = tracers.SimpleTracer()
    self.opt_out_cache = False
    self.max_spiral_loops: int = 1
    self.memory_config = None
    self._data_storage_dir = None
    self.start_computation_period = None
```

#### `_calculate()` (lignes 121-169)
```python
def _calculate(self, variable_name, period):
    population = self.get_variable_population(variable_name)
    holder = population.get_holder(variable_name)
    variable = self.tax_benefit_system.get_variable(variable_name, check_existence=True)
    self._check_period_consistency(period, variable)

    # 1. Chercher dans le cache
    cached_array = holder.get_array(period)
    if cached_array is not None:
        return cached_array

    # 2. Exécuter la formule
    self._check_for_cycle(variable.name, period)
    array = self._run_formula(variable, population, period)

    # 3. Valeur par défaut si pas de formule
    if array is None:
        array = holder.default_array()  # ← numpy.full(population.count, default)

    array = self._cast_formula_result(array, variable)
    holder.put_in_cache(array, period)
    return array
```

**Point critique** : `holder.default_array()` utilise `self.population.count`. En mode dynamique, ce count devra correspondre à la population de la période en cours.

#### `set_input()` (lignes 518-548)
```python
def set_input(self, variable_name, period, value):
    variable = self.tax_benefit_system.get_variable(variable_name, check_existence=True)
    period = periods.period(period)
    self.get_holder(variable_name).set_input(period, value)
```

### 2.2 `SimulationBuilder` — `/openfisca_core/simulations/simulation_builder.py`

**Total : 858 lignes**

#### Méthodes clés pour l'initialisation des populations

| Méthode | Lignes | Ce qu'elle fait |
|---|---|---|
| `build_from_dict()` | 73-155 | Point d'entrée principal, dispatche vers `build_from_entities` ou `build_from_variables` |
| `build_from_entities()` | 157-270 | Construit depuis un dict complete (personnes + ménages explicites) |
| `build_from_variables()` | 272-310 | Construit depuis des variables seules (infère la structure) |
| `build_default_simulation()` | 312-331 | Simulation par défaut : N personnes, N ménages de 1 personne |
| `create_entities()` | 333-334 | Appelle `tax_benefit_system.instantiate_entities()` |
| `declare_person_entity()` | 336-341 | **Fixe `count` et `ids`** pour les personnes |
| `declare_entity()` | 343-347 | **Fixe `count` et `ids`** pour les entités groupe |
| `join_with_persons()` | 352-377 | **Fixe `members_entity_id` et `members_role`** |

#### `declare_person_entity()` — Le point où count est fixé (L336-341)
```python
def declare_person_entity(self, person_singular, persons_ids):
    person_instance = self.populations[person_singular]
    person_instance.ids = numpy.array(list(persons_ids))
    person_instance.count = len(person_instance.ids)   # ← FIXÉ ICI
    self.persons_plural = person_instance.entity.plural
```

#### `join_with_persons()` — Le point où les memberships sont fixés (L352-377)
```python
def join_with_persons(self, group_population, persons_group_assignment, roles):
    group_sorted_indices = numpy.unique(persons_group_assignment, return_inverse=True)[1]
    group_population.members_entity_id = numpy.argsort(group_population.ids)[group_sorted_indices]
    # ... assignation des rôles ...
```

### 2.3 `_BuildDefaultSimulation` — `/openfisca_core/simulations/_build_default_simulation.py`

**Total : 160 lignes**

Pattern builder qui enchaîne `.add_count().add_ids().add_members_entity_id()` :

```python
# L90 : for population in self.populations.values(): population.count = self.count
# L122 : for population in self.populations.values(): population.ids = numpy.array(range(self.count))
# L159 : for population: population.members_entity_id = numpy.array(range(self.count))
```

---

## 3. OpenFisca-core : Stockage des données (Holders)

### 3.1 `Holder` — `/openfisca_core/holders/holder.py`

**Total : 326 lignes**

#### `__init__()` (L27-46)
```python
def __init__(self, variable, population):
    self.population = population
    self.variable = variable
    self.simulation = population.simulation
    self._eternal = self.variable.definition_period == periods.DateUnit.ETERNITY
    self._memory_storage = storage.InMemoryStorage(is_eternal=self._eternal)
    self._disk_storage = None
    self._on_disk_storable = False
    self._do_not_store = False
    # ... configuration mémoire ...
```

#### Méthodes clés

| Méthode | Lignes | Ce qu'elle fait | Impact PoC |
|---|---|---|---|
| `get_array(period)` | 83-95 | Récupère depuis `_memory_storage` ou `_disk_storage` | 🔴 Doit remapper en mode dynamique |
| `set_input(period, array)` | 166-240 | Valid et stocke une entrée | ⚠️ Vérification de taille implicite |
| `_to_array(value)` | 242-263 | Convertit en numpy array du bon type | ✅ |
| `_set(period, value)` | 265-308 | Stocke dans memory ou disk storage | ✅ |
| `put_in_cache(value, period)` | 310-321 | Stocke un résultat calculé | ✅ |
| `default_array()` | 323-325 | `self.variable.default_array(self.population.count)` | 🔴 Dépend de `count` |
| `delete_arrays(period)` | 74-81 | Supprime du cache | ✅ |
| `clone(population)` | 48-60 | Copie le holder | ⚠️ |

#### `_set()` — Contrainte de taille (L265-308)
```python
def _set(self, period, value):
    value = self._to_array(value)
    if not self._eternal:
        if self.variable.definition_period != period.unit or period.size > 1:
            raise errors.PeriodMismatchError(...)
    # Stocke dans memory ou disk storage
    if should_store_on_disk:
        self._disk_storage.put(value, period)
    else:
        self._memory_storage.put(value, period)
```

**Note** : `_set()` ne vérifie PAS la taille de l'array ! C'est `check_array_compatible_with_entity()` qui le fait, mais il n'est pas appelé systématiquement dans `_set()`. La vérification est dans `set_input()` via `_to_array()` → L257 : `numpy.array(value, dtype=...)`.

### 3.2 `InMemoryStorage` — `/openfisca_core/data_storage/in_memory_storage.py`

**Total : 199 lignes**

Structure très simple : un dictionnaire `{Period: ndarray}`.

```python
class InMemoryStorage:
    _arrays: MutableMapping[Period, Array]    # L25

    def get(self, period) -> Array | None:     # L31-65    — lookup dans _arrays
    def put(self, value, period) -> None:      # L67-94    — _arrays[period] = value
    def delete(self, period=None) -> None:     # L96-143   — supprime du dict
    def get_known_periods(self) -> KeysView:   # L145-166
    def get_memory_usage(self) -> dict:        # L168-195
```

**Point important** : Le storage ne sait rien de la population. Il stocke bêtement des arrays par période. Le remapping devra être fait **dans le Holder**, pas dans le storage.

---

## 4. LIAM2 : Architecture des entités

### 4.1 `Entity` — `/liam2/liam2/entities.py`

**Total : 812 lignes**

#### `__init__()` (lignes 162-253) — Structure complète
```python
class Entity(object):
    def __init__(self, name, fields=None, links=None, macro_strings=None,
                 process_strings=None, array=None):
        self.name = name                           # L175

        # Champs obligatoires ajoutés si absents :
        # 'id' (int) et 'period' (int)             # L201-204
        self.fields = fields                        # L205
        self.links = links                          # L206

        self.expectedrows = tables.parameters.EXPECTED_ROWS_TABLE  # L215
        self.table = None                           # L216 — table HDF5 de sortie
        self.input_table = None                     # L217

        self.indexed_input_table = None             # L219
        self.indexed_output_table = None            # L220

        self.input_rows = {}                        # L222 — {period: (start, stop)}
        self.input_index = {}                       # L227 — {period: id_to_rownum}
        self.output_rows = {}                       # L229 — {period: (start, stop)}
        self.output_index = {}                      # L230 — {period: id_to_rownum}
        self.output_index_node = None               # L231

        self.base_period = None                     # L233
        self.array_period = array_period            # L236 — période courante du array
        self.array = array                          # L237 — ★ ColumnArray redimensionnable

        self.lag_fields = []                        # L239
        self.array_lag = None                       # L240

        self.num_tmp = 0                            # L242
        self.temp_variables = {}                    # L243
        self.id_to_rownum = None                    # L244 — ★ MAPPING CENTRAL

        if array is not None:                       # L245-251
            rows_per_period, index_per_period = index_table(array)
            self.input_rows = rows_per_period
            self.output_rows = rows_per_period
            self.input_index = index_per_period
            self.output_index = index_per_period
            self.id_to_rownum = index_per_period[array_period]
```

### 4.2 `ColumnArray` — `/liam2/liam2/data.py` (lignes 68-264)

Stockage par colonnes, chaque champ est un numpy array séparé.

#### Méthodes clés
```python
class ColumnArray:
    def __init__(self, array=None):                 # L69-89
        # columns = {name: numpy_array, ...}

    def __getitem__(self, key):                     # L91-100  — accès par nom de champ
    def __setitem__(self, key, value):              # L102-132 — assignation

    def keep(self, key):                            # L171-177 — ★ FILTRAGE (suppression)
        # key = masque booléen ou indices
        for name, column in self.columns.items():
            self.columns[name] = column[key]

    def append(self, array):                        # L179-184 — ★ EXTENSION (ajout)
        for name, column in self.columns.items():
            self.columns[name] = np.concatenate((column, array[name]))

    @classmethod
    def empty(cls, length, dtype):                  # L189-195 — Création vide
    @classmethod
    def from_table(cls, table, start, stop):        # L197-221 — Depuis table HDF5
```

### 4.3 `Field` et `FieldCollection` — `/liam2/liam2/entities.py` (lignes 87-158)

```python
class Field:
    name: str
    dtype: type
    default_value: any
    input: bool      # présent dans les données d'entrée ?
    output: bool     # à écrire en sortie ?

class FieldCollection(list):
    @property
    def names(self): ...        # Noms des champs
    @property
    def name_types(self): ...   # [(name, type), ...]
    @property
    def dtype(self): ...        # np.dtype composé
    @property
    def default_values(self): ...  # {name: default_value}
```

### 4.4 `Link` (Many2One, One2Many) — `/liam2/liam2/links.py`

```python
class Link:                                         # L19-58
    _name: str
    _link_field: str              # nom du champ de liaison (ex: "household_id")
    _target_entity_name: str      # nom de l'entité cible
    _target_entity: Entity        # résolu après parsing

class Many2One(Link):                               # L61-76
    # person.household.income → valeur de income pour le ménage de la personne
    def get(self, key, *args, **kwargs): ...

class One2Many(Link):                               # L79-93
    # household.persons.count() → nombre de personnes du ménage
    def count(self, ...): ...
    def sum(self, ...): ...
```

**Analogie OpenFisca** : `Many2One` ≈ `person.household` (projector), `One2Many` ≈ `household.members` (GroupPopulation).

---

## 5. LIAM2 : Système d'indexation id_to_rownum

### 5.1 `index_table()` — `/liam2/liam2/data.py` (lignes 617-658)

Construit les index à partir d'une table triée par période :

```python
def index_table(table):
    """
    table : itérable de lignes avec colonnes 'period' et 'id', trié par période.
    Retourne : (rows_per_period, id_to_rownum_per_period)
    """
    rows_per_period = {}          # {period: (start_row, end_row)}
    id_to_rownum_per_period = {}  # {period: ndarray}

    # Pour chaque ligne :
    #   - Si nouvelle période : sauvegarder l'index de la période précédente
    #   - temp_id_to_rownum[row_id] = idx - start_row
    #   - Vérifier les doublons

    # Le résultat est un ndarray de taille max_id+1
    # où id_to_rownum[id] = position dans le tableau pour cette période
    # et id_to_rownum[id] = -1 si l'id n'existe pas pour cette période
```

### 5.2 `build_period_array()` — `/liam2/liam2/data.py` (lignes 541-614)

Construit le tableau de données pour une période de départ en fusionnant les données de toutes les périodes antérieures :

```python
def build_period_array(input_table, fields_to_keep, output_fields,
                       input_rows, input_index, start_period, default_values):
    # 1. Trouver toutes les périodes <= start_period
    # 2. Calculer is_present : qui est présent dans au moins une période
    # 3. Construire id_to_rownum pour la période cible
    # 4. Pour chaque période (en ordre inverse) :
    #    - Trouver les individus dont la source n'est pas encore connue
    #    - Les remplir depuis cette période
    # 5. Lire les données et retourner (output_array, id_to_rownum)
```

### 5.3 `EntityContext.id_to_rownum` — `/liam2/liam2/context.py` (lignes 280-292)

Sélection du bon index selon la période courante :

```python
@property
def id_to_rownum(self):
    period = self.eval_ctx.period
    if self.is_array_period:
        return self.entity.id_to_rownum      # période courante
    elif period in self.entity.output_index:
        return self.entity.output_index[period]  # période simulée passée
    else:
        return self.entity.input_index[period]   # période d'entrée
```

### 5.4 `flush_index()` — `/liam2/liam2/entities.py` (lignes 707-724)

Sauvegarde de l'index en fin de période :

```python
def flush_index(self, period):
    # Sauvegarder en mémoire
    self.output_index[period] = self.id_to_rownum

    # Sauvegarder sur disque (HDF5)
    h5file.create_array(self.output_index_node, "_%d" % period,
                        self.id_to_rownum, "Period %d index" % period)

    # Libérer l'index de la période précédente (pointer vers le disque)
    prev_disk_array = getattr(self.output_index_node, '_%d' % (period - 1))
    self.output_index[period - 1] = DiskBackedArray(prev_disk_array)
```

---

## 6. LIAM2 : Opérations dynamiques (ajout/suppression)

### 6.1 `add_individuals()` — `/liam2/liam2/exprmisc.py` (lignes 199-241)

```python
def add_individuals(target_context, children):
    target_entity = target_context.entity
    id_to_rownum = target_entity.id_to_rownum
    array = target_entity.array
    num_rows = len(array)
    num_birth = len(children)

    # 1. Étendre le tableau de données
    target_entity.array.append(children)  # ColumnArray.append()

    # 2. Étendre les variables temporaires
    for name, temp_value in temp_variables.items():
        if isinstance(temp_value, np.ndarray) and temp_value.shape == (num_rows,):
            extra = get_default_vector(num_birth, temp_value.dtype)
            temp_variables[name] = np.concatenate((temp_value, extra))

    # 3. Étendre les variables extra du contexte
    for name, temp_value in extra_variables.items():
        if isinstance(temp_value, np.ndarray) and temp_value.shape:
            extra = get_default_vector(num_birth, temp_value.dtype)
            extra_variables[name] = np.concatenate((temp_value, extra))

    # 4. Mettre à jour id_to_rownum
    id_to_rownum_tail = np.arange(num_rows, num_rows + num_birth)
    target_entity.id_to_rownum = np.concatenate(
        (id_to_rownum, id_to_rownum_tail))
```

### 6.2 `New.compute()` — `/liam2/liam2/exprmisc.py` (lignes 258-338)

Orchestration de la création de nouveaux individus :

```python
def compute(self, context, entity_name=None, filter=None, number=None, **kwargs):
    # 1. Déterminer qui donne naissance (filtre) ou combien (nombre)
    # 2. Créer un sous-tableau avec les valeurs par défaut
    # 3. Attribuer les nouveaux IDs :
    #    children['id'] = np.arange(num_individuals, num_individuals + num_birth)
    # 4. Définir la période :
    #    children['period'] = context.period
    # 5. Appliquer les kwargs (valeurs d'initialisation)
    # 6. Appeler add_individuals(target_context, children)
    # 7. Invalider le cache d'expressions
    # 8. Retourner les IDs des nouveaux individus
```

### 6.3 `RemoveIndividuals` — `/liam2/liam2/actions.py` (lignes 83-142)

```python
class RemoveIndividuals(FunctionExpr):
    def compute(self, context, filter=None):
        not_removed = ~filter_value
        entity = context.entity
        len_before = len(entity.array)

        # 1. Filtrer le tableau principal
        entity.array.keep(not_removed)

        # 2. Filtrer les variables temporaires
        for name, temp_value in temp_variables.items():
            if isinstance(temp_value, np.ndarray) and len(temp_value) == len_before:
                temp_variables[name] = temp_value[not_removed]

        # 3. Recalculer id_to_rownum
        already_removed = entity.id_to_rownum == -1
        already_removed_indices = filter_to_indices(already_removed)
        already_removed_indices_shifted = \
            already_removed_indices - np.arange(len(already_removed_indices))

        id_to_rownum = np.arange(len_before)
        id_to_rownum -= filter_value.cumsum()
        id_to_rownum[filter_value] = -1
        entity.id_to_rownum = np.insert(id_to_rownum,
                                        already_removed_indices_shifted, -1)

        # 4. Invalider le cache
        expr_cache.invalidate(context.period, context.entity_name)
```

**Point subtil** : Le recalcul de `id_to_rownum` après suppression est complexe car il faut :
- Décrémenter les positions des survivants (cumsum)
- Ré-insérer les `-1` pour les individus déjà supprimés avant cette période
- Ne pas réduire la taille de `id_to_rownum` (les IDs passés y restent)

---

## 7. LIAM2 : Boucle temporelle

### 7.1 `simulate_period()` — `/liam2/liam2/simulation.py` (lignes 530-621)

```python
def simulate_period(period_idx, period, processes, entities, init=False):
    # 1. Fixer la période courante
    eval_ctx.period = period

    # 2. Charger les données de la période
    if not init:
        for entity in entities:
            entity.load_period_data(period)  # ← merge_arrays + update id_to_rownum

    # 3. Mettre à jour le champ 'period' dans les arrays
    for entity in entities:
        entity.array_period = period
        entity.array['period'] = period

    # 4. Exécuter les processus séquentiellement
    for process_def in processes:
        process, periodicity = process_def
        eval_ctx.entity_name = process.entity.name
        if period_idx % periodicity == 0:
            process.run_guarded(eval_ctx)

    # 5. Stocker les données de la période
    for entity in entities:
        entity.store_period_data(period)  # ← flush_index + écriture HDF5
```

### 7.2 `Entity.load_period_data()` — `/liam2/liam2/entities.py` (lignes 647-681)

```python
def load_period_data(self, period):
    # 1. Sauvegarder les champs lag
    if self.lag_fields:
        self.array_lag = np.empty(len(self.array), dtype=np.dtype(self.lag_fields))
        for field, _ in self.lag_fields:
            self.array_lag[field] = self.array[field]

    # 2. Vérifier si des données existent pour cette période
    rows = self.input_rows.get(period)
    if rows is None:
        return

    # 3. Fusionner les nouvelles données
    start, stop = rows
    input_array = self.input_table.read(start, stop)
    self.array, self.id_to_rownum = merge_arrays(
        self.array, input_array,
        result_fields='array1',
        default_values=self.fields.default_values
    )
```

### 7.3 `Entity.store_period_data()` — `/liam2/liam2/entities.py` (lignes 726-747)

```python
def store_period_data(self, period):
    # 1. Purger les variables temporaires
    self.temp_variables = {}

    # 2. Écrire dans la table HDF5
    if self.table is not None:
        startrow = self.table.nrows
        self.array.append_to_table(self.table)
        self.output_rows[period] = (startrow, self.table.nrows)
        self.flush_index(period)  # ← sauvegarde id_to_rownum
        self.table.flush()
```

---

## 8. Cartographie des dépendances pour le PoC

### 8.1 Fichiers OpenFisca à modifier (par priorité)

```
Priorité 1 (Phase 0-1) :
  openfisca_core/populations/_core_population.py    ← count/ids → propriétés + attributes dynamiques
  openfisca_core/simulations/simulation.py          ← flag dynamic + current_period

Priorité 2 (Phase 2) :
  openfisca_core/populations/population.py          ← add_individuals(), remove_individuals()
  openfisca_core/holders/holder.py                  ← _extend_arrays(), _shrink_arrays(), get_array() adapté

Priorité 3 (Phase 3) :
  openfisca_core/populations/group_population.py    ← add_members(), remove_members(), index par période

Priorité 4 (Phase 4-6) :
  openfisca_core/simulations/simulation_builder.py  ← paramètre dynamic
  openfisca_core/simulations/_build_default_simulation.py
```

### 8.2 Fichiers OpenFisca à NE PAS modifier (le PoC ne les touche pas)

```
  openfisca_core/data_storage/in_memory_storage.py  ← le remapping est dans Holder
  openfisca_core/data_storage/on_disk_storage.py
  openfisca_core/entities/_core_entity.py
  openfisca_core/entities/entity.py
  openfisca_core/entities/group_entity.py
  openfisca_core/projectors/*.py                    ← utilisent GroupPopulation (adapté en Phase 3)
```

### 8.3 Fichiers LIAM2 de référence (à consulter pendant le développement)

```
Modèle de données :
  liam2/entities.py       ← Entity.__init__(), build_period_array(), load_period_data(), flush_index()
  liam2/data.py           ← ColumnArray, index_table(), merge_arrays(), build_period_array()
  liam2/context.py        ← EntityContext.id_to_rownum (sélection du bon index)

Opérations dynamiques :
  liam2/exprmisc.py       ← add_individuals() (L199-241), New.compute() (L258-338)
  liam2/actions.py        ← RemoveIndividuals (L83-142)

Boucle temporelle :
  liam2/simulation.py     ← simulate_period() (L530-621)

Relations entre entités :
  liam2/links.py          ← Many2One, One2Many, LinkGet.compute()
```

### 8.4 Tests existants (pour la non-régression)

```
OpenFisca-core :
  openfisca_core/entities/tests/test_entity.py
  openfisca_core/entities/tests/test_group_entity.py
  + tous les tests dans openfisca_core/ (doctest et pytest)
```

### 8.5 Commandes utiles pour le développement

```bash
# Lancer les tests OpenFisca-core
cd /home/benjello/projects/openfisca-core
pytest openfisca_core/ -v

# Lancer les doctests
pytest --doctest-modules openfisca_core/

# Chercher toutes les utilisations de 'count' dans les populations
grep -rn "\.count" openfisca_core/populations/

# Chercher toutes les utilisations de check_array_compatible
grep -rn "check_array_compatible" openfisca_core/
```
