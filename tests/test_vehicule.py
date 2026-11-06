"""Tests unitaires du module simulateur.vehicule."""
import pytest

from simulateur.vehicule import Vehicule
from simulateur.route import Route


# ------------------------------------------------------------------ cas nominaux
def test_creation_nominale():
    v = Vehicule("V1", ["A-B", "B-C"], vitesse_max=110, temps_depart=30)
    assert v.identifiant == "V1"
    assert v.itineraire == ["A-B", "B-C"]
    assert (v.index_route, v.position, v.vitesse, v.distance_totale) == (0, 0.0, 0.0, 0.0)
    assert v.vitesse_max == 110 and v.temps_depart == 30
    assert not v.arrive and v.temps_parcours is None


@pytest.mark.parametrize("vitesse_kmh, delta_t, attendu_m", [
    (36, 60, 600), (72, 30, 600), (3.6, 10, 10),
])
def test_avancer_convertit_kmh_en_metres(vitesse_kmh, delta_t, attendu_m):
    v = Vehicule("V1", ["A-B"], vitesse_max=200)
    v.avancer(delta_t, vitesse_kmh)
    assert v.position == pytest.approx(attendu_m)
    assert v.distance_totale == pytest.approx(attendu_m)


def test_avancer_cumule_la_distance():
    v = Vehicule("V1", ["A-B"])
    v.avancer(10, 36)
    v.avancer(10, 36)
    assert v.position == pytest.approx(200)


def test_temps_parcours():
    v = Vehicule("V1", ["A-B"], temps_depart=120)
    v.temps_arrivee = 420
    assert v.arrive and v.temps_parcours == 300


def test_nom_route_suivante():
    v = Vehicule("V1", ["A-B", "B-C"])
    assert v.nom_route_suivante() == "B-C"
    v.index_route = 1
    assert v.nom_route_suivante() is None


def test_changer_de_route():
    r1, r2 = Route("A-B", "A", "B", 1000, 50), Route("B-C", "B", "C", 1000, 50)
    v = Vehicule("V1", ["A-B", "B-C"])
    r1.ajouter_vehicule(v)
    v.changer_de_route(r2, depassement=30)
    assert v not in r1.vehicules and v in r2.vehicules
    assert v.position == 30 and v.index_route == 1 and v.route is r2


# ------------------------------------------------------------------- cas limites
def test_vitesse_plafonnee_par_vitesse_max():
    v = Vehicule("V1", ["A-B"], vitesse_max=50)
    v.avancer(60, 100)
    assert v.vitesse == 50


def test_avancer_vitesse_nulle():
    v = Vehicule("V1", ["A-B"])
    v.avancer(100, 0)
    assert v.position == 0 and v.vitesse == 0


def test_avancer_duree_nulle():
    v = Vehicule("V1", ["A-B"])
    v.avancer(0, 50)
    assert v.position == 0


def test_itineraire_un_seul_troncon():
    v = Vehicule("V1", ["A-B"])
    assert v.nom_route_suivante() is None


def test_itineraire_est_copie():
    original = ["A-B"]
    v = Vehicule("V1", original)
    original.append("B-C")
    assert v.itineraire == ["A-B"]


# ------------------------------------------------------------------ cas invalides
@pytest.mark.parametrize("vitesse_max", [0, -10])
def test_vitesse_max_non_positive_refusee(vitesse_max):
    with pytest.raises(ValueError):
        Vehicule("V1", ["A-B"], vitesse_max=vitesse_max)


def test_itineraire_vide_refuse():
    with pytest.raises(ValueError):
        Vehicule("V1", [])


def test_temps_depart_negatif_refuse():
    with pytest.raises(ValueError):
        Vehicule("V1", ["A-B"], temps_depart=-1)


def test_identifiant_vide_refuse():
    with pytest.raises(ValueError):
        Vehicule("", ["A-B"])


def test_vitesse_max_de_mauvais_type():
    with pytest.raises(TypeError):
        Vehicule("V1", ["A-B"], vitesse_max="rapide")


def test_avancer_duree_negative_refusee():
    v = Vehicule("V1", ["A-B"])
    with pytest.raises(ValueError):
        v.avancer(-5, 50)


def test_avancer_vitesse_autorisee_negative_refusee():
    v = Vehicule("V1", ["A-B"])
    with pytest.raises(ValueError):
        v.avancer(10, -20)


# --------------------------------------------------------------------- cohérence
@pytest.mark.parametrize("vitesse_max, autorisee", [(50, 100), (130, 20), (90, 90)])
def test_vitesse_jamais_superieure_aux_deux_limites(vitesse_max, autorisee):
    v = Vehicule("V1", ["A-B"], vitesse_max=vitesse_max)
    v.avancer(10, autorisee)
    assert v.vitesse == min(vitesse_max, autorisee)


def test_position_ne_decroit_jamais():
    v = Vehicule("V1", ["A-B"])
    precedent = 0
    for vit in (10, 0, 50, 5):
        v.avancer(10, vit)
        assert v.position >= precedent
        precedent = v.position
