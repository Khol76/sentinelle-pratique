# 🛡️ Sentinelle Web

Mini application web en **Python + Flask** qui analyse une adresse web et lui attribue un **score de risque d'hameçonnage** (0 = très risqué, 100 = aucun signal détecté), avec les raisons expliquées en langage clair.

> ⚠️ L'analyse est purement textuelle : l'application ne visite jamais les liens analysés.

## 🔍 Les 6 règles de détection

| # | Règle | Pénalité |
|---|-------|----------|
| 1 | Pas de HTTPS — la connexion n'est pas chiffrée | −30 |
| 2 | Présence d'un « @ » — tout ce qui le précède est ignoré par le navigateur | −30 |
| 3 | Adresse très longue (> 75 caractères) | −20 |
| 4 | Domaine imitant une marque connue (ex. `paypa1.com`) — avec traduction des chiffres en lettres (0→o, 1→l…) et vérification du domaine officiel, pour ne jamais pénaliser le vrai site | −25 |
| 5 | Trop de sous-domaines (5 morceaux ou plus) — sert à cacher le vrai site tout au bout de l'adresse | −20 |
| 6 | Adresse IP au lieu d'un nom de domaine (ex. `http://192.168.0.25/login`) | −25 |

**Verdicts :** 80–100 → *Probablement sûr* 🟢 · 50–79 → *Prudence* 🟠 · 0–49 → *Risqué* 🔴

## ✨ Fonctionnalités

- **Historique de session** : chaque analyse s'ajoute à un historique personnel (10 dernières, la plus récente en premier), avec pastilles de couleur — parfait pour comparer plusieurs liens pendant une démo.
- **Bouton « Effacer l'historique »** pour repartir à zéro.
- **Présentation soignée** : bandeau bleu marine et accents dorés, mise en page adaptative (mobile et bureau).

## 🚀 Installation et lancement

Python 3 requis (`python --version` pour vérifier).

```bash
# 1. Aller dans le dossier du projet
cd sentinelle-pratique

# 2. Créer un environnement virtuel
python -m venv .venv

# 3. L'activer
#    Windows (PowerShell) :  .venv\Scripts\Activate.ps1
#    macOS / Linux :         source .venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Lancer l'application
python app.py
```

Ouvrir ensuite **http://127.0.0.1:5000** dans le navigateur.

## 🧪 Jeux de tests

Le fichier `jeux-de-tests.md` détaille 6 adresses avec le score et le verdict attendus pour chacune :

| Adresse | Score | Verdict |
|---|---|---|
| `https://www.google.com` | 100 | Probablement sûr |
| `http://banque-legitime.com@site-pirate.ru/connexion` | 40 | Risqué |
| `https://www.paypa1.com/connexion` | 75 | Prudence |
| `http://desjardins-securite.com` | 45 | Risqué |
| `https://connexion.banque.nationale.securite-verification.com/session/identifiant/client` | 60 | Prudence |
| `https://www.paypal.com/signin` | 100 | Probablement sûr |

## 🗂️ Structure du projet

```
sentinelle-pratique/
├── app.py               ← serveur Flask + logique d'analyse (6 règles)
├── requirements.txt     ← dépendances (Flask)
├── static/
│   └── style.css        ← feuille de style partagée (marine/or)
└── templates/
    ├── index.html       ← page du formulaire
    └── resultat.html    ← page de résultat (score, raisons, historique)
```

## 🛠️ Technologies

- Python 3 + Flask (routes, gabarits Jinja2, sessions)
- HTML / CSS maison (variables CSS, adaptatif)

## 👤 Contexte

Projet d'entraînement réalisé en vue d'**HackDécouverte 2026** (hackathon, 14 novembre 2026, Université Concordia, Montréal). La version du jour J sera reconstruite sur place avec l'équipe.

**Auteur :** Olivier Montpetit ([@khol76](https://github.com/khol76)) — AEC Infrastructure informatique et cybersécurité, Cégep Bois-de-Boulogne.

## 🔒 Limites honnêtes

- L'application détecte des *signaux* d'hameçonnage : elle ne garantit jamais qu'un site est légitime.
- L'historique vit dans un cookie de session : il disparaît si les cookies sont effacés et ne suit pas d'un appareil à l'autre. Un vrai produit le stockerait côté serveur, dans une base de données.
