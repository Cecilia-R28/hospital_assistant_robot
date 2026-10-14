# HIAR — Checkpoint général
**Date : 14 octobre 2026**
**Projet : Hospital Intelligent Assistant Robot**
**Branche de travail : `integration/v1.0-robot`**
**Dernier commit HMI sur cette branche : `a7dac8d`**

## 1. Objectif

Développer un prototype low-cost d'assistant robotique hospitalier :
smartphone → interface Web → demande structurée → ROS 2 → Supervisor →
navigation réactive → ESP32 → L298N → moteurs.

Principe d'architecture :
**L'IA comprend. La navigation décide du mouvement. Le Supervisor valide. L'ESP32 exécute.**

Le HMI ne commande jamais directement les moteurs.

## 2. État confirmé au 14 octobre

### Interface Web V0.9 / contrat V0.10
- Interface Flask accessible depuis le smartphone.
- Catalogue avec consultation, orientation et renseignements.
- API `/api/request` et demandes structurées.
- `CONTRACT.md` décrit le contrat HMI/ROS 2.
- Tests de catalogue et d'API disponibles.

### HMI vers ROS 2 V1.0
- Le serveur Web a fonctionné sur le Raspberry Pi.
- Une demande Pharmacie a été reçue sur `/hmi/request`.
- Message observé :
  `{"category": "ORIENTATION", "destination": "PHARMACY"}`.
- Type du topic : `std_msgs/msg/String`, contenant le JSON sous forme de chaîne.
- Le commit initial du pont est `d08d574`.

Limite : cette preuve valide la publication et la réception sur le topic.
Elle ne prouve pas que le Supervisor traite la demande ni que le robot se déplace.

### Fiabilité de l'API
Les améliorations locales ont été testées puis enregistrées dans le commit
`a7dac8d` sur `integration/v1.0-robot` :
- rejet des services indisponibles ;
- réponse HTTP 503 si le pont ne publie pas ;
- capture des exceptions de publication ;
- tests supplémentaires pour les échecs.

Résultat de test observé avant le commit :
`22 passed in 1.29s`.

Ces tests sont locaux et automatisés ; ils ne remplacent pas les tests ROS 2 réels ni les essais physiques.

## 3. État Git

Branches observées :
- `main` : `28c5c31`.
- `feature/v0.9-web-interface` : `d08d574`, interface et pont initial.
- `feature/v0.8-navigation` : `1baa5b1`, code de navigation/perception existant.
- `integration/v1.0-robot` : contient le HMI et le commit d'amélioration `a7dac8d`, poussé sur GitHub.

La branche d'intégration est distincte des branches originales.
Ne pas fusionner, réinitialiser ni nettoyer les branches à l'aveugle.

## 4. Code ROS 2 de V0.8

Les sources présentes dans `feature/v0.8-navigation` comprennent :
- `esp32_interface_node.py`
- `navigation_decision_node.py`
- `obstacle_detector_node.py`
- `robot_status_node.py`
- `robot_supervisor.py`
- `setup.py` avec les exécutables de navigation et de détection.

Le nœud de navigation lit :
- `/sensors/ultrasonic`
- `/sensors/ir_left`
- `/sensors/ir_right`
- `/esp32/status`
- `/navigation/command`

Il publie ses décisions sur `/robot/command`.

Le Supervisor V0.8 :
- reçoit `/robot/command` ;
- reçoit `/sensors/obstacle` ;
- refuse FORWARD lorsqu'un obstacle est signalé ;
- publie les commandes autorisées sur `/robot/motor_command` ;
- publie `/robot/status`.

L'interface ESP32 V0.8 écoute `/robot/motor_command` et publie les données des trois capteurs.

Important : les sources V0.8 sont dans une branche Git distincte. Le fait d'y accéder avec `git show` ne signifie pas qu'elles sont présentes dans le dossier de travail courant.

Le collaborateur a modifié la partie firmware ESP32, et non les nœuds ROS 2.
Préserver le code ROS 2 V0.8 existant et comparer les versions avant toute modification.

## 5. Firmware ESP32

Copie sauvegardée dans le dépôt :
`firmware/esp32/HIAR_ESP32_Test/HIAR_ESP32_Test.ino`

Original sur le disque E :
`E:\SOUTENANCE\M2\Medical Robot Assistant\HIAR_ESP32_Test\HIAR_ESP32_Test.ino`

La copie a été vérifiée par `cmp` et est identique à l'original.
Taille observée : 16 492 octets, 1 141 lignes.

Le firmware utilise notamment :
- `DIST,<cm>`
- `IR,LEFT,<0|1>`
- `IR,RIGHT,<0|1>`
- `ACK,...`
- `SAFETY,...`
- `REJECTED,...`

Ces formats correspondent à ceux recherchés par l'interface ESP32 de V0.8.
Le fonctionnement combiné reste à valider physiquement.

Points à examiner avant les essais :
- vitesse configurée à 75 %, contre 128/255 dans un ancien checkpoint ;
- le compteur `MAX_MOVE_DURATION` peut être réinitialisé par les commandes FORWARD répétées ;
- le L298N chauffe fortement : procéder aux tests avec prudence.

Ne pas modifier le firmware sans test ciblé.

## 6. Environnements

### PC / WSL
- Windows, WSL2, Ubuntu 22.04.5.
- ROS 2 Humble, Python 3.10.12 et Git.
- Dépôt : `~/projects/hospital_assistant_robot`.
- Package ROS 2 : `hospital_robot`.

### Raspberry Pi
- Ubuntu 22.04.5 ARM64 et ROS 2 Humble.
- Environnement Python HMI : `~/hiar-venv`.
- Copie de déploiement HMI :
  `~/hiar_web_interface_deploy_20261014`.

Le déploiement du package robotique complet sur le Pi n'est pas encore confirmé.
Ne pas supposer que tous les nœuds du PC tournent actuellement sur le Pi.

## 7. Matériel connu

- ESP32, L298N, deux moteurs DC.
- HC-SR04 frontal et deux capteurs IR LM393.
- Pas d'encodeurs.
- Pas de LiDAR.

Brochage :
- ENA 25, IN1 26, IN2 27.
- ENB 14, IN3 33, IN4 32.
- HC-SR04 TRIG 13, ECHO 34 avec diviseur de tension.
- IR gauche 18, IR droit 19.

Logique des IR :
- 1 = libre ;
- 0 = obstacle.

## 8. Pièce manquante de V1.0

Le pont Flask publie sur `/hmi/request`, mais aucune souscription à ce topic n'a été trouvée dans les fichiers Python du package de la branche d'intégration.

Il faut concevoir ou identifier un récepteur de la demande HMI, puis définir comment une destination validée est transmise à la navigation, sans contourner le Supervisor.

Ne pas connecter directement le HMI aux commandes moteur.
Ne pas supposer que publier un JSON déclenche déjà un déplacement.

## 9. Priorités

1. Préserver le firmware et le checkpoint dans Git.
2. Intégrer les sources ROS 2 V0.8 à la branche d'intégration après inspection contrôlée.
3. Vérifier les dépendances et `setup.py`, puis compiler et lancer les nœuds.
4. Vérifier le protocole série avec le firmware sauvegardé.
5. Faire fonctionner les capteurs, la navigation et le Supervisor ensemble.
6. Relier la demande HMI à la logique de navigation.
7. Tester la sécurité et le comportement physique.
8. Documenter les résultats et préparer le gel du prototype.

## 10. Scénarios physiques à valider

1. Obstacle frontal → arrêt.
2. Centre bloqué, gauche libre, droite bloquée → gauche.
3. Centre bloqué, gauche bloquée, droite libre → droite.
4. Les deux côtés libres → choix déterministe.
5. Toutes les directions bloquées → état bloqué et arrêt sûr.
6. Après virage → recontrôle avant reprise de l'avance.

Si la navigation complète n'est pas stable vers le 18 octobre, réduire le scénario de démonstration à ce qui peut être validé sans danger.

## 11. Roadmap

- 14–16 octobre : sécuriser les fichiers, intégrer progressivement le code V0.8 et vérifier le build.
- 17–19 octobre : relier HMI, traitement ROS 2 et Supervisor ; décider du scénario démontrable.
- 20–22 octobre : essais d'intégration et mesures.
- 23–25 octobre : corrections, captures, sauvegarde et gel du prototype.
- 26–31 octobre : finaliser le manuscrit, objectif environ 90 pages.
- 1–10 novembre : préparation et répétitions de soutenance.
- 11 novembre : soutenance prévue.

Préserver huit heures de sommeil.
Ne pas ajouter de fonctionnalités optionnelles avant que le scénario principal soit stable.

## 12. Règles de reprise

- Inspecter avant de modifier.
- Travailler une commande à la fois.
- Attendre la sortie avant de poursuivre.
- Préserver les branches originales et les fichiers locaux.
- Distinguer tests simulés, réception ROS 2 et comportement physique.
- Ne déclarer une étape terminée que lorsque sa preuve a été observée.

**Prochaine action :** vérifier le contenu du checkpoint, puis examiner l'état Git avant d'enregistrer les dossiers `docs/` et `firmware/`.
