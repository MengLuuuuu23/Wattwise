# WattWise

WattWise is a smart software system that lowers electricity bills for commercial buildings in Malaysia. It shifts air conditioning and cooling work to times when electricity is cheap or free, helping buildings avoid expensive battery purchases. It connects directly to existing building meters and controls without needing any new hardware attached to sealed utility devices.

This is an entry for the Sime Darby Property University Hackathon 2026, "Township of Tomorrow", Planet track, Energy Efficiency category ("smarter energy use across the township").

## The Problem

One single bad half-hour can set a building's entire monthly electricity bill. Buildings on medium-voltage power pay a "demand charge" based purely on their highest 30-minute spike of electricity use in a month. In typical Malaysian offices, that spike happens between 8:30 and 10:30 AM when everyone arrives for work. Shopping malls are busiest in the evenings and weekends, so their peak hits then instead. Either way, a single 30-minute window dictates the cost for the whole month.

- **High Demand Charges:** These cost between RM89.27 and RM97.06 per kW each month, triggered by just one half-hour window.
- **Solar Mismatch:** Solar power peaks at midday. It is strong long after the morning peak has passed, and weak when the morning peak actually hits.
- **Wasted Surplus Solar:** Under current rules (SELCO), excess solar energy cannot be sent back to the grid. Midday surplus power is wasted unless it is used right away.
- **Strict Legal Compliance:** The Energy Efficiency and Conservation Act (EECA 2024) requires large energy consumers to appoint an energy manager, run an energy management system, and file regular audits and reports.
- **Batteries Are Too Expensive:** Buying batteries to store energy is heavy on upfront costs. A 500 kWh battery system costs roughly US$55,000 to US$65,000 just for the cells—often two to three times that amount when fully installed—plus ongoing replacement costs.

The pressure isn't just on individual buildings; the entire national power grid is feeling the strain, according to Tenaga Nasional Berhad (TNB) and the Grid System Operator (Source: Eco-Business, Sept 2026):

- **Data Centres:** Data centres already consume 9.28% of Malaysia's electricity, and they draw a constant, heavy load from the moment they plug in.
- **Renewable Energy Fluctuations:** Renewable sources create supply swings. Malaysia aims for 40% renewable energy in its power mix by 2035 and 70% of installed capacity by 2050.
- **Grid Flexibility:** The grid operator stresses that flexibility is just as important as building new power lines.

A building that flattens its morning peak and soaks up midday solar energy is doing exactly what the grid needs. WattWise saves money at the building level, but acts like a good citizen for the national grid.

## The Idea

![[Pasted image 20261012174704.png]]

Instead of moving electricity around, WattWise moves _when_ the work happens. It schedules heavy energy tasks during hours when power is cheap or free:

- Chiller start times
- Water pumps
- Pre-cooling

How WattWise operates day-to-day:

- **Before 8:00 AM (Pre-cool):** Chill the building early so the concrete walls and air act like a thermal thermos.
- **8:30 to 10:30 AM (Coast):** Ride through the expensive peak window using the stored cold, keeping power draw low.
- **Midday (Soak):** Absorb extra solar power into the building's thermal mass and water tanks.

The indoor temperature stays comfortably inside the 24 to 26°C range. Comfort is a strict rule built into the software scheduler, meaning no one can accidentally change or trade away comfort settings.

## How It Works

| **Module** | **Function** |
| --- | --- |
| **WATTWISE-1** | Forecasts solar generation and building energy demand 30 minutes to 3 hours ahead, aligned with the 30-minute billing schedule. |
| **WATTWISE-2** | Schedules flexible equipment using a smart rule engine first, and an adaptive learning scheduler over time. |

The system loops every 30 minutes. This matches the exact interval that utility companies measure for demand charges, which is the entire point of the design.

Surrounding these two core modules is a wrapper for tenant green billing and automated EECA compliance report generation, built directly from the logged data the scheduler already records.

## Quantified Objectives

The figures below are categorized as verified (sourced directly), derived (calculated from verified inputs), or illustrative (model outputs based on simulations, awaiting real pilot data). None of these are field-measured results yet.

### Engineering Objectives

| **Objective**                  | **Target**                                                                                                                      | **Basis**                                                                 |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Peak demand reduction**      | 5% to 15% of site peak demand, targeting 10%+                                                                                   | Based on load factor limits; rule-engine testing currently achieves 14.5% |
| **Indoor comfort**             | Zero violations outside the 24 to 26°C range                                                                                    | Hard rule built into the scheduler that overrides energy savings          |
| **Solar forecasting accuracy** | Normalized root mean square error (nRMSE) under 8% at 30 minutes ahead, beating standard tracking                               | Based on published Malaysian rooftop LSTM benchmarks (6.75% / R² 0.957)   |
| **Surplus solar absorbed**     | 30 to 40 kWh per day on average per site                                                                                        | Illustrative estimate; surplus energy is highest on low-occupancy days    |
| **Re-plan frequency**          | Every 30 minutes                                                                                                                | Matches the utility demand charge measurement window                      |
| **Hardware needed**            | None. Connects to existing utility meters and building management systems (BMS). Older buildings may need a small data gateway. | Per site                                                                  |

_Modelled on a 1,000 kW peak commercial building, roughly the size of the Wisma R&D building (628 to 1,001 kW peak demand). Illustrative, pending pilot data._

| **Peak Shave Target** | **Power Shifted (kW)** | **Annual Savings (RM1,071 to RM1,165 per kW-year)** |
| --- | --- | --- |
| **5%** | 50 kW | RM53,600 to RM58,200 |
| **10%** | 100 kW | RM107,100 to RM116,500 |
| **15%** | 150 kW | RM160,700 to RM174,700 |

Adding the solar-redirect savings (30 to 40 kWh/day at an estimated RM0.30 to RM0.36 per kWh) brings an extra RM3,300 to RM5,300 per year. A mid-sized building can save roughly **RM110,000 to RM122,000 per year** in recurring savings with zero upfront hardware costs.

Valued at a typical 5% capitalization rate, this creates about **RM2.2m to RM2.4m in building asset value** per site.

### Portfolio Impact

Sime Darby Property’s reported 2025 electricity consumption totals 24,921,964 kWh (89,719 GJ). The Investment & Asset Management division (malls and commercial properties) accounts for 48,131 GJ, which is roughly 13.4 million kWh/year and an average draw of ~1,526 kW (SR2025, verified). Its total annual demand-charge pool is estimated at **RM2.5m to RM2.7m per year** (derived).

| **Portfolio Peak Reduction** | **Annual Savings** | **Share of Group Electricity Spend** |
| --- | --- | --- |
| **10%** | RM252,000 to RM273,000 | ~3% |
| **15%** | RM378,000 to RM410,000 | ~5% |

Estimated portfolio asset value increase at a 5% cap rate: **RM5.0m to RM8.2m** (derived).

### The Honest Reality Check

Sime Darby Property’s FY2025 profit before tax was RM803.4m. Saving RM250,000 to RM410,000 across the portfolio represents about 0.03% to 0.05% of profit. This is a smart operational optimization rather than a financial rescue mission—and we acknowledge that upfront.

The real value lies in four distinct advantages:

1. **Zero Upfront Cost, Recurring, Compounding:** Savings repeat every single month and grow whenever utility tariffs increase, unlike physical hardware that depreciates over time.
2. **More Than Just Energy Savings:** The same software platform handles tenant green billing and compliance reporting, which helps retain tenants rather than just cutting costs.
3. **Maximizing Existing Solar Investments:** Sime Darby Property already has 603 kWp of solar capacity across nine assets and a pioneering CREAM rollout on its balance sheet. WattWise ensures that solar energy is actually used during the hours it matters most.
4. **The Strategic Wedge:** Owning each building's data and control systems is the entry ticket to advanced operating layers and future grid-flexibility revenue. While competitors can copy a scheduling algorithm, being the first software platform integrated directly into Sime Darby Property's own data is a unique advantage.

## The Township Layer

Sime Darby Property is Malaysia’s first Local Energy Generation Aggregator under CREAM, pooling residential rooftop solar energy and wheeling it through TNB's power grid to nearby commercial buildings. That clean energy typically arrives around midday. However, the building's utility bill is still hit by demand charges set during morning spikes that the midday solar barely touches. This timing mismatch is the exact problem WattWise solves for individual buildings.

At the township scale, the system forecasts energy use per site, schedules equipment per building, and generates tenant billing and compliance reports from a single unified dataset. Whether the wheeled solar energy directly lowers the demand charge is a technical settlement detail currently being verified with grid operators, rather than an unproven assumption.

## Repository Layout

- `00 Documents/`: Concepts, build plans, source materials, and critiques
- `01 Prediction Module/`: WATTWISE-1 source code
- `02 Scheduler Module/`: WATTWISE-2 source code
- `03 User Interface/`: Dashboard interface

## Status

Proposal stage. Registration closes October 21, 2026; the final proposal is due October 23, 2026, at 11:59 PM and requires four components: a pitch deck (10 main slides plus an appendix), a 5-minute demo video, a link to the codebase, and optional supporting documents. Finals take place on November 14, 2026.

WATTWISE-1 runs on calibrated synthetic interval data. WATTWISE-2’s rule engine successfully shaves 14.5% of peak energy use on test days with zero comfort violations, fitting squarely within our target 5% to 15% range. Every figure in this project is clearly labeled as a prototype, published benchmark, or illustrative estimate. All referenced facts are tracked in the sources ledger (`Notes/03-FACTS-AND-SOURCES.md`).
