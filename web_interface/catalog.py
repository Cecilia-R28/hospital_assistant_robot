"""Catalogue des services HIAR : catégories -> éléments.

Source unique utilisée par l'interface (V0.9) et par la
construction des demandes structurées (V0.10).
"""

CATALOG = {
    "CONSULTATION": {
        "label": "Consultation",
        "icon": "🩺",
        "field": "action",
        "items": {
            "APPOINTMENT": {"label": "Prendre rendez-vous", "available": True},
            "VITAL_SIGNS": {"label": "Mesurer mes signes vitaux", "available": False},
        },
    },
    "ORIENTATION": {
        "label": "Orientation",
        "icon": "🧭",
        "field": "destination",
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
        "items": {
            "HIV": {"label": "VIH / SIDA", "available": True},
            "MALARIA": {"label": "Paludisme", "available": True},
            "DIABETES": {"label": "Diabète", "available": True},
            "HYPERTENSION": {"label": "Hypertension", "available": True},
        },
    },
}
