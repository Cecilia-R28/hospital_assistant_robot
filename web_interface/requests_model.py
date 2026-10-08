"""Construction des demandes structurées HIAR (V0.10)."""

from catalog import CATALOG


def build_request(category, item):
    """Retourne la demande structurée, ou lève ValueError si inconnue.

    Exemple : build_request("ORIENTATION", "PHARMACY")
    -> {"category": "ORIENTATION", "destination": "PHARMACY"}
    """
    if category not in CATALOG:
        raise ValueError(f"Catégorie inconnue : {category}")
    entry = CATALOG[category]
    if item not in entry["items"]:
        raise ValueError(f"Élément inconnu pour {category} : {item}")
    return {"category": category, entry["field"]: item}
