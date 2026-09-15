import serial

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ESP32Interface(Node):

    def __init__(self):
        super().__init__('esp32_interface')

        # Configuration série
        self.port = '/dev/ttyUSB0'
        self.baudrate = 115200

        # Connexion à l'ESP32
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )

            self.get_logger().info(
                f'Connected to ESP32 on {self.port}'
            )

        except serial.SerialException as error:
            self.serial_connection = None

            self.get_logger().error(
                f'Unable to connect to ESP32: {error}'
            )

        # Réception des commandes venant du système ROS2
        self.command_subscription = self.create_subscription(
            String,
            '/robot/command',
            self.command_callback,
            10
        )

        # Publication de l'état de l'ESP32
        self.status_publisher = self.create_publisher(
            String,
            '/esp32/status',
            10
        )

        self.get_logger().info(
            'ESP32 interface node started.'
        )

    def command_callback(self, message):

        command = message.data.strip().upper()

        allowed_commands = [
            'FORWARD',
            'BACKWARD',
            'LEFT',
            'RIGHT',
            'STOP'
        ]

        if command not in allowed_commands:
            self.get_logger().warning(
                f'Invalid command rejected: {command}'
            )
            return

        if self.serial_connection is None:
            self.get_logger().error(
                'ESP32 is not connected.'
            )
            return

        try:
            # Envoi de la commande à l'ESP32
            self.serial_connection.write(
                f'{command}\n'.encode('utf-8')
            )

            self.get_logger().info(
                f'Sent to ESP32: {command}'
            )

            # Attente de la réponse de l'ESP32
            response = self.serial_connection.readline()

            if response:

                response = response.decode(
                    'utf-8',
                    errors='replace'
                ).strip()

                self.get_logger().info(
                    f'ESP32 response: {response}'
                )

                # Réponse attendue
                expected_response = f'ACK:{command}'

                # Vérification de l'ACK
                if response == expected_response:

                    self.get_logger().info(
                        f'Command confirmed by ESP32: {command}'
                    )

                    status_message = String()
                    status_message.data = response

                    self.status_publisher.publish(
                        status_message
                    )

                else:

                    self.get_logger().error(
                        f'Unexpected ESP32 response: {response}. '
                        f'Expected: {expected_response}'
                    )

            else:

                self.get_logger().error(
                    f'No response from ESP32 for command: {command}'
                )

        except serial.SerialException as error:

            self.get_logger().error(
                f'Serial communication error: {error}'
            )

            self.get_logger().error(
                'Communication with ESP32 lost. '
                'Robot must STOP.'
            )

            self.close_serial_connection()

    def close_serial_connection(self):

        if self.serial_connection is not None:

            try:
                self.serial_connection.close()

                self.get_logger().info(
                    'ESP32 serial connection closed.'
                )

            except serial.SerialException as error:

                self.get_logger().error(
                    f'Error while closing serial connection: {error}'
                )

            finally:
                self.serial_connection = None


def main(args=None):

    rclpy.init(args=args)

    node = ESP32Interface()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:

        node.get_logger().info(
            'ESP32 interface node stopped by user.'
        )

    finally:

        node.close_serial_connection()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()