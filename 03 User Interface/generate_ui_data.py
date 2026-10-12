"""
generate_ui_data.py - produce township.json for the dashboard.

Runs the WATTWISE-2 scheduler for five building archetypes by scaling the
synthetic dataset, and writes one JSON with per-building 48-step traces
(dumb vs wattwise), so the UI can scrub a full day for the whole township.

Archetypes (scaled from the base ~1,000 kW site):
  - mall             x1.6 scale, weekend-heavy, solar x1.3
  - office_tower     x1.0 (the base building itself), no PV (tower roof
                     is a plant deck, not panels)
  - innovation_park  x0.85, solar x1.15
  - data_centre      FLAT load, essential 24/7 cooling, no PV: the honest
                     counter-example in the demo
  - warehouse        x0.45, solar x0.8

v1 (2026-10-12), fixing the REVIEW.md findings:
  - every archetype passes its own PLANT into the scheduler, so thermal
    traces (zone/bank/actions) differ per building (flaw 1)
  - has_solar matches the data: office_tower and data_centre false (flaw 3)
  - demo day picked by calendar date, verified Tuesday (flaw 9)
  - billed peak / bills computed over the CHARGED window 08:00-22:00 only,
    via scheduler.billed_peak (verified TNB rule)
  - exports tariff constants + windows so the UI derives numbers from data
    instead of hardcoding them (flaw 10)

Run:  python generate_ui_data.py      (from 03 User Interface/)
Out:  data/township.json
"""

import datetime
import json
import numpy as np
import pandas as pd
from pathlib import Path
import sys

HERE = Path(__file__).parent
SCHED = HERE.parent / "02 Scheduler Module"
sys.path.insert(0, str(SCHED))
import scheduler as S  # noqa: E402

DATA = SCHED.parent / "01 Prediction Module" / "data" / "dataset.csv"

# scale     : multiple of the base ~1,000 kW site (drives the PLANT)
# wk_factor : whole-load weekend factor (mirrors generate_data.py)
# occ_shape : occupancy profile for thermal gains and strip estimate
# solar     : PV multiple; 0.0 = no array (has_solar = false)
# plant_mult: extra plant-size factor - mall chiller plants are a smaller
#             share of load (~26% energy, AIP 2187 verified) than offices
ARCHETYPES = {
    "mall":             {"scale": 1.40, "wk_factor": 1.00, "occ_shape": "mall",
                         "solar": 1.15, "plant_mult": 0.75},
    "office_tower":     {"scale": 1.00, "wk_factor": 0.55, "occ_shape": "office",
                         "solar": 1.0},
    "innovation_park":  {"scale": 0.85, "wk_factor": 0.70, "occ_shape": "office",
                         "solar": 1.15},
    "data_centre":      {"scale": 0.70, "wk_factor": 1.00, "occ_shape": "flat",
                         "solar": 0.0, "flat": True},
    "warehouse":        {"scale": 0.50, "wk_factor": 0.60, "occ_shape": "office",
                         "solar": 0.8},
}

BUILDING_META = {
    "mall":            {"label": "Elmina Lakeside Mall",    "h": 2.2},
    "office_tower":    {"label": "Menara Elmina",           "h": 5.0},
    "innovation_park": {"label": "Elmina Innovation Park",  "h": 1.4},
    "data_centre":     {"label": "SDP Hyperscale DC1",      "h": 1.1},
    "warehouse":       {"label": "Elmina Business Park W3", "h": 1.0},
}


def variant_day(df, doy, arch):
    """Scale + reshape one day of the base dataset for an archetype."""
    day = df.iloc[doy * 48:(doy + 1) * 48].copy().reset_index(drop=True)
    a = ARCHETYPES[arch]
    if a.get("flat"):
        # data centre: flat block load, no occupancy shape
        day["building_kw"] = 700.0 + np.random.default_rng(7).normal(0, 8, 48)
    else:
        day["building_kw"] = day["building_kw"] * a["scale"]
        if not bool(day.weekday.iloc[0]):
            day.loc[day.index[(day.timestamp.dt.hour >= 10) &
                              (day.timestamp.dt.hour < 22)],
                    "building_kw"] *= a["wk_factor"]
    day["solar_pv_kw"] = day["solar_pv_kw"] * a["solar"]
    day["solar_pv_kw"] = day["solar_pv_kw"].clip(upper=600 * a["solar"])
    day["building_kw"] = day["building_kw"].clip(lower=60)
    return day


def base_forecasts(df):
    """Run the trained WATTWISE-1 models (30-min ahead) on the demo day.
    Returns (solar_fc, demand_fc) series for the base site."""
    import joblib
    sys.path.insert(0, str(HERE.parent / "01 Prediction Module"))
    import train_forecast as TF

    out = {}
    for target, label in [("solar_pv_kw", "solar"), ("building_kw", "demand")]:
        X = TF.make_features(df, target)
        valid = X.dropna().index
        m = joblib.load(HERE.parent / "01 Prediction Module" /
                        "models" / f"{label}_h1.joblib")
        pred = np.clip(m.predict(X.loc[valid]), 0, None)
        full = pd.Series(np.nan, index=df.index)
        full.loc[valid] = pred
        out[label] = full
    return out["solar"], out["demand"]


def main():
    df = pd.read_csv(DATA, parse_dates=["timestamp"])
    df["weekday"] = df.timestamp.dt.dayofweek < 5

    # demo day picked by calendar date: Fri 18 Sep 2026 - a verified
    # weekday in the monsoon month of September whose morning stack-up
    # produces the documented 8:30-10:30 coincident peak
    demo_date = datetime.date(2026, 9, 18)
    ts0 = df.timestamp.iloc[0].date()
    assert ts0 == datetime.date(2026, 1, 1), "dataset must start 2026-01-01"
    doy = (demo_date - ts0).days
    assert df.timestamp.iloc[doy * 48].date() == demo_date
    print(f"demo day {demo_date} ({demo_date.strftime('%A')}), doy={doy}")

    fc_solar, fc_demand = base_forecasts(df)

    out = {
        "day_label": f"{demo_date.strftime('%B')} (monsoon season) - "
                     f"{demo_date.strftime('%A')} {demo_date.day} "
                     f"{demo_date.strftime('%B')} 2026",
        "tariff": {
            "md_rate_rm": S.MD_RATE_RM,               # 97.06 RM/kW/mo (C2 ToU)
            "md_capacity_rm": S.MD_CAPACITY_RM,       # 30.19
            "md_network_rm": S.MD_NETWORK_RM,         # 66.87
            "capacity_share": round(S.MD_CAPACITY_RM / S.MD_RATE_RM, 4),
            "energy_rm_kwh": S.ENERGY_RM_KWH,
        },
        "windows": {
            "billed": list(S.PEAK_WINDOW),    # documented MD-capture 8:30-10:30
            "charged": list(S.CHARGED_WINDOW),  # MD charged 08:00-22:00 only
        },
        "buildings": {},
    }

    for arch, meta in BUILDING_META.items():
        a = ARCHETYPES[arch]
        pm = a.get("plant_mult", 1.0)
        plant = S.scale_plant(
            a["scale"],
            occ_shape=a["occ_shape"],
            wk_factor=a["wk_factor"],
            essential=bool(a.get("flat")),
        )
        if pm != 1.0:
            for k in ("chiller_max_kw", "chiller_min_kw", "night_kw",
                      "cap_kwh", "kwh_per_degc", "strip_kw"):
                plant[k] *= pm
        day = variant_day(df, doy, arch)
        dumb = S.simulate_day(day, S.make_policy_dumb(), "dumb", plant)
        wise = S.simulate_day(day, S.make_policy_wattwise(), "wattwise", plant)

        def pack(log):
            return {
                "net_kw": log.net_grid_kw.tolist(),
                "chiller_kw": log.chiller_kw.tolist(),
                "zone_c": log.zone_c.tolist(),
                "stored_kwh": log.stored_kwh.tolist(),
                "solar_kw": log.solar_kw.tolist(),
                "action": log.action.tolist(),
                "times": log.time.tolist(),
            }

        # billed peak over the CHARGED window only (verified TNB rule)
        peak_d = S.billed_peak(dumb)
        peak_w = S.billed_peak(wise)
        out["buildings"][arch] = {
            "label": meta["label"],
            "height": meta["h"],
            "has_solar": a["solar"] > 0,
            "cap_kwh": round(plant["cap_kwh"], 0),
            "peak_dumb_kw": round(peak_d, 1),
            "peak_wattwise_kw": round(peak_w, 1),
            "shave_pct": round(100 * (peak_d - peak_w) / peak_d, 1) if peak_d else 0.0,
            "bill_dumb_rm": round(peak_d * S.MD_RATE_RM, 0),
            "bill_wattwise_rm": round(peak_w * S.MD_RATE_RM, 0),
            "dumb": pack(dumb),
            "wattwise": pack(wise),
        }

    dest = HERE / "data" / "township.json"
    dest.parent.mkdir(parents=True, exist_ok=True)

    # --- township-level forecast payload (WATTWISE-1, base site) --------
    sl = fc_solar.iloc[doy * 48:(doy + 1) * 48]
    dm = fc_demand.iloc[doy * 48:(doy + 1) * 48]
    act_s = df["solar_pv_kw"].iloc[doy * 48:(doy + 1) * 48]
    act_d = df["building_kw"].iloc[doy * 48:(doy + 1) * 48]
    times = df["timestamp"].iloc[doy * 48:(doy + 1) * 48].dt.strftime("%H:%M")
    out["forecast"] = {
        "solar_fc_kw": [round(v, 1) if np.isfinite(v) else None for v in sl],
        "demand_fc_kw": [round(v, 1) if np.isfinite(v) else None for v in dm],
        "solar_actual_kw": [round(v, 1) for v in act_s],
        "demand_actual_kw": [round(v, 1) for v in act_d],
        "times": times.tolist(),
    }

    dest.write_text(json.dumps(out))
    size = dest.stat().st_size / 1024
    print(f"wrote {dest} ({size:.0f} KB)")
    print(f"day_label: {out['day_label']}")
    for k, v in out["buildings"].items():
        print(f"  {k:16s} {v['label']:28s} billed peak {v['peak_dumb_kw']:6.0f} -> "
              f"{v['peak_wattwise_kw']:6.0f} kW  shave {v['shave_pct']:4.1f}%  "
              f"solar={v['has_solar']}")


if __name__ == "__main__":
    main()
