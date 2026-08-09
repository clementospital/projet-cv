# Site multi-pages — évolution du générateur de CV

Date : 2026-08-09
Auteur : Clément Ospital (avec Claude Code)

## Objectif

Remplacer la page web unique (CV en ligne) par un vrai petit site personnel de
4 pages, plus travaillé visuellement et interactif, tout en gardant le PDF
(ATS, une page) et le README markdown identiques. `cv.yaml` reste la source
unique de vérité ; seule la sortie web change de forme.

## Décisions

**Style visuel : thème « développeur / terminal ».** Fond sombre par défaut
(`#0a0e0c`), texte clair, accent vert terminal (`#39ff88`) et cyan secondaire
(`#5fd9e0`), typographie monospace système sur les titres/nav/accents (aucune
police externe : `ui-monospace, "Cascadia Code", "SFMono-Regular", Consolas,
"Liberation Mono", Menlo, monospace`), corps de texte en police système sans-
serif pour la lisibilité sur les longs paragraphes. Composant récurrent :
carte "fenêtre de terminal" (barre avec 3 pastilles + titre façon nom de
fichier) pour les blocs de contenu.

**Thème clair en bascule manuelle, pas automatique.** Contrairement à
l'ancienne page CV qui suivait `prefers-color-scheme`, le site est sombre par
défaut (cohérent avec l'identité "terminal") avec un bouton de bascule
persistant (`localStorage`) plutôt qu'une détection OS — choix assumé pour
préserver l'ambiance.

**4 pages**, nav commune, générées depuis un layout Jinja2 partagé
(`base.html.j2` + `{% extends %}`) :

- **Accueil** (`index.html`) : hero (nom, accroche, curseur clignotant CSS),
  deux CTA (Voir mon parcours / Télécharger le CV), aperçu rapide des
  langages.
- **Parcours** (`parcours.html`) : timeline verticale, expérience
  professionnelle puis formation (deux sections distinctes, pas d'entrelacement
  chronologique — plus simple et clair que de fusionner les deux types
  d'entrées sur une même ligne de temps).
- **Compétences** (`competences.html`) : compétences groupées, langues,
  centres d'intérêt, en cartes "fenêtre".
- **Projets** (`projets.html`) : page placeholder ("bientôt disponible"),
  lien vers le profil GitHub en attendant.

**Interactivité (JS vanilla, sans dépendance)** :
- Menu mobile (burger) sous 768px
- Bascule thème clair/sombre persistante
- Apparition au scroll (`IntersectionObserver`), avec amélioration
  progressive : le contenu reste visible si JS est désactivé (la classe qui
  cache les éléments n'est ajoutée qu'après confirmation que JS tourne)
- Bouton "copier l'email" avec retour visuel

## Hors périmètre

- Page Projets vide pour l'instant (cf. spec précédente)
- Pas de framework front, pas de police externe, pas de nouvelle dépendance
  Python
- PDF et README markdown inchangés dans leur structure (toujours ATS /
  une page pour le PDF)

## Impact technique

- `templates/web.html.j2` est retiré, remplacé par `base.html.j2` +
  4 templates de page qui en héritent
- `src/build.py` gagne une liste `PAGES` (id, template, fichier de sortie,
  libellé de nav) et boucle dessus pour générer les 4 fichiers HTML ; la nav
  est générée une seule fois à partir de cette liste (pas de duplication dans
  chaque template)
- `static/script.js` ajouté, copié vers `dist/` au même titre que
  `style.css`
- `cv.yaml` gagne un champ optionnel `identite.github`
