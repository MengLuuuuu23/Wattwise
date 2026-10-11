# WattWise - Technical Build Plan (WATTWISE-1 and WATTWISE-2)

The engineering document: how to actually build both models, end to end. This expands `02-BUILD-GUIDE.md` into full implementation detail. Stack assumption: Python 3.11+, PyTorch, pandas/numpy, scikit-learn, matplotlib for figures, FastAPI + the existing widget HTML for the demo front end. Everything runs locally; no cloud dependency on stage wifi.

---

## Part 0 - Data foundation (both models share this)

### 0.1 Time base

Everything is on a **30-minute grid** (48 slots/day). This is not arbitrary: the demand charge is set by the highest 30-minute interval, and Malaysian interval meters and SEDA applications all use 30-minute readings. Every dataset, feature, prediction and schedule action lives on this grid.

### 0.2 What to acquire, in priority order

| Priority | Data | Source | Use |
|---|---|---|---|
| 1 | 30-min interval load (kW), 12+ months | SDP/GSPARX pilot site export, read-only | both models, baseline peak |
| 2 | 30-min PV generation (kW), same period | inverter logs (SolarEdge/Fronius/Huawei export CSV) | W1 target, W2 supply |
| 3 | Weather: irradiance (GHI), ambient temp, wind, humidity | [Solcast API](https://solcast.com/) (free tier) or MET Malaysia | W1 input, W2 forecast |
| 4 | PV module temperature | inverter sensor logs; else estimate from ambient + irradiance | W1 input |
| 5 | Building context: floor area, chiller specs, operating hours | site one-pager from mentors | W2 thermal model sizing |

If Priority 1-2 are unavailable before the deadline (likely), fall back to published measured data: Wisma R&D bills (load), Monash GCPV 5-min PV series (generation), both linked in `03-FACTS-AND-SOURCES.md`. Synthetic fallback generator is specified in 0.3.

### 0.3 Synthetic fallback generator (do this first regardless, it is also the demo)

Deterministic, seeded, reproducible:

```python
import numpy as np

def solar_kw(t):                      # t = 0..47, 30-min slots
    h = t / 2
    x = (h - 12.8) / 3.6              # peak ~12:48, sigma 3.6h
    v = 600 * np.exp(-x * x)          # 600 kWp site
    # tropical cloud noise: 3 stochastic dips, seeded
    rng = np.random.default_rng(42)
    for _ in range(3):
        dip_start = rng.integers(16, 40)   # between 8am-8pm
        dip_len = rng.integers(1, 3)
        v[dip_start:dip_start+dip_len] *= rng.uniform(0.3, 0.7)
    return np.maximum(v, 0)

def base_load_kw(t):
    h = t / 2
    v = np.full(48, 260.0)            # night base
    v[(h>=6)&(h<8)]   = 260 + (h[(h>=6)&(h<8)]-6)/2*420      # ramp
    v[(h>=8)&(h<11)]  = 680 + 270*np.sin((h[(h>=8)&(h<11)]-8)/3*np.pi)  # peak ~950
    v[(h>=11)&(h<14)] = 780
    v[(h>=14)&(h<18)] = 720 - (h[(h>=14)&(h<18)]-14)*30
    v[(h>=18)&(h<22)] = 620 - (h[(h>=18)&(h<22)]-18)*55
    v[h>=22] = 300
    return v
```

Validation gates for the synthetic data: peak lands 8:30-10:30 (matches measured MDRed capture), solar bell 11:00-14:00, night load plausible vs Wisma R&D average band (220-340 kW). These three checks make the synthetic set defensible on stage: "shaped to match published measured Malaysian profiles".

---

## Part 1 - WATTWISE-1: the prediction model

Two heads, one shared dataset: **solar generation** and **building demand**. Same architecture pattern for both; train separately.

### 1.1 Problem framing

- **Task A (solar):** predict PV kW for the next 1-6 slots (30 min to 3 h ahead), per site.
- **Task B (demand):** predict building load kW for the same horizons.
- **Horizon choice:** the scheduler needs (a) enough lead time to pre-cool before 8:30am, (b) coverage of the 8:30-10:30 window. So the operational forecast is the **6-slot (3 h) horizon**, with 1-slot (30 min) as the accuracy headline number to compare against published benchmarks.

### 1.2 Feature set (per timestamp t)

| Feature | Why | Source |
|---|---|---|
| GHI (W/m2), current + last 4 slots | dominant PV driver, PCC 0.96 | weather API |
| PV module temp (C) | efficiency loss, PCC 0.88 | inverter/est |
| Ambient temp (C) | load driver (cooling) + PV | weather |
| Wind speed (m/s) | cooling of modules, PCC 0.51 | weather |
| Hour-of-day (sin/cos encoded) | daily cycle both heads | derived |
| Lagged target: t-1..t-4 | persistence baseline the LSTM must beat | meter/inverter |
| Day-type flag (weekday/weekend/holiday) | load shape differs | calendar |

Keep the feature count small. The IJIE paper won with four features; adding weak ones hurts.

### 1.3 Architecture

```python
class ForecastLSTM(nn.Module):
    def __init__(self, n_features=9, hidden=64, layers=2, horizon=6):
        super().__init__()
        self.lstm = nn.LSTM(n_features, hidden, layers,
                            batch_first=True, dropout=0.1)
        self.head = nn.Linear(hidden, horizon)   # predicts next 6 slots
    def forward(self, x):                        # x: (B, 24, 9) = 12h lookback
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :])
```

- Lookback window: **24 slots (12 h)**. Literature (RAST sliding-window study) shows longer windows help; 24 is the sweet spot for 48-slot days.
- Input normalisation: z-score per feature, statistics saved for inference.
- Loss: MSE for training, but **report nRMSE and R2** to match the published benchmarks (nRMSE 6.75% / R2 0.957 @ 30-min, IJIE 2025).

### 1.4 Training protocol

1. **Split by time blocks, never shuffled:** oldest 70% train, next 15% validation, newest 15% test. Shuffling a time series leaks the future and inflates accuracy.
2. **Baselines first, network second.** Persistence (yhat(t+1) = y(t)) and linear regression on the same features. The LSTM must beat persistence on the test block or the features are wrong. Report all three; judges love a beaten baseline.
3. **Hyperparameters:** hidden {32, 64, 128}, layers {1, 2}, dropout {0.0, 0.1}, lr 1e-3 with Adam, early stopping on validation loss (patience 10 epochs). A 20-30 config grid search is a poor man's Bayesian optimisation and is fine at this scale; say "grid search over the published hyperparameter ranges" on stage.
4. **Overfitting guards:** early stopping, dropout, and a learning curve plot (train vs val loss) in the appendix.
5. **Expected result on synthetic data:** R2 well above 0.9 at 1-slot (synthetic is easier than reality, say so); on real data, target R2 0.90+ at 30-min, degrading to ~0.85 at 3 h. If far off, check for feature misalignment (weather timestamp vs slot timestamp is the classic bug).

### 1.5 Acceptance criteria

- [ ] Beats persistence on test block for both heads
- [ ] 30-min solar forecast nRMSE within striking distance of published 6.75% (synthetic will be lower; real data may be higher, both honest)
- [ ] Horizon 6 forecast covers the 8:30-10:30 window from a 5:30am prediction (verify timestamps end to end)
- [ ] Inference runs in <50 ms on CPU (it will; needed for the live demo)

### 1.6 Honest labelling on slides

Until real data: "prototype achieves X on simulated site data shaped to published Malaysian profiles; published benchmark for this model class on real Malaysian rooftop PV is nRMSE 6.75% / R2 0.957 (IJIE 2025)". Never blend the two numbers into one claim.

---

## Part 2 - WATTWISE-2: the scheduler

Build in three stages. Each stage is demo-able; do not skip to stage 3.

### Stage 1 - Rule engine (v0, one day of work)

The core insight frozen in code. States follow the day:

```python
def schedule(slot, solar_forecast, zone_temp, cold_store):
    h = slot / 2
    if 5.0 <= h < 7.5:                    # PRECOOL
        return {"chiller": "MAX", "pumps": "ON", "note": "store cold cheap"}
    if 8.5 <= h < 10.5:                   # COAST (billed window)
        return {"chiller": "MIN", "pumps": "OFF", "note": "spend stored cold"}
    if 11.0 <= h < 14.5 and solar_forecast > 400:   # SOAK
        return {"chiller": "MAX", "pumps": "ON", "note": "run on solar"}
    if 15.0 <= h < 17.0:                  # RELIEF
        return {"chiller": "LOW", "pumps": "AS_NEEDED"}
    return {"chiller": "TRACK", "pumps": "AUTO"}    # NORMAL
```

Guards: comfort is a **hard constraint**. If zone temp >= 25.5C, override state, chill (comfort wins over savings, always, and log the override).

### Stage 2 - Building thermal model (the "digital twin lite")

First-order lumped model, enough fidelity to prove comfort holds while the bill drops:

```python
# zone temperature dynamics, 30-min steps
T[t+1] = T[t] + dt * ( (T_amb[t] - T[t])/tau + Q_internal/C
                       + Q_solar_gain[t]/C - chiller_kw[t]/COP/C )
```

- `tau` (thermal time constant): 2-4 h for concrete construction. Calibrate by hand: run the sim with chillers off, check the building warms ~1C/hour (the blackout test).
- `COP` (chiller coefficient of performance): 4-6 for Malaysian water-cooled plant; use 5 and say it's an assumption.
- `Q_internal`: occupancy + equipment heat; tune so the unmanaged baseline matches the synthetic load curve's shape.
- Cold store bookkeeping: kWh of cooling stored/released, tracked on the same grid.

**The demo money shot:** one figure, two panels. Top: grid draw, unmanaged vs scheduled (peak visibly cut ~717 to ~565 kW territory). Bottom: zone temperature with the 24-26C comfort band shaded, line staying inside. Bill falls AND comfort holds, simultaneously, from the same simulation run. This is the single most persuasive artifact the team can produce.

### Stage 3 - Learning scheduler (RL), only after 23 Oct

- **Environment:** Stage 2 thermal model wrapped in a Gym interface. State = (hour, zone temp, cold store, solar forecast next 3h, current load). Action = chiller level in {MIN, LOW, TRACK, MAX} (discrete, 4 actions). Reward = `-kWh_cost(t) - big_penalty * comfort_violation(t)` with the demand-charge peak added as a terminal bonus each simulated month: `reward -= 97.06 * max(0, peak_new - peak_prev)`.
- **Algorithm:** DQN first (discrete actions, small state, fast to train). Double-DQN if time permits. Tabular Q-learning is an acceptable fallback and trains in minutes on this state space.
- **Expected behaviour:** the agent should *discover* pre-cooling, as the NREL controller did. If it does, that's a slide: "our scheduler learned pre-cooling unprompted, replicating NREL's real-building result". If it doesn't, the reward shaping is wrong, check the demand-charge term.
- **Training:** 10k+ simulated days, evaluate on held-out weather sequences. Report vs Stage 1 rules: the bar is "beats rules by X% at equal comfort violations (zero)".

### Integration contract between W1 and W2

```
every 30 min:
    feats   = read(meters, inverter, weather_api)          # SENSE
    f_solar, f_load = W1.predict(feats, horizon=6)          # PREDICT
    actions = W2.schedule(state, f_solar, f_load)           # SCHEDULE
    bms.send(actions)  [demo: sim.step(actions)]            # ACT
    log(everything)                                         # LEARN + EECA trail
```

The 30-minute cadence matches the billing interval, which is the whole design point.

---

## Part 3 - Verification and honest numbers

| Claim on slide | Backing |
|---|---|
| "-20% peak" | simulation output vs unmanaged baseline; NREL 20% real-building benchmark |
| "RM14.7k/month saved" | (717-565) x RM97.06 arithmetic on the sim |
| "comfort never broken" | Stage 2 sim with overrides logged |
| "R2 0.9+" | W1 test block, clearly labelled synthetic-or-real |

Every figure keeps its "illustrative / prototype / published benchmark" tag. The sources ledger (`03-FACTS-AND-SOURCES.md`) is the single place facts live; slides cite, never invent.

## Part 4 - Repo layout and division of labour (3-5 people)

```
wattwise/
  data/          raw + synthetic generators + README on provenance
  models/
    w1_forecast/  train.py, evaluate.py, checkpoints/
    w2_schedule/  rules.py, thermal.py, env.py, train_rl.py
  sim/           day_simulator.py (drives the demo figures)
  api/           fastapi app exposing /forecast /schedule /state
  demo/          dashboard HTML (adapt compare_widget.html)
  figures/       every slide figure, generated by scripts not hand-drawn
```

Suggested split: one on W1, one on W2 rules + thermal, one on demo/dashboard, one on data + figures, one on deck + QA (rehearsing against `05-QA-CRIB-SHEET.md`).

## Part 5 - Risks and fallbacks

| Risk | Fallback |
|---|---|
| No real data by finale | synthetic set shaped to published profiles, labelled as such |
| RL doesn't converge | ship Stage 1 rules + thermal sim; RL becomes "next step" honestly |
| BMS protocol question from judge | "read-only pilot first; write access follows a proven forecast on their own data" |
| Numbers challenged | everything traces to the sources ledger or the sim script, both in repo |
| Demo machine fails | pre-render figures + a recorded screen capture as backup |
