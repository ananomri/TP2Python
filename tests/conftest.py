"""Fixtures partagées par tous les tests."""
import json

import pytest

from simulateur.route import Route
from simulateur.simulation import ReseauRoutier


@pytest.fixture
def reseau_abc():
    """Réseau linéaire A -> B -> C, deux routes de 1000 m limitées à 50 km/h (capacité 40)."""
    r = ReseauRoutier()
    for nom, x in (("A", 0), ("B", 1), ("C", 2)):
        r.ajouter_intersection(nom, x, 0)
    r.ajouter_route(Route("A-B", "A", "B", 1000, 50))
    r.ajouter_route(Route("B-C", "B", "C", 1000, 50))
    return r


@pytest.fixture
def ecrire_config(tmp_path):
    """Fabrique un fichier de configuration JSON temporaire et renvoie son chemin."""
    def _ecrire(**surcharges):
        config = {
            "graine": 1,
            "vehicules_par_minute": 10,
            "vitesse_max_vehicule": [90, 130],
            "intersections": {"A": {"x": 0, "y": 0}, "B": {"x": 1, "y": 0}, "C": {"x": 2, "y": 0}},
            "routes": [{"de": "A", "vers": "B", "longueur": 1000, "limite_vitesse": 50},
                       {"de": "B", "vers": "C", "longueur": 1000, "limite_vitesse": 50}],
        }
        config.update(surcharges)
        chemin = tmp_path / "config.json"
        chemin.write_text(json.dumps(config), encoding="utf-8")
        return str(chemin)
    return _ecrire
