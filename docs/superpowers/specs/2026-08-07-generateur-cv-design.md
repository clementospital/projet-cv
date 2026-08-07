# Générateur de CV multi-format — spec de conception

Date : 2026-08-07
Auteur : Clément Ospital (avec Claude Code)

## Objectif

Pipeline qui prend `cv.yaml` (source unique de vérité) et génère trois sorties :
un PDF compatible ATS, une page web statique, et le `README.md` du repo (qui
affiche le CV en markdown sur GitHub). Un seul appel `python src/build.py`
produit tout. Redéploiement automatique via GitHub Actions à chaque push.

## Contexte

Projet à but d'apprentissage : chaque partie doit rester lisible, sans
sur-ingénierie (pas de classes abstraites, pas de système de plugins, pas de
dépendance ajoutée sans validation préalable, pas de `TODO` laissé dans le code).

## Stack

- Python 3.11+
- PyYAML (lecture de `cv.yaml`)
- Jinja2 (templating des 3 sorties)
- Playwright, moteur Chromium (génération PDF)
- HTML/CSS écrits à la main, aucun framework front, aucune dépendance externe
  (pas de CDN, pas de Google Fonts)
- GitHub Actions (CI/CD)

### Choix : Playwright plutôt que WeasyPrint

Playwright pilote un vrai Chromium headless, donc le rendu PDF utilise le même
moteur que la prévisualisation web (`style.css` et `print.css` se comportent de
façon cohérente entre les deux sorties). WeasyPrint a un moteur de rendu maison
avec un support CSS partiel (grid, flexbox, media queries) qui aurait pu diverger
du rendu web. Coût du choix : téléchargement d'un binaire Chromium
(`playwright install chromium`, ~300 Mo, une fois).

## Schéma `cv.yaml`

Toutes les clés sont en français. Les dates sont toujours au format `YYYY-MM` et
formatées à l'affichage par `build.py` (jamais de texte de date en dur dans le
YAML). `date_fin: null` signifie "en cours" (poste ou formation sans fin connue).

```yaml
identite:
  nom: "Clément Ospital"
  titre: "Étudiant en Génie Informatique et Réseaux"
  email: "clement.ospital64@gmail.com"
  telephone: "+33 07 83 62 68 63"
  localisation: "Toulouse, France"

accroche: >
  Étudiant en dernière année du Master Génie Informatique et Réseaux à l'INSA
  Toulouse, passionné par le développement logiciel, la cybersécurité et
  l'intelligence artificielle, je recherche un poste à temps plein dans ces
  domaines à l'issue de mon stage chez Capgemini. Je souhaite mettre à profit
  et approfondir mes compétences en programmation, et contribuer efficacement
  aux projets de mon futur employeur.

experiences:
  - poste: "Stagiaire"
    entreprise: "Capgemini Toulouse"
    lieu: "Toulouse"
    date_debut: "2026-06"
    date_fin: "2026-09"
    points:
      - "Secteur GNSS : création d'un logiciel d'automatisation des retours clients utilisant une IA pour aider les équipes à traiter les demandes plus vite."
  - poste: "Équipier"
    entreprise: "McDonald's"
    lieu: "Benejacq"
    date_debut: "2024-06"
    date_fin: "2024-08"
    points:
      - "Travail au comptoir, en contact avec les clients, adaptation aux demandes."
      - "Apprentissage du métier en situation réelle, intégration rapide à l'équipe."
  - poste: "Tourneur-Fraiseur"
    entreprise: "Nexteam"
    lieu: "Narcastet"
    date_debut: "2023-07"
    date_fin: "2023-08"
    points:
      - "Découverte du métier au sein d'une équipe de travailleurs, sous supervision."
      - "Expérience du travail à la chaîne, exigeant une bonne cohésion d'équipe."

formations:
  - diplome: "Master en Génie Informatique et Réseaux"
    etablissement: "INSA Toulouse"
    lieu: "Toulouse"
    date_debut: "2022-09"
    date_fin: "2027-06"
  - diplome: "Échange Erasmus — Département Informatique"
    etablissement: "Oslo Metropolitan University"
    lieu: "Oslo, Norvège"
    date_debut: "2025-01"
    date_fin: "2025-06"
  - diplome: "Baccalauréat, mention Très Bien (spé. Mathématiques et NSI)"
    etablissement: "Lycée Paul Rey"
    lieu: "Nay"
    date_debut: "2019-09"
    date_fin: "2022-06"

competences:
  - categorie: "Langages de programmation"
    items: ["Python", "Ada", "HTML", "C", "CSS", "Bash", "OCaml", "Java", "JavaScript"]
  - categorie: "Savoir-être"
    items:
      - "Esprit d'initiative et capacité à apprendre rapidement de nouvelles technologies"
      - "Solides compétences en résolution de problèmes et optimisation d'algorithmes"
      - "Esprit d'équipe et capacité à communiquer des concepts techniques à des publics variés"

projets: []   # vide pour l'instant, à compléter plus tard avec de vrais projets

langues:
  - langue: "Français"
    niveau: "Langue maternelle"
  - langue: "Anglais"
    niveau: "C1 (TOEIC 955)"

centres_interet:
  - categorie: "Sports"
    items: ["Football", "Badminton", "Randonnée", "Ski"]
  - categorie: "Autres"
    items: ["Voyages et découverte de nouvelles cultures", "Programmation et jeux vidéo"]
```

### Règles de validation (au démarrage de `build.py`)

Champs requis, sinon arrêt avec message clair (ex. `Erreur cv.yaml :
experiences[1].date_debut manquant`), pas de stacktrace brute :

- `identite.nom`, `identite.email`
- Pour chaque élément de `experiences` : `poste`, `entreprise`, `date_debut`
- Pour chaque élément de `formations` : `diplome`, `etablissement`, `date_debut`
- `date_fin` est le seul champ nullable de ces deux listes

Pas de dépendance de validation externe (`pydantic`, `jsonschema`) — vérifications
écrites à la main.

### Formatage des dates

Fonction dédiée dans `build.py`, mapping des mois français écrit à la main (pas
de dépendance `babel` ni de locale système) : `"2026-06"` → `"Juin 2026"`.
`date_fin: null` → `"En cours"`.

## Architecture et flux de données

```
cv.yaml
src/build.py
templates/
  web.html.j2
  pdf.html.j2
  readme.md.j2
static/style.css
static/print.css
dist/                  # index.html + cv.pdf (seul fichier commité du dossier)
README.md              # généré par build.py, tracké en git, écrasé à chaque build
requirements.txt
.gitignore
.github/workflows/build.yml
```

`src/build.py`, exécuté par `python src/build.py` :

1. Charge `cv.yaml` avec PyYAML
2. Valide les champs requis (cf. ci-dessus)
3. Pré-traite les données : formatage des dates, résolution `date_fin: null` →
   "En cours"
4. Rend les 3 templates Jinja2 avec le contexte préparé
5. Écrit :
   - `dist/index.html` (page web)
   - `dist/cv.pdf` (généré via Playwright/Chromium headless à partir du HTML
     rendu par `pdf.html.j2`)
   - `README.md` à la racine du repo (écrasé, c'est la version markdown du CV)

### `.gitignore`

```
.venv/
__pycache__/
*.pyc
.env
dist/*
!dist/cv.pdf
```

Le PDF final est commité pour être consultable directement depuis le repo sans
dépendre du déploiement Pages ; le reste de `dist/` (HTML généré) est ignoré.

## Contraintes de sortie

**PDF (compatible ATS)** : une seule colonne, aucune image, aucun tableau pour
la mise en page, texte réellement sélectionnable, ordre de lecture logique dans
le DOM, tient sur une page si le contenu le permet. `print.css` gère le format
A4 et les sauts de page proprement (`page-break-inside: avoid` sur les blocs
d'expérience/formation).

**Web** : responsive, mode sombre via `prefers-color-scheme`, liens cliquables
vers les projets, aucune dépendance externe.

**Markdown (`README.md`)** : lisible directement sur GitHub, structure calquée
sur les mêmes sections que les deux autres sorties.

## Hors périmètre (pour l'instant)

- Section `projets` : liste vide dans `cv.yaml`, à compléter plus tard avec de
  vrais projets (peu de dépôts publics trouvés sur `clemcloummm`)
- Remote GitHub / nom du repo pour Pages : pas encore configuré, à régler à
  l'étape 5 (workflow GitHub Actions)
- Pas de suite de tests automatisés (`pytest`) — la validation YAML au démarrage
  fait office de garde-fou, cohérent avec la contrainte "pas de sur-ingénierie"

## Phasage (validation utilisateur requise entre chaque étape)

1. Schéma `cv.yaml` (ce document) + fichier rempli avec les vraies données
2. `build.py` minimal : lecture YAML, validation, formatage dates, rendu →
   écrase `README.md`
3. `web.html.j2` + `style.css`, servi en local (`python -m http.server` depuis
   `dist/`) pour validation visuelle
4. `pdf.html.j2` + `print.css` (A4, sauts de page), généré via Playwright
5. `.github/workflows/build.yml` : build à chaque push, publication GitHub
   Pages, commit du PDF généré dans le repo

## Fichiers supprimés du scaffold précédent

`.gitignore` et `requirements.txt` du commit `ceca49d` sont recréés de zéro :
l'ancien `requirements.txt` était un `pip freeze` de 146 paquets sans rapport
avec ce projet (environnement accidentel). Le nouveau `requirements.txt` ne
contiendra que `pyyaml`, `jinja2`, `playwright`.
