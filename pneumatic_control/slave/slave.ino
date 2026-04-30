// ==============================
// SLAVE: Pumps 4-7
// ==============================
//
// Receives from Master via SoftwareSerial:
//   Slave A1 (RX) <- Master A0 (TX)
//   Format: "P,<global_id>,<state>\n"
//   global_id: 4-7   state: I / D / H
//   Example: "P,6,D\n"
//
// Pump behavior:
//   'I' -> pump ON
//   'D' -> pump OFF
//   'H' -> pump OFF
//
// Local motor mapping (AFMotor shield):
//   pump 4 -> M1
//   pump 5 -> M2
//   pump 6 -> M3
//   pump 7 -> M4
//
// No valve control on Slave (all valves are on Master via I2C).

#include <AFMotor.h>
#include <SoftwareSerial.h>

// ── Configuration ─────────────────────────────────────────────────────────────

namespace Config {
  static const uint8_t  kLocalPumpCount = 4;
  static const uint8_t  kPumpIdOffset   = 4;    // global id 4-7 -> local index 0-3
  static const uint8_t  kFullSpeed      = 255;

  // SoftwareSerial from Master.
  // Slave A1 = RX <- Master A0 (TX).
  // A0 is declared as TX here because SoftwareSerial requires both pins,
  // but it is not physically connected.
  static const uint8_t  kLinkRxPin      = A1;
  static const uint8_t  kLinkTxPin      = A0;   // not connected
  static const unsigned long kLinkBaud  = 9600;

  static const unsigned long kUsbBaud   = 115200;

  static const size_t   kLineBufferSize = 24;
}

// ── Local pumps (AFMotor shield M1-M4 = pumps 4-7) ───────────────────────────

AF_DCMotor _pump4(1, MOTOR12_64KHZ);
AF_DCMotor _pump5(2, MOTOR12_64KHZ);
AF_DCMotor _pump6(3, MOTOR12_64KHZ);
AF_DCMotor _pump7(4, MOTOR12_64KHZ);
AF_DCMotor* localPumps[Config::kLocalPumpCount] = { &_pump4, &_pump5, &_pump6, &_pump7 };

// ── SoftwareSerial link from Master ──────────────────────────────────────────

SoftwareSerial linkSerial(Config::kLinkRxPin, Config::kLinkTxPin);

// ── Line buffer for SoftwareSerial input ─────────────────────────────────────

char   lineBuffer[Config::kLineBufferSize];
size_t lineLen = 0;

// ── Pump control ──────────────────────────────────────────────────────────────

// Drive one motor-shield channel (motorIndex 0-3).
void setMotor(int motorIndex, bool on) {
  if (motorIndex < 0 || motorIndex >= (int)Config::kLocalPumpCount) return;
  localPumps[motorIndex]->run(on ? FORWARD : RELEASE);
}

// Control a local pump by its local index (0-3).
// I -> ON;  D or H -> OFF.
void setLocalPump(int localIndex, char state) {
  bool on = (state == 'I');
  setMotor(localIndex, on);
}

// ── Command parser ────────────────────────────────────────────────────────────

// Parse a complete line (newline already stripped).
// Expected format: "P,<global_id>,<state>"   e.g. "P,5,I"
static void parsePumpCommand(const char* line) {
  // Check frame marker and first comma.
  if (line[0] != 'P' || line[1] != ',') {
    Serial.print(F("ERR: bad frame: "));
    Serial.println(line);
    return;
  }

  // Parse integer id after "P,".
  const char* p = line + 2;
  int id = 0;
  bool hasDigits = false;
  while (*p >= '0' && *p <= '9') {
    id = id * 10 + (*p - '0');
    ++p;
    hasDigits = true;
  }
  if (!hasDigits) {
    Serial.println(F("ERR: missing pump id"));
    return;
  }

  // Expect comma after the id.
  if (*p != ',') {
    Serial.println(F("ERR: missing comma after id"));
    return;
  }
  ++p;  // skip comma

  // Parse and validate state character.
  char state = *p;
  if (state != 'I' && state != 'D' && state != 'H') {
    Serial.print(F("ERR: invalid state: '"));
    Serial.print(state);
    Serial.println(F("'"));
    return;
  }

  // Map global pump id (4-7) to local motor index (0-3).
  int localIndex = id - (int)Config::kPumpIdOffset;
  if (localIndex < 0 || localIndex >= (int)Config::kLocalPumpCount) {
    Serial.print(F("ERR: pump id out of range: "));
    Serial.println(id);
    return;
  }

  setLocalPump(localIndex, state);

  // Debug echo.
  Serial.print(F("P"));
  Serial.print(id);
  Serial.print(F(" (M"));
  Serial.print(localIndex + 1);
  Serial.print(F(") -> "));
  if      (state == 'I') Serial.println(F("Inflate"));
  else if (state == 'D') Serial.println(F("Deflate"));
  else                   Serial.println(F("Hold"));
}

// ── SoftwareSerial line reader (non-blocking) ─────────────────────────────────

static void readLinkSerial() {
  while (linkSerial.available() > 0) {
    char c = (char)linkSerial.read();

    if (c == '\n' || c == '\r') {
      if (lineLen > 0) {
        lineBuffer[lineLen] = '\0';
        parsePumpCommand(lineBuffer);
        lineLen = 0;
      }
      continue;
    }

    if (lineLen < (Config::kLineBufferSize - 1)) {
      lineBuffer[lineLen++] = c;
    } else {
      lineLen = 0;
      lineBuffer[0] = '\0';
      Serial.println(F("ERR: line buffer overflow, resetting"));
    }
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────

static void initLocalPumps() {
  for (uint8_t i = 0; i < Config::kLocalPumpCount; ++i) {
    localPumps[i]->setSpeed(Config::kFullSpeed);
    localPumps[i]->run(RELEASE);
  }
}

void setup() {
  Serial.begin(Config::kUsbBaud);
  linkSerial.begin(Config::kLinkBaud);

  initLocalPumps();

  Serial.println(F("SLAVE ready"));
  Serial.println(F("Waiting for pump commands from MASTER (P,<id>,<state>)..."));
}

void loop() {
  readLinkSerial();
}
