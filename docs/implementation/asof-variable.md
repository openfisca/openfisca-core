# AsOfVariable — Variables à valeur persistante

## Concept

Une `AsOfVariable` est une variable dont la valeur, une fois fixée à un
**instant**, persiste dans le temps jusqu'à ce qu'elle soit explicitement
modifiée. C'est l'analogue vectoriel des paramètres OpenFisca.

```
Comparison des sémantiques :

Variable classique (MONTH) :
  2024-01: [OWNER, TENANT]    ← renseigné
  2024-02: [default, default]  ← non renseigné → valeur par défaut !
  2024-03: [default, default]

AsOfVariable (MONTH, as_of=True) :
  Instant 2024-01-01: [OWNER, TENANT]    ← renseigné
  2024-02: [OWNER, TENANT]               ← persiste automatiquement
  Instant 2024-04-15: personne 1 → TENANT  ← changement
  2024-05: [TENANT, TENANT]              ← nouvelle valeur persiste
```

### Orthogonalité avec definition_period

`as_of` porte sur un **instant** (quand la valeur change).
`definition_period` porte sur une **période** (granularité de calcul).
Les deux sont indépendants :

```python
class housing_occupancy_status(Variable):
    value_type = Enum
    possible_values = HousingOccupancyStatus
    entity = Household
    definition_period = MONTH    # utilisable dans des formulas mensuelles
    as_of = True                 # valeur ancrée à un instant, persiste
```

| | Paramètre | Variable | AsOfVariable |
|---|---|---|---|
| Valeur | Scalaire | Vecteur (N,) | Vecteur (N,) |
| Indexé par | Instant | Période | **Instant** |
| Persiste | ✅ | ❌ (default) | ✅ |
| definition_period | — | MONTH/YEAR | MONTH/YEAR |
| A une formule | Non | Possible | Possible |

## Analyse du code existent

### Flux actuel : `Simulation._calculate` → `Holder.get_array`

```
Simulation._calculate(variable_name, period)
  → holder.get_array(period)
    → self._memory_storage.get(period)   # dict lookup exact: _arrays[period]
    → retourne None si pas trouvé
  → si None: lance la formule ou retourne default_array
```

Le point de branchement est `Holder.get_array` (ligne 83 de holder.py).
Actuellement, c'est un lookup exact par période dans un dict. Pour une
AsOfVariable, il faut un lookup "le plus récent ≤ période demandée".

### Flux d'écriture : `set_input` → `_set` → `InMemoryStorage.put`

```
Holder.set_input(period, array)
  → Holder._set(period, value)
    → self._memory_storage.put(value, period)  # _arrays[period] = value
```

Pour une AsOfVariable, le `set_input` reçoit une valeur à un instant
(= début de période). Le stockage est le même, mais le GET change.

## Implémentation proposée

### Niveau 1 : Lookup "as of" dans get_array (~20 lignes)

Modifier `Holder.get_array` pour chercher la période la plus récente
quand la variable est `as_of` :

```python
# holder.py, dans Holder:

def __init__(self, variable, population):
    # ... existent ...
    self._as_of = getattr(self.variable, 'as_of', False)

def get_array(self, period):
    if self.variable.is_neutralized:
        return self.default_array()

    value = self._memory_storage.get(period)
    if value is not None:
        return value

    # NOUVEAU : pour les AsOfVariable, chercher la valeur la plus récente
    if self._as_of:
        value = self._get_as_of(period)
        if value is not None:
            return value

    if self._disk_storage:
        return self._disk_storage.get(period)
    return None

def _get_as_of(self, period):
    """Find the most recent stored value at or before period.start."""
    target = period.start
    best_period = None
    best_start = None

    for known_period in self._memory_storage.get_known_periods():
        start = known_period.start
        if start <= target:
            if best_start is None or start > best_start:
                best_start = start
                best_period = known_period

    if best_period is not None:
        return self._memory_storage.get(best_period)
    return None
```

### Attribute sur Variable (~5 lignes)

```python
# variable.py, dans Variable.__init__:

self.as_of = self.set(
    attr,
    "as_of",
    required=False,
    default=False,
    allowed_type=bool,
)
```

### Niveau 2 : Optimisation du lookup O(1) avec bisect (~30 lignes)

Le lookup linéaire O(P) dans `_get_as_of` peut être optimisé en
maintenant une liste triée d'instants :

```python
import bisect

class AsOfMixin:
    def __init__(self):
        self._sorted_instants = []  # maintenu trié

    def _register_instant(self, period):
        instant = period.start
        pos = bisect.bisect_right(self._sorted_instants, instant)
        if pos == 0 or self._sorted_instants[pos - 1] != instant:
            self._sorted_instants.insert(pos, instant)

    def _get_as_of(self, period):
        target = period.start
        pos = bisect.bisect_right(self._sorted_instants, target)
        if pos > 0:
            best_instant = self._sorted_instants[pos - 1]
            # Retrouver la période qui a cet instant comme start
            for known_period in self._memory_storage.get_known_periods():
                if known_period.start == best_instant:
                    return self._memory_storage.get(known_period)
        return None
```

### Niveau 3 : Économie mémoire avec reference sharing (~15 lignes en plus)

Quand une AsOfVariable est renseignée mais que la valeur n'a pas changé
par rapport à l'instant précédent, on réutilise le **même object** Python :

```python
def _set_as_of(self, period, value):
    """Set input with reference sharing for unchanged arrays."""
    prev = self._get_as_of(period)
    if prev is not None and numpy.array_equal(value, prev):
        # La valeur n'a pas changé → pointer vers le même object
        self._memory_storage.put(prev, period)
    else:
        self._memory_storage.put(value.copy(), period)
    self._register_instant(period)
```

## Compatibilité vectorielle

### Aucun impact sur les formulas

Le contrat est : `holder.get_array(period)` retourne toujours un
`ndarray` dense de shape `(N,)`. Les formulas ne savent pas si la valeur
vient d'un lookup exact ou d'un lookup "as of" :

```python
# Cette formule fonctionne IDENTIQUEMENT pour Variable et AsOfVariable
def formula(household, period):
    status = household.members("housing_occupancy_status", period)
    # status est un ndarray (N,), comme toujours
    return household.any(status == HousingOccupancyStatus.OWNER)
```

### Aucun impact sur les agrégations

`household.sum()`, `household.any()`, `bincount`, fancy indexing — tout
fonctionne car l'opérande est un ndarray dense standard.

### Le seul coût

La matérialisation au GET pour le niveau 3 (patches) coûte O(N) pour la
copie. Mais les niveaux 1-2 ne copient pas (ils retournent une référence
vers l'array stocké).

**Attention** : si une formule modifie l'array retourné in-place, elle
corromprait aussi les autres périodes qui pointent vers le même object.
Deux options :
- Retourner une copie défensive (CPU cost)
- Documenter que les arrays retournés sont en lecture seule

## Examples de variables candidates

| Variable | definition_period | Fréquence de changement | Gain mémoire |
|---|---|---|---|
| `housing_occupancy_status` | MONTH | ~0.5%/mois | ~25× |
| `marital_status` | MONTH | ~0.1%/mois | ~50× |
| `employer_id` | MONTH | ~2%/mois | ~10× |
| `region_code` | MONTH | ~0.3%/mois | ~30× |
| `birth` | ETERNITY | jamais | déjà ETERNITY |
| `salary` | MONTH | ~5%/mois | ~3× (peu d'intérêt) |

## Plan d'implémentation

| Phase | Quoi | Effort | Risque |
|---|---|---|---|
| 1 | Attribute `as_of=True` sur Variable | 0.5 jour | Nul |
| 2 | `_get_as_of` dans Holder.get_array | 1 jour | Faible |
| 3 | Tests unitaires (AsOf lookup, edge cases) | 0.5 jour | Nul |
| 4 | Optimisation bisect (si P > 50) | 0.5 jour | Nul |
| 5 | Reference sharing au set_input | 0.5 jour | Faible |
| 6 | country-template: marquer les variables candidates | 0.5 jour | Nul |
| **Total** | | **~3.5 jours** | **Faible** |

## Risques

1. **Mutation in-place** : si une formule fait `result += 1` sur l'array
   retourné, elle modifie aussi les autres périodes. Mitigation : copie
   défensive ou `ndarray.flags.writeable = False`.

2. **Interaction avec set_input_divide_by_period** : ces helpers
   répartissent un input sur plusieurs sous-périodes. Pour une AsOfVariable,
   cette répartition n'a pas de sens. Il faut vérifier la cohérence.

3. **Interaction avec OnDiskStorage** : le lookup "as of" doit aussi
   marcher pour le stockage disque. Probablement pas critique en v1.

## Ce qui a été implémenté — v44.3.0

[PR #1365](https://github.com/openfisca/openfisca-core/pull/1365)

### Variable.as_of

- Attribut `as_of` ajouté dans `Variable.__init__` via le mécanisme
  `set()` standard (fichier `openfisca_core/variables/variable.py`).
- Setter `set_as_of()` : normalise `True → "start"`, accepte
  `"start"` / `"end"`, rejette toute autre valeur avec `ValueError`.
- Guard : si `as_of` et un helper `set_input` (ex.
  `set_input_divide_by_period`) sont tous deux déclarés → `ValueError`
  à l'instantiation (incompatibilité sémantique).

### Holder (fichier `openfisca_core/holders/holder.py`)

- `__init__` : cache `self._as_of` et initialise `self._sorted_instants`
  (liste triée d'instants, uniquement si `_as_of` est actif).
- `get_array` : si le lookup mémoire exact échoue et que `_as_of` est
  actif, appelle `_get_as_of(period)` avant de tenter le disk storage.
- `_get_as_of(period)` : lookup O(log P) via `bisect.bisect_right` sur
  `_sorted_instants`, avec fallback linéaire pour les holders clonés
  dont `_sorted_instants` n'a pas encore été reconstruit.
- `_register_instant(period)` : insertion triée sans doublon dans
  `_sorted_instants`, appelée à chaque `_set`.
- `_set` : pour les variables `as_of`, calcule si la valeur a changé
  par rapport à l'état précédent. Si inchangée : reference sharing
  (même objet Python réutilisé). Si changée : copie défensive +
  `array.flags.writeable = False` pour protéger le stockage.
- `clone()` : copie `_sorted_instants` indépendamment pour éviter la
  corruption entre la simulation originale et sa copie.

### Risques mitigés

| Risque | Statut |
|---|---|
| Mutation in-place | ✅ `writeable = False` sur tous les arrays stockés |
| Interaction `set_input_divide_by_period` | ✅ `ValueError` au chargement |
| OnDiskStorage | ⚠️ Non traité — le lookup `_get_as_of` n'interroge pas le disk storage |

### Tests

18 tests dans `tests/core/test_asof_variable.py`, sans dépendance à
`openfisca-country-template` :

| Test | Ce qu'il vérifie |
|---|---|
| `test_asof_persists_forward` | Valeur de jan retrouvée en fév, mar, déc |
| `test_asof_no_value_before_first_stored` | `None` si rien posé avant le target |
| `test_asof_exact_match_returns_stored_value` | Lookup exact passe par le chemin rapide |
| `test_asof_takes_most_recent_value` | La valeur la plus récente ≤ target est retournée |
| `test_asof_convention_start` | Valeur mi-année invisible pour une période antérieure |
| `test_asof_convention_end` | Valeur mi-année visible pour un YEAR avec `as_of="end"` |
| `test_non_asof_variable_unaffected` | Variables sans `as_of` restent inchangées |
| `test_asof_no_patch_when_value_unchanged` | Aucun patch stocké si la valeur ne change pas |
| `test_asof_patch_stores_only_changed_indices` | Un patch ne stocke que les indices/valeurs modifiés |
| `test_asof_retroactive_patch` | Un `set_input` rétroactif est reflété dans tous les GETs ultérieurs |
| `test_asof_snapshot_cursor_no_copy_between_patches` | GETs séquentiels sans patch entre eux réutilisent le même array |
| `test_asof_base_array_is_read_only` | Le tableau de base a `writeable=False` |
| `test_asof_get_array_returns_read_only` | `get_array` retourne toujours un array read-only |
| `test_asof_setting_value_does_not_mutate_caller_array` | Le tableau du caller reste modifiable |
| `test_as_of_true_normalises_to_start` | `True` → `"start"` |
| `test_as_of_false_default` | Absence de `as_of` → `False` |
| `test_as_of_invalid_value_raises` | Valeur inconnue → `ValueError` |
| `test_as_of_with_set_input_helper_raises` | `as_of` + helper dispatch → `ValueError` |

### Ce qui a été implémenté — v44.4.0

> PR #1366 (branche `feat/as-of-patches`) — remplace le stockage dense de
> v44.3.0 par un stockage sparse (base + patches) avec snapshot cursor.

#### Holder : nouveaux attributs

| Attribut | Type | Description |
|---|---|---|
| `_as_of_base` | `ndarray` (read-only) | Premier tableau complet posé via `set_input` |
| `_as_of_base_instant` | `Instant` | Instant auquel la base a été établie |
| `_as_of_patches` | `list[(Instant, ndarray[int32], ndarray[dtype])]` | Diffs successifs triés par instant |
| `_as_of_patch_instants` | `list[Instant]` | Liste parallèle à `_as_of_patches` pour `bisect` |
| `_as_of_snapshot` | `(Instant, ndarray, int) \| None` | Cursor cache : `(instant, array, last_patch_idx)` |

#### Méthodes

- **`_set_as_of(period, value)`** : 1er appel → base read-only ; appels
  suivants → diff sparse via `numpy.where`. Les patches sont insérés en
  position triée (via `bisect`) pour gérer les `set_input` rétroactifs.
  Le snapshot est invalidé si un patch rétroactif couvre son instant.
- **`_reconstruct_at(target_instant)`** : bisect + snapshot cursor.
  - O(1) cache hit si `snap_instant == target_instant`.
  - O(k) forward si `snap_instant < target_instant` et snapshot valide
    (`snap_patch_idx <= last_patch_idx`).
  - O(N + k×P) backward (ou premier accès) : recalcul depuis la base.
  - Retourne `None` si aucune base ou `target_instant < base_instant`.
- **`_get_as_of(period)`** : thin wrapper → `_reconstruct_at(period.start)`
  ou `period.stop` selon la convention `as_of`.
- **`_set`** : route vers `_set_as_of` si `self._as_of`, court-circuite
  `_memory_storage` et le disk storage.
- **`get_array`** : court-circuite vers `_get_as_of` si `self._as_of`.
- **`clone`** : `_as_of_base` partagée (read-only), listes de patches
  copiées indépendamment (les arrays idx/vals internes sont read-only),
  snapshot réinitialisé à `None`.

#### Risques mitigés (mis à jour)

| Risque | Mitigation |
|---|---|
| Mutation in-place | ✅ `_as_of_base.flags.writeable = False` ; arrays retournés par `get_array` sont read-only |
| Retroactive `set_input` | ✅ Patches insérés en position triée ; snapshot invalidé si `snap_instant >= instant` |
| Interaction `set_input_divide_by_period` | ✅ `ValueError` au chargement |
| OnDiskStorage | ⚠️ Non traité — `_get_as_of` n'interroge pas le disk storage |

#### Ce qui n'est PAS encore implémenté

- Multi-snapshot LRU (un seul snapshot curseur maintenu par holder)
- Garbage collection de patches anciens
- Stratégie de stockage configurable par variable (`storage_strategy`,
  `max_snapshots`)

## Pourquoi le stockage dense était insuffisant (résolu en v44.4.0)

### Le problème fondamental

L'optimisation de reference sharing n'est utile que si
`numpy.array_equal(new_value, prev_value)` est `True` — c'est-à-dire
quand **aucun individu** n'a changé de valeur. Pour les variables dont
les changements sont dispersés dans la population (chaque mois, quelques
centaines ou milliers de personnes changent, mais pas les mêmes), cette
condition n'est quasiment jamais vraie.

**Scénario concret** : 100 000 fonctionnaires, variable `echelon`
(int16), 0,5–2 % changent par mois de façon aléatoire et indépendante,
simulation sur 10 ans (120 mois).

```
Mois 1  : [3, 5, 2, 7, 1, ...]  ← 1 tableau plein stocké
Mois 2  : [3, 5, 2, 8, 1, ...]  ← 1 seul changement (personne #4)
           ^--- mais numpy.array_equal → False → NOUVEAU tableau plein stocké
Mois 3  : [3, 5, 2, 8, 2, ...]  ← 1 seul changement (personne #5)
           ^--- encore un tableau plein
...
Mois 120: ...  ← 120 tableaux pleins au total
```

L'optimisation reference sharing du `_set` ne détecte pas les
changements partiels : elle compare les tableaux entiers.

### Chiffrage mémoire

| Stratégie | N = 100K | N = 1M | Remarque |
|---|---|---|---|
| **Dense v44.3.0** (1 `set_input`/mois) | 120 × 200 Ko = **24 Mo** | 120 × 2 Mo = **240 Mo** | Reference sharing = 0% gain |
| **Patches sparse** | base 200 Ko + 120 × ~2 Ko = **~0,4 Mo** | base 2 Mo + 120 × ~20 Ko = **~4 Mo** | ×60 moins de mémoire |

Le gain réel dépend du taux de changement mensuel `r` :

```
Gain mémoire ≈ 1 / (2r + 1/P)   où P = nombre de mois, r = taux de changement

r = 0,5%,  P = 120 → gain ≈ ×40
r = 2%,    P = 120 → gain ≈ ×12
r = 10%,   P = 120 → gain ≈ ×3   (l'AsOf perd de son intérêt)
r = 50%,   P = 120 → gain ≈ ×1   (aussi bien de rester en dense)
```

### Pourquoi la solution est les patches sparse

La vraie économie mémoire nécessite de ne stocker que le **diff** à
chaque `set_input`. L'API externe reste identique ; c'est le stockage
interne qui change :

```python
# Au lieu de :
_memory_storage.put(full_array, period)

# On stocke :
_as_of_base    : ndarray          # tableau initial — 1 seule copie (N)
_as_of_patches : list[            # diffs successifs
    (Instant, indices: ndarray[int32], values: ndarray[dtype])
]
```

À chaque `set_input(period, full_array)` :

```python
prev = _reconstruct_as_of(period.start)  # état précédent
changed = full_array != prev
if not changed.any():
    return  # rien n'a changé, aucun stockage
idx  = numpy.where(changed)[0].astype(numpy.int32)
vals = full_array[idx].copy()
_as_of_patches.append((period.start, idx, vals))  # seulement ~k×8 octets
```

À chaque `get_array(period)` :

```python
result = _as_of_base.copy()          # copie O(N)
for instant, idx, vals in _as_of_patches:
    if instant <= target: result[idx] = vals  # scatter O(k)
    else: break
return result
```

Avec le **snapshot cursor** (une seule copie dense gardée en cache),
les accès séquentiels jan→fév→mar deviennent incrémentaux O(k) au
lieu de O(N + k×P) à chaque GET. Voir la section
"Stratégie de cache intelligent (snapshot cursor)" pour les détails.

### Ce que ça change par rapport à v44.3.0

| | v44.3.0 (dense) | v44.4.0 (patches) ✅ |
|---|---|---|
| `_memory_storage` pour `as_of` | Utilisé (tableau plein) | Inutilisé — remplacé par `_as_of_base` + `_as_of_patches` |
| Mémoire par `set_input` | O(N) | O(k) — k = nb individus changeant |
| Temps GET séquentiel | O(1) | O(k) avec snapshot cursor |
| Temps GET premier accès | O(1) | O(N) |
| Reference sharing utile | Seulement si 0 changement | Toujours (patches vides non stockés) |
| API externe | — | Identique (`set_input`, `get_array`) |
| Tests adaptés | — | `test_asof_reference_sharing` supprimé, 6 nouveaux tests ajoutés |

Ce problème est résolu en v44.4.0 — voir section précédente.

## Convention start / end

Quand une formule demande une AsOfVariable pour une **période** (pas un
instant), il faut choisir quel instant de la période sert de référence :

```
Période demandée : "2024" (YEAR)
                   ├── start = 2024-01-01
                   └── end   = 2024-12-31

marital_status posé à l'instant 2024-06-15 → MARRIED

Si as_of = "start" : lookup ≤ 2024-01-01 → SINGLE (valeur précédente)
Si as_of = "end"   : lookup ≤ 2024-12-31 → MARRIED
```

| Convention | Usage | Exemple |
|---|---|---|
| `as_of = "start"` | Valeur au début de la période | RSA : statut au 1er du mois |
| `as_of = "end"` | Valeur à la fin de la période | IR : situation au 31 décembre |

Défaut recommandé : `"start"` (cohérent avec le fonctionnement actuel,
cas le plus fréquent pour les droits sociaux mensuels).

## Interaction formule + as_of

### Cas normal (recommandé) : as_of sans formula

La variable est purement input-driven. Seules les valeurs posées via
`set_input` sont stockées. `get_array` retourne le dernier état sparse
reconstruit ; aucune formula n'est jamais invoquée.

### Cas avec formula

La formula s'exécute **uniquement** pour le premier appel dont
`holder.get_array(period)` retourne `None` (base pas encore établie,
ou accès avant la base). Une fois la base établie, tous les GETs
suivants retournent la valeur persistée → **la formula n'est plus
jamais rappelée**. Ce comportement est intentionnel.

Mécanisme interne :

```python
# Dans Simulation._calculate (simplifié) :
cached_array = holder.get_array(period)   # appelle _get_as_of
if cached_array is not None:
    return cached_array                   # ← as_of: retourne dès que la base existe
# Sinon, exécuter la formula…
result = formula(population, period)
holder.put_in_cache(result, period)       # → _set_as_of → établit la base
```

`_reconstruct_at` retourne un résultat dès que la base existe et que
`target_instant >= base_instant`. La formula n'est donc appelée qu'une
seule fois (à la première période demandée).

### Cas limite / avertissement

Si la formula est appelée pour une période antérieure à la base
existante (accès non-séquentiel sans `set_input` préalable),
`_reconstruct_at` retourne `None` et la formula s'exécute à nouveau.
Dans ce cas, l'appel à `_set_as_of` dans `put_in_cache` compare la
nouvelle valeur à l'état reconstruit à cet instant (qui est `None` →
la valeur entière est comparée à `None` → numpy lève une exception).

**Mitigation** : poser toujours un `set_input` pour la période initiale
avant de calculer une as_of variable avec formula, ou s'assurer d'un
accès séquentiel (chronologique).

### Incompatibilité explicite

`as_of` combiné avec un `set_input` helper (ex.
`set_input_divide_by_period`) lève une `ValueError` dès l'instantiation
de la variable. Voir `test_as_of_with_set_input_helper_raises`.

## Outil de benchmark

Le script `benchmarks/test_bench_asof.py` mesure la mémoire et le temps
de la feature as_of avec stockage sparse.

### Lancement

```bash
# Afficher les résultats mémoire (avec -s pour voir les prints)
.venv/bin/pytest benchmarks/test_bench_asof.py -v -s -k memory

# Afficher les temps de GET (benchmark compute)
.venv/bin/pytest benchmarks/test_bench_asof.py -v --benchmark-sort=name -k compute
```

### Ce qu'il mesure

- **Mémoire** : `_as_of_base.nbytes + Σ(idx.nbytes + vals.nbytes)` vs
  ce que le stockage dense aurait coûté (`N × dtype.itemsize × P`).
  Assert que le gain est > 10× pour N=1M, r=0.5%, P=30.
- **Temps GET séquentiel** : 360 GETs consécutifs sur 1M personnes,
  30 patches. Mesure le coût amorti du snapshot cursor.
- **Temps GET backward** : GET au dernier mois puis au premier mois
  (backward jump sans snapshot valide), pour mesurer le coût O(N+k×P).

### Interprétation

| Résultat | Signification |
|---|---|
| Ratio mémoire > 10× | Le sparse storage est efficace (r faible) |
| GET séquentiel ≈ O(k) par step | Le snapshot cursor fonctionne |
| GET backward ≈ O(N) | Recalcul depuis la base — attendu |

## Benchmark : mémoire et temps avec patches

### Protocole

- Variable int16 (enum-like), 0.5% de changement par patch
- Chaque GET = copie du base array + application des patches
- Mesuré sur i7-1185G7, Python 3.11, numpy, médiane sur 50 runs

### Résultats (N = 1M personnes)

| Patches | Dense | AsOf | Gain mém. | Temps GET | Copie seule | Surcoût |
|---|---|---|---|---|---|---|
| 1 | 4.0 Mo | 2.1 Mo | 2× | 0.09 ms | 0.07 ms | +18% |
| 3 | 8.0 Mo | 2.2 Mo | 3.7× | 0.11 ms | 0.07 ms | +53% |
| 10 | 22 Mo | 2.5 Mo | 8.8× | 0.18 ms | 0.07 ms | ×2.5 |
| 30 | 62 Mo | 3.5 Mo | 17.7× | 0.36 ms | 0.07 ms | ×5 |
| 100 | 202 Mo | 7.0 Mo | 28.9× | 1.25 ms | 0.07 ms | ×17 |

### Impact sur une simulation complète

10 AsOf variables, 360 périodes, 1M personnes, 30 patches/variable :

| | Dense | AsOf (patches naïfs) |
|---|---|---|
| Mémoire | 620 Mo | 35 Mo |
| Temps GET total | ~0 ms | ~130 ms |

## Stratégie de cache intelligent (snapshot cursor)

> ✅ Implémenté en v44.4.0 — voir `Holder._reconstruct_at` dans
> `openfisca_core/holders/holder.py`.

### Le problème

Avec les patches naïfs, chaque GET applique **tous** les patches depuis
la base. Pour 30 patches, c'est 30 applications par GET, même si on a
déjà calculé la valeur pour une période voisine.

### L'idée : garder un snapshot curseur

Quand on accède à une AsOfVariable pour une période, on **garde le
résultat dense en cache**. Au prochain accès, au lieu de repartir de la
base, on repart du **dernier snapshot** et on n'applique que les patches
**entre le snapshot et la période demandée**.

```
Patches :  P0(base)  P1   P2   P3   P4   P5   ...   P29

GET("2024-01") : base + P0                     → snapshot S₀ = résultat
GET("2024-02") : S₀ + P1 (si P1 ≤ 2024-02)    → snapshot S₁ = résultat
GET("2024-03") : S₁ + (rien entre 02 et 03)    → snapshot S₂ = S₁ (même ref)
GET("2024-04") : S₂ + P2 (si P2 ≤ 2024-04)    → snapshot S₃ = résultat
...
```

### Le mécanisme (implémentation réelle)

Le snapshot est stocké dans `self._as_of_snapshot` sous la forme d'un
tuple `(Instant, array, last_patch_idx)`.  La méthode
`_reconstruct_at(target_instant)` implémente les trois cas :

```python
def _reconstruct_at(self, target_instant):
    if self._as_of_base is None or target_instant < self._as_of_base_instant:
        return None

    # Nombre de patches applicables : bisect sur _as_of_patch_instants
    pos = bisect.bisect_right(self._as_of_patch_instants, target_instant)
    last_patch_idx = pos - 1  # -1 = seule la base s'applique

    snapshot = self._as_of_snapshot
    if snapshot is not None:
        snap_instant, snap_array, snap_patch_idx = snapshot

        # Cas 1 : cache hit exact — O(1)
        if snap_instant == target_instant:
            return snap_array

        # Cas 2 : forward access — O(k) incrémental
        if snap_instant < target_instant and snap_patch_idx <= last_patch_idx:
            result = snap_array
            for i in range(snap_patch_idx + 1, last_patch_idx + 1):
                _, idx, vals = self._as_of_patches[i]
                if result is snap_array:
                    result = result.copy()  # copy-on-write
                result[idx] = vals
            if result is not snap_array:
                result.flags.writeable = False
            self._as_of_snapshot = (target_instant, result, last_patch_idx)
            return result

    # Cas 3 : backward jump ou premier accès — O(N + k×P)
    result = self._as_of_base.copy()
    for i in range(last_patch_idx + 1):
        _, idx, vals = self._as_of_patches[i]
        result[idx] = vals
    result.flags.writeable = False
    self._as_of_snapshot = (target_instant, result, last_patch_idx)
    return result
```

### Analyse des coûts par type d'accès

| Accès | Patches naïfs | Snapshot cursor |
|---|---|---|
| 1er accès | O(N) + O(k×P) | O(N) + O(k×P) ← identique |
| Suivant, avant dans le temps | O(N) + O(k×P) | **O(k) ou O(1)** ← incrémental |
| Suivant, même date | O(N) + O(k×P) | **O(1)** ← cache hit |
| Retour en arrière | O(N) + O(k×P) | O(N) + O(k×P) ← recalcul |

### Chiffrage : 360 accès séquentiels, 30 patches, 1M personnes

| | Patches naïfs | Snapshot cursor |
|---|---|---|
| Copies base (O(N)) | **360** | **1** |
| Applications de patches | 360 × 30 = **10 800** | **30** |
| Temps total | **~130 ms** | **~5 ms** |

### L'arbitrage mémoire / temps

```
                        ◄── Plus de mémoire
                        ──► Plus rapide

Dense               ████████████████████████████  620 Mo   ~0 ms
(1 array/période)

Snapshot cursor      ████                          37 Mo    ~5 ms
(base + patches
 + 1 snapshot)

Patches naïfs        ███                           35 Mo    ~130 ms
(base + patches
 seulement)
```

| Stratégie | Mémoire | Temps (360 accès) | vs Dense |
|---|---|---|---|
| Dense | 620 Mo | ~0 ms | 1× |
| **Snapshot cursor** | **37 Mo** | **~5 ms** | **17× moins de mém.** |
| Patches naïfs | 35 Mo | ~130 ms | 18× moins de mém. |

Le snapshot cursor ajoute **1 array** (~2 Mo pour 1M int16) par rapport
aux patches naïfs, mais divise le temps par **~25**.

### Variante : multi-snapshot (LRU cache) — pas encore implémenté

Si la simulation fait des accès non-linéaires (ex: formule qui compare
la valeur à P et P-12), on peut garder les **K derniers snapshots** :

```python
from collections import OrderedDict

class AsOfHolder:
    def __init__(self, base, max_snapshots=3):
        self._snapshots = OrderedDict()  # instant → (array, patch_idx)
        self._max_snapshots = max_snapshots
```

Pour K=3, on garde 3 snapshots × 2 Mo = 6 Mo supplémentaires, et on
couvre les patterns d'accès courants (P, P-1, P-12).

### Résumé

Le snapshot cursor transforme l'arbitrage mémoire/temps :

- **Mémoire** : +1 array (~2 Mo) vs patches naïfs = +6%
- **Temps** : ÷25 (130 ms → 5 ms) pour un accès séquentiel
- **Complexité** : ~20 lignes de plus que les patches naïfs
- **Robustesse** : dégénère gracieusement vers patches naïfs si accès
  aléatoire (jamais pire)

## Garbage collection intelligent des snapshots

### Principe

Avec un multi-snapshot (LRU ou pas), on peut accumuler des snapshots.
Plutôt que de les garder tous, on peut les **élaguer intelligemment**
en fonction de leur coût de reconstruction.

L'idée : un snapshot est "bon marché" à supprimer s'il est
reconstituable avec peu de patches depuis un snapshot voisin. Il est
"coûteux" à supprimer s'il faudrait repartir de la base + beaucoup
de patches pour le recréer.

### Stratégie 1 : Éviction par coût de reconstruction

```
Snapshots gardés en cache :

  S₁(jan)  S₂(mars)  S₃(avril)  S₄(juin)  S₅(sept)
     │        │          │          │          │
     └─ 3p ──┘   └─ 1p ─┘   └─ 2p ─┘   └─ 4p ─┘

  Coût de reconstruction de S₃ depuis S₂ = 1 patch → BON MARCHÉ
  Coût de reconstruction de S₅ depuis S₄ = 4 patches → CHER

  → Supprimer S₃ en priorité (1 seul patch pour le recréer)
```

```python
def _evict_cheapest_snapshot(self):
    """Remove the snapshot with the lowest reconstruction cost."""
    if len(self._snapshots) <= 1:
        return

    items = list(self._snapshots.items())
    min_cost = float('inf')
    min_idx = None

    for i in range(1, len(items)):
        prev_instant, (_, prev_patch_idx) = items[i - 1]
        curr_instant, (_, curr_patch_idx) = items[i]
        cost = curr_patch_idx - prev_patch_idx  # nb patches entre les deux
        if cost < min_cost:
            min_cost = cost
            min_idx = i

    if min_idx is not None:
        instant_to_evict = items[min_idx][0]
        del self._snapshots[instant_to_evict]
```

### Stratégie 2 : Horizon temporel

La simulation advance dans le temps. Les snapshots dans le **passé
lointain** sont moins utiles que ceux proches du présent.

```
Temps →  ──────────────────────────────────►

Snapshots :  S₁   S₂   S₃   S₄   S₅   S₆   [curseur actuel]
             ▲              ▲
             passé lointain  passé récent

Règle : garder les snapshots à distance croissante dans le passé

  - curseur actuel : toujours gardé
  - P-1, P-2 : gardés (accès P-1 fréquent dans les formulas)
  - P-12 : gardé (comparison annuelle)
  - au-delà : élaguer
```

```python
def _gc_by_horizon(self, current_instant):
    """Keep snapshots at increasing distance in the past."""
    keep_offsets = {0, 1, 2, 12, 24}  # en mois
    keep_instants = set()

    for offset in keep_offsets:
        target = current_instant.offset(-offset, 'month')
        # Garder le snapshot le plus proche de target
        best = min(self._snapshots.keys(),
                   key=lambda s: abs(s - target),
                   default=None)
        if best is not None:
            keep_instants.add(best)

    # Supprimer les snapshots hors du set
    for instant in list(self._snapshots.keys()):
        if instant not in keep_instants:
            del self._snapshots[instant]
```

### Stratégie 3 : Budget mémoire

On fixe un **budget** en nombre de snapshots (ou en octets). Quand le
budget est dépassé, on évince le snapshot le moins utile :

```python
class AsOfHolder:
    def __init__(self, base, memory_budget_bytes=None, max_snapshots=5):
        self._base = base
        self._patches = []
        self._snapshots = OrderedDict()
        self._max_snapshots = max_snapshots
        self._memory_budget = memory_budget_bytes or (base.nbytes * max_snapshots)

    def _maybe_gc(self):
        """Evict snapshots if over budget."""
        while len(self._snapshots) > self._max_snapshots:
            self._evict_cheapest_snapshot()

    def get(self, period):
        result = self._get_or_compute(period)
        self._maybe_gc()
        return result
```

### Stratégie 4 : Fusion de patches

Quand deux patches consécutifs modifient les **mêmes indices**, on
peut les fusionner en un seul (seule la dernière valeur compte) :

```
Avant fusion :
  Patch 3 : indices=[42, 99, 200], values=[2, 1, 3]
  Patch 4 : indices=[42, 150],     values=[0, 2]

Après fusion :
  Patch 3+4 : indices=[42, 99, 150, 200], values=[0, 1, 2, 3]
              (personne 42 → valeur du patch 4 gagne)
```

Cela réduit le nombre d'opérations de scatter dans le GET.

### Tableau récapitulatif

| Stratégie GC | Quand utiliser | Complexité | Gain |
|---|---|---|---|
| **Coût de reconstruction** | Toujours | ~15 lignes | Évince les snapshots faciles à recréer |
| **Horizon temporel** | Simulations longues (>5 ans) | ~20 lignes | Libère la mémoire du passé |
| **Budget mémoire** | Contrainte RAM forte | ~10 lignes | Plafonné, prévisible |
| **Fusion de patches** | Beaucoup de patches sur les mêmes individus | ~20 lignes | Accélère le GET |

### L'idée générale

Le cache de snapshots se comporte comme un **arbre de checkpoints** :

```
base ──P₁──P₂──[S₁]──P₃──P₄──P₅──[S₂]──P₆──...──[Sₖ]──Pₙ──[curseur]

où S = snapshot gardé, P = patch

Le GC supprime les S dont le coût de re-traversée des P est faible.
Le GC garde les S proches du curseur (accès probables).
Le GC fusionne les P quand c'est possible.

Le système s'adapte automatiquement :
  - Simulation courte (30 mois) : 1-2 snapshots suffisent
  - Simulation longue (30 ans) : horizon + budget → 5-10 snapshots
  - Variable qui change souvent : plus de snapshots gardés
  - Variable qui change peu : patches seuls, pas de snapshot
```

## Stratégie de stockage par variable

### Pourquoi par variable ?

Chaque variable a un profil de changement propre. Appliquer la même
stratégie à toutes n'est pas optimal :

| Variable | Changement/mois | Profil | Stratégie idéale |
|---|---|---|---|
| `birth` | 0% | Constante | ETERNITY (déjà fait) |
| `marital_status` | ~0.1% | Très stable | Patches, pas de snapshot |
| `housing_occupancy_status` | ~0.5% | Stable | Patches, 1 snapshot |
| `employer_id` | ~2% | Modéré | Patches + 2-3 snapshots |
| `region_code` | ~0.3% | Stable | Patches, 1 snapshot |
| `salary` | ~100% | Volatile | Dense (l'AsOf n'a pas de sens) |

### Déclaration sur la Variable

```python
class marital_status(Variable):
    value_type = Enum
    definition_period = MONTH
    as_of = "start"
    # Le mainteneur peut préciser la stratégie :
    storage_strategy = "patches"         # ou "snapshots", "dense", "auto"
    max_snapshots = 0                    # pas de snapshot pour cette var

class employer_id(Variable):
    value_type = int
    definition_period = MONTH
    as_of = "start"
    storage_strategy = "snapshots"
    max_snapshots = 3                    # garder 3 checkpoints

class salary(Variable):
    value_type = float
    definition_period = MONTH
    # Pas d'as_of : change tout le temps → stockage dense classique
```

### Stratégie "auto" (par défaut)

Si le mainteneur ne précise pas, le système choisit à l'initialisation
en analysant les données d'input :

```python
def _pick_strategy(self):
    """Choose storage strategy based on input data profile."""
    if not self._patches:
        return "dense"  # pas de patches → stockage classique

    total_changes = sum(len(idx) for _, idx, _ in self._patches)
    total_cells = len(self._base) * len(self._patches)
    change_rate = total_changes / total_cells

    if change_rate < 0.01:
        # Moins de 1% change par patch → patches seuls, pas de snapshot
        return "patches_only"
    elif change_rate < 0.10:
        # 1-10% → patches + quelques snapshots
        return "snapshots"
    else:
        # Plus de 10% → l'AsOf n'est pas rentable, dense
        return "dense"
```

### Budget mémoire global réparti entre variables

Au lieu d'un budget par variable, on peut fixer un **budget global**
et le répartir intelligemment :

```python
class Simulation:
    def __init__(self, ..., asof_memory_budget_mb=100):
        self._asof_budget = asof_memory_budget_mb * 1e6

    def _allocate_snapshot_budget(self):
        """Give more snapshot budget to variables that change often."""
        asof_vars = [h for h in self.holders.values() if h._as_of]

        # Calculer le taux de changement de chaque variable
        rates = {}
        for holder in asof_vars:
            total = sum(len(idx) for _, idx, _ in holder._patches)
            rates[holder.variable.name] = total

        total_rate = sum(rates.values()) or 1

        # Répartir le budget proportionnellement
        for holder in asof_vars:
            share = rates[holder.variable.name] / total_rate
            holder._max_snapshots = max(1, int(
                share * self._asof_budget / holder._base.nbytes
            ))
```

### Exemple concret

Budget global : 100 Mo, N = 1M personnes

| Variable | dtype | Array size | Change rate | Budget | Snapshots |
|---|---|---|---|---|---|
| `marital_status` | int16 | 2 Mo | 0.1% | 5 Mo | **2** |
| `housing_status` | int16 | 2 Mo | 0.5% | 25 Mo | **12** |
| `employer_id` | int32 | 4 Mo | 2% | 50 Mo | **12** |
| `region_code` | int16 | 2 Mo | 0.3% | 20 Mo | **10** |

La variable qui change le plus (`employer_id`) obtient le plus de
snapshots. Cell qui change le moins (`marital_status`) en a 2, ce
qui suffit pour le curseur actuel et un point de comparison.

### Résumé

La stratégie par variable permet un **arbitrage fin** :

- **Déclaratif** : le mainteneur peut préciser `storage_strategy` et
  `max_snapshots` s'il connait le profil de la variable
- **Automatique** : sinon le système analyse les données et choisit
- **Global** : un budget mémoire total est réparti entre les variables
  proportionnellement à leur volatilité
- **Pas de surcoût pour les variables denses** : `salary` reste en
  stockage classique, le mécanisme AsOf ne s'active que quand c'est
  déclaré

## Auto-tuning par profiling run

### Principe

Plutôt que de deviner la bonne stratégie, on **measure** les patterns
d'accès réels en faisant un run à blanc (profiling run), puis on résout
un problème d'optimisation sous contraintes.

```
┌─────────────────────────────────────────────────────┐
│  Phase 1 : Profiling run                            │
│                                                     │
│  Simulation normal + instrumentation               │
│  → enregistre pour chaque variable AsOf :           │
│    - nb d'accès par période                         │
│    - pattern d'accès (séquentiel ? sauts ?)         │
│    - taux de changement réel                        │
│    - taille d'un array                              │
│                                                     │
│  Phase 2 : Optimisation                             │
│                                                     │
│  Entrée : profils + contraintes (budget RAM, temps) │
│  Sortie : nb de snapshots par variable              │
│                                                     │
│  Phase 3 : Run optimisé                             │
│                                                     │
│  Simulation avec les stratégies calibrées           │
└─────────────────────────────────────────────────────┘
```

### Phase 1 : Instrumentation

Ajouter un mode `profile=True` au Holder qui enregistre les accès
sans changer le comportement :

```python
class AsOfHolder:
    def __init__(self, ..., profile=False):
        self._profile = profile
        self._access_log = []  # [(period, timestamp), ...]

    def get(self, period):
        if self._profile:
            self._access_log.append((period, time.monotonic()))
        return self._do_get(period)

    def get_profile(self):
        """Compute access profile from the log."""
        if not self._access_log:
            return None

        periods = [p for p, _ in self._access_log]
        n_accesses = len(periods)

        # Directionalité : % d'accès strictement croissants
        forward = sum(
            1 for i in range(1, len(periods))
            if periods[i].start > periods[i-1].start
        )
        directionality = forward / max(1, n_accesses - 1)

        # Spread : combien de périodes distinctes
        unique_periods = len(set(periods))

        # Taux de réaccès : même période demandée plusieurs fois
        reaccess_rate = 1 - unique_periods / n_accesses

        return {
            "variable": self.variable.name,
            "n_accesses": n_accesses,
            "unique_periods": unique_periods,
            "directionality": directionality,
            "reaccess_rate": reaccess_rate,
            "n_patches": len(self._patches),
            "change_rate": self._compute_change_rate(),
            "array_bytes": self._base.nbytes,
        }
```

### Phase 2 : Optimisation sous contraintes

Le profil de chaque variable donne le **coût** de chaque stratégie.
On résout ensuite :

```
Minimiser  Σᵢ temps_get(varᵢ, snapshotsᵢ)
Sous       Σᵢ mémoire(varᵢ, snapshotsᵢ) ≤ budget_RAM
           snapshotsᵢ ≥ 0
```

Où pour chaque variable i, avec le profil mesuré :

```python
def cost_model(profile, n_snapshots):
    """Estimate time and memory for a given number of snapshots."""
    N = profile["array_bytes"]                          # taille d'un array
    P = profile["n_patches"]                            # nb de patches
    A = profile["n_accesses"]                           # nb d'accès total
    d = profile["directionality"]                       # % accès forward

    # Mémoire = base + patches + snapshots
    patch_bytes = sum(idx.nbytes + val.nbytes for _, idx, val in patches)
    memory = N + patch_bytes + n_snapshots * N

    # Temps : dépend du pattern d'accès
    if n_snapshots == 0:
        # Patches naïfs : chaque accès repart de la base
        avg_patches_per_get = P / 2       # en moyenne la moitié
        time_per_get = N + avg_patches_per_get * k_per_patch
    else:
        # Avec snapshots : accès forward = incrémental
        avg_gap = P / (n_snapshots + 1)   # patches entre 2 snapshots
        forward_cost = avg_gap * k_per_patch  # O(k) par patch
        backward_cost = N + P / 2 * k_per_patch  # recalcul total
        time_per_get = d * forward_cost + (1 - d) * backward_cost

    total_time = A * time_per_get
    return memory, total_time
```

Résolution (budget RAM fixé, minimiser le temps) :

```python
def optimize_strategies(profiles, ram_budget):
    """Find optimal snapshot count per variable under RAM constraint.

    Simple greedy: give snapshots to the variable where it saves the
    most time per byte of memory used.
    """
    # Commencer avec 0 snapshots pour tout le monde
    snapshots = {p["variable"]: 0 for p in profiles}
    used_ram = sum(p["array_bytes"] for p in profiles)  # bases only

    while True:
        # Pour chaque variable, calculer le gain marginal
        # d'ajouter 1 snapshot
        best_var = None
        best_ratio = 0  # time_saved / memory_added

        for p in profiles:
            var = p["variable"]
            n = snapshots[var]
            mem_before, time_before = cost_model(p, n)
            mem_after, time_after = cost_model(p, n + 1)

            mem_delta = mem_after - mem_before  # = array_bytes
            time_delta = time_before - time_after

            if time_delta > 0 and used_ram + mem_delta <= ram_budget:
                ratio = time_delta / mem_delta  # ms saved per Mo
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_var = var
                    best_mem = mem_delta

        if best_var is None:
            break  # plus de budget ou plus de gain

        snapshots[best_var] += 1
        used_ram += best_mem

    return snapshots
```

### Phase 3 : Application

```python
class Simulation:
    def optimize_asof_strategies(self, ram_budget_mb=100):
        """Run profiling, then optimize storage strategies."""
        # Phase 1 : profiling run
        for holder in self._asof_holders():
            holder._profile = True

        self._run_all_formulas()  # run à blanc

        # Phase 2 : optimisation
        profiles = [h.get_profile() for h in self._asof_holders()]
        optimal = optimize_strategies(profiles, ram_budget_mb * 1e6)

        # Phase 3 : appliquer
        for holder in self._asof_holders():
            holder._max_snapshots = optimal[holder.variable.name]
            holder._profile = False
            holder._access_log.clear()

        return optimal
```

Usage :

```python
sim = SimulationBuilder().build(tbs, scenario)
# Calibration automatique
strategies = sim.optimize_asof_strategies(ram_budget_mb=200)
# → {'marital_status': 0, 'employer_id': 5, 'housing_status': 2, ...}

# Maintenant la simulation est optimisée
result = sim.calculate("disposable_income", "2024-01")
```

### Ou bien : contrainte inverse (temps fixé, minimiser la RAM)

```
Minimiser  Σᵢ mémoire(varᵢ, snapshotsᵢ)
Sous       Σᵢ temps_get(varᵢ, snapshotsᵢ) ≤ budget_temps
```

Même algorithme greedy en inversant le ratio : on **ajoute** des
snapshots tant que le temps est au-dessus du budget, en ciblant la
variable où 1 snapshot fait gagner le plus de temps.

### Ce que le profiling run capte

| Donnée mesurée | Ce qu'elle révèle | Impact sur la stratégie |
|---|---|---|
| `directionality` = 0.95 | Accès quasi-linéaire dans le temps | 1 snapshot curseur suffit |
| `directionality` = 0.5 | Accès aléatoire (sauts) | Plus de snapshots distribués |
| `reaccess_rate` = 0.8 | Même période demandée souvent | Cache LRU très efficace |
| `n_accesses` = 2 | Variable rarement lue | Pas besoin de snapshot |
| `n_accesses` = 1000 | Variable très sollicitée | Investir en snapshots |
| `change_rate` = 0.001 | Très stable | Patches seuls suffisent |
| `change_rate` = 0.1 | Volatile | Snapshots fréquents ou dense |

### Coût du profiling : ordres de grandeur mesurés

Mesuré avec `country-template`, N = 1M personnes, i7-1185G7 :

| Opération | Temps | Catégorie |
|---|---|---|
| **Simulation build** | **153 ms** | Setup (le plus cher) |
| `household.sum(salary)` | 5.1 ms | Agrégation entité |
| `numpy.where(mask, a, b)` | 4.0 ms | Calcul formule |
| `set_input(salary)` | 1.5 ms | Écriture |
| `a + b` | 1.0 ms | Calcul formule |
| **AsOf GET (30 patches)** | **0.85 ms** | AsOf |
| `numpy.copy(4 Mo)` | 0.28 ms | Copie |
| `default_array` (zeros) | 0.21 ms | Allocation |
| `calculate('income_tax')` (cache hit) | 0.08 ms | Pipeline |
| **AsOf incrémental (1 patch, 5K idx)** | **0.01 ms** | AsOf (snapshot) |
| `get_array` (cache hit) | 0.01 ms | Lecture |
| **3600 × list.append** (profiling) | **0.53 ms** | Instrumentation |

L'instrumentation de profiling (0.53 ms) est **0.06%** du temps total
d'une simulation typique (~815 ms). Le vrai coût n'est pas le
profiling, c'est de savoir **quand** profiler.

### Quand profiler : la question de l'homogénéité

Le profiling "en ligne" (calibrer sur les premiers accès) ne marche
que si le pattern d'accès est **homogène dans le temps**. Or ce n'est
pas toujours le cas :

| Cas | Homogène ? | Profiling en ligne |
|---|---|---|
| Simulation mensuelle 1 an, mêmes variables chaque mois | ✅ | ✅ Marche |
| Simulation 30 ans, `pension` n'apparait qu'après 20 ans | ❌ | ❌ Rate `pension` |
| Formule avec `P-12` : pas de lookback avant le mois 13 | ❌ | ❌ Directionnalité fausse |
| Réforme qui change le graphe de dépendances | ❌ | ❌ Profil du baseline ≠ réforme |

### Stratégies de profiling

| Stratégie | Quand | Coût | Fiabilité |
|---|---|---|---|
| **En ligne (50 premiers accès)** | Simulation homogène | 0 | Bonne si homogène |
| **Recalibration périodique** | Simulation hétérogène | ~0 (tous les 100 accès) | Bonne |
| **Baseline = profiling** | Multi-run avec même graphe | 0 (déjà fait) | Exacte |
| **Dry run complete** | Pattern très variable | 1× temps simulation | Exacte |

#### Recalibration périodique (recommandée)

La plus robuste : on réajuste la stratégie tous les K accès, sans
supposer l'homogénéité :

```python
class AsOfHolder:
    RECALIBRATE_EVERY = 100  # accès

    def get(self, period):
        self._access_count += 1
        self._access_log.append(period.start)

        if self._access_count % self.RECALIBRATE_EVERY == 0:
            self._recalibrate()

        return self._do_get(period)

    def _recalibrate(self):
        """Adjust strategy based on recent access pattern."""
        recent = self._access_log[-self.RECALIBRATE_EVERY:]

        # Mesurer la directionnalité récente
        forward = sum(
            1 for i in range(1, len(recent))
            if recent[i] > recent[i-1]
        )
        directionality = forward / (len(recent) - 1)

        # Si accès très directionnel → 1 snapshot curseur suffit
        if directionality > 0.8:
            self._max_snapshots = 1
        # Si accès aléatoire → plus de snapshots
        elif directionality < 0.3:
            self._max_snapshots = min(5, self._max_snapshots + 1)
        # Si accès avec lookback (P et P-12) → garder 2
        else:
            self._max_snapshots = 2
```

Le surcoût de recalibration : ~100 comparisons d'instants = **~0.01 ms**
tous les 100 accès. Invisible.

#### Et si le pattern change radicalement ?

Exemple : une simulation qui fait 12 mois linéairement, puis remonte
dans le temps pour comparer. La recalibration détecte le changement
de directionnalité et augmente les snapshots automatiquement.

```
Accès 1-12 :   jan → fév → ... → déc    (directionality = 1.0)
  → stratégie : 1 snapshot curseur ✅

Accès 13-24 :  déc → jan, déc → fév, ... (directionality = 0.0)
  → recalibration détecte le changement
  → stratégie : 3 snapshots distribués ✅
```

Le coût du mauvais choix pendant les ~100 premiers accès de la
nouvelle phase est borné : au pire, on paye le prix des patches naïfs
pendant 100 accès × 0.85 ms = ~85 ms, puis on recalibre. Pour une
simulation de plusieurs seconds, c'est acceptable.
