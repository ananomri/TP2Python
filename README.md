# simulateur

Package Python qui simule le déplacement de véhicules sur un réseau routier.
Le réseau est un **graphe orienté** : les intersections sont les nœuds, les routes
les arêtes. Chaque véhicule suit le trajet le plus rapide (algorithme de Dijkstra)
et sa vitesse diminue quand la route se remplit. Le package détecte ensuite les
zones de congestion.

## Fonctionnalités

- modélisation d'un réseau (intersections, routes à une ou plusieurs voies, sens unique ou double sens) ;
- calcul d'itinéraires par Dijkstra, fondé sur le **temps** de parcours et non la distance ;
- modèle de vitesse linéaire : `v = limite × max(0,1 ; 1 − occupation)` ;
- génération de trafic selon un débit (véhicules/minute), reproductible grâce à une graine ;
- statistiques : vitesse moyenne, temps de parcours, occupation par route, zones de congestion ;
- validation stricte des paramètres (`TypeError` / `ValueError`).

## Organisation

```
simulateur/
├── simulateur/
│   ├── __init__.py       # API publique
│   ├── _validation.py    # contrôles de type et de valeur (interne)
│   ├── vehicule.py       # classe Vehicule
│   ├── route.py          # classe Route
│   └── simulation.py     # ReseauRoutier, Analyseur, Simulation
├── tests/
│   ├── conftest.py
│   ├── test_vehicule.py
│   ├── test_route.py
│   └── test_simulation.py
├── data/config_reseau.json
├── exemples/exemple_simple.py
├── README.md
└── pyproject.toml
```

## Prérequis

- Python **3.9 ou plus récent** ;
- aucune dépendance d'exécution ;
- `pytest` pour lancer les tests.

## Installation

```bash
# depuis le dossier du projet (là où se trouve pyproject.toml)
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -e ".[dev]"            # installe le package + pytest
```

## Exemple d'utilisation

```python
from simulateur import Simulation

simu = Simulation("data/config_reseau.json")
simu.lancer_simulation(n_tours=60, delta_t=60)      # 60 tours d'une minute

resume = simu.analyseur.resume(simu.reseau)
print(resume["vitesse_moyenne_globale_kmh"])        # 36.09
print(resume["zones_congestion"])                   # routes saturées (ex. F-E)
```

Construire un réseau à la main :

```python
from simulateur import ReseauRoutier, Route, Vehicule

reseau = ReseauRoutier()
reseau.ajouter_intersection("A", 0, 0)
reseau.ajouter_intersection("B", 1, 0)
reseau.ajouter_route(Route("A-B", "A", "B", longueur=1000, limite_vitesse=50))
print(reseau.plus_court_chemin("A", "B"))           # ['A-B']
```

Fichier de configuration (JSON) :

| Clé | Rôle |
|---|---|
| `graine` | graine du générateur aléatoire (résultats reproductibles) |
| `vehicules_par_minute` | débit de création de véhicules (≥ 0) |
| `vitesse_max_vehicule` | `[min, max]` en km/h, `0 < min ≤ max` |
| `intersections` | `{"A": {"x": 0, "y": 2}, ...}` |
| `routes` | liste de `{de, vers, longueur, limite_vitesse, nb_voies?, double_sens?}` |

## Erreurs levées

| Situation | Exception |
|---|---|
| paramètre du mauvais type (ex. `longueur="a"`) | `TypeError` |
| valeur hors domaine (longueur ≤ 0, itinéraire vide, `n_tours` < 0, `delta_t` ≤ 0…) | `ValueError` |
| intersection inconnue, route ou intersection en double | `ValueError` |
| fichier de configuration absent | `FileNotFoundError` |

## Documentation (Sphinx)

La documentation HTML est générée à partir des docstrings (style Google).

```bash
pip install -e ".[docs]"
cd docs
make html            # Windows : make.bat html
# ouvrir docs/_build/html/index.html
```

## Tests

```bash
pytest -v                          # tous les tests
pytest tests/test_vehicule.py -v   # un module
pytest tests/test_route.py -v
pytest tests/test_simulation.py -v
pytest -k "invalide or refuse" -v  # seulement les cas invalides
pytest -x                          # s'arrêter au premier échec
```

Chaque module est testé selon quatre axes : cas nominaux, cas limites, cas invalides
et cohérence avec les règles du simulateur.
