import pytest
import rclpy
from std_msgs.msg import String

from hospital_robot.hmi_request_node import HMIRequestReceiver


@pytest.fixture
def receiver(monkeypatch):
    initialized_here = not rclpy.ok()

    if initialized_here:
        rclpy.init()

    node = HMIRequestReceiver()
    statuses = []
    monkeypatch.setattr(node, "publish_status", statuses.append)

    yield node, statuses

    node.destroy_node()

    if initialized_here and rclpy.ok():
        rclpy.shutdown()


def send_request(node, payload):
    message = String()
    message.data = payload
    node.request_callback(message)


def test_valid_pharmacy_request_is_accepted(receiver):
    node, statuses = receiver

    send_request(
        node,
        '{"category": "ORIENTATION", "destination": "PHARMACY"}',
    )

    assert statuses == ["VALIDATED:ORIENTATION:PHARMACY"]


def test_unknown_destination_is_rejected(receiver):
    node, statuses = receiver

    send_request(
        node,
        '{"category": "ORIENTATION", "destination": "CAFETERIA"}',
    )

    assert statuses == ["REJECTED:UNKNOWN_OR_UNAVAILABLE_ITEM"]


def test_unavailable_vital_signs_are_rejected(receiver):
    node, statuses = receiver

    send_request(
        node,
        '{"category": "CONSULTATION", "action": "VITAL_SIGNS"}',
    )

    assert statuses == ["REJECTED:UNKNOWN_OR_UNAVAILABLE_ITEM"]


def test_invalid_json_is_rejected(receiver):
    node, statuses = receiver

    send_request(node, '{"category":')

    assert statuses == ["REJECTED:INVALID_JSON"]


def test_unexpected_field_is_rejected(receiver):
    node, statuses = receiver

    send_request(
        node,
        '{"category": "ORIENTATION", '
        '"destination": "PHARMACY", "command": "FORWARD"}',
    )

    assert statuses == ["REJECTED:INVALID_FIELDS"]
