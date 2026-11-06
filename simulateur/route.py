"""Modèle d'une route : tronçon à sens unique entre deux intersections.

La vitesse praticable sur une route diminue avec son occupation (modèle linéaire
de type Greenshields).
"""
from simulateur._validation import verifier_entier, verifier_nombre, verifier_texte


class Route:
    """Tronçon routier orienté qui contient des véhicules et limite leur vitesse.

    Responsabilités : calculer sa capacité, son taux d'occupation et la vitesse
    autorisée ; accueillir et retirer des véhicules ; faire avancer les véhicules
    présents en signalant ceux qui atteignent la fin du tronçon.

    Attributes:
        ESPACE_PAR_VEHICULE (float): Place moyenne par véhicule, distance de sécurité
            comprise (m).
        FACTEUR_VITESSE_MIN (float): Fraction minimale de la limite conservée en cas
            d'embouteillage total.
        nom (str): Nom de la route (ex. ``"A-B"``).
        origine (str): Intersection de départ.
        destination (str): Intersection d'arrivée.
        longueur (float): Longueur en mètres.
        limite_vitesse (float): Vitesse limite en km/h.
        nb_voies (int): Nombre de voies.
        vehicules (list[Vehicule]): Véhicules actuellement sur la route.
    """

    ESPACE_PAR_VEHICULE = 25.0
    FACTEUR_VITESSE_MIN = 0.10

    def __init__(self, nom, origine, destination, longueur, limite_vitesse, nb_voies=1):
        """Crée une route.

        Args:
            nom (str): Nom non vide.
            origine (str): Intersection de départ (non vide).
            destination (str): Intersection d'arrivée (non vide, différente de ``origine``).
            longueur (float): Longueur en mètres, strictement positive.
            limite_vitesse (float): Limite en km/h, strictement positive.
            nb_voies (int): Nombre de voies, entier >= 1.

        Raises:
            TypeError: Si un paramètre n'a pas le bon type.
            ValueError: Si une valeur est hors domaine ou si ``origine == destination``.
        """
        self.nom = verifier_texte("nom", nom)
        self.origine = verifier_texte("origine", origine)
        self.destination = verifier_texte("destination", destination)
        if self.origine == self.destination:
            raise ValueError("l'origine et la destination doivent être différentes")
        self.longueur = verifier_nombre("longueur", longueur, strictement_positif=True)
        self.limite_vitesse = verifier_nombre("limite_vitesse", limite_vitesse, strictement_positif=True)
        self.nb_voies = verifier_entier("nb_voies", nb_voies, minimum=1)
        self.vehicules = []

    # ------------------------------------------------------------ propriétés
    @property
    def capacite(self):
        """float: Nombre de véhicules que la route contient confortablement (au moins 1)."""
        return max(1.0, self.longueur * self.nb_voies / self.ESPACE_PAR_VEHICULE)

    @property
    def taux_occupation(self):
        """float: Rapport véhicules / capacité (0 = vide, 1 = pleine, > 1 = surcharge)."""
        return len(self.vehicules) / self.capacite

    def vitesse_autorisee(self):
        """Calcule la vitesse praticable vu l'encombrement.

        Formule : ``limite * max(FACTEUR_VITESSE_MIN, 1 - occupation)``.

        Returns:
            float: Vitesse autorisée en km/h, comprise entre 10 % de la limite et la limite.
        """
        facteur = max(self.FACTEUR_VITESSE_MIN, 1.0 - self.taux_occupation)
        return self.limite_vitesse * facteur

    def vitesse_moyenne(self):
        """Calcule la vitesse moyenne réelle des véhicules présents.

        Returns:
            float | None: Moyenne en km/h, ``None`` si la route est vide.
        """
        if not self.vehicules:
            return None
        return sum(v.vitesse for v in self.vehicules) / len(self.vehicules)

    # --------------------------------------------------------------- actions
    def ajouter_vehicule(self, vehicule):
        """Place un véhicule au début de la route.

        Args:
            vehicule (Vehicule): Véhicule à accueillir (position remise à 0).
        """
        vehicule.route = self
        vehicule.position = 0.0
        self.vehicules.append(vehicule)

    def retirer_vehicule(self, vehicule):
        """Retire un véhicule de la route ; sans effet s'il n'y est pas.

        Args:
            vehicule (Vehicule): Véhicule à retirer.
        """
        if vehicule in self.vehicules:
            self.vehicules.remove(vehicule)
        vehicule.route = None

    def mettre_a_jour_vehicules(self, delta_t):
        """Fait avancer tous les véhicules de la route pendant ``delta_t`` secondes.

        La vitesse autorisée est calculée une seule fois, avec la charge du début de pas.

        Args:
            delta_t (float): Durée du pas en secondes, positive ou nulle.

        Returns:
            list[Vehicule]: Véhicules ayant atteint ou dépassé la fin de la route
            (le réseau décide ensuite de leur sort).

        Raises:
            TypeError: Si ``delta_t`` n'est pas un nombre.
            ValueError: Si ``delta_t`` est négatif.
        """
        delta_t = verifier_nombre("delta_t", delta_t, positif_ou_nul=True)
        vitesse = self.vitesse_autorisee()
        arrives = []
        for v in list(self.vehicules):
            v.avancer(delta_t, vitesse)
            if v.position >= self.longueur:
                arrives.append(v)
        return arrives

    def __repr__(self):
        return (f"Route({self.nom}: {self.origine}->{self.destination}, {self.longueur:.0f} m, "
                f"{self.limite_vitesse:.0f} km/h, {len(self.vehicules)} veh.)")
