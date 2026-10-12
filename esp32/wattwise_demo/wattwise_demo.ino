/*
  WattWise physical demo node - ESP32 (v4, POSITIONAL servo, fan sweep)
  =====================================================================
  VERDICT from the bench: the servo is POSITIONAL (0-180, hard stops).
  Proof: v3.1 commanded write(180) constantly and the horn swung to one
  extreme and PARKED - a continuous servo would have spun. Positional
  servos cannot spin 360; continuous motion for them = an oscillating
  fan sweep, which is what this sketch does.

  Wiring:
    LED red   GPIO 19 (220R to GND)
    LED green GPIO 18 (220R to GND)
    Servo     GPIO 13 (5V + common GND)
    LCD I2C   SDA 21 / SCL 22 (5V + common GND)

  Behaviour:
    Servo = the chiller plant, oscillating like a fan:
      - fast sweep outside the billed window
      - SLOW sweep through the peak window 08:30-10:30 in wattwise mode
      - stays FAST through the peak in dumb mode (the waste we sell
        against), red LED blinking to call it out
    Green LED = off-peak window (outside 08:30-10:30)
    Red LED   = peak window (solid when coasting, blinking when dumb)
    LCD row 1 = clock + mode, row 2 = state + kW (kW only when the CLI
      is linked; standalone honestly shows "no link")

  Standalone: boots at 05:30 wattwise (precool, green on, sweeping);
    compressed day = 5 minutes. Peak lands ~37 s after boot.
  Tandem: python wattwise.py --port COMx  (CLI becomes the clock;
    set time / mode / play drive the hardware live)

  Tuning: smaller STEP_xx = faster sweep. If motion is jittery, that is
  the power rail: feed the servo its own 5V (battery pack), common GND.
*/

#include <ESP32Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ---------------- user config ----------------
#define LCD_ADDR 0x27
#define BAUD 115200

// ---------------- pins ----------------
static const int LED_RED = 19;
static const int LED_GREEN = 18;
static const int SERVO_PIN = 13;

// ---------------- demo windows (hours, mirrors scheduler.py) ----------
static const float PEAK_START = 8.5, PEAK_END = 10.5;   // billed window
static const float PRECOOL_START = 5.5, PRECOOL_END = 8.0;

// ---------------- positional sweep speed (ms per degree step) ---------
static const int STEP_FAST = 5;     // off-peak: fast fan sweep
static const int STEP_PRECOOL = 3; // precool surge: maximum
static const int STEP_SLOW = 50;   // peak window coast: lazy sweep

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

// sweep state
int servoPos = 90;
int servoDir = 1;

float hourNow() { return (simMinute % 1440) / 60.0; }
bool inPeak() { float h = hourNow(); return h >= PEAK_START && h < PEAK_END; }
bool inPrecool() { float h = hourNow(); return h >= PRECOOL_START && h < PRECOOL_END; }
bool wattwiseActive() { return strcmp(serMode, "wattwise") == 0; }

String stateWord() {
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
  // positional servo: oscillate 0..180 like an oscillating fan.
  // Speed = ms per degree: fast normally, lazy through the peak.
  String st = stateWord();
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
  // window indicators: green = off-peak, red = peak window.
  // red blinks when the peak is unmanaged (dumb mode) - the waste visual
  digitalWrite(LED_GREEN, peak ? LOW : HIGH);
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
  if (st == "PEAK") st = wattwiseActive() ? "COAST" : "WASTED";
  if (lastSerialMs) {
    // linked: kW granted comes live from the CLI
    snprintf(l1, sizeof(l1), "%-8s %5.0f kW", st.c_str(), grantedKw);
  } else {
    // standalone: no data source for kW - say so instead of faking 0.
    // keep it short: longest state (PRECOOL) + this text must fit 16 cols
    snprintf(l1, sizeof(l1), "%-8s offline", st.c_str());
  }
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
  // positional boot test: one gentle full sweep 90->180->0->90.
  // If the horn does not sweep here, it is wiring/power/dead servo.
  lcdShow("WattWise node", "servo sweep test");
  for (int p = 90; p <= 180; p += 2) { servo.write(p); delay(15); }
  for (int p = 180; p >= 0; p -= 2)   { servo.write(p); delay(15); }
  for (int p = 0; p <= 90; p += 2)    { servo.write(p); delay(15); }
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
