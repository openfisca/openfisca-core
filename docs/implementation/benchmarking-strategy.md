# Stratégie de benchmarking pour OpenFisca-Core

## Objectif

Disposer de mesures **reproductibles** de performance (temps de calcul ET
mémoire) pour guider les choix d'implémentation (liens, populations
dynamiques, backends de stockage). Remplacer le « doigt mouillé » par
des chiffres rigoureux.

## Ce qu'on mesure

### Les 3 dimensions

| Dimension | Métrique | Outil |
|---|---|---|
| **Temps de calcul** | Médiane + IQR (ms) | `pytest-benchmark` |
| **Mémoire** | Pic RSS (Mo), octets/personne | `tracemalloc` |
| **Scaling** | T(N) et M(N) pour N = 100..1M | Paramétrage pytest |

### Les scénarios clés

| Scénario | Variables | Ce qu'il stresse |
|---|---|---|
| **S1** : `disposable_income` | ~15 en cascade | Moteur de calcul complet |
| **S2** : `members_position` | 1 propriété | GroupPopulation |
| **S3** : `GroupPopulation.sum` | Agrégation | bincount / reduce |
| **S4** : Multi-période (12 mois) | ~15 × 12 | Cache + mémoire |
| **S5** : Chargement du TBS | Setup | Parsing paramètres |

### Les tailles de population

| N | Usage typique |
|---|---|
| 100 | Tests unitaires |
| 10 000 | Échantillon enquête |
| 100 000 | Grosse enquête |
| 1 000 000 | Microsimulation nationale |

## Protocole

1. **Seed fixe** : `numpy.random.default_rng(42)` partout
2. **Warmup** : 1 passe à blanc avant les mesures
3. **Statistiques** : médiane + IQR, pas la moyenne
4. **Comparer avant/après** : sauvegarder les résultats par commit

## Outils

- `pytest-benchmark` : mesures de temps avec stats
- `tracemalloc` (stdlib) : mesures de mémoire
- `asv` (optionnel, futur) : tracking historique par commit

## Structure

```
benchmarks/
  conftest.py              # fixtures communes
  test_bench_compute.py    # temps de calcul
  test_bench_memory.py     # mémoire
  README.md
```

## Intégration CI (futur)

Comparaison automatique master vs PR sur chaque pull request.
