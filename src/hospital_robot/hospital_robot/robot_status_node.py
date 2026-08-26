import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class RobotStatusNode(Node):

    def __init__(self):
        super().__init__('robot_status_node')

        self.status = 'IDLE'

        self.publisher = self.create_publisher(
            String,
            '/robot/status',
            10
        )

        self.timer = self.create_timer(
            1.0,
            self.publish_status
        )

        self.get_logger().info(
            'HIAR Robot Status Node started'
        )

    def publish_status(self):

        message = String()
        message.data = self.status

        self.publisher.publish(message)

        self.get_logger().info(
            f'Robot status: {self.status}'
        )


def main(args=None):

    rclpy.init(args=args)

    node = RobotStatusNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()