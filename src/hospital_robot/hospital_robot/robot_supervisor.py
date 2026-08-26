import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class RobotSupervisor(Node):

    def __init__(self):
        super().__init__('robot_supervisor')

        self.subscription = self.create_subscription(
            String,
            '/robot/status',
            self.status_callback,
            10
        )

        self.get_logger().info(
            'HIAR Robot Supervisor started'
        )

    def status_callback(self, message):

        status = message.data

        self.get_logger().info(
            f'Received robot status: {status}'
        )


def main(args=None):

    rclpy.init(args=args)

    node = RobotSupervisor()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()