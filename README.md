# Gabarit PDF vers Markdown

Projet gabarit pour convertir un document PDF local en une structure Markdown avec extraction des images.

## Objectif

Déposer un ou plusieurs fichiers PDF dans `entree/depot/`, exécuter un script, puis récupérer une sortie structurée dans `sortie/`.

## Structure

```text
entree/
  depot/               # PDF à convertir
sortie/
  <document>/          # 1 dossier par PDF converti
    index.md           # table des matières du document
    01-*.md            # sections extraites depuis le sommaire PDF
    images/            # images extraites du PDF
erreurs/
  <document>/          # rapports d'erreur
scripts/
  process_pdfs.py      # script principal
  install_skills.py    # installation optionnelle des compétences locales
competences/
  maintenance-pdf-markdown/
AGENTS.md
requirements.txt
skills.config.json
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Sous Windows PowerShell :

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Utilisation

1. Déposer un PDF dans `entree/depot/`.
2. Lancer :

```bash
python3 scripts/process_pdfs.py
```

3. Récupérer le résultat dans `sortie/<document>/`.

## Options utiles

```bash
python3 scripts/process_pdfs.py --force
python3 scripts/process_pdfs.py --pdf "entree/depot/mon-document.pdf"
python3 scripts/process_pdfs.py --sortie-dir sortie
```

## Résultat généré

Pour un PDF `Mon document.pdf`, le script crée typiquement :

```text
sortie/
  mon_document/
    Mon document.pdf
    index.md
    01-introduction.md
    02-conclusion.md
    images/
      image-001.png
      image-002.jpeg
```

`index.md` contient la table des matières du document et pointe vers les sections extraites.

## Limitations

- La qualité dépend de la structure interne du PDF.
- Les tableaux sont convertis en tableaux Markdown simples.
- Certains PDF scannés ou très complexes peuvent nécessiter un traitement OCR distinct.
- Les images extraites correspondent aux objets graphiques détectés dans le PDF.

## Compétences locales

Le dépôt inclut une compétence locale minimale dans `competences/maintenance-pdf-markdown/` pour guider les futures évolutions du projet.

Installation optionnelle :

```bash
python3 scripts/install_skills.py
```

Sous Windows, vous pouvez aussi lancer directement :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\process_pdfs.ps1
```

## Dépendances système

Le projet a besoin de :

- Python 3.10+
- `pip`
- `PyMuPDF` installé via `requirements.txt`

Si votre installation Python ne fournit pas `pip`, réinstallez Python avec l'option `pip` activée ou utilisez un environnement virtuel standard Windows.
