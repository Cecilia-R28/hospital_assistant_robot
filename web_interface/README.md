# HIAR : interface tactile (HMI) V0.9 / V0.10

Interface Web locale, utilisée depuis un smartphone comme écran tactile de HIAR.
Elle ne dépend pas d'Internet et ne commande jamais directement les moteurs.

## Contenu

- `catalog.py` : catalogue des catégories, actions, destinations et fiches d'information (source unique).
- `requests_model.py` : transforme un choix en demande structurée (V0.10).
- `app.py` : serveur Flask (page d'accueil et route `/api/request`).
- `templates/index.html`, `static/hmi.css`, `static/hmi.js` : écrans, style, navigation.
- `tests/test_catalog.py` : tests pytest.

## Lancer

    cd web_interface
    python3 app.py

Prérequis : `sudo apt install -y python3-flask python3-pytest`.
Ouvrir ensuite http://localhost:5000 sur le PC.

## Tests

    cd web_interface
    python3 -m pytest tests -v

## Demandes structurées

    {"category": "ORIENTATION", "destination": "PHARMACY"}
    {"category": "CONSULTATION", "action": "APPOINTMENT"}
    {"category": "INFORMATION", "topic": "HIV"}

Destinations du MVP : PHARMACY, LABORATORY, RECEPTION.
Un identifiant inconnu est refusé par l'API (erreur 400).

## Mode démonstration technique

Ajouter `?debug` à l'adresse (http://localhost:5000/?debug) affiche la demande
structurée sous chaque confirmation.

## Utiliser le smartphone (serveur dans WSL2)

Le Wi-Fi de la box peut isoler les appareils entre eux. La méthode qui a fonctionné :

1. Windows : Paramètres, Réseau et Internet, Point d'accès sans fil mobile, l'activer.
   Le PC prend l'adresse 192.168.137.1.
2. Connecter le téléphone à ce réseau.
3. Dans WSL, lancer le serveur, puis relever l'adresse de WSL avec `hostname -I`.
4. PowerShell administrateur (remplacer IP_WSL par l'adresse relevée) :

        netsh interface portproxy add v4tov4 listenport=5000 listenaddress=0.0.0.0 connectport=5000 connectaddress=IP_WSL
        New-NetFirewallRule -DisplayName "HIAR 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow

5. Sur le téléphone : http://192.168.137.1:5000 (téléphone en paysage).

L'adresse de WSL change à chaque redémarrage de WSL : supprimer la règle puis la recréer.

    netsh interface portproxy delete v4tov4 listenport=5000 listenaddress=0.0.0.0

## Limites connues

- Les signes vitaux ne sont pas branchés : l'écran indique "En préparation".
- Les fiches Renseignements sont des informations générales non diagnostiques.
  Les textes sont à valider avec une source officielle (OMS, ministère de la Santé) avant la soutenance.
- Aucun lien avec ROS2 pour l'instant : le pont HMI vers ROS2 sera ajouté à l'intégration.
- Non testé sur le Raspberry Pi.
