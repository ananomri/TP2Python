"""Exemple minimal : simuler une heure de trafic sur le réseau fourni."""
from simulateur import Simulation

simu = Simulation("data/config_reseau.json")
simu.lancer_simulation(n_tours=60, delta_t=60)          # 60 tours d'une minute

resume = simu.analyseur.resume(simu.reseau)
print("Vitesse moyenne globale :", resume["vitesse_moyenne_globale_kmh"], "km/h")
print("Trajets terminés        :", resume["temps_parcours_min"]["nb_trajets"])
print("Zones de congestion     :", [z["route"] for z in resume["zones_congestion"]])
