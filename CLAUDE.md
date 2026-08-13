# projet-cv

Générateur de CV : `cv.yaml` (source unique de vérité, clés en français) →
`python src/build.py` produit **3 sorties** : site web statique 4 pages
(`dist/`), PDF ATS une page (`dist/cv.pdf`, commité en git), et `README.md`
(écrasé à chaque build, tracké en git).

## Règles à respecter absolument

- **Ne jamais éditer `README.md` ni `dist/*.html` directement** — ce sont des
  sorties générées, écrasées au prochain build. Éditer `cv.yaml` et/ou les
  templates dans `templates/`.
- Toute modif de contenu (expérience, formation, compétence, certification,
  projet…) passe par `cv.yaml`, puis lancer `python src/build.py`. `dist/cv.pdf`
  et `README.md` doivent être régénérés (et committés) après toute modif de
  `cv.yaml` ou des templates.
- Dates toujours au format `YYYY-MM` dans le YAML ; `date_fin: null` = "en
  cours". Le formatage français est fait par `build.py` (`formater_date`),
  jamais de texte de date en dur.
- **Le PDF doit tenir sur une seule page** (contrainte ATS forte, déjà
  resserrée plusieurs fois dans l'historique). Après toute modif touchant le
  PDF (`pdf.html.j2`, `print.css`, ou ajout de contenu dans `cv.yaml`),
  vérifier le nombre de pages (ex. via `pypdf`) et resserrer `print.css` si ça
  déborde sur 2 pages.
- Projet volontairement simple : pas de sur-ingénierie (pas de classes
  abstraites, pas de dépendance ajoutée sans validation, pas de `TODO` dans le
  code), zéro dépendance front externe (pas de CDN, pas de police externe).

## Ajouter une nouvelle section au CV (ex. certifications)

Une section = 1 clé dans `cv.yaml` + rendu à ajouter dans **4 endroits** :
`templates/competences.html.j2` (ou page pertinente, web), `templates/pdf.html.j2`
(garder compact — une ligne par section si possible, pour la contrainte 1 page),
`templates/readme.md.j2`, et si la section a des dates, ajouter le formatage
dans `preparer_contexte()` de `src/build.py`.

## Schéma d'un projet (`cv.yaml` → `projets:`)

Chaque projet suit un format volontairement intuitif, affiché comme une fiche
structurée sur `templates/projet.html.j2` : `nom`, `type` (`"Projet scolaire"`
ou `"Projet personnel"`, pilote le badge coloré), `objectif` (à quoi ça sert),
`pourquoi` (pourquoi ce projet — contexte du cours, ou problème résolu si
personnel), `technos`, `url` (lien vers le dépôt GitHub). Champs optionnels
pour enrichir la page détail : `contribution`, `lancement`, `extraits`,
`apprentissage`, `points_forts`, `points_amelioration`. Respecter ce même
format pour tout nouveau projet ajouté.

## Stack & commandes

- Python 3.11+, PyYAML, Jinja2, Playwright (Chromium headless pour le PDF).
- Setup local : `python -m venv .venv && .venv/bin/pip install -r
  requirements.txt && .venv/bin/playwright install chromium`
- Build : `python src/build.py`
- Prévisualisation web : `python -m http.server` depuis `dist/`
- `.venv/` n'est pas commité (gitignored) — à recréer si absent.

## CI/CD

`.github/workflows/build.yml` : à chaque push sur `main` (hors commits
`[skip ci]`), build complet → déploiement GitHub Pages + commit auto de
`dist/cv.pdf` et `README.md` régénérés.

## Détails de conception

Les décisions de design (pourquoi Playwright plutôt que WeasyPrint, pourquoi
4 pages avec thème terminal, etc.) sont documentées dans
`docs/superpowers/specs/`. Les consulter avant de proposer un changement
d'architecture.
