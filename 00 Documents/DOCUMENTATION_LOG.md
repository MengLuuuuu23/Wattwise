# WattWise — Documentation Log
*A dated chronological record of builds, updates, and key decisions (newest first).*

> **Note:** Data figures follow our source discipline (verified vs. illustrative). Full engineering history is available via the repository's git log.

---

### 2026-10-14 — Forecast-to-dispatch integration
* **WATTWISE-1 → WATTWISE-2:** The +30-minute solar and demand predictions are aligned to the interval they forecast, so dispatch uses values issued one interval earlier. Ambient temperature uses a one-step persistence forecast until a weather forecast is available.
* **Solar absorption:** The WattWise soak rule estimates local PV surplus after forecast non-flexible demand, then caps chiller draw to that surplus and the plant limit. Comfort remains the hard constraint, and CREAM wheeling credits are not assumed in settlement.
* **Evidence status:** Source integration is in place. The repository tracks the trained WATTWISE-1 models. Re-score the forecast-informed scheduler with the trained models before quoting updated savings; prior rule-only results predate this change.

### 2026-10-14 — Runnable forecast fallback and honest dashboard diagnostics
* **Pipeline availability:** Added a transparent persistence fallback for environments without trained artifacts or optional dependencies. Forecast source is carried into scheduler logs, the summary, and the dashboard payload; dependencies are listed in `requirements.txt`.
* **Dashboard evidence:** Replaced hard-coded held-out demand accuracy with error calculated only over elapsed intervals in the synthetic demo replay. The dashboard discloses the forecast source and excludes CREAM wheeling credits from site-meter savings.
* **Next evidence gate:** Run the refreshed pipeline against the tracked trained models, then evaluate forecast error and scheduler savings over representative conditions before updating proposal claims.

### 2026-10-13 — Physical Demo Kit (`esp32/wattwise_demo`)
* **Hardware Evolution:** Upgraded through version iterations to v4. A physical dial actuator physicalizes the active schedule (sweeping quickly during off-peak hours, moving slowly between 08:30–10:30, and running fast in basic mode).
* **Interface & Controls:** Includes status indicator lights, a 16x2 text display, a power toggle button, and a standalone 5-minute accelerated day cycle.
* **Companion Link:** `wattwise.py --port COMx` streams status, time, mode, state, and power at 115200 baud. The terminal link acts as the system master clock when connected and automatically wakes up sleeping hardware nodes.

### 2026-10-13 — Companion Monitor (`03 User Interface/wattwise.py`)
* **Terminal Dashboard:** A command-line twin of the main web dashboard sharing the same township data model.
* **Features:** Five distinct views, 3-level drill-down navigation (entire portfolio $\rightarrow$ township $\rightarrow$ individual building) for building and forecast tabs, a timeline-driven schedule view showing half-hour power allowances per building, day navigation, system health views (equipment watchlist, solar health, rule runtimes), and CSV export capabilities using built-in libraries only.

### 2026-10-12 — Multi-Town Portfolio Setup
* **Data Model v2:** Expanded to cover three townships (City of Elmina, Bandar Bukit Raja, and Ara Damansara) encompassing 13 buildings total.
* **Forecasting & Solar:** Incorporates solar forecasts per town and building, demand forecasts per building, and realistic on-site solar utilization (no grid export; excess power is safely clipped).
* **Dataset Scale:** Total dataset size reached ~640 KB to accommodate a 21-day schedule window (3 weeks $\times$ 7 days $\times$ 13 buildings).

### 2026-10-12 — Smart Scheduler v1
* **Baseline Configuration:** Implemented per-building equipment parameters with a realistic baseline comparison (using night setbacks and standard morning timers, causing energy peaks to consistently land between 09:30–10:30, matching recorded peak demand windows).
* **Reference Cases:** Utilized an essential data center building as a reliable counter-example for load profiles.
* **Tariff Constants:** Integrated commercial Time-of-Use rate structures ($30.19 + 66.87 = 97.06\text{ RM/kW/month}$).

### 2026-10-11 to 2026-10-12 — Foundation: Core Modules (01–03)
The three modules everything else is built on (first commits of the build, dated from repository history):

* **01 Prediction Module — WATTWISE-1** *(Committed 2026-10-12 00:03)*
  * Built using two core scripts: `generate_data.py` constructs a calibrated synthetic dataset (one year of 30-minute data for a modelled ~1,000 kW commercial site with 600 kWp PV, totaling 17,520 rows). `train_forecast.py` trains 12 gradient-boosting forecasters (solar and demand across 6 horizons from +30 min to +3 h) evaluated walk-forward on the final 60 days (time order preserved, never shuffled).
  * **Results:** Solar normalized RMSE of 7.35% (R-squared 0.996); demand mean absolute error of $10.2\text{ kW}$.
  * **Calibration Anchors:** Specific yield of 1,285 kWh/kWp/year vs. the 1,274 Malaysian national average; load factor of 0.51 (intentionally peaky to provide shaving headroom); net peak landing in a September monsoon month.
  * **Model Choice:** `HistGradientBoostingRegressor` chosen as a defensible tabular baseline. Any complex neural architecture must outperform this on the exact same split to justify its overhead.

* **02 Scheduler Module — WATTWISE-2 v0** *(Committed 2026-10-12 00:23)*
  * A rule-based controller coupled with a building thermal simulator, benchmarked against a reactive "dumb" baseline under identical weather and load profiles. Uses a 4-stage priority sequence: **precooling (05:30–08:30) $\rightarrow$ coasting (08:30–10:30) $\rightarrow$ soaking (11:00–14:30 on surplus solar) $\rightarrow$ proportional comfort tracking**.
  * **Results:** Achieved a 14.5% peak reduction (mean daily peak dropping from 794.6 kW to 679.6 kW) with zero comfort violations, holding zones strictly inside a 24–26 °C band day and night.
  * **Design Iterations:** Three prior iterations were discarded due to unrealistic physics (e.g., thermal banks that never depleted or afternoon rebounds performing worse than baseline). The final shipped thermal model treats stored coldness as a finite 900 kWh budget and rejects silent comfort overrides.

* **03 User Interface** *(First commit 2026-10-12 00:41, with five same-day revisions)*
  * Comprises `index.html` and the startup script `START-DASHBOARD.bat`. 
  * **Evolution Lineage:** 3D township dashboard (Three.js) $\rightarrow$ light theme with Calibri typography, collapsible 2D site map, and live WATTWISE-1 forecast tab $\rightarrow$ solar forecast table-chart (amber capsules with green/red actual underlines) $\rightarrow$ 5-tab engineering workstation (overview register + alarms, scheduler control room, reports/EECA/CSV, command bar) $\rightarrow$ MATLAB-style workstation featuring ribbon toolbars, dockable panels, breadcrumb command bar, and status bar. QA findings from the cleanup pass are documented in `03 User Interface/REVIEW.md`.

> **Source Discipline Notice:** The prediction metrics above represent walk-forward performance on calibrated synthetic data to validate pipelines and feature engineering, not measured field results. Published Malaysian benchmarks of this class indicate solar nRMSE around 6.75% and R-squared around 0.957. Synthetic R-squared values must never be cited as real-world operational performance.
