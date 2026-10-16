from unittest.mock import MagicMock

from hospital_robot.navigation_decision_node import NavigationDecision


def make_node(state):
    node = MagicMock()
    node.state = state
    node.now.return_value = 100.0
    node.state_start_time = 99.0
    node.center_distance = 10.0
    node.ir_left_state = 0
    node.ir_right_state = 0
    node.sensor_stop_sent = False
    node.turn_direction = None
    return node


def test_decide_enters_blocked_when_both_ir_sensors_are_blocked():
    node = make_node("DECIDE")
    node.sensors_ready.return_value = True
    node.decide.return_value = "STOP"

    NavigationDecision.step(node)

    node.send.assert_called_once_with("STOP")
    node.change_state.assert_called_once_with("BLOCKED")
    assert node.publish_text.call_count == 2


def test_blocked_does_not_resume_when_sensors_are_stale():
    node = make_node("BLOCKED")
    node.sensors_ready.return_value = False

    NavigationDecision.step(node)

    node.send.assert_not_called()
    node.change_state.assert_not_called()


def test_blocked_stays_blocked_when_both_directions_remain_blocked():
    node = make_node("BLOCKED")
    node.sensors_ready.return_value = True
    node.decide.return_value = "STOP"

    NavigationDecision.step(node)

    node.send.assert_not_called()
    node.change_state.assert_not_called()


def test_blocked_returns_to_decide_when_a_direction_is_safe():
    node = make_node("BLOCKED")
    node.sensors_ready.return_value = True
    node.decide.return_value = "LEFT"

    NavigationDecision.step(node)

    node.change_state.assert_called_once_with("DECIDE")
    node.send.assert_not_called()


def make_request_node(state="IDLE"):
    node = make_node(state)
    node.destination = None
    node.status_publisher = MagicMock()
    node.publish_text = MagicMock()
    node.get_logger = MagicMock()
    return node


def test_valid_navigation_request_stores_destination_without_movement():
    import json
    from std_msgs.msg import String

    node = make_request_node()
    message = String()
    message.data = json.dumps({
        "category": "ORIENTATION",
        "destination": "PHARMACY",
    })

    NavigationDecision.navigation_request_callback(node, message)

    assert node.destination == "PHARMACY"
    assert node.state == "IDLE"
    node.send.assert_not_called()
    node.publish_text.assert_called_once_with(
        node.status_publisher,
        "REQUEST_RECEIVED:PHARMACY",
    )


def test_invalid_navigation_destination_is_rejected():
    from std_msgs.msg import String

    node = make_request_node()
    message = String()
    message.data = (
        '{"category":"ORIENTATION","destination":"CAFETERIA"}'
    )

    NavigationDecision.navigation_request_callback(node, message)

    assert node.destination is None
    assert node.state == "IDLE"
    node.send.assert_not_called()
    node.publish_text.assert_not_called()
    node.get_logger().warning.assert_called_once()


def test_invalid_navigation_request_json_is_rejected():
    from std_msgs.msg import String

    node = make_request_node()
    message = String()
    message.data = '{"category":'

    NavigationDecision.navigation_request_callback(node, message)

    assert node.destination is None
    assert node.state == "IDLE"
    node.send.assert_not_called()
    node.publish_text.assert_not_called()
    node.get_logger().warning.assert_called_once()
