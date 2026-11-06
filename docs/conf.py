"""Configuration de Sphinx pour la documentation du package ``simulateur``."""
import os
import sys

# Permet à autodoc d'importer le package depuis la racine du projet
sys.path.insert(0, os.path.abspath(".."))

import simulateur  # noqa: E402

project = "simulateur"
author = "[Prénom NOM]"
copyright = "2026, " + author
release = simulateur.__version__
language = "fr"

extensions = [
    "sphinx.ext.autodoc",      # génère la doc à partir des docstrings
    "sphinx.ext.napoleon",     # comprend le style Google (Args / Returns / Raises)
    "sphinx.ext.viewcode",     # liens « [source] » vers le code
]

# --- autodoc --------------------------------------------------------------
autodoc_member_order = "bysource"       # ordre du fichier plutôt qu'alphabétique
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}

# --- napoleon (docstrings Google) ----------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_ivar = True                # « Attributes: » rendu en variables d'instance

# --- HTML -----------------------------------------------------------------
html_theme = "alabaster"                # thème fourni avec Sphinx
html_static_path = ["_static"]
templates_path = []
exclude_patterns = ["_build"]
