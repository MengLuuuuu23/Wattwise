# WattWise — Documentation Log
*A dated chronological record of builds, updates, and key decisions (newest first).*

> **Note:** Data figures follow our source discipline (verified vs. illustrative). Full engineering history is available via the repository's git log.

---

### 2026-10-13 — Physical Demo Kit (`esp32/wattwise_demo`)
* **Hardware Evolution:** Upgraded through version iterations to v4. A physical dial actuator physicalizes the active schedule (sweeping quickly during off-peak hours, moving slowly between 08:30–10:30, and running fast in basic mode).
* **Interface & Controls:** Includes status indicator lights, a 16x2 text display, a power toggle button, and a standalone 5-minute accelerated day cycle.
* **Bench Testing Findings:** 
  * Confirmed the dial motor is positional (v3.1 constant-write test successfully held it at maximum, whereas a continuous-spin motor would have kept turning).
  * Traced display flicker root cause to the motor sharing the USB 5V power line.
  * Configured the standalone display to read `"offline"` rather than displaying a misleading 0 kW when disconnected.
* **Companion Link:** `wattwise.py --port COMx` streams status, time, mode, state, and power at 115200 baud. The terminal link acts as the system master clock when connected and automatically wakes up sleeping hardware nodes.

### 2026-10-13 — Companion Monitor (`03 User Interface/wattwise.py`)
* **Terminal Dashboard:** A command-line twin of the main web dashboard sharing the same township data model.
* **Features:** Five distinct views, 3-level drill-down navigation (entire portfolio -> township -> individual building) for building and forecast tabs, a timeline-driven schedule view showing half-hour power allowances per building, day navigation, system health views (equipment watchlist, solar health, rule runtimes), and CSV export capabilities using built-in libraries only.

### 2026-10-12 — Multi-Town Portfolio Setup
* **Data Model v2:** Expanded to cover three townships (City of Elmina, Bandar Bukit Raja, and Ara Damansara) encompassing 13 buildings total.
* **Forecasting & Solar:** Incorporates solar forecasts per town and building, demand forecasts per building, and realistic on-site solar utilization (no grid export; excess power is safely clipped).
* **Dataset Scale:** Total dataset size reached ~640 KB to accommodate a 21-day schedule window (3 weeks x 7 days x 13 buildings).

### 2026-10-12 — Smart Scheduler v1
* **Baseline Configuration:** Implemented per-building equipment parameters with a realistic baseline comparison (using night setbacks and standard morning timers, causing energy peaks to consistently land between 09:30–10:30, matching recorded peak demand windows).
* **Reference Cases:** Utilized an essential data center building as a reliable counter-example for load profiles.
* **Tariff Constants:** Integrated commercial Time-of-Use rate structures ($30.19 + 66.87 = 97.06$ RM/kW/month).

### 2026-10-11 -> 2026-10-12 — Foundation: Core Modules 01-03
*The three modules everything else is built on. First commits of the build; all dated from the repository history.*

* **01 Prediction Module — WATTWISE-1 (2026-10-12 00:03).** Two scripts. `generate_data.py` builds a calibrated synthetic dataset: one year of 30-minute data for a modelled ~1,000 kW commercial site with 600 kWp PV (17,520 rows). `train_forecast.py` trains 12 gradient-boosting forecasters (solar and demand x 6 horizons, +30 min to +3 h) and evaluates them **walk-forward on the final 60 days, time order kept, never shuffled**.
  * Results: solar **nRMSE 7.35%** (R² 0.996); demand **MAE 10.2 kW**.
  * Calibration anchors: specific yield **1,285 kWh/kWp/yr** vs the 1,274 Malaysian average; load factor **0.51** (deliberately peaky, the profile with shaving headroom); net peak landing in a September monsoon month.
  * Chosen model is `HistGradientBoostingRegressor` as a defensible tabular baseline. The LSTM described in the deck must beat this on the identical split to justify its complexity.
* **02 Scheduler Module — WATTWISE-2 v0 (2026-10-12 00:23).** A rule-based controller plus a building thermal simulator, scored against a reactive "dumb" baseline on the same weather and load. Four rules in priority order: **precool (05:30-08:30) -> coast (08:30-10:30) -> soak (11:00-14:30 on surplus solar) -> proportional comfort tracking**.
  * Results: **14.5% peak shave** (mean daily peak 794.6 -> 679.6 kW), **zero comfort violations**, zone held inside a hard 24-26 °C band day and night.
  * Three prior iterations were rejected for dishonest physics (cold bank that never drained, a fake perfect coast, an afternoon rebound that scored worse than baseline). The shipped thermal model treats banked cold as a finite 900 kWh budget and never silently clamps a comfort violation.
* **03 User Interface (first commit 2026-10-12 00:41, five revisions in one day).** `index.html` plus `START-DASHBOARD.bat`. Lineage: 3D township dashboard (three.js) -> **light theme, Calibri, collapsible 2D site map, tabbed layout with a live WATTWISE-1 forecast tab** -> solar forecast table-chart (amber forecast capsule, green/red actual underline) -> five-tab engineering UI (overview register + alarms, scheduler control room, reports/EECA/CSV, command bar) -> **MATLAB-style workstation** (ribbon toolbars, dockable panels, breadcrumb command bar, status bar). QA findings from the cleanup pass are recorded in `03 User Interface/REVIEW.md`.

*Source discipline: the prediction figures above are walk-forward results on **calibrated synthetic data**. They validate the pipeline and the feature set, not real-world accuracy. Published Malaysian benchmarks of this class: solar nRMSE 6.75%, R² 0.957. Never quote the synthetic R² values as measured field performance.*