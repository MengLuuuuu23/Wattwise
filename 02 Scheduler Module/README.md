# WATTWISE-2 — Scheduler Module

Decides, every 30 minutes, what the building's flexible chiller plant does.
This is the **rule-based v0**: explainable, auditable rules a judge can read
line by line. The learning scheduler (deep RL, per the deck) must beat THIS
baseline on the same simulator to justify its complexity.

## Files

| File | Job |
|---|---|
| `scheduler.py` | the simulator + both policies + scoring |
| `results/summary.json` | headline numbers |
| `results/dayXXX_{dumb,wattwise}.csv` | full 48-step traces for 5 representative days (weekdays, weekend, monsoon) |

## How it works

Two policies run on the same synthetic building + weather from
`01 Prediction Module/data/dataset.csv`:

- **policy_dumb** — how buildings run today: reactively hold 25°C, chill
  hard when warm. No planning, no lookahead.
- **policy_wattwise** — four rules, in priority order:
  1. **precool** (05:30-08:30): bank cold into thermal mass before the
     billed window, while grid draw is cheap
  2. **coast** (08:30-10:30): minimum chilling through the danger window,
     burning banked cold
  3. **soak** (11:00-14:30, solar > 250 kW): run chillers on surplus
     solar so midday generation displaces grid kWh
  4. **comfort tracking** (always): proportional response keeps the zone
     inside 24-26°C, day and night — comfort is the hard wall

## Forecast-informed dispatch

`scheduler.py` loads the saved WATTWISE-1 +30-minute solar and demand
models. Predictions are aligned to the interval they describe, so the
decision for an interval uses inputs from the previous interval. Ambient
temperature uses a one-step persistence forecast because WATTWISE-1 does
not currently forecast weather.

The WattWise policy estimates non-flexible load from the demand forecast,
then compares it with forecast on-site solar. It enters **soak** only when
the predicted local surplus can support the minimum chiller load, and caps
that load below full plant. The baseline and WattWise policy receive the
same forecast inputs. The simulated thermal state and retrospective meter
scoring still use actual synthetic rows; this is an evaluation, not a live
deployment result. Wheeled CREAM energy is not counted as a site credit.

Run `train_forecast.py` first if the model files are missing, then run
`scheduler.py` or `generate_ui_data.py` to refresh the results and dashboard
payload. If the optional trained model artifacts or dependencies are absent,
the pipeline uses a one-step persistence forecast (the previous interval's
value). Output records and the dashboard label this fallback; its same-day
diagnostic errors are not walk-forward accuracy metrics.

## Thermal model (deliberately simple + conservative)

- Zone warms per step: envelope (ambient) + internal (occupancy) gains,
  sized so a tropical midday needs ~full plant to hold the band
- Chilling cools the zone; surplus cold banks at 85% efficiency
- Banked cold is a **finite budget** (900 kWh): coasting drains it,
  and an empty bank forces honest recovery
- The zone MAY exceed 26°C in the sim — violations are counted, never
  silently clamped
- Meter arithmetic strips the dataset's embedded cooling load and adds
  the scheduled chiller draw, so nothing is double-counted

## Previous results (5 representative synthetic days; pre-forecast dispatch)

| Metric | Dumb baseline | WattWise |
|---|---|---|
| Mean daily peak (net grid) | 794.6 kW | **679.6 kW** |
| Peak shave | — | **14.5%** |
| Mean day bill (MD + energy, illustrative) | RM81,728 | **RM70,659** |
| Comfort violations (>26°C) | 5 | **0** |

These figures predate forecast-informed dispatch. The repository tracks all
12 trained models, but the forecast-informed scheduler has not yet been
re-scored in this update. Do not treat the fallback diagnostic run as a
replacement for trained-model results.

Regenerate `results/` and `03 User Interface/data/township.json` using the
tracked models and installed requirements before quoting updated performance.

Note the mechanism in the traces: WattWise's peak moves to late afternoon
(16:00-17:00) at a lower level, instead of the dumb baseline stacking its
chiller + morning load inside the 8:30-10:30 billed window.

## Honest caveats

1. **Synthetic building.** The absolute kW values inherit every assumption
   of the data generator. The 14.5% is evidence the *mechanism* works, not
   a field-measured saving.
2. **The peak relocation is tariff-aware in spirit only.** Under C1 the MD
   is set by any interval 08:00-22:00, so an afternoon peak still bills;
   the win comes from the *level* (679 vs 794), not the timing alone.
   Under C2 ToU (peak 14:00-22:00), the afternoon rebound would bill at
   peak rates — the rule set should be re-tuned per tariff class before
   any real deployment (red team S2).
3. **Forecast robustness.** Dispatch now receives forecasts aligned to their
   target interval. The persisted baseline forecast is only a continuity
   fallback; report forecast-driven savings only after retraining the models
   and scoring across representative forecast-error conditions.

## Next steps

- [x] Drive the scheduler with aligned WATTWISE-1 forecasts (persistence
      fallback is explicitly identified when trained artifacts are absent)
- [ ] Tariff switch: C1 vs C2 mode with different rule tuning
- [ ] Plots for the deck: overlay day traces (zone temp, chiller kW,
      net grid kW, dumb vs WattWise)
- [ ] The RL scheduler: same simulator, same scoring, must beat 14.5%
