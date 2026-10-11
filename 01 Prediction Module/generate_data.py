"""
generate_data.py — build the synthetic 30-minute dataset for WATTWISE-1.

Creates one year of half-hourly data for a modelled Malaysian commercial
building (an "Elmina Innovation Park"-style site, ~1,000 kW peak class):

  - solar_pv_kw      output of a 600 kWp rooftop array
  - building_kw      gross building load (base + occupancy + cooling)
  - weather columns  irradiance, cloud, ambient temp, humidity (the
                     features the forecaster is allowed to see)

Physics anchors (see Notes/03-FACTS-AND-SOURCES.md):
  - PV yield ~1,274 kWh/kWp/yr, clear-sky bell peaking ~13:00
  - cooling follows ambient temp + occupancy; offices ramp 8:30-10:30,
    malls peak festive-afternoon style (weekend +0)
  - monsoon season = Sep-Nov: more cloud, lower yield
  - noise + occasional cloud events so forecasts have something to miss

Run:  python generate_data.py   (from 01 Prediction Module/)
Out:  data/dataset.csv  (~17,520 rows = 365 days x 48)
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)

# --- site parameters ---
KWp = 600.0          # array size
BASE_KW = 260.0      # overnight base load (servers, security, lights)
PEAK_KW = 950.0      # gross building peak (matches our worked example)
N_DAYS = 365         # one full year

# --- helpers ---------------------------------------------------------

def clear_sky_irradiance(times):
    """Simple solar geometry bell: 0 at night, peak ~13:00 local."""
    hour = times.hour + times.minute / 60.0
    # sun rises ~7:10, sets ~19:10 near the equator
    sol = np.clip(np.sin(np.pi * (hour - 7.17) / 12.0), 0, None)
    return 1000.0 * sol  # W/m2 clear-sky GHI


def cloud_factor(times):
    """Daily-varying cloud: monsoon (Sep-Nov) cloudier, plus random events."""
    month = times.month
    base = np.where((month >= 9) & (month <= 11), 0.55, 0.25)  # mean cloud
    # day-to-day persistence + intra-day noise
    day = times.date
    day_cloud = {}
    for d in sorted(set(day)):
        day_cloud[d] = np.clip(RNG.normal(base[0], 0.18), 0.05, 0.95)
        # ~8% of days get a heavy monsoon event
        if RNG.random() < 0.08:
            day_cloud[d] = np.clip(day_cloud[d] + 0.35, 0.3, 0.98)
    return np.array([day_cloud[d] for d in day])


def ambient_temp(times, cloud):
    """Tropical: 24C night, ~33C midday, cooler under cloud."""
    hour = times.hour + times.minute / 60.0
    diurnal = 4.5 * np.sin(np.pi * (hour - 6) / 12.0)
    return 27.5 + diurnal - 4.0 * cloud


def building_load(times, temp, weekday):
    """Base + occupancy ramp + cooling driven by temp, with noise."""
    hour = times.hour + times.minute / 60.0

    # occupancy: office-style ramp 8:30-10:30, plateau, decay after 18:00
    occ = np.zeros_like(hour)
    ramp = (hour >= 7.5) & (hour < 10.5)
    occ[ramp] = (hour[ramp] - 7.5) / 3.0
    occ[(hour >= 10.5) & (hour < 18.0)] = 1.0
    decay = (hour >= 18.0) & (hour < 21.0)
    occ[decay] = 1.0 - (hour[decay] - 18.0) / 3.0

    # slight weekend reduction (office component drops, mall stays)
    wk = np.where(weekday, 1.0, 0.55)

    # cooling: tracks temp above 24C plus occupancy
    cooling = 380.0 * np.clip((temp - 24.0) / 9.0, 0, 1.2) * (0.35 + 0.65 * occ)

    load = BASE_KW + 250.0 * occ * wk + cooling * wk + RNG.normal(0, 12, len(hour))
    return np.clip(load, 180, None)


# --- build the frame --------------------------------------------------

idx = pd.date_range("2026-01-01", periods=N_DAYS * 48, freq="30min")
times = idx
weekday = idx.dayofweek < 5

ghi_clear = clear_sky_irradiance(idx)
cloud = cloud_factor(idx)
ghi = ghi_clear * (1.0 - 0.75 * cloud) * RNG.normal(1.0, 0.04, len(idx))
ghi = np.clip(ghi, 0, None)

temp = ambient_temp(idx, cloud)
humidity = 68 + 18 * cloud + RNG.normal(0, 4, len(idx))

# PV: performance-ratio-style derate; temp derate above 25C cell temp
cell_temp = temp + ghi / 800.0 * 25.0
temp_derate = 1 - 0.004 * np.clip(cell_temp - 25.0, 0, None)
pv = KWp * (ghi / 1000.0) * 0.65 * temp_derate
pv = np.clip(pv + RNG.normal(0, 4, len(idx)), 0, None)

load = building_load(idx, temp, weekday)

df = pd.DataFrame({
    "timestamp": idx,
    "ghi_wm2": ghi.round(1),
    "cloud_pct": (cloud * 100).round(1),
    "ambient_c": temp.round(2),
    "humidity_pct": np.clip(humidity, 30, 100).round(1),
    "solar_pv_kw": pv.round(1),
    "building_kw": load.round(1),
    "weekday": weekday,
})
df["net_grid_kw"] = (df["building_kw"] - df["solar_pv_kw"]).round(1)

out = Path(__file__).parent / "data" / "dataset.csv"
out.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out, index=False)

# --- sanity report ----------------------------------------------------
print(f"wrote {out}  rows={len(df)}")
print(f"solar  total {df.solar_pv_kw.sum() * 0.5:,.0f} kWh  "
      f"(specific yield {df.solar_pv_kw.sum() * 0.5 / KWp:,.0f} kWh/kWp — "
      f"target ~1,274)")
print(f"load   peak {df.building_kw.max():.0f} kW  "
      f"mean {df.building_kw.mean():.0f} kW  "
      f"LF {df.building_kw.mean()/df.building_kw.max():.2f}")
print(f"net   peak {df.net_grid_kw.max():.0f} kW  "
      f"(month of max: {df.loc[df.net_grid_kw.idxmax(), 'timestamp'].strftime('%B')})")
