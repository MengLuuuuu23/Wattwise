"""
train_forecast.py — WATTWISE-1 forecaster.

Trains two models on the 30-minute dataset:

  1. solar  : predicts solar_pv_kw for the next 6 intervals (30 min - 3 h)
  2. demand : predicts building_kw for the next 6 intervals

Design (honest, per Notes/07-CRITIQUE.md):
  - features = weather (irradiance, cloud, temp, humidity) + calendar
    (hour, weekday) + RECENT HISTORY of the target itself
  - model = gradient boosting (sklearn HistGradientBoostingRegressor):
    solid on tabular data, fast to train, no GPU needed
  - evaluation = walk-forward on the last 60 days (no shuffling: time
    series), reporting R2 / MAE / nRMSE at 30-min and 3-h horizons

This is deliberately the "defensible baseline". An LSTM can be added
later and compared against this on identical splits.

Run:  python train_forecast.py
Out:  models/*.joblib  +  metrics.json  +  plots/
"""

import json
import importlib.util
import numpy as np
import pandas as pd
from pathlib import Path
try:
    from joblib import dump, load
except ImportError:  # forecasting can still use the explicit fallback below
    dump = load = None

HERE = Path(__file__).parent
DATA = HERE / "data" / "dataset.csv"
MODELS = HERE / "models"
PLOTS = HERE / "plots"
HORIZONS = [1, 2, 3, 4, 5, 6]  # intervals ahead: 30 min ... 3 h
TEST_DAYS = 60
MODEL_SOURCE = "WATTWISE-1 HistGradientBoosting"
FALLBACK_SOURCE = "one-step persistence fallback"


# --- load + feature engineering ---------------------------------------

def load_frame():
    df = pd.read_csv(DATA, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def make_features(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """Everything the forecaster may know at time t (no future leakage)."""
    t = df["timestamp"]
    f = pd.DataFrame(index=df.index)

    # calendar
    f["hour"] = t.dt.hour + t.dt.minute / 60.0
    f["dow"] = t.dt.dayofweek
    f["month"] = t.dt.month

    # weather now
    for c in ["ghi_wm2", "cloud_pct", "ambient_c", "humidity_pct"]:
        f[c] = df[c]

    # recent history of the target (t, t-1, t-2, t-3, daily lag)
    for lag in [0, 1, 2, 3, 48]:
        col = df[target].shift(lag)
        f[f"{target}_lag{lag}"] = col
    # recent trend
    f[f"{target}_delta"] = df[target].diff()

    return f


def make_targets(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """Target value at t + h, for each horizon h."""
    out = pd.DataFrame(index=df.index)
    for h in HORIZONS:
        out[f"h{h}"] = df[target].shift(-h)
    return out


def forecast_h1(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Load the +30-min WATTWISE-1 models and align predictions to target rows.

    A forecast stored at row t is issued from features at t-30 minutes,
    so dispatch can use it without reading future weather or meter values.
    The first interval has no forecast until a preceding observation exists.
    """
    forecasts = {}
    use_models = (load is not None and importlib.util.find_spec("sklearn")
                  is not None and all(
        (MODELS / f"{label}_h1.joblib").is_file()
        for label in ("solar", "demand")
    ))
    for target, label in [("solar_pv_kw", "solar"),
                          ("building_kw", "demand")]:
        aligned = pd.Series(np.nan, index=df.index, dtype=float)
        if use_models:
            X = make_features(df, target)
            valid = X.dropna().index.to_numpy(dtype=int)
            model = load(MODELS / f"{label}_h1.joblib")
            prediction = np.clip(model.predict(X.loc[valid]), 0, None)
            target_idx = valid + 1
            keep = target_idx < len(df)
            aligned.loc[target_idx[keep]] = prediction[keep]
        elif len(df) > 1:
            # Transparent last-value baseline: the forecast for row t uses
            # only the observed value at t-1. Never substitute future actuals.
            aligned.iloc[1:] = np.clip(
                df[target].iloc[:-1].to_numpy(dtype=float), 0, None)
        forecasts[label] = aligned
    return forecasts


def forecast_source() -> str:
    """Identify which forecast path is available for this run."""
    if (load is not None and importlib.util.find_spec("sklearn") is not None
            and all(
        (MODELS / f"{label}_h1.joblib").is_file()
        for label in ("solar", "demand")
    )):
        return MODEL_SOURCE
    return FALLBACK_SOURCE


# --- training ----------------------------------------------------------

def train_target(df, target, label):
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor
    except ImportError as exc:
        raise RuntimeError(
            "Training needs scikit-learn. Install the repository dependencies "
            "with `python -m pip install -r requirements.txt`."
        ) from exc
    X = make_features(df, target)
    Y = make_targets(df, target)

    n_test = TEST_DAYS * 48
    split = len(df) - n_test
    # drop rows with any NaN (warmup lags / final horizons)
    valid = X.dropna().index.intersection(Y.dropna().index)
    train_idx = [i for i in valid if i < split]
    test_idx = [i for i in valid if i >= split]

    Xtr, Xte = X.loc[train_idx], X.loc[test_idx]
    results, models = {}, {}

    for h in HORIZONS:
        ytr = Y.loc[train_idx, f"h{h}"]
        m = HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.08, max_depth=None,
            l2_regularization=1.0, random_state=0,
        )
        m.fit(Xtr, ytr)
        yte = Y.loc[test_idx, f"h{h}"]
        pred = m.clip(0, None) if hasattr(m, "clip") else m
        yhat = np.clip(m.predict(Xte), 0, None)

        r2 = 1 - np.sum((yte - yhat) ** 2) / np.sum((yte - yte.mean()) ** 2)
        mae = np.mean(np.abs(yte - yhat))
        nrmse = np.sqrt(np.mean((yte - yhat) ** 2)) / yte.mean()

        results[h] = {
            "r2": round(float(r2), 4),
            "mae_kw": round(float(mae), 2),
            "nrmse_pct": round(float(nrmse) * 100, 2),
        }
        models[h] = m
        print(f"  [{label}] +{h*30:>3}min  R2={r2:.3f}  MAE={mae:6.1f} kW  "
              f"nRMSE={nrmse*100:5.2f}%")

    return results, models, test_idx, Y


def main():
    if dump is None:
        raise RuntimeError(
            "Saving trained models needs joblib. Install the repository "
            "dependencies with `python -m pip install -r requirements.txt`."
        )
    df = load_frame()
    MODELS.mkdir(exist_ok=True)
    PLOTS.mkdir(exist_ok=True)

    all_metrics = {}
    for target, label in [("solar_pv_kw", "solar"), ("building_kw", "demand")]:
        print(f"\n=== {label} ===")
        results, models, test_idx, Y = train_target(df, target, label)
        all_metrics[label] = results
        for h, m in models.items():
            dump(m, MODELS / f"{label}_h{h}.joblib")

    (HERE / "metrics.json").write_text(json.dumps(all_metrics, indent=2))
    print(f"\nwrote metrics.json + {len(all_metrics)*len(HORIZONS)} models")
    print("benchmarks (published, Malaysian rooftop LSTM): "
          "nRMSE 6.75% / R2 0.957 at 30-min")


if __name__ == "__main__":
    main()
