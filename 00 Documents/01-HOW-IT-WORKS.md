# WattWise - How It Works

WattWise is an **invisible software layer that connects to existing meters and building controls**. It reads data the building already produces and sends schedule commands to equipment the building already owns. It never touches sealed utility meters, never requires firmware access, and never generates or stores electricity itself.

## The closed loop

```
SENSE -> PREDICT (WATTWISE-1) -> SCHEDULE (WATTWISE-2) -> ACT (via BMS) -> re-measure
```

The loop re-plans every 30 minutes, deliberately matching the interval the demand charge is measured on.

### 1. SENSE

Inputs, all already available in a modern commercial building:

- 30-minute interval meter data (main incomer and sub-meters)
- Inverter/generation logs from rooftop solar
- Weather forecast (irradiance, temperature, wind)
- The TNB tariff structure and peak windows
- Building state: zone temperatures, chiller status, tank levels

### 2. WATTWISE-1: Solar + demand prediction

**What it predicts:** solar output and building demand, 30 minutes to 3 hours ahead, at 30-minute resolution.

**Inputs (the four that matter):** global horizontal irradiance, PV module temperature, ambient temperature, wind speed. These are the features published Malaysian studies found significantly correlated with PV output (PCC 0.51-0.96). Plus the site's own generation history from inverter logs.

**Architecture:** LSTM (recurrent network), which handles tropical cloud-ramp events, the genuinely hard part of Malaysian solar forecasting.

**Training:** on the site's own history. Bayesian optimisation for hyperparameters, k-fold cross-validation against overfitting. Site-tuned, not global: each building's panels get their own model.

**Published accuracy (Malaysian data, not our result yet):**

| Benchmark | Result | Source |
|---|---|---|
| LSTM, rooftop PV, 30-min ahead | nRMSE 6.75%, R2 0.957 | [IJIE 17(2) 2025, Penang](https://journal.uthm.edu.my/index.php/ijie/article/download/17144/7422/103525) |
| LSTM + weather forecast, 8 MWp farm | R2 0.92 day-ahead | [Ayer Keroh, Malacca case study](https://exa.ai/library/publication/5sjhrt2fcfs) |
| Sliding-window LSTM, 25 MWac | up to 30.7% MAE reduction | [RAST 2025, Pasir Gudang](https://ph01.tci-thaijo.org/index.php/RAST/article/view/263014) |

Why good enough: ~93% of variance explained half an hour ahead is ample lead time to pre-cool. A 7% error on a 600 kWp array is about 40 kW, well inside the margin of a 100 kW shave target. The scheduler needs *when* and *roughly how much*, not a perfect curve.

### 3. WATTWISE-2: The scheduler

**What it controls (flexible loads only):**

- Chiller start times (pre-cool early, coast through peak)
- Water pumps (fill tanks at midday: "a battery made of water")
- Equipment sequencing (never two big motors in the same half hour)

**What it never touches:** comfort. Zone temperatures stay inside the comfort band, always. This is a hard constraint, not a preference.

**How it decides:** optimisation plus reinforcement learning.

- Train offline on a **digital twin** (building simulator such as EnergyPlus calibrated to the site) before touching real equipment.
- **Reward = bill saved, minus heavy penalties for any comfort violation.**
- Improves monthly as it learns the building's rhythm.

**Published evidence this works:**

- [NREL's deep-RL controller](https://www.energy.gov/sites/default/files/2023-05/bto-peer-2023-andreybernstein-modrlc.pdf) on a real 40-floor New York building (4 chillers, 8 cooling towers): **20% peak demand cut, 20% bill cut**, within 10% of a hand-built MPC. Critically, it **learned pre-cooling by itself** from the reward function. Pre-cooling is not our invention; it is what the objective function discovers.
- [DQN multi-zone HVAC study](https://www.osti.gov/pages/servlets/purl/1866667): **23% cost reduction**, also learned pre-heating unprompted.

**The physics: cold is the battery**

- Comfort is a range (about 24-26C), not a point. Most buildings pin one setpoint and waste the rest of the band.
- Pre-cool to the bottom of the band early; drift slowly to the top during the peak window. Concrete warms slowly, so the drift is gentle (about a degree per couple of hours). Occupants barely register it.
- Tropical caveat: humidity limits how far the band can open. This is why savings are claimed at a conservative 10% of MD, not the 20-65% battery vendors claim.
- Proof it works: during a mall blackout the building stays cool for an hour or more on thermal mass alone. WattWise times that effect deliberately.

**Honest constraint:** deferral only works on flexible loads (pre-cooling, pumps, anything with storage or inertia). Lighting when a shop is open or a lift in use cannot move far. The savings ceiling is set by the flexible fraction of load, which is why the product scopes to landlord common-area plant (chillers, pumps, ventilation), and why cooling's 26-58% share of building energy is the addressable pool.

### 4. ACT

Commands go to the existing BMS/BAS over standard protocols (Modbus, BACnet, vendor APIs). No new actuators, no new meters, no firmware in sealed utility devices.

## The township layer

SDP as LEGA aggregates solar across townships (CREAM). WattWise is pitched as the operating system for that aggregation: forecasting per site, scheduling per building, one dashboard across the estate, tenant billing and EECA reporting generated from the same data.

One nuance to keep straight: CREAM power is **wheeled through TNB's grid** to the receiving building; it is a contractual kWh supply, not panels behind the meter. So it offsets the energy line, while the demand charge lands on the receiving building's meter regardless (the timing mismatch: CREAM solar arrives midday, the billed peak is morning). Say "timing mismatch", not "billing mechanics"; the settlement detail is unverified.
