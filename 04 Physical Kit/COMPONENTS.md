# WattWise Physical Demo Kit — Components & Wiring

The tabletop prop for the WattWise pitch: an ESP32 node that physically
acts out what the scheduler does. Servo = the chiller plant (sweeps fast
off-peak, crawls through the billed window), LEDs = the tariff windows,
LCD = the dispatcher's readout. Runs standalone
or tandem with the CLI over USB.

## Bill of materials

| #   | Component                                     | Qty   |
| --- | --------------------------------------------- | ----- |
| 1   | ESP32 dev board (30-pin)                      | 1     |
| 2   | Positional servo, 0–180° (SG90 class)         | 1     |
| 3   | LED red 5 mm                                  | 1     |
| 4   | LED green 5 mm                                | 1     |
| 5   | Resistor 220 Ω                                | 2     |
| 6   | LCD 16x2 with I2C backpack (PCF8574)          | 1     |
| 7   | Breadboard + jumper wires                     | 1 set |
| 8   | Micro-USB cable (data)                        | 1     |
| 9   | Push button (optional)                        | 1     |
| 10  | External 5V supply (optional but recommended) | 1     |

## Pin map

| Peripheral | Pin | Wiring |
|---|---|---|
| LED red | GPIO 19 | 220 Ω in series to GND (resistor either side of the LED is fine) |
| LED green | GPIO 18 | 220 Ω in series to GND |
| Servo signal | GPIO 13 | yellow/orange |
| Servo power | 5V / VIN | red — use the external pack if jitter appears |
| Servo ground | GND | brown/black — COMMON with everything |
| LCD SDA | GPIO 21 | I2C data |
| LCD SCL | GPIO 22 | I2C clock |
| LCD power | 5V / VIN | |
| Power button | GPIO 0 | onboard BOOT button; or breadboard button to GND on GPIO 27 |

**All grounds tie together** — ESP32, servo, LCD, external pack if used.

## What it does

- **Power-up:** silent (screen dark, servo limp). Press the button →
  LED blink test → servo sweep test → demo starts at 05:30 precool.
  Press again anytime → "powering off..." → quiet until next press.
- **Standalone:** one simulated day per 5 minutes. Green = off-peak,
  servo sweeps briskly; at 08:30–10:30 red comes on and the sweep goes
  visibly lazy (WattWise coasting).
- **Tandem with the CLI** (recommended for judging):
  `python wattwise.py --port COM3` from `03 User Interface` — the CLI
  becomes the clock. `set time 09:00` / `mode dumb` / `play` drive the
  hardware live; the LCD shows the live kW granted to whatever
  building/town is selected on screen. Dumb mode at peak = servo stays
  fast + red LED blinks + LCD reads WASTED — the before/after shot.

## Software

- Sketch: `esp32/wattwise_demo/wattwise_demo.ino` (Arduino IDE,
  board "ESP32 Dev Module"; libraries: ESP32Servo, LiquidCrystal I2C).

