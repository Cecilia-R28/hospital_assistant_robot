from enum import Enum

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class RobotState(Enum):
    IDLE = 'IDLE'
    WAITING = 'WAITING'
    NAVIGATING = 'NAVIGATING'
    ARRIVED = 'ARRIVED'
    OBSTACLE = 'OBSTACLE'
    EMERGENCY_STOP = 'EMERGENCY_STOP'
    ERROR = 'ERROR'


class RobotSupervisor(Node):

    def __init__(self):
        super().__init__('robot_supervisor')

        self.current_state = RobotState.IDLE

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

        if status == RobotState.IDLE.value:
            self.current_state = RobotState.IDLE
            self.get_logger().info(
                'Robot is ready and waiting for a task.'
            )

        elif status == RobotState.WAITING.value:
            self.current_state = RobotState.WAITING
            self.get_logger().info(
                'Robot is waiting for an instruction.'
            )

        elif status == RobotState.NAVIGATING.value:
            self.current_state = RobotState.NAVIGATING
            self.get_logger().info(
                'Robot is navigating.'
            )

        elif status == RobotState.ARRIVED.value:
            self.current_state = RobotState.ARRIVED
            self.get_logger().info(
                'Robot has arrived at the destination.'
            )

        elif status == RobotState.OBSTACLE.value:
            self.current_state = RobotState.OBSTACLE
            self.get_logger().warn(
                'Obstacle detected! Robot must stop or avoid it.'
            )

        elif status == RobotState.EMERGENCY_STOP.value:
            self.current_state = RobotState.EMERGENCY_STOP
            self.get_logger().error(
                'EMERGENCY STOP activated!'
            )

        elif status == RobotState.ERROR.value:
            self.current_state = RobotState.ERROR
            self.get_logger().error(
                'Robot entered ERROR state.'
            )

        else:
            self.get_logger().warn(
                f'Unknown robot status: {status}'
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

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()