"""
scheduler.py - WATTWISE-2 rule-based scheduler v0.

Decides, every 30 minutes, what the building's flexible chiller plant should
do, using WATTWISE-1's forecasts. This is the "defensible baseline"
scheduler: simple, explainable rules a judge can audit line by line. The
learning scheduler described in the deck must beat THIS to justify itself.

The physics it exploits (see Notes/01-HOW-IT-WORKS.md):
  - pre-cool before the 8:30-10:30am billed window; coast through it on
    banked cold (comfort band 24-26C is the HARD constraint)
  - soak midday surplus solar into chilled water / thermal mass
  - the cold bank is finite: coasting has a real budget, not magic

Calibration notes (kept honest):
  - heat gain is sized so holding the band at tropical midday needs
    roughly the full chiller plant, otherwise coasting would be free
  - building_kw from the dataset already contains a cooling component;
    we strip our estimate of it and add the scheduled chiller draw,
    so we never double-count
  - the zone MAY exceed 26C in the sim; we count it as a violation
    instead of silently clamping

Run:  python scheduler.py
Out:  results/day_*.csv  +  summary.json
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE.parent / "01 Prediction Module" / "data" / "dataset.csv"

# --- tariff + building parameters (sourced, Notes/03) ------------------
MD_RATE_RM = 97.06            # RM/kW/month, MV ToU (worst case)
ENERGY_RM_KWH = 0.454         # 45.4 sen base energy rate
CHILLER_MAX_KW = 380.0        # flexible chiller plant capacity
CHILLER_MIN_KW = 60.0         # healthy part-load floor
BAND_LO_C, BAND_HI_C = 24.0, 26.0   # comfort band, HARD constraint
PEAK_WINDOW = (8.5, 10.5)     # the billed danger window, hours
PRECOOL_START = 5.5           # start banking cold here
SOAK_START, SOAK_END = 11.0, 14.5  # solar surplus window
CAPACITY_KWH_C = 900.0        # max banked cold, kWh
KWH_PER_DEGC = 130.0          # thermal mass: kWh per degree C


def in_window(h, w):
    return w[0] <= h < w[1]


def occupancy(h, weekday):
    """Reconstruct the generator's occupancy shape (0..1)."""
    if not weekday:
        # weekends: mall-style, gentler but longer
        return 0.75 if 10 <= h < 21 else 0.25
    if 7.5 <= h < 10.5:
        return (h - 7.5) / 3.0
    if 10.5 <= h < 18.0:
        return 1.0
    if 18.0 <= h < 21.0:
        return 1.0 - (h - 18.0) / 3.0
    return 0.0


def heat_gain(r, h, weekday):
    """deg C the zone warms per 30-min step with chillers off.
    Sized so midday tropical holding needs ~full plant."""
    occ = occupancy(h, weekday)
    envelope = 0.12 * max(0.0, r.ambient_c - 24.0)   # ~1.1C at 33C
    internal = 0.55 * occ                             # people + equipment
    return envelope + internal + 0.05


def strip_cooling(r, h, weekday):
    """Estimate the cooling component embedded in building_kw (kW),
    using the same shape the data generator used."""
    occ = occupancy(h, weekday)
    shape = np.clip((r.ambient_c - 24.0) / 9.0, 0, 1.2) * (0.35 + 0.65 * occ)
    return 380.0 * shape * (1.0 if weekday else 0.9)


def simulate_day(day_df, policy, label):
    """Run one day under a scheduling policy. Returns per-step log."""
    zone = 25.2
    stored = 0.0
    rows = []
    for _, r in day_df.iterrows():
        h = r.timestamp.hour + r.timestamp.minute / 60.0
        weekday = bool(r.weekday)

        # 1. policy decides the chiller draw for this step
        chiller_kw, action = policy(h, zone, stored, r)

        # 2. thermal physics for this step
        cool_c = chiller_kw * 0.5 / KWH_PER_DEGC          # deg C cooled
        heat_c = heat_gain(r, h, weekday)                  # deg C warmed

        if cool_c >= heat_c:
            surplus = cool_c - heat_c
            zone = max(BAND_LO_C, zone - surplus)
            banked = surplus * KWH_PER_DEGC * 0.85         # 15% storage loss
            stored = min(CAPACITY_KWH_C, stored + banked)
        else:
            deficit = heat_c - cool_c
            # burn banked cold first
            burn_kwh = min(stored, deficit * KWH_PER_DEGC)
            stored -= burn_kwh
            deficit -= burn_kwh / KWH_PER_DEGC
            zone += deficit                                # honest: may pass 26

        # 3. safety net: comfort is the hard wall
        if zone > BAND_HI_C:
            chiller_kw = CHILLER_MAX_KW                    # emergency pull-down
            zone = min(zone, BAND_HI_C + 0.4)              # recovery takes time
            action = "safety"

        # 4. meter: strip the generator's cooling, add our scheduled draw
        nonflex = max(0.0, r.building_kw - strip_cooling(r, h, weekday))
        total = nonflex + chiller_kw
        net = max(total - r.solar_pv_kw, 0.0)

        rows.append({
            "time": r.timestamp.strftime("%H:%M"),
            "zone_c": round(zone, 2),
            "stored_kwh": round(stored, 1),
            "chiller_kw": round(chiller_kw, 1),
            "total_kw": round(total, 1),
            "solar_kw": round(r.solar_pv_kw, 1),
            "net_grid_kw": round(net, 1),
            "action": action,
        })
    out = pd.DataFrame(rows)
    out.attrs["label"] = label
    return out


# --- policy A: dumb baseline (how buildings run today) ------------------

def policy_dumb(h, zone, stored, r):
    """Reactive: hold 25C. Chill hard whenever warm, no planning."""
    if h < 6 or h > 21.5:
        return (20.0, "night-min")
    if zone > 25.0:
        return (CHILLER_MAX_KW, "reactive")
    return (CHILLER_MIN_KW, "hold")


# --- policy B: WattWise rules -------------------------------------------

def policy_wattwise(h, zone, stored, r):
    """Pre-cool before the peak window, coast through it, soak midday."""
    solar = r.solar_pv_kw

    if in_window(h, (PRECOOL_START, PEAK_WINDOW[0])):
        return (CHILLER_MAX_KW, "precool")

    if in_window(h, PEAK_WINDOW):
        return (CHILLER_MIN_KW, "coast")

    if in_window(h, (SOAK_START, SOAK_END)) and solar > 250.0:
        return (CHILLER_MAX_KW * 0.9, "soak")

    # comfort management outside the danger window: track the band with
    # a proportional response, so we never fall behind and rebound
    # (applies at night too: comfort never sleeps)
    if zone >= BAND_HI_C - 0.2:
        return (CHILLER_MAX_KW, "comfort-urgent")
    if 6 <= h < 22:
        if zone >= 25.4:
            return (CHILLER_MAX_KW * 0.8, "comfort-catchup")
        if zone >= 25.0:
            return (CHILLER_MAX_KW * 0.5, "comfort-hold")
        return (CHILLER_MIN_KW, "hold")

    if h < 5.5 or h > 21.5:
        return (20.0, "night-min")

    return (CHILLER_MIN_KW, "hold")


# --- scoring -------------------------------------------------------------

def score(logs):
    peaks, bills = [], []
    for log in logs:
        peak = log.net_grid_kw.max()
        md = peak * MD_RATE_RM                      # illustrative: day max
        energy = float((log.net_grid_kw * 0.5 * ENERGY_RM_KWH).sum())
        peaks.append(peak)
        bills.append(md + energy)
    return {
        "peak_kw_mean": round(float(np.mean(peaks)), 1),
        "peak_kw_max": round(float(np.max(peaks)), 1),
        "day_bill_rm_mean": round(float(np.mean(bills)), 0),
    }


def main():
    df = pd.read_csv(DATA, parse_dates=["timestamp"])
    df["weekday"] = df.timestamp.dt.dayofweek < 5

    # representative days: 2 weekdays, weekend, a clear + a monsoon day
    picks = [8, 9, 11, 12, 260]
    logs = {"dumb": [], "wattwise": []}
    for doy in picks:
        day = df.iloc[doy * 48:(doy + 1) * 48].reset_index(drop=True)
        logs["dumb"].append(simulate_day(day, policy_dumb, "dumb"))
        logs["wattwise"].append(simulate_day(day, policy_wattwise, "wattwise"))

    results = {k: score(v) for k, v in logs.items()}
    sh = results["dumb"]["peak_kw_mean"] - results["wattwise"]["peak_kw_mean"]
    results["peak_shave_pct"] = round(100 * sh / results["dumb"]["peak_kw_mean"], 1)
    results["comfort_violations_wattwise"] = int(sum(
        (l.zone_c > BAND_HI_C + 0.01).sum() for l in logs["wattwise"]))
    results["comfort_violations_dumb"] = int(sum(
        (l.zone_c > BAND_HI_C + 0.01).sum() for l in logs["dumb"]))

    outdir = HERE / "results"
    outdir.mkdir(exist_ok=True)
    (outdir / "summary.json").write_text(json.dumps(results, indent=2))
    for doy, l1, l2 in zip(picks, logs["dumb"], logs["wattwise"]):
        l1.to_csv(outdir / f"day{doy:03d}_dumb.csv", index=False)
        l2.to_csv(outdir / f"day{doy:03d}_wattwise.csv", index=False)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
