// ============================================
// HIAR V0.8 - ULTRASON + IR GAUCHE/DROITE
// ESP32 + L298N + HC-SR04 + IR LM393
// ESP32 Arduino Core 3.x
//
// Architecture perception V0.8 :
//   HC-SR04  -> obstacle frontal
//   IR gauche -> obstacle côté gauche
//   IR droit  -> obstacle côté droit
//
// IR :
//   1 = CLEAR
//   0 = OBSTACLE
//
// Comportement autonome ajouté :
//   - Devant libre  → FORWARD
//   - Obstacle devant → regarde gauche/droite
//     - gauche libre  → LEFT
//     - droite libre  → RIGHT
//     - les deux libres → préfère LEFT
//     - les deux bloqués → STOP
// ============================================

#include "driver/gpio.h"

// ============================================
// TYPES
// ============================================
enum UsState {
  US_IDLE,
  US_WAITING_ECHO
};

enum MotionMode {
  MODE_IDLE,
  MODE_FORWARD,
  MODE_BACKWARD,
  MODE_LEFT,
  MODE_RIGHT
};

// Déclarations anticipées
void requestMotion(MotionMode mode);
void applyMotion(MotionMode mode);

// ============================================
// MOTEUR A — GAUCHE
// ============================================
const int MOTOR_A_EN  = 25;
const int MOTOR_A_IN1 = 26;
const int MOTOR_A_IN2 = 27;

// ============================================
// MOTEUR B — DROIT
// ============================================
const int MOTOR_B_EN  = 14;
const int MOTOR_B_IN1 = 33;
const int MOTOR_B_IN2 = 32;

// ============================================
// HC-SR04 — AVANT
// ============================================
const int ULTRASONIC_TRIG = 13;
const int ULTRASONIC_ECHO = 34;

const unsigned long ULTRASONIC_TIMEOUT_US      = 25000;
const unsigned long ULTRASONIC_MIN_INTERVAL_US = 60000;

// ============================================
// IR LM393
// ============================================
const int IR_LEFT_PIN  = 18;
const int IR_RIGHT_PIN = 19;

// 1 = CLEAR
// 0 = OBSTACLE
int lastIrLeftState  = -1;
int lastIrRightState = -1;
unsigned long lastIrPublish = 0;
const unsigned long IR_PUBLISH_INTERVAL = 100;

// ============================================
// PWM MOTEURS
// ============================================
const int PWM_FREQ       = 20000;
const int PWM_RESOLUTION = 8;

// ============================================
// VITESSE
// ============================================
const int MOTOR_SPEED_PERCENT = 75;
const int MOTOR_SPEED = (255 * MOTOR_SPEED_PERCENT) / 100;

// ============================================
// SÉCURITÉ
// ============================================
const unsigned long MAX_MOVE_DURATION = 2000;
const float OBSTACLE_STOP_CM = 20.0f;
const int MAX_INVALID_READS = 3;
const unsigned long GUARD_INTERVAL = 60;
const unsigned long REVERSE_PAUSE_MS = 150;

// ============================================
// MODE AUTONOME (désactivé par défaut)
// ============================================
bool autoMode = false;

// ============================================
// RÉCEPTION SÉRIE
// ============================================
const size_t RX_MAX = 32;
char rxBuffer[RX_MAX + 1];
size_t rxLen = 0;
bool rxDiscard = false;

// ============================================
// ULTRASON — ISR
// ============================================
volatile UsState usState = US_IDLE;
volatile unsigned long usEchoStartUs    = 0;
volatile unsigned long usEchoDurationUs = 0;
volatile bool usResultReady = false;
volatile bool usResultValid = false;

unsigned long usTriggerTimeUs = 0;
unsigned long lastUsTriggerUs = 0;

void IRAM_ATTR ultrasonicISR() {
  unsigned long now = micros();
  if (gpio_get_level((gpio_num_t)ULTRASONIC_ECHO) == 1) {
    usEchoStartUs = now;
  } else {
    if (usState == US_WAITING_ECHO) {
      usEchoDurationUs = now - usEchoStartUs;
      usResultValid = true;
      usResultReady = true;
      usState = US_IDLE;
    }
  }
}

void resetUltrasonic() {
  noInterrupts();
  usState = US_IDLE;
  usResultReady = false;
  usResultValid = false;
  interrupts();
}

bool requestUltrasonic() {
  if (usState != US_IDLE)
    return false;

  unsigned long now = micros();
  if (now - lastUsTriggerUs < ULTRASONIC_MIN_INTERVAL_US)
    return false;

  lastUsTriggerUs = now;

  noInterrupts();
  usResultReady = false;
  usResultValid = false;
  interrupts();

  digitalWrite(ULTRASONIC_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG, LOW);

  usState = US_WAITING_ECHO;
  usTriggerTimeUs = now;
  return true;
}

void updateUltrasonic() {
  if (usState == US_WAITING_ECHO &&
      (micros() - usTriggerTimeUs) > ULTRASONIC_TIMEOUT_US) {
    noInterrupts();
    if (usState == US_WAITING_ECHO) {
      usState = US_IDLE;
      usResultValid = false;
      usResultReady = true;
    }
    interrupts();
  }
}

bool getUltrasonicDistance(float &dist) {
  if (!usResultReady)
    return false;

  noInterrupts();
  usResultReady = false;
  bool valid = usResultValid;
  unsigned long dur = usEchoDurationUs;
  interrupts();

  if (!valid || dur == 0) {
    dist = -1.0f;
  } else {
    dist = (dur * 0.0343f) / 2.0f;
  }
  return true;
}

// ============================================
// MOTEURS
// ============================================
MotionMode motionMode = MODE_IDLE;
unsigned long movementStartTime = 0;

// ============================================
// DEMANDE DE MOUVEMENT DIFFÉRÉE
// ============================================
bool motionPending = false;
MotionMode pendingMotion = MODE_IDLE;
unsigned long pendingSince = 0;

void setMotion(MotionMode mode) {
  motionPending = false;
  motionMode = mode;

  switch (mode) {
    case MODE_IDLE:
      ledcWrite(MOTOR_A_EN, 0);
      ledcWrite(MOTOR_B_EN, 0);
      digitalWrite(MOTOR_A_IN1, LOW);
      digitalWrite(MOTOR_A_IN2, LOW);
      digitalWrite(MOTOR_B_IN1, LOW);
      digitalWrite(MOTOR_B_IN2, LOW);
      break;

    case MODE_FORWARD:
      digitalWrite(MOTOR_A_IN1, HIGH);
      digitalWrite(MOTOR_A_IN2, LOW);
      digitalWrite(MOTOR_B_IN1, HIGH);
      digitalWrite(MOTOR_B_IN2, LOW);
      ledcWrite(MOTOR_A_EN, MOTOR_SPEED);
      ledcWrite(MOTOR_B_EN, MOTOR_SPEED);
      break;

    case MODE_BACKWARD:
      digitalWrite(MOTOR_A_IN1, LOW);
      digitalWrite(MOTOR_A_IN2, HIGH);
      digitalWrite(MOTOR_B_IN1, LOW);
      digitalWrite(MOTOR_B_IN2, HIGH);
      ledcWrite(MOTOR_A_EN, MOTOR_SPEED);
      ledcWrite(MOTOR_B_EN, MOTOR_SPEED);
      break;

    case MODE_LEFT:
      digitalWrite(MOTOR_A_IN1, LOW);
      digitalWrite(MOTOR_A_IN2, HIGH);
      digitalWrite(MOTOR_B_IN1, HIGH);
      digitalWrite(MOTOR_B_IN2, LOW);
      ledcWrite(MOTOR_A_EN, MOTOR_SPEED);
      ledcWrite(MOTOR_B_EN, MOTOR_SPEED);
      break;

    case MODE_RIGHT:
      digitalWrite(MOTOR_A_IN1, HIGH);
      digitalWrite(MOTOR_A_IN2, LOW);
      digitalWrite(MOTOR_B_IN1, LOW);
      digitalWrite(MOTOR_B_IN2, HIGH);
      ledcWrite(MOTOR_A_EN, MOTOR_SPEED);
      ledcWrite(MOTOR_B_EN, MOTOR_SPEED);
      break;
  }

  if (mode != MODE_IDLE)
    movementStartTime = millis();
}

// ============================================
// GARDE AVANT (mesure continue)
// ============================================
float guardBuffer[3] = {-1, -1, -1};
int guardBufIdx = 0;
int invalidCount = 0;
unsigned long lastGuardTrigger = 0;

float lastFilteredDistance = -1.0f;   // ← nouvelle variable pour la décision

float computeGuardDistance() {
  float tmp[3];
  int n = 0;
  for (int i = 0; i < 3; i++) {
    if (guardBuffer[i] >= 0)
      tmp[n++] = guardBuffer[i];
  }
  if (n == 0) return -1.0f;
  if (n == 1) return tmp[0];
  if (n == 2) return (tmp[0] + tmp[1]) * 0.5f;

  float a = tmp[0], b = tmp[1], c = tmp[2];
  if (a > b) { float t = a; a = b; b = t; }
  if (b > c) { float t = b; b = c; c = t; }
  if (a > b) { float t = a; a = b; b = t; }
  return b;
}

void resetGuard() {
  guardBuffer[0] = -1.0f;
  guardBuffer[1] = -1.0f;
  guardBuffer[2] = -1.0f;
  guardBufIdx = 0;
  invalidCount = 0;
  lastGuardTrigger = 0;
  lastFilteredDistance = -1.0f;
}

void updateForwardGuard() {
  float d;

  // Nouvelle mesure disponible
  if (getUltrasonicDistance(d)) {
    guardBuffer[guardBufIdx] = d;
    guardBufIdx = (guardBufIdx + 1) % 3;

    float filtered = computeGuardDistance();
    lastFilteredDistance = filtered;          // ← on garde la dernière distance

    if (filtered < 0) {
      invalidCount++;
      if (invalidCount >= MAX_INVALID_READS) {
        setMotion(MODE_IDLE);
        Serial.println("SAFETY,SENSOR_INVALID");
        return;
      }
    } else {
      invalidCount = 0;
      Serial.printf("DIST,%.1f\n", filtered);

      // CORRECTION 2 : arrêt local sur obstacle pendant FORWARD
      if (motionMode == MODE_FORWARD && filtered < OBSTACLE_STOP_CM) {
        setMotion(MODE_IDLE);
        Serial.printf("SAFETY,OBSTACLE,%.1f\n", filtered);
      }
    }
  }

  // Demande une nouvelle mesure régulièrement
  unsigned long now = millis();
  if (now - lastGuardTrigger < GUARD_INTERVAL)
    return;

  if (requestUltrasonic())
    lastGuardTrigger = now;
}

// ============================================
// IR
// ============================================
void publishIrStates() {
  int leftState  = digitalRead(IR_LEFT_PIN);
  int rightState = digitalRead(IR_RIGHT_PIN);

  if (leftState != lastIrLeftState ||
      millis() - lastIrPublish >= IR_PUBLISH_INTERVAL) {
    Serial.printf("IR,LEFT,%d\n", leftState);
    lastIrLeftState = leftState;
  }

  if (rightState != lastIrRightState ||
      millis() - lastIrPublish >= IR_PUBLISH_INTERVAL) {
    Serial.printf("IR,RIGHT,%d\n", rightState);
    lastIrRightState = rightState;
  }

  lastIrPublish = millis();
}

// ============================================
// DÉCISION AUTONOME (ajouté)
// ============================================
void decideAutonomousMotion() {
  // CORRECTION 1 : sans AUTO_ON, le robot ne décide jamais seul
  if (!autoMode)
    return;

  // On attend d'avoir au moins une mesure valide
  if (lastFilteredDistance < 0)
    return;

  bool frontClear = (lastFilteredDistance >= OBSTACLE_STOP_CM);

  int irLeft  = digitalRead(IR_LEFT_PIN);   // 1 = CLEAR
  int irRight = digitalRead(IR_RIGHT_PIN);  // 1 = CLEAR

  if (frontClear) {
    // Devant libre → on avance
    if (motionMode != MODE_FORWARD) {
      requestMotion(MODE_FORWARD);
      Serial.println("AUTO,FORWARD");
    }
  } else {
    // Obstacle devant → on regarde les côtés
    if (irLeft == 1 && irRight == 0) {
      // Gauche libre, droite bloquée
      if (motionMode != MODE_LEFT) {
        requestMotion(MODE_LEFT);
        Serial.println("AUTO,LEFT");
      }
    }
    else if (irRight == 1 && irLeft == 0) {
      // Droite libre, gauche bloquée
      if (motionMode != MODE_RIGHT) {
        requestMotion(MODE_RIGHT);
        Serial.println("AUTO,RIGHT");
      }
    }
    else if (irLeft == 1 && irRight == 1) {
      // Les deux libres → on préfère gauche
      if (motionMode != MODE_LEFT) {
        requestMotion(MODE_LEFT);
        Serial.println("AUTO,LEFT_PREF");
      }
    }
    else {
      // Les deux bloqués → arrêt
      if (motionMode != MODE_IDLE) {
        setMotion(MODE_IDLE);
        Serial.println("AUTO,STOP_BOTH_BLOCKED");
      }
    }
  }
}

// ============================================
// DEMANDES DE MOUVEMENT
// ============================================
void applyMotion(MotionMode mode) {
  if (mode == MODE_FORWARD && motionMode != MODE_FORWARD) {
    resetGuard();
    resetUltrasonic();
  }
  setMotion(mode);
}

void requestMotion(MotionMode mode) {
  bool reversing =
    (mode != MODE_IDLE &&
     motionMode != MODE_IDLE &&
     mode != motionMode);

  if (reversing) {
    setMotion(MODE_IDLE);
    pendingMotion = mode;
    pendingSince = millis();
    motionPending = true;
  } else {
    applyMotion(mode);
  }
}

void updatePendingMotion() {
  if (motionPending &&
      (millis() - pendingSince >= REVERSE_PAUSE_MS)) {
    MotionMode m = pendingMotion;
    motionPending = false;
    applyMotion(m);
  }
}

// ============================================
// COMMANDES SÉRIE (inchangées)
// ============================================
void processCommand(const char* raw) {
  char buf[RX_MAX + 1];
  size_t n = strlen(raw);
  if (n > RX_MAX) n = RX_MAX;

  size_t j = 0;
  for (size_t i = 0; i < n; i++) {
    char c = raw[i];
    if (c >= 'a' && c <= 'z') c -= 32;
    buf[j++] = c;
  }
  buf[j] = '\0';

  size_t start = 0;
  size_t end = j;
  while (start < end && (buf[start] == ' ' || buf[start] == '\t')) start++;
  while (end > start && (buf[end - 1] == ' ' || buf[end - 1] == '\t')) end--;
  buf[end] = '\0';

  const char* cmd = buf + start;

  if (strcmp(cmd, "STOP") == 0) {
    setMotion(MODE_IDLE);
    Serial.println("ACK,STOP");
    return;
  }
  else if (strcmp(cmd, "FORWARD") == 0) {
    requestMotion(MODE_FORWARD);
    Serial.printf("ACK,FORWARD,%d\n", MOTOR_SPEED_PERCENT);
    return;
  }
  else if (strcmp(cmd, "BACKWARD") == 0) {
    requestMotion(MODE_BACKWARD);
    Serial.printf("ACK,BACKWARD,%d\n", MOTOR_SPEED_PERCENT);
    return;
  }
  else if (strcmp(cmd, "LEFT") == 0) {
    requestMotion(MODE_LEFT);
    Serial.printf("ACK,LEFT,%d\n", MOTOR_SPEED_PERCENT);
    return;
  }
  else if (strcmp(cmd, "RIGHT") == 0) {
    requestMotion(MODE_RIGHT);
    Serial.printf("ACK,RIGHT,%d\n", MOTOR_SPEED_PERCENT);
    return;
  }
  // CORRECTION 3 : commandes de test du mode autonome
  else if (strcmp(cmd, "AUTO_ON") == 0) {
    autoMode = true;
    Serial.println("ACK,AUTO_ON");
    return;
  }
  else if (strcmp(cmd, "AUTO_OFF") == 0) {
    autoMode = false;
    setMotion(MODE_IDLE);
    Serial.println("ACK,AUTO_OFF");
    return;
  }
  else {
    setMotion(MODE_IDLE);
    Serial.printf("REJECTED,%s\n", cmd);
  }
}

// ============================================
// RÉCEPTION SÉRIE
// ============================================
void handleSerial() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (rxDiscard) {
        rxDiscard = false;
        rxLen = 0;
      } else if (rxLen > 0) {
        rxBuffer[rxLen] = '\0';
        processCommand(rxBuffer);
        rxLen = 0;
      }
    } else if (rxDiscard) {
      // Ignore
    } else if (rxLen < RX_MAX) {
      rxBuffer[rxLen++] = c;
    } else {
      rxLen = 0;
      rxDiscard = true;
      setMotion(MODE_IDLE);
      Serial.println("REJECTED,OVERFLOW");
    }
  }
}

// ============================================
// SETUP
// ============================================
void setup() {
  Serial.begin(115200);

  // Moteurs
  pinMode(MOTOR_A_IN1, OUTPUT);
  pinMode(MOTOR_A_IN2, OUTPUT);
  pinMode(MOTOR_B_IN1, OUTPUT);
  pinMode(MOTOR_B_IN2, OUTPUT);

  ledcAttach(MOTOR_A_EN, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_B_EN, PWM_FREQ, PWM_RESOLUTION);

  // HC-SR04
  pinMode(ULTRASONIC_TRIG, OUTPUT);
  pinMode(ULTRASONIC_ECHO, INPUT);
  digitalWrite(ULTRASONIC_TRIG, LOW);

  attachInterrupt(
    digitalPinToInterrupt(ULTRASONIC_ECHO),
    ultrasonicISR,
    CHANGE
  );

  // IR
  pinMode(IR_LEFT_PIN, INPUT_PULLUP);
  pinMode(IR_RIGHT_PIN, INPUT_PULLUP);

  // Stop
  setMotion(MODE_IDLE);
  delay(200);

  Serial.println();
  Serial.println("================================");
  Serial.println("HIAR V0.8 ULTRASONIC + IR + AUTO");
  Serial.println("================================");
  Serial.printf("Motor speed: %d%% (PWM %d/255 @ %d Hz)\n",
                MOTOR_SPEED_PERCENT, MOTOR_SPEED, PWM_FREQ);
  Serial.printf("Max move duration: %lu ms\n", MAX_MOVE_DURATION);
  Serial.printf("Obstacle stop: %.0f cm\n", OBSTACLE_STOP_CM);
  Serial.printf("HC-SR04 TRIG: GPIO%d, ECHO: GPIO%d\n",
                ULTRASONIC_TRIG, ULTRASONIC_ECHO);
  Serial.printf("IR LEFT: GPIO%d\n", IR_LEFT_PIN);
  Serial.printf("IR RIGHT: GPIO%d\n", IR_RIGHT_PIN);
  Serial.println("IR logic: 1=CLEAR, 0=OBSTACLE");
  Serial.println("Mode: AUTONOME (devant libre → avance, sinon gauche/droite)");
  Serial.println("Commands série toujours prioritaires: FORWARD BACKWARD LEFT RIGHT STOP");
}

// ============================================
// LOOP
// ============================================
void loop() {
  // 1. Commandes série (prioritaires)
  handleSerial();

  // 2. Mouvement différé
  updatePendingMotion();

  // 3. Timeout ultrason
  updateUltrasonic();

  // 4. Timeout mouvement (sécurité)
  if (motionMode != MODE_IDLE &&
      (millis() - movementStartTime >= MAX_MOVE_DURATION)) {
    setMotion(MODE_IDLE);
    Serial.println("SAFETY,TIMEOUT");
  }

  // 5. IR
  publishIrStates();

  // 6. Mesure ultrason continue
  updateForwardGuard();

  // 7. Décision autonome (nouveau)
  decideAutonomousMotion();
}