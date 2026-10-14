"""Pont HMI vers ROS2 : publie les demandes validées sur /hmi/request.

Si rclpy n'est pas disponible (tests, PC sans ROS2), le pont reste inactif
et l'interface continue de fonctionner normalement.
"""
import json
import threading

TOPIC = "/hmi/request"

try:
    import rclpy
    from std_msgs.msg import String
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False


class RosBridge:
    def __init__(self):
        self._node = None
        self._publisher = None
        self._lock = threading.Lock()
        self.error = None

    @property
    def active(self):
        return self._publisher is not None

    def start(self):
        """Démarre le node ROS2. Retourne True si le pont est actif."""
        if not ROS_AVAILABLE:
            self.error = "rclpy indisponible (ROS2 non chargé)"
            return False
        try:
            rclpy.init()
            self._node = rclpy.create_node("hmi_bridge")
            self._publisher = self._node.create_publisher(String, TOPIC, 10)
            return True
        except Exception as err:
            self.error = str(err)
            return False

    def publish(self, request_dict):
        """Publie la demande (JSON).

        Retourne True si l'appel de publication réussit, False sinon.
        Cela ne garantit pas la réception ou l'exécution par le robot.
        """
        if not self.active:
            self.error = "Pont ROS2 inactif"
            return False

        try:
            message = String()
            message.data = json.dumps(request_dict, ensure_ascii=False)
            with self._lock:
                self._publisher.publish(message)
            self.error = None
            return True
        except Exception as err:
            self.error = str(err)
            return False

    def stop(self):
        if self._node is not None:
            self._node.destroy_node()
            self._node = None
            self._publisher = None
            rclpy.shutdown()
