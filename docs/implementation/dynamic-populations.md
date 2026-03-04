# Plan d'implémentation : Populations dynamiques dans OpenFisca-core

## Résumé

Ce document décrit le plan d'implémentation pour ajouter le support de **populations dynamiques** dans OpenFisca-core, c'est-à-dire la possibilité de faire évoluer le nombre d'individus (personnes, ménages, etc.) au cours du temps lors d'une simulation. Cette fonctionnalité est inspirée du système d'indexation de [LIAM2](https://github.com/liam2/liam2).

L'objectif est de permettre, au sein d'une simulation, de :
- **Ajouter des individus** (naissances, immigration, formation de nouveaux ménages)
- **Supprimer des individus** (décès, émigration, dissolution de ménages)
- **Modifier la composition des entités de groupe** (changement de ménage, séparations, unions)

Tout en **conservant la compatibilité ascendante** avec le fonctionnement actuel d'OpenFisca (populations statiques).

---

## Table des matières

1. [Analyse de l'existant](#1-analyse-de-lexistant)
2. [Concepts clés de LIAM2 à transposer](#2-concepts-clés-de-liam2-à-transposer)
3. [Architecture cible](#3-architecture-cible)
4. [Plan d'implémentation par phases](#4-plan-dimplémentation-par-phases)
5. [Problèmes identifiés et solutions](#5-problèmes-identifiés-et-solutions)
6. [Impact sur les projects existants](#6-impact-sur-les-projects-existants)
7. [Plan de test](#7-plan-de-test)

---

## 1. Analyse de l'existant

### 1.1 OpenFisca-core : modèle statique

#### Structure des populations

```
CorePopulation (openfisca_core/populations/_core_population.py)
├── count: int                    # Taille fixe, définie à l'initialisation
├── ids: Sequence[str]            # Identifiants fixes (noms ou indices)
├── entity: CoreEntity            # Entité associée
├── simulation: Simulation        # Simulation parente
├── _holders: dict[str, Holder]   # Stockage des variables calculées
│
├── Population (population.py)        # Pour les entités « personne »
│   └── hérite de CorePopulation
│
└── GroupPopulation (group_population.py)  # Pour les entités groupe (ménage, etc.)
    ├── members: Population            # Référence vers la population des personnes
    ├── members_entity_id: ndarray     # Mapping personne → index d'entité groupe (FIXE)
    ├── members_role: ndarray          # Rôle de chaque personne dans l'entité (FIXE)
    └── members_position: ndarray      # Position dans l'entité (FIXE)
```

#### Points de blocage pour des populations dynamiques

| Composant | Fichier | Problème |
|---|---|---|
| `count` | `_core_population.py:35` | Attribute entier simple, assigné une seule fois |
| `ids` | `_core_population.py:41` | Liste fixe `[]` |
| `check_array_compatible_with_entity()` | `_core_population.py:262-293` | Vérifie `array.size == self.count` → interdit les arrays de taille différente |
| `empty_array()` | `_core_population.py:171-193` | `numpy.zeros(self.count)` → taille fixe |
| `filled_array()` | `_core_population.py:195-230` | `numpy.full(self.count, ...)` → taille fixe |
| `Holder.default_array()` | `holders/holder.py:323-325` | Utilise `self.population.count` fixe |
| `InMemoryStorage` | `data_storage/in_memory_storage.py` | Stocke des arrays par période sans notion de taille variable |
| `members_entity_id` | `group_population.py:55-61` | Array numpy fixe |
| `declare_person_entity()` | `simulation_builder.py:336-341` | Fixe `count = len(ids)` une seule fois |
| `_BuildDefaultSimulation` | `_build_default_simulation.py` | Construit tout en une passe |

#### Calcul paresseux (lazy evaluation)

OpenFisca calcule les variables **à la demande** via `Simulation._calculate()`. Il n'y a pas de boucle temporelle explicite. Quand une formule référence une variable pour une période passée, elle est calculée récursivement. Cela implique que :
- On ne sait pas à l'avance dans quel ordre les périodes seront visitées
- La taille de la population doit être connue pour chaque période demandée

### 1.2 LIAM2 : modèle dynamique

#### Structure des entités

```
Entity (liam2/entities.py)
├── name: str
├── fields: FieldCollection          # Définition des champs (nom, type, etc.)
├── array: ColumnArray               # Données actuelles (redimensionnable)
├── id_to_rownum: ndarray            # ★ Mapping id → position dans array
├── input_index: dict[period, ndarray]   # id_to_rownum par période (input)
├── output_index: dict[period, ndarray]  # id_to_rownum par période (output)
├── input_rows: dict[period, (start, stop)]  # Lignes dans la table d'entrée
├── output_rows: dict[period, (start, stop)] # Lignes dans la table de sortie
├── temp_variables: dict             # Variables temporaires (par période)
└── links: dict[str, Link]           # Relations Many2One / One2Many
```

#### Le mécanisme `id_to_rownum`

C'est un tableau numpy de taille `max_id + 1` :
- `id_to_rownum[id]` = position de l'individu dans `array`, ou `-1` s'il n'existe pas

```python
# Période 1 : 4 individus (ids 0,1,2,3)
id_to_rownum = [0, 1, 2, 3]
array = [données de 4 individus]

# Période 2 : individu 2 supprimé, individu 4 ajouté
id_to_rownum = [0, 1, -1, 2, 3]   # la taille grandit, -1 = absent
array = [données de 4 individus (0,1,3,4)]
```

#### Opérations dynamiques

**Ajout** (`add_individuals` dans `exprmisc.py:199-241`) :
1. Assigner de nouveaux `id` (incrémentaux) aux individus
2. Créer un `ColumnArray` pour les nouveaux individus
3. `entity.array.append(children)` → étend le tableau de données
4. Étendre toutes les variables temporaires
5. Mettre à jour `id_to_rownum` : concaténer les nouvelles positions

**Suppression** (`RemoveIndividuals` dans `actions.py:83-142`) :
1. Appliquer un masque booléen `not_removed` sur `entity.array.keep()`
2. Filtrer toutes les variables temporaires
3. Recalculer `id_to_rownum` : mettre `-1` pour les supprimés, décaler les positions

#### Boucle temporelle

LIAM2 suit une boucle **séquentielle** explicite :
```
pour chaque période:
    charger les données (load_period_data)  → merge_arrays + update id_to_rownum
    exécuter les processus séquentiellement
    stocker les résultats (store_period_data + flush_index)
```

---

## 2. Concepts clés de LIAM2 à transposer

### 2.1 Identifiants permanents (`id`)

Chaque individu reçoit un **identifiant entier permanent** à sa création. Cet identifiant ne change jamais et n'est jamais réattribué. C'est la clé de voûte du système.

**Transposition OpenFisca** : Actuellement, `ids` dans `CorePopulation` est une séquence de chaînes de caractères (noms comme "Alice", "Bob") ou d'entiers. Il faut introduire un système d'`id` permanents entiers, indépendant des `ids` actuels.

### 2.2 Le mapping `id_to_rownum`

Un tableau numpy où l'indice est l'`id` et la valeur est la position dans le tableau de données courant (ou `-1` si l'individu n'existe plus).

**Transposition OpenFisca** : Ajouter cet attribute dans `CorePopulation`. Le `count` actuel devient dérivé : `count = np.sum(id_to_rownum != -1)`.

### 2.3 L'index par période

LIAM2 conserve un `id_to_rownum` par période (`output_index`). Cela permet d'accéder aux données d'une période passée même si la population a changé depuis.

**Transposition OpenFisca** : Le `InMemoryStorage` stocke déjà des arrays par période, mais il faut aussi stocker le mapping id→position pour chaque période, sinon on ne peut pas interpréter les anciens arrays.

### 2.4 Le `ColumnArray` redimensionnable

LIAM2 utilise un `ColumnArray` qui stocke les données par colonnes (chaque champ est un numpy array séparé) et supporte `append()` et `keep()`.

**Transposition OpenFisca** : Le concept le plus proche est le `Holder` + `InMemoryStorage`. Mais OpenFisca ne stocke pas toutes les variables dans une seule structure — chaque variable a son propre `Holder`.

### 2.5 Boucle temporelle séquentielle

LIAM2 exécute les processus séquentiellement, période par période, ce qui garantit un ordre d'exécution connu pour les mutations de population.

**Transposition OpenFisca** : Il faudra un **mode séquentiel** (optionnel) où la simulation advance période par période, permettant des mutations entre les périodes.

---

## 3. Architecture cible

### 3.1 Principe directeur : deux modes de fonctionnement

```
Simulation
├── mode="static"   (défaut, comportement actuel inchangé)
│   └── count fixe, pas de mutations, calcul paresseux
│
└── mode="dynamic"  (nouveau)
    └── count variable, mutations possibles, boucle temporelle séquentielle
```

### 3.2 Nouveau modèle de données

```python
class CorePopulation:
    # === Attributes existants (inchangés en mode statique) ===
    entity: CoreEntity
    simulation: Simulation
    _holders: dict[str, Holder]

    # === Nouveaux attributes pour le mode dynamique ===
    _dynamic: bool = False           # Active le mode dynamique
    _permanent_ids: ndarray[int]     # IDs permanents des individus actuels
    _id_to_rownum: ndarray[int]      # Mapping id → position (-1 = absent)
    _next_id: int = 0                # Prochain ID à attribuer
    _period_index: dict[Period, ndarray[int]]  # id_to_rownum par période

    # === count devient une propriété ===
    @property
    def count(self) -> int:
        if self._dynamic:
            return len(self._permanent_ids)
        return self._count  # mode statique : attribute fixe comme avant

    @count.setter
    def count(self, value: int):
        self._count = value

    # === ids devient une propriété ===
    @property
    def ids(self) -> ndarray:
        if self._dynamic:
            return self._permanent_ids
        return self._ids

    @ids.setter
    def ids(self, value):
        self._ids = value
```

### 3.3 Diagramme de classes simplifié (mode dynamique)

```
                    ┌─────────────────────┐
                    │     Simulation      │
                    │─────────────────────│
                    │ mode: str           │ "static" | "dynamic"
                    │ populations: dict   │
                    │ current_period: Per. │ (nouveau, mode dynamique)
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────────┐
              │                │                     │
   ┌──────────▼──────────┐    ...    ┌───────────────▼──────────┐
   │     Population      │           │    GroupPopulation        │
   │   (SingleEntity)    │           │    (GroupEntity)          │
   │─────────────────────│           │──────────────────────────│
   │ _permanent_ids      │           │ _permanent_ids           │
   │ _id_to_rownum       │           │ _id_to_rownum            │
   │ _period_index       │           │ _period_index            │
   │─────────────────────│           │ _members_entity_id_index │ {period: array}
   │ add_individuals()   │           │ _members_role_index      │ {period: array}
   │ remove_individuals()│           │──────────────────────────│
   └─────────────────────┘           │ add_individuals()        │
                                     │ remove_individuals()     │
                                     │ update_memberships()     │
                                     └──────────────────────────┘
```

### 3.4 Flux de données en mode dynamique

```
Initialisation
    │
    ▼
┌─────────────────────────────┐
│ Période t₀ : état initial   │
│ - Créer permanent_ids       │
│ - Créer id_to_rownum        │
│ - Sauvegarder period_index  │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Période t : début           │
│ - Charger l'état (t-1)      │◄──────── Référence au period_index[t-1]
│ - Appliquer les mutations : │
│   • naissances (add)        │
│   • décès (remove)          │
│   • recomposition ménages   │
│ - Mettre à jour id_to_rownum│
│ - Calculer les variables    │
│ - Sauvegarder period_index  │
└──────────────┬──────────────┘
               │
               ▼
             t = t+1 → boucle
```

---

## 4. Plan d'implémentation par phases

### Phase 0 : Préparation (non-breaking, aucun changement d'API)

**Objectif** : Refactorer les attributes `count` et `ids` en propriétés sans changer le comportement.

#### Étape 0.1 : Transformer `count` en propriété dans `CorePopulation`

**Fichier** : `openfisca_core/populations/_core_population.py`

```python
# AVANT (ligne 35)
count: int = 0

# APRÈS
_count: int = 0

@property
def count(self) -> int:
    return self._count

@count.setter
def count(self, value: int) -> None:
    self._count = value
```

**Risque** : Faible. Les propriétés sont transparentes pour le code existent.
**Tests** : Tous les tests existants doivent passer sans modification.

#### Étape 0.2 : Transformer `ids` en propriété dans `CorePopulation`

**Fichier** : `openfisca_core/populations/_core_population.py`

```python
# AVANT (ligne 41)
ids: Sequence[str] = []

# APRÈS
_ids: Sequence[str] = []

@property
def ids(self) -> Sequence[str]:
    return self._ids

@ids.setter
def ids(self, value: Sequence[str]) -> None:
    self._ids = value
```

#### Étape 0.3 : Vérifier que tous les tests passent

Exécuter la suite de tests complète pour s'assurer que les refactorings sont transparents.

---

### Phase 1 : Infrastructure de base du mode dynamique

**Objectif** : Introduire les structures de données nécessaires sans modifier le comportement par défaut.

#### Étape 1.1 : Ajouter un flag `dynamic` à la `Simulation`

**Fichier** : `openfisca_core/simulations/simulation.py`

```python
class Simulation:
    def __init__(
        self,
        tax_benefit_system: TaxBenefitSystem,
        populations: Mapping[str, Population],
        dynamic: bool = False,   # ← NOUVEAU
    ) -> None:
        # ... code existent ...
        self.dynamic = dynamic
        if dynamic:
            for population in self.populations.values():
                population._enable_dynamic_mode()
```

**Impact** : Aucun, car `dynamic=False` par défaut.

#### Étape 1.2 : Ajouter le système d'identifiants permanents dans `CorePopulation`

**Fichier** : `openfisca_core/populations/_core_population.py`

Ajouter les attributes et méthodes suivants :

```python
class CorePopulation:
    # Nouveaux attributes
    _dynamic: bool = False
    _permanent_ids: numpy.ndarray | None = None   # IDs permanents (entiers)
    _id_to_rownum: numpy.ndarray | None = None     # Mapping id → position
    _next_id: int = 0                               # Compteur d'IDs
    _period_index: dict | None = None               # {period: id_to_rownum}

    def _enable_dynamic_mode(self) -> None:
        """Activer le mode dynamique. Appelé par Simulation.__init__."""
        self._dynamic = True
        self._period_index = {}

        # Convertir les ids existants en identifiants permanents entiers
        n = self._count
        self._permanent_ids = numpy.arange(n, dtype=int)
        self._id_to_rownum = numpy.arange(n, dtype=int)
        self._next_id = n

    @property
    def count(self) -> int:
        if self._dynamic:
            return len(self._permanent_ids)
        return self._count

    @count.setter
    def count(self, value: int) -> None:
        self._count = value
```

#### Étape 1.3 : Ajouter `_period_index` et méthode `snapshot_period()`

```python
def snapshot_period(self, period: Period) -> None:
    """Sauvegarder l'état du mapping id_to_rownum pour la période donnée."""
    if self._dynamic:
        self._period_index[period] = self._id_to_rownum.copy()

def get_period_id_to_rownum(self, period: Period) -> numpy.ndarray | None:
    """Récupérer le mapping id_to_rownum pour une période passée."""
    if self._dynamic:
        return self._period_index.get(period)
    return None
```

#### Étape 1.4 : Adapter `check_array_compatible_with_entity()`

**Fichier** : `openfisca_core/populations/_core_population.py`

```python
def check_array_compatible_with_entity(self, array: t.VarArray) -> None:
    if self._dynamic:
        # En mode dynamique, la taille de l'array peut différer de count
        # si elle correspond à un count d'une période antérieure
        return  # La vérification est déléguée au code qui utilise l'array
    if self.count == array.size:
        return
    raise InvalidArraySizeError(array, self.entity.key, self.count)
```

**Note** : En mode dynamique, la vérification de taille est relaxée car les arrays de périodes différentes peuvent avoir des tailles différentes. La cohérence est guarantee par le `_period_index`.

---

### Phase 2 : Mutations de population pour les entités simples (personnes)

**Objectif** : Permettre d'ajouter et supprimer des individus dans une `Population` (entité personne).

#### Étape 2.1 : Implémenter `add_individuals()` dans `Population`

**Fichier** : `openfisca_core/populations/population.py`

```python
def add_individuals(self, count: int, values: dict[str, ndarray] | None = None) -> ndarray:
    """Ajouter de nouveaux individus à la population.

    Args:
        count: Nombre d'individus à ajouter.
        values: Dictionnaire {nom_variable: array_valeurs} pour initialiser
                les variables des nouveaux individus.

    Returns:
        ndarray: Les IDs permanents attribués aux nouveaux individus.

    Raises:
        RuntimeError: Si le mode dynamique n'est pas activé.
    """
    if not self._dynamic:
        raise RuntimeError(
            "Cannot add individuals in static mode. "
            "Use Simulation(..., dynamic=True) to enable dynamic populations."
        )

    # 1. Attribuer de nouveaux IDs permanents
    new_ids = numpy.arange(self._next_id, self._next_id + count, dtype=int)
    self._next_id += count

    # 2. Étendre _permanent_ids
    self._permanent_ids = numpy.concatenate([self._permanent_ids, new_ids])

    # 3. Mettre à jour id_to_rownum
    old_len = len(self._id_to_rownum)
    new_rownums = numpy.arange(self.count - count, self.count, dtype=int)
    # Agrandir id_to_rownum si nécessaire
    if self._next_id > len(self._id_to_rownum):
        extension = numpy.full(
            self._next_id - len(self._id_to_rownum), -1, dtype=int
        )
        self._id_to_rownum = numpy.concatenate([self._id_to_rownum, extension])
    self._id_to_rownum[new_ids] = new_rownums

    # 4. Étendre les arrays dans les holders existants
    for variable_name, holder in self._holders.items():
        holder._extend_arrays(count, values.get(variable_name) if values else None)

    return new_ids
```

#### Étape 2.2 : Implémenter `remove_individuals()` dans `Population`

```python
def remove_individuals(self, mask: ndarray) -> None:
    """Supprimer des individus de la population.

    Args:
        mask: Masque booléen de taille count. True = à supprimer.

    Raises:
        RuntimeError: Si le mode dynamique n'est pas activé.
    """
    if not self._dynamic:
        raise RuntimeError(
            "Cannot remove individuals in static mode. "
            "Use Simulation(..., dynamic=True) to enable dynamic populations."
        )

    not_removed = ~mask
    removed_ids = self._permanent_ids[mask]

    # 1. Filtrer _permanent_ids
    self._permanent_ids = self._permanent_ids[not_removed]

    # 2. Mettre à jour id_to_rownum
    # Marquer les supprimés avec -1
    self._id_to_rownum[removed_ids] = -1
    # Recalculer les positions des survivants
    new_rownum = 0
    for i in range(len(self._id_to_rownum)):
        if self._id_to_rownum[i] != -1:
            self._id_to_rownum[i] = new_rownum
            new_rownum += 1

    # 3. Filtrer les arrays dans les holders existants
    for variable_name, holder in self._holders.items():
        holder._shrink_arrays(not_removed)
```

#### Étape 2.3 : Adapter le `Holder` pour supporter le redimensionnement

**Fichier** : `openfisca_core/holders/holder.py`

```python
class Holder:
    def _extend_arrays(self, count: int, values: ndarray | None = None) -> None:
        """Étendre les arrays stockés pour accueillir de nouveaux individus.

        Seul l'array de la période courante est étendu. Les arrays des
        périodes passées conservent leur taille originale (leur interprétation
        nécessite le period_index correspondent).
        """
        current_period = self.simulation.current_period
        if current_period is None:
            return

        array = self._memory_storage.get(current_period)
        if array is not None:
            if values is not None:
                extension = numpy.array(values, dtype=array.dtype)
            else:
                extension = numpy.full(count, self.variable.default_value, dtype=array.dtype)
            new_array = numpy.concatenate([array, extension])
            self._memory_storage.put(new_array, current_period)

    def _shrink_arrays(self, keep_mask: ndarray) -> None:
        """Filtrer les arrays pour la période courante après suppression d'individus."""
        current_period = self.simulation.current_period
        if current_period is None:
            return

        array = self._memory_storage.get(current_period)
        if array is not None:
            self._memory_storage.put(array[keep_mask], current_period)

    def default_array(self) -> ndarray:
        """Return a new array of the appropriate length for the entity."""
        return self.variable.default_array(self.population.count)
```

**Note sur les périodes passées** : Les arrays des périodes passées ne sont PAS redimensionnés. Pour accéder à la valeur d'un individu qui existait à la période `t` mais a été ajouté à la période `t'`, on utilise le `_period_index[t]` pour mapper l'id à la position dans l'array de la période `t`. Si l'individu n'existait pas, la valeur est la valeur par défaut.

---

### Phase 3 : Mutations pour les entités de groupe (ménages)

**Objectif** : Gérer les changements de composition des entités de groupe.

#### Étape 3.1 : Ajouter un index par période pour les memberships

**Fichier** : `openfisca_core/populations/group_population.py`

```python
class GroupPopulation(Population):
    def _enable_dynamic_mode(self) -> None:
        super()._enable_dynamic_mode()
        # Historique des memberships par période
        self._members_entity_id_index: dict[Period, ndarray] = {}
        self._members_role_index: dict[Period, ndarray] = {}

    def snapshot_period(self, period: Period) -> None:
        """Sauvegarder l'état complete pour la période."""
        super().snapshot_period(period)
        if self._dynamic:
            if self._members_entity_id is not None:
                self._members_entity_id_index[period] = self._members_entity_id.copy()
            if self._members_role is not None:
                self._members_role_index[period] = self._members_role.copy()
```

#### Étape 3.2 : Propager les ajouts de personnes aux entités de groupe

Quand des personnes sont ajoutées, il faut aussi mettre à jour les `GroupPopulation` auxquelles elles appartiennent.

```python
def add_members(
    self,
    person_ids: ndarray,
    entity_ids: ndarray,
    roles: ndarray,
) -> None:
    """Associer de nouvelles personnes à des entités de groupe.

    Args:
        person_ids: IDs permanents des nouvelles personnes.
        entity_ids: ID d'entité de groupe pour chaque personne.
        roles: Rôle de chaque personne dans l'entité.
    """
    if not self._dynamic:
        raise RuntimeError("Dynamic mode required.")

    # Étendre members_entity_id
    self._members_entity_id = numpy.concatenate([
        self._members_entity_id, entity_ids
    ])

    # Étendre members_role
    self._members_role = numpy.concatenate([
        self._members_role, roles
    ])

    # Invalider le cache de members_position
    self._members_position = None
    self._ordered_members_map = None
```

#### Étape 3.3 : Propager les suppressions de personnes

```python
def remove_members(self, person_keep_mask: ndarray) -> None:
    """Supprimer des personnes des entités de groupe.

    Args:
        person_keep_mask: Masque booléen sur la population des personnes.
                          True = conserver, False = supprimer.
    """
    if not self._dynamic:
        raise RuntimeError("Dynamic mode required.")

    self._members_entity_id = self._members_entity_id[person_keep_mask]
    self._members_role = self._members_role[person_keep_mask]
    self._members_position = None
    self._ordered_members_map = None

    # Recalculer count : nombre d'entités de groupe distinctes
    if len(self._members_entity_id) > 0:
        self._count = numpy.max(self._members_entity_id) + 1
    else:
        self._count = 0
```

#### Étape 3.4 : Ajouter/supprimer des entités de groupe

```python
def add_groups(self, count: int) -> ndarray:
    """Créer de nouvelles entités de groupe (ex: nouveaux ménages)."""
    if not self._dynamic:
        raise RuntimeError("Dynamic mode required.")

    new_ids = numpy.arange(self._next_id, self._next_id + count, dtype=int)
    self._next_id += count
    self._permanent_ids = numpy.concatenate([self._permanent_ids, new_ids])

    # Mettre à jour id_to_rownum
    # ...similaire à add_individuals dans Population

    return new_ids

def remove_groups(self, mask: ndarray) -> None:
    """Supprimer des entités de groupe (ex: dissolution de ménages).

    Note: les personnes membres doivent être réassignées AVANT
    d'appeler cette méthode.
    """
    # ...similaire à remove_individuals dans Population
```

---

### Phase 4 : Boucle temporelle séquentielle

**Objectif** : Fournir un mécanisme de simulation période par période en mode dynamique.

#### Étape 4.1 : Ajouter `current_period` à la `Simulation`

**Fichier** : `openfisca_core/simulations/simulation.py`

```python
class Simulation:
    current_period: Period | None = None  # Période en cours (mode dynamique)
```

#### Étape 4.2 : Implémenter `run_period()` et `advance_period()`

```python
def run_period(self, period: Period, processes: list[callable] | None = None) -> None:
    """Exécuter une période en mode dynamique.

    Args:
        period: La période à simuler.
        processes: Liste optionnelle de functions (mutations) à exécuter.
                   Chaque fonction reçoit la simulation en argument.
    """
    if not self.dynamic:
        raise RuntimeError("run_period() requires dynamic=True")

    self.current_period = period

    # 1. Exécuter les processus de mutation (naissances, décès, etc.)
    if processes:
        for process in processes:
            process(self)

    # 2. Sauvegarder l'état de la période
    for population in self.populations.values():
        population.snapshot_period(period)

def simulate(
    self,
    start_period: Period,
    end_period: Period,
    period_processes: dict[str, list[callable]] | None = None,
    variables_to_compute: list[str] | None = None,
) -> None:
    """Exécuter une simulation dynamique sur une plage de périodes.

    Args:
        start_period: Première période.
        end_period: Dernière période.
        period_processes: Processus de mutation par type de période.
        variables_to_compute: Variables à calculer pour chaque période.
    """
    if not self.dynamic:
        raise RuntimeError("simulate() requires dynamic=True")

    for period in periods.period_range(start_period, end_period):
        self.run_period(period, period_processes)

        if variables_to_compute:
            for var_name in variables_to_compute:
                self.calculate(var_name, period)
```

---

### Phase 5 : Accès aux données historiques et adaptation du cache

**Objectif** : Permettre aux formulas d'accéder correctement aux données de périodes passées malgré les changements de population.

#### Étape 5.1 : Adapter `Holder.get_array()` pour le mode dynamique

**Fichier** : `openfisca_core/holders/holder.py`

```python
def get_array(self, period) -> ndarray | None:
    """Get the value of the variable for the given period.

    En mode dynamique, si l'array stocké a une taille différente
    de la population actuelle, il est « re-indexé » via le period_index.
    """
    if period is not None and not isinstance(period, periods.Period):
        period = periods.period(period)

    values = self._memory_storage.get(period)
    if values is None:
        return None

    population = self.population
    if not population._dynamic:
        return values

    # Mode dynamique : si l'array a la bonne taille, c'est direct
    if len(values) == population.count:
        return values

    # Sinon, il faut remapper via le period_index
    return self._remap_to_current_population(values, period)

def _remap_to_current_population(self, values: ndarray, period: Period) -> ndarray:
    """Remapper un array d'une période passée vers la population actuelle.

    Les individus qui n'existaient pas à cette période reçoivent
    la valeur par défaut.
    """
    population = self.population
    past_index = population.get_period_id_to_rownum(period)
    current_index = population._id_to_rownum

    result = numpy.full(population.count, self.variable.default_value, dtype=values.dtype)

    for pid in population._permanent_ids:
        current_row = current_index[pid]
        if current_row == -1:
            continue  # ne devrait pas arriver pour la population courante

        if pid < len(past_index) and past_index[pid] != -1:
            past_row = past_index[pid]
            result[current_row] = values[past_row]
        # sinon : valeur par défaut (l'individu n'existait pas)

    return result
```

**Optimisation** : La boucle Python ci-dessus est pédagogique. L'implémentation réelle utilisera des opérations vectorisées numpy :

```python
def _remap_to_current_population(self, values: ndarray, period: Period) -> ndarray:
    population = self.population
    past_index = population.get_period_id_to_rownum(period)

    result = numpy.full(population.count, self.variable.default_value, dtype=values.dtype)

    # Trouver les IDs communs entre la population actuelle et la passée
    current_ids = population._permanent_ids
    valid_in_past = (current_ids < len(past_index)) & (past_index[
        numpy.minimum(current_ids, len(past_index) - 1)
    ] != -1)

    # Pour les IDs valides dans le passé, copier les valeurs
    valid_ids = current_ids[valid_in_past]
    past_rows = past_index[valid_ids]
    current_rows = population._id_to_rownum[valid_ids]
    result[current_rows] = values[past_rows]

    return result
```

#### Étape 5.2 : Adapter les projections dans `GroupPopulation`

Les méthodes `sum()`, `project()`, etc. de `GroupPopulation` doivent utiliser le bon `members_entity_id` selon la période.

```python
@projectors.projectable
def sum(self, array, role=None):
    self.entity.check_role_validity(role)
    if self._dynamic:
        # En mode dynamique, utiliser les memberships courants
        # (les arrays reçus ont déjà été remappés si nécessaire)
        members_entity_id = self._members_entity_id
    else:
        members_entity_id = self.members_entity_id

    self.members.check_array_compatible_with_entity(array)
    if role is not None:
        role_filter = self.members.has_role(role)
        return numpy.bincount(
            members_entity_id[role_filter],
            weights=array[role_filter],
            minlength=self.count,
        )
    return numpy.bincount(members_entity_id, weights=array, minlength=self.count)
```

**Note** : Le `minlength=self.count` est important en mode dynamique car le nombre d'entités de groupe peut avoir changé.

---

### Phase 6 : API utilisateur et intégration

**Objectif** : Fournir une API propre pour les utilisateurs qui veulent écrire des microsimulations dynamiques.

#### Étape 6.1 : API de haut niveau pour les mutations

```python
# === Exemple d'utilisation ===

from openfisca_core import periods, simulations

# Créer une simulation dynamique
simulation = SimulationBuilder.build_from_dict(
    tax_benefit_system,
    input_dict,
    dynamic=True,  # ← NOUVEAU
)

# Définir un processus de naissances
def process_births(simulation):
    person = simulation.persons
    # Exemple: 10% des femmes âgées de 20-40 ans donnent naissance
    is_woman = person("sexe", simulation.current_period) == 1
    age = person("age", simulation.current_period)
    fertile = is_woman & (age >= 20) & (age <= 40)
    birth_prob = numpy.random.random(person.count) < 0.10
    gives_birth = fertile & birth_prob

    num_births = gives_birth.sum()
    if num_births > 0:
        # Ajouter les enfants
        new_ids = person.add_individuals(num_births, values={
            "age": numpy.zeros(num_births, dtype=int),
            "sexe": numpy.random.randint(0, 2, num_births),
        })

        # Assigner les enfants aux ménages de leurs mères
        mother_household_ids = simulation.household.members_entity_id[gives_birth]
        household = simulation.get_population("households")
        household.add_members(
            person_ids=new_ids,
            entity_ids=mother_household_ids,
            roles=numpy.full(num_births, Household.CHILD),
        )

# Définir un processus de décès
def process_deaths(simulation):
    person = simulation.persons
    age = person("age", simulation.current_period)
    # Table de mortalité simplifiée
    death_prob = numpy.where(age > 80, 0.05, 0.001)
    dies = numpy.random.random(person.count) < death_prob

    if numpy.any(dies):
        # Supprimer des ménages d'abord
        for entity_key, population in simulation.populations.items():
            if hasattr(population, 'members'):
                population.remove_members(~dies)
        # Supprimer les personnes
        person.remove_individuals(dies)

# Exécuter la simulation
for year in range(2020, 2030):
    period = periods.period(year)
    simulation.run_period(period, processes=[
        process_births,
        process_deaths,
    ])
    # Calculer les variables d'intérêt
    revenus = simulation.calculate("revenu_disponible", period)
```

#### Étape 6.2 : Adapter le `SimulationBuilder` pour le mode dynamique

**Fichier** : `openfisca_core/simulations/simulation_builder.py`

```python
class SimulationBuilder:
    def build_from_dict(
        self,
        tax_benefit_system: TaxBenefitSystem,
        input_dict: Params,
        dynamic: bool = False,   # ← NOUVEAU paramètre
    ) -> Simulation:
        # ... code existent ...
        simulation = Simulation(tax_benefit_system, populations, dynamic=dynamic)
        # ... reste du code ...
```

---

## 5. Problèmes identifiés et solutions

### 5.1 Calcul paresseux vs boucle séquentielle

**Problème** : En mode statique, OpenFisca calcule les variables à la demande (lazy). En mode dynamique, il faut savoir « quelle version de la population » utiliser pour chaque période.

**Solution** : En mode dynamique, imposer une boucle séquentielle (`run_period()`). Le `current_period` de la simulation détermine quelle population est active. Les accès à des périodes passées utilisent le `_period_index` pour remapper les données.

### 5.2 Formulas qui accèdent au passé

**Problème** : Une formule peut faire `person("revenu", period.last_year)` alors que la population a changé entre les deux périodes.

**Solution** : Le `Holder.get_array()` adapté (Phase 5) remappera automatiquement les données via `_remap_to_current_population()`. Les nouveaux individus recevront la valeur par défaut pour les périodes antérieures à leur création. Les individus supprimés n'apparaîtront plus dans les résultats courants.

### 5.3 Cohérence personne-ménage

**Problème** : Quand des personnes sont ajoutées/supprimées, les entités de groupe doivent être mises à jour de façon cohérente.

**Solution** :
- L'API force l'utilisateur à gérer explicitement les memberships (comme dans LIAM2).
- Fournir des helpers pour les cas courants (naissance → ajout au ménage de la mère, décès → suppression du ménage).
- Validation : vérifier qu'après les mutations, chaque personne est assignée à exactement un ménage.

### 5.4 Performance

**Problème** : Le remapping via `_remap_to_current_population()` est coûteux s'il est appelé souvent.

**Solutions** :
- Cache : ne remapper que si la taille diffère de la population courante.
- Optimisation : utiliser des opérations numpy vectorisées (pas de boucle Python).
- Limitation : ne conserver les `_period_index` que pour N périodes glissantes.

### 5.5 Mémoire

**Problème** : Stocker un `id_to_rownum` par période peut consommer beaucoup de mémoire.

**Solutions** :
- Ne conserver que les N dernières périodes (paramétrable).
- Compression : stocker les deltas plutôt que les tableaux completes.
- Disk-backed : utiliser le `OnDiskStorage` existent pour les anciennes périodes.

### 5.6 Compatibilité avec les projects existants

**Problème** : Les pays (openfisca-france, etc.) ne doivent pas être affectés.

**Solution** : Le mode `dynamic=False` est le défaut. Aucun changement de comportement. Les projects existants fonctionnent exactement comme avant. Le mode dynamique est opt-in.

### 5.7 Sérialisation / API web

**Problème** : L'API REST d'OpenFisca expose des simulations via JSON. Comment gérer les populations dynamiques ?

**Solution (future)** : Hors scope du PoC. Pour l'instant, le mode dynamique sera utilisable uniquement via l'API Python.

### 5.8 Multi-pas de temps : un avantage clé d'OpenFisca

#### Le pas de temps unique de LIAM2

LIAM2 fonctionne avec un **pas de temps unique** par simulation (typiquement
l'année). Toutes les variables sont calculées au même rythme, toutes les
mutations se produisent une fois par an :

```yaml
# LIAM2 : un seul pas de temps
globals:
    periodic:
        - start_period: 2020
          periods: 30       # 30 pas annuels

simulation:
    processes:           # exécutés une fois par AN
        - ageing()
        - birth()
        - death()
        - marriage()
        - compute_income()
        - compute_tax()
```

Conséquence : si l'impôt sur le revenu est annuel mais que les cotisations
sociales sont mensuelles, LIAM2 doit choisir un pas de temps (en général
l'année) et perdre la granularité mensuelle, ou inverser et perdre en
performance.

#### Les pas de temps multiples d'OpenFisca

OpenFisca gère nativement **plusieurs granularités temporelles** :

| `definition_period` | Examples | Conversions automatiques |
|---|---|---|
| `ETERNITY` | date de naissance, sexe | Jamais recalculé |
| `YEAR` | impôt sur le revenu, RSA éligibilité | Some des mois, etc. |
| `MONTH` | salaire, cotisations sociales | Divise l'année par 12, etc. |
| `DAY` | (rarement utilisé) | |

```python
# OpenFisca : granularité native
class salaire_net(Variable):
    definition_period = MONTH     # calculé mensuellement

class impot_revenu(Variable):
    definition_period = YEAR      # calculé annuellement
    def formula(person, period):
        # Some automatique des salaires mensuels
        salaire_annuel = person("salaire_net", period, options=[ADD])
        return bareme.calc(salaire_annuel)
```

#### Impact sur les populations dynamiques

Le multi-pas de temps a des implications majeures en mode dynamique :

**1. Les mutations peuvent se produire à différentes fréquences**

```python
# Naissances et décès → mensuels (démographie fine)
# Réformes fiscales → annuelles (changement de barème)
# Marriage/divorce → événementiel (n'importe quand)

def process_births(simulation):
    """Exécuté chaque MOIS."""
    ...

def process_divorce(simulation):
    """Exécuté chaque MOIS (événementiel)."""
    ...

def process_tax_reform(simulation):
    """Exécuté chaque ANNÉE."""
    ...

# Boucle multi-pas de temps
for year in range(2020, 2050):
    process_tax_reform(simulation)
    for month in range(1, 13):
        period = periods.period(f"{year}-{month:02d}")
        simulation.evolve(period, processes=[
            process_births,
            process_divorce,
        ])
        # Calculus mensuels
        simulation.calculate("salaire_net", period)

    # Calculus annuels (agrègent les mois automatiquement)
    simulation.calculate("impot_revenu", periods.period(year))
```

**2. La fréquence des snapshots de composition est un choix**

| Stratégie | Stockage (1M pers, 30 ans) | Précision |
|---|---|---|
| Snapshot annuel | ~33 Mo × 30 = **1 Go** | Composition fixe dans l'année |
| Snapshot mensuel | ~33 Mo × 360 = **12 Go** | Composition exacte chaque mois |
| Snapshot à chaque mutation | Variable | Exact mais coûteux |

La recommendation est de **snapshoter au rythme des mutations** :
- Si les mutations sont annuelles → snapshot annuel
- Si les mutations sont mensuelles → snapshot mensuel
- La fenêtre glissante (opt. 1) limit l'impact mémoire

**3. La frontière temporelle (déterminisme) respecte le multi-pas de temps**

Le tracker `_settled_up_to` compare des `Period`, qui ont une granularité.
Un `evolve("2024-06")` est après un `calculate(V, "2024-05")` mais avant
un `calculate(V, "2024")` (l'année entière) :

```python
# OK : évoluer un mois, calculer le mois suivant
simulation.calculate("salaire", "2024-05")    # settled = 2024-05
simulation.evolve("2024-06")                   # ✅ 2024-06 > 2024-05

# ATTENTION : calculer l'ANNÉE bloque les mutations mensuelles
simulation.calculate("impot_revenu", "2024")   # settled = 2024 (couvre tout)
simulation.evolve("2024-07")                   # ❌ 2024-07 ⊂ 2024

# → il faut calculer l'année APRÈS avoir évolué tous les mois
```

La règle pour le multi-pas de temps :

> **Les variables annuelles ne doivent être calculées qu'après que tous
> les mois de l'année ont été évolués.**

**4. Comparison avec LIAM2**

| Aspect | LIAM2 | OpenFisca dynamique |
|---|---|---|
| Pas de temps | Unique (annuel) | Multiple (mois, année, éternité) |
| Mutations | 1 fois / période | À chaque sous-période |
| Granularité | Grossière | Fine (cotisations mensuelles + impôt annuel) |
| Conversions | Manuelles | Automatiques (`ADD`, `DIVIDE`) |
| Complexité | Simple | Plus complexe (ordre des calculus) |
| Précision | 🟡 | ✅ Meilleure |

**Conclusion** : Le multi-pas de temps est un **avantage majeur** d'OpenFisca
pour la microsimulation dynamique. Il permet de modéliser des phénomènes à
des fréquences différentes (démographie mensuelle + fiscalité annuelle)
dans une seule simulation, ce que LIAM2 ne peut pas faire nativement.

### 5.9 Déterminisme : l'invariant fundamental

#### Le problème

La propriété fondamentale d'OpenFisca est que pour des entrées données, le résultat
d'un calcul est **toujours le même**, quel que soit l'ordre d'exécution.
OpenFisca est essentiellement une **fonction pure**.

Les populations dynamiques introduisent des **mutations** de la structure, ce qui
crée un risque de **perte de déterminisme** : le même appel `calculate(V, p)` pourrait
donner des résultats différents selon qu'il est exécuté avant ou après une mutation.

#### L'invariant à garantir

> **Pour toute variable V et toute période p, `calculate(V, p)` doit toujours
> retourner le même résultat, quel que soit le moment où il est appelé dans la
> simulation.**

#### Les deux scénarios de violation

**Scénario 1 : Calcul avant mutation, recalcul après**

```python
# Ménage M0 = {Alice (3000€), Bob (2000€)}

revenu_avant = simulation.calculate("revenu_menage", "2024-06")
# → 5000€ (Alice + Bob)

simulation.evolve_population("2024-07")  # divorce : Bob quitte M0

revenu_après = simulation.calculate("revenu_menage", "2024-06")
# → 3000€ ??? L'invariant est violé !
```

Le problème : si la mutation modifie `members_entity_id` **en place**, alors le calcul
pour 2024-06 (avant le divorce) donne un résultat différent après la mutation.

**Scénario 2 : Mutation rétroactive**

```python
simulation.evolve_population("2024-07")  # mutation à juillet
result = simulation.calculate("V", "2024-06")  # calcul pour juin
  # → utilise composition("2024-06") qui dépend de composition("2024-05")

simulation.evolve_population("2024-05")  # mutation à mai ← RÉTROACTIF !
  # → change composition("2024-05") → invalid le résultat pour juin
```

#### Mécanisme de vérification

Le framework doit **détecter et empêcher** ces violations.

**Observation** : vérifier quelles variables dépendent (transitivement) de la
composition est **coûteux** — cela nécessite une analyse complète du graphe de
dépendances. Mais on peut utiliser une approach **conservatrice et triviale** :

> En mode dynamique, le temps advance dans un seul sens. Une fois qu'on a calculé
> **quoi que ce soit** à la période t, on ne peut plus muter la composition pour
> une période ≤ t.

C'est un simple entier — la « frontière » — à comparer. Coût : **O(1) par appel**.

```python
class PopulationStateTracker:
    """Version simplifiée : un seul entier, pas d'analyse de dépendances.

    Au lieu de déterminer quelles variables dépendent de la composition
    (coûteux), on adopte une approach conservatrice : TOUT calcul à la
    période t « gèle » la composition pour toute période ≤ t.
    """

    def __init__(self):
        self._settled_up_to: Period | None = None  # max période "lue"

    def on_calculate(self, period):
        """Appelé à chaque calculate(). Coût : O(1)."""
        if self._settled_up_to is None or period > self._settled_up_to:
            self._settled_up_to = period

    def on_evolve(self, period):
        """Appelé à chaque evolve(). Coût : O(1)."""
        if self._settled_up_to is not None and period <= self._settled_up_to:
            raise DeterminismError(
                f"Cannot evolve population at {period}: "
                f"variables have already been calculated up to "
                f"{self._settled_up_to}. Evolve populations BEFORE "
                f"calculating variables for that period."
            )
```

**Pourquoi c'est suffisant** :
- ✅ **Correct** — aucun faux négatif (on ne laisse jamais passer une violation)
- ✅ **O(1)** — pas d'analyse de graphe, juste une comparison d'entiers
- ✅ **Naturel** — correspond au workflow `evolve(t)` → `calculate(*, t)` → `evolve(t+1)`
- 🟡 **Conservateur** — un calcul indépendant de la composition gèle quand même la
  période. En pratique, c'est rarement un problème car l'ordre naturel est chronologique.

Si un jour on a besoin de relâcher cette contrainte (calculer une variable « indépendante
de la composition » pour une période future), on pourra ajouter un décorateur
`@composition_independent` sur les variables concernées. Mais c'est une optimisation,
pas un prérequis.

#### Analogie avec les bases de données

C'est le même problème que les **conflicts lecture/écriture** en transactions :

| Concept BD | Équivalent OpenFisca dynamique |
|---|---|
| Lecture (SELECT) | `calculate(V, t)` — lit la composition à t |
| Écriture (UPDATE) | `evolve(t)` — modifie la composition à t |
| Read-after-Write | ✅ OK : évoluer puis calculer |
| Write-after-Read | ❌ Interdit : calculer puis évoluer la même période |
| Isolation niveau | Chaque calcul voit un snapshot cohérent |

#### La règle simple

> **La composition à toute période t doit être fixée (« settled ») avant que
> quiconque lise un résultat qui en dépend. Une fois fixée, elle ne peut
> plus changer.**

Concrètement, la simulation dynamique doit :

1. **Évoluer les populations séquentiellement** : t=1, t=2, t=3...
2. **Calculer les variables à la demande** : mais le framework vérifie qu'on
   ne demande pas une composition pas encore fixée, et qu'on ne modifie pas
   une composition déjà utilisée
3. **Signaler une erreur claire** (`DeterminismError`) si l'utilisateur tente
   de violer l'invariant

#### Contrainte sur les formulas d'évolution

Si la composition est modélisée comme une variable temporelle (cf. analyse
des lines), sa formule ne doit dépendre que de variables à des **périodes
antérieures** pour éviter les cycles intra-période :

```python
# ✅ OK : la composition à t dépend de variables à t-1
household_id(t) ← divorce(t) ← revenu_menage(t-1) ← household_id(t-1)

# ❌ CYCLE : la composition à t dépend de variables à t
household_id(t) ← divorce(t) ← revenu_menage(t) ← household_id(t) ← BOUCLE
```

Cette contrainte peut être vérifiée par analyse statique du graphe de dépendances.

#### Implémentation concrète

Voici ce qu'il faut concrètement ajouter à OpenFisca-core :

**1. Une exception (~5 lignes)**

Fichier : `openfisca_core/errors.py`

```python
class DeterminismError(Exception):
    """Raised when a population mutation would break calculation determinism.

    This happens when evolve() is called for a period that has already
    been used by calculate().
    """
    pass
```

**2. Le tracker intégré à Simulation (~20 lignes)**

Fichier : `openfisca_core/simulations/simulation.py`

```python
class Simulation:
    def __init__(self, ..., dynamic=False):
        # ... existent ...
        self._dynamic = dynamic
        self._settled_up_to: Period | None = None   # ← NOUVEAU

    def calculate(self, variable_name, period, ...):
        # Hook AVANT le calcul existent — O(1)
        if self._dynamic:
            p = periods.period(period)
            if self._settled_up_to is None or p > self._settled_up_to:
                self._settled_up_to = p

        # ... code existent inchangé ...
        return self._calculate(variable_name, period)

    def evolve(self, period):
        """Muter la population à cette période."""
        p = periods.period(period)

        # Vérification O(1) — compare un entier
        if self._settled_up_to is not None and p <= self._settled_up_to:
            raise DeterminismError(
                f"Cannot evolve population at {p}: calculations "
                f"have already been done up to {self._settled_up_to}. "
                f"Call evolve() BEFORE calculate() for this period."
            )

        self.current_period = p
        # ... exécution des mutations ...
```

**3. Snapshot de composition automatique (~15 lignes)**

Fichier : `openfisca_core/populations/group_population.py`

```python
class GroupPopulation:
    def _snapshot_composition(self, period):
        """Sauvegarder la composition courante pour cette période.

        Appelé automatiquement par Simulation.evolve().
        """
        self._members_entity_id_index[period] = (
            self._members_entity_id.copy()
        )
        self._members_role_index[period] = (
            self._members_role.copy()
        )

    @property
    def members_entity_id(self):
        """Retourne la composition de la période courante."""
        if self._dynamic and self.simulation.current_period:
            stored = self._members_entity_id_index.get(
                self.simulation.current_period)
            if stored is not None:
                return stored
        return self._members_entity_id
```

**4. Récapitulatif de l'implémentation**

| Ajout | Fichier | Lignes | Coût runtime |
|---|---|---|---|
| `DeterminismError` | `errors.py` | ~5 | 0 |
| `_settled_up_to` + hook dans `calculate()` | `simulation.py` | ~15 | O(1) par calcul |
| Vérification dans `evolve()` | `simulation.py` | ~10 | O(1) par mutation |
| `_snapshot_composition()` | `group_population.py` | ~15 | O(n) par période |
| **Total** | | **~45 lignes** | **Négligeable** |

---

## 6. Impact sur les projects existants

### 6.1 Aucun impact en mode statique (défaut)

| Project | Impact |
|---|---|
| openfisca-france | ❌ Aucun (`dynamic=False` par défaut) |
| openfisca-tunisia | ❌ Aucun |
| country-template | ❌ Aucun |
| openfisca-survey-manager | ❌ Aucun |

### 6.2 Changements internes (transparents pour les utilisateurs)

| Changement | Risque de régression |
|---|---|
| `count` devient propriété | 🟢 Très faible (transparent) |
| `ids` devient propriété | 🟢 Très faible (transparent) |
| Nouveaux attributes `_dynamic`, etc. | 🟢 Nul (opt-in) |
| `check_array_compatible_with_entity()` adapté | 🟡 Faible (seulement en mode dynamique) |
| Nouveau paramètre `dynamic=False` | 🟢 Nul (valeur par défaut) |

### 6.3 Nouveaux cas d'utilisation activés

- Microsimulation dynamique (projection démographique avec impôts/transferts)
- Modèles de retraite avec entrées/sorties du marché du travail
- Études d'impact à long terme avec changements démographiques
- Combination OpenFisca + LIAM2 dans un seul framework

---

## 7. Plan de test

### 7.1 Tests de non-régression (Phase 0)

```python
# Vérifier que TOUS les tests existants passent après le refactoring count/ids en propriétés
# Commande : pytest openfisca_core/
```

### 7.2 Tests unitaires du mode dynamique (Phases 1-3)

```python
class TestDynamicPopulation:
    def test_enable_dynamic_mode(self):
        """Vérifier que l'activation du mode dynamique initialise correctement les structures."""

    def test_add_individuals(self):
        """Vérifier l'ajout d'individus : count, ids, id_to_rownum."""

    def test_remove_individuals(self):
        """Vérifier la suppression d'individus : count, ids, id_to_rownum, -1 dans l'index."""

    def test_add_then_remove(self):
        """Vérifier la cohérence après ajout puis suppression."""

    def test_snapshot_period(self):
        """Vérifier que period_index est correctement sauvegardé."""

    def test_remap_to_current_population(self):
        """Vérifier le remapping depuis une période passée vers la population courante."""

    def test_remap_new_individual_gets_default(self):
        """Un individu ajouté après la période t reçoit la valeur par défaut pour t."""

    def test_remap_removed_individual_absent(self):
        """Un individu supprimé n'apparaît plus dans les résultats courants."""

class TestDynamicGroupPopulation:
    def test_add_members(self):
        """Vérifier l'ajout de personnes à un ménage."""

    def test_remove_members(self):
        """Vérifier la suppression de personnes d'un ménage."""

    def test_add_groups(self):
        """Vérifier la création de nouvelles entités de groupe."""

    def test_sum_after_mutation(self):
        """Vérifier que sum() fonctionne après ajout/suppression."""

    def test_project_after_mutation(self):
        """Vérifier que project() fonctionne après ajout/suppression."""
```

### 7.3 Test d'intégration (Phases 4-6)

```python
class TestDynamicSimulation:
    def test_full_lifecycle(self):
        """
        Scénario complete :
        1. Créer une simulation avec 100 personnes, 50 ménages
        2. Période 1 : calculer revenu, impôt
        3. Période 2 : ajouter 10 naissances, supprimer 5 décès
        4. Période 2 : calculer revenu, impôt (population = 105)
        5. Accéder aux données de la période 1 pour un individu qui existait
        6. Vérifier que les nouveaux individus ont la valeur par défaut pour la période 1
        """

    def test_backward_compatibility(self):
        """Vérifier qu'une simulation standard (dynamic=False) fonctionne exactement comme avant."""

    def test_formula_accessing_past_period(self):
        """Vérifier qu'une formule accédant au passé fonctionne malgré le changement de population."""
```

---

## Annexe A : Correspondence OpenFisca ↔ LIAM2

| Concept LIAM2 | Concept OpenFisca actuel | Concept OpenFisca cible |
|---|---|---|
| `Entity.array` (ColumnArray) | `Holder._memory_storage` (par variable) | Inchangé (un Holder par variable) |
| `Entity.id_to_rownum` | N/A | `CorePopulation._id_to_rownum` |
| `Entity.output_index` | N/A | `CorePopulation._period_index` |
| `Entity.fields` | `Variable` (classe séparée) | Inchangé |
| `new()` / `add_individuals()` | N/A | `Population.add_individuals()` |
| `RemoveIndividuals` | N/A | `Population.remove_individuals()` |
| `Entity.load_period_data()` | `Holder.get_array(period)` | `Holder.get_array()` + remapping |
| `Entity.store_period_data()` | `Holder.put_in_cache()` | `Population.snapshot_period()` |
| `Link (Many2One/One2Many)` | Projectors + `GroupPopulation` | `GroupPopulation` étendu |
| `Simulation.simulate_period()` | N/A (calcul paresseux) | `Simulation.run_period()` |
| `EvaluationContext` | `Simulation` + `Population` | Inchangé |

## Annexe B : Fichiers à modifier

| Fichier | Phase | Type de modification |
|---|---|---|
| `populations/_core_population.py` | 0, 1, 2 | Propriétés count/ids, attributes dynamiques, add/remove |
| `populations/population.py` | 2 | `add_individuals()`, `remove_individuals()` |
| `populations/group_population.py` | 3 | `add_members()`, `remove_members()`, `add_groups()`, index par période |
| `holders/holder.py` | 2, 5 | `_extend_arrays()`, `_shrink_arrays()`, `get_array()` adapté |
| `simulations/simulation.py` | 1, 4 | Flag `dynamic`, `current_period`, `run_period()`, `simulate()` |
| `simulations/simulation_builder.py` | 6 | Paramètre `dynamic` |
| `simulations/_build_default_simulation.py` | 6 | Support du mode dynamique |
| `data_storage/in_memory_storage.py` | 5 | Aucune modification (le remapping est dans Holder) |

## Annexe C : Estimation de l'effort

| Phase | Description | Estimation |
|---|---|---|
| Phase 0 | Refactoring count/ids en propriétés | 1-2 jours |
| Phase 1 | Infrastructure mode dynamique | 2-3 jours |
| Phase 2 | Mutations pour entités simples | 3-4 jours |
| Phase 3 | Mutations pour entités de groupe | 3-4 jours |
| Phase 4 | Boucle temporelle séquentielle | 2-3 jours |
| Phase 5 | Accès historique et adaptation cache | 3-5 jours |
| Phase 6 | API utilisateur et intégration | 2-3 jours |
| Tests | Tests unitaires + intégration | 3-4 jours |
| **Total** | | **~20-28 jours de développement** |

**Recommendation pour le PoC** : Se concentrer sur les Phases 0, 1, 2 et un test de bout en bout simplifié (sans les entités de groupe). Cela représente environ **7-10 jours** et permettra de valider l'approche avant d'investir dans les phases suivantes.

## Annexe D : Analyse de performance

### D.1 Scénario de référence

Pour chiffrer les coûts, prenons un cas réaliste :

| Paramètre | Valeur | Justification |
|---|---|---|
| Population initiale | N = 1 000 000 personnes | Enquête ménages type |
| Ménages | 400 000 | ~2,5 personnes/ménage |
| Autres groupes | 2 types (famille, foyer fiscal) | France |
| Variables | V = 500 | openfisca-france en a ~800 |
| Périodes simulées | P = 30 ans | Projection démographique |
| Croissance population | +0,5% / an | ≈ 1 150 000 personnes en fin |
| Variables effectivement calculées | V_eff = 100 par période | Evaluation lazy |
| Taille d'un float64 | 8 octets | numpy standard |
| Taille d'un int32 | 4 octets | IDs, rôles |

### D.2 Stockage : mode statique (référence)

En mode statique actuel, grâce à l'évaluation lazy, seules les variables
demandées sont stockées :

```
Mémoire = V_eff × N × 8 octets × P_effectif
        = 100 × 1M × 8 × 1 (une seule période en général)
        = 800 Mo
```

En pratique, OpenFisca utilise souvent une seule période (cross-section),
donc le stockage est ~800 Mo.

### D.3 Surcoût de stockage en mode dynamique

Le mode dynamique ajoute les structures suivantes **par période** :

| Structure | Taille par période | × 30 périodes | Description |
|---|---|---|---|
| `_id_to_rownum` | N_max × 4 octets = 4,6 Mo | 138 Mo | Mapping id → position |
| `_members_entity_id_index` | N × 4 × 3 groupes = 12 Mo | 360 Mo | Composition ménage/famille/foyer |
| `_members_role_index` | N × 4 × 3 groupes = 12 Mo | 360 Mo | Rôle dans chaque groupe |
| `_permanent_ids` snapshot | N × 4 octets = 4 Mo | 120 Mo | Qui existe à chaque période |
| **Sous-total structures** | **~33 Mo / période** | **~978 Mo** | |

Et les **arrays de variables** de taille variable :

| Structure | Taille par période | × 30 périodes | Description |
|---|---|---|---|
| Variables calculées (taille variable) | V_eff × N(t) × 8 = 800 Mo | ~25 Go | Arrays de taille différente à chaque période |
| **Total maximum théorique** | | **~26 Go** | Si on garde tout |

**Mais en pratique**, on ne garde pas tout. Voir les optimisations ci-dessous.

### D.4 Surcoût de temps de calcul

| Opération | Coût | Fréquence | Impact |
|---|---|---|---|
| Hook `on_calculate` (frontière temporelle) | O(1) | Chaque `calculate()` | **Négligeable** |
| Hook `on_evolve` (vérification) | O(1) | Chaque `evolve()` | **Négligeable** |
| `_snapshot_composition()` | O(N) — copie d'arrays | 1 fois par période | **~15 ms** pour 1M personnes |
| `add_individuals()` | O(N_new + N_old) — concaténation | 1 fois par période | **~5 ms** pour 5000 naissances |
| `remove_individuals()` | O(N) — filtrage + re-indexation | 1 fois par période | **~20 ms** pour 1M personnes |
| `_remap_to_current_population()` | O(N) — vectorisé numpy | Chaque accès passé | **~10 ms** pour 1M personnes |
| `calculate()` standard (inchangé) | O(N) | Chaque variable | Identique au mode statique |

**Surcoût total par période** (hors calcul de variables) :

```
snapshot + mutations + quelques remappings
≈ 15 ms + 25 ms + 10 × 10 ms
≈ 140 ms par période
```

Sur 30 périodes : **~4 secondes** de surcoût total, ce qui est négligeable
par rapport au temps de calcul des variables elles-mêmes (typiquement
plusieurs minutes pour 1M individus × 100 variables).

### D.5 Optimisations

#### Optimisation 1 : Fenêtre glissante (rolling window)

La plupart des formulas ne regardent que quelques périodes en arrière
(typiquement 1-2 ans pour les revenus, rarement plus de 5 ans).
On peut ne conserver que les K dernières périodes en mémoire :

```python
class Simulation:
    def __init__(self, ..., history_window=5):
        self._history_window = history_window

    def _cleanup_old_periods(self):
        """Supprimer les snapshots plus vieux que la fenêtre."""
        if self.current_period is None:
            return
        cutoff = self.current_period - self._history_window
        for pop in self.populations.values():
            old_periods = [
                p for p in pop._period_index
                if p < cutoff
            ]
            for p in old_periods:
                del pop._period_index[p]
                if hasattr(pop, '_members_entity_id_index'):
                    pop._members_entity_id_index.pop(p, None)
                    pop._members_role_index.pop(p, None)
```

**Gain** : Au lieu de ~1 Go de structures, on stocke seulement
~33 Mo × 5 = **165 Mo**. Réduction de **85%**.

#### Optimisation 2 : Remapping lazy avec cache

Ne remapper un array que la première fois qu'il est demandé pour la
population courante, puis le cacher :

```python
class Holder:
    _remapped_cache: dict[tuple[Period, int], ndarray] = {}

    def _remap_to_current_population(self, values, period):
        cache_key = (period, self.population.count)
        if cache_key in self._remapped_cache:
            return self._remapped_cache[cache_key]

        result = self._do_remap(values, period)  # le vrai travail
        self._remapped_cache[cache_key] = result
        return result
```

**Gain** : Évite de remapper N fois le même array si plusieurs variables
le demandent. Les remappings passent de O(V_eff × N) à O(N) amorti.

#### Optimisation 3 : Nettoyage des variables intermédiaires (GC)

Beaucoup de variables sont **intermédiaires** — elles ne sont utilisées
que pour calculer d'autres variables et ne sont jamais relues ensuite.
On peut les supprimer une fois utilisées :

```python
class Simulation:
    def gc_variable(self, variable_name, period=None):
        """Supprimer une variable du cache pour libérer de la mémoire.

        À appeler après que la variable n'est plus nécessaire.
        """
        population = self.get_variable_population(variable_name)
        holder = population.get_holder(variable_name)
        if period:
            holder.delete_arrays(period)
        else:
            holder.delete_arrays()

    def gc_period(self, period, keep=None):
        """Supprimer toutes les variables d'une période, sauf cells à garder.

        Args:
            period: Période à nettoyer.
            keep: Set de noms de variables à conserver.
        """
        keep = keep or set()
        for pop in self.populations.values():
            for var_name, holder in pop._holders.items():
                if var_name not in keep:
                    holder.delete_arrays(period)
```

**Utilisation typique** :

```python
for year in range(2020, 2050):
    period = periods.period(year)
    simulation.evolve(period, processes=[births, deaths])

    # Calculer les variables d'intérêt
    revenu = simulation.calculate("revenu_disponible", period)
    impot = simulation.calculate("impot_revenu", period)

    # Sauvegarder les résultats dans un fichier externe
    save_results(period, revenu, impot)

    # Nettoyer : garder seulement les variables nécessaires
    # pour les formulas futures (cells qui regardent le passé)
    simulation.gc_period(period, keep={"revenu_net", "age", "household_id"})
```

**Gain** : Au lieu de garder V_eff = 100 variables par période,
on n'en garde que 5-10. Réduction mémoire de **90-95%** sur les arrays
de variables.

#### Optimisation 4 : Stockage delta

Au lieu de copier entièrement `members_entity_id` à chaque période,
ne stocker que les **changements** (delta) par rapport à la période précédente :

```python
class GroupPopulation:
    def _snapshot_composition_delta(self, period, prev_period):
        """Stocker seulement les indices qui ont changé."""
        prev = self._members_entity_id_index.get(prev_period)
        current = self._members_entity_id

        if prev is not None and len(prev) == len(current):
            changed = prev != current
            n_changed = changed.sum()

            if n_changed < len(current) * 0.1:  # < 10% de changements
                # Stocker le delta : indices + nouvelles valeurs
                self._members_entity_id_index[period] = {
                    'type': 'delta',
                    'base': prev_period,
                    'indices': numpy.where(changed)[0],
                    'values': current[changed],
                }
                return

        # Fallback : copie complète si trop de changements
        self._members_entity_id_index[period] = current.copy()
```

**Gain** : Si seuls 1% des individus changent de ménage par période
(réaliste), chaque snapshot passe de 4 Mo à **~80 Ko**. Sur 30 périodes :
de 120 Mo à **~2,4 Mo**.

#### Optimisation 5 : Périodes anciennes sur disque

Utiliser le `OnDiskStorage` existent d'OpenFisca pour les périodes
anciennes qui ne sont plus dans la fenêtre glissante mais pourraient
être demandées occasionnellement :

```python
class Holder:
    def _evict_to_disk(self, period):
        """Déplacer un array de la mémoire vers le disque."""
        array = self._memory_storage.get(period)
        if array is not None:
            self._disk_storage.put(array, period)
            self._memory_storage.delete(period)
```

**Gain** : Mémoire libérée pour les anciennes périodes, accès toujours
possible mais plus lent (disque).

#### Optimisation 6 : Pré-allocation

Au lieu de concaténer des arrays à chaque `add_individuals()` (coûteux :
copie de l'ancien + nouveau), pré-allouer un buffer plus grand :

```python
class CorePopulation:
    _buffer_size: int = 0       # taille réelle du buffer
    _active_count: int = 0      # nombre d'individus actifs

    def _ensure_capacity(self, needed):
        """Doubler la capacité si le buffer est plein."""
        if needed > self._buffer_size:
            new_size = max(needed, self._buffer_size * 2)
            # Realloquer une seule fois
            ...

    @property
    def count(self):
        return self._active_count  # pas la taille du buffer
```

**Gain** : La complexité amortie de `add_individuals()` passe de
O(N_old + N_new) à **O(N_new)** amorti (comme `list.append()` en Python).

### D.6 Bilan avec optimisations

| Resource | Sans optimisation | Avec optimisations | Réduction |
|---|---|---|---|
| **Structures dynamiques** | ~1 Go (30 périodes) | ~165 Mo (fenêtre 5) | **-85%** |
| **Variables en cache** | ~25 Go (30 × 100 vars) | ~800 Mo (GC + fenêtre) | **-97%** |
| **Composition (snapshot)** | ~120 Mo | ~2,4 Mo (delta) | **-98%** |
| **Total mémoire** | ~26 Go | **~1 Go** | **-96%** |
| **Temps surcoût/période** | ~140 ms | ~100 ms (cache remap) | **-30%** |
| **Temps total surcoût** | ~4 s | ~3 s | Négligeable |

### D.7 Recommendations par phase

| Phase | Optimisations à implémenter | Priorité |
|---|---|---|
| **PoC** | Aucune (garder simple) | — |
| **Phase 1** | Fenêtre glissante (opt. 1) + GC basique (opt. 3) | Haute |
| **Phase 2** | Cache remap (opt. 2) + pré-allocation (opt. 6) | Moyenne |
| **Phase 3** | Delta storage (opt. 4) + disque (opt. 5) | Basse |

L'approche recommandée est de **ne pas optimiser prématurément** :
commencer par l'implémentation naïve, mesurer les goulots d'étranglement
réels sur un cas d'usage concret, puis appliquer les optimisations
ciblées. Les optimisations 1 et 3 (fenêtre + GC) suffisent pour la
grande majorité des cas d'usage.

#### Optimisation 7 : Planificateur de simulation (passe à blanc)

L'idée est de décrire l'exercice à l'avance — quelles variables calculer,
à quels instants, avec quel scénario d'évolution de population — et de
faire une **passe d'analyse** avant l'exécution pour déterminer ex ante :

- Combien de mémoire il faut pré-allouer
- Quelles variables garder en RAM et pour combien de temps
- Lesquelles évacuer en priorité (et quand les recalculer si nécessaire)
- Quand sauvegarder sur disque plutôt qu'effacer

C'est le même problème que l'**allocation de registres** dans un compilateur,
ou le **plan d'exécution** d'un motor de base de données.

**Étape 1 : Déclarer l'exercice**

```python
from openfisca_core.planner import SimulationPlan, MONTH, YEAR

plan = SimulationPlan(
    start_period="2020",
    end_period="2050",
    mutation_frequency=MONTH,
    initial_population=1_000_000,
    growth_rate=0.005,   # +0.5% / an

    # Quelles variables calculer et à quel rythme
    variables_to_compute={
        "salaire_net": MONTH,         # chaque mois
        "cotisations": MONTH,          # chaque mois
        "impot_revenu": YEAR,          # chaque année
        "revenu_disponible": YEAR,     # chaque année
    },

    # Quelles variables sauvegarder en sortie
    variables_to_output={"revenu_disponible", "impot_revenu"},

    # Budget mémoire maximum
    memory_budget_gb=8,
)
```

**Étape 2 : Analyse des dépendances (passe à blanc)**

Le planificateur parcourt le graphe de dépendances des variables
déclarées et calcule la **durée de via** de chaque variable :

```python
class SimulationPlanner:
    """Analyse statique d'un exercise de simulation."""

    def analyze(self, plan: SimulationPlan,
                tax_benefit_system: TaxBenefitSystem) -> ExecutionPlan:
        """Passe à blanc : analyse sans rien calculer."""

        # 1. Construire le graphe de dépendances
        dep_graph = self._build_dependency_graph(
            plan.variables_to_compute, tax_benefit_system)

        # 2. Calculer la durée de via de chaque variable
        #    = écart entre la période de calcul et la dernière
        #      période où une autre variable en a besoin
        lifetimes = {}
        for var, freq in plan.variables_to_compute.items():
            # Regarder quelles variables dépendent de var
            # et à quel décalage temporel
            max_lookback = self._max_lookback(var, dep_graph)
            lifetimes[var] = max_lookback
            # Ex: salaire_net est lu par impot_revenu
            #     avec options=[ADD] sur 12 mois
            #     → lifetime = 12 mois

        # 3. Estimer la mémoire nécessaire à chaque instant
        peak_memory = self._estimate_peak_memory(
            plan, lifetimes)

        # 4. Générer la stratégie d'éviction
        eviction_schedule = self._plan_evictions(
            plan, lifetimes, peak_memory)

        return ExecutionPlan(
            lifetimes=lifetimes,
            peak_memory_gb=peak_memory,
            eviction_schedule=eviction_schedule,
            fits_in_memory=peak_memory <= plan.memory_budget_gb,
            needs_disk=peak_memory > plan.memory_budget_gb,
        )
```

**Étape 3 : Résultat de l'analyse**

```python
exec_plan = planner.analyze(plan, tbs)

print(exec_plan)
# Variable lifetimes:
#   salaire_net    : 12 mois (lu par impot_revenu via ADD)
#   cotisations    : 1 mois  (non relu après calcul)
#   impot_revenu   : 1 an    (lu par revenu_disponible)
#   revenu_disponible : 0    (variable de sortie, sauvegardé directement)
#   age            : ∞       (ETERNITY, jamais évacué)
#   household_id   : ∞       (composition, jamais évacué)
#
# Peak memory: 2.3 Go (à mois 12 de chaque année)
# Budget: 8 Go → ✅ Tout tient en RAM
#
# Eviction schedule (par période) :
#   Après chaque mois :
#     - évacuer cotisations (non relu)
#   Après chaque année :
#     - évacuer salaire_net des 12 mois
#     - évacuer impot_revenu (après calcul de revenu_disponible)
#     - sauvegarder revenu_disponible vers sortie
```

**Étape 4 : Exécution avec le plan**

```python
# Au lieu de gérer manuellement le GC :
simulation.execute(exec_plan)

# Ou bien : le plan est utilisé automatiquement par la boucle
for year in range(2020, 2050):
    for month in range(1, 13):
        period = periods.period(f"{year}-{month:02d}")
        simulation.evolve(period, processes=[births, deaths])
        simulation.calculate("salaire_net", period)
        simulation.calculate("cotisations", period)

        # Le plan dit : cotisations peut être évacuée maintenant
        exec_plan.apply_evictions(simulation, period)

    year_period = periods.period(year)
    simulation.calculate("impot_revenu", year_period)
    simulation.calculate("revenu_disponible", year_period)

    # Le plan dit : sauvegarder revenu_disponible,
    # évacuer salaire_net et impot_revenu
    exec_plan.apply_evictions(simulation, year_period)
```

**Ce que permet la passe à blanc** :

| Ce qu'on apprend | Comment | Utilité |
|---|---|---|
| **Mémoire pic** | Some des variables vivantes au pire moment | Savoir si ça tient en RAM |
| **Durée de via** par variable | Écart max entre period et dernier lecteur | Savoir quand évacuer |
| **Variables intermédiaires** | Cells qui ne sont lues que 1 fois | Évacuation immédiate |
| **Variables longue durée** | Cells lues avec lookback (ex: `ADD` sur 12 mois) | Garder K périodes |
| **Besoin disque** | Si pic > budget RAM | Planifier les écritures disque |
| **Pré-allocation** | N(t) pour chaque période | Allouer les buffers à l'avance |

**Analogie** :

| Domaine | Équivalent |
|---|---|
| Compilateur | Allocation de registres (variables → registres/mémoire) |
| Base de données | Plan d'exécution de requête (EXPLAIN ANALYZE) |
| Ordonnanceur OS | Scheduling de tâches avec contraintes mémoire |

**Coût de la passe à blanc** : O(V × P) dans le pire cas (V variables, P périodes),
mais avec des constantes très faibles (pas de calcul numérique, juste du parcours
de graphe). Pour 500 variables × 360 périodes mensuelles = 180 000 opérations
de graphe, soit **< 1 seconde**.

### D.8 Recommendations révisées avec le planificateur

| Phase | Optimisations | Priorité |
|---|---|---|
| **PoC** | Aucune (garder simple) | — |
| **Phase 1** | Fenêtre glissante (opt. 1) + GC basique (opt. 3) | Haute |
| **Phase 2** | Cache remap (opt. 2) + pré-allocation (opt. 6) | Moyenne |
| **Phase 3** | Planificateur (opt. 7) : passe à blanc + éviction auto | Moyenne |
| **Phase 4** | Delta storage (opt. 4) + disque (opt. 5) | Basse |

Le planificateur (opt. 7) est une optimisation de **phase 3** : il n'est pas
nécessaire pour le PoC ni pour les premiers cas d'usage, mais il devient
précieux dès qu'on fait des simulations longues (30+ ans) avec un budget
mémoire constraint. Il transforme le GC manuel (opt. 3) en un GC **automatique
et optimal**.

## Annexe E : Analyse des backends de données (RAM / disque)

### E.1 Backend actuel d'OpenFisca : dict Python + fichiers `.npy`

#### RAM : `InMemoryStorage`

```python
# openfisca_core/data_storage/in_memory_storage.py
class InMemoryStorage:
    _arrays: dict[Period, ndarray]      # dict Python basique

    def get(self, period) -> ndarray:
        return self._arrays.get(period)   # lookup O(1)

    def put(self, value, period):
        self._arrays[period] = value      # insertion O(1)
```

- **Technologie** : dict Python standard + arrays numpy
- **Avantage** : Ultra-simple (~200 lignes), zéro dépendance
- **Limit** : Pas de compression, pas de partage mémoire, pas d'éviction
  automatique, GC entièrement manuel

#### Disque : `OnDiskStorage`

```python
# openfisca_core/data_storage/on_disk_storage.py
class OnDiskStorage:
    def put(self, value, period):
        path = f"{self.storage_dir}/{period}.npy"
        numpy.save(path, value)           # format brut, non compressé

    def get(self, period):
        return numpy.load(path)           # lecture complète en RAM
```

- **Technologie** : fichiers `.npy` individuals (un par variable × période)
- **Avantage** : Format natif numpy, rapide en lecture/écriture
- **Limites** :
  - **Pas de compression** : 1M float64 = 8 Mo par fichier, toujours
  - **Un fichier par variable × période** : 500 vars × 30 périodes = 15 000 fichiers
  - **Pas de memory-mapping** : `numpy.load()` charge tout en RAM
  - **Pas de lecture partielle** : impossible de ne lire qu'un sous-ensemble

### E.2 Backend de LIAM2 : ColumnArray + HDF5/PyTables

#### RAM : `ColumnArray`

```python
# liam2/data.py
class ColumnArray:
    columns: dict[str, ndarray]    # une array par champ
    dtype: np.dtype                # schéma structuré

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.columns[key]      # accès par colonne O(1)
        else:
            # slicing : filtre chaque colonne
            return ColumnArray({k: v[key] for k, v in self.columns.items()})

    def append(self, other):
        for name, col in self.columns.items():
            self.columns[name] = np.concatenate((col, other[name]))
```

- **Technologie** : stockage columnar (une ndarray par champ)
- **Avantage** : Accès par colonne rapide, extension (append) simple
- **Limit** : Pas de compression, append coûteux (copie O(N))

#### Disque : HDF5 via PyTables

```python
# liam2/data.py, simulation.py
import tables  # PyTables

# Lecture par chunks de 10 Mo
def from_table(cls, table, start=0, stop=None, buffersize=10 * MB):
    ca = cls.empty(numlines, dtype)
    chunk = np.empty(buffer_rows, dtype=dtype)
    while numlines > 0:
        table.read(table_start, table_start + buffer_rows, out=chunk)
        ...
```

- **Technologie** : un seul fichier HDF5, tables structurées par période/entité
- **Advantages** :
  - **Fichier unique** : pas 15 000 fichiers
  - **Lecture par chunks** : ne charge pas tout en RAM
  - **Compression blosc** : ~3-5× réduction de taille
  - **Indexation** : accès direct par période via `index_table()`
- **Limites** :
  - **PyTables** est peu maintenu (dépendance fragile)
  - **HDF5** : format binaire complexe, pas facilement interopérable
  - Pas de memory-mapping efficace pour les tables structurées

### E.3 Comparison OpenFisca vs LIAM2

| Critère | OpenFisca | LIAM2 |
|---|---|---|
| **Format RAM** | dict de ndarray (row-oriented) | ColumnArray (column-oriented) |
| **Format disque** | `.npy` (un fichier par var/période) | HDF5 (fichier unique) |
| **Compression** | ❌ Non | ✅ blosc (3-5×) |
| **Chunked I/O** | ❌ Non (load tout) | ✅ Oui (10 Mo) |
| **Nb fichiers** | 15 000+ | 1 |
| **Memory-map** | ❌ Non | 🟡 Partiel |
| **Dépendance** | numpy seul | numpy + PyTables |
| **Complexité** | ~500 lignes | ~1000 lignes |
| **Interopérabilité** | 🟡 `.npy` | 🟡 HDF5 |

### E.4 Technologies modernes à considérer

#### Option 1 : Apache Arrow + Polars

**Qu'est-ce que c'est ?** Format columnar en mémoire, zero-copy, interopérable.

```python
import pyarrow as pa
import polars as pl

# Écriture (compressé, columnar)
table = pa.table({"salary": salaries, "age": ages})
pa.parquet.write_table(table, "period_2024.parquet",
                        compression="zstd")  # ratio ~5-10×

# Lecture (memory-mapped, zero-copy)
table = pa.parquet.read_table("period_2024.parquet",
                               columns=["salary"])  # lecture sélective !
salary = table["salary"].to_numpy()

# Ou avec Polars (plus rapide que pandas)
df = pl.scan_parquet("period_2024.parquet")
result = df.select("salary").filter(pl.col("age") > 18).collect()
```

| Avantage | Détail |
|---|---|
| **Compression** | zstd : ratio 5-10× vs `.npy` brut |
| **Lecture sélective** | Ne charger que les colonnes nécessaires |
| **Memory-mapping** | `mmap=True` → pas de copie en RAM |
| **Zero-copy** | Partageable entre processus sans sérialisation |
| **Interopérable** | Lisible par Python, R, Julia, Spark, DuckDB |
| **Très maintenu** | Apache Foundation, Google, Meta contribuent |

| Inconvénient | Détail |
|---|---|
| Dépendance | `pyarrow` (~200 Mo d'install) |
| Conversion | ndarray → Arrow → ndarray (surcoût initial) |

**Verdict** : ✅ **Meilleur candidate** pour remplacer `.npy` et HDF5.

#### Option 2 : numpy memory-mapped files

```python
# Écriture
np.save("salary_2024.npy", salary)

# Lecture memory-mapped (pas de chargement en RAM)
salary = np.load("salary_2024.npy", mmap_mode='r')
# L'OS charge les pages à la demande, le kernel gère le cache
```

| Avantage | Détail |
|---|---|
| **Zéro dépendance** | numpy seul |
| **Lazy loading** | L'OS charge à la demande (via mmap) |
| **Simple** | 1 ligne de changement dans `OnDiskStorage` |

| Inconvénient | Détail |
|---|---|
| Pas de compression | Même taille que `.npy` |
| Un fichier par var | Toujours 15 000 fichiers |
| Pas de lecture partielle | Le mmap aide mais pas de filtre colonne |

**Verdict** : 🟡 **Quick win** (1 ligne de changement), mais limité.

#### Option 3 : Lance (format columnar moderne)

```python
import lance

# Écriture
ds = lance.write_dataset(pa.table({"salary": salary}),
                          "simulation.lance")

# Lecture sélective + versionnée
salary = ds.to_table(columns=["salary"],
                      filter="period = 2024").to_pandas()
```

| Avantage | Détail |
|---|---|
| **Versionné** | Chaque période = une version, pas de fichier séparé |
| **Filtrage** | Lecture sélective par période, colonne, condition |
| **Compression** | zstd, ~5-10× |

| Inconvénient | Détail |
|---|---|
| Jeune | Moins mature qu'Arrow/Parquet |
| Dépendance | `pylance` |

**Verdict** : 🟡 Intéressant pour le versionnement par période, mais encore jeune.

#### Option 4 : DuckDB (base analytique embeddée)

```python
import duckdb

# Écriture
con = duckdb.connect("simulation.duckdb")
con.execute("""
    CREATE TABLE salary AS
    SELECT * FROM read_parquet('period_*.parquet')
""")

# Agrégation directe (sans charger en RAM !)
result = con.execute("""
    SELECT household_id, SUM(salary) as total
    FROM salary
    WHERE period = 2024 AND role = 'CHILD'
    GROUP BY household_id
""").fetchnumpy()
```

| Avantage | Détail |
|---|---|
| **SQL** | Agrégations (sum, count, avg...) sans code numpy |
| **Streaming** | Ne charge pas tout en RAM |
| **Compression** | Très bon ratio |
| **Out-of-core** | Gère automatiquement le spill disque |

| Inconvénient | Détail |
|---|---|
| Overhead | Conversion SQL → résultat pour chaque calcul |
| Modèle | Relationnel, pas vectoriel (changement de paradigme) |

**Verdict** : 🟡 Puissant pour l'analytique, mais changement de paradigme trop
important pour le cœur d'OpenFisca. Utile en **post-traitement** des résultats.

#### Option 5 : Zarr (arrays N-D compressées, chunked)

```python
import zarr

# Écriture
store = zarr.DirectoryStore("simulation.zarr")
root = zarr.group(store)
root.create_dataset("salary/2024",
                     data=salary,
                     chunks=(100000,),     # chunks de 100K éléments
                     compressor=zarr.Blosc(cname='zstd'))

# Lecture (lazy, chunked)
salary = root["salary/2024"][:]           # tout
salary_chunk = root["salary/2024"][0:1000]  # partiel
```

| Avantage | Détail |
|---|---|
| **Chunked** | Lecture partielle par tranche |
| **Compression** | blosc/zstd, très rapide |
| **Structure hiérarchique** | `variable/période` — naturel pour OpenFisca |
| **Cloud-ready** | S3, GCS, Azure Blob comme backend |

| Inconvénient | Détail |
|---|---|
| Pas columnar | Chaque variable = un dataset (c'est déjà le cas en OpenFisca) |
| Dépendance | `zarr` (léger ~1 Mo) |

**Verdict** : ✅ **Très bon candidate** — la structure hiérarchique
variable/période correspond exactement à l'organisation d'OpenFisca.

#### Option 6 : Shared Memory (multiprocessing.shared_memory)

```python
from multiprocessing import shared_memory

# Créer un block partagé
shm = shared_memory.SharedMemory(name="salary_2024",
                                   create=True,
                                   size=salary.nbytes)
shared_array = np.ndarray(salary.shape, dtype=salary.dtype,
                           buffer=shm.buf)
shared_array[:] = salary[:]

# Autre processus : accès zero-copy
shm2 = shared_memory.SharedMemory(name="salary_2024")
salary = np.ndarray(shape, dtype=np.float64, buffer=shm2.buf)
```

| Avantage | Détail |
|---|---|
| **Zero-copy** | Partagé entre processus sans sérialisation |
| **Stdlib** | Aucune dépendance externe |
| **Rapide** | Pas de copie, pas de I/O |

| Inconvénient | Détail |
|---|---|
| Complexe | Gestion manuelle du cycle de via |
| Local | Même machine uniquement |

**Verdict** : 🟡 Utile pour le parallélisme, pas pour le stockage.

### E.5 Tableau comparatif

| Technologie | Compression | Lecture sélective | Memory-map | Dépendance | Interop. | Maturité | Effort intégration |
|---|---|---|---|---|---|---|---|
| `.npy` (actuel) | ❌ | ❌ | 🟡 mmap_mode | aucune | 🟡 | ✅ | — |
| HDF5/PyTables (LIAM2) | ✅ blosc | 🟡 chunks | 🟡 | PyTables | 🟡 | ✅ | Moyen |
| **Arrow/Parquet** | ✅ zstd 5-10× | ✅ colonnes | ✅ | pyarrow | ✅✅ | ✅✅ | Moyen |
| **Zarr** | ✅ blosc/zstd | ✅ chunks | ✅ | zarr | ✅ | ✅ | Faible |
| DuckDB | ✅ | ✅ SQL | ✅ auto | duckdb | ✅ | ✅ | Élevé |
| Lance | ✅ | ✅ + versions | ✅ | pylance | 🟡 | 🟡 | Moyen |
| numpy mmap | ❌ | ❌ | ✅ | aucune | 🟡 | ✅ | **1 ligne** |
| SharedMemory | ❌ | ❌ | ✅ | stdlib | ❌ | ✅ | Élevé |

### E.6 Recommendation : stratégie par couche

```
┌──────────────────────────────────────────────────┐
│         API OpenFisca (inchangée)                 │
│  simulation.calculate("salary", "2024")           │
├──────────────────────────────────────────────────┤
│         Holder (couche d'abstraction)             │
│  get_array(period) → ndarray                      │
│  put_in_cache(array, period)                      │
├──────────────────────────────────────────────────┤
│  Backend pluggable (nouveau)                      │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │ InMemory   │ │ Zarr       │ │ Arrow/Parquet│  │
│  │ (actuel)   │ │ (chunked,  │ │ (columnar,   │  │
│  │            │ │ compressé) │ │ interop)     │  │
│  └────────────┘ └────────────┘ └──────────────┘  │
└──────────────────────────────────────────────────┘
```

#### Phase 1 : Quick win — numpy mmap (1 ligne)

```python
# OnDiskStorage.get() : ajouter mmap_mode
def get(self, period):
    return numpy.load(path, mmap_mode='r')  # ← seul changement
```

Gain : les fichiers ne sont plus chargés en RAM, l'OS gère le cache.

#### Phase 2 : Zarr comme backend hybride

Zarr est le replacement naturel d'`OnDiskStorage` car sa structure
(variable/période → array compressée) correspond exactement à OpenFisca :

```python
class ZarrStorage:
    """Backend Zarr : compression + chunked + hiérarchique."""

    def __init__(self, path, compressor=None):
        self._store = zarr.DirectoryStore(path)
        self._root = zarr.group(self._store)
        self._compressor = compressor or zarr.Blosc(cname='zstd', clevel=3)

    def put(self, value, period, variable_name):
        key = f"{variable_name}/{period}"
        self._root.create_dataset(
            key, data=value, overwrite=True,
            chunks=(min(100_000, len(value)),),
            compressor=self._compressor,
        )

    def get(self, period, variable_name):
        key = f"{variable_name}/{period}"
        if key in self._root:
            return self._root[key][:]
        return None
```

Gain : compression 5×, lecture partielle, un seul répertoire structuré.

#### Phase 3 : Arrow/Parquet pour l'interopérabilité

Quand il faut échanger des données avec d'autres outils (R, Spark, etc.)
ou faire du post-traitement analytique, exporter en Parquet :

```python
class ParquetExporter:
    """Export des résultats de simulation en Parquet."""

    def export_period(self, simulation, period, variables, path):
        columns = {}
        for var in variables:
            columns[var] = simulation.calculate(var, period)
        table = pa.table(columns)
        pa.parquet.write_table(table, f"{path}/{period}.parquet",
                                compression="zstd")
```

### E.7 Gains attendus

| Métrique | Actuel (`.npy`) | Zarr (Phase 2) | Gain |
|---|---|---|---|
| **Taille disque** (1M pers, 100 vars, 1 période) | 800 Mo | ~160 Mo | **5×** |
| **Taille disque** (30 périodes) | 24 Go | ~5 Go | **5×** |
| **Nb fichiers** | 3 000 | 1 répertoire | **∞** |
| **Temps écriture** (1M float64) | ~50 ms | ~30 ms (+ compression) | **1,7×** |
| **Temps lecture** (1M float64) | ~50 ms | ~20 ms (décompression rapide) | **2,5×** |
| **Lecture partielle** (100K sur 1M) | 50 ms (charge tout) | ~5 ms | **10×** |

### E.8 Zarr vs Arrow/Parquet : analyse approfondie

#### Le modèle de données

La différence fondamentale est le **modèle de données** :

```
ZARR : tableau N-dimensionnel (comme un fichier numpy, mais chunked/compressé)
┌─────────────────────────────────────────┐
│  salary/2024-01  →  [3000, 2500, ...]   │  1 variable, 1 période = 1 array 1D
│  salary/2024-02  →  [3000, 2600, ...]   │
│  age/eternity    →  [32, 45, 2, ...]    │
│  tax/2024        →  [1200, 900, ...]    │
└─────────────────────────────────────────┘
Structure hiérarchique : variable/période → array

PARQUET : table relationnelle (lignes × colonnes)
┌──────────┬─────────┬─────┬──────┐
│ person_id│ salary  │ age │ tax  │  Toutes les colonnes ensemble
├──────────┼─────────┼─────┼──────┤
│ 0        │ 3000    │ 32  │ 1200 │
│ 1        │ 2500    │ 45  │ 900  │
│ 2        │ 0       │ 2   │ 0    │
└──────────┴─────────┴─────┴──────┘
Structure tabulaire : 1 fichier = N colonnes × M lignes
```

Or OpenFisca stocke ses données **une variable à la fois** (un Holder
par variable, un array par période). C'est exactement le modèle Zarr.

#### Scénario 1 : Cache interne (pendant la simulation)

Pendant la simulation, le motor accède aux données **une variable à la fois** :

```python
salary = simulation.calculate("salary", "2024-01")
# → le Holder va chercher un SEUL array de 1M floats
```

**Zarr gagne** — accès naturel :

```python
# Zarr : une ligne
salary = root["salary"]["2024-01"][:]  # → ndarray directement

# Parquet : overhead de conversion
table = pq.read_table("2024-01.parquet", columns=["salary"])
salary = table["salary"].to_numpy()  # conversion Arrow → numpy
```

#### Scénario 2 : Export des résultats (après la simulation)

Après la simulation, on veut exporter **toutes les variables ensemble** :

```python
# "Donne-moi salary, age, tax pour toutes les personnes"
# → pour ouvrir dans R, DuckDB, Polars, ou un notebook
```

**Parquet gagne** — format tabulaire natif :

```python
# Parquet : une ligne
df = pl.read_parquet("results_2024.parquet")
df.filter(pl.col("age") > 18).select("salary", "tax")

# Zarr : assemblage manuel colonne par colonne
salary = root["salary"]["2024"][:]
age = root["age"]["eternity"][:]
tax = root["tax"]["2024"][:]
df = pd.DataFrame({"salary": salary, "age": age, "tax": tax})
```

#### Scénario 3 : Populations dynamiques (taille variable)

Quand la population change de taille entre les périodes :

```python
# 2024 : 1 000 000 personnes
# 2025 : 1 005 000 personnes (naissances)
# 2026 : 1 009 500 personnes
```

**Zarr gagne** — chaque dataset a sa propre taille :

```python
# Zarr : chaque période a sa propre taille, aucun problème
root["salary"]["2024"]  # shape: (1_000_000,)
root["salary"]["2025"]  # shape: (1_005_000,)

# Parquet : une table = une taille fixe
# Il faut un fichier par période, ou ajouter une colonne "period"
# et gérer les individus absents (valeurs nulles)
```

#### Comparison détaillée

| Critère | Zarr | Arrow/Parquet |
|---|---|---|
| **Modèle** | Arrays N-D (comme numpy) | Tables (comme pandas/SQL) |
| **Unité de stockage** | 1 variable/période = 1 dataset | 1 fichier = N variables × M personnes |
| **Accès typique** | `root["salary"]["2024"][:]` | `pq.read_table(f, columns=["salary"])` |
| **Écriture incrémentale** | ✅ Un dataset à la fois | 🟡 Possible mais pas naturel |
| **Append (nouvelles personnes)** | ✅ Resize le dataset | 🔴 Réécrire le fichier |
| **Taille variable par période** | ✅ Natif | 🔴 1 fichier par période |
| **Structure hiérarchique** | ✅ Groupes/sous-groupes | ❌ Plat |
| **Interopérabilité** | 🟡 Python, Julia, R | ✅✅ Python, R, Spark, DuckDB, Polars |
| **Écosystème analytique** | ❌ Pas de SQL, pas de Polars | ✅✅ DuckDB, Polars, Spark natifs |
| **Dépendance Python** | `zarr` (~1 Mo) | `pyarrow` (~200 Mo) |
| **Compression** | blosc/zstd par chunk | zstd/snappy par page de colonne |
| **Maturité** | ✅ Stable (v2→v3) | ✅✅ Standard de facto |

#### Architecture recommandée : les deux pour des usages différents

```
┌─────────────────────────────────────────────────────┐
│                  OpenFisca                           │
│                                                     │
│  ┌──────────────────────────────────────┐           │
│  │  SIMULATION (motor de calcul)       │           │
│  │                                      │           │
│  │  InMemoryStorage (dict → ndarray)    │  ← RAM    │
│  │         ↕ éviction                   │           │
│  │  ZarrStorage (variable/période)      │  ← DISQUE │
│  │                                      │           │
│  └────────────────┬─────────────────────┘           │
│                   │ export                           │
│  ┌────────────────▼─────────────────────┐           │
│  │  SORTIE (analyse, publication)       │           │
│  │                                      │           │
│  │  Parquet (table complète)            │  ← ÉCHANGE│
│  │  → DuckDB, Polars, R, Spark         │           │
│  └──────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

| Usage | Techno | Pourquoi |
|---|---|---|
| **Cache interne** (pendant la simulation) | **Zarr** | 1 variable/période = 1 dataset, taille variable, léger (~1 Mo de dépendance) |
| **Export/analyse** (après la simulation) | **Parquet** | Tabulaire, interopérable, tout l'écosystème data science |
| **RAM** (calcul en cours) | `InMemoryStorage` (actuel) | Aucun changement nécessaire |

**En résumé** : Zarr **à l'intérieur** (il replace `OnDiskStorage`),
Parquet **à l'extérieur** (il sert de format d'échange). Les deux sont
complémentaires, pas concurrents.

## Annexe F : Performance de calcul et accélération

### F.1 État actuel : ce qui est déjà vectorisé

OpenFisca est **déjà largement vectorisé** grâce à numpy. Les formulas
opèrent sur des arrays completes de tous les individus simultanément :

```python
# Chaque formule est vectorisée (calcul sur 1M individus d'un coup)
class impot_revenu(Variable):
    def formula(person, period):
        revenu = person("revenu_net", period)          # ndarray 1M
        return bareme.calc(revenu)                     # opération vectorisée
```

De plus, les **agrégations groupe** (`sum`, `any`, `count`) utilisent
`numpy.bincount()`, qui est une des opérations les plus rapides de numpy.

OpenFisca utilise aussi déjà **numexpr** (multi-threadé) pour évaluer
des expressions simples.

### F.2 Les points chauds non-vectorisés

L'analyse du code révèle **3 boucles Python** dans le chemin critique :

#### Hotspot 1 : `members_position` — boucle Python O(N)

```python
# group_population.py, ligne 44
# BOUCLE PYTHON sur chaque personne !
for k in range(nb_persons):
    entity_index = self.members_entity_id[k]
    self._members_position[k] = counter_by_entity[entity_index]
    counter_by_entity[entity_index] += 1
```

C'est un calcul de **rang intra-groupe** : pour chaque personne, son
index dans son ménage (0 = première personne, 1 = deuxième, etc.).
Pour 1M de personnes, cette boucle Python prend **~2-5 secondes**.

#### Hotspot 2 : `reduce()` — boucle sur la taille max des groupes

```python
# group_population.py, ligne 156
# Boucle sur le plus grand ménage (typiquement 5-15 personnes)
for p in range(biggest_entity_size):
    values = self.value_nth_person(p, filtered_array, default=neutral_element)
    result = reducer(result, values)
```

Utilisé par `min()`, `max()`, `all()`. La boucle est courte (5-15 itérations)
mais chaque itération fait un `value_nth_person()` qui est O(N).

#### Hotspot 3 : `get_rank()` — matrice dense intermédiaire

```python
# population.py, ligne 129
# Crée une matrice (nb_entities × biggest_entity_size) même si sparse
matrix = numpy.asarray([
    entity.value_nth_person(k, filtered_criteria, default=numpy.inf)
    for k in range(biggest_entity_size)
]).transpose()

sorted_matrix = numpy.argsort(numpy.argsort(matrix))
```

Pour 400K ménages × 15 positions max : une matrice de 6M éléments,
même si la plupart des ménages ont 2-3 personnes.

### F.3 Technologies d'accélération

#### Numba — JIT compilation pour les boucles

**Ce que c'est** : Compilateur JIT qui transforme les functions Python
en code machine LLVM. Idéal pour les boucles sur des arrays numpy.

```python
import numba

# AVANT : boucle Python ~5 secondes pour 1M personnes
def members_position_python(entity_id, nb_entities):
    n = len(entity_id)
    position = numpy.empty(n, dtype=int)
    counter = numpy.zeros(nb_entities, dtype=int)
    for k in range(n):
        idx = entity_id[k]
        position[k] = counter[idx]
        counter[idx] += 1
    return position

# APRÈS : Numba ~5 millisecondes (1000× plus rapide)
@numba.njit
def members_position_numba(entity_id, nb_entities):
    n = len(entity_id)
    position = numpy.empty(n, dtype=numba.int64)
    counter = numpy.zeros(nb_entities, dtype=numba.int64)
    for k in range(n):
        idx = entity_id[k]
        position[k] = counter[idx]
        counter[idx] += 1
    return position
```

| Avantage | Détail |
|---|---|
| **1000× sur les boucles** | Compilation LLVM, cache du résultat |
| **Zéro changement de code** | Juste un décorateur `@numba.njit` |
| **Parallélisme** | `@numba.njit(parallel=True)` + `prange` |
| **Types numpy natifs** | Pas de conversion |

| Inconvénient | Détail |
|---|---|
| Compilation initiale | ~0.5-2s à la première exécution (puis caché) |
| Subset de Python | Pas de dicts, pas de classes, pas d'objets |
| Dépendance | ~100 Mo, dépend de LLVM |

**Verdict** : ✅ **Meilleur candidate** pour les hotspots 1-3.

#### Numpy pur — vectorisation sans boucle

Certains hotspots peuvent être éliminés **sans dépendance** en utilisant
des opérations numpy plus avancées :

```python
# members_position sans boucle — numpy pur
def members_position_vectorized(entity_id, nb_entities):
    # Trier par entity_id pour grouper
    order = numpy.argsort(entity_id, kind='stable')
    sorted_ids = entity_id[order]

    # Compter la taille de chaque groupe
    group_sizes = numpy.bincount(entity_id, minlength=nb_entities)

    # Créer les positions 0,1,2... dans chaque groupe
    # via cumsum des "débuts de groupe"
    group_starts = numpy.concatenate([[0], numpy.cumsum(group_sizes[:-1])])
    positions_sorted = numpy.arange(len(entity_id)) - group_starts[sorted_ids]

    # Remettre dans l'ordre original
    result = numpy.empty_like(entity_id)
    result[order] = positions_sorted
    return result
```

| Avantage | Détail |
|---|---|
| **Zéro dépendance** | numpy seul |
| **~10-50× vs boucle Python** | Opérations vectorisées C |

| Inconvénient | Détail |
|---|---|
| Code plus complexe | Moins lisible que la boucle |
| Pas toujours possible | Certains patterns ne se vectorisent pas |

**Verdict** : ✅ **À faire en premier** (aucune dépendance nouvelle).

#### JAX — GPU + auto-différentiation

```python
import jax
import jax.numpy as jnp

@jax.jit
def compute_tax(income):
    # Exactement comme numpy, mais compilé XLA
    # et exécutable sur GPU
    brackets = jnp.array([0, 10000, 25000, 50000])
    rates = jnp.array([0.0, 0.14, 0.30, 0.40])
    return jnp.sum(jnp.maximum(income[:, None] - brackets, 0) * rates, axis=1)
```

| Avantage | Détail |
|---|---|
| **GPU** | Calcul sur carte graphique |
| **Auto-diff** | Dérivées automatiques (analyse de sensibilité) |
| **XLA compilation** | Très rapide sur grands arrays |

| Inconvénient | Détail |
|---|---|
| **Changement de paradigme** | Arrays JAX ≠ arrays numpy (immutables) |
| **Pas d'indexation fancy** | `bincount` n'existe pas nativement |
| **GPU requis** | Peu d'intérêt sans GPU |
| **Grosse dépendance** | ~500 Mo |

**Verdict** : 🟡 Intéressant pour le futur (analyse de sensibilité), mais
changement trop important pour le cœur d'OpenFisca.

#### mypyc — compiler le Python typé en C

```python
# Compile le code Python typé (mypy) en extension C
# Sans changer le code source !
# $ mypyc openfisca_core/populations/group_population.py
```

| Avantage | Détail |
|---|---|
| Transparent | Code Python existent |
| 2-5× sur le code non-numpy | Overhead d'interprétation éliminé |

| Inconvénient | Détail |
|---|---|
| Gains modestes | Les hotspots sont dans les boucles numpy |
| Compilation | Étape de build supplémentaire |

**Verdict** : 🟡 Gain marginal, les vrais hotspots sont les boucles.

#### NumExpr — déjà utilisé par OpenFisca

OpenFisca utilise déjà `numexpr` pour évaluer des expressions. Mais
l'usage est limité à `eval_expression()` dans `commons/misc.py`.

On pourrait l'utiliser plus largement dans les formulas :

```python
# Au lieu de :
result = (income - deductions) * rate + flat_amount

# Avec numexpr (multi-threadé automatiquement) :
result = numexpr.evaluate("(income - deductions) * rate + flat_amount")
```

**Gain** : 2-4× sur les expressions arithmétiques multi-opérations, grâce
au multi-threading automatique et à l'élimination des temporaires.

**Verdict** : ✅ Déjà en dépendance, à utiliser plus largement.

#### Bottleneck — functions glissantes optimisées

```python
import bottleneck as bn

# 10-20× plus rapide que numpy pour :
bn.nansum(array)
bn.nanmean(array)
bn.move_mean(array, window=12)    # moyenne glissante
bn.rankdata(array)                # rang (utile pour get_rank!)
```

**Verdict** : 🟡 Utile pour `get_rank()` et les moyennes glissantes.

#### Multiprocessing — parallélisme par entité ou période

```python
from concurrent.futures import ProcessPoolExecutor

def calculate_parallel(simulation, variables, period):
    """Calculer plusieurs variables en parallèle."""
    # Les variables indépendantes peuvent être calculées en parallèle
    with ProcessPoolExecutor() as executor:
        futures = {
            var: executor.submit(simulation.calculate, var, period)
            for var in variables
            if not has_dependency(var, variables)
        }
        return {var: f.result() for var, f in futures.items()}
```

| Avantage | Détail |
|---|---|
| Utilise tous les cœurs | 4-8× sur machine multi-cœurs |
| Pas de dépendance | stdlib Python |

| Inconvénient | Détail |
|---|---|
| Overhead copie | Les arrays doivent être copiés entre processus |
| Complexité | Gestion des dépendances entre variables |

**Verdict** : 🟡 Intéressant mais complexe. Shared memory (Annexe E) aide.

### F.4 Gains estimés par hotspot

| Hotspot | Méthode | Avant | Après | Gain |
|---|---|---|---|---|
| `members_position` | numpy vectorisé | 5 s | 50 ms | **100×** |
| `members_position` | + Numba | 5 s | 5 ms | **1000×** |
| `reduce(min/max)` | numpy `ufunc.reduceat` | 200 ms | 20 ms | **10×** |
| `get_rank` | `bottleneck.rankdata` + groupby | 500 ms | 50 ms | **10×** |
| Expressions arithmétiques | `numexpr` élargi | 100 ms | 30 ms | **3×** |
| Formulas indépendantes | Multiprocessing | 10 s | 3 s | **3×** |

### F.5 Recommendation par priorité

| Priorité | Action | Effort | Dépendance | Gain |
|---|---|---|---|---|
| **1. 🔴 Haute** | Vectoriser `members_position` en numpy pur | 1 jour | Aucune | 100× |
| **2. 🔴 Haute** | Vectoriser `reduce()` via `numpy.ufunc.reduceat` | 1 jour | Aucune | 10× |
| **3. 🟡 Moyenne** | Utiliser `numexpr` dans plus de formulas | 2 jours | Déjà en dépendance | 3× |
| **4. 🟡 Moyenne** | Ajouter Numba pour `members_position` + `get_rank` | 1 jour | numba | 1000× |
| **5. 🟢 Basse** | Paralléliser les formulas indépendantes | 5 jours | Aucune | 3× |
| **6. 🟢 Future** | JAX pour l'analyse de sensibilité | 10+ jours | jax | GPU |

**Principe directeur** : Vectoriser en numpy pur d'abord (aucune dépendance),
Numba ensuite pour les cas irréductibles (boucles sur indices groupés),
JAX/GPU en dernier pour des cas d'usage spécifiques.

### F.6 Conclusion réaliste

Une analyse exhaustive du code d'openfisca-core montre qu'il n'y a en
réalité que **3 endroits** où des boucles Python parcourent des arrays
de données :

| Endroit | Boucle sur | Taille typique | Impact |
|---|---|---|---|
| `members_position` | Chaque personne | N = 1M | 🔴 **Seul vrai hotspot** |
| `reduce()` (min/max/all) | Taille max ménage | 5-15 | 🟡 Court mais O(N)/itération |
| `get_rank()` | Taille max ménage | 5-15 | 🟡 Idem |

**Tout le reste** — `parameters`, `entities`, `holders`, `tracers`,
`tax_benefit_system`, `simulations` — ne boucle que sur des **structures
de métadonnées** (quelques dizaines d'éléments). Aucun intérêt à optimiser.

Les formulas elles-mêmes (le code écrit par les modélisateurs dans les
pays) sont déjà vectorisées par construction : chaque `person("salary", period)`
retourne un ndarray et les opérations sont numpy.

**Conclusion** : OpenFisca-core est **déjà bien optimisé** en termes de
temps de calcul. Numba, JAX ou Cython n'auraient un impact mesurable que
sur les 3 functions de groupement listées ci-dessus. L'effort
d'optimisation le plus rentable est de vectoriser `members_position` en
numpy pur (1 jour, 100× de gain, 0 dépendance).

Pour la microsimulation dynamique, les vrais goulots d'étranglement ne
seront **pas le calcul** mais :

1. **Le stockage mémoire** (cf. Annexe D) — comment garder 30 ans de
   données variables en RAM
2. **La gestion des mutations** — add/remove d'individus avec ré-indexation
3. **L'I/O disque** (cf. Annexe E) — quand la simulation dépasse la RAM
   disponible

C'est pourquoi les Annexes D (optimisations mémoire) et E (backends
disque) sont **plus importantes** que l'Annexe F pour le succès de la
microsimulation dynamique.

## Annexe G : Optimisations mémoire — sparse arrays et retyping

### G.1 Types actuels dans OpenFisca

OpenFisca est **déjà assez compact** dans ses choix de types :

| `value_type` Python | `dtype` numpy | Octets/élément | Optimal ? |
|---|---|---|---|
| `bool` | `bool_` | 1 | ✅ Oui |
| `int` | `int32` | 4 | 🟡 Parfois surdimensionné |
| `float` | **`float32`** | 4 | ✅ Déjà 32 bits (pas 64 !) |
| `Enum` | **`int16`** | 2 | ✅ Compact |
| `date` | `datetime64[D]` | 8 | ✅ Nécessaire |
| `str` | `object` | ~50+ | 🔴 Coûteux (Python objects) |

**Point important** : OpenFisca utilise déjà `float32` et non `float64`.
C'est un choix inhabituel (numpy et pandas utilisent `float64` par défaut)
qui divise déjà la mémoire par 2 pour les montants monétaires.

### G.2 Retyping (downcasting) : gain marginal

#### Opportunités

| Variable | Type actuel | Plage réelle | Type minimal | Gain par personne |
|---|---|---|---|---|
| `age` | int32 (4 o) | 0-120 | int8 (1 o) | 3 octets |
| `nb_children` | int32 (4 o) | 0-15 | int8 (1 o) | 3 octets |
| `housing_occupancy_status` | int16 (2 o) | 0-3 | int8 (1 o) | 1 octet |
| `salary` | float32 (4 o) | 0-500K | float32 | 0 (déjà optimal) |
| `income_tax` | float32 (4 o) | 0-200K | float32 | 0 |
| `mother_id` | int32 (4 o) | 0-N | int32 nécessaire | 0 |

#### Impact réel

Pour 1M de personnes, 500 variables :
- Variables int qui pourraient passer en int8 : ~20 sur 500 → **~60 Mo** économisés
- Variables float : **aucun gain** (déjà float32)
- Total mémoire de la simulation : ~2 Go → gain de 60 Mo = **~3%**

**Verdict** : 🟡 Gain **négligeable** par rapport à la complexité d'implémentation.
Le retyping est une micro-optimisation, pas une stratégie structurante.

#### Implémentation possible (simple)

```python
# Variable avec hint de dtype
class age(Variable):
    value_type = int
    dtype_hint = numpy.int8   # ← nouveau, optionnel
    entity = Person
    definition_period = MONTH
```

Mais attention : si une formule fait `ages + incomes`, numpy va upcast
automatiquement en float32. Le gain en RAM est perdu dès qu'il y a une
opération mixte.

### G.3 Sparse arrays : gain potentiellement très important

#### Le constat

En microsimulation, beaucoup de variables sont **majoritairement nulles** :

| Variable | Qui la reçoit ? | % non-zéro | Pourquoi sparse |
|---|---|---|---|
| `pension` | Retraités (≥65 ans, ~20%) | **20%** | 80% des personnes ont 0 |
| `basic_income` | Adultes sans revenu (~5%) | **5%** | 95% ont 0 |
| `parenting_allowance` | Ménages monoparentaux (~5%) | **5%** | 95% ont 0 |
| `housing_allowance` | Locataires sous plafond (~20%) | **20%** | 80% ont 0 |
| `salary` | Actifs occupés (~50%) | **50%** | 50% ont 0 (enfants, retraités) |
| `child_benefit` | Ménages avec enfants (~40%) | **40%** | 60% ont 0 |
| `income_tax` | Personnes avec revenu (~60%) | **60%** | Peu sparse |
| `disposable_income` | Tous les ménages | **100%** | ❌ Pas sparse |

#### Gain estimé

Pour 1M de personnes, en supposant ~200 variables « sparse » (sur 500) avec
un taux de remplissage moyen de 30% :

```
Dense :  200 vars × 1M × 4 octets = 800 Mo
Sparse : 200 vars × 1M × 4 × 0.30 + overhead = ~280 Mo
Gain :   ~520 Mo (~65% de réduction sur les variables sparse)
```

Sur le budget total de ~2 Go, c'est un gain de **~25%**.

#### Technologies disponibles

##### Option A : `scipy.sparse` (CSR/CSC)

```python
from scipy import sparse

# Créer un array sparse
salary_sparse = sparse.csr_matrix(salary_dense.reshape(1, -1))
# Mémoire : ne stocke que les non-zéros + indices

# Convertir pour le calcul
salary_dense = salary_sparse.toarray().ravel()
```

| Avantage | Détail |
|---|---|
| Mature | scipy, très utilisé |
| Efficace en mémoire | Ne stocke que les non-zéros |

| Inconvénient | Détail |
|---|---|
| **Conçu pour les matrices 2D** | Pas pour les vecteurs 1D |
| **Pas compatible numpy** | `bincount(sparse)` → erreur |
| **Conversion nécessaire** | Il faut `.toarray()` avant tout calcul |
| **Overhead de conversion** | Annule le gain si on convertit souvent |

**Verdict** : 🔴 **Mauvais candidate** pour OpenFisca — les opérations
centrales (`bincount`, fancy indexing, comparisons) ne fonctionnent pas
sur les arrays sparse.

##### Option B : Masque + array compressé (maison)

```python
class SparseHolder:
    """Stocke un vecteur avec valeur par défaut et exceptions."""

    def __init__(self, default_value, dtype):
        self._default = default_value
        self._dtype = dtype
        self._indices = None     # indices des non-défaut
        self._values = None      # valeurs correspondantes
        self._length = 0

    def from_dense(self, array, default_value=0):
        mask = array != default_value
        self._indices = numpy.where(mask)[0]
        self._values = array[mask]
        self._length = len(array)

    def to_dense(self):
        result = numpy.full(self._length, self._default, dtype=self._dtype)
        if self._indices is not None:
            result[self._indices] = self._values
        return result

    @property
    def nbytes(self):
        if self._indices is None:
            return 0
        return self._indices.nbytes + self._values.nbytes
```

| Avantage | Détail |
|---|---|
| **Simple** | ~30 lignes de code |
| **Compatible** | `.to_dense()` → ndarray normal |
| **Prédictible** | Le gain est proportionnel au taux de zéros |

| Inconvénient | Détail |
|---|---|
| Conversion `to_dense()` | Nécessaire avant chaque calcul |
| Pas de calcul in-place | Le sparse n'est utile qu'au **repos** (stockage) |

**Verdict** : ✅ **Bon candidate** pour le stockage, mais le gain n'est réel
que quand la variable est au repos (pas en cours de calcul).

##### Option C : Delta storage (stocker uniquement les changements)

L'idée : d'une période à l'autre, seuls ~5% des salaires changent.
Ne stocker que le delta, comme en compression vidéo (I-frame + P-frames).

```python
class DeltaStorage:
    def store_delta(self, period, array):
        changed = array != self._ref_array    # comparison O(N)
        self._deltas[period] = {
            'indices': numpy.where(changed)[0],
            'values': array[changed],
        }
```

**Analyse honnête des coûts** :

1. **On ne sait pas avant le calcul** si les valeurs ont changé. La formule
   produit un ndarray dense complete — le delta est un **post-traitement** :
   ```
   result = formula(person, period)    # ndarray dense, inévitable
   holder.put_in_cache(result, period) # → ici on POURRAIT faire le delta
   ```

2. **Le coût de comparison est significatif** :
   - `a != b` : ~1 ms pour 1M float32
   - `numpy.where(changed)` : ~1 ms
   - Total : ~2.5 ms par variable par période
   - Pour 500 variables × 30 périodes : **~37 secondes** de comparisons
   - La simulation elle-même prend ~4 secondes (cf. Annexe D)
   → Le post-traitement delta coûte **10× le calcul** !

3. **La référence doit rester en mémoire** pour reconstruire les valeurs :
   ```
   Sans delta : salary[2024] (4 Mo) + salary[2025] (4 Mo) = 8 Mo
   Avec delta : salary[2024] (4 Mo) + Δ25 (0.2 Mo)       = 4.2 Mo
   ```
   Le gain n'est significatif que pour **beaucoup de périodes** (>10).

4. **Le chaînage de deltas** (comme les P-frames vidéo) nécessite des
   « keyframes » réguliers sinon la reconstruction est O(nb_périodes × N).

**Verdict** : 🟡 **Coûteux à implémenter correctement** et le surcoût de
comparison (~37s) est disproportionné. Ne pas implémenter explicitement
— la compression zstd (ci-dessous) capture le même gain automatiquement.

### G.4 Comment fonctionne zstd (et pourquoi c'est suffisant)

#### Qu'est-ce que zstd ?

**Zstandard (zstd)** est un algorithme de compression créé par Yann Collect
chez Facebook en 2016. C'est le successeur moderne de gzip, devenu le
standard de facto pour la compression rapide.

#### Les deux étapes de zstd

**Étape 1 : LZ77 — trouver les répétitions**

```
Données :  [3000, 2500, 0, 0, 0, 0, 0, 0, 0, 0, 3000, 2500, 0, 0]
            ├─ seq A ─┤  ├──── 8 zéros ────┤  ├ copie A ┤  ├───┤

Compressé : [seq A][répéter 0 × 8][copier depuis offset -11, len 2][0 × 2]
```

L'algorithme parcourt les données avec une fenêtre glissante et replace
les séquences déjà vues par des références `(offset, longueur)`. Pour les
séquences de zéros, un seul token suffit pour dire « répéter 0, N fois ».

**Étape 2 : Codage entropique (FSE/Huffman)**

Les tokens fréquents (comme « répéter 0 ») sont encodés sur peu de bits,
les tokens rares sur plus de bits. Comme le code Morse : E = `.` (fréquent,
court), Q = `--.-` (rare, long).

#### Pourquoi c'est efficace pour les arrays OpenFisca

| Pattern dans les données | Ce que zstd fait | Ratio typique |
|---|---|---|
| Séquences de 0 (pension des non-retraités) | Un token « répéter 0 × N » | **100-1000×** |
| Valeurs identiques (même salaire) | Référence vers l'occurrence précédente | **10-50×** |
| Valeurs proches (salaires ~3000±500) | Octets de poids fort identiques → factorisation | **3-5×** |
| Données aléatoires pures | Quasi-incompressible | ~1× |

#### Vitesse : plus rapide que le disque

| Algorithme | Compression | Décompression | Ratio |
|---|---|---|---|
| gzip | ~30 Mo/s | ~300 Mo/s | 3-5× |
| **zstd** | **300 Mo/s** | **1000 Mo/s** | **3-8×** |
| lz4 | 600 Mo/s | 3000 Mo/s | 2-3× |
| aucun | — | — | 1× |

zstd décompresse à **1 Go/s** — plus vite que la lecture d'un SSD classique
(~500 Mo/s). Lire un fichier compressé zstd est souvent **plus rapide**
que lire le même fichier non compressé, car il y a moins d'octets à
transférer depuis le disque.

#### Le sparse implicite

Un array de 1M float32 avec 80% de zéros :
- Dense : 4 Mo
- zstd : **~0.4 Mo** (ratio ~10×)
- Sparse explicite (indices + valeurs) : ~1.6 Mo (200K × 8 octets)

Paradoxe : **zstd est plus compact que le sparse explicite** car il n'a pas
le surcoût des indices (4 octets par élément non-zéro).

#### Le delta implicite (avec Zarr 2D)

Au lieu de stocker chaque période séparément :

```
salary/2024  → [3000, 2500, 0, 0, ...]   # compressé indépendamment
salary/2025  → [3060, 2550, 0, 0, ...]   # compressé indépendamment
```

On peut organiser les données en array 2D `(temps × individus)` :

```
salary → [[3000, 2500, 0, 0, ...],    ← 2024
          [3060, 2550, 0, 0, ...]]    ← 2025
```

Avec des chunks Zarr sur l'axe temps (ex: chunks de 12 mois), zstd
voit les colonnes d'octets quasi-identiques d'une ligne à l'autre et
les factorise automatiquement via LZ77. C'est du **delta implicite**
sans aucune comparison explicite, sans gestion de keyframes, sans
surcoût algorithmique.

```python
# Zarr 2D avec chunks temporels
import zarr

root = zarr.open("simulation.zarr", mode="w")
salary_ds = root.create_dataset(
    "salary",
    shape=(30, 1_000_000),           # 30 périodes × 1M personnes
    chunks=(12, 100_000),            # chunks de 12 mois × 100K personnes
    dtype="float32",
    compressor=zarr.Blosc(cname="zstd", clevel=3),
)

# Écriture période par période
salary_ds[0, :] = salary_2024       # première période
salary_ds[1, :] = salary_2025       # deuxième période (quasi identique)
# → zstd comprime TRÈS bien car les chunks temporels contiennent
#   des colonnes presque identiques
```

### G.5 Où le sparse/delta a un sens, et où il n'en a pas

#### ✅ Sens pour le **stockage au repos** (cache / disque)

Quand une variable est calculée et mise en cache pour une période donnée,
mais pas activement utilisée pour le calcul en cours :

```
Calcul période 2024-01 → salary[2024-01] en RAM (dense, nécessaire)
Calcul période 2024-02 → salary[2024-01] en cache (compressé OK !)
```

#### ❌ Pas de sens pour le **calcul actif**

Les opérations centrales d'OpenFisca **exigent** des arrays denses :
- `numpy.bincount(entity_id, weights=salary)` → dense requis
- `salary[mother_id]` (fancy indexing) → dense requis
- `salary * rate` (opérations élément-par-élément) → dense requis
- `numpy.where(condition, a, b)` → dense requis

### G.6 Recommendation révisée

```
┌─────────────────────────────────────────────┐
│  CALCUL ACTIF                               │
│  (période courante)                          │
│  → tout en DENSE (ndarray)                   │
│  → bincount, fancy indexing fonctionnent     │
├─────────────────────────────────────────────┤
│  CACHE / DISQUE                             │
│  → Zarr 2D (temps × individus) + zstd       │
│  → sparse implicite (séquences de 0)         │
│  → delta implicite (corrélations temporelles)│
│  → aucun code supplémentaire                 │
└─────────────────────────────────────────────┘
```

### G.7 Tableau décisionnel révisé

| Optimisation | Gain | Effort | Coût caché | Priorité |
|---|---|---|---|---|
| **Zarr + zstd** | ~5-10× | 1 jour | Aucun | ✅ **Faire** |
| **Zarr 2D** (temps × individus) | +2-3× inter-période | 2 jours | Aucun | ✅ **Faire** |
| **Delta explicite** | ~10-200× | 3-5 jours | Comparison ~37s, keyframes | 🔴 **Ne pas faire** |
| **Sparse explicite** | ~2-4× | 3-5 jours | Conversion à chaque calcul | 🔴 zstd le fait mieux |
| **Retyping int32→int8** | ~3% global | 1-2 jours | Upcast dans les formulas | 🟡 Micro-optimisation |

**Conclusion révisée** : La réponse est **zstd, pas du code**. La
compression Zarr/zstd avec une organisation 2D capture automatiquement :
- Le sparse (séquences de zéros → ratio 10-100×)
- Le delta inter-période (colonnes quasi-identiques → ratio 5-20×)
- Le tout sans aucune comparison explicite, sans gestion de keyframes,
  sans risque de bugs, et à une vitesse de décompression (1 Go/s) plus
  rapide que la lecture disque.
