/*
  WattWise physical demo node - ESP32
  ===================================
  Hardware (see wiring plan):
    LED red   GPIO 19 (220R to GND)
    LED green GPIO 18 (220R to GND)
    Servo     GPIO 13 (5V/VIN + common GND)
    LCD I2C   SDA 21 / SCL 22 (5V/VIN + common GND)

  Behaviour:
    - Servo = the chiller plant. FAST outside the billed window,
      SLOW during the peak window 08:30-10:30 (WattWise coasting).
      In dumb (baseline) mode it stays FAST through the peak -
      the physical picture of the waste WattWise removes.
    - Red LED   = peak window (blinks when the peak is unmanaged/dumb)
    - Green LED = WattWise mode active
    - LCD row 1 = clock + mode, row 2 = state + kW of cooling granted

  Two ways to run:
    1) Tandem with the CLI (recommended): flash, then run
         python wattwise.py --port COMx
       The CLI streams "S,HH:MM,mode,STATE,kW" lines at 115200 and the
       node follows the on-screen clock exactly (scrub/play/react live).
    2) Standalone: no serial link for 3 s -> internal compressed clock
       (one simulated day per 5 minutes) cycles night/precool/peak/soak.

  Arduino IDE:
    Board: ESP32 Dev Module
    Libraries (Library Manager): "ESP32Servo" (Kevin Harrington),
    "LiquidCrystal I2C" (Frank de Brabander). LCD address is usually
    0x27; if blank, try 0x3F.

  If your servo is a CONTINUOUS-rotation model, set CONTINUOUS_ROTATION
  to true (speed = pulse offset from neutral instead of sweep position).
*/

#include <ESP32Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ---------------- user config ----------------
#define CONTINUOUS_ROTATION false   // true only for continuous-rotation servos
#define LCD_ADDR 0x27
#define BAUD 115200

// ---------------- pins ----------------
static const int LED_RED = 19;
static const int LED_GREEN = 18;
static const int SERVO_PIN = 13;

// ---------------- demo windows (hours, mirrors scheduler.py) ----------
static const float PEAK_START = 8.5, PEAK_END = 10.5;   // billed window
static const float PRECOOL_START = 5.5, PRECOOL_END = 8.0;

// ---------------- sweep speeds (ms per degree) ------------------------
static const int STEP_FAST = 4;     // non-peak: high speed
static const int STEP_PRECOOL = 3;  // precool surge: maximum
static const int STEP_SLOW = 40;    // peak window coast: low speed

// continuous-rotation pulse widths (us) if enabled
static const int PULSE_FAST = 2000;
static const int PULSE_SLOW = 1650;
static const int PULSE_STOP = 1500;

// ---------------- standalone clock ----------------
static const unsigned long TICK_MS = 6250;   // 48 steps x 6.25 s = 5 min/day
static const unsigned long LINK_TIMEOUT_MS = 3000;

LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);
Servo servo;

// ---------------- state ----------------
int simMinute = 0;              // 0..1439, from serial or internal clock
char serMode[8] = "dumb";       // dumb | wattwise
char serState[10] = "";         // "", DUMB, NORMAL, PRECOOL, PEAK
float grantedKw = 0.0;
unsigned long lastSerialMs = 0;
unsigned long lastTickMs = 0;
unsigned long lastLcdMs = 0;
unsigned long lastBlinkMs = 0;
bool blinkOn = false;

// servo sweep state
int servoPos = 90;
int servoDir = 1;
unsigned long lastServoMs = 0;

float hourNow() { return (simMinute % 1440) / 60.0; }
bool inPeak() { float h = hourNow(); return h >= PEAK_START && h < PEAK_END; }
bool inPrecool() { float h = hourNow(); return h >= PRECOOL_START && h < PRECOOL_END; }

// effective state: serial word wins when linked, windows decide otherwise
bool wattwiseActive() { return strcmp(serMode, "wattwise") == 0; }

String stateWord() {
  if (lastSerialMs && strlen(serState)) return String(serState);
  if (!wattwiseActive()) return "DUMB";
  if (inPeak()) return "PEAK";
  if (inPrecool()) return "PRECOOL";
  return "NORMAL";
}

void handleLine(char *line) {
  // expected: S,HH:MM,mode,STATE,KW
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
    int pulse = PULSE_FAST;
    if (st == "PEAK") pulse = wattwiseActive() ? PULSE_SLOW : PULSE_FAST;
    servo.writeMicroseconds(pulse);
    return;
  }
  // positional servo: sweep 0..180, speed = state
  int stepMs = STEP_FAST;
  if (st == "PEAK")      stepMs = wattwiseActive() ? STEP_SLOW : STEP_FAST;
  else if (st == "PRECOOL") stepMs = STEP_PRECOOL;
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
  // green: wattwise mode active
  digitalWrite(LED_GREEN, managed ? HIGH : LOW);
  // red: peak window; solid when WattWise manages it, blinking when dumb
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

void driveLcd() {
  unsigned long now = millis();
  if (now - lastLcdMs < 500) return;
  lastLcdMs = now;
  char l0[17], l1[17];
  snprintf(l0, sizeof(l0), "%02d:%02d %-8s",
           simMinute / 60, simMinute % 60,
           wattwiseActive() ? "WATTWISE" : "BASELINE");
  String st = stateWord();
  if (st == "PEAK") st = wattwiseActive() ? "COAST" : "UNMANAGED";
  snprintf(l1, sizeof(l1), "%-8s %5.0f kW", st.c_str(), grantedKw);
  lcd.setCursor(0, 0); lcd.print(l0);
  lcd.setCursor(0, 1); lcd.print(l1);
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
  lcd.setCursor(0, 0); lcd.print("WattWise node");
  lcd.setCursor(0, 1); lcd.print("booting...");
  delay(800);
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
    // link lost -> fall back to the internal clock
    lastSerialMs = 0;
    serState[0] = 0;
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
