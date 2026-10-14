import app as app_module
import ros_bridge as ros_bridge_module
from ros_bridge import RosBridge


class FakeBridge:
    def __init__(self):
        self.sent = []

    def publish(self, request_dict):
        self.sent.append(request_dict)
        return True


def post(payload):
    return app_module.app.test_client().post("/api/request", json=payload)


def test_inactive_bridge_does_not_publish():
    bridge = RosBridge()
    assert bridge.publish({"category": "ORIENTATION", "destination": "PHARMACY"}) is False


def test_publish_exception_is_caught(monkeypatch):
    class FakeMessage:
        data = ""

    class FailingPublisher:
        def publish(self, message):
            raise RuntimeError("Erreur publisher simulée")

    bridge = RosBridge()
    bridge._publisher = FailingPublisher()
    monkeypatch.setattr(ros_bridge_module, "String", FakeMessage, raising=False)

    result = bridge.publish({"category": "ORIENTATION", "destination": "PHARMACY"})

    assert result is False
    assert bridge.error == "Erreur publisher simulée"


def test_valid_request_is_published(monkeypatch):
    fake = FakeBridge()
    monkeypatch.setattr(app_module, "bridge", fake)
    data = post({"category": "ORIENTATION", "item": "PHARMACY"}).get_json()
    assert data["published"] is True
    assert fake.sent == [{"category": "ORIENTATION", "destination": "PHARMACY"}]


def test_publish_failure_is_reported_by_api(monkeypatch):
    class FailingBridge:
        error = "Publication ROS2 échouée"

        def publish(self, request_dict):
            return False

    monkeypatch.setattr(app_module, "bridge", FailingBridge())
    response = post({"category": "ORIENTATION", "item": "PHARMACY"})
    data = response.get_json()

    assert response.status_code == 503
    assert data["ok"] is False
    assert data["published"] is False
    assert data["error"] == "Publication ROS2 échouée"


def test_invalid_request_is_never_published(monkeypatch):
    fake = FakeBridge()
    monkeypatch.setattr(app_module, "bridge", fake)
    response = post({"category": "ORIENTATION", "item": "CAFETERIA"})
    assert response.status_code == 400
    assert fake.sent == []


def test_unavailable_item_is_rejected_by_api(monkeypatch):
    fake = FakeBridge()
    monkeypatch.setattr(app_module, "bridge", fake)

    response = post({"category": "CONSULTATION", "item": "VITAL_SIGNS"})

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert fake.sent == []
