# AGENTS

## But du dépôt

Ce dépôt sert à convertir des PDF locaux en une structure Markdown exploitable, avec sections et images extraites.

## Règles de travail

- Conserver un flux simple : `entree/depot` -> `scripts/process_pdfs.py` -> `sortie`.
- Préserver des chemins et noms de fichiers stables pour faciliter l'automatisation.
- Garder le code Python compatible avec un usage local simple, sans service externe obligatoire.
- Documenter toute nouvelle option CLI dans `README.md`.
- Ne pas introduire de dépendances lourdes sans justification claire.

## Arborescence attendue

- `entree/depot/` contient les PDF source.
- `sortie/` contient un dossier par document extrait.
- `erreurs/` contient les rapports d'échec.
- `scripts/` contient les points d'entrée et utilitaires.
- `skills/` contient les compétences locales liées au maintien du gabarit.

## Vérifications à faire après modification

- Exécuter `python scripts/process_pdfs.py --help`.
- Tester au moins une conversion locale.
- Vérifier la présence de `index.md`, des sections Markdown et du dossier `images/`.
- Vérifier que le mode `--force` remplace correctement une extraction existante.

## Style

- Favoriser des fonctions courtes et explicites.
- Ajouter des commentaires seulement quand une contrainte n'est pas évidente.
- Garder la documentation en français.
