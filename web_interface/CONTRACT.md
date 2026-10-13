# Contrat HMI vers ROS2 (V0.10)

Statut : défini, pas encore implémenté (nécessite le package hospital_robot, après fusion avec V0.8).

## Topic

- Nom : `/hmi/request`
- Type : `std_msgs/String`
- Contenu : une demande structurée au format JSON

## Formats

    {"category": "ORIENTATION", "destination": "PHARMACY"}
    {"category": "CONSULTATION", "action": "APPOINTMENT"}
    {"category": "INFORMATION", "topic": "HIV"}

## Valeurs autorisées

- ORIENTATION : PHARMACY, LABORATORY, RECEPTION
- CONSULTATION : APPOINTMENT (VITAL_SIGNS non disponible)
- INFORMATION : HIV, MALARIA, DIABETES, HYPERTENSION

## Règles

- Le HMI ne publie jamais de commande moteur (FORWARD, LEFT, GPIO...) : seulement une intention.
- Une demande ORIENTATION donne une destination ; la navigation décide du mouvement.
- Le Supervisor reste le seul à valider les mouvements.
- Le futur node `hmi_bridge` valide la demande puis la publie, sans rien interpréter.
