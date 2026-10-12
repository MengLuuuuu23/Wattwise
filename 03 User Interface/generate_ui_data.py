"""
generate_ui_data.py - produce township.json for the dashboard + CLI.

v2 (2026-10-13): multi-town portfolio. Three SDP-style townships, each
with several commercial buildings (mall, offices, cafes, retail,
warehouse, data centre). The JSON keeps a flat "buildings" dict (dashboard
compatibility) plus a "towns" index with per-town aggregates. Every
building carries its own scaled WATTWISE-1 solar forecast and its
total_kw, so "solar actually used on-site" is exact:
net = max(total - solar, 0) - no export under SELCO, surplus is clipped.

Townships are synthetic archetypes on the same calibrated base site;
labels reuse real SDP township names for the rollout story (numbers stay
illustrative, per 03-FACTS-AND-SOURCES discipline).

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

# --- reusable building archetypes ---------------------------------------
# scale     : multiple of the base ~1,000 kW site (drives the PLANT)
# wk_factor : whole-load weekend factor (mirrors generate_data.py)
# occ_shape : occupancy profile for thermal gains and strip estimate
# solar     : PV multiple; 0.0 = no array (has_solar = false)
# plant_mult: plant-size factor (mall-type plants are a smaller share of
#             load, ~26% energy, AIP 2187 verified)
ARCHETYPES = {
    "mall":      {"scale": 1.40, "wk_factor": 1.00, "occ_shape": "mall",
                  "solar": 1.15, "plant_mult": 0.75},
    "office":    {"scale": 1.00, "wk_factor": 0.55, "occ_shape": "office",
                  "solar": 1.0},
    "office_md": {"scale": 0.65, "wk_factor": 0.55, "occ_shape": "office",
                  "solar": 0.7},
    "office_sm": {"scale": 0.22, "wk_factor": 0.55, "occ_shape": "office",
                  "solar": 0.15, "plant_mult": 1.2},
    "retail":    {"scale": 0.55, "wk_factor": 1.00, "occ_shape": "mall",
                  "solar": 0.50, "plant_mult": 0.75},
    "retail_sm": {"scale": 0.35, "wk_factor": 1.00, "occ_shape": "mall",
                  "solar": 0.30, "plant_mult": 0.75},
    "cafe":      {"scale": 0.10, "wk_factor": 1.00, "occ_shape": "mall",
                  "solar": 0.06, "plant_mult": 0.80},
    "cafe_sm":   {"scale": 0.12, "wk_factor": 1.00, "occ_shape": "mall",
                  "solar": 0.08, "plant_mult": 0.80},
    "park":      {"scale": 0.85, "wk_factor": 0.70, "occ_shape": "office",
                  "solar": 1.15},
    "dc":        {"scale": 0.70, "wk_factor": 1.00, "occ_shape": "flat",
                  "solar": 0.0, "flat": True},
    "warehouse": {"scale": 0.50, "wk_factor": 0.60, "occ_shape": "office",
                  "solar": 0.8},
    "warehouse_sm": {"scale": 0.40, "wk_factor": 0.60, "occ_shape": "office",
                     "solar": 0.5, "plant_mult": 1.25},
}

# --- the portfolio: three townships --------------------------------------
TOWNS = {
    "elmina": {
        "label": "City of Elmina",
        "buildings": {
            "elmina_mall":   ("Elmina Lakeside Mall",    "mall"),
            "elmina_tower":  ("Menara Elmina",           "office"),
            "elmina_park":   ("Elmina Innovation Park",  "park"),
            "elmina_dc":     ("SDP Hyperscale DC1",      "dc"),
            "elmina_wh":     ("Elmina Business Park W3", "warehouse"),
        },
    },
    "bbr": {
        "label": "Bandar Bukit Raja",
        "buildings": {
            "bbr_plaza":  ("BBR Community Plaza", "retail"),
            "bbr_office": ("BBR Corporate Office", "office_md"),
            "bbr_cafe":   ("Kafe Nusantara BBR",  "cafe"),
            "bbr_wh":     ("BBR Logistics Hub",   "warehouse_sm"),
        },
    },
    "ara": {
        "label": "Ara Damansara",
        "buildings": {
            "ara_tower":  ("Ara Damansara Tower",  "office"),
            "ara_retail": ("Ara Retail Row",       "retail_sm"),
            "ara_cafe":   ("Ara Corner Cafe",      "cafe_sm"),
            "ara_clinic": ("Ara Medical Centre",   "office_sm"),
        },
    },
}

FLOORS = {"elmina_mall": "2F", "elmina_tower": "17F", "elmina_park": "3F",
          "elmina_dc": "1F", "elmina_wh": "1F"}


def build_plant(arch):
    """Derive the PLANT dict for an archetype key (shared by all loops)."""
    a = ARCHETYPES[arch]
    pm = a.get("plant_mult", 1.0)
    plant = S.scale_plant(
        a["scale"],
        occ_shape=a["occ_shape"],
        wk_factor=a["wk_factor"],
        essential=bool(a.get("flat")),
    )
    if pm != 1.0:
        for kk in ("chiller_max_kw", "chiller_min_kw", "night_kw",
                   "cap_kwh", "kwh_per_degc", "strip_kw"):
            plant[kk] *= pm
    return plant


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
    base_fc_day = fc_solar.iloc[doy * 48:(doy + 1) * 48].tolist()
    base_dm_day = fc_demand.iloc[doy * 48:(doy + 1) * 48].tolist()

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
        "towns": {},       # town index + aggregates (filled below)
        "buildings": {},   # flat, all buildings, dashboard-compatible
    }

    for tkey, town in TOWNS.items():
        for bkey, (label, arch) in town["buildings"].items():
            a = ARCHETYPES[arch]
            plant = build_plant(arch)
            day = variant_day(df, doy, arch)
            dumb = S.simulate_day(day, S.make_policy_dumb(), "dumb", plant)
            wise = S.simulate_day(day, S.make_policy_wattwise(), "wattwise", plant)

            def pack(log):
                # per-building demand forecast: the base-site WATTWISE-1
                # demand forecast scaled to this building (weekday demo
                # day, so the plain scale applies). Flat sites (DC) know
                # their own block load: forecast = the flat line.
                if a.get("flat"):
                    dm_fc = [700.0] * 48
                else:
                    dm_fc = [round(v * a["scale"], 1)
                             if v is not None and np.isfinite(v) else None
                             for v in base_dm_day]
                return {
                    "net_kw": log.net_grid_kw.tolist(),
                    "total_kw": log.total_kw.tolist(),
                    "chiller_kw": log.chiller_kw.tolist(),
                    "zone_c": log.zone_c.tolist(),
                    "stored_kwh": log.stored_kwh.tolist(),
                    "solar_kw": log.solar_kw.tolist(),
                    "solar_fc_kw": [round(v * a["solar"], 1)
                                    if v is not None and np.isfinite(v)
                                    else None for v in base_fc_day],
                    "demand_fc_kw": dm_fc,
                    "action": log.action.tolist(),
                    "times": log.time.tolist(),
                }

            # billed peak over the CHARGED window only (verified TNB rule)
            peak_d = S.billed_peak(dumb)
            peak_w = S.billed_peak(wise)
            out["buildings"][bkey] = {
                "label": label,
                "town": tkey,
                "town_label": town["label"],
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

    # --- town aggregates -------------------------------------------------
    for tkey, town in TOWNS.items():
        keys = list(town["buildings"].keys())
        agg_fc, agg_act = [], []
        for i in range(48):
            agg_fc.append(round(sum(out["buildings"][k]["wattwise"]["solar_fc_kw"][i] or 0
                                    for k in keys), 1))
            agg_act.append(round(sum(out["buildings"][k]["wattwise"]["solar_kw"][i]
                                    for k in keys), 1))
        out["towns"][tkey] = {
            "label": town["label"],
            "buildings": keys,
            "solar_fc_kw": agg_fc,
            "solar_actual_kw": agg_act,
            "peak_dumb_kw": round(sum(out["buildings"][k]["peak_dumb_kw"] for k in keys), 1),
            "peak_wattwise_kw": round(sum(out["buildings"][k]["peak_wattwise_kw"] for k in keys), 1),
            "bill_dumb_rm": round(sum(out["buildings"][k]["bill_dumb_rm"] for k in keys), 0),
            "bill_wattwise_rm": round(sum(out["buildings"][k]["bill_wattwise_rm"] for k in keys), 0),
        }

    # --- weekly dispatch schedules (3 weeks around the demo week) -------
    # the scheduler tab is a planner: per day, per building, what the
    # rules dispatch (chiller kW) at each half-hour. Weekends differ from
    # weekdays because the underlying dataset days differ.
    demo_monday = demo_date - datetime.timedelta(days=demo_date.weekday())
    week_mondays = [demo_monday - datetime.timedelta(days=7),
                    demo_monday,
                    demo_monday + datetime.timedelta(days=7)]
    out["demo_date"] = demo_date.isoformat()
    out["weeks"] = [{"monday": m.isoformat(),
                     "label": "week of %s" % m.strftime("%d %b %Y")}
                    for m in week_mondays]

    out["week_schedule"] = {}
    for tkey, town in TOWNS.items():
        for bkey, (label, arch) in town["buildings"].items():
            plant = build_plant(arch)
            days = []
            for wi, wmon in enumerate(week_mondays):
                for d in range(7):
                    ddate = wmon + datetime.timedelta(days=d)
                    doy_d = (ddate - ts0).days
                    day = variant_day(df, doy_d, arch)
                    dl = S.simulate_day(day, S.make_policy_dumb(), "dumb", plant)
                    wl = S.simulate_day(day, S.make_policy_wattwise(),
                                        "wattwise", plant)
                    days.append({
                        "date": ddate.isoformat(),
                        "week": wi, "dow": d,
                        "chiller_kw": wl.chiller_kw.tolist(),
                        "action": wl.action.tolist(),
                        "net_kw": wl.net_grid_kw.tolist(),
                        "solar_kw": wl.solar_kw.tolist(),
                        "zone_c": wl.zone_c.tolist(),
                        "peak_dumb_kw": round(S.billed_peak(dl), 1),
                        "peak_wattwise_kw": round(S.billed_peak(wl), 1),
                        "bill_dumb_rm": round(S.billed_peak(dl) * S.MD_RATE_RM, 0),
                        "bill_wattwise_rm": round(S.billed_peak(wl) * S.MD_RATE_RM, 0),
                    })
            out["week_schedule"][bkey] = {"days": days}

    dest = HERE / "data" / "township.json"
    dest.parent.mkdir(parents=True, exist_ok=True)

    # --- portfolio-level forecast payload (WATTWISE-1, base site) --------
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

    warn = []
    for tkey, town in TOWNS.items():
        print(f"  {town['label']}")
        for k in town["buildings"]:
            v = out["buildings"][k]
            shave = v["shave_pct"]
            if not (0 <= shave <= 15.05):
                warn.append((k, shave))
            print(f"    {k:14s} {v['label']:26s} peak {v['peak_dumb_kw']:6.0f} -> "
                  f"{v['peak_wattwise_kw']:6.0f} kW  shave {shave:4.1f}%  "
                  f"solar={v['has_solar']}")
        t = out["towns"][tkey]
        print(f"    {'':14s} {'TOWN TOTAL':26s} peak {t['peak_dumb_kw']:6.0f} -> "
              f"{t['peak_wattwise_kw']:6.0f} kW  bill RM {t['bill_dumb_rm']:,.0f} -> "
              f"RM {t['bill_wattwise_rm']:,.0f}")
    if warn:
        print("SHAVE DISCIPLINE WARNING:", warn)


if __name__ == "__main__":
    main()
