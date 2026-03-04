# Analyse du système de lines de LIAM2 et transposition dans OpenFisca

> Document d'analyse pour l'implémentation de lines inter-entités dans OpenFisca-core,
> inspiré du système `Link` / `Many2One` / `One2Many` de LIAM2.
>
> **Date d'analyse** : 2026-02-22
> **Projects analysés** :
> - LIAM2 : `/home/benjello/projects/liam2`
> - OpenFisca-core : `/home/benjello/projects/openfisca-core`

---

## Table des matières

1. [Le système de lines de LIAM2](#1-le-système-de-lines-de-liam2)
2. [Le système de lines existent dans OpenFisca](#2-le-système-de-lines-existent-dans-openfisca)
3. [Analyse comparative et écarts](#3-analyse-comparative-et-écarts)
4. [Ce que les lines de LIAM2 apporteraient à OpenFisca](#4-ce-que-les-lines-de-liam2-apporteraient-à-openfisca)
5. [Plan d'implémentation](#5-plan-dimplémentation)

---

## 1. Le système de lines de LIAM2

### 1.1 Vue d'ensemble

Dans LIAM2, les **lines** (links) sont des relations nommées entre entités, déclarées dans
le fichier YAML du modèle et résolues à l'exécution via le système `id_to_rownum`.

Il existe deux types fondamentaux :

```
           Many2One                     One2Many
    ┌──────────────────┐         ┌──────────────────┐
    │ Personne → Ménage│         │ Ménage → Personnes│
    │                  │         │                   │
    │ person.household │         │ household.persons │
    │ = "Donne-moi le  │         │ = "Donne-moi les  │
    │   ménage de cette │        │   personnes de ce  │
    │   personne"       │        │   ménage"           │
    └──────────────────┘         └───────────────────┘
```

Les lines reliant toujours deux entités via un **champ de liaison** (`link_field`) :
un champ entier contenant l'`id` de l'entité cible.

### 1.2 Déclaration des lines (YAML)

**Fichier de référence** : `liam2/tests/examples/demo05.yml`

```yaml
entities:
    household:
        links:
            # One2Many : un ménage a potentiellement plusieurs personnes
            persons: {type: one2many, target: person, field: hh_id}

    person:
        fields:
            - mother_id: int    # champ de liaison vers la mère (entité person)
            - hh_id:     int    # champ de liaison vers le ménage (entité household)

        links:
            # Many2One : une personne a une mère (même entité)
            mother: {type: many2one, target: person, field: mother_id}

            # One2Many : une personne a potentiellement des enfants (même entité)
            children: {type: one2many, target: person, field: mother_id}

            # Many2One : une personne appartient à un ménage (entité différente)
            household: {type: many2one, target: household, field: hh_id}
```

**Parsing** dans `Entity.from_yaml()` (`entities.py:255-273`) :
```python
link_defs = entity_def.get('links', {})
str2class = {'one2many': One2Many, 'many2one': Many2One}
links = dict((name,
              str2class[l['type']](name, l['field'], l['target']))
             for name, l in link_defs.items())
```

### 1.3 Architecture des classes de lines

**Fichier** : `/liam2/liam2/links.py` — 410 lignes

```
Link (base, L19-58)
├── _name: str                    # nom du line (ex: "household")
├── _link_field: str              # champ de liaison (ex: "hh_id")
├── _target_entity_name: str      # nom de l'entité cible (ex: "household")
├── _target_entity: Entity        # référence résolue vers l'entité cible
├── _entity: Entity               # entité source (attachée après parsing)
│
├── Many2One (L61-76)             # N individus → 1 cible
│   ├── get(key) → LinkGet        # accès à un champ de la cible
│   └── __getattr__ = get         # syntax point : person.household.rent
│
└── One2Many (L79-93)             # 1 individu → N cibles
    ├── count() → Count
    ├── sum()   → Sum
    ├── avg()   → Avg
    ├── min()   → Min
    └── max()   → Max
```

#### Expressions de lines :

```
LinkExpression (L121-154, base abstraite)
├── link: Link                    # le line utilisé
├── target_expr: Expr             # l'expression à évaluer sur la cible
│
├── LinkGet (L157-239)            # Many2One : accès à un champ
│   ├── compute()                 # résolution via id_to_rownum
│   ├── get(key)                  # chaînage : person.mother.household.rent
│   └── __getattr__ = get
│
└── Aggregate (L242-298)          # One2Many : agrégation
    ├── compute()                 # résolution via id_to_rownum inverse
    ├── Sum (L301-341)
    │   └── Count (L344-354)      # cas spécial de Sum avec expr=1
    ├── Avg (L357-367)            # Sum / Count
    ├── Min (L370-387)
    └── Max (L390-391)
```

### 1.4 Mécanisme de résolution : `LinkGet.compute()` (Many2One)

**Fichier** : `links.py:205-232`

C'est le cœur du mécanisme Many2One. Comment `person.household.rent` est résolu :

```python
def compute(self, context, link, target_expr, missing_value=None):
    # 1. Récupérer les IDs de la cible pour chaque individu source
    #    Ex: target_ids = [0, 1, 2, 0, 2] (les hh_id des 5 personnes)
    target_ids = context[link._link_field]     # = context['hh_id']

    # 2. Obtenir le contexte de l'entité cible (ménage)
    target_context = self.target_context(context)

    # 3. Convertir les IDs en numéros de ligne via id_to_rownum
    #    Ex: id_to_rownum = [0, 1, 2]  (3 ménages)
    #    → target_rows = [0, 1, 2, 0, 2]
    id_to_rownum = target_context.id_to_rownum
    target_rows = id_to_rownum[target_ids]

    # 4. Évaluer l'expression cible dans le contexte cible
    #    Ex: target_values = [800, 650, 900] (rent des 3 ménages)
    target_values = expr_eval(target_expr, target_context)

    # 5. Récupérer les valeurs pour chaque individu source
    #    Ex: result_values = [800, 800, 650, 900, 800]
    result_values = target_values[target_rows]

    # 6. Gérer les valeurs manquantes (line cassé, id = -1)
    return ne.evaluate("where((ids != mi) & (rows != mi), values, mv)",
                       {'ids': target_ids, 'rows': target_rows,
                        'values': result_values, 'mi': missing_int,
                        'mv': missing_value})
```

**Schéma du flux de données** :

```
Entité source (person)              Entité cible (household)
┌─────────────────────┐             ┌──────────────────────┐
│ id  hh_id  age      │             │ id   rent            │
│ 0    0     25       │ ──┐         │ 0    800             │
│ 1    0     30       │ ──┤ hh_id   │ 1    650             │
│ 2    1     45       │ ──┼──────►  │ 2    900             │
│ 3    2     10       │ ──┤         └──────────────────────┘
│ 4    0     5        │ ──┘
└─────────────────────┘          id_to_rownum = [0, 1, 2]

person.household.rent:
  hh_id  = [0, 0, 1, 2, 0]
  rows   = id_to_rownum[hh_id] = [0, 0, 1, 2, 0]
  rent   = [800, 650, 900]
  result = rent[rows] = [800, 800, 650, 900, 800]
```

### 1.5 Mécanisme de résolution : `Aggregate.compute()` (One2Many)

**Fichier** : `links.py:249-298`

Comment `household.persons.sum(age)` est résolu :

```python
def compute(self, context, link, target_expr, target_filter=None, weights=None):
    # ici context = contexte du ménage (entité source)
    # La colonne de liaison est sur le côté CIBLE (les personnes)

    # 1. Obtenir le contexte de l'entité cible (personnes)
    target_context = link._target_context(context)

    # 2. Récupérer les IDs source dans le contexte cible
    #    = pour chaque personne, l'id de son ménage
    source_ids = target_context[link._link_field]  # = [0, 0, 1, 2, 0]

    # 3. Évaluer l'expression cible (sur les personnes)
    expr_value = expr_eval(target_expr, target_context)  # age des personnes

    # 4. Appliquer le filtre éventuel
    if filter_value is not None:
        source_ids = source_ids[filter_value]
        expr_value = expr_value[filter_value]

    # 5. Convertir les IDs source en numéros de ligne du MÉNAGE
    id_to_rownum = context.id_to_rownum   # du ménage
    source_rows = id_to_rownum[source_ids]

    # 6. Agréger (délégué à eval_rows, implémenté par Sum, Min, Max, etc.)
    return self.eval_rows(source_rows, expr_value, weights_value, context)
```

#### `Sum.eval_rows()` (L302-322)

```python
def eval_rows(self, source_rows, expr_value, weights_value, context):
    idx_for_missing = context_length(context)  # taille du résultat

    # Remplacer les lignes manquantes par un index hors bornes
    source_rows[source_rows == missing_int] = idx_for_missing

    # bincount : some par groupe
    if weights_value is not None:
        expr_value = expr_value * weights_value
    counts = np.bincount(source_rows, expr_value)

    # Tronquer au nombre d'entités source (retirer le bucket des manquants)
    counts.resize(idx_for_missing)
    return counts
```

**Schéma** :

```
Entité cible (person)              Entité source (household)
┌─────────────────────┐            ┌──────────────────┐
│ id  hh_id  age      │            │ id   result      │
│ 0    0     25       │ ──┐        │ 0    60   (25+30+5) │
│ 1    0     30       │ ──┤ hh_id  │ 1    45          │
│ 2    1     45       │ ──┼──────► │ 2    10          │
│ 3    2     10       │ ──┤        └──────────────────┘
│ 4    0     5        │ ──┘
└─────────────────────┘         bincount([0,0,1,2,0], [25,30,45,10,5])
                                        = [60, 45, 10]
```

### 1.6 Chaînage de lines

**Fichier** : `links.py:171-201`

LIAM2 permet de chaîner les lines : `person.mother.household.rent`

Le mécanisme est récursif, construit dans `LinkGet.get()` :

```python
# partner.mother.household.region se décompose en :
LinkGet(Link('partner'),
        LinkGet(Link('mother'),
                LinkGet(Link('household'),
                        Variable('region'))))
```

À l'exécution :
1. Évaluer `region` dans le contexte `household`
2. Résoudre `household.region` via le line `household` → résultat par personne
3. Résoudre `mother.X` via le line `mother` → résultat par personne
4. Résoudre `partner.X` via le line `partner` → résultat par personne

### 1.7 Lines intra-entité (même entité)

LIAM2 supporte les lines entre individus de **la même entité** :
```yaml
person:
    links:
        mother: {type: many2one, target: person, field: mother_id}
        children: {type: one2many, target: person, field: mother_id}
```

Cela permet :
- `mother.age` → l'âge de la mère de chaque personne
- `children.count()` → le nombre d'enfants de chaque personne
- `children.sum(age)` → la some des âges des enfants
- `mother.dead` → est-ce que la mère est décédée

### 1.8 Le line `other` (PrefixingLink)

**Fichier** : `links.py:96-118`

LIAM2 fournit un line spécial `other` utilisé dans le contexte du matching
(formation de couples, etc.). Il permet d'accéder aux champs de l'autre individu
dans une paire.

```python
class PrefixingLink(object):
    # Préfixe les noms de champs avec '__other_'
    # pour accéder aux champs de l'autre individu dans un matching
    def __getattr__(self, key):
        return Variable(self.entity, self.prefix + key)
```

### 1.9 Functions temporelles et lines

**Fichier** : `/liam2/liam2/tfunc.py` — 205 lignes

Les lines sont aussi utilisés dans les functions temporelles (`lag`, `duration`, `tavg`, `tsum`).
Le mécanisme est le même : `id_to_rownum` permet de mapper les individus entre périodes.

**`fill_missing_values()`** (L15-36) — Le pattern fundamental :
```python
@staticmethod
def fill_missing_values(ids, values, context, filler='auto'):
    """
    ids: ids présents dans la période passée
    values: valeurs pour la période passée
    context: contexte de la période courante
    """
    result = np.full(context_length(context), filler, dtype=values.dtype)
    if len(ids):
        id_to_rownum = context.id_to_rownum
        rows = id_to_rownum[ids]
        safe_put(result, rows, values)
    return result
```

Ce pattern est réutilisable pour remapper des données entre populations de tailles différentes.

### 1.10 Gestion des lines cassés

Quand un individu référencé est supprimé (décès), le line pointe vers un `id` dont le
`id_to_rownum` vaut `-1`. LIAM2 gère ça via la valeur manquante :

```python
# Dans LinkGet.compute() (L229-232)
return ne.evaluate("where((ids != mi) & (rows != mi), values, mv)",
                   {'ids': target_ids, 'rows': target_rows,
                    'values': result_values, 'mi': missing_int,
                    'mv': missing_value})
```

Et dans le modèle, l'utilisateur peut explicitement casser un line :
```yaml
# Après un décès, briser le line vers la mère
- mother_id: if(mother.dead, UNSET, mother_id)
```

### 1.11 Résolution et attachment des lines

**Fichier** : `entities.py:275-279`

Après le parsing de toutes les entités, les lines sont résolus :
```python
def attach_and_resolve_links(self, entities):
    for link in self.links.values():
        link._attach(self)           # associe le line à son entité source
        link._resolve_target(entities)  # résout le nom de cible en référence Entity
```

Les lines sont ensuite accessibles comme variables dans le namespace de l'entité :
```python
# entities.py:339
variables.update(self.links)
```

### 1.12 Limites du système de lines de LIAM2

Malgré sa généralité, le système de lines de LIAM2 présente des limitations
qu'il est important d'identifier pour ne pas les reproduire aveuglément.

#### 1.12.1 Pas de Many2Many natif

Comme détaillé dans la section 3.2.4, les relations Many2Many (ex: personnes ↔ entreprises
pour le multi-emploi) nécessitent une entité de jointure. Ce n'est pas un type de line
primitif.

#### 1.12.2 Pas de sémantique de rôle

Un line LIAM2 est **générique** : il relie des entités sans qualifier la nature de la
relation. Contrairement à OpenFisca qui sait que la personne #3 est « enfant » du
ménage #0, LIAM2 sait seulement que la personne #3 appartient au ménage #0.

```yaml
# LIAM2 : pas de rôle, filtres manuals nécessaires
- nb_children: persons.count(age < 18)       # approximation par l'âge
# ou un champ booléen dédié :
- nb_children: persons.count(is_child)

# OpenFisca : rôles natifs, sémantiquement corrects
household.nb_persons(role=Household.CHILD)    # exact, par construction
```

C'est un **avantage d'OpenFisca** à conserver dans toute implémentation future.

#### 1.12.3 Pas de contrainte d'intégrité

LIAM2 ne vérifie **aucune cohérence** sur les lines :

- **One2One non garanti** : si on déclare un line `partner` en Many2One, rien n'empêche
  que 3 personnes pointent vers le même « conjoint »
- **Pas de vérification de référence** : un `mother_id` peut pointer vers un ID qui
  n'existe pas (le résultat sera silencieusement la valeur manquante)
- **Pas de cohérence bidirectionnelle** : si la personne A a `partner_id = B`, rien
  ne garantit que B a `partner_id = A`

#### 1.12.4 Pas de métadonnées sur les lines

Un line est un **simple ID entier**. On ne peut pas attacher d'information à la
relation elle-même (date de début, intensité, type). Il faut des champs séparés :

```yaml
# On ne peut PAS enrichir le line :
links:
    household: {type: many2one, target: household, field: hh_id,
                since: join_date}           # ← n'existe pas

# Il faut un champ séparé sur l'entité :
fields:
    - hh_id: int
    - hh_join_date: int                     # date d'entrée (champ séparé)
```

#### 1.12.5 Pas de traversée récursive

Le chaînage est **explicite et fini** (`person.mother.mother.age` = grand-mère).
Impossible de faire des requêtes récursives :

```yaml
# Possible : chaîne fixe explicite
person.mother.age                    # mère
person.mother.mother.age             # grand-mère

# Impossible : traversée récursive / graphe
person.ancestors.count()             # ← n'existe pas
person.all_descendants.sum(income)   # ← n'existe pas
person.shortest_path_to(other)       # ← n'existe pas
```

#### 1.12.6 Pas d'ordonnancement sur les One2Many

Les lines One2Many fournissent des agrégations (`sum`, `count`, `min`, `max`, `avg`)
mais pas d'accès ordonné. On ne peut pas demander « le 2ème enfant le plus âgé » :

```yaml
# Possible
children.max(age)            # âge du plus vieux
children.count()             # nombre d'enfants

# Impossible
children.nth(2, age)         # ← 2ème plus vieux : n'existe pas
children.sort(age).first()   # ← tri puis accès : n'existe pas
```

**Note** : OpenFisca fait légèrement mieux ici avec `value_nth_person(n, array)`,
qui retourne la valeur de la n-ième personne d'un groupe (par position d'insertion,
pas par tri).

#### 1.12.7 Pas de lines polymorphes

Un line pointe toujours vers **une seule entité cible**. On ne peut pas dire « ce
champ pointe vers une personne OU une entreprise selon le cas » :

```yaml
# Impossible :
beneficiary: {type: many2one,
              target: [person, employer],    # ← n'existe pas
              field: beneficiary_id,
              discriminator: beneficiary_type}
```

#### 1.12.8 Pas de lines temporels croisés

Les lines sont résolus dans le **contexte de la période courante**. On ne peut pas
facilement suivre un line tel qu'il existait à une période passée :

```yaml
# "Le rent de mon ménage actuel" → facile
person.household.rent

# "Le ménage où j'étais l'année dernière" → pas directement possible
# Il faudrait : lag(hh_id) puis résoudre manuellement
```

La fonction `lag()` permet de récupérer la valeur passée d'un champ, mais pas de
naviguer un line dans le contexte d'une période passée.

#### 1.12.9 Tableau récapitulatif des limites de LIAM2

| Limitation | Impact | OpenFisca fait mieux ? |
|---|---|---|
| Pas de Many2Many natif | Entité jointure nécessaire | Non (même limitation) |
| Pas de rôles | Filtres manuals / champs dédiés | **Oui** ✅ (rôles natifs) |
| Pas d'intégrité référentielle | Lines silencieusement cassés | Non |
| Pas de métadonnées sur les lines | Champs séparés nécessaires | Non |
| Pas de traversée récursive | Chaînes finies seulement | Non |
| Pas d'ordonnancement One2Many | Pas de « n-ième trié » | 🟡 `value_nth_person()` (par position) |
| Pas de lines polymorphes | Un line = une entité cible fixe | Non |
| Pas de lines temporels croisés | Résolution à la période courante | Non |

---

## 2. Le système de lines existent dans OpenFisca

### 2.1 Vue d'ensemble : OpenFisca a bien des lines, mais implicites et structurels

OpenFisca-core possède **déjà** un système de lines entre entités, mais il est
profondément différent de celui de LIAM2. Le choix architectural fundamental d'OpenFisca
est d'avoir **fusionné le concept de line avec celui d'entité de groupe** (`GroupEntity`).

Concrètement, OpenFisca gère les relations via **quatre mécanismes complémentaires** :

```
1. GroupEntity + Rôles        → Définition structurelle des relations
2. members_entity_id          → Line implicite personne → groupe (dans GroupPopulation)
3. Projectors                 → Navigation syntaxique dans les formulas
4. containing_entities        → Hiérarchie entre entités de groupe
```

### 2.2 Mécanisme 1 : `GroupEntity` + Rôles — La définition structurelle

**Fichiers** : `entities/group_entity.py` (125 lignes), `entities/role.py` (93 lignes)

En OpenFisca, les relations sont définies via la **structure même des entités**,
pas via des lines déclaratifs. Chaque `GroupEntity` possède :
- Des **rôles** (ex: PARENT, CHILD) qui déterminent la nature de l'appartenance
- Des **sous-rôles** (ex: FIRST_PARENT, SECOND_PARENT) pour les rôles multi-positions
- Un attribute `max` optionnel sur les rôles pour limiter le nombre d'individus par rôle

```python
# Déclaration d'un GroupEntity (dans un project pays, ex: openfisca-france)
household = GroupEntity(
    "household", "households", "A household", "...",
    roles=[
        {
            "key": "parent",
            "subroles": ["first_parent", "second_parent"],  # max=2 implicite
        },
        {
            "key": "child",
            "plural": "children",  # pas de max → nombre illimité
        },
    ],
    containing_entities=("family",),  # le ménage contient la famille
)
```

**Comparison avec LIAM2** :
```yaml
# LIAM2 : line déclaratif pur, sans notion de rôle
household:
    links:
        persons: {type: one2many, target: person, field: hh_id}

person:
    links:
        household: {type: many2one, target: household, field: hh_id}
```

**Différence clé** : LIAM2 a un line générique entre entités. OpenFisca encode la
**sémantique** de la relation (qui est parent, qui est enfant) directement dans la
structure. C'est un avantage pour la modélisation fiscale (ex: filtrer par rôle), mais
un inconvénient pour la généralité.

### 2.3 Mécanisme 2 : `members_entity_id` — Le line implicite personne → groupe

**Fichier** : `populations/group_population.py` (lignes 14-82)

Le line effectif entre personnes et entités de groupe est incarné par trois tableaux numpy
dans `GroupPopulation`, tous de taille `nb_personnes` :

```python
class GroupPopulation(Population):
    _members_entity_id = None   # L17 — Index du groupe pour chaque personne
    _members_role = None        # L18 — Rôle de chaque personne
    _members_position = None    # L19 — Position dans le groupe (calculée paresseusement)
```

Exemple :
```
5 personnes, 3 ménages

Personne   p0   p1   p2   p3   p4
           ─────────────────────────
entity_id  [0,   0,   1,   2,   0]     → p0,p1,p4 dans ménage 0
role       [PAR, PAR, PAR, PAR, CHI]   → p4 est enfant du ménage 0
position   [0,   1,   0,   0,   2]     → p4 est en position 2 du ménage 0
```

C'est l'**équivalent fonctionnel** du champ `hh_id` de LIAM2, mais avec des différences :

| Aspect | LIAM2 `hh_id` | OpenFisca `members_entity_id` |
|---|---|---|
| Nature | Variable sur l'entité personne | Attribute de GroupPopulation |
| Contenu | ID permanent du ménage | **Index positionnel** (0-based) du ménage |
| Déclaration | Champ explicite dans les données | Construit par le SimulationBuilder |
| Modifiable | Oui (simple assignation) | Non (fixé à l'initialisation) |
| Résolution | `id_to_rownum[hh_id]` → position | Direct (c'est déjà la position) |

**Point subtil** : Comme `members_entity_id` contient déjà des positions (pas des IDs),
OpenFisca n'a **pas besoin** de `id_to_rownum` pour les lines personne↔groupe actuels.
C'est efficace mais rigide.

### 2.4 Mécanisme 3 : Projectors — La navigation syntaxique

**Fichier** : `projectors/` — 5 fichiers

Les **projectors** sont le mécanisme qui rend les lines utilisables dans les formulas.
Ils encapsulent les opérations de mapping (projection et agrégation) derrière une
syntax avec le point.

```
Projector (projector.py, L4-38, base abstraite)
├── reference_entity               # la population de référence
├── parent                         # pour le chaînage
├── __getattr__(attribute)         # résolution via get_projector_from_shortcut
├── __call__(*args, **kwargs)      # appel : person.household("rent", "2024")
├── transform_and_bubble_up()      # applique la transformation et remonte dans la chaîne
├── transform()                    # à implémenter par les sous-classes
│
├── EntityToPersonProjector        ← person.household
│   │  "Donne à chaque personne une valeur de son groupe"
│   └── transform(result) = GroupPopulation.project(result)
│       == result[members_entity_id]
│
├── FirstPersonToEntityProjector   ← household.first_person
│   │  "Donne à chaque groupe la valeur de sa première personne"
│   └── transform(result) = GroupPopulation.value_nth_person(0, result)
│
└── UniqueRoleToEntityProjector    ← household.declarant_principal
    │  "Donne à chaque groupe la valeur de la personne avec un rôle unique"
    └── transform(result) = GroupPopulation.value_from_person(result, role)
```

**Le dispatcher** (`projectors/helpers.py:20-140`) :

```python
def get_projector_from_shortcut(population, shortcut, parent=None):
    entity = population.entity

    # CAS 1 : Depuis une entité personne (Entity/SingleEntity)
    if isinstance(entity, entities.Entity):
        # Le shortcut doit être le nom d'une population (ex: "household")
        if shortcut not in populations:
            return None
        return EntityToPersonProjector(populations[shortcut], parent)

    # CAS 2 : Depuis une entité groupe
    if shortcut == "first_person":
        return FirstPersonToEntityProjector(population, parent)

    if isinstance(entity, entities.GroupEntity):
        # CAS 2a : Rôle unique (ex: "declarant_principal")
        role = entities.find_role(entity.roles, shortcut, total=1)
        if role is not None:
            return UniqueRoleToEntityProjector(population, role, parent)

        # CAS 2b : Entité contenante (ex: "family" pour un household)
        if shortcut in entity.containing_entities:
            projector = getattr(
                FirstPersonToEntityProjector(population, parent), shortcut)
            return projector

    return None
```

**Exemple d'utilisation dans une formule** :

```python
class impot(Variable):
    def formula(person, period):
        # person.household est un EntityToPersonProjector
        # person.household("rent") :
        #   1. Calcule rent sur l'entité household → array taille nb_ménages
        #   2. Projette via members_entity_id → array taille nb_personnes
        rent = person.household("rent", period)
        return rent * 0.1
```

**Point fort vs LIAM2** : Les rôles (PARENT, CHILD) permettent des requêtes sémantiques
que LIAM2 ne peut pas faire sans filtre explicite :
```python
# OpenFisca : accès direct par rôle
household.declarant_principal("salary", period)

# LIAM2 : nécessite un filtre ou un champ dédié
# (pas d'équivalent direct)
```

### 2.5 Mécanisme 4 : `containing_entities` — Hiérarchie entre groupes

**Fichier** : `entities/group_entity.py:99,121`

OpenFisca permet de déclarer qu'une entité de groupe **contient** une autre :

```python
household = GroupEntity("household", ..., containing_entities=("family",))
# = "les membres d'une famille sont toujours un sous-ensemble d'un ménage"
```

Cela permet un **chaînage limité** entre groupes :
```python
# Dans une formule sur le ménage :
household.family("allocation_familiale", period)
# → passe par : household → first_person → family → allocation
```

C'est le seul type de « chaînage de lines » supporté par OpenFisca.

### 2.6 Agrégations personne → groupe

`GroupPopulation` fournit des méthodes d'agrégation directement :

```python
# group_population.py
@projectors.projectable
def sum(self, array, role=None):          # L94-119 — some via bincount
def any(self, array, role=None):          # L121-138 — au moins un vrai
def reduce(self, array, func, role):      # L140-160 — réduction générique
def all(self, array, role=None):          # L162-183 — tous vrais
def max(self, array, role=None):          # L185-206 — maximum
def min(self, array, role=None):          # L208-233 — minimum
def nb_persons(self, role=None):          # L235-249 — décompte
def value_from_person(self, array, role): # L253-279 — valeur d'un rôle unique
def value_nth_person(self, n, array):     # L281-305 — n-ième personne
def project(self, array, role=None):      # L313-319 — projection groupe→personne
```

Toutes ces méthodes sont marquées `@projectable` et utilisables via les projectors :
```python
# Utilisation dans une formule (les deux syntaxes sont équivalentes) :
household.sum(person("salary", period))                    # appel direct
person.household.sum(person("salary", period))             # via projector
household.sum(person("salary", period), role=Household.CHILD)  # filtré par rôle
```

### 2.7 Résumé : ce qu'OpenFisca fait et ne fait pas avec les lines

#### ✅ Ce qu'OpenFisca fait déjà bien

1. **Line personne → groupe** : `person.household("rent", period)` — Efficace et naturel
2. **Agrégation groupe → personnes** : `household.sum(salary)` — Performant (bincount)
3. **Rôles** : `household.sum(salary, role=CHILD)` — Sémantique riche, absent de LIAM2
4. **Accès à un rôle unique** : `household.declarant_principal("age")` — Pratique
5. **Chaînage limité** : `household.family("allocation")` — Via `containing_entities`
6. **Syntax dans les formulas** : Projectors + `@projectable` — Élégant

#### ❌ Ce qu'OpenFisca ne sait pas faire

1. **Line personne → personne** : `person.mother("age")` — **Impossible**
2. **Lines nommés personnalisés** : `person.employer("wage")` — **Impossible** sans changer le framework
3. **Chaînage libre** : `person.mother.household("rent")` — **Impossible**
4. **Modification des lines** : changer de ménage — **Impossible** après l'initialisation
5. **Filtre arbitraire** : `household.sum(salary, condition=(age > 18))` — Seulement par rôle
6. **Poids sur agrégation** : `household.count(weights=w)` — **Absent**
7. **Line cassé** : gérer un décès avec `mother_id = -1` — **Impossible**

---

## 3. Analyse comparative et écarts

### 3.1 Le choix architectural fundamental

OpenFisca et LIAM2 ont fait des choix architecturaux **différents mais cohérents** :

**LIAM2** : Les lines sont des **objects de première classe**, déclarés explicitement,
et résolus via un système d'indexation générique (`id_to_rownum`). Tout line est
un champ entier + une déclaration. C'est **générique** mais sans sémantique :
LIAM2 ne sait pas qui est « parent » ou « enfant ».

**OpenFisca** : Les lines sont **fusionnés avec la structure des entités**. La relation
personne↔groupe est incarnée par `GroupEntity` + `GroupPopulation` + `members_entity_id`.
C'est **spécialisé** pour le cas d'usage de la microsimulation fiscale : les rôles ajoutent
de la sémantique, les projectors rendent la syntax naturelle, et les agrégations par rôle
sont directs.

```
           LIAM2                           OpenFisca
           ─────                           ─────────
Philosophie Lines explicites, génériques    Lines implicites, spécialisés
Avantage    Flexibilité totale              Sémantique riche (rôles)
Inconvénient Pas de notion de rôle          Pas de lines intra-entité
Résolution  id_to_rownum (indirection)     members_entity_id (direct)
Déclaration YAML (configuration)            Python (code)
```

Le choix d'OpenFisca est **optimal pour la microsimulation cross-sectionnelle**
(un snapshot fiscal d'une population donnée), mais **insuffisant pour la
microsimulation dynamique** (simulation sur plusieurs périodes avec évolution
de la population et des relations).

### 3.2 Analyse par type de cardinalité

Les relations entre entités se classent en quatre types de cardinalité.
Voici ce que chaque système supporte pour chacune :

#### 3.2.1 One2One (1↔1) — Un individu ↔ exactement un autre

> *Chaque source a exactement une cible, et chaque cible a exactement une source.*

**Examples concrets** :
- Personne ↔ Conjoint (dans un couple monogame)
- Ménage ↔ Logement principal
- Personne ↔ Numéro de sécurité sociale

```
Person 0 ←──────→ Person 3      (couple)
Person 1 ←──────→ Person 2      (couple)
Person 4           (célibataire)
```

| | LIAM2 | OpenFisca |
|---|---|---|
| **Supporté ?** | ✅ Via `Many2One` (cas particulier) | 🟡 Partiellement |
| **Comment ?** | `partner: {type: many2one, target: person, field: partner_id}` | `UniqueRoleToEntityProjector` (ex: `household.declarant_principal`) |
| **Lecture** | `partner.age` | `household.declarant_principal("age", period)` |
| **Limitation** | La contrainte d'unicité n'est pas vérifiée | Fonctionne **uniquement** entre personne↔groupe (pas personne↔personne) |

**Différence clé** : LIAM2 peut faire un One2One **entre personnes** (`person.partner.age`).
OpenFisca ne peut faire un One2One qu'**entre un groupe et une personne avec un rôle unique**
(`household.declarant_principal`). Pour accéder au conjoint, OpenFisca fournit
`value_from_partner()`, mais cette méthode est codée en dur pour les rôles à deux sous-rôles
et ne fonctionne qu'au sein d'un même groupe.

#### 3.2.2 Many2One (N→1) — Plusieurs sources → une cible

> *Chaque source a au plus une cible, mais une cible peut avoir plusieurs sources.*

**Examples concrets** :
- Personnes → Ménage (plusieurs personnes vivent dans un ménage)
- Personne → Mère (chaque personne a une mère)
- Personne → Employeur (chaque salarié a un employeur)
- Personne → Commune de résidence

```
Person 0 ──┐
Person 1 ──┼──→ Household 0
Person 4 ──┘
Person 2 ──────→ Household 1
Person 3 ──────→ Household 2
```

| | LIAM2 | OpenFisca |
|---|---|---|
| **Supporté ?** | ✅ Pleinement | 🟡 Partiel |
| **Inter-entité** | `household: {type: many2one, target: household, field: hh_id}` | `EntityToPersonProjector` (`person.household`) |
| **Intra-entité** | `mother: {type: many2one, target: person, field: mother_id}` | ❌ **Impossible** |
| **Lecture inter** | `person.household.rent` | `person.household("rent", period)` |
| **Lecture intra** | `person.mother.age` | ❌ |
| **Dynamique** | `hh_id = new('household')` (changement de ménage) | ❌ Fixé à l'initialisation |

**C'est le type de line le mieux supporté** par les deux systèmes (pour le cas inter-entité).
Le manque principal d'OpenFisca est le **Many2One intra-entité** : on ne peut pas dire
« donne-moi l'âge de la mère de cette personne ».

#### 3.2.3 One2Many (1→N) — Une source → plusieurs cibles

> *Chaque source peut avoir plusieurs cibles. C'est le symétrique du Many2One.*

**Examples concrets** :
- Ménage → ses personnes (un ménage contient plusieurs personnes)
- Mère → ses enfants (une mère a potentiellement plusieurs enfants)
- Employeur → ses salariés
- Commune → ses résidents

```
Household 0 ──→ Person 0, Person 1, Person 4
Household 1 ──→ Person 2
Household 2 ──→ Person 3
```

| | LIAM2 | OpenFisca |
|---|---|---|
| **Supporté ?** | ✅ Pleinement | 🟡 Partiel |
| **Inter-entité** | `persons: {type: one2many, target: person, field: hh_id}` | `GroupPopulation.sum()`, `.nb_persons()`, etc. |
| **Intra-entité** | `children: {type: one2many, target: person, field: mother_id}` | ❌ **Impossible** |
| **Agrégations** | `count()`, `sum()`, `avg()`, `min()`, `max()` | `sum()`, `any()`, `all()`, `min()`, `max()`, `nb_persons()` |
| **Filtre** | Par expression : `persons.sum(age, age < 18)` | Par rôle uniquement : `sum(salary, role=CHILD)` |
| **Poids** | `persons.count(weights=w)` | ❌ |
| **Dynamique** | Ajout/suppression d'individus = MAJ automatique | ❌ Fixé |

**Différence notable sur les agrégations** :
- LIAM2 : on accède au line puis on agrège → `household.persons.sum(age)`
- OpenFisca : on agrège directement sur le GroupPopulation → `household.sum(person("age", period))`

La syntax OpenFisca est **moins naturelle** pour les expressions impliquant un filtre :
```python
# LIAM2 : naturel
household.persons.sum(salary, age >= 18)

# OpenFisca : contournement nécessaire
salary = person("salary", period)
is_adult = person("age", period) >= 18
household.sum(salary * is_adult)
```

#### 3.2.4 Many2Many (N↔N) — Plusieurs sources ↔ plusieurs cibles

> *Chaque source peut avoir plusieurs cibles, et chaque cible peut avoir plusieurs sources.*

**Examples concrets** :
- Personnes ↔ Entreprises (une personne peut avoir plusieurs employeurs, un employeur a plusieurs salariés)
- Étudiants ↔ Cours (un étudiant suit plusieurs cours, un cours a plusieurs étudiants)
- Personnes ↔ Associations
- Patients ↔ Médecins

```
Person 0 ──→ Employer A, Employer B    (deux emplois)
Person 1 ──→ Employer A               (un emploi)
Person 2 ──→ Employer B, Employer C    (deux emplois)
```

| | LIAM2 | OpenFisca |
|---|---|---|
| **Supporté ?** | ❌ Non nativement | ❌ Non |
| **Contournement** | Via une entité intermédiaire de jointure | Via une entité intermédiaire |

**Ni LIAM2 ni OpenFisca ne supportent nativement le Many2Many.** Cependant,
la **capacité à contourner** cette limitation est très différente entre les deux systèmes.

##### Cas concret : le multi-emploi (personnes ↔ entreprises)

Le multi-emploi est un cas de Many2Many fréquent en microsimulation :
une personne peut avoir plusieurs emplois/salaires, et une entreprise
a plusieurs salariés.

```
Personne A ──→ Emploi chez Entreprise X (salaire 2000€)
           └─→ Emploi chez Entreprise Y (salaire 500€)
Personne B ──→ Emploi chez Entreprise X (salaire 3000€)
Personne C ──→ Emploi chez Entreprise Y (salaire 1500€)
           └─→ Emploi chez Entreprise Z (salaire 800€)
```

##### En LIAM2 : faisable via une entité de jointure

On crée une entité `employment` avec des lines Many2One vers `person` et `employer` :

```yaml
entities:
    person:
        fields:
            - age: int
        links:
            employments: {type: one2many, target: employment, field: person_id}

    employer:
        fields:
            - sector: int
        links:
            employments: {type: one2many, target: employment, field: employer_id}

    employment:
        fields:
            - person_id: int
            - employer_id: int
            - salary: float
            - hours: float
        links:
            person:   {type: many2one, target: person, field: person_id}
            employer: {type: many2one, target: employer, field: employer_id}
```

Ce qui permet des calculus comme :
```yaml
# Sur l'entité person :
- total_salary: employments.sum(salary)           # salaire total
- nb_jobs: employments.count()                     # nombre d'emplois

# Sur l'entité employer :
- payroll: employments.sum(salary)                 # masse salariale
- headcount: employments.count()                   # effectif

# Sur l'entité employment :
- employer_sector: employer.sector                 # secteur de l'employeur
- worker_age: person.age                           # âge du salarié
```

##### En OpenFisca : impossible dans l'architecture actuelle

La raison est **structurelle**. OpenFisca a une hiérarchie rigide :

```
Entity (person)  ←── le seul niveau « individu »
   └── appartient à N GroupEntities (household, family, foyer_fiscal...)
       chacune via UN SEUL members_entity_id
```

Pour modéliser le multi-emploi, il faudrait inverser l'architecture :

```
Entity (employment)  ←── une ligne par emploi (l'unité atomique)
   └── GroupEntity « person » (regroupant les emplois d'une personne)
   └── GroupEntity « employer » (regroupant les emplois d'une entreprise)
```

Mais cela **casse** toute l'architecture d'OpenFisca :

1. L'entité de base ne serait plus la **personne** mais l'**emploi**
2. La personne deviendrait un `GroupEntity` contenant des emplois
3. Toutes les variables (âge, genre, etc.) devraient être projetées de
   la « personne-groupe » vers l'emploi
4. **Aucune formule existante ne fonctionnerait** sans réécriture complète

C'est la conséquence directe du choix d'avoir **un et un seul** `Entity`
(la personne) comme brique de base.

##### Impact sur la modélisation fiscale

| Scénario | LIAM2 | OpenFisca |
|---|---|---|
| 1 personne → 1 emploi → 1 entreprise | ✅ Many2One | ✅ (GroupEntity employeur) |
| 1 personne → N emplois → N entreprises | ✅ Entité jointure | ❌ **Impossible** |
| Cotisations employeur par emploi | ✅ Variable sur `employment` | ❌ Approximation au niveau personne |
| Plafonnement de cotisations par emploi | ✅ Calcul sur `employment` | ❌ Perte d'information sur les seuils |

Ce n'est pas un cas théorique : les systèmes de cotisations sociales appliquent souvent
des **seuils et plafonds par emploi** (plafond de sécurité sociale, taux réduits, etc.).
L'approximation habituelle en OpenFisca consiste à tout agréger au niveau de la personne,
ce qui produit des résultats incorrects quand une personne a plusieurs emplois dont
les salaires sont chacun sous le plafond mais dont la some le dépasse.

#### 3.2.5 Tableau récapitulatif par cardinalité

| Cardinalité | Exemple | LIAM2 | OpenFisca | Écart |
|---|---|---|---|---|
| **One2One inter** | ménage↔logement | ✅ M2O | 🟡 `UniqueRoleToEntityProjector` | OpenFisca limité au groupe↔personne |
| **One2One intra** | personne↔conjoint | ✅ M2O | 🟡 `value_from_partner()` codé en dur | OpenFisca très limité |
| **Many2One inter** | personnes→ménage | ✅ M2O | ✅ `EntityToPersonProjector` | 🟢 Équivalent |
| **Many2One intra** | personne→mère | ✅ M2O | ❌ | 🔴 **Absent** |
| **One2Many inter** | ménage→personnes | ✅ O2M + agrégations | ✅ `GroupPopulation` agrégations | 🟢 Équivalent (filtre limité) |
| **One2Many intra** | mère→enfants | ✅ O2M + agrégations | ❌ | 🔴 **Absent** |
| **Many2Many** | personnes↔employeurs | ❌ (entité jointure) | ❌ | 🟡 Absent des deux |

**Conclusion par cardinalité** : Le manque le plus criant d'OpenFisca concerne les
relations **intra-entité** (personne↔personne), quel que soit le type de cardinalité.
Pour les relations **inter-entités**, OpenFisca couvre bien le Many2One et le One2Many
dans le cas standard personne↔groupe, mais ne permet pas de définir de nouvelles
relations inter-entités au-delà de cells codées dans la structure GroupEntity.

### 3.3 Table de correspondence fonctionnelle détaillée

| Fonctionnalité | LIAM2 | OpenFisca | Écart |
|---|---|---|---|
| **Personne → Groupe** | `person.household.rent` (Many2One + LinkGet) | `person.household("rent", period)` (EntityToPersonProjector) | 🟢 **Équivalent** |
| **Groupe → Personnes (agrégation)** | `household.persons.sum(salary)` (One2Many + Sum) | `household.sum(person("salary", period))` | 🟢 **Équivalent** (syntax différente) |
| **Personne → Personne (même entité)** | `person.mother.age` (Many2One intra-entité) | ❌ N'existe pas | 🔴 **Absent** |
| **Personne → Personnes (même entité)** | `person.children.count()` (One2Many intra-entité) | ❌ N'existe pas | 🔴 **Absent** |
| **Chaînage de lines** | `person.mother.household.rent` | Seulement via `containing_entities` (groupe→groupe) | 🟠 **Très limité** |
| **Rôle unique → Groupe** | N/A (pas de rôles) | `household.declarant_principal("salary")` | 🟢 **OpenFisca uniquement** |
| **Première personne** | N/A | `household.first_person("age")` | 🟢 **OpenFisca uniquement** |
| **Filtre par rôle** | N/A (pas de rôles) | `household.sum(salary, role=CHILD)` | 🟢 **OpenFisca uniquement** |
| **Line cassé (décès)** | `if(mother.dead, UNSET, mother_id)` | N/A (pas de line dynamique) | 🔴 **Absent** |
| **Filtre arbitraire sur agrégation** | `persons.sum(age, age < 18)` | Seulement par rôle | 🟠 **Limité** |
| **Poids sur agrégation** | `persons.count(weights=weight)` | N/A | 🔴 **Absent** |
| **Moyenne, min, max** | `persons.avg(age)`, `persons.min(age)` | `household.min(salary)`, `household.max(salary)` | 🟢 **Équivalent** |
| **Line nommé personnalisé** | Oui, déclarés dans YAML | Non, structure fixe (GroupEntity) | 🔴 **Absent** |
| **Résolution via id_to_rownum** | Oui, toujours | Non, via `members_entity_id` (index positionnels) | 🟡 Architectures différentes |

### 3.4 Les manques à combler (par ordre de priorité)

#### 3.4.1 🔴 Lines intra-entité (personne ↔ personne)

**Le plus important.** LIAM2 permet de créer des lines entre individus de la même entité :
- `mother` : personne → sa mère
- `partner` : personne → son conjoint
- `children` : personne → ses enfants

OpenFisca ne supporte que les lines **personne ↔ groupe** via le système de rôles.
Il est **impossible** d'accéder directement aux caractéristiques d'un autre individu
qui n'est pas dans le même groupe.

**Conséquences** :
- Impossible de calculer `mother.age` (âge de la mère)
- Impossible de compter le nombre d'enfants d'une personne (`children.count()`)
- Impossible de modéliser les transferts intra-familiaux hors ménage

**Note** : OpenFisca contourne partiellement ce manque via `value_from_partner()`,
mais cette méthode ne fonctionne que pour les couples au sein d'un même groupe et
nécessite que le rôle ait exactement deux sous-rôles.

#### 3.4.2 🔴 Lines nommés personnalisables

LIAM2 permet de définir **n'importe quel line** via un simple champ `id` et une déclaration YAML.
OpenFisca a une structure de lines **codée en dur** : personne ↔ ménage/foyer/famille.

On ne peut pas ajouter un line `employeur` (personne → entreprise) ou `médecin traitant`
(personne → médecin) sans modifier le code du framework.

#### 3.4.3 🟠 Filtre arbitraire et poids sur les agrégations One2Many

LIAM2 permet de filtrer par **n'importe quelle expression** :
```yaml
persons.sum(age, age < 18)           # some des âges des mineurs
persons.count(ISFEMALE and age > 60) # nombre de femmes de 60+
persons.avg(salary, weights=hours)   # moyenne pondérée des salaires
```

OpenFisca ne filtre que par **rôle** :
```python
household.sum(salary, role=Household.CHILD)  # some des salaires des enfants
```

Pour filtrer par condition, il faut passer par un calcul intermédiaire et l'écrire
dans la formule :
```python
# Contournement OpenFisca actuel (verbeux)
salary = person("salary", period)
is_adult = person("age", period) >= 18
salary_adults = salary * is_adult
total = household.sum(salary_adults)
```

### 3.5 Les atouts d'OpenFisca à conserver

Il est crucial de ne pas perdre les advantages d'OpenFisca dans l'enrichissement :

1. **Les rôles** — La notion de rôle (PARENT, CHILD, DECLARANT) est absente de LIAM2
   et apporte une sémantique très utile pour la modélisation fiscale
2. **La syntax projector** — `person.household("rent", period)` est naturelle et
   les formulas sont lisibles
3. **La performance** — `members_entity_id` comme index direct (pas d'indirection
   via `id_to_rownum`) est efficace pour le cas statique
4. **La compatibilité** — Des centaines de formulas existantes dans les pays
   utilisent les projectors actuels

### 3.6 Différences architecturales profondes

| Aspect | LIAM2 | OpenFisca |
|---|---|---|
| **Résolution** | Via `id_to_rownum` (ID permanent → position) | Via `members_entity_id` (position directe) |
| **Direction** | Bidirectionnelle (M2O et O2M sont symétriques) | Unidirectionnelle (personne → groupe par `project()`, groupe → personne par `sum()` etc.) |
| **Champ de liaison** | Un champ entier explicite dans les données (`hh_id`, `mother_id`) | Implicite dans `GroupPopulation.members_entity_id` |
| **Scope** | Inter-entité **et** intra-entité | Inter-entité uniquement (personne ↔ groupe) |
| **Déclaration** | Dans le modèle YAML (configuration) | Dans le code Python (via GroupEntity + rôles) |
| **Sémantique** | Aucune (line générique) | Riche (rôles, sous-rôles, positions) |
| **Dynamisme** | Les lines peuvent changer (simple assignation de `hh_id`) | Les lines sont fixés à l'initialisation |
| **Chaînage** | Libre et illimité (`a.b.c.d.e`) | Limité à `containing_entities` |

---

## 4. Ce que les lines de LIAM2 apporteraient à OpenFisca

### 4.1 Cas d'utilisation concrets

#### Lines familiaux (intra-entité)
```python
# Accéder à l'âge de la mère
age_mere = person.mother("age", period)      # Many2One intra-entité

# Nombre d'enfants
nb_enfants = person.children.count()          # One2Many intra-entité

# Revenu du conjoint
revenu_conjoint = person.partner("revenu", period)

# Pension alimentaire : basée sur le revenu de l'autre parent
pension = person.ex_partner("revenu", period) * 0.10
```

#### Lines inter-entités supplémentaires
```python
# Personne → Entreprise
salaire_employeur = person.employeur("masse_salariale", period)

# Personne → Commune
taux_tf = person.commune("taux_taxe_fonciere", period)
```

#### Agrégations avec filtres
```python
# Some des revenus des membres féminins du ménage de plus de 18 ans
household.persons.sum(revenu, condition=(gender == "F") & (age >= 18))

# Moyenne pondérée
household.persons.avg(revenu, weights=temps_travail)
```

### 4.2 Advantages par rapport au système actuel

1. **Expressivité** : Les formulas deviennent plus naturelles et lisibles
2. **Généralité** : Plus besoin de bidouiller avec des variables intermédiaires
3. **Extensibilité** : Les pays peuvent définir leurs propres lines
4. **Dynamisme** : Les lines peuvent évoluer (séparations, déménagements)
5. **Intra-entité** : Accès aux caractéristiques d'individus liés (mère, conjoint)

---

## 5. Plan d'implémentation : un système de lines « LIAM2 amélioré »

### 5.1 Vision architecturale

L'approche recommandée est de concevoir un système de lines **à la LIAM2, augmenté
de rôles**, qui soit un **surensemble strict** des capacités actuelles d'OpenFisca.
Les projectors existants deviennent alors du **sucre syntaxique** par-dessus le
nouveau système de lines.

```
┌─────────────────────────────────────────────────────────┐
│              Système de lines « LIAM2 amélioré »        │
│                                                         │
│  ┌────────────────────┐   ┌──────────────────────────┐  │
│  │ Many2OneLink       │   │ One2ManyLink              │  │
│  │  + role_field ←NEW │   │  + role-filtered aggr.←NEW│  │
│  │  + get()           │   │  + sum/count/avg/min/max  │  │
│  │  + chaînage        │   │  + nth() ←NEW             │  │
│  └────────────────────┘   │  + get_by_role() ←NEW     │  │
│                           └──────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│  Couche de compatibilité (sucre syntaxique)              │
│                                                         │
│  EntityToPersonProjector  →  Many2OneLink.get()         │
│  UniqueRoleToEntityProjector → One2ManyLink.get_by_role()│
│  FirstPersonToEntityProjector → One2ManyLink.nth(0)     │
│  GroupPopulation.sum(role=)  → One2ManyLink.sum(role=)  │
│  value_from_partner()       → One2OneLink.get()         │
│  containing_entities        → Many2OneLink inter-groupes │
└─────────────────────────────────────────────────────────┘
```

### 5.2 L'insight clé : un rôle = une métadonnée sur un line Many2One

Dans OpenFisca actuel, quand la personne P appartient au ménage H avec le rôle PARENT :
- C'est un line **Many2One** : personne → ménage (via `members_entity_id`)
- Plus une **métadonnée** : le rôle (via `members_role`)
- Plus une **position** : rang dans le groupe (via `members_position`)

En enrichissant le `Many2One` de LIAM2 avec un champ de rôle optionnel,
on peut reproduire **tout** ce que fait OpenFisca :

```python
# LIAM2 standard :
# household: {type: many2one, target: household, field: hh_id}

# LIAM2 amélioré : ajout de rôle et position
# household: {type: many2one, target: household, field: hh_id,
#             role_field: hh_role, position_field: hh_position}
```

### 5.3 Preuve de couverture : tout OpenFisca est reproductible

Voici chaque fonctionnalité actuelle d'OpenFisca et son expression équivalente
dans le système de lines « LIAM2 amélioré » :

| # | Fonctionnalité OpenFisca actuelle | Expression avec lines enrichis | Mécanisme |
|---|---|---|---|
| 1 | `person.household("rent", period)` | `person.household_link.get("rent", period)` | M2O standard |
| 2 | `household.sum(salary)` | `household.persons_link.sum("salary", period)` | O2M standard |
| 3 | `household.sum(salary, role=CHILD)` | `household.persons_link.sum("salary", period, role=CHILD)` | O2M + filtre rôle |
| 4 | `household.declarant_principal("age")` | `household.persons_link.get_by_role("age", period, role=DECLARANT)` | O2M + rôle unique |
| 5 | `household.first_person("age")` | `household.persons_link.nth(0, "age", period)` | O2M + position |
| 6 | `person.has_role(Household.CHILD)` | `person.household_link.role == CHILD` | Métadonnée du M2O |
| 7 | `person.value_from_partner(salary)` | `person.partner_link.get("salary", period)` | M2O intra-entité |
| 8 | `household.family("alloc")` | `household.family_link.get("alloc", period)` | M2O inter-groupes |
| 9 | `person.get_rank(household, age)` | `person.household_link.rank("age", period)` | Rang dans le M2O |
| 10 | `household.nb_persons(role=CHILD)` | `household.persons_link.count(role=CHILD)` | O2M + filtre rôle |
| 11 | `household.any(condition, role=R)` | `household.persons_link.any(condition, role=R)` | O2M + filtre rôle |
| 12 | `household.all(condition, role=R)` | `household.persons_link.all(condition, role=R)` | O2M + filtre rôle |
| 13 | `household.min(salary, role=R)` | `household.persons_link.min("salary", period, role=R)` | O2M + filtre rôle |
| 14 | `household.max(salary, role=R)` | `household.persons_link.max("salary", period, role=R)` | O2M + filtre rôle |

**Résultat : 14/14 fonctionnalités couvertes.** De plus, le nouveau système
offre les capacités supplémentaires suivantes, impossibles actuellement :

| # | Nouvelle capacité | Expression | Impossible en OpenFisca actuel |
|---|---|---|---|
| A | Line intra-entité M2O | `person.mother_link.get("age", period)` | ❌ |
| B | Line intra-entité O2M | `person.children_link.count()` | ❌ |
| C | Chaînage libre | `person.mother_link.household_link.get("rent", period)` | ❌ |
| D | Filtre arbitraire sur O2M | `household.persons_link.sum("salary", condition=age>=18)` | ❌ |
| E | Poids sur agrégation | `household.persons_link.count(weights=w)` | ❌ |
| F | Line nommé quelconque | `person.employer_link.get("sector", period)` | ❌ |
| G | Line dynamique (cassable) | `person.set_link_value("mother_id", -1)` | ❌ |

### 5.4 Classes du système de lines enrichi

#### 5.4.1 `Link` — Classe de base

**Fichier** : `openfisca_core/links/link.py`

```python
class Link:
    """Line entre deux entités (ou au sein de la même entité).

    Un line est défini par :
    - un nom (ex: "household", "mother", "employer")
    - un champ de liaison : le nom de la Variable contenant les IDs cibles
    - l'entité cible
    - optionnellement : un champ de rôle et un champ de position
    """

    def __init__(
        self,
        name: str,
        link_field: str,
        target_entity_key: str,
        role_field: str | None = None,        # ← ENRICHISSEMENT OpenFisca
        position_field: str | None = None,     # ← ENRICHISSEMENT OpenFisca
    ):
        self.name = name
        self.link_field = link_field
        self.target_entity_key = target_entity_key
        self.role_field = role_field
        self.position_field = position_field

        # Résolu après construction
        self._source_population = None
        self._target_population = None

    def resolve(self, populations: dict):
        """Résoudre les références vers les populations."""
        self._target_population = populations[self.target_entity_key]

    def attach(self, population):
        """Attacher le line à sa population source."""
        self._source_population = population
```

#### 5.4.2 `Many2OneLink` — Line N→1 enrichi de rôles

**Fichier** : `openfisca_core/links/many2one.py`

```python
class Many2OneLink(Link):
    """Line N→1 enrichi.

    Par rapport au Many2One de LIAM2, ajoute :
    - role_field : accès au rôle de l'individu source dans le groupe cible
    - position_field : rang de l'individu source dans le groupe cible
    - rank() : classement par une expression au sein du groupe
    """

    def get(self, variable_name: str, period) -> ndarray:
        """Valeur d'une variable de l'entité cible pour chaque source.

        Équivalent OpenFisca : EntityToPersonProjector.transform()
        Équivalent LIAM2 : LinkGet.compute()
        """
        source_pop = self._source_population
        target_pop = self._target_population

        # 1. Récupérer les IDs cibles
        target_ids = source_pop.simulation.calculate(self.link_field, period)

        # 2. Calculer les valeurs sur la cible
        target_values = target_pop.simulation.calculate(variable_name, period)

        # 3. Résolution : id → position (via id_to_rownum ou directement)
        target_rows = self._resolve_ids(target_ids)

        # 4. Indexer + gérer les valeurs manquantes
        variable = target_pop.entity.get_variable(variable_name)
        result = numpy.full(source_pop.count, variable.default_value,
                            dtype=target_values.dtype)
        valid = target_rows >= 0
        result[valid] = target_values[target_rows[valid]]
        return result

    @property
    def role(self) -> ndarray | None:
        """Rôle de chaque individu source dans le groupe cible.

        Équivalent OpenFisca : members_role / has_role()
        """
        if self.role_field is None:
            return None
        return self._source_population.simulation.calculate(
            self.role_field, ETERNITY)

    def has_role(self, role) -> ndarray:
        """Test de rôle. Équivalent OpenFisca : population.has_role(role)"""
        return self.role == role

    def rank(self, variable_name: str, period) -> ndarray:
        """Rang de l'individu source dans le groupe, trié par variable.

        Équivalent OpenFisca : population.get_rank()
        """
        # Implémentation via argsort groupé
        ...

    def __call__(self, variable_name, period):
        return self.get(variable_name, period)

    def __getattr__(self, name):
        """Chaînage : person.mother.household.rent"""
        target_link = self._target_population.entity.get_link(name)
        if target_link is not None:
            return ChainedLink(self, target_link)
        raise AttributeError(f"No link '{name}' on {self.target_entity_key}")

    def _resolve_ids(self, target_ids):
        """Convertir des IDs en positions (row numbers)."""
        target_pop = self._target_population
        if hasattr(target_pop, '_id_to_rownum'):
            id_to_rownum = target_pop._id_to_rownum
            rows = numpy.full_like(target_ids, -1)
            valid = (target_ids >= 0) & (target_ids < len(id_to_rownum))
            rows[valid] = id_to_rownum[target_ids[valid]]
            return rows
        else:
            rows = target_ids.copy()
            rows[rows < 0] = -1
            rows[rows >= target_pop.count] = -1
            return rows
```

#### 5.4.3 `One2ManyLink` — Line 1→N enrichi de rôles et d'accès ordonnés

**Fichier** : `openfisca_core/links/one2many.py`

```python
class One2ManyLink(Link):
    """Line 1→N enrichi.

    Par rapport au One2Many de LIAM2, ajoute :
    - Filtrage par rôle (en plus du filtre par condition)
    - nth() : accès à la n-ième cible par position
    - get_by_role() : accès à la cible ayant un rôle unique donné
    """

    # ── Agrégations (LIAM2 + rôles OpenFisca) ──────────────────────

    def sum(self, variable_name, period, role=None, condition=None,
            weights=None) -> ndarray:
        """Some. Équivalent OpenFisca : GroupPopulation.sum(array, role)"""
        values = self._target_values(variable_name, period)
        return self._aggregate(numpy.add, 0.0, values, role, condition, weights)

    def count(self, role=None, condition=None, weights=None,
              period=None) -> ndarray:
        """Décompte. Équivalent OpenFisca : GroupPopulation.nb_persons(role)"""
        values = numpy.ones(self._target_population.count)
        return self._aggregate(numpy.add, 0, values, role, condition, weights)

    def avg(self, variable_name, period, role=None, condition=None,
            weights=None) -> ndarray:
        """Moyenne."""
        s = self.sum(variable_name, period, role, condition, weights)
        c = self.count(role, condition, period=period)
        return numpy.where(c > 0, s / c, 0)

    def min(self, variable_name, period, role=None,
            condition=None) -> ndarray:
        """Minimum. Équivalent OpenFisca : GroupPopulation.min(array, role)"""
        values = self._target_values(variable_name, period)
        return self._aggregate(numpy.minimum, numpy.inf, values, role, condition)

    def max(self, variable_name, period, role=None,
            condition=None) -> ndarray:
        """Maximum. Équivalent OpenFisca : GroupPopulation.max(array, role)"""
        values = self._target_values(variable_name, period)
        return self._aggregate(numpy.maximum, -numpy.inf, values, role, condition)

    def any(self, variable_name, period, role=None,
            condition=None) -> ndarray:
        """Au moins un vrai. Équivalent : GroupPopulation.any()"""
        values = self._target_values(variable_name, period)
        return self._aggregate(numpy.logical_or, False, values, role, condition)

    def all(self, variable_name, period, role=None,
            condition=None) -> ndarray:
        """Tous vrais. Équivalent : GroupPopulation.all()"""
        values = self._target_values(variable_name, period)
        return self._aggregate(numpy.logical_and, True, values, role, condition)

    # ── Accès positionnels et par rôle (enrichissements OpenFisca) ──

    def nth(self, n, variable_name, period) -> ndarray:
        """Valeur de la n-ième cible.

        Équivalent OpenFisca : GroupPopulation.value_nth_person(n, array)
        """
        ...

    def get_by_role(self, variable_name, period, role) -> ndarray:
        """Valeur de la cible ayant un rôle unique donné.

        Équivalent : UniqueRoleToEntityProjector →
            GroupPopulation.value_from_person(array, role)
        """
        ...

    # ── Mécanique interne ──────────────────────────────────────────

    def _aggregate(self, ufunc, identity, values, role=None,
                   condition=None, weights=None):
        """Agrégation générique avec filtre rôle + condition + poids.

        Combine la logique de LIAM2 (Aggregate.compute) avec les
        filtres par rôle d'OpenFisca (GroupPopulation.sum).
        """
        target_pop = self._target_population
        source_pop = self._source_population

        # IDs source dans le contexte cible
        source_ids = target_pop.simulation.calculate(self.link_field, period)
        source_rows = self._resolve_source_ids(source_ids)

        # Filtre par rôle (enrichissement OpenFisca)
        if role is not None and self.role_field is not None:
            roles = target_pop.simulation.calculate(self.role_field, ETERNITY)
            role_mask = (roles == role)
            source_rows = source_rows[role_mask]
            values = values[role_mask]

        # Filtre par condition (capacité LIAM2)
        if condition is not None:
            source_rows = source_rows[condition]
            values = values[condition]

        # Poids (capacité LIAM2)
        if weights is not None:
            values = values * weights

        # Filtrer les lines invalides
        valid = source_rows >= 0
        source_rows = source_rows[valid]
        values = values[valid]

        # Agrégation
        if ufunc in (numpy.add,):
            return numpy.bincount(source_rows, weights=values,
                                  minlength=source_pop.count)
        else:
            result = numpy.full(source_pop.count, identity, dtype=values.dtype)
            ufunc.at(result, source_rows, values)
            return result
```

### 5.5 Migration : les projectors deviennent des façades

La clé de la compatibilité ascendante est de **réimplémenter les projectors actuels
comme des façades** (thin wrappers) par-dessus le nouveau système de lines :

```python
class EntityToPersonProjector(Projector):
    """person.household("rent", period)
    → délègue à Many2OneLink.get()
    """
    def transform(self, result):
        link = self._get_underlying_link()
        return link.get(self._variable_name, self._period)


class UniqueRoleToEntityProjector(Projector):
    """household.declarant_principal("salary", period)
    → délègue à One2ManyLink.get_by_role()
    """
    def transform(self, result):
        link = self._get_underlying_link()
        return link.get_by_role(self._variable_name, self._period, self.role)


class FirstPersonToEntityProjector(Projector):
    """household.first_person("age", period)
    → délègue à One2ManyLink.nth(0)
    """
    def transform(self, result):
        link = self._get_underlying_link()
        return link.nth(0, self._variable_name, self._period)
```

Et `GroupPopulation` peut déléguer ses agrégations au line sous-jacent :

```python
class GroupPopulation(CorePopulation):
    @projectors.projectable
    def sum(self, array, role=None):
        # AVANT : numpy.bincount(self.members_entity_id, weights=array)
        # APRÈS : délègue au line implicite
        persons_link = self.entity.get_link("_members")
        if persons_link and role is not None:
            return persons_link.sum(array, role=role)
        # Fallback
        return numpy.bincount(self.members_entity_id, weights=array,
                              minlength=self.count)
```

### 5.6 Génération automatique de lines depuis les GroupEntity existantes

Au démarrage de la simulation, le système génère automatiquement des lines
à partir de la structure `GroupEntity` + `GroupPopulation` existante :

```python
class Simulation:
    def _generate_links_from_group_entities(self):
        """Générer les lines implicites depuis les GroupEntity existantes.

        Permet à tout code existent de continuer à fonctionner.
        """
        person_entity = self.persons.entity

        for key, population in self.populations.items():
            if not isinstance(population, GroupPopulation):
                continue

            group_entity = population.entity

            # 1. Many2One implicite : person → group
            m2o = Many2OneLink(
                name=group_entity.key,
                link_field=f"_implicit_{group_entity.key}_id",
                target_entity_key=group_entity.key,
                role_field=f"_implicit_{group_entity.key}_role",
                position_field=f"_implicit_{group_entity.key}_position",
            )
            person_entity.add_link(m2o)

            # 2. One2Many implicite : group → persons
            o2m = One2ManyLink(
                name="members",
                link_field=f"_implicit_{group_entity.key}_id",
                target_entity_key=person_entity.key,
                role_field=f"_implicit_{group_entity.key}_role",
            )
            group_entity.add_link(o2m)
```

### 5.7 Architecture résultante

```
                    AVANT (OpenFisca actuel)
                    ────────────────────────
Entity ──── GroupEntity ──── Role
              │
Population ── GroupPopulation
              │  members_entity_id / members_role / members_position
              │  sum() / project() / ...
              │
Projector ──── EntityToPersonProjector
              │  FirstPersonToEntityProjector
              │  UniqueRoleToEntityProjector
              │
Formulas:  person.household("rent", period)


                    APRÈS (LIAM2 amélioré)
                    ─────────────────────
Entity ──── GroupEntity ──── Role  (inchangé)
   │
   ├── _links: dict[str, Link]    (NOUVEAU)
   │    ├── Many2OneLink (+ role, position)
   │    ├── One2ManyLink (+ role, nth, get_by_role)
   │    └── ChainedLink
   │
Population ── GroupPopulation      (inchangé extérieurement, délègue)
   │
Projector ──── façades vers Links  (réimplémentés en interne)
   │
Formulas:  person.household("rent", period)            ← INCHANGÉ
           person.mother("age", period)                 ← NOUVEAU
           household.members.sum("salary", role=CHILD)  ← NOUVEAU
           person.mother.household("rent", period)      ← NOUVEAU
```

### 5.8 Plan de réalisation par phases

| Phase | Description | Fichiers | Effort |
|---|---|---|---|
| **Phase 1** | Classes `Link`, `Many2OneLink`, `One2ManyLink`, `ChainedLink` | `links/` (nouveau module) | 3-4 jours |
| **Phase 2** | Ajout de `_links` à `CoreEntity`, résolution dans `Simulation` | `entities/`, `simulations/` | 2-3 jours |
| **Phase 3** | Génération automatique de lines depuis `GroupEntity` | `simulations/` | 2-3 jours |
| **Phase 4** | Réimplémentation des projectors comme façades | `projectors/` | 2-3 jours |
| **Phase 5** | API pays : déclaration de lines (mother, employer...) | `entities/`, docs | 1-2 jours |
| **Phase 6** | Tests (unitaires, intégration, non-régression) | `tests/` | 3-4 jours |
| **Total** | | | **~14-19 jours** |

### 5.9 Critère de succès

Le nouveau système est considéré comme réussi si :

1. **Toutes les formulas existantes** de tous les pays continuent de
   fonctionner **sans aucune modification**
2. Les **14 fonctionnalités** du tableau §5.3 passent des tests de non-régression
3. Les **7 nouvelles capacités** (A-G) fonctionnent dans des tests unitaires
4. La **performance** ne montre pas de dégradation significative (< 10%)
5. La déclaration de lines personnalisés fonctionne dans un project pays de test

### 5.10 Relation avec le PoC « populations dynamiques »

Le système de lines est **complémentaire** au PoC des populations dynamiques :

- **Sans populations dynamiques** : les lines fonctionnent en mode statique, avec des
  variables de liaison fixées à l'initialisation. Les lines intra-entité (mother, children)
  sont possibles mais ne changent pas au cours de la simulation.

- **Avec populations dynamiques** : les lines deviennent pleinement dynamiques. Les
  variables de liaison (`mother_id`, `hh_id`) peuvent être modifiées, et les ajouts/suppressions
  d'individus se propagent correctement via `id_to_rownum`.

**Recommendation** : Implémenter le système de lines **avant** les populations dynamiques.
Les lines en mode statique apportent déjà une valeur significative (lines familiaux,
lines employeur) et constituent le socle sur lequel les populations dynamiques s'appuieront.

### 5.11 Format de déclaration des entités et lines

#### 5.11.1 La déclaration actuelle (OpenFisca-France)

Aujourd'hui, les entités sont déclarées en Python dans un fichier `entities.py`
par pays, sans aucune notion de line explicite :

```python
# openfisca_france/entities.py (actuel)
from openfisca_core.entities import build_entity

Individu = build_entity(key='individu', ..., is_person=True)

Famille = build_entity(
    key='famille', ...,
    roles=[
        {'key': 'parent', 'subroles': ['demandeur', 'conjoint']},
        {'key': 'enfant', 'plural': 'enfants'},
    ],
)

FoyerFiscal = build_entity(
    key='foyer_fiscal', ...,
    roles=[
        {'key': 'declarant', 'subroles': ['declarant_principal', 'conjoint']},
        {'key': 'personne_a_charge', 'plural': 'personnes_a_charge'},
    ],
)

Menage = build_entity(
    key='menage', ...,
    roles=[
        {'key': 'personne_de_reference', 'max': 1},
        {'key': 'conjoint', 'max': 1},
        {'key': 'enfant', 'plural': 'enfants'},
        {'key': 'autre', 'plural': 'autres'},
    ],
)

entities = [Individu, Famille, FoyerFiscal, Menage]
```

Les lines personne↔groupe sont **implicites** — ils existent du seul fait
qu'il y a un `GroupEntity` avec des rôles. Il n'y a aucune déclaration de line.

#### 5.11.2 Option A : Déclaration YAML (à la LIAM2)

Cette approach rendrait la structure des entités et lines **déclarative et lisible
d'un coup d'œil** :

```yaml
# entities.yml — OpenFisca-France avec lines explicites

entities:
    individu:
        is_person: true
        label: "Individu"

        links:
            # Lines personne → groupe (remplacent l'implicite actuel)
            famille:
                type: many2one
                target: famille
                field: famille_id
                role_field: famille_role

            foyer_fiscal:
                type: many2one
                target: foyer_fiscal
                field: foyer_fiscal_id
                role_field: foyer_fiscal_role

            menage:
                type: many2one
                target: menage
                field: menage_id
                role_field: menage_role

            # Lines intra-entité (NOUVEAUX — impossibles aujourd'hui)
            mere:
                type: many2one
                target: individu
                field: mere_id

            pere:
                type: many2one
                target: individu
                field: pere_id

            conjoint:
                type: many2one
                target: individu
                field: conjoint_id

            enfants:
                type: one2many
                target: individu
                field: mere_id

    famille:
        label: "Famille (prestations familiales)"
        roles:
            parent:
                plural: parents
                subroles: [demandeur, conjoint]
            enfant:
                plural: enfants

        links:
            membres:
                type: one2many
                target: individu
                field: famille_id
                role_field: famille_role

    foyer_fiscal:
        label: "Déclaration d'impôts"
        roles:
            declarant:
                plural: declarants
                subroles: [declarant_principal, conjoint]
            personne_a_charge:
                plural: personnes_a_charge

        links:
            membres:
                type: one2many
                target: individu
                field: foyer_fiscal_id
                role_field: foyer_fiscal_role

    menage:
        label: "Logement principal"
        roles:
            personne_de_reference:
                max: 1
            conjoint:
                max: 1
            enfant:
                plural: enfants
            autre:
                plural: autres

        links:
            membres:
                type: one2many
                target: individu
                field: menage_id
                role_field: menage_role
```

**Avantage** : Vue d'ensemble complète et lisible de toute la structure relationnelle.
On voit immédiatement que l'individu a 6 types de lines (3 vers des groupes, 3 intra-entité).

#### 5.11.3 Option B : Déclaration Python enrichie

Cette approach conserve le `build_entity()` existent et ajoute les lines
via `add_link()` — **zéro rupture de compatibilité** :

```python
# openfisca_france/entities.py (enrichi — compatible avec l'existant)
from openfisca_core.entities import build_entity
from openfisca_core.links import Many2OneLink, One2ManyLink

# ── Entités (INCHANGÉ par rapport à aujourd'hui) ──────────────────

Individu = build_entity(
    key='individu',
    plural='individus',
    label='Individu',
    is_person=True,
)

Famille = build_entity(
    key='famille',
    plural='familles',
    label='Famille',
    roles=[
        {'key': 'parent', 'subroles': ['demandeur', 'conjoint']},
        {'key': 'enfant', 'plural': 'enfants'},
    ],
)

FoyerFiscal = build_entity(
    key='foyer_fiscal',
    plural='foyers_fiscaux',
    label="Déclaration d'impôts",
    roles=[
        {'key': 'declarant', 'subroles': ['declarant_principal', 'conjoint']},
        {'key': 'personne_a_charge', 'plural': 'personnes_a_charge'},
    ],
)

Menage = build_entity(
    key='menage',
    plural='menages',
    label='Logement principal',
    roles=[
        {'key': 'personne_de_reference', 'max': 1},
        {'key': 'conjoint', 'max': 1},
        {'key': 'enfant', 'plural': 'enfants'},
        {'key': 'autre', 'plural': 'autres'},
    ],
)

# ── Lines supplémentaires (NOUVEAU) ───────────────────────────────
# Les lines personne ↔ groupe sont auto-générés depuis les GroupEntity.
# On déclare ici les lines SUPPLÉMENTAIRES :

# Lines familiaux intra-entité
Individu.add_link(Many2OneLink('mere', field='mere_id', target='individu'))
Individu.add_link(Many2OneLink('pere', field='pere_id', target='individu'))
Individu.add_link(Many2OneLink('conjoint', field='conjoint_id', target='individu'))
Individu.add_link(One2ManyLink('enfants', field='mere_id', target='individu'))

# Exemple : line vers l'employeur (si modélisé)
# Individu.add_link(Many2OneLink('employeur', field='employeur_id', target='entreprise'))

entities = [Individu, Famille, FoyerFiscal, Menage]
```

**Avantage** : Le fichier `entities.py` d'un pays qui n'a **pas encore** de lines
supplémentaires reste **strictement identique** à aujourd'hui. Les 4 lignes `add_link()`
sont le seul ajout.

#### 5.11.4 Option C : Approach mixte (recommandée)

**Python pour les entités, YAML optionnel pour les lines** :

```python
# openfisca_france/entities.py — approach mixte

from openfisca_core.entities import build_entity, load_links

# Entités : déclaration Python (comme aujourd'hui)
Individu = build_entity(key='individu', ..., is_person=True)
Famille = build_entity(key='famille', ..., roles=[...])
FoyerFiscal = build_entity(key='foyer_fiscal', ..., roles=[...])
Menage = build_entity(key='menage', ..., roles=[...])

entities = [Individu, Famille, FoyerFiscal, Menage]

# Lines : chargement optionnel depuis un fichier YAML
load_links('links.yml', entities)    # ← optionnel
```

```yaml
# openfisca_france/links.yml — déclaration des lines supplémentaires
links:
    individu:
        mere:     {type: many2one, target: individu, field: mere_id}
        pere:     {type: many2one, target: individu, field: pere_id}
        conjoint: {type: many2one, target: individu, field: conjoint_id}
        enfants:  {type: one2many, target: individu, field: mere_id}
```

#### 5.11.5 Comparison des approaches

| Critère | YAML (A) | Python (B) | Mixte (C) |
|---|---|---|---|
| **Compatibilité** | 🔴 Rupture totale | ✅ Zéro rupture | ✅ Zéro rupture |
| **Lisibilité** | ✅ Vue d'ensemble | 🟡 Plus verbeux | ✅ Chaque format fait ce qu'il fait mieux |
| **Validation IDE** | ❌ Pas de typage | ✅ Autocomplétion | 🟡 Partiel |
| **Migration** | 🔴 Réécriture totale | ✅ Ajout incrémental | ✅ Ajout incrémental |
| **Extensibilité** | 🟡 Limité au schéma | ✅ Illimité | ✅ Illimité |
| **Effort** | 3-4 jours (parser) | 1 jour (`add_link()`) | 2 jours |

#### 5.11.6 Recommendation : Python d'abord (Option B)

L'approche **Python d'abord** est la plus pragmatique pour le démarrage :

1. **Zéro rupture** — `build_entity()` ne change pas
2. **Les lines personne↔groupe restent implicites** — auto-générés depuis `GroupEntity`
   (cf. §5.6), aucune modification requise dans les pays existants
3. **Les lines supplémentaires sont opt-in** — un pays ajoute `add_link()` uniquement
   quand il en a besoin
4. **Un loader YAML peut venir ensuite** — pour ceux qui préfèrent la structure déclarative,
   sans bloquer le développement initial
5. **La migration est progressive** — chaque pays peut adopter les lines à son rythme

Concrètement, un pays existent (ex: `openfisca-france`) pourrait ajouter les lines
familiaux en **4 lignes de code** sans toucher à rien d'autre :

```python
# Ajout à la fin de entities.py — c'est tout !
Individu.add_link(Many2OneLink('mere', field='mere_id', target='individu'))
Individu.add_link(Many2OneLink('pere', field='pere_id', target='individu'))
Individu.add_link(Many2OneLink('conjoint', field='conjoint_id', target='individu'))
Individu.add_link(One2ManyLink('enfants', field='mere_id', target='individu'))
```

Et les formulas pourraient immédiatement utiliser :
```python
class pension_alimentaire(Variable):
    def formula(individu, period):
        age_mere = individu.mere("age", period)         # Many2One intra
        nb_enfants = individu.enfants.count(period)      # One2Many intra
        revenu_conjoint = individu.conjoint("revenu_net", period)  # One2One intra
        rent_menage = individu.menage("rent", period)    # Many2One inter (existent)
        return ...
```

### 5.12 Extensibilité des opérations sur les lines : l'avantage Python

#### 5.12.1 Le problème de LIAM2 : un vocabulaire fermé

Dans LIAM2, les opérations disponibles sur les lines sont **figées dans le DSL YAML** :
`sum`, `count`, `avg`, `min`, `max`, et quelques autres. Si un modélisateur a besoin
d'une nouvelle opération (médiane, écart-type, percentile, Gini, etc.), il doit
**modifier le code source du motor LIAM2** — ce qui n'est pas à la portée d'un
utilisateur standard.

```yaml
# LIAM2 : vocabulaire fermé
- total: household.persons.sum(salary)      # ✅ existe
- nb: household.persons.count()              # ✅ existe
- median: household.persons.median(salary)   # ❌ n'existe pas
- gini: household.persons.gini(salary)       # ❌ n'existe pas
- top3: household.persons.top_n(3, salary)   # ❌ n'existe pas
```

C'est la conséquence directe du choix d'un DSL déclaratif : **le DSL définit les
limites de ce qui est exprimable.**

#### 5.12.2 L'avantage Python : un vocabulaire ouvert

Avec une approach Python, les opérations sur les lines sont des **méthodes Python
ordinaires**. N'importe qui peut en ajouter — dans le framework, dans un package pays,
ou même directement dans une formule :

```python
# ── Niveau 1 : Utilisation directe de numpy dans les formulas ──────

class gini_menage(Variable):
    def formula(menage, period):
        salaries = menage.members("salary", period)
        # On peut utiliser N'IMPORTE quelle opération numpy/scipy
        entity_ids = menage.members_entity_id
        ginis = numpy.zeros(menage.count)
        for i in range(menage.count):
            s = salaries[entity_ids == i]
            s_sorted = numpy.sort(s)
            n = len(s)
            if n > 0:
                index = numpy.arange(1, n + 1)
                ginis[i] = (2 * numpy.sum(index * s_sorted)) / (n * numpy.sum(s_sorted)) - (n + 1) / n
        return ginis
```

```python
# ── Niveau 2 : Extension du One2ManyLink par sous-classement ──────

class EnhancedOne2ManyLink(One2ManyLink):
    """Line One2Many avec opérations statistiques avancées."""

    def median(self, variable_name, period, role=None) -> ndarray:
        """Médiane par groupe."""
        values = self._target_values(variable_name, period)
        source_rows = self._get_source_rows(role)
        return self._grouped_operation(numpy.median, values, source_rows)

    def std(self, variable_name, period, role=None) -> ndarray:
        """Écart-type par groupe."""
        values = self._target_values(variable_name, period)
        source_rows = self._get_source_rows(role)
        return self._grouped_operation(numpy.std, values, source_rows)

    def percentile(self, variable_name, period, q, role=None) -> ndarray:
        """Percentile par groupe."""
        ...

    def top_n(self, n, variable_name, period, role=None) -> ndarray:
        """Some ou valeurs des n plus grandes valeurs par groupe."""
        ...

    def weighted_avg(self, variable_name, weight_name, period,
                     role=None) -> ndarray:
        """Moyenne pondérée par groupe."""
        values = self._target_values(variable_name, period)
        weights = self._target_values(weight_name, period)
        weighted_sum = self._aggregate(numpy.add, 0.0,
                                        values * weights, role)
        total_weight = self._aggregate(numpy.add, 0.0, weights, role)
        return numpy.where(total_weight > 0,
                           weighted_sum / total_weight, 0)
```

```python
# ── Niveau 3 : Helpers spécifiques à un pays ──────────────────────

# openfisca_france/links/helpers.py
def parts_fiscales(foyer_fiscal, period):
    """Calcul du nombre de parts fiscales — logique spécifique France.

    Utilise les lines et rôles pour une implémentation lisible.
    """
    membres = foyer_fiscal.entity.get_link("membres")
    nb_declarants = membres.count(role=FoyerFiscal.DECLARANT, period=period)
    nb_pac = membres.count(role=FoyerFiscal.PERSONNE_A_CHARGE, period=period)
    ages = membres._target_values("age", period)
    # ... logique complexe des demi-parts ...
    return parts
```

```python
# ── Niveau 4 : Composition libre dans les formulas ────────────────

class allocation_logement(Variable):
    def formula(menage, period):
        membres = menage.entity.get_link("membres")

        # Opérations combinées librement
        revenus = membres._target_values("revenu_net", period)
        ages = membres._target_values("age", period)

        # Revenu moyen des adultes (filtre arbitraire)
        revenu_adultes = membres.avg("revenu_net", period,
                                      condition=(ages >= 18))

        # Part des enfants dans le ménage
        nb_total = membres.count(period=period)
        nb_enfants = membres.count(role=Menage.ENFANT, period=period)
        ratio_enfants = numpy.where(nb_total > 0,
                                     nb_enfants / nb_total, 0)

        # Calcul libre, pas de limit du DSL
        rent = menage("rent", period)
        return rent * 0.5 * (1 + ratio_enfants) * (revenu_adultes < 2000)
```

#### 5.12.3 Comparison : vocabulaire fermé vs ouvert

| Aspect | LIAM2 (YAML DSL) | OpenFisca (Python) |
|---|---|---|
| **Opérations de base** | `sum`, `count`, `avg`, `min`, `max` | ✅ Les mêmes |
| **Ajout d'opérations** | Modifier le motor LIAM2 | Sous-classer `One2ManyLink` ou écrire du numpy |
| **Qui peut étendre ?** | Développeur LIAM2 uniquement | N'importe quel modélisateur |
| **Opérations statistiques** | ❌ Absentes | ✅ `median`, `std`, `percentile`, `gini`... |
| **Logique métier** | ❌ Limitée au DSL | ✅ `parts_fiscales()`, `quotient_familial()`... |
| **Composition** | Limitée (expressions LIAM2) | Illimitée (Python + numpy) |
| **Débogage** | Opaque (DSL interprété) | Standard (pdb, breakpoints, print) |
| **Tests unitaires** | Limités | pytest standard |

#### 5.12.4 L'insight : les lines sont des objects, pas des instructions

La différence fondamentale est conceptuelle :

- **LIAM2** : un line est une **instruction** dans un language déclaratif.
  Les opérations possibles sont cells que le language prévoit.

- **OpenFisca avec lines** : un line est un **object Python**.
  Les opérations possibles sont cells de Python — donc **illimitées**.

Cela signifie que le framework fournit les primitives (`get`, `sum`, `count`, `nth`,
`get_by_role`...) et que les utilisateurs peuvent :

1. **Combiner** ces primitives librement dans leurs formulas
2. **Sous-classer** les types de lines pour ajouter des méthodes
3. **Créer des helpers** spécifiques à leur système pays
4. **Utiliser tout l'écosystème Python** (numpy, scipy, pandas) dans les calculus

C'est un avantage décisif de l'approche Python qui justifie pleinement
la recommendation de ne **pas** remplacer Python par un DSL YAML, mais
de s'inspirer de la **logique** de LIAM2 tout en restant dans Python.

### 5.13 Analyse de performance du système de lines

#### 5.13.1 État actuel : tout est déjà vectorisé

Une analyse exhaustive du code des projectors et de `GroupPopulation` montre
que **toutes les opérations de lines sont déjà vectorisées** en numpy :

| Opération | Code (simplifié) | Complexité | Vectorisé ? |
|---|---|---|---|
| **project** (entity→person) | `array[members_entity_id]` | O(N) fancy index | ✅ numpy pur |
| **sum** (person→entity) | `numpy.bincount(entity_id, weights=array)` | O(N) | ✅ numpy pur |
| **any** (person→entity) | `sum(array) > 0` | O(N) | ✅ numpy pur |
| **count** / `nb_persons` | `numpy.bincount(entity_id)` | O(N) | ✅ numpy pur |
| **has_role** (filtre) | `members_role == role` | O(N) comparison | ✅ numpy pur |
| **value_from_person** (rôle unique) | `array[members_map][role_filter[members_map]]` | O(N) fancy index | ✅ numpy pur |
| **value_nth_person** | `array[members_map][positions[members_map] == n]` | O(N) | ✅ numpy pur |
| **project avec rôle** | `numpy.where(role_condition, array[entity_id], 0)` | O(N) | ✅ numpy pur |
| **ordered_members_map** | `numpy.argsort(entity_id)` | O(N log N) | ✅ numpy pur |

**Aucune boucle Python** dans les projectors. Les 3 classes de projectors
(`EntityToPersonProjector`, `FirstPersonToEntityProjector`,
`UniqueRoleToEntityProjector`) sont de simples wrappers de ~10 lignes
qui délèguent à des opérations numpy.

#### 5.13.2 Les opérations du futur système de lines

Les nouvelles opérations que le système de lines ajouterait sont :

| Opération | Implémentation prévue | Vectorisé ? |
|---|---|---|
| **Many2One.get** | `target_array[link_ids]` — fancy indexing | ✅ O(N) |
| **Many2One.set** | `link_ids[:] = new_ids` — assignation | ✅ O(N) |
| **One2Many.sum** | `numpy.bincount(link_ids, weights=values)` | ✅ O(N) |
| **One2Many.count** | `numpy.bincount(link_ids)` | ✅ O(N) |
| **One2Many.filter_by_role** | `values[roles == target_role]` | ✅ O(N) |
| **ChainedLink.get** | `target2[target1[link_ids]]` — 2 fancy indexings | ✅ O(N) |
| **Link integrity check** | `numpy.isin(link_ids, valid_ids)` | ✅ O(N) |
| **id_to_rownum lookup** | `rownum_array[ids]` — direct indexing | ✅ O(1) par élément |

Tout est du **fancy indexing numpy** ou du **bincount** — les deux
opérations les plus optimisées de numpy (implémentées en C).

#### 5.13.3 Et les lines intra-entité (mère, conjoint) ?

Les nouveaux lines intra-entité (`person.mother`, `person.spouse`) sont
encore plus simples car ce sont de purs Many2One :

```python
# person.mother("salary", period)
# Implémentation : UNE seule ligne numpy
mother_salary = salary_array[mother_id]  # fancy indexing O(N)

# person.mother.household("income", period)
# Chaîné : DEUX fancy indexings
mother_hh_id = household_id[mother_id]   # O(N)
mother_hh_income = income[mother_hh_id]  # O(N)
```

Pas de boucle, pas de matrice, pas de tri — juste de l'indexation.

#### 5.13.4 Où sont les hotspots ?

Les seuls hotspots du système de lines/projectors sont ceux **déjà identifiés**
dans `group_population.py`, qui sont partagés avec le système de projectors
existent :

| Hotspot | Utilisé par | Impact |
|---|---|---|
| `members_position` (boucle Python) | `value_nth_person`, `get_rank` | 🔴 Seul vrai problème |
| `reduce()` (boucle sur taille max) | `min`, `max`, `all` | 🟡 Mineur |
| `get_rank()` (matrice dense) | `get_rank` | 🟡 Mineur |

Les projectors eux-mêmes (`EntityToPersonProjector.transform`,
`FirstPersonToEntityProjector.transform`, etc.) n'ont **aucune boucle** — ce
sont des appels directs à des opérations numpy O(N).

#### 5.13.5 Conclusion

**Le système de lines n'a aucun problème de performance intrinsèque.**

Toutes les opérations de line se réduisent à :
- **Fancy indexing** : `array[ids]` → C optimisé dans numpy
- **bincount** : `numpy.bincount(ids, weights)` → C optimisé dans numpy
- **Comparison vectorielle** : `array == value` → C optimisé dans numpy

Il n'y a **aucun besoin** de Numba, JAX, Cython ou autre accélérateur pour
le système de lines. Les seuls hotspots sont dans les functions de groupement
(`members_position`, `reduce`, `get_rank`) qui sont **communes** au système
actuel et au futur système de lines.

L'effort d'optimisation sur les lines se concentre donc sur :

1. **Vectoriser `members_position`** en numpy pur (bénéficie aussi aux
   projectors actuels) — 1 jour, 100× de gain
2. **L'intégrité des lines** : vérifier que les `link_ids` pointent vers
   des individus existants — un `numpy.isin()`, O(N), déjà vectorisé
3. **Le cache `id_to_rownum`** : maintenir le mapping quand la population
   mute — O(N) par mutation, déjà prévu dans le plan de populations dynamiques
