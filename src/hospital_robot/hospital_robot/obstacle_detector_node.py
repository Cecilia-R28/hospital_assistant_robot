import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32
from std_msgs.msg import String


class ObstacleDetector(Node):

    def __init__(self):
        super().__init__('obstacle_detector')

        # Seuil de détection provisoire
        self.obstacle_threshold_cm = 20.0

        # Souscription aux mesures ultrasoniques
        self.ultrasonic_subscription = self.create_subscription(
            Float32,
            '/sensors/ultrasonic',
            self.ultrasonic_callback,
            10
        )

        # Publication de l'état de détection
        self.obstacle_publisher = self.create_publisher(
            String,
            '/sensors/obstacle',
            10
        )

        self.get_logger().info(
            'Obstacle detector started.'
        )

        self.get_logger().info(
            f'Obstacle threshold: '
            f'{self.obstacle_threshold_cm:.1f} cm'
        )

    def ultrasonic_callback(self, message):

        distance = message.data

        if distance <= 0.0:
            self.get_logger().warning(
                f'Invalid distance received: {distance:.2f} cm'
            )
            return

        if distance < self.obstacle_threshold_cm:

            state = 'OBSTACLE'

        else:

            state = 'CLEAR'

        obstacle_message = String()
        obstacle_message.data = state

        self.obstacle_publisher.publish(
            obstacle_message
        )

        self.get_logger().info(
            f'Distance: {distance:.1f} cm -> {state}'
        )


def main(args=None):

    rclpy.init(args=args)

    node = ObstacleDetector()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        node.get_logger().info(
            'Obstacle detector stopped by user.'
        )

    finally:

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
