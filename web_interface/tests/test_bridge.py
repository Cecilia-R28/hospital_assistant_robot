import app as app_module
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


def test_valid_request_is_published(monkeypatch):
    fake = FakeBridge()
    monkeypatch.setattr(app_module, "bridge", fake)
    data = post({"category": "ORIENTATION", "item": "PHARMACY"}).get_json()
    assert data["published"] is True
    assert fake.sent == [{"category": "ORIENTATION", "destination": "PHARMACY"}]


def test_invalid_request_is_never_published(monkeypatch):
    fake = FakeBridge()
    monkeypatch.setattr(app_module, "bridge", fake)
    response = post({"category": "ORIENTATION", "item": "CAFETERIA"})
    assert response.status_code == 400
    assert fake.sent == []
