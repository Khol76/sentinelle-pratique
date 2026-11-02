# Sentinelle Web — projet d'entraînement HackDécouverte
# Une mini application Flask qui analyse une URL et lui donne un score de risque.
#
# Concepts Flask à retenir :
#   1. Une "route" = une adresse de ton site (ex. "/" ou "/analyser")
#      reliée à une fonction Python grâce au décorateur @app.route(...)
#   2. request.form = les données envoyées par un formulaire HTML
#   3. render_template(...) = génère une page HTML en y injectant des variables
#   4. Le navigateur fait une REQUÊTE, Flask répond une RÉPONSE (souvent du HTML)
#
# Le trajet d'une analyse, du clic jusqu'à l'écran :
#   formulaire (index.html) --POST--> route /analyser --appelle--> analyser_url()
#   --puis--> render_template("resultat.html", ...) --> la page affiche score,
#   verdict et raisons. L'URL est analysée comme du TEXTE seulement :
#   on ne visite jamais le lien.
#
# Cinq règles de détection (score de départ : 100) :
#   1. pas de HTTPS .................. -30
#   2. présence d'un « @ » ............ -30
#   3. adresse très longue (> 75) ..... -20
#   4. domaine imitant une marque ..... -25   (NOUVEAU)
#   5. trop de sous-domaines .......... -20   (NOUVEAU)

from flask import Flask, redirect, render_template, request, session, url_for
from urllib.parse import urlparse
import ipaddress
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cle-d-entrainement-sentinelle")

# --- Règle 4 : les marques qu'on surveille et leurs domaines OFFICIELS -------
# Si l'adresse contient le nom d'une marque mais n'est PAS son domaine
# officiel, c'est un signal classique d'hameçonnage (ex. « paypa1.com »,
# « desjardins-securite.com »).
MARQUES = {
    "paypal": ["paypal.com"],
    "google": ["google.com", "google.ca"],
    "desjardins": ["desjardins.com"],
    "apple": ["apple.com"],
    "microsoft": ["microsoft.com"],
    "amazon": ["amazon.com", "amazon.ca"],
    "netflix": ["netflix.com"],
    "facebook": ["facebook.com"],
}

# Les fraudeurs remplacent souvent des lettres par des chiffres
# (paypa1, faceb00k, g00gle). On « traduit » ces chiffres en lettres
# avant de comparer, pour attraper les imitations déguisées.
TRADUCTION_LEET = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a",
                                 "5": "s", "7": "t", "$": "s"})


def domaine_est_officiel(domaine, officiels):
    """Vrai si le domaine EST un domaine officiel de la marque,
    ou un de ses sous-domaines légitimes (ex. www.paypal.com)."""
    for officiel in officiels:
        if domaine == officiel or domaine.endswith("." + officiel):
            return True
    return False


def marque_imitee(domaine):
    """Retourne le nom de la marque imitée, ou None si tout est beau."""
    domaine_traduit = domaine.translate(TRADUCTION_LEET)
    for marque, officiels in MARQUES.items():
        if marque in domaine_traduit and not domaine_est_officiel(domaine, officiels):
            return marque
    return None


def analyser_url(url):
    """Retourne (score, raisons) : score de 0 (très risqué) à 100 (sûr),
    et la liste des raisons en langage clair."""
    score = 100
    raisons = []

    # Si l'utilisateur n'a pas mis de schéma (http/https), on en ajoute un
    # pour que urlparse puisse bien découper l'adresse.
    # On ajoute « https:// » (comme les navigateurs modernes quand on tape
    # juste « yahoo.fr ») : seul un « http:// » écrit explicitement est
    # pénalisé. On enlève aussi les espaces d'un copier-coller.
    url = url.strip()
    url_analysee = url if "://" in url else "https://" + url
    morceaux = urlparse(url_analysee)
    domaine = morceaux.hostname or ""   # ex. "www.paypa1.com" (sans le chemin)

    # Règle 1 — pas de HTTPS : la connexion n'est pas chiffrée
    if morceaux.scheme != "https":
        score -= 30
        raisons.append("Le site n'utilise pas HTTPS : la connexion n'est pas chiffrée.")

    # Règle 2 — présence d'un « @ » : tout ce qui précède le @ est ignoré
    # par le navigateur, une technique classique d'hameçonnage
    # (ex. http://banque-legitime.com@site-pirate.ru)
    if "@" in url:
        score -= 30
        raisons.append("L'adresse contient un « @ » : le vrai site est celui après le @, pas celui affiché avant.")

    # Règle 3 — URL très longue : souvent utilisée pour noyer le vrai domaine
    if len(url) > 75:
        score -= 20
        raisons.append("L'adresse est très longue (" + str(len(url)) + " caractères) : fréquent dans les liens d'hameçonnage.")

    # Règle 4 — domaine qui imite une marque connue (NOUVEAU)
    marque = marque_imitee(domaine)
    if marque:
        score -= 25
        raisons.append("Le domaine imite la marque « " + marque + " » sans être son site officiel : "
                       "une adresse comme « " + domaine + " » cherche à te faire croire que tu es sur le vrai site.")

    # Règle 5 — nombre inhabituel de sous-domaines (NOUVEAU)
    # Un domaine normal a 2 ou 3 morceaux séparés par des points
    # (ex. google.com = 2, www.google.com = 3). Les fraudeurs empilent les
    # sous-domaines pour cacher le vrai domaine à la fin de l'adresse.
    morceaux_domaine = domaine.split(".") if domaine else []
    if len(morceaux_domaine) >= 5:
        score -= 20
        raisons.append("L'adresse empile " + str(len(morceaux_domaine)) + " morceaux de domaine séparés par des points : "
                       "empiler les sous-domaines sert souvent à cacher le vrai site, tout au bout de l'adresse.")

    # Règle 6 — adresse IP au lieu d'un nom de domaine
    hote = morceaux.hostname
    if hote:
        try:
            ipaddress.ip_address(hote)  # réussit seulement si c'est une IP
            score -= 25
            raisons.append(
                "L'adresse utilise une adresse IP (" + hote + ") au lieu d'un nom de domaine : les sites légitimes utilisent presque toujours un nom de domaine.")
        except ValueError:
            pass  # ce n'est pas une IP : rien à signaler pour cette règle

    if not raisons:
        raisons.append("Aucun signal de risque détecté par nos règles de base. Reste vigilant : ça ne garantit pas que le site est légitime.")

    return max(score, 0), raisons


def details_url(url):
    """Retourne une fiche d'informations sur l'adresse (affichée sur la page
    de résultat), et l'adresse « sûre » vers laquelle on peut continuer.
    Toujours une analyse TEXTUELLE : on ne visite jamais le site."""
    url = url.strip()
    url_complete = url if "://" in url else "https://" + url
    morceaux = urlparse(url_complete)
    domaine = morceaux.hostname or ""

    est_ip = False
    if domaine:
        try:
            ipaddress.ip_address(domaine)
            est_ip = True
        except ValueError:
            pass

    morceaux_domaine = domaine.split(".") if domaine else []
    marque = marque_imitee(domaine)

    # .port lève une erreur si le port n'est pas un nombre (ex. « site.com:abc »)
    try:
        port = str(morceaux.port) if morceaux.port else "par défaut"
    except ValueError:
        port = "invalide ⚠️"

    fiche = [
        ("Adresse complète", url_complete),
        ("Protocole", morceaux.scheme.upper() if morceaux.scheme else "inconnu"),
        ("Connexion chiffrée", "Oui 🔒" if morceaux.scheme == "https" else "Non ⚠️"),
        ("Domaine", domaine or "introuvable"),
        ("Domaine principal", ".".join(morceaux_domaine[-2:]) if len(morceaux_domaine) >= 2 and not est_ip else "—"),
        ("Extension (TLD)", "." + morceaux_domaine[-1] if morceaux_domaine and not est_ip else "—"),
        ("Nombre de morceaux de domaine", str(len(morceaux_domaine))),
        ("Adresse IP au lieu d'un nom", "Oui ⚠️" if est_ip else "Non"),
        ("Port", str(morceaux.port) if morceaux.port else "par défaut"),
        ("Chemin", morceaux.path or "/"),
        ("Paramètres", morceaux.query or "aucun"),
        ("Contient un « @ »", "Oui ⚠️" if "@" in url else "Non"),
        ("Longueur de l'adresse", str(len(url)) + " caractères"),
        ("Marque imitée", marque if marque else "aucune détectée"),
    ]

    # On ne propose de continuer que vers une adresse web classique
    # (http/https) avec un domaine : jamais « javascript: », « file: », etc.
    lien_sur = url_complete if morceaux.scheme in ("http", "https") and domaine else None
    return fiche, lien_sur


def verdict_pour(score):
    """Traduit le score en verdict + couleur d'affichage."""
    if score >= 80:
        return "Probablement sûr", "vert"
    if score >= 50:
        return "Prudence", "orange"
    return "Risqué", "rouge"


# Route 1 : la page d'accueil, qui affiche le formulaire
@app.route("/")
def accueil():
    return render_template("index.html")


# Route 2 : reçoit le formulaire (méthode POST) et affiche le résultat
@app.route("/analyser", methods=["POST"])
def analyser():
    url = request.form["url"]          # le champ nommé "url" du formulaire
    score, raisons = analyser_url(url)  # notre logique Python ordinaire
    verdict, couleur = verdict_pour(score)
    fiche, lien_sur = details_url(url)
    # Mission 3 — la nouvelle analyse va EN PREMIER, max 10 entrées,
    # et on RÉASSIGNE la liste complète (le piège expliqué plus haut).
    historique = session.get("historique", [])
    historique = [{"url": url, "score": score, "verdict": verdict,
                   "couleur": couleur}] + historique
    session["historique"] = historique[:10]

    return render_template("resultat.html", url=url, score=score,
                           raisons=raisons, verdict=verdict, couleur=couleur,
                           fiche=fiche, lien_sur=lien_sur,
                           historique=session["historique"])

@app.route("/effacer-historique")
def effacer_historique():
    session.pop("historique", None)
    return redirect(url_for("accueil"))

# Point d'entrée : « python app.py » démarre le serveur de développement
if __name__ == "__main__":
    app.run(debug=True)
