# WattWise - Build Guide (to 23 October, then to 14 November)

Two targets: the **proposal (23 Oct)** needs a credible story; the **finale (14 Nov)** needs a working demo. A proposal-stage entry does not need a finished product, but a simulated demo is the difference between a concept deck and a shortlisted one.

## Phase 1: the demo simulation (highest value, do first)

Build the simulation we already prototyped as the interactive widget and time graph. It is a 48-slot half-hourly model:

**Model spec (Python, numpy/matplotlib, then a small web view):**

```
solar(t):   bell curve peaking 12:48, sigma 3.6h, 600 kWp scale, floor 0
baseLoad(t): night 260 kW; ramp 6-8am to 680; morning peak 950 at 9:30;
            midday 780; decline 720->600 through afternoon; evening 620->300
Battery:    500 kWh capacity, 250 kW max charge/discharge,
            discharges when net load > 620 kW, charges on surplus 10:00-14:00
WattWise:   +140 kW 5:00-7:30 (pre-cool); -190 kW 8:00-11:00 (coast);
            +150 kW 11:00-14:30 when solar > 400 (soak); -80 kW 15:00-17:00
```

Expected outputs (verify against these): battery building peak ~717 kW, WattWise peak ~565 kW, RM69,584 vs RM54,862/month at RM97.06/kW.

**Deliverables:** the day-curve comparison figure (white bg, red vs dashed amber, solar gold area, peak-window band 8:30-10:30), and an animated scrub-through version for the live pitch.

## Phase 2: WATTWISE-1 prototype

**Data options, in order of strength:**

1. Real 30-min interval data from SDP or a landlord (ask during mentoring sprint; they respond well to "we only need read-only meter exports").
2. Published measured profiles: [Wisma R&D UM](https://doi.org/10.1049/cp.2018.1305) (3 years of C1 bills, MD 628-1,001 kW), [Monash Malaysia GCPV paper](https://www.sciencedirect.com/science/article/abs/pii/S0960148121002871) (232.5 kWp, 5-min data, 2019, PR 85.4%).
3. Synthetic: physical solar model (clear-sky curve + cloud noise, use PVLIB or even the bell model above) + a load profile from the literature.

**Model:**

- Start with a plain LSTM (PyTorch, ~2 layers, 64-128 hidden). Inputs: irradiance, module temp, ambient temp, wind, hour-of-day, plus lagged power.
- Train/val/test split by time blocks (never shuffle time series). Metrics: nRMSE and R2, report against the published benchmark (nRMSE 6.75%, R2 0.957 @ 30-min ahead).
- Baselines to beat: persistence (predict last value) and linear regression. If you cannot beat persistence, the features are wrong, not the network.
- On synthetic data you can honestly say "our prototype achieves X% on simulated site data", which is a different league from quoting literature.

## Phase 3: WATTWISE-2 v0 (rules, not RL)

Do NOT start with RL. Start with the rule engine, which is one afternon of work:

```python
def schedule(hour, solar_forecast, zone_temp, tank_level):
    if 5.0 <= hour < 7.5:  return "PRECOOL"   # chillers max, store cold
    if 8.5 <= hour < 10.5: return "COAST"     # chillers min, comfort floor
    if solar_forecast > 400 and 11 <= hour < 14.5: return "SOAK"  # pumps+precool on solar
    if 15 <= hour < 17:    return "RELIEF"    # spend stored cold
    return "NORMAL"
```

Then a thermal model of the building (first-order: temperature decays toward ambient with time constant ~2-4h) so the demo can show zone temperature staying inside 24-26C *while* the grid draw chart plays out. That pairing (bill falls, comfort holds) is the demo's money shot.

RL only if time remains after 23 Oct: EnergyPlus or a simple RC-network digital twin, reward = demand-charge reduction with comfort as a hard constraint. Even a tabular Q-learning on a 4-state toy model is enough to show the mechanism honestly.

## Phase 4: the wrapper

- Dashboard: one page, one site. Solar forecast vs actual, current grid draw, schedule state (PRECOOL/COAST/SOAK/RELIEF), month-to-date peak vs cap, EECA report export button (even if it only generates a CSV+PDF summary).
- Tech: Python backend (FastAPI), simple web front (the widget HTML we built is a starting point), everything local for the demo. No cloud dependency on stage wifi.

## Timeline

| When | What |
|---|---|
| Now - 16 Oct | Phase 1 simulation + figures; drop into deck |
| 16 - 22 Oct | Phase 2 model on synthetic data; slide numbers become "prototype" numbers |
| 23 Oct | **Proposal submission** |
| 24 Oct - 2 Nov | Phase 3 rule engine + thermal model; live demo flow |
| 2 - 6 Nov | Mentoring sprint: ask for real meter data, ask about CREAM settlement |
| 6 - 11 Nov | Dashboard polish, pitch rehearsal against the QA crib sheet |
| 14 Nov | **Grand finale** |

## Data questions to ask SDP mentors (do not guess these)

1. Can we get read-only 30-min interval exports for one commercial site?
2. On CREAM supply to an LGC building: does the MD register see net or gross? (Timing mismatch is the safe framing until answered.)
3. Which BMS/protocol do SDP malls actually run? (Determines the ACT layer story.)
4. Any existing tenant sub-metering, or is green billing greenfield?
