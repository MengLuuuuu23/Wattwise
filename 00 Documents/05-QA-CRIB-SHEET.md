# WattWise - QA Crib Sheet

Every objection we anticipated, with the answer. Rehearse these; the finale is a leadership panel, not a technical one, but one engineer in the room can sink an unprepared answer.

## "Why not just buy a battery?"

> "A battery works, and with enough capital it shaves the peak at least as well as we do. The question is cost: US$55-65k in cells alone for a 500 kWh system, typically 2-3x that installed, plus replacement. WattWise reaches most of the same saving with zero capex because the flexible load was already bought and paid for. And we stack on top of a battery if one exists, we are not against hardware, we are against waiting for it."

**SDP-specific version (use when the judge is from Sime Darby):** SDP is NOT battery-averse. They were the first developer in Malaysia to put expandable BESS in homes (Elmina Ridge, Nov 2024, 122 units, first in country), they are testing repurposed EV batteries to cut BESS cost ~40%, and the Sep 2025 Elmina launch included TNB's first Community Energy Storage System. But look at where every one of those batteries sits: residential-scale and community-scale, framed by their own COO as "resilient infrastructure" and "independence from the grid" ([SDP release](https://simedarbyproperty.com/press-releases/sime-darby-property-leads-way-malaysias-first-solar-powered-homes); [The Edge](https://theedgemalaysia.com/node/734558)). There is no announcement of BESS in their commercial buildings for Maximum Demand shaving. The malls, offices and Innovation Park, the MV tariff class where RM89-97/kW bites, have no battery plan on record. So the line is: **their battery strategy is residential and community scale and doesn't touch the commercial demand charge; that's our lane.** And if cheap repurposed batteries eventually reach their commercial stock, a battery with a smart scheduler beats a dumb one, so WattWise complements Elmina Ridge instead of competing with it. Also worth noting: their EV-repurposing R&D exists to make batteries cheaper, which concedes our core premise that batteries are expensive.

## "Won't pre-cooling affect comfort?"

> "Comfort is a range, roughly 24-26C, and most buildings pin one setpoint in the middle of it. We use the whole band: cool to the bottom early, drift gently to the top during the peak window. Concrete warms slowly, about a degree per couple of hours, which occupants barely register. Comfort is a hard constraint in the scheduler, with automatic penalties, not a suggestion. And in the tropics humidity tightens the top of the band, which is exactly why we claim a conservative 10% and not vendor numbers."

## "Is WattWise passive software embedded in meters?"

> "Neither. It connects to existing meters and building controls, reading data and sending schedule commands over BMS protocols. Nothing is embedded in sealed utility meters, that would need firmware access nobody grants, and interfering with utility metering is an offence under the Electricity Supply Act. And it is not passive: the scheduler actively stages loads. A passive layer is a dashboard; dashboards already exist."

## "Your load curve, where is it from?"

> "It's a model, labelled illustrative on the slide. The published measured anchors are real: Wisma R&D ran MD 628-1,001 kW against a 220-340 kW average, and the morning peak capture at 8:30-10:30 is from the literature. We replace the model curve with the pilot site's 30-minute interval data the moment we have read access."

## "How is this different from Solarvest / Neuron Cloud / KERO?"

> "Solarvest and Plus Xnergy sell hardware-first bundles; we run on whatever is already installed. Neuron Cloud and Tanand do engineering operations control; they do not do tenant billing, and in a multi-tenant property the landlord bills tenants, so billing is not a side feature. KERO is retrospective compliance reporting; we are forward control that also produces the compliance record. The gap we occupy is the combination: forecasting + scheduling + billing + EECA, hardware-agnostic."

## "CREAM solar reduces the demand charge, right?"

> "Careful: CREAM energy is wheeled through TNB's grid as a contractual kWh supply to the receiving building. It lands midday. The billed peak is 8:30-10:30am. So it offsets the energy line while the demand charge on the receiving meter is set by a half hour the solar barely touches. The safe framing is timing mismatch; the exact settlement mechanics are something we'd confirm with GSPARX."

## "10% sounds small. Solarvest claims 20-65%."

> "Their 20-65% comes with a battery in the loop. Software-only is bounded by the flexible fraction of load, cooling is 26-58% of building energy, and the comfort band sets how far you can push it. We would rather defend 10% we can deliver than 65% that needs a container of cells."

## "What buildings does this actually work on?"

> "Peaky ones. Load factor is the qualifying test: Wisma R&D ran 0.22-0.54 against TNB's recommended 0.6, that's a fat peak to shave. A modern mall at 0.86 is nearly flat and has little to give, so we target offices, innovation parks and mixed commercial, the SDP stock beyond the flagship malls."

## "Who pays and how do you make money?"

> "SaaS subscription per site, priced against a fraction of the verified saving, roughly RM1,071-1,165 per kW-year. The landlord's payback story is immediate because there is no capex line. Tenant billing and EECA reporting are retention hooks, the demand saving is the acquisition hook."

## "EECA, is that really a selling point?"

> "It is a forcing function. Above 21,600 GJ in any 12 months a consumer must appoint a Registered Energy Manager within 3 months, implement an EnMS within a year, and file annual reports and 5-yearly audits. The REM must exist anyway; WattWise is their instrumentation, not their replacement. Saying that out loud defuses the biggest objection in the room."

## "Data centres? AI? The theme says innovation."

> "The grid angle is real, data centres take 9.28% of national electricity and TNB is asking for exactly what we produce: flatter peaks and self-consuming solar. But our ML is modest and honest, an LSTM forecaster and an RL scheduler with published benchmarks. We are not claiming an AI moonshot; we are claiming a working operating layer for assets that exist today."

## Vocabulary landmines (never say these)

- "TNB fines / penalties" -> it is a **charge**
- "Illegal solar export" -> it is a **prohibited export under SELCO** (compliance condition)
- "Routes power" -> software **schedules loads**, it does not route electricity
- "Tripled" (unqualified) -> **close to tripled on general supply**; ToU is 2.15x
- "RM0 hardware" -> **no new major equipment**
- "Our model achieves 6.75% nRMSE" -> **models of this type on Malaysian rooftop data achieve...** (until the prototype runs)
- Any number from the DO-NOT-USE list in 03-FACTS-AND-SOURCES.md
