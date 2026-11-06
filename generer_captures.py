"""Génère des captures « terminal » nettes (PNG 220 dpi) pour le compte rendu.

Usage :   python generer_captures.py      (depuis la racine du projet)
Résultat : dossier captures/ -> à copier à côté de rapport.tex.
Aucune vraie capture d'écran n'est nécessaire : la sortie de chaque commande
est rendue dans une image de terminal (police monospace, fond sombre).
"""
import os
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RACINE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(RACINE, "captures")
os.makedirs(SORTIE, exist_ok=True)
PY = "python" if os.name == "nt" else "python3"


def lancer(commande):
    """Exécute `commande` à la racine du projet et renvoie stdout + stderr."""
    r = subprocess.run(commande, cwd=RACINE, shell=True, capture_output=True, text=True, encoding="utf-8")
    return (r.stdout + r.stderr).rstrip()


def capture(commande, texte, fichier, largeur=105, max_lignes=75):
    """Rend `texte` comme une fenêtre de terminal et l'enregistre dans captures/."""
    lignes = [f"$ {commande}", ""] + texte.splitlines()
    if len(lignes) > max_lignes:
        lignes = lignes[:max_lignes - 2] + ["  [...]", lignes[-1]]
    lignes = [l if len(l) <= largeur else l[:largeur - 3] + "..." for l in lignes]
    h = 0.205 * len(lignes) + 0.7
    fig = plt.figure(figsize=(11, h), facecolor="#1e1e1e")
    fig.text(0.02, 1 - 0.45 / h, "\n".join(lignes), family="DejaVu Sans Mono", fontsize=9.5,
             color="#d4d4d4", va="top", ha="left", linespacing=1.35)
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        fig.patches.append(plt.Circle((0.015 + i * 0.016, 1 - 0.18 / h), 0.006,
                                      transform=fig.transFigure, color=c))
    fig.savefig(os.path.join(SORTIE, fichier), dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("  ->", os.path.join("captures", fichier))


def arborescence():
    sortie = ["simulateur/"]
    for dossier, sous, fichiers in os.walk(RACINE):
        sous[:] = sorted(d for d in sous if d not in
                         ("__pycache__", ".pytest_cache", "captures", ".git", "simulateur.egg-info", ".venv", "rapport"))
        niveau = 0 if dossier == RACINE else os.path.relpath(dossier, RACINE).count(os.sep) + 1
        if dossier != RACINE:
            sortie.append("   " * (niveau - 1) + "|-- " + os.path.basename(dossier) + "/")
        for f in sorted(fichiers):
            if f.endswith((".pyc", ".png", ".zip")) or f == "generer_captures.py":
                continue
            sortie.append("   " * niveau + "|-- " + f)
    return "\n".join(sortie)


if __name__ == "__main__":
    print("Génération des captures...")
    capture("tree simulateur", arborescence(), "01_structure.png")
    c = f'{PY} -c "from simulateur import Route; help(Route.vitesse_autorisee)"'
    capture(c, lancer(c), "02_docstring_help.png")
    c = f'{PY} -c "import simulateur.route as m; print(m.__doc__)"'
    capture(c, lancer(c), "03_docstring_module.png")
    for nom, fichier in (("pytest -v", "04_pytest_complet.png"),
                         ("pytest tests/test_vehicule.py -v", "05_pytest_vehicule.png"),
                         ("pytest tests/test_route.py -v", "06_pytest_route.png"),
                         ("pytest tests/test_simulation.py -v", "07_pytest_simulation.png")):
        c = f"{PY} -m {nom}"
        capture(c, lancer(c), fichier, largeur=110)
    c = f"{PY} -m pytest -q"
    capture(c, lancer(c), "08_pytest_resume.png")
    c = f"{PY} exemples/exemple_simple.py"
    capture(c, lancer(c), "09_exemple.png")
    c = f'{PY} -c "from simulateur import Route; Route(\'A-B\',\'A\',\'B\',-100,50)"'
    capture(c, lancer(c), "10_erreur_validation.png")
    # ---- Sphinx : compilation + captures de la page HTML --------------------
    try:
        import sphinx  # noqa: F401
    except ImportError:
        print("  (Sphinx absent : pip install -e .[docs] puis relancer pour les captures 11 à 13)")
    else:
        c = f"{PY} -m sphinx -b html docs docs/_build/html"
        capture(c, lancer(c), "11_sphinx_build.png")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                nav = pw.chromium.launch()
                page = nav.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
                for page_html, fichier in (("index.html", "12_sphinx_index.png"), ("api.html", "13_sphinx_api.png")):
                    page.goto("file://" + os.path.join(RACINE, "docs", "_build", "html", page_html))
                    page.screenshot(path=os.path.join(SORTIE, fichier), full_page=False)
                    print("  ->", os.path.join("captures", fichier))
                nav.close()
        except Exception as e:                       # playwright non installé : capture manuelle
            print("  (captures HTML non générées :", type(e).__name__, ") -> ouvrir docs/_build/html/index.html")
    print("Terminé : voir le dossier captures/")
