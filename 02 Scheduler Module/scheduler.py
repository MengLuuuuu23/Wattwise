"""
scheduler.py - WATTWISE-2 rule-based scheduler v1.

Decides, every 30 minutes, what the building's flexible chiller plant should
do, using WATTWISE-1's forecasts. This is the "defensible baseline"
scheduler: simple, explainable rules a judge can audit line by line. The
learning scheduler described in the deck must beat THIS to justify itself.

The physics it exploits (see Notes/01-HOW-IT-WORKS.md):
  - pre-cool before the 8:30-10:30am billed window; coast through it on
    banked cold (comfort band 24-26C is the HARD constraint)
  - soak midday surplus solar into chilled water / thermal mass
  - the cold bank is finite: coasting has a real budget, not magic

v1 changes (2026-10-12), each tied to a verified source or a review finding:
  - per-building PLANT parameters: chiller capacity, thermal mass, bank
    size, envelope/internal gains all scale with the building, so two
    archetypes no longer produce identical zone/bank/action traces
  - baseline policy recalibrated to how dumb BMS controls actually run:
    chillers OFF overnight (night setback), timer morning-startup pull-down
    stacked onto the occupancy ramp. This reproduces the documented
    coincident MD peak at 8:30-10:30 (Energies 2019 MDRed paper, verified
    in Notes/03-FACTS-AND-SOURCES.md) which v0 failed to show.
  - billed peak measured over the CHARGED window 08:00-22:00 only:
    TNB does not charge MD during off-peak 22:00-08:00 (Tariff Booklet,
    verified). v0 maxed over the whole day, mis-billing precool done
    before 08:00.
  - "essential" plants (data centre): fixed 24/7 cooling, zero flexible
    capacity, no banking - the honest counter-example.

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

# --- tariff + band parameters (sourced, Notes/03-FACTS-AND-SOURCES.md) ---
MD_CAPACITY_RM = 30.19       # RM/kW/month capacity component (C2 ToU)
MD_NETWORK_RM = 66.87         # RM/kW/month network component (C2 ToU)
MD_RATE_RM = MD_CAPACITY_RM + MD_NETWORK_RM   # = 97.06
ENERGY_RM_KWH = 0.454         # 45.4 sen base energy rate
BAND_LO_C, BAND_HI_C = 24.0, 26.0   # comfort band, HARD constraint
PEAK_WINDOW = (8.5, 10.5)     # the billed danger window, hours
PRECOOL_START = 5.5           # start banking cold here (off-peak: uncharged)
SOAK_START, SOAK_END = 11.0, 14.5  # solar surplus window
# MD is not charged 22:00-08:00 (TNB Tariff Booklet, verified) - the
# billed peak is the max draw INSIDE this window only
CHARGED_WINDOW = (8.0, 22.0)
# the documented MD-capture window (8:30-10:30) and the policy windows:
# WattWise stops precooling and starts coasting at the CHARGED-window edge
# so no full-power step ever lands inside a billed interval
COAST_WINDOW = (8.0, 10.5)

# --- the base-site plant (~1,000 kW class office) ------------------------
# Every archetype derives its own plant by scaling these (see
# generate_ui_data.py). Absolute numbers describe the base site only.
BASE_PLANT = {
    "chiller_max_kw": 380.0,   # flexible chiller plant capacity
    "chiller_min_kw": 60.0,    # healthy part-load floor
    "night_kw": 20.0,          # WattWise night hold (comfort never sleeps)
    "cap_kwh": 900.0,          # max banked cold, kWh
    "kwh_per_degc": 130.0,     # thermal mass: kWh per degree C
    "envelope_k": 0.12,        # degC gain per (ambient-24) per 30-min step
    "internal_k": 0.55,        # degC gain per step at full occupancy
    "strip_kw": 380.0,         # cooling estimate embedded in building_kw
    "essential": False,        # True = fixed 24/7 cooling, no flexibility
    "occ_shape": "office",     # occupancy profile: office | mall | flat
}


def scale_plant(scale, **overrides):
    """Derive an archetype plant from the base site.

    kW / kWh quantities scale linearly with the building. The envelope
    coefficient scales as scale**(-1/3): bigger buildings have
    proportionally less exterior skin per unit of thermal mass, so they
    warm more slowly per degree of ambient.
    """
    p = dict(BASE_PLANT)
    for k in ("chiller_max_kw", "chiller_min_kw", "night_kw",
              "cap_kwh", "kwh_per_degc", "strip_kw"):
        p[k] = BASE_PLANT[k] * scale
    p["envelope_k"] = BASE_PLANT["envelope_k"] * scale ** (-1.0 / 3.0)
    p.update(overrides)
    return p


def in_window(h, w):
    return w[0] <= h < w[1]


def occupancy(h, weekday, shape="office"):
    """Time-of-day occupancy shape (0..1) the DATA GENERATOR embedded in
    building_kw. Weekday-independent: the generator scales the whole load
    by a weekend factor instead (see strip_cooling)."""
    if shape == "flat":
        # data centre: small steady staff load around the clock
        return 0.25
    if shape == "mall":
        # malls: doors 10:00-21:00, gentle afternoon hump, every day
        if 10 <= h < 11:
            return 0.3 + 0.5 * (h - 10)
        if 11 <= h < 21:
            return 0.8 + 0.2 * (1.0 - abs(h - 15.0) / 6.0)
        return 0.1
    # office time-of-day ramp (the generator's shape)
    if 7.5 <= h < 10.5:
        return (h - 7.5) / 3.0
    if 10.5 <= h < 18.0:
        return 1.0
    if 18.0 <= h < 21.0:
        return 1.0 - (h - 18.0) / 3.0
    return 0.0


def realistic_occ(h, weekday, shape="office"):
    """Actual people in the building - drives OUR thermal model's internal
    gains. Unlike the generator's shape, this drops on office weekends."""
    if shape == "flat":
        return 0.25
    if shape == "mall":
        return occupancy(h, weekday, "mall")
    if not weekday:
        return 0.15 if 9 <= h < 18 else 0.05
    return occupancy(h, weekday, "office")


def heat_gain(r, h, weekday, plant):
    """deg C the zone warms per 30-min step with chillers off.
    Sized so midday tropical holding needs ~full plant."""
    occ = realistic_occ(h, weekday, plant["occ_shape"])
    envelope = plant["envelope_k"] * max(0.0, r.ambient_c - 24.0)
    internal = plant["internal_k"] * occ
    return envelope + internal + 0.05


def strip_cooling(r, h, weekday, plant):
    """Estimate of the cooling component embedded in building_kw (kW).
    Mirrors the generator: same time-of-day shape, whole-load weekend
    factor 0.55 (see generate_data.py building_load)."""
    if plant.get("essential"):
        # essential plants cool at a constant rate around the clock
        return plant["strip_kw"]
    occ = occupancy(h, weekday, plant["occ_shape"])
    shape = np.clip((r.ambient_c - 24.0) / 9.0, 0, 1.2) * (0.35 + 0.65 * occ)
    # weekend whole-load factor the generator applied (mall-style archetypes
    # boost weekends; office-style cut them)
    wk = plant.get("wk_factor", 0.55)
    return plant["strip_kw"] * shape * (1.0 if weekday else wk)


def simulate_day(day_df, policy, label, plant=None):
    """Run one day under a scheduling policy. Returns per-step log."""
    P = plant or BASE_PLANT
    zone = 25.2
    stored = 0.0
    rows = []
    for _, r in day_df.iterrows():
        h = r.timestamp.hour + r.timestamp.minute / 60.0
        weekday = bool(r.weekday)

        # Decisions use inputs available from the prior interval. The
        # simulated physics and meter still use the actual row below.
        solar_fc = getattr(r, "solar_forecast_kw", np.nan)
        demand_fc = getattr(r, "demand_forecast_kw", np.nan)
        ambient_fc = getattr(r, "ambient_forecast_c", np.nan)
        have_forecast = not (pd.isna(solar_fc) or pd.isna(demand_fc)
                             or pd.isna(ambient_fc))
        if pd.isna(solar_fc):
            solar_fc = r.solar_pv_kw
        if pd.isna(demand_fc):
            demand_fc = r.building_kw
        if pd.isna(ambient_fc):
            ambient_fc = r.ambient_c
        decision_row = r.copy()
        decision_row["solar_pv_kw"] = solar_fc
        decision_row["building_kw"] = demand_fc
        decision_row["ambient_c"] = ambient_fc

        # 1. policy decides the chiller draw using WATTWISE-1 forecasts.
        chiller_kw, action = policy(h, zone, stored, decision_row, P)

        # 2. thermal physics for this step
        cool_c = chiller_kw * 0.5 / P["kwh_per_degc"]       # deg C cooled
        heat_c = heat_gain(r, h, weekday, P)                # deg C warmed

        if cool_c >= heat_c:
            surplus = cool_c - heat_c
            zone = max(BAND_LO_C, zone - surplus)
            if not P["essential"]:
                # flexible plants bank the surplus cold; essential plants
                # have no thermal storage to charge (honest counter-example)
                banked = surplus * P["kwh_per_degc"] * 0.85  # 15% storage loss
                stored = min(P["cap_kwh"], stored + banked)
        else:
            deficit = heat_c - cool_c
            # burn banked cold first
            burn_kwh = min(stored, deficit * P["kwh_per_degc"])
            stored -= burn_kwh
            deficit -= burn_kwh / P["kwh_per_degc"]
            zone += deficit                                # honest: may pass 26

        # 3. safety net: comfort is the hard wall
        #    (essential plants already run at their fixed max)
        if zone > BAND_HI_C and not P["essential"]:
            chiller_kw = P["chiller_max_kw"]               # emergency pull-down
            zone = min(zone, BAND_HI_C + 0.4)              # recovery takes time
            action = "safety"

        # 4. meter: strip the generator's cooling, add our scheduled draw
        nonflex = max(0.0, r.building_kw - strip_cooling(r, h, weekday, P))
        total = nonflex + chiller_kw
        net = max(total - r.solar_pv_kw, 0.0)

        rows.append({
            "time": r.timestamp.strftime("%H:%M"),
            "zone_c": round(zone, 2),
            "stored_kwh": round(stored, 1),
            "chiller_kw": round(chiller_kw, 1),
            "total_kw": round(total, 1),
            "solar_kw": round(r.solar_pv_kw, 1),
            "solar_forecast_kw": round(float(solar_fc), 1),
            "demand_forecast_kw": round(float(demand_fc), 1),
            "ambient_forecast_c": round(float(ambient_fc), 2),
            "forecast_source": getattr(r, "forecast_source", None)
                               or ("aligned forecast" if have_forecast
                                   else "observed-value-fallback"),
            "net_grid_kw": round(net, 1),
            "action": action,
        })
    out = pd.DataFrame(rows)
    out.attrs["label"] = label
    return out


def billed_peak(log):
    """Max demand over the CHARGED window only (08:00-22:00).
    TNB does not charge MD during off-peak hours - verified, Notes/03."""
    hrs = (log.time.str.slice(0, 2).astype(int)
           + log.time.str.slice(3, 5).astype(int) / 60.0)
    mask = hrs.between(CHARGED_WINDOW[0], CHARGED_WINDOW[1],
                       inclusive="left")
    return float(log.net_grid_kw[mask].max())


# --- policy A: dumb baseline (how buildings run today) -------------------

# dumb BMS morning timer, by building type: full plant, no zone feedback.
# offices ramp 7:00-10:30; malls open 10:00 so their timer runs 9:30-13:00
DUMB_TIMER = {"office": (7.0, 10.5), "mall": (9.5, 13.0), "flat": (0.0, 0.0)}


def _hold_kw(zone, target, heat_c, plant):
    """kW needed to hold `target` this step (staged proportional)."""
    need = heat_c * plant["kwh_per_degc"] / 0.5
    if zone > target:
        need += (zone - target) * plant["kwh_per_degc"] / 0.5
    return min(max(need, plant["chiller_min_kw"]), plant["chiller_max_kw"])


def make_policy_dumb():
    """How buildings run today:
    - night setback: small draw holding the top of the band
    - a wall-clock timer runs the plant at 100% through the morning
      occupied ramp, ignoring both zone state and the MD clock
    - after the timer: bang-bang at 25C - full power whenever warm,
      minimum when satisfied - so bursts stack onto the afternoon peak
    The timer stack-up (full plant + occupancy ramp + solar still weak)
    is what produces the documented 8:30-10:30 coincident MD peak
    (Energies 2019 MDRed paper, verified in Notes/03-FACTS-AND-SOURCES)."""
    def policy(h, zone, stored, r, plant):
        if plant["essential"]:
            return (plant["chiller_max_kw"], "essential-cooling")
        t0, t1 = DUMB_TIMER.get(plant["occ_shape"], (7.0, 10.5))
        if h < t0 or h > 21.5:
            # night setback: hold the top of the band, nothing more
            heat_c = heat_gain(r, h, bool(r.weekday), plant)
            return (_hold_kw(zone, 26.0, heat_c, plant), "night-setback")
        if h < t1:
            return (plant["chiller_max_kw"], "startup-timer")
        # after the timer: setpoint control at 25C. Mostly modulating,
        # with a full-power burst only when the zone drifts high.
        heat_c = heat_gain(r, h, bool(r.weekday), plant)
        if zone > 25.5:
            return (plant["chiller_max_kw"], "reactive")
        return (_hold_kw(zone, 25.0, heat_c, plant), "hold")
    return policy


# --- policy B: WattWise rules -------------------------------------------

# after coast ends, recovery to 25C is spread gently (target 25.4, capped
# plant) so the pull-down never becomes the new billed peak
POST_COAST = (10.5, 12.5)


def make_policy_wattwise():
    """Pre-cool before the peak window (mostly in the uncharged off-peak),
    coast through it on banked cold, soak midday solar."""
    def policy(h, zone, stored, r, plant):
        if plant["essential"]:
            return (plant["chiller_max_kw"], "essential-cooling")
        solar = max(0.0, float(r.solar_pv_kw))
        demand = max(0.0, float(r.building_kw))
        nonflex_forecast = max(0.0, demand - strip_cooling(
            r, h, bool(r.weekday), plant))
        solar_surplus_forecast = max(0.0, solar - nonflex_forecast)

        if in_window(h, (PRECOOL_START, CHARGED_WINDOW[0])):
            return (plant["chiller_max_kw"], "precool")

        if in_window(h, COAST_WINDOW):
            # coast: hold the top of the comfort band with a capped plant,
            # burning the banked cold first. Not a blind shutdown - the
            # zone must ride 8:00-10:30 without ever crossing 26C.
            heat_c = heat_gain(r, h, bool(r.weekday), plant)
            kw = min(_hold_kw(zone, BAND_HI_C - 0.2, heat_c, plant),
                     plant["chiller_max_kw"] * 0.5)
            return (kw, "coast")

        if (in_window(h, (SOAK_START, SOAK_END))
                and solar_surplus_forecast >= plant["chiller_min_kw"]):
            # Use the demand and PV forecasts to consume expected local
            # surplus first, capped below full plant. No wheeled-energy
            # credit is assumed in the meter calculation.
            soak_kw = min(plant["chiller_max_kw"] * 0.9,
                          solar_surplus_forecast)
            return (soak_kw, "soak")

        if in_window(h, POST_COAST):
            # gentle recovery: ride back toward 25C over a couple of hours
            # with a capped plant instead of snapping back at full power
            heat_c = heat_gain(r, h, bool(r.weekday), plant)
            kw = min(_hold_kw(zone, 25.4, heat_c, plant),
                     plant["chiller_max_kw"] * 0.75)
            return (kw, "recovery")

        # comfort management outside the danger window: proportional
        # tracking of the band - exactly the cooling the zone needs, so
        # afternoon recovery never becomes the new billed peak
        # (applies at night too: comfort never sleeps)
        heat_c = heat_gain(r, h, bool(r.weekday), plant)
        if zone >= BAND_HI_C - 0.15:
            return (plant["chiller_max_kw"], "comfort-urgent")
        if 6 <= h < 22:
            kw = _hold_kw(zone, 25.0, heat_c, plant)
            if kw >= plant["chiller_max_kw"] * 0.85:
                act = "comfort-catchup"
            elif kw >= plant["chiller_max_kw"] * 0.4:
                act = "comfort-hold"
            else:
                act = "hold"
            return (kw, act)

        if h < 5.5 or h > 21.5:
            return (plant["night_kw"], "night-min")

        return (plant["chiller_min_kw"], "hold")
    return policy


# backwards-compatible single-site entry points (base site)
policy_dumb = make_policy_dumb()
policy_wattwise = make_policy_wattwise()


# --- scoring -------------------------------------------------------------

def score(logs):
    peaks, bills = [], []
    for log in logs:
        peak = billed_peak(log)                          # charged window only
        md = peak * MD_RATE_RM
        energy = float((log.net_grid_kw * 0.5 * ENERGY_RM_KWH).sum())
        peaks.append(peak)
        bills.append(md + energy)
    return {
        "billed_peak_kw_mean": round(float(np.mean(peaks)), 1),
        "billed_peak_kw_max": round(float(np.max(peaks)), 1),
        "day_bill_rm_mean": round(float(np.mean(bills)), 0),
    }


def main():
    df = pd.read_csv(DATA, parse_dates=["timestamp"])
    df["weekday"] = df.timestamp.dt.dayofweek < 5

    # WATTWISE-1 h1 models issue forecasts for the next half-hour. Align
    # those predictions to the interval they describe before simulation.
    import sys
    sys.path.insert(0, str(HERE.parent / "01 Prediction Module"))
    import train_forecast as TF
    forecast = TF.forecast_h1(df)
    df["solar_forecast_kw"] = forecast["solar"]
    df["demand_forecast_kw"] = forecast["demand"]
    df["ambient_forecast_c"] = df["ambient_c"].shift(1)
    df["forecast_source"] = TF.forecast_source()

    # representative days: 2 weekdays, weekend, a clear + a monsoon day
    picks = [8, 9, 11, 12, 260]
    logs = {"dumb": [], "wattwise": []}
    for doy in picks:
        day = df.iloc[doy * 48:(doy + 1) * 48].reset_index(drop=True)
        logs["dumb"].append(simulate_day(day, policy_dumb, "dumb"))
        logs["wattwise"].append(simulate_day(day, policy_wattwise, "wattwise"))

    results = {k: score(v) for k, v in logs.items()}
    results["forecast_source"] = TF.forecast_source()
    results["evaluation_basis"] = "calibrated synthetic data; five representative days"
    sh = (results["dumb"]["billed_peak_kw_mean"]
          - results["wattwise"]["billed_peak_kw_mean"])
    results["peak_shave_pct"] = round(
        100 * sh / results["dumb"]["billed_peak_kw_mean"], 1)
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
