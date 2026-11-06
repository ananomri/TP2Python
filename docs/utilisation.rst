Installation et utilisation
===========================

Installation
------------

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate          # Windows : .venv\Scripts\activate
   pip install -e ".[dev,docs]"

Exemple
-------

.. code-block:: python

   from simulateur import Simulation

   simu = Simulation("data/config_reseau.json")
   simu.lancer_simulation(n_tours=60, delta_t=60)      # 60 tours d'une minute

   resume = simu.analyseur.resume(simu.reseau)
   print(resume["vitesse_moyenne_globale_kmh"])
   print(resume["zones_congestion"])

Construire un réseau à la main
------------------------------

.. code-block:: python

   from simulateur import ReseauRoutier, Route

   reseau = ReseauRoutier()
   reseau.ajouter_intersection("A", 0, 0)
   reseau.ajouter_intersection("B", 1, 0)
   reseau.ajouter_route(Route("A-B", "A", "B", longueur=1000, limite_vitesse=50))
   print(reseau.plus_court_chemin("A", "B"))           # ['A-B']

Erreurs levées
--------------

.. list-table::
   :header-rows: 1
   :widths: 60 40

   * - Situation
     - Exception
   * - Paramètre du mauvais type (ex. ``longueur="a"``)
     - ``TypeError``
   * - Valeur hors domaine, intersection inconnue, doublon
     - ``ValueError``
   * - Fichier de configuration absent
     - ``FileNotFoundError``
