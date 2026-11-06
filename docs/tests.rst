Tests
=====

La suite de tests utilise ``pytest`` (95 tests, un fichier par module).

.. code-block:: bash

   pytest -v                          # tous les tests
   pytest tests/test_vehicule.py -v   # un module
   pytest tests/test_route.py -v
   pytest tests/test_simulation.py -v

Chaque module est testé selon quatre axes : cas nominaux, cas limites,
cas invalides et cohérence avec les règles du simulateur.
