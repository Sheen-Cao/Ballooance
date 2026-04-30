// ==============================
// MASTER: Pumps 0-3 + Valves 0-7
// ==============================
//
// PC -> Master (USB Serial, 115200 baud):
//
//   [Mode 1] Full command — 8 chars, one per balloon (index 0-7):
//     Valid chars: I = Inflate, D = Deflate, H = Hold
//     Example: IIIHHHDD
//
//   [Mode 2] Selective command — space-separated tokens, each "<indices>-<state>":
//     Only the listed balloons change; all others keep their current state.
//     Multiple indices share one state character.  Same balloon can appear
//     multiple times — last token wins.
//     Examples:
//       02-D 537-I        → 0,2=Deflate; 3,5,7=Inflate
//       1-D 2-I 56-D      → 1=D, 2=I, 5=D, 6=D
//       2-I 2-D           → balloon 2 ends up D (last wins)
//
// Balloon behavior (3-way valve: de-energized = pump→balloon, energized = balloon→exhaust):
//   'I' -> valve OFF, pump ON
//   'D' -> valve ON,  pump OFF
//   'H' -> valve OFF, pump OFF
//
// Pumps 0-3: controlled locally via AFMotor shield (M1-M4).
// Pumps 4-7: sent to Slave via SoftwareSerial.
//
// Master -> Slave (SoftwareSerial):
//   Master A0 (TX) -> Slave A1 (RX)
//   Format: "P,<global_id>,<state>\n"   e.g. "P,5,I\n"
//
// Valves 0-7: Adafruit I2C 8-channel solenoid driver (MCP23017).
//   SDA = A4,  SCL = A5   (hardware I2C on Uno)
//   Address: Config::kValveI2CAddr  (default 0x20)
//   Protocol: register write to GPIOA (0x12), bit N = valve N (1=ON, 0=OFF)

#include <AFMotor.h>
#include <SoftwareSerial.h>
#include <Wire.h>

// ── Configuration ─────────────────────────────────────────────────────────────

namespace Config {
  static const uint8_t  kBalloonCount   = 8;
  static const uint8_t  kLocalPumpCount = 4;    // pumps 0-3 on this shield (M1-M4)
  static const uint8_t  kFullSpeed      = 255;

  // SoftwareSerial to Slave.
  // Master A0 = TX -> Slave A1 (RX).
  // A1 is declared as RX here because SoftwareSerial requires both pins,
  // but it is not physically connected.
  static const uint8_t  kLinkTxPin      = A0;
  static const uint8_t  kLinkRxPin      = A1;   // not connected
  static const unsigned long kLinkBaud  = 9600;

  static const unsigned long kUsbBaud   = 115200;

  // I2C solenoid driver address (MCP23017 default = 0x20, all A0/A1/A2 open).
  static const uint8_t  kValveI2CAddr   = 0x20;

  // MCP23017 register addresses (IOCON.BANK = 0, default).
  static const uint8_t  kMCP_IODIRA     = 0x00;  // Port A direction (0=output)
  static const uint8_t  kMCP_GPIOA      = 0x12;  // Port A GPIO output

  static const size_t   kCmdLength      = 8;
  // Worst-case selective line: "0-I 1-I 2-I 3-I 4-I 5-I 6-I 7-I" = 31 chars + NUL
  static const size_t   kLineBufferSize = 40;
}

// ── Local pumps (AFMotor shield M1-M4 = pumps 0-3) ───────────────────────────

AF_DCMotor _pump0(1, MOTOR12_64KHZ);
AF_DCMotor _pump1(2, MOTOR12_64KHZ);
AF_DCMotor _pump2(3, MOTOR12_64KHZ);
AF_DCMotor _pump3(4, MOTOR12_64KHZ);
AF_DCMotor* localPumps[Config::kLocalPumpCount] = { &_pump0, &_pump1, &_pump2, &_pump3 };

// ── SoftwareSerial link to Slave ──────────────────────────────────────────────

SoftwareSerial linkSerial(Config::kLinkRxPin, Config::kLinkTxPin);

// ── Valve state (8 bits, one per valve) ──────────────────────────────────────

uint8_t valveState = 0;  // bit N = valve N: 1=ON, 0=OFF

// ── Per-balloon state (I/D/H) — used by selective commands ───────────────────

char balloonState[Config::kBalloonCount];  // initialised to 'H' in setup()

// ── USB serial line buffer ────────────────────────────────────────────────────

char   lineBuffer[Config::kLineBufferSize];
size_t lineLen = 0;

// ── Valve functions ───────────────────────────────────────────────────────────

// Configure MCP23017 Port A as all-output. Call once in setup().
void initValveDriver() {
  Wire.beginTransmission(Config::kValveI2CAddr);
  Wire.write(Config::kMCP_IODIRA);  // point to IODIRA register
  Wire.write(0x00);                 // all Port A pins = output
  Wire.endTransmission();
}

// Push the full 8-bit valve state to MCP23017 Port A (GPIOA).
void writeValveByte(uint8_t data) {
  Wire.beginTransmission(Config::kValveI2CAddr);
  Wire.write(Config::kMCP_GPIOA);  // point to GPIOA register
  Wire.write(data);                // bit N = solenoid N (1=ON, 0=OFF)
  Wire.endTransmission();
}

// Turn a single valve on or off and update the driver immediately.
// id: 0-7
void setValve(int id, bool on) {
  if (id < 0 || id >= (int)Config::kBalloonCount) return;
  if (on) {
    valveState |=  (uint8_t)(1u << id);
  } else {
    valveState &= ~(uint8_t)(1u << id);
  }
  writeValveByte(valveState);
}

// ── Pump functions ────────────────────────────────────────────────────────────

// Drive one motor-shield channel (motorIndex 0-3).
void setMotor(int motorIndex, bool on) {
  if (motorIndex < 0 || motorIndex >= (int)Config::kLocalPumpCount) return;
  localPumps[motorIndex]->run(on ? FORWARD : RELEASE);
}

// Control a local pump by its global id (0-3).
// I -> ON;  D or H -> OFF.
void setLocalPump(int id, char state) {
  bool on = (state == 'I');
  setMotor(id, on);
}

// ── Slave communication ───────────────────────────────────────────────────────

// Send a pump command for a remote pump (id 4-7): "P,<id>,<state>\n"
void sendPumpCommandToSlave(int id, char state) {
  linkSerial.print('P');
  linkSerial.print(',');
  linkSerial.print(id);
  linkSerial.print(',');
  linkSerial.print(state);
  linkSerial.print('\n');
}

// ── Top-level balloon control ─────────────────────────────────────────────────

// Apply a state to balloon id (0-7) and record it.
//   I -> valve OFF, pump ON   (pump connected to balloon via de-energized valve)
//   D -> valve ON,  pump OFF  (balloon vented to exhaust via energized valve)
//   H -> valve OFF, pump OFF  (balloon sealed, pump off)
void setBalloonState(int id, char state) {
  balloonState[id] = state;
  setValve(id, state == 'D');

  if (id < (int)Config::kLocalPumpCount) {
    setLocalPump(id, state);
  } else {
    sendPumpCommandToSlave(id, state);
  }
}

// ── Command processing ────────────────────────────────────────────────────────

static bool isValidState(char c) {
  return c == 'I' || c == 'D' || c == 'H';
}

// Print the current state of all 8 balloons (used by both command modes).
static void printCurrentState() {
  Serial.print(F("STATE: "));
  for (uint8_t i = 0; i < Config::kBalloonCount; ++i) {
    Serial.print(balloonState[i]);
  }
  Serial.println();
}

// ── Mode 1: full 8-char command ───────────────────────────────────────────────

static bool processFullCommand(const char* cmd, size_t len) {
  if (len != Config::kCmdLength) {
    Serial.print(F("ERR: expected 8 chars, got "));
    Serial.println(len);
    return false;
  }

  // Validate all characters before applying anything.
  for (uint8_t i = 0; i < Config::kCmdLength; ++i) {
    if (!isValidState(cmd[i])) {
      Serial.print(F("ERR: bad char at balloon "));
      Serial.print(i);
      Serial.print(F(": '"));
      Serial.print(cmd[i]);
      Serial.println(F("' (allowed: I/D/H)"));
      return false;
    }
  }

  for (uint8_t i = 0; i < Config::kCmdLength; ++i) {
    setBalloonState(i, cmd[i]);
  }

  Serial.print(F("CMD: "));
  Serial.println(cmd);
  return true;
}

// ── Mode 2: selective command ─────────────────────────────────────────────────
//
// Format: space-separated tokens, each "<indices>-<state>"
//   indices : one or more digits 0-7 (order irrelevant)
//   state   : I / D / H
// Examples:
//   "02-D 537-I"   "1-D 2-I 56-D"   "2-I 2-D"  (last token wins per balloon)

static bool parseSelectiveCommand(const char* line, size_t len) {
  const char* p   = line;
  const char* end = line + len;
  bool anyApplied = false;

  while (p < end) {
    // Skip spaces between tokens.
    while (p < end && *p == ' ') ++p;
    if (p >= end) break;

    // Collect digit run (balloon indices).
    const char* idStart = p;
    while (p < end && *p >= '0' && *p <= '9') ++p;
    size_t idCount = (size_t)(p - idStart);

    if (idCount == 0) {
      Serial.print(F("ERR: expected balloon index (0-7), got: '"));
      Serial.print(*p);
      Serial.println(F("'"));
      return false;
    }

    // Expect '-' separator.
    if (p >= end || *p != '-') {
      Serial.println(F("ERR: expected '-' after balloon indices"));
      return false;
    }
    ++p;

    // Expect state character.
    if (p >= end || !isValidState(*p)) {
      Serial.print(F("ERR: expected I/D/H after '-', got: '"));
      if (p < end) Serial.print(*p);
      Serial.println(F("'"));
      return false;
    }
    char state = *p;
    ++p;

    // Apply state to each listed balloon index.
    for (size_t i = 0; i < idCount; ++i) {
      int id = idStart[i] - '0';
      if (id >= (int)Config::kBalloonCount) {
        Serial.print(F("ERR: balloon id out of range: "));
        Serial.println(id);
        return false;
      }
      setBalloonState(id, state);
      anyApplied = true;
    }
  }

  if (!anyApplied) {
    Serial.println(F("ERR: empty selective command"));
    return false;
  }

  printCurrentState();
  return true;
}

// ── Dispatcher ────────────────────────────────────────────────────────────────

static bool processCommand(const char* cmd, size_t len) {
  if (len == 0) return false;

  // A '-' anywhere in the line means selective mode.
  for (size_t i = 0; i < len; ++i) {
    if (cmd[i] == '-') return parseSelectiveCommand(cmd, len);
  }

  return processFullCommand(cmd, len);
}

// ── USB Serial line reader (non-blocking) ─────────────────────────────────────

static void readUsbSerialLines() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();

    if (c == '\n' || c == '\r') {
      if (lineLen > 0) {
        lineBuffer[lineLen] = '\0';
        processCommand(lineBuffer, lineLen);
        lineLen = 0;
      }
      continue;
    }

    if (lineLen < (Config::kLineBufferSize - 1)) {
      lineBuffer[lineLen++] = c;
    } else {
      lineLen = 0;
      lineBuffer[0] = '\0';
      Serial.println(F("ERR: input line too long, resetting"));
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
  Wire.begin();

  // All balloons start in Hold state.
  for (uint8_t i = 0; i < Config::kBalloonCount; ++i) balloonState[i] = 'H';

  initLocalPumps();
  initValveDriver();   // configure MCP23017 Port A as output
  writeValveByte(0);   // all valves OFF at startup

  Serial.println(F("MASTER ready"));
  Serial.println(F("Full cmd  : IIIHHHDD  (8 chars, sets all balloons)"));
  Serial.println(F("Selective : 02-D 537-I  (<indices>-<state> tokens)"));
}

void loop() {
  readUsbSerialLines();
}
