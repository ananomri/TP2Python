"""Réseau routier, analyse statistique et boucle de simulation.

Ce module réunit trois classes :

* :class:`ReseauRoutier` -- le réseau vu comme un graphe orienté (intersections = nœuds,
  routes = arêtes), avec calcul d'itinéraires (Dijkstra) et déplacement des véhicules ;
* :class:`Analyseur` -- enregistre l'état du réseau à chaque tour et calcule des statistiques ;
* :class:`Simulation` -- charge une configuration JSON et exécute la boucle de simulation.
"""
import heapq
import json
import random

from simulateur._validation import verifier_entier, verifier_nombre, verifier_texte
from simulateur.route import Route
from simulateur.vehicule import Vehicule


class ReseauRoutier:
    """Graphe orienté de routes qui contient les véhicules et les fait avancer.

    Responsabilités : stocker intersections et routes, valider leur ajout, calculer
    le trajet le plus rapide, créer des véhicules et gérer leur passage d'une route
    à l'autre jusqu'à leur arrivée.

    Attributes:
        intersections (dict[str, tuple[float, float]]): Nom -> coordonnées ``(x, y)``.
        routes (dict[str, Route]): Nom de route -> objet :class:`Route`.
        vehicules_arrives (list[Vehicule]): Véhicules ayant terminé leur trajet.
    """

    TENTATIVES_ALEATOIRES = 50   # essais aléatoires avant la recherche exhaustive d'un trajet

    def __init__(self):
        """Crée un réseau vide."""
        self.intersections = {}
        self.routes = {}
        self.vehicules_arrives = []
        self._compteur_id = 0

    # ---------------------------------------------------------- construction
    def ajouter_intersection(self, nom, x, y):
        """Ajoute une intersection.

        Args:
            nom (str): Nom unique et non vide.
            x (float): Abscisse (pour la carte).
            y (float): Ordonnée (pour la carte).

        Raises:
            TypeError: Si un argument n'a pas le bon type.
            ValueError: Si le nom est vide ou déjà utilisé.
        """
        verifier_texte("nom", nom)
        if nom in self.intersections:
            raise ValueError(f"intersection déjà existante : {nom}")
        self.intersections[nom] = (verifier_nombre("x", x), verifier_nombre("y", y))

    def ajouter_route(self, route):
        """Ajoute une route entre deux intersections existantes.

        Args:
            route (Route): Route à ajouter.

        Raises:
            ValueError: Si une extrémité est inconnue ou si le nom de route existe déjà.
        """
        if route.origine not in self.intersections or route.destination not in self.intersections:
            raise ValueError(f"Route {route.nom}: intersection inconnue")
        if route.nom in self.routes:
            raise ValueError(f"route déjà existante : {route.nom}")
        self.routes[route.nom] = route

    @classmethod
    def depuis_config(cls, config):
        """Construit un réseau à partir d'un dictionnaire de configuration.

        Chaque route est créée dans les deux sens, sauf si ``"double_sens": false``.

        Args:
            config (dict): Dictionnaire avec les clés ``"intersections"`` et ``"routes"``.

        Returns:
            ReseauRoutier: Le réseau construit.

        Raises:
            KeyError: Si une clé obligatoire est absente.
            ValueError: Si une intersection ou une route est invalide.
        """
        reseau = cls()
        for nom, coord in config["intersections"].items():
            reseau.ajouter_intersection(nom, coord["x"], coord["y"])
        for r in config["routes"]:
            args = dict(longueur=r["longueur"], limite_vitesse=r["limite_vitesse"],
                        nb_voies=r.get("nb_voies", 1))
            a, b = r["de"], r["vers"]
            reseau.ajouter_route(Route(f"{a}-{b}", a, b, **args))
            if r.get("double_sens", True):
                reseau.ajouter_route(Route(f"{b}-{a}", b, a, **args))
        return reseau

    # ----------------------------------------------------------- itinéraires
    def plus_court_chemin(self, depart, arrivee):
        """Cherche le trajet le plus rapide à vide (algorithme de Dijkstra).

        Le coût d'une route est son temps de parcours théorique
        (longueur / limite de vitesse), et non sa longueur.

        Args:
            depart (str): Intersection de départ.
            arrivee (str): Intersection d'arrivée.

        Returns:
            list[str] | None: Noms des routes à emprunter (liste vide si
            ``depart == arrivee``), ou ``None`` si l'arrivée est inaccessible.

        Raises:
            ValueError: Si ``depart`` ou ``arrivee`` n'est pas une intersection du réseau.
        """
        for nom in (depart, arrivee):
            if nom not in self.intersections:
                raise ValueError(f"intersection inconnue : {nom}")
        dist = {depart: 0.0}
        precedent = {}
        file = [(0.0, depart)]
        while file:
            d, noeud = heapq.heappop(file)
            if noeud == arrivee:
                break
            if d > dist.get(noeud, float("inf")):
                continue
            for route in self.routes.values():
                if route.origine != noeud:
                    continue
                nd = d + route.longueur / (route.limite_vitesse / 3.6)
                if nd < dist.get(route.destination, float("inf")):
                    dist[route.destination] = nd
                    precedent[route.destination] = route
                    heapq.heappush(file, (nd, route.destination))
        if arrivee not in dist:
            return None
        chemin, noeud = [], arrivee
        while noeud != depart:
            route = precedent[noeud]
            chemin.append(route.nom)
            noeud = route.origine
        return list(reversed(chemin))

    # ------------------------------------------------------------- véhicules
    def _tirer_trajet(self, rng):
        """Choisit un couple (départ, arrivée) reliés par un chemin.

        Tente d'abord des tirages aléatoires, puis parcourt tous les couples
        (ordre mélangé) pour garantir la terminaison.

        Args:
            rng (random.Random): Générateur pseudo-aléatoire.

        Returns:
            list[str]: Itinéraire non vide.

        Raises:
            ValueError: Si moins de deux intersections existent ou si aucun trajet n'est possible.
        """
        noms = list(self.intersections)
        if len(noms) < 2:
            raise ValueError("il faut au moins deux intersections pour créer un véhicule")
        for _ in range(self.TENTATIVES_ALEATOIRES):
            depart, arrivee = rng.sample(noms, 2)
            itineraire = self.plus_court_chemin(depart, arrivee)
            if itineraire:
                return itineraire
        couples = [(a, b) for a in noms for b in noms if a != b]
        rng.shuffle(couples)
        for depart, arrivee in couples:
            itineraire = self.plus_court_chemin(depart, arrivee)
            if itineraire:
                return itineraire
        raise ValueError("aucun trajet possible dans ce réseau")

    def generer_vehicule(self, temps, rng, vitesse_max_plage=(90, 130)):
        """Crée un véhicule au trajet aléatoire et le place sur sa première route.

        Args:
            temps (float): Instant de création (s).
            rng (random.Random): Générateur pseudo-aléatoire.
            vitesse_max_plage (tuple[float, float]): Bornes ``(min, max)`` de la vitesse
                maximale du conducteur (km/h).

        Returns:
            Vehicule: Le véhicule créé.

        Raises:
            ValueError: Si le réseau a moins de deux intersections, si aucun trajet n'est
                possible ou si la plage de vitesse est invalide.
        """
        _verifier_plage_vitesse(vitesse_max_plage)
        itineraire = self._tirer_trajet(rng)
        self._compteur_id += 1
        v = Vehicule(f"V{self._compteur_id:04d}", itineraire,
                     vitesse_max=rng.uniform(*vitesse_max_plage), temps_depart=temps)
        self.routes[itineraire[0]].ajouter_vehicule(v)
        return v

    # ------------------------------------------------------------ simulation
    def mettre_a_jour(self, delta_t, temps):
        """Exécute un pas de simulation pour tout le réseau.

        Chaque route fait avancer ses véhicules ; ceux qui atteignent la fin passent
        à la route suivante (en conservant leur dépassement, même s'il couvre plusieurs
        routes courtes) ou sont déclarés arrivés.

        Args:
            delta_t (float): Durée du pas en secondes.
            temps (float): Temps simulé à la fin du pas (pour dater les arrivées).

        Raises:
            ValueError: Si ``delta_t`` est négatif.
        """
        sortants = []
        for route in self.routes.values():
            for v in route.mettre_a_jour_vehicules(delta_t):
                sortants.append((route, v))

        for route, v in sortants:
            depassement = v.position - route.longueur
            while True:
                suivante = v.nom_route_suivante()
                if suivante is None:
                    route.retirer_vehicule(v)
                    v.temps_arrivee = temps
                    v.vitesse = 0.0
                    self.vehicules_arrives.append(v)
                    break
                nouvelle = self.routes[suivante]
                v.changer_de_route(nouvelle, depassement)
                if v.position < nouvelle.longueur:
                    break
                depassement = v.position - nouvelle.longueur
                route = nouvelle

    # ----------------------------------------------------------------- état
    def vehicules_en_route(self):
        """Liste les véhicules actuellement sur le réseau.

        Returns:
            list[Vehicule]: Véhicules présents sur au moins une route.
        """
        return [v for r in self.routes.values() for v in r.vehicules]


def _verifier_plage_vitesse(plage):
    """Valide une plage ``(min, max)`` de vitesses maximales.

    Args:
        plage (Sequence[float]): Deux nombres ``(min, max)``.

    Raises:
        ValueError: Si la plage n'a pas deux éléments, si ``min <= 0`` ou ``min > max``.
        TypeError: Si les bornes ne sont pas des nombres.
    """
    if len(plage) != 2:
        raise ValueError("la plage de vitesse doit contenir deux valeurs [min, max]")
    mini = verifier_nombre("vitesse min", plage[0], strictement_positif=True)
    maxi = verifier_nombre("vitesse max", plage[1], strictement_positif=True)
    if mini > maxi:
        raise ValueError("la plage de vitesse doit vérifier min <= max")


class Analyseur:
    """Enregistre l'état du réseau à chaque tour et calcule des statistiques.

    Attributes:
        SEUIL_CONGESTION (float): Occupation à partir de laquelle une route est congestionnée.
        historique (list[dict]): Un dictionnaire par tour (état du réseau à cet instant).
    """

    SEUIL_CONGESTION = 0.6

    def __init__(self):
        """Crée un analyseur avec un historique vide."""
        self.historique = []

    # --------------------------------------------------------- enregistrement
    def enregistrer(self, temps, reseau):
        """Ajoute à l'historique une « photo » du réseau.

        Args:
            temps (float): Temps simulé en secondes.
            reseau (ReseauRoutier): Réseau observé.
        """
        vehicules = reseau.vehicules_en_route()
        vitesse_moy = (sum(v.vitesse for v in vehicules) / len(vehicules)) if vehicules else 0.0
        self.historique.append({
            "temps_min": temps / 60.0,
            "vehicules_en_route": len(vehicules),
            "vehicules_arrives": len(reseau.vehicules_arrives),
            "vitesse_moyenne": vitesse_moy,
            "routes": {
                nom: {"nb_vehicules": len(r.vehicules),
                      "occupation": r.taux_occupation,
                      "vitesse_moyenne": r.vitesse_moyenne()}
                for nom, r in reseau.routes.items()
            },
        })

    # ------------------------------------------------------------ statistiques
    def vitesse_moyenne_globale(self):
        """Moyenne des vitesses moyennes sur les tours où des véhicules circulaient.

        Returns:
            float: Vitesse en km/h, 0.0 si aucun tour exploitable.
        """
        valeurs = [h["vitesse_moyenne"] for h in self.historique if h["vehicules_en_route"] > 0]
        return sum(valeurs) / len(valeurs) if valeurs else 0.0

    def occupation_moyenne_par_route(self):
        """Calcule l'occupation moyenne de chaque route sur toute la simulation.

        Returns:
            dict[str, float]: Nom de route -> occupation moyenne (vide si pas d'historique).
        """
        noms = self.historique[0]["routes"].keys() if self.historique else []
        n = len(self.historique)
        return {nom: sum(h["routes"][nom]["occupation"] for h in self.historique) / n for nom in noms}

    def zones_congestion(self, seuil=None):
        """Liste les routes dont l'occupation a atteint le seuil.

        Args:
            seuil (float | None): Seuil d'occupation ; ``SEUIL_CONGESTION`` si ``None``.

        Returns:
            list[dict]: Dictionnaires ``route``, ``pic_occupation`` et
            ``tours_congestionnes``, triés du pire au moins pire.
        """
        seuil = self.SEUIL_CONGESTION if seuil is None else seuil
        zones = []
        for nom in (self.historique[0]["routes"] if self.historique else []):
            pic = max(h["routes"][nom]["occupation"] for h in self.historique)
            tours = sum(1 for h in self.historique if h["routes"][nom]["occupation"] >= seuil)
            if tours:
                zones.append({"route": nom, "pic_occupation": pic, "tours_congestionnes": tours})
        return sorted(zones, key=lambda z: z["pic_occupation"], reverse=True)

    def temps_parcours(self, reseau):
        """Calcule des statistiques sur les trajets terminés.

        Args:
            reseau (ReseauRoutier): Réseau contenant ``vehicules_arrives``.

        Returns:
            dict: ``nb_trajets`` et durées ``moyen``, ``min``, ``max`` en minutes
            (0.0 si aucun trajet terminé).
        """
        durees = [v.temps_parcours / 60.0 for v in reseau.vehicules_arrives]
        if not durees:
            return {"nb_trajets": 0, "moyen": 0.0, "min": 0.0, "max": 0.0}
        return {"nb_trajets": len(durees), "moyen": sum(durees) / len(durees),
                "min": min(durees), "max": max(durees)}

    def resume(self, reseau):
        """Synthétise la simulation dans un dictionnaire (affichage ou export JSON).

        Args:
            reseau (ReseauRoutier): Réseau simulé.

        Returns:
            dict: ``nb_tours``, ``vitesse_moyenne_globale_kmh``, ``temps_parcours_min``,
            ``vehicules_encore_en_route`` et ``zones_congestion``.
        """
        return {
            "nb_tours": len(self.historique),
            "vitesse_moyenne_globale_kmh": round(self.vitesse_moyenne_globale(), 2),
            "temps_parcours_min": {k: round(v, 2) for k, v in self.temps_parcours(reseau).items()},
            "vehicules_encore_en_route": len(reseau.vehicules_en_route()),
            "zones_congestion": [{**z, "pic_occupation": round(z["pic_occupation"], 2)}
                                 for z in self.zones_congestion()],
        }


class Simulation:
    """Chef d'orchestre : charge la configuration et exécute la boucle de simulation.

    Attributes:
        config (dict): Configuration lue dans le fichier JSON.
        reseau (ReseauRoutier): Réseau construit à partir de la configuration.
        analyseur (Analyseur): Collecte les statistiques de chaque tour.
        rng (random.Random): Générateur initialisé avec la graine de la configuration.
        temps (float): Temps simulé écoulé, en secondes.
    """

    def __init__(self, fichier_config):
        """Charge et valide la configuration, puis construit le réseau.

        Args:
            fichier_config (str): Chemin d'un fichier JSON de configuration.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            json.JSONDecodeError: Si le fichier n'est pas du JSON valide.
            ValueError: Si le débit ou la plage de vitesse sont invalides.
        """
        with open(fichier_config, encoding="utf-8") as f:
            self.config = json.load(f)
        verifier_nombre("vehicules_par_minute", self.config.get("vehicules_par_minute", 5),
                        positif_ou_nul=True)
        _verifier_plage_vitesse(self.config.get("vitesse_max_vehicule", [90, 130]))
        self.reseau = ReseauRoutier.depuis_config(self.config)
        self.analyseur = Analyseur()
        self.rng = random.Random(self.config.get("graine"))
        self.temps = 0.0
        self._reste_generation = 0.0

    def _generer_trafic(self, delta_t):
        """Crée les nouveaux véhicules d'un pas selon le débit configuré.

        La partie fractionnaire de véhicules à créer est reportée au pas suivant.

        Args:
            delta_t (float): Durée du pas en secondes.
        """
        taux = self.config.get("vehicules_par_minute", 5)
        self._reste_generation += taux * delta_t / 60.0
        n = int(self._reste_generation)
        self._reste_generation -= n
        plage = tuple(self.config.get("vitesse_max_vehicule", [90, 130]))
        for _ in range(n):
            self.reseau.generer_vehicule(self.temps, self.rng, plage)

    def lancer_simulation(self, n_tours, delta_t, afficher_tous_les=0, callback=None):
        """Exécute ``n_tours`` pas de ``delta_t`` secondes.

        Args:
            n_tours (int): Nombre de tours, entier >= 0.
            delta_t (float): Durée d'un tour en secondes, strictement positive.
            afficher_tous_les (int): Si > 0, appelle ``callback`` tous les N tours.
            callback (Callable[[float, Analyseur], None] | None): Fonction appelée avec
                le temps simulé (minutes) et l'analyseur.

        Returns:
            Analyseur: L'analyseur contenant l'historique complet.

        Raises:
            TypeError: Si ``n_tours`` n'est pas un entier ou ``delta_t`` pas un nombre.
            ValueError: Si ``n_tours`` est négatif ou ``delta_t`` n'est pas strictement positif.
        """
        verifier_entier("n_tours", n_tours, minimum=0)
        delta_t = verifier_nombre("delta_t", delta_t, strictement_positif=True)
        for tour in range(1, n_tours + 1):
            self._generer_trafic(delta_t)
            self.temps += delta_t
            self.reseau.mettre_a_jour(delta_t, self.temps)
            self.analyseur.enregistrer(self.temps, self.reseau)
            if callback and afficher_tous_les and tour % afficher_tous_les == 0:
                callback(self.temps / 60.0, self.analyseur)
        return self.analyseur
