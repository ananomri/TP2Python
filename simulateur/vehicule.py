"""Modèle d'un véhicule circulant sur le réseau.

Un véhicule suit un itinéraire (liste ordonnée de noms de routes). À chaque
instant il se trouve sur une seule route, à une position exprimée en mètres
depuis le début de cette route.
"""
from simulateur._validation import verifier_nombre, verifier_texte


class Vehicule:
    """Véhicule qui suit un itinéraire et avance selon la vitesse autorisée.

    Responsabilités : mémoriser son itinéraire, sa position, sa vitesse et sa
    distance parcourue ; avancer pendant un pas de temps ; passer d'une route
    à la suivante ; fournir son temps de parcours une fois arrivé.

    Attributes:
        identifiant (str): Identifiant unique (ex. ``"V0001"``).
        itineraire (list[str]): Noms des routes à parcourir, dans l'ordre.
        index_route (int): Indice de la route courante dans ``itineraire``.
        vitesse_max (float): Vitesse maximale voulue par le conducteur (km/h).
        route (Route | None): Route actuelle, ``None`` hors réseau.
        position (float): Mètres parcourus depuis le début de la route courante.
        vitesse (float): Vitesse réelle à l'instant courant (km/h).
        distance_totale (float): Distance parcourue depuis le départ (m).
        temps_depart (float): Instant de départ (s, temps simulé).
        temps_arrivee (float | None): Instant d'arrivée (s), ``None`` tant qu'en route.
    """

    def __init__(self, identifiant, itineraire, vitesse_max=130.0, temps_depart=0.0):
        """Crée un véhicule.

        Args:
            identifiant (str): Identifiant non vide.
            itineraire (list[str]): Noms de routes, au moins un élément.
            vitesse_max (float): Vitesse maximale souhaitée en km/h, strictement positive.
            temps_depart (float): Instant de départ en secondes, positif ou nul.

        Raises:
            TypeError: Si un paramètre n'a pas le bon type.
            ValueError: Si l'itinéraire est vide, si ``vitesse_max`` n'est pas
                strictement positive ou si ``temps_depart`` est négatif.
        """
        self.identifiant = verifier_texte("identifiant", identifiant)
        itineraire = list(itineraire)
        if not itineraire:
            raise ValueError("l'itinéraire ne peut pas être vide")
        self.itineraire = itineraire
        self.index_route = 0
        self.vitesse_max = verifier_nombre("vitesse_max", vitesse_max, strictement_positif=True)

        self.route = None
        self.position = 0.0
        self.vitesse = 0.0

        self.distance_totale = 0.0
        self.temps_depart = verifier_nombre("temps_depart", temps_depart, positif_ou_nul=True)
        self.temps_arrivee = None

    # ------------------------------------------------------------------ état
    @property
    def arrive(self):
        """bool: ``True`` si le véhicule a terminé son trajet."""
        return self.temps_arrivee is not None

    @property
    def temps_parcours(self):
        """float | None: Durée du trajet en secondes, ``None`` tant que non arrivé."""
        if self.temps_arrivee is None:
            return None
        return self.temps_arrivee - self.temps_depart

    def nom_route_suivante(self):
        """Donne la prochaine route de l'itinéraire.

        Returns:
            str | None: Nom de la route suivante, ``None`` si la route courante est la dernière.
        """
        if self.index_route + 1 < len(self.itineraire):
            return self.itineraire[self.index_route + 1]
        return None

    # ------------------------------------------------------------- mouvement
    def avancer(self, delta_t, vitesse_autorisee):
        """Fait avancer le véhicule pendant ``delta_t`` secondes.

        La vitesse réelle est ``min(vitesse_max, vitesse_autorisee)``.

        Args:
            delta_t (float): Durée du pas en secondes, positive ou nulle.
            vitesse_autorisee (float): Vitesse permise par la route (km/h), positive ou nulle.

        Raises:
            TypeError: Si un argument n'est pas un nombre.
            ValueError: Si un argument est négatif.
        """
        delta_t = verifier_nombre("delta_t", delta_t, positif_ou_nul=True)
        vitesse_autorisee = verifier_nombre("vitesse_autorisee", vitesse_autorisee, positif_ou_nul=True)
        self.vitesse = min(self.vitesse_max, vitesse_autorisee)
        distance = (self.vitesse / 3.6) * delta_t        # km/h -> m/s
        self.position += distance
        self.distance_totale += distance

    def changer_de_route(self, nouvelle_route, depassement=0.0):
        """Quitte la route actuelle et entre sur ``nouvelle_route``.

        Args:
            nouvelle_route (Route): Route à rejoindre.
            depassement (float): Mètres déjà parcourus au-delà de la fin de l'ancienne
                route pendant le pas courant ; ils sont reportés sur la nouvelle route.
        """
        if self.route is not None:
            self.route.retirer_vehicule(self)
        self.index_route += 1
        nouvelle_route.ajouter_vehicule(self)
        self.position = depassement

    def __repr__(self):
        nom = self.route.nom if self.route else None
        return (f"Vehicule({self.identifiant}, route={nom}, pos={self.position:.0f} m, "
                f"v={self.vitesse:.0f} km/h)")
