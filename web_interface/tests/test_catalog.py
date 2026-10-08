import pytest

from catalog import CATALOG
from requests_model import build_request


def test_three_categories():
    assert set(CATALOG) == {"CONSULTATION", "ORIENTATION", "INFORMATION"}


def test_orientation_has_three_destinations():
    assert set(CATALOG["ORIENTATION"]["items"]) == {"PHARMACY", "LABORATORY", "RECEPTION"}


def test_vital_signs_not_available_yet():
    assert CATALOG["CONSULTATION"]["items"]["VITAL_SIGNS"]["available"] is False


def test_build_destination_request():
    assert build_request("ORIENTATION", "PHARMACY") == {
        "category": "ORIENTATION", "destination": "PHARMACY"}


def test_build_action_request():
    assert build_request("CONSULTATION", "APPOINTMENT") == {
        "category": "CONSULTATION", "action": "APPOINTMENT"}


def test_build_topic_request():
    assert build_request("INFORMATION", "HIV") == {
        "category": "INFORMATION", "topic": "HIV"}


def test_unknown_category_is_rejected():
    with pytest.raises(ValueError):
        build_request("PAIEMENT", "PHARMACY")


def test_unknown_item_is_rejected():
    with pytest.raises(ValueError):
        build_request("ORIENTATION", "CAFETERIA")
