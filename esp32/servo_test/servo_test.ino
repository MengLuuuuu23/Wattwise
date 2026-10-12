/*
  servo_test - bare minimum sweep to isolate a silent servo
  Flashes GPIO 13 ONLY: nothing else is initialized.
  If this moves the servo, your wiring/power are fine and the issue is
  in the main sketch setup; if it does NOT move, it is wiring, power,
  or a dead servo - no sketch can fix that.

  Watch for: movement should be a steady back-and-forth sweep taking
  about 3 seconds each way. Jitter or stutter here = power problem
  (servo needs its own 5V supply, common ground with the ESP32).
*/

#include <ESP32Servo.h>

Servo servo;

void setup() {
  servo.setPeriodHertz(50);
  servo.attach(13, 500, 2400);
  servo.write(90);
  delay(500);
}

void loop() {
  // sweep 0 -> 180 -> 0, steady pace
  for (int p = 0; p <= 180; p += 2) {
    servo.write(p);
    delay(15);
  }
  for (int p = 180; p >= 0; p -= 2) {
    servo.write(p);
    delay(15);
  }
}
