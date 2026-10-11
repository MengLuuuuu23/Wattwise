# WattWise

**Wattwise is an autonomous software layer that cuts electricity costs in Malaysian commercial buildings. It shifts flexible cooling load to hours when power is cheap or free. Wattwise eliminates the need to install batteries adjacent to buildings, and operates as a digital brain of smart meters when applicable.**

This is an entry for the Sime Darby Property University Hackathon 2026, "Township of Tomorrow", Planet track (Smart energy efficiency).

## The Problem

One bad half hour sets the whole month's bill. Buildings on medium-voltage supply pay a demand charge for the single highest 30-minute interval of the month. Measured Malaysian buildings hit that peak between 8:30 and 10:30am, at the start of office hours.

- **Demand charges are RM89.27 to RM97.06 per kW**, set by one half hour, every month.
- **Solar peaks at midday.** It is strong after the billed peak has passed and weak when it lands.
- **Surplus solar cannot be sold.** Under SELCO rules, excess generation may not flow back to the grid. Midday surplus is wasted unless used in the moment.
- **Compliance is now law.** EECA 2024 requires large consumers to appoint an energy manager, run an EnMS, and file reports and audits.
- **The battery fix costs millions.** Store midday solar, discharge at peak. Heavy capital, depreciating hardware, replacement cycles.

And the squeeze is not only on buildings. The grid itself is being pushed from both sides at once, according to TNB and the Grid System Operator. *(Source: [Eco-Business, Sept 2026](https://www.eco-business.com/news/malaysias-power-grid-strains-under-data-centre-boom-and-renewables-growth/))*

- **Data centres already take 9.28% of Malaysia's electricity**, and they behave differently: flat, continuous load from the moment they connect.
- **Renewables add variability on the supply side.** Malaysia targets 40% of the power mix by 2035 and 70% of installed capacity by 2050.
- **The system's stated answer is flexibility, not just new wires.** GSO's position: flexibility is just as important as capacity.

A building that flattens its morning peak and absorbs midday solar is doing exactly what the grid is asking for. WattWise's savings are building-level, but its behaviour is grid-level good citizenship.

## The Idea

Move the load, not the electricity. WattWise schedules the building's flexible loads so the work happens when power is cheap or free:

- **Chiller start times**
- **Water pumps**
- **Pre-cooling**

With Wattwise:

- **Before 8am: pre-cool.** The building's concrete and air become a thermos.
- **8:30 to 10:30am: coast.** Ride through the billed window on stored cold.
- **Midday: soak.** Absorb surplus solar into thermal mass and water tanks.

Zone temperatures stays inside the 24 to 26°C band, ensuring comfort is never affected.

A published NREL study ran a learning controller on a real 40-floor building. It cut peak demand by about 20% and discovered pre-cooling on its own.

## How It Works

| Module | Job |
|---|---|
| **WATTWISE-1** | Forecasts solar output and building demand, 30 min to 3 h ahead, on the 30-minute billing grid |
| **WATTWISE-2** | Schedules flexible loads against those forecasts. Rule engine first, learning scheduler later |

The loop runs every 30 minutes. That matches the interval the demand charge is measured on, which is the whole design point.

## Repo Layout

- `00 Documents/` : concept, build plans, sources, critique
- `01 Prediction Module/` : WATTWISE-1
- `02 Scheduler Module/` : WATTWISE-2
- `03 User Interface/` : dashboard

## Status

Proposal stage. Expected submission is 20 Oct 2026. 
