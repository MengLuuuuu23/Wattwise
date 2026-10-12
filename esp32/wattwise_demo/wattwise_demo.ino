/*
  WattWise physical demo node - ESP32 (v2)
  ========================================
  Wiring (unchanged from your plan):
    LED red   GPIO 19 (220R to GND)
    LED green GPIO 18 (220R to GND)
    Servo     GPIO 13 (5V + common GND)
    LCD I2C   SDA 21 / SCL 22 (5V + common GND)

  v2 fixes (after first bench test):
    - boot self-test: LEDs blink 3x so you know they work
    - standalone starts at 05:30 in WATTWISE mode -> green LED on and
      servo surging (precool) the moment it powers up
    - LCD only rewritten when text changes (kills the flicker)
    - servo writes only on movement (less hum/jitter)
    - 360 fan mode for continuous-rotation servos (see below)

  360 DEGREES LIKE A FAN?
    Turn the servo horn gently by hand:
      - it hits a hard stop around half a turn -> POSITIONAL servo
        (physically cannot spin 360; it oscillates 0-180 like an
        oscillating fan instead - set CONTINUOUS_ROTATION false)
      - it spins freely forever -> CONTINUOUS-rotation servo
        (set CONTINUOUS_ROTATION true: it spins one direction, fast
        outside the peak, SLOW through the billed window)

  JITTER / LCD FLICKER:
    A servo on the ESP32 5V pin pulls big current spikes from USB and
    sags the whole rail (LCD flickers, motor stutters). Power the servo
    from its OWN 5V supply (battery pack, or a phone charger through a
    cut USB cable), keep all grounds tied together. This is wiring, not
    code - no sketch can fix a brownout.

  Libraries (Library Manager): "ESP32Servo", "LiquidCrystal I2C".
  LCD blank? try LCD_ADDR 0x3F instead of 0x27.
  Tandem with the CLI:  python wattwise.py --port COMx
*/

#include <ESP32Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ---------------- user config ----------------
#define CONTINUOUS_ROTATION true   // true only for continuous-rotation servos
#define LCD_ADDR 0x27
#define BAUD 115200

// ---------------- pins ----------------
static const int LED_RED = 19;
static const int LED_GREEN = 18;
static const int SERVO_PIN = 13;

// ---------------- demo windows (hours, mirrors scheduler.py) ----------
static const float PEAK_START = 8.5, PEAK_END = 10.5;   // billed window
static const float PRECOOL_START = 5.5, PRECOOL_END = 8.0;

// ---------------- positional servo sweep (ms per degree) ---------------
static const int STEP_FAST = 10;    // non-peak: high speed
static const int STEP_PRECOOL = 5; // precool surge: maximum
static const int STEP_SLOW = 60;   // peak window coast: low speed

// ---------------- continuous servo pulse widths (us) -------------------
static const int PULSE_FAST = 2000;   // full speed forward
static const int PULSE_SLOW = 1600;   // crawl forward (peak window)
static const int PULSE_STOP = 1500;   // neutral

// ---------------- standalone clock ----------------
static const unsigned long TICK_MS = 6250;      // 48 steps = 5 min per day
static const unsigned long LINK_TIMEOUT_MS = 3000;
static const int START_MINUTE = 5 * 60 + 30;    // boot at 05:30 (precool!)

LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);
Servo servo;

// ---------------- state ----------------
int simMinute = START_MINUTE;
char serMode[10] = "wattwise";   // standalone default: wattwise demo on
char serState[12] = "";          // "", NORMAL, PRECOOL, PEAK, DUMB
float grantedKw = 0.0;
unsigned long lastSerialMs = 0;
unsigned long lastTickMs = 0;
unsigned long lastServoMs = 0;
unsigned long lastBlinkMs = 0;
bool blinkOn = false;
char lcdLine0[17] = "", lcdLine1[17] = "";   // lcd cache: write on change only
int lastPulse = -1;                          // servo cache for continuous mode

// positional sweep state
int servoPos = 90;
int servoDir = 1;

float hourNow() { return (simMinute % 1440) / 60.0; }
bool inPeak() { float h = hourNow(); return h >= PEAK_START && h < PEAK_END; }
bool inPrecool() { float h = hourNow(); return h >= PRECOOL_START && h < PRECOOL_END; }
bool wattwiseActive() { return strcmp(serMode, "wattwise") == 0; }

String stateWord() {
  // serial word wins when linked; otherwise derive from the clock
  if (lastSerialMs && strlen(serState)) return String(serState);
  if (!wattwiseActive()) return "DUMB";
  if (inPeak()) return "PEAK";
  if (inPrecool()) return "PRECOOL";
  return "NORMAL";
}

void handleLine(char *line) {
  // protocol from the CLI: S,HH:MM,mode,STATE,KW
  if (line[0] != 'S' || line[1] != ',') return;
  char *p1 = strchr(line + 2, ',');   if (!p1) return; *p1 = 0;
  char *p2 = strchr(p1 + 1, ',');     if (!p2) return; *p2 = 0;
  char *p3 = strchr(p2 + 1, ',');     if (!p3) return; *p3 = 0;
  const char *t = line + 2, *mode = p1 + 1, *st = p2 + 1, *kw = p3 + 1;
  int hh = 0, mm = 0;
  if (sscanf(t, "%d:%d", &hh, &mm) == 2)
    simMinute = (hh * 60 + mm) % 1440;
  strncpy(serMode, mode, sizeof(serMode) - 1); serMode[sizeof(serMode) - 1] = 0;
  strncpy(serState, st, sizeof(serState) - 1); serState[sizeof(serState) - 1] = 0;
  grantedKw = atof(kw);
  lastSerialMs = millis();
}

void driveServo() {
  String st = stateWord();

  if (CONTINUOUS_ROTATION) {
    // continuous servo: spin one direction, speed = state
    int pulse = PULSE_FAST;
    if (st == "PEAK") pulse = wattwiseActive() ? PULSE_SLOW : PULSE_FAST;
    if (pulse != lastPulse) {          // write once per change only
      servo.writeMicroseconds(pulse);
      lastPulse = pulse;
    }
    return;
  }

  // positional servo: oscillate 0..180 like an oscillating fan,
  // speed = state (fewer, smaller writes = less hum)
  int stepMs = STEP_FAST;
  if (st == "PEAK")          stepMs = wattwiseActive() ? STEP_SLOW : STEP_FAST;
  else if (st == "PRECOOL")  stepMs = STEP_PRECOOL;
  unsigned long now = millis();
  if (now - lastServoMs >= (unsigned long)stepMs) {
    lastServoMs = now;
    servoPos += servoDir;
    if (servoPos >= 180) { servoPos = 180; servoDir = -1; }
    else if (servoPos <= 0) { servoPos = 0; servoDir = 1; }
    servo.write(servoPos);
  }
}

void driveLeds() {
  unsigned long now = millis();
  bool peak = inPeak();
  bool managed = wattwiseActive();
  // green: wattwise active (on from boot in standalone)
  digitalWrite(LED_GREEN, managed ? HIGH : LOW);
  // red: peak window; solid when coasting, blinking when dumb/unmanaged
  if (peak) {
    if (managed) {
      digitalWrite(LED_RED, HIGH);
    } else {
      if (now - lastBlinkMs >= 250) { lastBlinkMs = now; blinkOn = !blinkOn; }
      digitalWrite(LED_RED, blinkOn ? HIGH : LOW);
    }
  } else {
    digitalWrite(LED_RED, LOW);
  }
}

void lcdShow(const char *l0, const char *l1) {
  // only touch the lcd when a line actually changed (stops flicker)
  if (strncmp(l0, lcdLine0, 16) != 0) {
    strncpy(lcdLine0, l0, 16); lcdLine0[16] = 0;
    lcd.setCursor(0, 0); lcd.print(lcdLine0);
  }
  if (strncmp(l1, lcdLine1, 16) != 0) {
    strncpy(lcdLine1, l1, 16); lcdLine1[16] = 0;
    lcd.setCursor(0, 1); lcd.print(lcdLine1);
  }
}

void driveLcd() {
  char l0[17], l1[17];
  snprintf(l0, sizeof(l0), "%02d:%02d %-8s",
           simMinute / 60, simMinute % 60,
           wattwiseActive() ? "WATTWISE" : "BASELINE");
  String st = stateWord();
  if (st == "PEAK") st = wattwiseActive() ? "COAST" : "UNMANAGED";
  snprintf(l1, sizeof(l1), "%-8s %5.0f kW", st.c_str(), grantedKw);
  lcdShow(l0, l1);
}

void bootSelfTest() {
  // 3 blinks on both LEDs: proves LED wiring at power-up
  lcdShow("WattWise node", "LED test");
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_GREEN, HIGH); digitalWrite(LED_RED, LOW);  delay(150);
    digitalWrite(LED_GREEN, LOW);  digitalWrite(LED_RED, HIGH); delay(150);
  }
  digitalWrite(LED_RED, LOW);
  // one slow full sweep: proves servo signal+power at power-up.
  // if the horn does not move here, it is wiring/power/dead servo.
  lcdShow("WattWise node", "servo sweep...");
  for (int p = 90; p <= 180; p += 2) { servo.write(p); delay(20); }
  for (int p = 180; p >= 0; p -= 2)   { servo.write(p); delay(20); }
  for (int p = 0; p <= 90; p += 2)    { servo.write(p); delay(20); }
  servoPos = 90; servoDir = 1;
  lcdShow("WattWise node", "05:30 precool");
}

void setup() {
  Serial.begin(BAUD);
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_GREEN, LOW);
  servo.setPeriodHertz(50);
  servo.attach(SERVO_PIN, 500, 2400);
  servo.write(servoPos);
  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();
  bootSelfTest();
  lastTickMs = millis();
}

void loop() {
  // 1. serial link from the CLI
  static char buf[64];
  static uint8_t n = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (n) { buf[n] = 0; handleLine(buf); n = 0; }
    } else if (n < sizeof(buf) - 1) {
      buf[n++] = c;
    }
  }
  unsigned long now = millis();
  if (lastSerialMs && now - lastSerialMs > LINK_TIMEOUT_MS) {
    // link lost -> back to the standalone demo, wattwise on
    lastSerialMs = 0;
    serState[0] = 0;
    strcpy(serMode, "wattwise");
  }
  // 2. standalone compressed day when not linked
  if (!lastSerialMs && now - lastTickMs >= TICK_MS) {
    lastTickMs = now;
    simMinute = (simMinute + 30) % 1440;
  }
  // 3. hardware
  driveServo();
  driveLeds();
  driveLcd();
}
