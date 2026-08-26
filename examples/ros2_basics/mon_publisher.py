import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MonPublisher(Node):
    def __init__(self):
        super().__init__('mon_publisher')
        self.publisher_ = self.create_publisher(String, 'topic_test', 10)
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.compteur = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Message numero {self.compteur}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publie: {msg.data}')
        self.compteur += 1

def main(args=None):
    rclpy.init(args=args)
    node = MonPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
