"""Récepteur et validateur des demandes de l'interface HMI HIAR."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


VALID_REQUESTS = {
    "ORIENTATION": {
        "field": "destination",
        "items": {"PHARMACY", "LABORATORY", "RECEPTION"},
    },
    "CONSULTATION": {
        "field": "action",
        "items": {"APPOINTMENT"},
    },
    "INFORMATION": {
        "field": "topic",
        "items": {"HIV", "MALARIA", "DIABETES", "HYPERTENSION"},
    },
}


class HMIRequestReceiver(Node):
    """Valide les demandes HMI sans commander directement les moteurs."""

    def __init__(self):
        super().__init__("hmi_request_receiver")

        self.status_publisher = self.create_publisher(
            String,
            "/hmi/status",
            10,
        )

        # Canal de demande d'orientation ; ne commande pas les moteurs.
        self.navigation_request_publisher = self.create_publisher(
            String,
            "/navigation/request",
            10,
        )

        self.request_subscription = self.create_subscription(
            String,
            "/hmi/request",
            self.request_callback,
            10,
        )

        self.get_logger().info(
            "HMI request receiver started; no motor commands are issued."
        )

    def publish_status(self, status):
        message = String()
        message.data = status
        self.status_publisher.publish(message)

    def publish_navigation_request(self, request):
        """Publie une demande d'orientation validée, sans lancer le robot."""
        message = String()
        message.data = json.dumps(request, separators=(",", ":"))
        self.navigation_request_publisher.publish(message)

    def reject(self, reason):
        self.get_logger().warning(f"HMI request rejected: {reason}")
        self.publish_status(f"REJECTED:{reason}")

    def request_callback(self, message):
        try:
            request = json.loads(message.data)
        except (json.JSONDecodeError, TypeError):
            self.reject("INVALID_JSON")
            return

        if not isinstance(request, dict):
            self.reject("INVALID_FORMAT")
            return

        category = request.get("category")
        if not isinstance(category, str):
            self.reject("INVALID_CATEGORY")
            return

        category = category.upper()
        schema = VALID_REQUESTS.get(category)
        if schema is None:
            self.reject("UNKNOWN_CATEGORY")
            return

        field = schema["field"]
        if set(request.keys()) != {"category", field}:
            self.reject("INVALID_FIELDS")
            return

        item = request.get(field)
        if not isinstance(item, str):
            self.reject("INVALID_ITEM")
            return

        item = item.upper()
        if item not in schema["items"]:
            self.reject("UNKNOWN_OR_UNAVAILABLE_ITEM")
            return

        normalized_request = {"category": category, field: item}

        if category == "ORIENTATION":
            self.publish_navigation_request(normalized_request)
            self.get_logger().info(
                "Orientation request published on /navigation/request. "
                "No movement command has been issued."
            )

        self.get_logger().info(
            f"Validated HMI request: category={category}, {field}={item}."
        )
        self.publish_status(f"VALIDATED:{category}:{item}")


def main(args=None):
    rclpy.init(args=args)
    node = HMIRequestReceiver()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
