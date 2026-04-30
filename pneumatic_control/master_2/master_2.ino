// ==============================
// MASTER 2: Pumps 0-3 + Valves 0-7
// Configurable active balloon count (1-8)
// ==============================
//
// PC -> Master (USB Serial, 115200 baud):
//
//   [Config] Set active balloon count:
//     set <N>   where N = 1-8
//     Example:  set 4   (activates balloons 0-3; balloons 4-7 are held/off)
//     On set N, all balloons >= N are immediately put to Hold.
//
//   [Mode 1] Full command — exactly N chars, one per active balloon (index 0 to N-1):
//     Valid chars: I = Inflate, D = Deflate, H = Hold
//     Example (N=4): IIHD
//
//   [Mode 2] Selective command — space-separated tokens, each "<indices>-<state>":
//     Only the listed balloons change; all others keep current state.
//     Indices must be within the active range (0 to N-1).
//     Examples:
//       02-D 3-I       -> 0,2=Deflate; 3=Inflate
//       1-D 23-H       -> 1=D, 2=H, 3=H
//
// Balloon behavior (3-way valve: de-energized = pump->balloon, energized = balloon->exhaust):
//   'I' -> valve OFF, pump ON
//   'D' -> valve ON,  pump OFF
//   'H' -> valve OFF, pump OFF
//
// Pumps 0-3: controlled locally via AFMotor shield (M1-M4).
// Pumps 4-7: sent to Slave via SoftwareSerial (only if activeCount > 4).
//
// Master -> Slave (SoftwareSerial):
//   Master A0 (TX) -> Slave A1 (RX)
//   Format: "P,<global_id>,<state>\n"   e.g. "P,5,I\n"
//
// Valves 0-7: MCP23017 I2C GPIO expander.
//   SDA = A4,  SCL = A5   (hardware I2C on Uno)
//   Address: Config::kValveI2CAddr  (default 0x20, all address pins open)
//   Protocol: register write to GPIOA (0x12), bit N = valve N (1=ON, 0=OFF)

#include <AFMotor.h>
#include <SoftwareSerial.h>
#include <Wire.h>

// ── Configuration ─────────────────────────────────────────────────────────────

namespace Config {
  static const uint8_t  kBalloonMax      = 8;
  static const uint8_t  kLocalPumpCount  = 4;    // pumps 0-3 on this shield (M1-M4)
  static const uint8_t  kFullSpeed       = 255;

  static const uint8_t  kLinkTxPin       = A0;
  static const uint8_t  kLinkRxPin       = A1;   // not connected
  static const unsigned long kLinkBaud   = 9600;

  static const unsigned long kUsbBaud    = 115200;

  static const uint8_t  kValveI2CAddr    = 0x20;
  static const uint8_t  kMCP_IODIRA      = 0x00;
  static const uint8_t  kMCP_GPIOA       = 0x12;

  // Worst-case line: "set 8" = 5 chars; selective "0-I 1-I 2-I 3-I 4-I 5-I 6-I 7-I" = 31 chars
  static const size_t   kLineBufferSize  = 40;
}

// ── Local pumps (AFMotor shield M1-M4 = pumps 0-3) ───────────────────────────

AF_DCMotor _pump0(1, MOTOR12_64KHZ);
AF_DCMotor _pump1(2, MOTOR12_64KHZ);
AF_DCMotor _pump2(3, MOTOR12_64KHZ);
AF_DCMotor _pump3(4, MOTOR12_64KHZ);
AF_DCMotor* localPumps[Config::kLocalPumpCount] = { &_pump0, &_pump1, &_pump2, &_pump3 };

// ── SoftwareSerial link to Slave ──────────────────────────────────────────────

SoftwareSerial linkSerial(Config::kLinkRxPin, Config::kLinkTxPin);

// ── State ─────────────────────────────────────────────────────────────────────

uint8_t valveState  = 0;
uint8_t activeCount = Config::kBalloonMax;  // runtime-configurable; default all 8
char    balloonState[Config::kBalloonMax];  // per-balloon I/D/H; initialised to 'H'

// ── USB serial line buffer ────────────────────────────────────────────────────

char   lineBuffer[Config::kLineBufferSize];
size_t lineLen = 0;

// ── Valve functions ───────────────────────────────────────────────────────────

void initValveDriver() {
  Wire.beginTransmission(Config::kValveI2CAddr);
  Wire.write(Config::kMCP_IODIRA);
  Wire.write(0x00);                 // all Port A pins = output
  Wire.endTransmission();
}

void writeValveByte(uint8_t data) {
  Wire.beginTransmission(Config::kValveI2CAddr);
  Wire.write(Config::kMCP_GPIOA);
  Wire.write(data);
  Wire.endTransmission();
}

void setValve(int id, bool on) {
  if (id < 0 || id >= (int)Config::kBalloonMax) return;
  if (on) valveState |=  (uint8_t)(1u << id);
  else    valveState &= ~(uint8_t)(1u << id);
  writeValveByte(valveState);
}

// ── Pump functions ────────────────────────────────────────────────────────────

void setMotor(int motorIndex, bool on) {
  if (motorIndex < 0 || motorIndex >= (int)Config::kLocalPumpCount) return;
  localPumps[motorIndex]->run(on ? FORWARD : RELEASE);
}

void setLocalPump(int id, char state) {
  setMotor(id, state == 'I');
}

// ── Slave communication ───────────────────────────────────────────────────────

void sendPumpCommandToSlave(int id, char state) {
  linkSerial.print('P');
  linkSerial.print(',');
  linkSerial.print(id);
  linkSerial.print(',');
  linkSerial.print(state);
  linkSerial.print('\n');
}

// ── Top-level balloon control ─────────────────────────────────────────────────

void setBalloonState(int id, char state) {
  balloonState[id] = state;
  setValve(id, state == 'D');

  if (id < (int)Config::kLocalPumpCount) {
    setLocalPump(id, state);
  } else {
    sendPumpCommandToSlave(id, state);
  }
}

// ── Active count management ───────────────────────────────────────────────────

// Hold all balloons from index n to kBalloonMax-1 (shuts them down safely).
static void deactivateFrom(uint8_t n) {
  for (uint8_t i = n; i < Config::kBalloonMax; ++i) {
    setBalloonState(i, 'H');
  }
}

static void applyActiveCount(uint8_t n) {
  activeCount = n;
  deactivateFrom(n);  // immediately hold any balloon now outside the active range
  Serial.print(F("SET: "));
  Serial.print(activeCount);
  Serial.print(F(" balloons active (index 0-"));
  Serial.print(activeCount - 1);
  Serial.println(F(")"));
}

// ── Command helpers ───────────────────────────────────────────────────────────

static bool isValidState(char c) {
  return c == 'I' || c == 'D' || c == 'H';
}

static void printCurrentState() {
  Serial.print(F("STATE: "));
  for (uint8_t i = 0; i < activeCount; ++i) Serial.print(balloonState[i]);
  Serial.println();
}

// ── Mode 1: full command (N chars) ───────────────────────────────────────────

static bool processFullCommand(const char* cmd, size_t len) {
  if (len != activeCount) {
    Serial.print(F("ERR: expected "));
    Serial.print(activeCount);
    Serial.print(F(" chars, got "));
    Serial.println(len);
    return false;
  }

  for (uint8_t i = 0; i < activeCount; ++i) {
    if (!isValidState(cmd[i])) {
      Serial.print(F("ERR: bad char at balloon "));
      Serial.print(i);
      Serial.print(F(": '"));
      Serial.print(cmd[i]);
      Serial.println(F("' (allowed: I/D/H)"));
      return false;
    }
  }

  for (uint8_t i = 0; i < activeCount; ++i) setBalloonState(i, cmd[i]);

  Serial.print(F("CMD: "));
  for (uint8_t i = 0; i < activeCount; ++i) Serial.print(cmd[i]);
  Serial.println();
  return true;
}

// ── Mode 2: selective command ─────────────────────────────────────────────────
//
// Format: space-separated tokens, each "<indices>-<state>"
//   indices : one or more digits 0-7, all must be < activeCount
//   state   : I / D / H
// Examples:
//   "02-D 3-I"   "1-H 23-I"   "0-I 0-D"  (last token wins per balloon)

static bool parseSelectiveCommand(const char* line, size_t len) {
  const char* p   = line;
  const char* end = line + len;
  bool anyApplied = false;

  while (p < end) {
    while (p < end && *p == ' ') ++p;
    if (p >= end) break;

    const char* idStart = p;
    while (p < end && *p >= '0' && *p <= '9') ++p;
    size_t idCount = (size_t)(p - idStart);

    if (idCount == 0) {
      Serial.print(F("ERR: expected balloon index (0-"));
      Serial.print(activeCount - 1);
      Serial.print(F("), got: '"));
      Serial.print(*p);
      Serial.println(F("'"));
      return false;
    }

    if (p >= end || *p != '-') {
      Serial.println(F("ERR: expected '-' after balloon indices"));
      return false;
    }
    ++p;

    if (p >= end || !isValidState(*p)) {
      Serial.print(F("ERR: expected I/D/H after '-', got: '"));
      if (p < end) Serial.print(*p);
      Serial.println(F("'"));
      return false;
    }
    char state = *p;
    ++p;

    for (size_t i = 0; i < idCount; ++i) {
      int id = idStart[i] - '0';
      if (id >= (int)activeCount) {
        Serial.print(F("ERR: balloon "));
        Serial.print(id);
        Serial.print(F(" out of active range (0-"));
        Serial.print(activeCount - 1);
        Serial.println(F(")"));
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

// ── Config command: "set <N>" ─────────────────────────────────────────────────

static bool parseSetCommand(const char* line, size_t len) {
  // Minimum valid input: "set 1" (5 chars). Line already confirmed to start with "set ".
  if (len < 5) {
    Serial.println(F("ERR: usage: set <N>  (N = 1-8)"));
    return false;
  }

  char digit = line[4];
  if (digit < '1' || digit > '8') {
    Serial.print(F("ERR: N must be 1-8, got: '"));
    Serial.print(digit);
    Serial.println(F("'"));
    return false;
  }

  applyActiveCount((uint8_t)(digit - '0'));
  return true;
}

// ── Dispatcher ────────────────────────────────────────────────────────────────

static bool processCommand(const char* cmd, size_t len) {
  if (len == 0) return false;

  // "set " prefix -> configuration command
  if (len >= 5 && cmd[0]=='s' && cmd[1]=='e' && cmd[2]=='t' && cmd[3]==' ') {
    return parseSetCommand(cmd, len);
  }

  // '-' anywhere -> selective mode
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

  for (uint8_t i = 0; i < Config::kBalloonMax; ++i) balloonState[i] = 'H';

  initLocalPumps();
  initValveDriver();
  writeValveByte(0);  // all valves OFF at startup

  Serial.println(F("MASTER 2 ready"));
  Serial.print(F("Active balloons: "));
  Serial.print(activeCount);
  Serial.println(F(" (default: all 8)"));
  Serial.println(F("set <N>   : set active count 1-8 (e.g. \"set 4\")"));
  Serial.println(F("Full cmd  : N chars  (e.g. \"IIHD\" for N=4)"));
  Serial.println(F("Selective : <indices>-<state> tokens  (e.g. \"02-D 3-I\")"));
}

void loop() {
  readUsbSerialLines();
}67
