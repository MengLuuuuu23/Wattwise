"""
generate_ui_data.py — produce township.json for the 3D dashboard.

Runs the WATTWISE-2 scheduler for five building archetypes by scaling the
synthetic dataset, and writes one JSON with per-building 48-step traces
(dumb vs wattwise), so the UI can scrub a full day for the whole township.

Archetypes (scaled from the base ~1,000 kW site):
  - mall            x1.6, weekend-heavy (mall-style occupancy)
  - office_tower    x1.0, the base building itself
  - innovation_park x0.85
  - data_centre     FLAT load ~700 kW (no occupancy shape, no precool win:
                     the honest counter-example in the demo)
  - warehouse       x0.45

Run:  python generate_ui_data.py
Out:  data/township.json
"""

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

ARCHETYPES = {
    "mall":             {"scale": 1.60, "weekend_boost": 1.15, "solar": 1.3},
    "office_tower":     {"scale": 1.00, "weekend_boost": 0.55, "solar": 1.0},
    "innovation_park":  {"scale": 0.85, "weekend_boost": 0.70, "solar": 1.15},
    "data_centre":      {"scale": 0.70, "weekend_boost": 1.00, "solar": 0.0,
                         "flat": True},
    "warehouse":        {"scale": 0.45, "weekend_boost": 0.60, "solar": 0.8},
}

BUILDING_META = {
    "mall":             {"label": "Elmina Lakeside Mall",   "h": 2.2, "solar": True},
    "office_tower":     {"label": "Menara Elmina",          "h": 5.0, "solar": False},
    "innovation_park":  {"label": "Elmina Innovation Park", "h": 1.4, "solar": True},
    "data_centre":      {"label": "SDP Hyperscale DC1",     "h": 1.1, "solar": True},
    "warehouse":        {"label": "Elmina Business Park W3","h": 1.0, "solar": True},
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
                    "building_kw"] *= a["weekend_boost"]
    day["solar_pv_kw"] = day["solar_pv_kw"] * a["solar"]
    day["solar_pv_kw"] = day["solar_pv_kw"].clip(upper=600 * a["solar"])
    day["building_kw"] = day["building_kw"].clip(lower=60)
    return day


def main():
    df = pd.read_csv(DATA, parse_dates=["timestamp"])
    df["weekday"] = df.timestamp.dt.dayofweek < 5

    # demo day: a clear September Tuesday (doy 259 = Mon; use 260 Tue)
    doy = 260
    out = {"day_label": "September (monsoon season) — Tuesday", "buildings": {}}

    for arch, meta in BUILDING_META.items():
        day = variant_day(df, doy, arch)
        dumb = S.simulate_day(day, S.policy_dumb, "dumb")
        wise = S.simulate_day(day, S.policy_wattwise, "wattwise")

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

        peak_d = float(dumb.net_grid_kw.max())
        peak_w = float(wise.net_grid_kw.max())
        out["buildings"][arch] = {
            "label": meta["label"],
            "height": meta["h"],
            "has_solar": meta["solar"],
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
    dest.write_text(json.dumps(out))
    size = dest.stat().st_size / 1024
    print(f"wrote {dest} ({size:.0f} KB)")
    for k, v in out["buildings"].items():
        print(f"  {k:16s} {v['label']:28s} peak {v['peak_dumb_kw']:6.0f} -> "
              f"{v['peak_wattwise_kw']:6.0f} kW  shave {v['shave_pct']:4.1f}%")


if __name__ == "__main__":
    main()
