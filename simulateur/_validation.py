"""Fonctions de validation internes partagées par les modules du package.

Elles centralisent les contrôles de type et de valeur pour que tous les modules
lèvent les mêmes exceptions (``TypeError`` pour un mauvais type, ``ValueError``
pour une valeur hors domaine).
"""
from numbers import Real


def verifier_nombre(nom, valeur, *, strictement_positif=False, positif_ou_nul=False):
    """Vérifie qu'une valeur est un nombre réel fini, éventuellement positif.

    Args:
        nom (str): Nom du paramètre, utilisé dans le message d'erreur.
        valeur: Valeur à contrôler.
        strictement_positif (bool): Exige ``valeur > 0``.
        positif_ou_nul (bool): Exige ``valeur >= 0``.

    Returns:
        float: La valeur convertie en ``float``.

    Raises:
        TypeError: Si ``valeur`` n'est pas un nombre réel (les booléens sont refusés).
        ValueError: Si ``valeur`` est infinie, NaN ou ne respecte pas le signe exigé.
    """
    if isinstance(valeur, bool) or not isinstance(valeur, Real):
        raise TypeError(f"{nom} doit être un nombre, reçu {type(valeur).__name__}")
    valeur = float(valeur)
    if valeur != valeur or valeur in (float("inf"), float("-inf")):
        raise ValueError(f"{nom} doit être un nombre fini")
    if strictement_positif and valeur <= 0:
        raise ValueError(f"{nom} doit être strictement positif, reçu {valeur}")
    if positif_ou_nul and valeur < 0:
        raise ValueError(f"{nom} doit être positif ou nul, reçu {valeur}")
    return valeur


def verifier_entier(nom, valeur, *, minimum=None):
    """Vérifie qu'une valeur est un entier (les booléens sont refusés).

    Args:
        nom (str): Nom du paramètre, utilisé dans le message d'erreur.
        valeur: Valeur à contrôler.
        minimum (int | None): Borne inférieure autorisée (incluse), ou ``None``.

    Returns:
        int: La valeur contrôlée.

    Raises:
        TypeError: Si ``valeur`` n'est pas un entier.
        ValueError: Si ``valeur`` est inférieure à ``minimum``.
    """
    if isinstance(valeur, bool) or not isinstance(valeur, int):
        raise TypeError(f"{nom} doit être un entier, reçu {type(valeur).__name__}")
    if minimum is not None and valeur < minimum:
        raise ValueError(f"{nom} doit être >= {minimum}, reçu {valeur}")
    return valeur


def verifier_texte(nom, valeur):
    """Vérifie qu'une valeur est une chaîne non vide.

    Args:
        nom (str): Nom du paramètre, utilisé dans le message d'erreur.
        valeur: Valeur à contrôler.

    Returns:
        str: La valeur contrôlée.

    Raises:
        TypeError: Si ``valeur`` n'est pas une chaîne.
        ValueError: Si la chaîne est vide ou ne contient que des espaces.
    """
    if not isinstance(valeur, str):
        raise TypeError(f"{nom} doit être une chaîne, reçu {type(valeur).__name__}")
    if not valeur.strip():
        raise ValueError(f"{nom} ne peut pas être vide")
    return valeur
