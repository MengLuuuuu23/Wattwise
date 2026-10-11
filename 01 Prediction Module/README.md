# WATTWISE-1 — Prediction Module

Forecasts solar output and building demand 30 minutes to 3 hours ahead,
on the 30-minute grid the TNB demand charge is billed on.

## Files

| File | Job |
|---|---|
| `generate_data.py` | builds `data/dataset.csv`: one year of synthetic 30-min data for a modelled ~1,000 kW commercial site (600 kWp PV). Calibrated: specific yield 1,285 kWh/kWp/yr vs the 1,274 Malaysian average; load factor 0.51 (peaky, our target profile); net peak lands in a September monsoon month |
| `train_forecast.py` | trains + evaluates the forecasters, writes `models/*.joblib` and `metrics.json` |
| `data/dataset.csv` | 17,520 rows = 365 days x 48 intervals |
| `models/` | 12 trained models (2 targets x 6 horizons) |
| `metrics.json` | walk-forward test metrics (last 60 days, no shuffling) |

## How to run

```bash
# from 99 Wattwise/
.venv/Scripts/python.exe "01 Prediction Module/generate_data.py"
.venv/Scripts/python.exe "01 Prediction Module/train_forecast.py"
```

## Model design

- **Features**: weather (GHI, cloud %, ambient temp, humidity), calendar
  (hour-of-day, day-of-week, month), and recent history of the target
  (t, t-1, t-2, t-3, same-time-yesterday, plus first difference).
  No future leakage: everything is known at forecast time.
- **Model**: `HistGradientBoostingRegressor` (sklearn). Chosen as the
  defensible baseline: fast, strong on tabular data, no GPU. The LSTM
  described in the deck can be added later and must beat THIS on the
  identical walk-forward split to justify itself.
- **Evaluation**: walk-forward on the final 60 days (time order kept,
  never shuffled). Metrics: R2, MAE (kW), nRMSE.

## Results (walk-forward, last 60 days)

| Target | Horizon | R2 | MAE | nRMSE |
|---|---|---|---|---|
| solar | +30 min | 0.996 | 4.3 kW | 7.35% |
| solar | +3 h | 0.997 | 4.2 kW | 7.08% |
| demand | +30 min | 0.996 | 10.2 kW | 2.89% |
| demand | +3 h | 0.996 | 10.3 kW | 2.93% |

Solar nRMSE ~7.3% sits right beside the published Malaysian rooftop LSTM
benchmark (nRMSE 6.75%, R2 0.957) — on synthetic data, which is easier
than reality. MAE of 4.3 kW on a 600 kWp array and ~10 kW on a ~870 kW
peak building are both far inside the margin a 100 kW shave target needs.

## Honest caveats (read before quoting numbers)

1. **Synthetic data.** These numbers prove the pipeline works and the
   feature set is informative, NOT real-world accuracy. The deck must say
   "pipeline validated on calibrated synthetic data; published Malaysian
   benchmarks of this class: nRMSE 6.75%". Never present these R2s as
   measured field performance.
2. **The demand forecaster sees the weather the simulator used to build
   the load**, so it is flattered by construction. When real interval
   data arrives, demand nRMSE will be worse than 2.9% — expect it closer
   to the solar figure. This is exactly the red team's F2 point: no
   published benchmark exists for building demand under active control.
3. **Walk-forward, not true online**: the test window is held out in
   time, which is honest, but the model is trained once rather than
   re-fit daily as the production loop would.

## Next steps

- [ ] LSTM variant (Keras/PyTorch) compared on the identical split
- [ ] Plot: 3 sample days, actual vs forecast (both targets) for the deck
- [ ] Peak-hour skill metric: specifically how well the 8:30-10:30am
      morning window is predicted (that is what the scheduler pays for)
- [ ] Swap in real interval data the moment SDP/the pilot provides it
