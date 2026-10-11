# WattWise - Overview

**One line:** WattWise is a software layer that cuts electricity bills in Malaysian commercial buildings by moving *when* the building consumes power, not by adding hardware.

## The problem in plain language

Malaysian commercial buildings on medium-voltage supply are billed in an unusual way. Alongside the normal energy charge (kWh), TNB charges for **Maximum Demand**: the single worst half hour of the month, priced per kW. From 1 July 2025 that costs **RM89.27/kW (general)** or **RM97.06/kW (time-of-use)** every month. One busy half hour sets a huge fee for the whole month.

Two timing facts make this painful:

1. **The billed peak lands in the morning**, roughly 8:30 to 10:30am, when buildings ramp up. This is measured, not modelled: published studies record commercial MD capture at 8:30-10:30am and a C1 case at 9:00am.
2. **Solar peaks at midday.** Panels barely work at 9am and cannot store anything. So the flagship green investment (solar) does almost nothing for the most expensive part of the bill.

On top of that, under the SELCO rules surplus solar **cannot be exported**. Midday excess is wasted unless something in the building consumes it.

## The idea

Instead of storing electricity in an expensive battery (the Solarvest approach), WattWise **moves the load to the energy**:

- **Pre-cool early** (5:00-7:30am): run chillers while grid draw is cheap and the peak window is closed. The building's concrete and air hold the cold.
- **Coast through the morning peak** (8:30-10:30am): chillers idle; the building drifts slowly up within the comfort band.
- **Soak up midday solar** (11:00am-2:30pm): deliberately run pumps and pre-chilling on solar that would otherwise be wasted.
- **Relieve the evening** with cold and water stored earlier.

The sunshine gets stored as **cold air and pumped water**, using equipment the building already owns. No batteries, no rewiring, no construction. A software subscription.

## Why now

Three things changed at once for the target customer (Sime Darby Property):

- The July 2025 tariff restructure roughly tripled the demand charge on medium voltage.
- SDP became Malaysia's **first LEGA under CREAM**, aggregating rooftop solar across its townships.
- The **EECA 2024** law makes energy management, reporting and audits mandatory above 21,600 GJ/year.

Each alone is manageable. No operator has tooling for all three together. That layer does not exist. That is WattWise.

## Who gains

- **Landlord:** smaller demand charge, no wasted solar.
- **Tenants:** transparent green sub-metered billing.
- **Residents:** their leased rooftops (CREAM income) become part of a working system.
- **Regulator:** EECA reports generated automatically.
- **The township:** every building running as one system instead of twenty buildings with twenty bills.

## Where it fits in the hackathon

Sime Darby Property University Hackathon 2026, theme "Township of Tomorrow" ([simedarbyproperty.com/universityhackathon](https://simedarbyproperty.com/universityhackathon)). WattWise sits under **Planet, item 3: Energy efficiency**. The brief promises that winning solutions are reviewed for real-world implementation; a software layer with no capex is one of the few student ideas that could realistically pilot within months, because the assets (malls, innovation parks, CREAM solar, GSPARX panels) already exist.

## Key numbers (all verified, see 03-FACTS-AND-SOURCES.md)

| Fact | Value |
|---|---|
| MV demand charge | RM89.27-97.06 per kW per month |
| Old charge (pre-July 2025) | RM30.30 (C1) / RM45.10 (C2) |
| When the billed peak lands | 8:30-10:30am (measured) |
| Cooling's share of building load | 26-58% depending on building type |
| Demand-side saving, illustrative | ~RM116k/year per 100 kW shaved |
| Battery alternative | US$55-65k in cells alone, 2-3x installed |
| WattWise hardware cost | none (subscription) |
