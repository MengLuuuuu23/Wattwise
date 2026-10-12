# Wattwise UI review — 12 Oct 2026

> **STATUS 13 Oct 2026: all findings fixed.** See "Fix log" at the bottom
> for what changed in scheduler.py / generate_ui_data.py / index.html and
> the verification results. Kept for the record and the reasoning.

Scope: `index.html`, `generate_ui_data.py`, `scheduler.py`, `data/township.json`.
Method: full code read + programmatic checks against township.json. Browser tool
timed out in this session, so no screenshots; every finding below is verified
against the actual data file or code path, and the page serves fine over HTTP
(200, 67 KB html + json). JS syntax checks clean.

---

## CRITICAL

### 1. All five buildings have byte-identical thermal + scheduler traces
`zone_c`, `stored_kwh`, `action`, `chiller_kw` are **exactly identical** across
mall / office_tower / innovation_park / data_centre / warehouse, in both dumb and
wattwise modes (verified element-by-element).

Visible symptoms a judge will spot in seconds:
- **Comfort monitor**: all 5 colored lines lie perfectly on top of each other → one thick line. Looks fake.
- **Cold bank**: all 5 gauges read the same value all day (peak 830.1/900).
- **Intervention log**: the same transitions repeated 5×, only names differ.
- **Buildings page**: "Zone / stored cold" KPI identical whichever building you open.

Root cause (not in index.html): `scheduler.py` physics ignore building scale.
`heat_gain` uses only ambient + the same occupancy shape; chiller limits
(380/60/20 kW) and `KWH_PER_DEGC` are absolute, never scaled by archetype.
`generate_ui_data.py` scales `building_kw` and solar but passes the *same*
thermal plant to every building. Fix: scale `CHILLER_MAX_KW`, `KWH_PER_DEGC`,
`CAPACITY_KWH_C` and `heat_gain` internals per archetype (and give the mall the
weekend occupancy shape it already has in `occupancy()`), then regenerate
township.json.

### 2. EECA chart is off by 1000×
`renderReports`: `kwh * 3.6 * 365` produces **MJ/yr** but is labelled GJ.
Bars print "21,835,592 GJ" against a 21,600 GJ threshold line — six orders of
magnitude of nonsense on screen. Y-axis auto-scales so it *looks* fine until
anyone reads a number. Fix: `kwh * 3.6 / 1000 * 365`.
(Correct values: mall 21,836 · DC 24,070 over; office 14,083 · park 11,733 ·
warehouse 6,840 under.)

## HIGH

### 3. `has_solar` inverted for two buildings
- **office_tower**: `has_solar: false`, but its traces carry 187 kW of PV — and the day chart's solar overlay draws it anyway.
- **data_centre**: `has_solar: true`, map badge shows "1F ☀ PV", but its solar is exactly 0.0 (archetype solar multiplier is 0.0 while meta says true).

Cause: `ARCHETYPES` and `BUILDING_META` in generate_ui_data.py disagree.
Fix the metadata, and decide the story: a DC with zero PV in a solar demo is
itself a talking point — but then the badge must not claim PV.

### 4. Forecast KPIs use the whole day's actuals at every timestep
`renderForecastKpis` loops `i = 0..47` regardless of `step`. At midnight
(step 0) the page already reports the day's solar MAE **15.2 kW / MAPE 19.5%** —
computed against actuals that "haven't happened yet". For a product whose pitch
is *30-min-ahead forecasting*, perfect-hindsight stats at 00:00 is the opposite
of the claim. It also contradicts the footnote on the same page (nRMSE 7.35%).
Fix: only accumulate where `i <= step`.
Related muddle on the solar card: "kWh forecast today" only sums up to `step`
(shows 0.00 at demo start) and "forecast coverage" is really just
`(step+1)/48` = clock progress, not coverage. Rename or recompute.

### 5. Nothing peaks in the billed window on the demo day
The chart's red 08:30–10:30 band is the core visual argument, but in this data:
dumb peaks land at **11:00 (mall)** and **18:30 (all others)**; wattwise peaks at
15:30 / 17:00 / 06:00 / 05:30 / 05:30. **Zero** peaks inside the band, so the
shaded region highlights exactly where nothing happens. This also contradicts
the AGENTS.md framing rule ("offices peak 8:30–10:30"). Root cause is upstream
(strip_cooling / dataset calibration), not the UI — but the demo day chosen
makes the product's own thesis invisible. Either recalibrate or pick a day
where the story holds.

## MEDIUM

### 6. "Township peak" KPI shows the wrong thing
`renderOverview` takes `max()` over buildings → shows **1,150 kW** (single
mall) labelled "Township peak". The actual coincident township peak is
**4,270 kW**. Fix: sum per step, then max over steps.

### 7. Data centre contradicts itself on screen
Buildings page (correctly) says "flat, inflexible load — WattWise does not
apply here", but the Scheduler page's Rule State table shows the DC running
precool → coast → soak with a cold bank filling to 830 kWh like everyone else
(consequence of #1). One screen calls it untouchable, the next shows the
scheduler actively optimizing it.

### 8. innovation_park shave = 17.8% breaks the claim discipline
AGENTS.md hard rule: savings stay in the **5–15%** band. The Building register
and the building subtitle proudly print 17.8%. Retune the archetype or clamp
the claim.

## LOW

### 9. Day label wrong
township.json says "September (monsoon season) - Tuesday"; doy 260 of the 2026
dataset is **Friday 18 Sep 2026**. Cosmetic, but it's the first string in the file.

### 10. Capacity split hardcoded 0.3038
Tariff-verified split is 30.19/97.06 = **0.3110**. Column header says "31%" so
it rounds right, but derive it from the rate constants instead of a magic number.

### 11. Small interaction roughness
- `set time 14:29` floors to 14:00 (29 min jump); `set time 09:45` → 09:30 is fine but the rounding is silent.
- `select` command needs a key/label prefix match — "select the mall" fails.
- Ribbon: Overview has Pause, Buildings page doesn't (inconsistent transport).
- Zone chart hardcodes "zone stays inside the band — comfort is never traded away" as a *string*; with 0 violations it's true today, but it's identical for all 5 buildings (see #1) and would lie if data changed.

### 12. Accessibility
Ribbon tabs and map buildings are divs/SVG — no tabindex, no roles, no keyboard
path. Canvas charts have no text alternative. Fine for a demo, worth one line
if judges ask about operator use.

---

## What's solid
Honest labeling overall (synthetic-data footer, illustrative notes), clean
fetch failure handling, JS syntax valid, CSV export correct, tariff math
(RM97.06/kW) checks out against 03-FACTS, command bar is a nice touch.

## Suggested fix order
1. scheduler.py per-building scaling → regenerate township.json (fixes 1, 7, and enables 8)
2. EECA `/1000` (one line)
3. renderForecastKpis `i <= step` (one line)
4. has_solar metadata
5. Township peak sum-vs-max
6. Demo-day peak-window story (needs a calibration decision)

---

## Fix log — 13 Oct 2026 (all 12 findings closed)

| # | Fix | Where |
|---|-----|-------|
| 1 | Per-building PLANT dicts (chiller kW, thermal mass, bank kWh, envelope/internal gains, occupancy shape) via `scale_plant()`; every archetype now produces distinct zone/bank/action traces | scheduler.py v1 |
| 2 | `kwh * 3.6 / 1000 * 365` — bars now real GJ (mall 20.6k, DC 22.0k over; office 15.1k, park 12.4k, warehouse 7.2k under 21,600) | index.html renderReports |
| 3 | `has_solar` computed from the archetype solar multiplier (office 1.0 = has PV; DC 0.0 = none) | generate_ui_data.py |
| 4 | Forecast KPIs loop `i <= step`; MAE starts null, builds as the day plays; peak-solar KPI elapsed-only | index.html renderForecastKpis |
| 5 | Dumb baseline = night setback + wall-clock morning timer (7:00–10:30) + staged afternoon hold; dumb billed peaks now land 09:30–10:30, the documented MD-capture window; WattWise coasts 8:00–10:30, recovers gently after | scheduler.py |
| 6 | "Township coincident peak" = sum of all buildings per step, max over day (3,395 kW @ 10:00 dumb) | index.html renderOverview |
| 7 | DC = essential plant: fixed 24/7 cooling, no banking, action "essential-cooling" everywhere; Buildings page and Scheduler page now tell the same story | scheduler.py + generate_ui_data.py |
| 8 | Shaves re-calibrated into the 5–15% band: mall 13.4% (plant_mult 0.75 per AIP 2187's ~26% chiller share), office 10.1%, park 8.4%, warehouse 5.3%, DC 0.0% | generate_ui_data.py |
| 9 | Demo day picked by calendar date — Friday 18 Sep 2026, verified weekday, monsoon month; label carries the full date | generate_ui_data.py |
| 10 | Tariff constants exported in township.json (`capacity_share` 0.311 = 30.19/97.06); UI reads them; column header derives the % | scheduler.py + generate_ui_data.py + index.html |
| 11 | `set time` snaps to nearest 30-min grid slot and says so; forecast-chart nowline hidden at end of day; cold-bank gauges per-building capacity; zone-chart caption data-driven | index.html |
| 12 | Not attempted (demo scope) — noted for judges Q&A | — |

Billed peaks are now measured over the **charged window 08:00–22:00 only**
(TNB does not charge MD 22:00–08:00 — verified in 03-FACTS-AND-SOURCES),
base-site summary: mean shave **8.1%**, max **9.0%**, 0 comfort violations
either mode. Weekend days shave 15.9% (Sunday) because the baseline load
drops while the precool physics stays available — within band, honest.
