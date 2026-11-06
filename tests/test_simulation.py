"""Tests unitaires du module simulateur.simulation (réseau, analyseur, simulation)."""
import json
import os
import random

import pytest

from simulateur.route import Route
from simulateur.simulation import Analyseur, ReseauRoutier, Simulation
from simulateur.vehicule import Vehicule

CONFIG_REELLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "data", "config_reseau.json")


# =============================================================== ReseauRoutier
def test_plus_court_chemin_nominal(reseau_abc):
    assert reseau_abc.plus_court_chemin("A", "C") == ["A-B", "B-C"]


def test_dijkstra_choisit_le_plus_rapide_pas_le_plus_court(reseau_abc):
    reseau_abc.ajouter_route(Route("A-C", "A", "C", 1500, 10))   # court mais très lent
    assert reseau_abc.plus_court_chemin("A", "C") == ["A-B", "B-C"]


def test_chemin_inexistant_sens_unique(reseau_abc):
    assert reseau_abc.plus_court_chemin("C", "A") is None


def test_chemin_vers_soi_meme_est_vide(reseau_abc):
    assert reseau_abc.plus_court_chemin("A", "A") == []


def test_chemin_intersection_inconnue(reseau_abc):
    with pytest.raises(ValueError):
        reseau_abc.plus_court_chemin("A", "Z")
    with pytest.raises(ValueError):
        reseau_abc.plus_court_chemin("Z", "Z")


def test_ajouter_route_intersection_inconnue(reseau_abc):
    with pytest.raises(ValueError, match="intersection inconnue"):
        reseau_abc.ajouter_route(Route("A-Z", "A", "Z", 100, 50))


def test_ajouter_route_doublon_refuse(reseau_abc):
    with pytest.raises(ValueError):
        reseau_abc.ajouter_route(Route("A-B", "A", "B", 500, 30))


def test_ajouter_intersection_doublon_refuse(reseau_abc):
    with pytest.raises(ValueError):
        reseau_abc.ajouter_intersection("A", 9, 9)


def test_depuis_config_double_sens_par_defaut():
    config = {"intersections": {"A": {"x": 0, "y": 0}, "B": {"x": 1, "y": 0}},
              "routes": [{"de": "A", "vers": "B", "longueur": 100, "limite_vitesse": 50}]}
    assert set(ReseauRoutier.depuis_config(config).routes) == {"A-B", "B-A"}


def test_depuis_config_sens_unique():
    config = {"intersections": {"A": {"x": 0, "y": 0}, "B": {"x": 1, "y": 0}},
              "routes": [{"de": "A", "vers": "B", "longueur": 100, "limite_vitesse": 50,
                          "double_sens": False}]}
    assert set(ReseauRoutier.depuis_config(config).routes) == {"A-B"}


def test_config_reelle():
    with open(CONFIG_REELLE, encoding="utf-8") as f:
        r = ReseauRoutier.depuis_config(json.load(f))
    assert len(r.intersections) == 6 and len(r.routes) == 14


def test_generer_vehicule_nominal(reseau_abc):
    v = reseau_abc.generer_vehicule(0.0, random.Random(1))
    assert v.route is reseau_abc.routes[v.itineraire[0]]
    assert v.identifiant == "V0001" and v in v.route.vehicules


def test_generer_vehicule_une_seule_intersection():
    r = ReseauRoutier()
    r.ajouter_intersection("A", 0, 0)
    with pytest.raises(ValueError):
        r.generer_vehicule(0.0, random.Random(1))


def test_generer_vehicule_reseau_sans_aucun_trajet_ne_boucle_pas():
    r = ReseauRoutier()
    r.ajouter_intersection("A", 0, 0)
    r.ajouter_intersection("B", 1, 0)           # aucune route : aucun trajet possible
    with pytest.raises(ValueError):
        r.generer_vehicule(0.0, random.Random(1))


def test_vehicule_traverse_tout_le_trajet(reseau_abc):
    v = Vehicule("V1", ["A-B", "B-C"], vitesse_max=130)
    reseau_abc.routes["A-B"].ajouter_vehicule(v)
    temps = 0
    for _ in range(10):
        temps += 60
        reseau_abc.mettre_a_jour(60, temps)
    assert v.arrive and v in reseau_abc.vehicules_arrives
    assert reseau_abc.vehicules_en_route() == []


def test_depassement_conserve_a_l_intersection(reseau_abc):
    v = Vehicule("V1", ["A-B", "B-C"], vitesse_max=130)
    reseau_abc.routes["A-B"].ajouter_vehicule(v)
    v.position = 990
    vitesse = reseau_abc.routes["A-B"].vitesse_autorisee()
    reseau_abc.mettre_a_jour(10, 10)
    assert v.route.nom == "B-C"
    assert v.position == pytest.approx(990 + vitesse / 3.6 * 10 - 1000)


def test_pas_de_temps_geant_position_reste_dans_la_route():
    """Contrainte du réseau : un véhicule ne peut pas dépasser la fin de la route où il se trouve."""
    r = ReseauRoutier()
    for nom, x in (("A", 0), ("B", 1), ("C", 2), ("D", 3)):
        r.ajouter_intersection(nom, x, 0)
    for a, b in (("A", "B"), ("B", "C"), ("C", "D")):
        r.ajouter_route(Route(f"{a}-{b}", a, b, 100, 50))
    v = Vehicule("V1", ["A-B", "B-C", "C-D"], vitesse_max=130)
    r.routes["A-B"].ajouter_vehicule(v)
    r.mettre_a_jour(delta_t=60, temps=60)        # ~ 800 m en un pas : 8 routes de 100 m
    assert v.arrive
    assert r.vehicules_en_route() == []


# ================================================================== Analyseur
def test_analyseur_vide():
    a = Analyseur()
    assert a.vitesse_moyenne_globale() == 0.0
    assert a.zones_congestion() == []
    assert a.occupation_moyenne_par_route() == {}


def test_analyseur_temps_parcours_sans_trajet(reseau_abc):
    assert Analyseur().temps_parcours(reseau_abc) == {"nb_trajets": 0, "moyen": 0.0, "min": 0.0, "max": 0.0}


def test_analyseur_detecte_la_congestion(reseau_abc):
    for i in range(30):                                   # 30/40 = 75 % > seuil 60 %
        reseau_abc.routes["A-B"].ajouter_vehicule(Vehicule(f"V{i}", ["A-B"]))
    a = Analyseur()
    a.enregistrer(60, reseau_abc)
    zones = a.zones_congestion()
    assert [z["route"] for z in zones] == ["A-B"]
    assert zones[0]["pic_occupation"] == pytest.approx(0.75)
    assert a.zones_congestion(seuil=0.9) == []


def test_analyseur_zones_triees(reseau_abc):
    for nom, n in (("A-B", 25), ("B-C", 35)):
        for i in range(n):
            reseau_abc.routes[nom].ajouter_vehicule(Vehicule(f"{nom}{i}", [nom]))
    a = Analyseur()
    a.enregistrer(60, reseau_abc)
    assert [z["route"] for z in a.zones_congestion()] == ["B-C", "A-B"]


# ================================================================== Simulation
def test_simulation_nominale(ecrire_config):
    s = Simulation(ecrire_config())
    s.lancer_simulation(n_tours=30, delta_t=60)
    assert len(s.analyseur.historique) == 30
    assert s.temps == 30 * 60
    assert s.analyseur.resume(s.reseau)["nb_tours"] == 30


def test_simulation_zero_tour(ecrire_config):
    s = Simulation(ecrire_config())
    s.lancer_simulation(n_tours=0, delta_t=60)
    assert s.analyseur.historique == [] and s.temps == 0


@pytest.mark.parametrize("n_tours", [-1, 2.5, "10", None])
def test_n_tours_invalide_refuse(ecrire_config, n_tours):
    with pytest.raises((ValueError, TypeError)):
        Simulation(ecrire_config()).lancer_simulation(n_tours, 60)


@pytest.mark.parametrize("delta_t", [0, -60])
def test_delta_t_non_positif_refuse(ecrire_config, delta_t):
    with pytest.raises(ValueError):
        Simulation(ecrire_config()).lancer_simulation(5, delta_t)


def test_delta_t_de_mauvais_type(ecrire_config):
    with pytest.raises(TypeError):
        Simulation(ecrire_config()).lancer_simulation(5, "60")


def test_fichier_config_inexistant():
    with pytest.raises(FileNotFoundError):
        Simulation("n_existe_pas.json")


def test_debit_negatif_refuse(ecrire_config):
    with pytest.raises(ValueError):
        Simulation(ecrire_config(vehicules_par_minute=-5))


def test_plage_vitesse_incoherente_refusee(ecrire_config):
    with pytest.raises(ValueError):
        Simulation(ecrire_config(vitesse_max_vehicule=[130, 90]))


def test_generation_selon_le_debit(ecrire_config):
    s = Simulation(ecrire_config(vehicules_par_minute=10))
    s.lancer_simulation(20, 60)
    assert s.reseau._compteur_id == 200


def test_debit_nul_aucun_vehicule(ecrire_config):
    s = Simulation(ecrire_config(vehicules_par_minute=0))
    s.lancer_simulation(10, 60)
    assert s.reseau._compteur_id == 0


def test_callback_tous_les_n_tours(ecrire_config):
    appels = []
    s = Simulation(ecrire_config())
    s.lancer_simulation(30, 60, afficher_tous_les=10, callback=lambda t, a: appels.append(t))
    assert appels == [10.0, 20.0, 30.0]


def test_conservation_des_vehicules():
    s = Simulation(CONFIG_REELLE)
    s.lancer_simulation(40, 60)
    r = s.reseau
    assert r._compteur_id == len(r.vehicules_en_route()) + len(r.vehicules_arrives)


def test_reproductible_avec_la_graine():
    a, b = Simulation(CONFIG_REELLE), Simulation(CONFIG_REELLE)
    a.lancer_simulation(20, 60); b.lancer_simulation(20, 60)
    assert a.analyseur.resume(a.reseau) == b.analyseur.resume(b.reseau)


def test_graine_differente_resultat_different(ecrire_config):
    a = Simulation(ecrire_config(graine=1)); a.lancer_simulation(20, 60)
    b = Simulation(ecrire_config(graine=2)); b.lancer_simulation(20, 60)
    assert a.analyseur.historique != b.analyseur.historique


def test_vehicules_evoluent_selon_les_regles_de_deplacement():
    """Positions croissantes sur une route, vitesses bornées, trajets cohérents."""
    s = Simulation(CONFIG_REELLE)
    s.lancer_simulation(1, 60)
    suivi = {v.identifiant: (v.index_route, v.position) for v in s.reseau.vehicules_en_route()}
    s.lancer_simulation(1, 60)
    for v in s.reseau.vehicules_en_route():
        if v.identifiant in suivi:
            idx, pos = suivi[v.identifiant]
            assert v.index_route >= idx
            if v.index_route == idx:
                assert v.position > pos          # il a avancé
        assert 0 <= v.vitesse <= v.vitesse_max
        assert v.vitesse <= v.route.limite_vitesse + 1e-9


def test_contraintes_du_reseau_respectees_a_chaque_tour():
    s = Simulation(CONFIG_REELLE)
    for _ in range(60):
        s.lancer_simulation(1, 60)
        for route in s.reseau.routes.values():
            for v in route.vehicules:
                assert 0 <= v.position <= route.longueur
                assert v.itineraire[v.index_route] == route.nom
        assert all(v.route is None for v in s.reseau.vehicules_arrives)
        enroute = s.reseau.vehicules_en_route()
        assert len({v.identifiant for v in enroute}) == len(enroute)
        for v in s.reseau.vehicules_arrives:
            assert v.temps_parcours > 0


def test_les_trajets_utilisent_des_routes_existantes():
    s = Simulation(CONFIG_REELLE)
    s.lancer_simulation(10, 60)
    for v in s.reseau.vehicules_en_route() + s.reseau.vehicules_arrives:
        assert all(nom in s.reseau.routes for nom in v.itineraire)
