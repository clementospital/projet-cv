"""Génère index.html, cv.pdf et README.md à partir de cv.yaml.

Usage : python src/build.py
"""

import copy
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

RACINE = Path(__file__).resolve().parent.parent
CV_YAML = RACINE / "cv.yaml"
TEMPLATES_DIR = RACINE / "templates"
STATIC_DIR = RACINE / "static"
DIST_DIR = RACINE / "dist"
README_MD = RACINE / "README.md"

MOIS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}

# Pages du site, dans l'ordre de la nav. La nav elle-même est générée une seule
# fois dans base.html.j2 à partir de cette liste (pas de duplication par page).
PAGES = [
    {"id": "accueil", "template": "accueil.html.j2", "fichier": "index.html", "libelle": "Accueil"},
    {"id": "parcours", "template": "parcours.html.j2", "fichier": "parcours.html", "libelle": "Parcours"},
    {"id": "competences", "template": "competences.html.j2", "fichier": "competences.html", "libelle": "Compétences"},
    {"id": "projets", "template": "projets.html.j2", "fichier": "projets.html", "libelle": "Projets"},
]


def charger_cv(chemin: Path) -> dict:
    if not chemin.exists():
        raise FileNotFoundError(f"fichier introuvable : {chemin}")
    with chemin.open("r", encoding="utf-8") as f:
        try:
            donnees = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML invalide dans {chemin} :\n{exc}") from exc
    if not isinstance(donnees, dict):
        raise ValueError(f"{chemin} doit contenir un mapping YAML au premier niveau")
    return donnees


def valider(donnees: dict) -> None:
    erreurs = []

    identite = donnees.get("identite") or {}
    for champ in ("nom", "email"):
        if not identite.get(champ):
            erreurs.append(f"identite.{champ} manquant")

    for i, exp in enumerate(donnees.get("experiences") or []):
        for champ in ("poste", "entreprise", "date_debut"):
            if not exp.get(champ):
                erreurs.append(f"experiences[{i}].{champ} manquant")

    for i, form in enumerate(donnees.get("formations") or []):
        for champ in ("diplome", "etablissement", "date_debut"):
            if not form.get(champ):
                erreurs.append(f"formations[{i}].{champ} manquant")

    if erreurs:
        detail = "\n".join(f"  - {e}" for e in erreurs)
        raise ValueError(f"Erreur(s) dans cv.yaml :\n{detail}")


def formater_date(valeur: str | None) -> str:
    if valeur is None:
        return "En cours"
    annee, mois = valeur.split("-")
    return f"{MOIS_FR[int(mois)]} {annee}"


def preparer_contexte(donnees: dict) -> dict:
    """Ajoute les dates formatées en français sans toucher aux valeurs brutes YYYY-MM."""
    contexte = copy.deepcopy(donnees)
    for exp in contexte.get("experiences") or []:
        exp["date_debut_affichage"] = formater_date(exp.get("date_debut"))
        exp["date_fin_affichage"] = formater_date(exp.get("date_fin"))
    for form in contexte.get("formations") or []:
        form["date_debut_affichage"] = formater_date(form.get("date_debut"))
        form["date_fin_affichage"] = formater_date(form.get("date_fin"))
    return contexte


def generer_pdf(html: str, sortie: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        navigateur = playwright.chromium.launch()
        page = navigateur.new_page()
        page.set_content(html, wait_until="networkidle")
        page.pdf(path=str(sortie), format="A4", print_background=True)
        navigateur.close()


def rendre_templates(contexte: dict) -> None:
    # Autoescape uniquement pour les templates HTML : le markdown ne doit pas être échappé.
    # trim_blocks/lstrip_blocks sont désactivés : dans readme.md.j2, les sauts de ligne entre
    # tags sont significatifs pour le markdown (les avaler casse la mise en forme).
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=lambda nom: bool(nom) and nom.endswith(".html.j2"),
    )

    DIST_DIR.mkdir(exist_ok=True)
    annee = date.today().year

    # Web : une page par entrée de PAGES, toutes héritent de base.html.j2 (nav commune).
    for page in PAGES:
        html = env.get_template(page["template"]).render(
            page_actuelle=page["id"], pages=PAGES, annee=annee, base="", **contexte
        )
        (DIST_DIR / page["fichier"]).write_text(html, encoding="utf-8")
    shutil.copyfile(STATIC_DIR / "style.css", DIST_DIR / "style.css")
    shutil.copyfile(STATIC_DIR / "script.js", DIST_DIR / "script.js")

    # Une page détail par projet, dans dist/projets/. `base="../"` corrige les liens
    # relatifs (style.css, nav, cv.pdf...) hérités de base.html.j2 vu qu'on est un niveau
    # plus bas — nécessaire pour que ça marche aussi une fois publié sous un sous-chemin
    # GitHub Pages (ex. clementospital.github.io/projet-cv/).
    projets_dir = DIST_DIR / "projets"
    projets_dir.mkdir(exist_ok=True)
    for projet in contexte.get("projets") or []:
        html = env.get_template("projet.html.j2").render(
            page_actuelle="projets", pages=PAGES, annee=annee, base="../", projet=projet, **contexte
        )
        (projets_dir / f"{projet['slug']}.html").write_text(html, encoding="utf-8")

    # PDF : le CSS d'impression est injecté inline pour que le rendu ne dépende d'aucune
    # résolution de chemin file:// (Playwright charge le HTML via set_content, sans base URL).
    print_css = (STATIC_DIR / "print.css").read_text(encoding="utf-8")
    html_pdf = env.get_template("pdf.html.j2").render(print_css=print_css, **contexte)
    generer_pdf(html_pdf, DIST_DIR / "cv.pdf")

    # README markdown : écrase le README.md à la racine du repo à chaque build.
    # Sans trim_blocks, chaque ligne de tag Jinja laisse son propre saut de ligne : on
    # normalise les lignes vides répétées plutôt que de truffer le template de marqueurs -/+.
    markdown = env.get_template("readme.md.j2").render(**contexte)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"
    README_MD.write_text(markdown, encoding="utf-8")


def main() -> None:
    try:
        donnees = charger_cv(CV_YAML)
        valider(donnees)
        contexte = preparer_contexte(donnees)
        rendre_templates(contexte)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        sys.exit(1)

    print("Génération terminée : dist/ (site 4 pages), dist/cv.pdf, README.md")


if __name__ == "__main__":
    main()
