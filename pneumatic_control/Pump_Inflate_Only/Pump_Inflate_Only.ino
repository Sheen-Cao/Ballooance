#include <AFMotor.h>

// Adafruit Motor Shield v1 (AFMotor) channel mapping:
// - pump1: M1
// - valve: M3
// - pump2: M4 (kept OFF here)

AF_DCMotor pump1(3, MOTOR12_64KHZ);
AF_DCMotor valve(1, MOTOR12_64KHZ);
AF_DCMotor pump2(4, MOTOR12_64KHZ);

static const uint8_t PUMP_SPEED = 255;            // 0..255
static const unsigned long LOG_INTERVAL_MS = 1000;

bool running = true;
unsigned long lastLogMs = 0;

static void allStop() {
  pump1.run(RELEASE);
  pump2.run(RELEASE);
  valve.run(RELEASE);
}

static void applyInflateState() {
  // Inflate: open the inflate flow path (per your original comment: FORWARD connects port 2 & 3)
  valve.run(FORWARD);

  // Run pump1 continuously to inflate
  pump1.run(FORWARD);

  // Ensure deflate pump is OFF
  pump2.run(RELEASE);
}

void setup() {
  Serial.begin(9600);
  Serial.println();
  Serial.println("------");
  Serial.println("Continuous inflate (pump1) start");
  Serial.println("Commands: s=stop, r=run");

  pump1.setSpeed(PUMP_SPEED);
  pump2.setSpeed(PUMP_SPEED);
  valve.setSpeed(255);

  // Safety: start from a known OFF state, then enable inflate.
  allStop();
  delay(200);

  applyInflateState();
}

void loop() {
  // Optional serial control
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == 's' || c == 'S') {
      running = false;
      allStop();
      Serial.println("STOP");
    } else if (c == 'r' || c == 'R') {
      running = true;
      applyInflateState();
      Serial.println("RUN");
    }
  }

  if (running) {
    // Keep outputs in the intended state
    applyInflateState();
  }

  // Periodic log
  unsigned long now = millis();
  if (now - lastLogMs >= LOG_INTERVAL_MS) {
    lastLogMs = now;
    Serial.print("inflate running=");
    Serial.print(running ? "true" : "false");
    Serial.print(" speed=");
    Serial.println(PUMP_SPEED);
  }
}
