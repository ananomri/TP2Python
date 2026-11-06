"""Tests unitaires du module simulateur.route."""
import pytest

from simulateur.route import Route
from simulateur.vehicule import Vehicule


def remplir(route, n):
    for i in range(n):
        route.ajouter_vehicule(Vehicule(f"V{i}", [route.nom]))


# ------------------------------------------------------------------ cas nominaux
def test_creation_nominale():
    r = Route("A-B", "A", "B", longueur=1000, limite_vitesse=50, nb_voies=2)
    assert (r.nom, r.origine, r.destination) == ("A-B", "A", "B")
    assert (r.longueur, r.limite_vitesse, r.nb_voies) == (1000.0, 50.0, 2)
    assert r.vehicules == []


def test_capacite_et_occupation():
    r = Route("A-B", "A", "B", 1000, 50)           # capacité = 1000 / 25 = 40
    assert r.capacite == pytest.approx(40)
    remplir(r, 10)
    assert r.taux_occupation == pytest.approx(0.25)


def test_ajouter_et_retirer_vehicule():
    r = Route("A-B", "A", "B", 1000, 50)
    v = Vehicule("V1", ["A-B"])
    r.ajouter_vehicule(v)
    assert v in r.vehicules and v.route is r and v.position == 0
    r.retirer_vehicule(v)
    assert v not in r.vehicules and v.route is None


def test_mettre_a_jour_renvoie_les_vehicules_arrives_au_bout():
    r = Route("A-B", "A", "B", 1000, 36)           # ~10 m/s
    v = Vehicule("V1", ["A-B"], vitesse_max=130)
    r.ajouter_vehicule(v)
    assert r.mettre_a_jour_vehicules(50) == []
    assert r.mettre_a_jour_vehicules(50) == []
    assert r.mettre_a_jour_vehicules(50) == [v]


# ------------------------------------------------------------------- cas limites
@pytest.mark.parametrize("nb_veh, attendue", [
    (0, 50.0), (10, 37.5), (20, 25.0), (40, 5.0), (80, 5.0),
])
def test_vitesse_selon_occupation(nb_veh, attendue):
    r = Route("A-B", "A", "B", 1000, 50)
    remplir(r, nb_veh)
    assert r.vitesse_autorisee() == pytest.approx(attendue)


def test_capacite_minimale_de_un():
    assert Route("A-B", "A", "B", longueur=5, limite_vitesse=50).capacite == 1.0


def test_capacite_proportionnelle_aux_voies():
    r1 = Route("A-B", "A", "B", 1000, 50, nb_voies=1)
    r2 = Route("A-B", "A", "B", 1000, 50, nb_voies=2)
    assert r2.capacite == pytest.approx(2 * r1.capacite)


def test_vitesse_moyenne_route_vide():
    assert Route("A-B", "A", "B", 1000, 50).vitesse_moyenne() is None


def test_retirer_vehicule_absent_sans_erreur():
    Route("A-B", "A", "B", 1000, 50).retirer_vehicule(Vehicule("V1", ["A-B"]))


def test_surcharge_occupation_superieure_a_un():
    r = Route("A-B", "A", "B", 1000, 50)
    remplir(r, 60)
    assert r.taux_occupation == pytest.approx(1.5)


# ------------------------------------------------------------------ cas invalides
@pytest.mark.parametrize("longueur", [0, -100])
def test_longueur_non_positive_refusee(longueur):
    with pytest.raises(ValueError):
        Route("A-B", "A", "B", longueur, 50)


@pytest.mark.parametrize("limite", [0, -50])
def test_limite_vitesse_non_positive_refusee(limite):
    with pytest.raises(ValueError):
        Route("A-B", "A", "B", 1000, limite)


@pytest.mark.parametrize("voies", [0, -1])
def test_nb_voies_invalide_refuse(voies):
    with pytest.raises(ValueError):
        Route("A-B", "A", "B", 1000, 50, nb_voies=voies)


def test_nb_voies_non_entier_refuse():
    with pytest.raises(TypeError):
        Route("A-B", "A", "B", 1000, 50, nb_voies=1.5)


def test_origine_egale_destination_refusee():
    with pytest.raises(ValueError):
        Route("A-A", "A", "A", 1000, 50)


def test_nom_vide_refuse():
    with pytest.raises(ValueError):
        Route("", "A", "B", 1000, 50)


def test_longueur_de_mauvais_type():
    with pytest.raises(TypeError):
        Route("A-B", "A", "B", "longue", 50)


def test_mettre_a_jour_duree_negative_refusee():
    r = Route("A-B", "A", "B", 1000, 50)
    remplir(r, 1)
    with pytest.raises(ValueError):
        r.mettre_a_jour_vehicules(-1)


# --------------------------------------------------------------------- cohérence
def test_vitesse_decroit_avec_le_nombre_de_vehicules():
    r = Route("A-B", "A", "B", 1000, 50)
    vitesses = []
    for _ in range(6):
        vitesses.append(r.vitesse_autorisee())
        remplir(r, 8)
    assert vitesses == sorted(vitesses, reverse=True)


def test_vitesse_toujours_entre_plancher_et_limite():
    r = Route("A-B", "A", "B", 1000, 50)
    for n in (0, 5, 40, 200):
        r2 = Route("A-B", "A", "B", 1000, 50)
        remplir(r2, n)
        assert 0.1 * 50 <= r2.vitesse_autorisee() <= 50


def test_vitesse_moyenne_des_vehicules_presents():
    r = Route("A-B", "A", "B", 1000, 50)
    for vit in (20, 40):
        v = Vehicule("V", ["A-B"])
        v.vitesse = vit
        r.ajouter_vehicule(v)
    assert r.vitesse_moyenne() == pytest.approx(30)
