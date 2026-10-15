
import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32
from std_msgs.msg import Int32
from std_msgs.msg import String


# ============================================================
# CONFIGURATION
# ============================================================

# Distance minimale considérée comme libre devant le robot
OBSTACLE_CM = 20.0

# Fraîcheur maximale d'une mesure ultrason
CENTER_TIMEOUT_S = 2.0

# Fraîcheur maximale des états IR
IR_TIMEOUT_S = 1.0

# Intervalle entre deux vérifications
LOOP_PERIOD_S = 0.1

# Intervalle minimum entre deux FORWARD
FORWARD_RESEND_S = 0.5

# Durée d'une rotation courte
TURN_DURATION_S = 0.6

# Temps d'arrêt avant de relire les capteurs
RECHECK_DELAY_S = 0.2

# Nombre de lectures IR identiques nécessaires
# avant de considérer l'état comme stable
IR_STABLE_COUNT = 2


# ============================================================
# NAVIGATION DECISION NODE
# ============================================================

class NavigationDecision(Node):

    def __init__(self):

        super().__init__('navigation_decision')

        # ----------------------------------------------------
        # État général
        # ----------------------------------------------------

        self.state = 'IDLE'

        # Moment où l'état courant a commencé
        self.state_start_time = self.now()

        # ----------------------------------------------------
        # ULTRASON AVANT
        # ----------------------------------------------------

        self.center_distance = None
        self.last_center_time = 0.0

        # ----------------------------------------------------
        # IR GAUCHE
        # 1 = CLEAR
        # 0 = OBSTACLE
        # ----------------------------------------------------

        self.ir_left_state = None
        self.ir_left_candidate = None
        self.ir_left_count = 0
        self.last_ir_left_time = 0.0

        # ----------------------------------------------------
        # IR DROIT
        # 1 = CLEAR
        # 0 = OBSTACLE
        # ----------------------------------------------------

        self.ir_right_state = None
        self.ir_right_candidate = None
        self.ir_right_count = 0
        self.last_ir_right_time = 0.0

        # ----------------------------------------------------
        # Gestion des mouvements
        # ----------------------------------------------------

        self.last_forward_sent = 0.0

        # Permet d'éviter d'envoyer STOP toutes les 100 ms
        self.sensor_stop_sent = False

        # Direction actuelle de rotation
        self.turn_direction = None

        # ----------------------------------------------------
        # Subscriptions
        # ----------------------------------------------------

        # Ultrason frontal
        self.create_subscription(
            Float32,
            '/sensors/ultrasonic',
            self.center_callback,
            10
        )

        # IR gauche
        self.create_subscription(
            Int32,
            '/sensors/ir_left',
            self.ir_left_callback,
            10
        )

        # IR droit
        self.create_subscription(
            Int32,
            '/sensors/ir_right',
            self.ir_right_callback,
            10
        )

        # Statut ESP32
        self.create_subscription(
            String,
            '/esp32/status',
            self.esp32_status_callback,
            10
        )

        # Commande navigation
        self.create_subscription(
            String,
            '/navigation/command',
            self.nav_command_callback,
            10
        )

        # ----------------------------------------------------
        # Publications
        # ----------------------------------------------------

        self.command_publisher = self.create_publisher(
            String,
            '/robot/command',
            10
        )

        self.decision_publisher = self.create_publisher(
            String,
            '/navigation/decision',
            10
        )

        self.status_publisher = self.create_publisher(
            String,
            '/navigation/status',
            10
        )

        # ----------------------------------------------------
        # Boucle principale
        # ----------------------------------------------------

        self.create_timer(
            LOOP_PERIOD_S,
            self.step
        )

        self.get_logger().info(
            'Navigation decision node started.'
        )

        self.get_logger().info(
            'Sensors: FRONT ultrasonic + LEFT/RIGHT IR.'
        )

    # ========================================================
    # TEMPS
    # ========================================================

    def now(self):

        return self.get_clock().now().nanoseconds / 1e9

    # ========================================================
    # ENVOI COMMANDE ROBOT
    # ========================================================

    def send(self, command):

        message = String()
        message.data = command

        self.command_publisher.publish(message)

        self.get_logger().info(
            f'Navigation command: {command}'
        )

    # ========================================================
    # PUBLICATION TEXTE
    # ========================================================

    def publish_text(self, publisher, text):

        message = String()
        message.data = text

        publisher.publish(message)

    # ========================================================
    # CHANGEMENT D'ÉTAT
    # ========================================================

    def change_state(self, new_state):

        if self.state == new_state:
            return

        self.get_logger().info(
            f'State: {self.state} -> {new_state}'
        )

        self.state = new_state

        # Mémorise le début du nouvel état
        self.state_start_time = self.now()

    # ========================================================
    # CALLBACK ULTRASON AVANT
    # ========================================================

    def center_callback(self, message):

        distance = float(message.data)

        # Mesure invalide
        if distance <= 0.0:
            return

        self.center_distance = distance
        self.last_center_time = self.now()

    # ========================================================
    # CALLBACK IR GAUCHE
    # ========================================================

    def ir_left_callback(self, message):

        state = int(message.data)

        if state not in [0, 1]:

            self.get_logger().warning(
                f'Invalid LEFT IR state: {state}'
            )

            return

        self.last_ir_left_time = self.now()

        # Première valeur
        if self.ir_left_candidate is None:

            self.ir_left_candidate = state
            self.ir_left_count = 1

            return

        # Même valeur que la candidate
        if state == self.ir_left_candidate:

            self.ir_left_count += 1

        # Nouvelle valeur
        else:

            self.ir_left_candidate = state
            self.ir_left_count = 1

        # État considéré stable
        if self.ir_left_count >= IR_STABLE_COUNT:

            self.ir_left_state = self.ir_left_candidate

    # ========================================================
    # CALLBACK IR DROIT
    # ========================================================

    def ir_right_callback(self, message):

        state = int(message.data)

        if state not in [0, 1]:

            self.get_logger().warning(
                f'Invalid RIGHT IR state: {state}'
            )

            return

        self.last_ir_right_time = self.now()

        # Première valeur
        if self.ir_right_candidate is None:

            self.ir_right_candidate = state
            self.ir_right_count = 1

            return

        # Même valeur que la candidate
        if state == self.ir_right_candidate:

            self.ir_right_count += 1

        # Nouvelle valeur
        else:

            self.ir_right_candidate = state
            self.ir_right_count = 1

        # État considéré stable
        if self.ir_right_count >= IR_STABLE_COUNT:

            self.ir_right_state = self.ir_right_candidate

    # ========================================================
    # CALLBACK STATUT ESP32
    # ========================================================

    def esp32_status_callback(self, message):

        text = message.data.strip().upper()

        # L'ESP32 signale un obstacle pendant l'avance.
        if 'OBSTACLE' in text and self.state == 'FORWARD':

            self.get_logger().warning(
                f'ESP32 safety reported: {message.data}'
            )

            self.send('STOP')

            self.change_state('DECIDE')

    # ========================================================
    # COMMANDE START / STOP
    # ========================================================

    def nav_command_callback(self, message):

        command = message.data.strip().upper()

        # ----------------------------------------------------
        # START
        # ----------------------------------------------------

        if command == 'START':

            if self.state == 'IDLE':

                self.last_forward_sent = 0.0
                self.sensor_stop_sent = False
                self.turn_direction = None

                self.publish_text(
                    self.status_publisher,
                    'RUNNING'
                )

                self.change_state('FORWARD')

                self.get_logger().info(
                    'Navigation started.'
                )

            else:

                self.get_logger().info(
                    f'START ignored: '
                    f'robot already active ({self.state}).'
                )

        # ----------------------------------------------------
        # STOP
        # ----------------------------------------------------

        elif command == 'STOP':

            self.send('STOP')

            self.publish_text(
                self.status_publisher,
                'IDLE'
            )

            self.change_state('IDLE')

            self.sensor_stop_sent = False
            self.turn_direction = None

            self.get_logger().info(
                'Navigation stopped.'
            )

        # ----------------------------------------------------
        # COMMANDE INCONNUE
        # ----------------------------------------------------

        else:

            self.get_logger().warning(
                f'Unknown navigation command: {command}'
            )

    # ========================================================
    # VÉRIFICATION DES CAPTEURS
    # ========================================================

    def sensors_ready(self):

        current_time = self.now()

        # Ultrason disponible ?
        center_ready = (
            self.center_distance is not None
            and
            current_time - self.last_center_time
            <= CENTER_TIMEOUT_S
        )

        # IR gauche disponible ?
        left_ready = (
            self.ir_left_state is not None
            and
            current_time - self.last_ir_left_time
            <= IR_TIMEOUT_S
        )

        # IR droit disponible ?
        right_ready = (
            self.ir_right_state is not None
            and
            current_time - self.last_ir_right_time
            <= IR_TIMEOUT_S
        )

        return center_ready and left_ready and right_ready

    # ========================================================
    # DÉCISION DE NAVIGATION
    # ========================================================

    def decide(self):

        center = self.center_distance

        left = self.ir_left_state
        right = self.ir_right_state

        # ----------------------------------------------------
        # DEVANT LIBRE
        # ----------------------------------------------------

        if center > OBSTACLE_CM:

            return 'FORWARD'

        # ----------------------------------------------------
        # DEVANT BLOQUÉ
        # ----------------------------------------------------

        # Gauche = libre
        # Droite = obstacle
        if left == 1 and right == 0:

            return 'LEFT'

        # Gauche = obstacle
        # Droite = libre
        if left == 0 and right == 1:

            return 'RIGHT'

        # Gauche = libre
        # Droite = libre
        #
        # Choix déterministe :
        # priorité à gauche.
        if left == 1 and right == 1:

            return 'LEFT'

        # Gauche = obstacle
        # Droite = obstacle
        if left == 0 and right == 0:

            return 'STOP'

        return 'STOP'

    # ========================================================
    # BOUCLE PRINCIPALE
    # ========================================================

    def step(self):

        # ====================================================
        # IDLE
        # ====================================================

        if self.state == 'IDLE':

            return

        current_time = self.now()

        # ====================================================
        # FORWARD
        # ====================================================

        if self.state == 'FORWARD':

            # ------------------------------------------------
            # Vérifier la fraîcheur des capteurs
            # ------------------------------------------------

            if not self.sensors_ready():

                # STOP envoyé une seule fois
                if not self.sensor_stop_sent:

                    self.send('STOP')

                    self.sensor_stop_sent = True

                    self.publish_text(
                        self.status_publisher,
                        'SENSOR_NOT_READY'
                    )

                    self.get_logger().warning(
                        'Waiting for fresh sensor data.'
                    )

                return

            # Capteurs de nouveau disponibles
            self.sensor_stop_sent = False

            # ------------------------------------------------
            # Obstacle frontal
            # ------------------------------------------------

            if self.center_distance <= OBSTACLE_CM:

                self.send('STOP')

                self.publish_text(
                    self.decision_publisher,
                    'OBSTACLE'
                )

                self.get_logger().warning(
                    f'Obstacle detected: '
                    f'{self.center_distance:.1f} cm'
                )

                self.change_state('DECIDE')

                return

            # ------------------------------------------------
            # Envoi périodique de FORWARD
            # ------------------------------------------------

            if (
                current_time - self.last_forward_sent
                >= FORWARD_RESEND_S
            ):

                self.send('FORWARD')

                self.last_forward_sent = current_time

            return

        # ====================================================
        # DECIDE
        # ====================================================

        if self.state == 'DECIDE':

            # Les capteurs doivent être valides avant décision
            if not self.sensors_ready():

                if not self.sensor_stop_sent:

                    self.send('STOP')

                    self.sensor_stop_sent = True

                    self.publish_text(
                        self.status_publisher,
                        'SENSOR_NOT_READY'
                    )

                    self.get_logger().warning(
                        'Waiting for fresh sensor data.'
                    )

                return

            self.sensor_stop_sent = False

            decision = self.decide()

            self.publish_text(
                self.decision_publisher,
                decision
            )

            self.get_logger().info(
                f'RECHECK: '
                f'FRONT={self.center_distance:.1f} cm | '
                f'LEFT={self.ir_left_state} | '
                f'RIGHT={self.ir_right_state} | '
                f'DECISION={decision}'
            )

            # ------------------------------------------------
            # Devant libre
            # ------------------------------------------------

            if decision == 'FORWARD':

                self.change_state('FORWARD')

                return

            # ------------------------------------------------
            # Tourner à gauche
            # ------------------------------------------------

            if decision == 'LEFT':

                self.send('STOP')

                self.turn_direction = 'LEFT'

                self.send('LEFT')

                self.change_state('TURN_LEFT')

                return

            # ------------------------------------------------
            # Tourner à droite
            # ------------------------------------------------

            if decision == 'RIGHT':

                self.send('STOP')

                self.turn_direction = 'RIGHT'

                self.send('RIGHT')

                self.change_state('TURN_RIGHT')

                return

            # ------------------------------------------------
            # Bloqué
            # ------------------------------------------------

            if decision == 'STOP':

                self.send('STOP')

                self.publish_text(
                    self.status_publisher,
                    'BLOCKED'
                )

                self.get_logger().warning(
                    'Robot blocked: '
                    'LEFT and RIGHT obstacles.'
                )

                return

        # ====================================================
        # TURN LEFT
        # ====================================================

        if self.state == 'TURN_LEFT':

            elapsed = current_time - self.state_start_time

            if elapsed >= TURN_DURATION_S:

                self.send('STOP')

                self.turn_direction = None

                self.change_state('RECHECK')

            return

        # ====================================================
        # TURN RIGHT
        # ====================================================

        if self.state == 'TURN_RIGHT':

            elapsed = current_time - self.state_start_time

            if elapsed >= TURN_DURATION_S:

                self.send('STOP')

                self.turn_direction = None

                self.change_state('RECHECK')

            return

        # ====================================================
        # RECHECK
        # ====================================================

        if self.state == 'RECHECK':

            elapsed = current_time - self.state_start_time

            if elapsed >= RECHECK_DELAY_S:

                self.change_state('DECIDE')

            return

    # ========================================================
    # FERMETURE
    # ========================================================

    def stop_robot(self):

        self.send('STOP')


# ============================================================
# MAIN
# ============================================================

def main(args=None):

    rclpy.init(args=args)

    node = NavigationDecision()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        node.get_logger().info(
            'Navigation decision node stopped by user.'
        )

    finally:

        if rclpy.ok():

            node.stop_robot()

        node.destroy_node()

        if rclpy.ok():

            rclpy.shutdown()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == '__main__':

    main()
