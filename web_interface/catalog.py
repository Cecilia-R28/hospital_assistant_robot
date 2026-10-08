"""Catalogue des services HIAR : catégories -> éléments.

Source unique utilisée par l'interface (V0.9) et par la
construction des demandes structurées (V0.10).
"""

INFO_DISCLAIMER = (
    "Information générale non diagnostique. "
    "Elle ne remplace pas l'avis d'un professionnel de santé."
)

CATALOG = {
    "CONSULTATION": {
        "label": "Consultation",
        "icon": "🩺",
        "field": "action",
        "confirm": "Demande enregistrée : {label}.",
        "items": {
            "APPOINTMENT": {"label": "Prendre rendez-vous", "available": True},
            "VITAL_SIGNS": {"label": "Mesurer mes signes vitaux", "available": False},
        },
    },
    "ORIENTATION": {
        "label": "Orientation",
        "icon": "🧭",
        "field": "destination",
        "confirm": "Je vous accompagne vers : {label}.",
        "items": {
            "PHARMACY": {"label": "Pharmacie", "icon": "💊", "available": True},
            "LABORATORY": {"label": "Laboratoire", "icon": "🧪", "available": True},
            "RECEPTION": {"label": "Accueil / Réception", "icon": "🏥", "available": True},
        },
    },
    "INFORMATION": {
        "label": "Renseignements",
        "icon": "ℹ️",
        "field": "topic",
        "confirm": "Fiche d'information : {label}.",
        "items": {
            "HIV": {
                "label": "VIH / SIDA",
                "available": True,
                "info": (
                    "Le VIH est un virus qui affaiblit les défenses du corps.\n"
                    "Il se transmet par des rapports sexuels non protégés, par le sang "
                    "(aiguilles, matériel non stérile) et de la mère à l'enfant.\n"
                    "Il ne se transmet pas par une poignée de main, un baiser ou un repas partagé.\n"
                    "Seul un test de dépistage permet de savoir : demandez-le dans un centre de santé.\n"
                    "Un traitement existe et permet de vivre longtemps en bonne santé."
                ),
            },
            "MALARIA": {
                "label": "Paludisme",
                "available": True,
                "info": (
                    "Le paludisme est transmis par la piqûre de certains moustiques, surtout la nuit.\n"
                    "Signes fréquents : fièvre, frissons, maux de tête, courbatures.\n"
                    "Prévention : dormir sous une moustiquaire, éviter les eaux stagnantes.\n"
                    "En cas de fièvre, consultez vite un centre de santé pour faire un test, "
                    "surtout pour un enfant ou une femme enceinte."
                ),
            },
            "DIABETES": {
                "label": "Diabète",
                "available": True,
                "info": (
                    "Le diabète est une maladie où le taux de sucre dans le sang reste trop élevé.\n"
                    "Signes possibles : grande soif, besoin d'uriner souvent, fatigue, "
                    "perte de poids inexpliquée.\n"
                    "Seule une mesure de la glycémie par un professionnel permet de savoir.\n"
                    "Une alimentation équilibrée, de l'activité physique et un suivi médical "
                    "aident à réduire le risque et à mieux le contrôler."
                ),
            },
            "HYPERTENSION": {
                "label": "Hypertension",
                "available": True,
                "info": (
                    "L'hypertension est une pression du sang trop forte dans les artères.\n"
                    "Elle ne donne souvent aucun signe : il faut faire mesurer sa tension régulièrement.\n"
                    "Non soignée, elle augmente le risque d'AVC, de crise cardiaque "
                    "et de problèmes aux reins.\n"
                    "Moins de sel, de l'activité physique, pas de tabac et un suivi médical "
                    "aident à la maîtriser."
                ),
            },
        },
    },
}
