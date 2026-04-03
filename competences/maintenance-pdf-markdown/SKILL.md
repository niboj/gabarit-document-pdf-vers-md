---
name: maintenance-pdf-markdown
description: Maintenir et faire évoluer ce gabarit de conversion PDF vers Markdown sans casser le flux local ni la structure de sortie.
---

# Maintenance PDF Markdown

Utiliser ce skill quand une demande concerne l'évolution de ce dépôt, de ses scripts ou de sa documentation.

## Intentions

- Préserver le flux `entree/depot -> script -> sortie`.
- Garder la sortie Markdown lisible et stable.
- Limiter les dépendances et la complexité opérationnelle.

## Vérifications minimales

1. Vérifier `python scripts/process_pdfs.py --help`.
2. Tester une conversion locale.
3. Confirmer la présence de `index.md`, des sections et du dossier `images/`.
4. Mettre à jour `README.md` si l'usage change.
