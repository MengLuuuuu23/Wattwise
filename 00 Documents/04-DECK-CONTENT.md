# WattWise - Deck Content (slide by slide)

Final text for the Wattwise_v2 deck. Numbers follow 03-FACTS-AND-SOURCES.md; illustrative items are labelled.

## Slide 1 - Title

PROJECT NAME: WATTWISE
Solar Output & Energy Scheduling Prediction Model for Commercial Properties
*(consider retitling to the broader promise: "The township energy operating layer")*

## Slide 2 - The Problem

- A commercial building is billed on its **worst half hour of the month**, not on how much energy it uses. (TNB)
- That half hour costs **RM89.27 to RM97.06 per kW** of Maximum Demand, set by the single highest 30-minute interval. (TNB RP4; Trexon)
- Solar does not fix it: solar cuts midday energy, never the morning peak, and under SELCO surplus **cannot be exported**. (SEDA)

## Slide 3 - How Does This Affect People?

- Mall operators pass cost on: PPK estimated **RM5m/yr** extra for a 500k sq ft mall. (PPK via The Star/FMT)
- Pass-through has broken: operating cost exceeds recoverable charges by **27%**, up from 13.4% in 2022. (PPK survey via The Edge)
- Grid tightening: data centres take **9.28%** of national electricity; peak hit **20.75 GW**. (Eco-Business; TMR)

## Slide 4 - Sime Darby's Projects

- SDP owns **five malls** and a **RM1.5bn** investment portfolio across townships including City of Elmina, KL East, Bandar Bukit Raja. (simedarbyproperty.com; Bursa Feb 2025)
- Already generating solar two ways: **GSPARX JV** (Jul 2024) on its own buildings; Malaysia's **first CREAM rollout as LEGA** at Elmina, wheeled through TNB's grid to SDP's own commercial loads. (SDP releases)
- **The assets, the solar and the green credentials already exist.**

## Slide 5 - How Does This Affect Sime Darby?

- Around those same assets, all three rules changed at once: demand charge close to tripled on MV (**RM30.30 to RM89.27/kW** general; RM45.10 to RM97.06 ToU), CREAM made SDP the nation's first LEGA with no off-the-shelf tooling, and EECA 2024 added statutory duties above 21,600 GJ. (TNB; SDP; ST)
- CREAM power arrives as green energy through the grid, **but the demand charge still lands on the receiving building's meter**.
- **None of this is SDP falling behind. No operator has tooling for all three together. WattWise is that layer.**

## Slide 8 - What Would Be an Appropriate Solution?

Intro: the three problems share one shape, they are **timing problems**, so the solution must act *before* the meter records.

| The solution must... | Because... |
|---|---|
| Predict the peak before it happens | MD is set by one 30-min window; reacting after means paying all month |
| Use the solar SDP already owns | CREAM/GSPARX output arrives midday; the billed peak is 8:30-10:30am |
| Turn the same data into compliance | EECA needs EnMS, reports, audits; existing data should auto-fill them |
| Add no new hardware | Batteries cost millions; meters, panels, chillers already exist |

Closer: **Anything meeting all four is a software layer. That's what we built.**

## Slide 9 - Existing Competition

Fix the typo "asset asset-heavy". Reword Plus Xnergy solution cell to "monitors and optimises building energy use" (SOURCE does whole-building analytics, not just HVAC). Keep the speaker note.

| Company | Scope | Solution |
|---|---|---|
| Solarvest | I&C EPC | Large-scale solar + BESS bundled with PowerTrack AIoT for peak shaving |
| Plus Xnergy | CleanTech solutions | Asset-heavy engineering; SOURCE EPMS monitors and optimises building energy |
| Schneider | Global BMS | EcoStruxure building automation and energy monitoring |
| **Wattwise** | **Hardware-agnostic SaaS** | **Pure software overlay: forecasting + peak shaving + automated EECA compliance + tenant billing** |

## Slide 10 - How It Works (analogy, corrected)

> Imagine a station where the trains only run at noon, but the crowds arrive at 9am. No trains, packed platform, and the station is charged for the crowd, not the quiet.
> That's a Malaysian commercial property: solar arrives midday, but the half hour that sets the month's demand charge lands in the morning.

**Delete the IOI City Mall / Sunway Pyramid sentence entirely** (no public record; both are competitors' assets). Rename this slide "The Problem, Retold" and slide 11 "WATTWISE: The Station Conductor" so they stop sharing a title.

## Slide 11 - The Station Conductor

> WATTWISE is a software layer with two parts:
> (1) A **forecasting model** that predicts the site's solar output (weather and irradiance data, plus the site's own generation history) *and* the building's demand profile.
> (2) A **scheduler** that stages flexible loads, like HVAC start times, pumps and pre-cooling, so the same work runs on cheap or free power: midday solar and off-peak hours, instead of the metered morning peak.

## Slides 12-13 - WATTWISE-1 and WATTWISE-2

Final rendered versions exist (wattwise1_v2.png, wattwise2_v1.png). Core text:

**WATTWISE-1.** Trained on: sunlight intensity, panel temperature, air temperature, wind speed, plus the site's own inverter history (no new hardware). How: learns from past output, re-learns monthly, tuned per building. Accuracy: **~93% of solar variation explained 30 min ahead; R2 0.957 published benchmark** on Malaysian rooftop PV; prototype retrains on pilot data.

**WATTWISE-2.** Controls: chiller start times (cool early, coast through peak), water pumps (fill at midday, "a battery made of water"), equipment sequencing (no two big motors in one half hour); **never touches comfort**. Learns: digital twin first, reward = bill saved minus comfort penalties, improves monthly. Proven: **~20% peak cut on a real 40-floor building (NREL)**; 23% cost cut in published RL studies, where pre-cooling emerged by itself.

## Slide 14 - Benefits of Implementing WATTWISE

Same building. Same work. **Smaller bill.**

1. **Lower demand charges** - worst half hour costs RM89.27-97.06/kW; keep it low and save ~RM1,000/yr per kW shaved.
2. **No wasted solar** - surplus can't be sold, so store it as cold air and pumped water: free energy, not lost energy.
3. **Compliance on autopilot** - legal reports written from data already collected. No extra paperwork or staff.
4. **Nothing to buy** - no batteries, no rewiring; runs existing equipment. Software subscription, no new major equipment.

## Slide 15 - What This Looks Like on One Building

1,000 kW peak site (scale of the measured Wisma R&D building, 628-1,001 kW). Illustrative, pending pilot data.

| | Today | With WattWise |
|---|---|---|
| Peak demand | 1,000 kW | 900 kW |
| Demand charge | RM97,060/mo | RM87,354/mo |
| Yearly saving | - | ~RM116,000 |
| Solar thrown away | 30-40 kWh/day | redirected, ~RM4,000-5,300/yr |
| Battery doing the same job | US$55-65k cells, 2-3x installed | |
| Upfront cost of WattWise | software subscription, no new major equipment | |

Footnote: illustrative, from TNB RP4 rates and published studies; replace with pilot interval data.

## Slide 16 - One Township, Everyone Gains

WattWise is not building software. **It is township infrastructure.**

- **Residents** - Earn, not just host: CREAM rooftop income keeps flowing because the energy stays usable.
- **Tenants** - Finally see the bill: green sub-metering replaces the service-charge mystery.
- **The township** - Stays ahead of the law: margin others lose to peak fees and EECA compliance is kept.
- **The grid** - Gets a good citizen: flattened peaks, absorbed solar, less network stress as data centres grow.

Closer: **People, businesses and nature thriving together is the hackathon's theme. This is the layer that makes it operational - one township as one system, not twenty buildings with twenty bills.**

## Slide 17 - Finale

> WattWise helps commercial property managers coordinate energy data, tenant billing and EECA reporting today, while preparing their portfolios for Malaysia's demand-response future.

(Clean out the pasted AI notes and the share.google link from the speaker notes; keep the competitor analysis distilled in slide 9 only.)
