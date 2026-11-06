"""Package ``simulateur`` : simulation du trafic de véhicules sur un réseau routier.

Modules :
    * :mod:`simulateur.vehicule`   -- la classe :class:`Vehicule` ;
    * :mod:`simulateur.route`      -- la classe :class:`Route` ;
    * :mod:`simulateur.simulation` -- :class:`ReseauRoutier`, :class:`Analyseur`, :class:`Simulation`.
"""
from simulateur.vehicule import Vehicule
from simulateur.route import Route
from simulateur.simulation import ReseauRoutier, Analyseur, Simulation

__all__ = ["Vehicule", "Route", "ReseauRoutier", "Analyseur", "Simulation"]
__version__ = "1.0.0"
