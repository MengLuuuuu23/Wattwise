# WattWise - FAQ (from the questions actually asked)

The real questions from building this pitch, answered the way we settled them. These are the ones teammates will ask too.

## "Isn't the whole point of solar panels to use stored energy from off-peak hours?"

Almost, and the gap in that sentence is the whole pitch. **Solar panels don't store anything.** A panel is a generator, not a battery: it makes electricity the instant sunlight hits it and stops when the sun doesn't. Zero at night, weak at 8am, strongest at noon. There is no "collect now, use later" unless you physically add a battery, which is the expensive hardware we avoid. The cruel timing problem in Malaysia: the billed peak is 8:30-10:30am when solar barely works, and solar's best hours are midday when the surplus can't even be exported. The industry's traditional answer is to put a battery in the middle. WattWise flips the direction: instead of moving the electricity to the load (battery), it moves the load to the electricity (scheduling). Store the sun as cold air and pumped water at noon, coast on it at breakfast.

## "If surplus energy could just be sold back to the grid, why would anyone need WattWise?"

Because "selling back" is either prohibited, capped, or underpaid for exactly our customer, and even in the best case it doesn't touch the demand charge. Four prongs:

1. **SDP's commercial solar is on SELCO, where export is prohibited outright.** The TNB/ST guideline (GP/ST/No.51/2024) is explicit: energy from a self-consumption installation "shall be strictly for the self-consumption of the owner or occupier" and "no energy produced... is allowed to be supplied to and for the use of any other person". The schemes are mutually exclusive: a premise on NEM/FiT cannot also register a separate SELCO installation. So for the buildings we target, there is no sell-back to fall back on. ([TNB SELCO guideline PDF](https://www.mytnb.com.my/-/media/Project/TNB/myTNBportal/Renewable-Energy/SELCO/SELCO-GUIDELINE-NEW_250303_103609.pdf), [SEDA SELCO page](https://www.seda.gov.my/reportal/self-consumption/))
2. **Even under NEM (the scheme where export exists), export is an offset at a reduced rate, not a sale at retail.** A kWh pushed to the grid earns you far less than a kWh you consume yourself is worth (~45.40 sen/kWh base retail). So self-consuming surplus, by soaking it into pre-cooling and pumped water, is the *highest-value* use of every surplus kWh. Exporting is the second-best use of the same electron; WattWise monetizes it at full retail value instead.
3. **NEM has caps our customer can't always fit under.** Commercial NEM 2024 limits installed capacity to 85% of Maximum Demand, and quota is allocated in windows, not guaranteed. ([SEDA NEM 2024 guideline](https://www.seda.gov.my/reportal/wp-content/uploads/2024/12/NEM-2024_Rakyat_2211.pdf))
4. **The killer: selling surplus does nothing for the demand charge.** Export credit lands on the energy line. The MD charge is set by the 8:30-10:30am peak when solar is weak, so a building could sell every surplus midday kWh and still pay the full demand charge. WattWise is the only one of the two options that attacks both lines.

So the FAQ-grade one-liner: **even if sell-back were possible, it's the worse deal: underpaid per kWh and useless against the charge that actually hurts.** Internal use at retail value plus peak compression beats export every time.

## "Won't pre-cooling affect comfort?"

No, because comfort is a range (24-26C), not a point. Pre-cool to the bottom of the band early, drift gently to the top during the peak; concrete warms slowly so the drift is about a degree per couple of hours, which people barely feel. Humidity tightens the band's top in the tropics, so comfort is a hard constraint in the scheduler with penalties, and the honest savings claim stays at ~10%. Proof the physics works: during a mall blackout the building stays cool for an hour or more on thermal mass alone. (Full answer in 05-QA-CRIB-SHEET.md.)

## "What does 'defer demand' actually mean?"

Moving a load's *timing*, not reducing its energy. The demand charge punishes your worst half hour of power draw (kW), not total consumption (kWh). So a chiller that would start at 8:30am starts at 6:30am instead: same kWh, colder building, and during the 8:30-10:30 window the chiller coasts. The work still happens; it just doesn't pile into the half hour TNB bills on. Constraint: only flexible loads can move (pre-cooling, pumps, thermal mass). Lighting when a shop is open cannot. That's why the pitch scopes to landlord common-area plant.

## "Wait, whose meter does the CREAM demand charge land on?"

The **receiving commercial building's** incoming TNB meter, the Local Green Consumer (in the Elmina pilot, the Innovation Park). Homeowners' meters never see CREAM power (they lease rooftops, export through a generation meter). The LEGA's export side has no demand charge. One nuance: CREAM energy is wheeled through the grid, so it offsets the energy line; whether it touches the MD register is unverified, so say "timing mismatch", not "billing mechanics".

## "Is WattWise 'embedded in smart meters' / 'passive'?"

No and no. It **connects to** existing meters and building controls (reads data, sends BMS commands). Nothing can be embedded in sealed utility meters, and "passive" would make it a dashboard, which is a different (existing) product. Accurate line: "an invisible software layer that connects to existing meters and building controls", invisible to occupants, active on the loads, and honestly assuming the building has networked metering or a BMS (older buildings may need a small gateway, hence "no new major equipment" rather than "RM0").

## "Is the worked example realistic?"

Mostly, with three adjustments we made. The arithmetic is exact (RM97.06/kW x 12 = RM1,164.72 per kW-year; 100 kW = RM116,472/yr). The 10% shave is the defensible software-only band, not hype, and load factor 0.22-0.54 buildings have fat peaks to shave (flat malls at 0.86 don't). We cut surplus solar from 100 to 30-40 kWh/day average (surplus concentrates on weekends/low-occupancy days), quote the battery as "cells alone, 2-3x installed" (which strengthens the comparison), and say "no new major equipment" instead of RM0. Also: pre-cooling can slightly *increase* total kWh while cutting *cost*, so never claim total energy drops.

## "Does the forecasting accuracy hold up?"

The design is grounded: LSTM on the four features Malaysian studies correlate with PV output (irradiance, module temp, ambient temp, wind) plus site history. Published Malaysian benchmarks: [nRMSE 6.75% / R2 0.957 at 30-min ahead (rooftop)](https://journal.uthm.edu.my/index.php/ijie/article/download/17144/7422/103525), [R2 0.92 day-ahead (8 MWp farm)](https://exa.ai/library/publication/5sjhrt2fcfs). Honest posture: these are *models of this type on Malaysian data*, not our measured result, until the prototype runs. Why good enough: 7% error on 600 kWp is ~40 kW, inside the margin of a 100 kW shave target; the scheduler needs "when and roughly how much", not a perfect curve.

## "Does the whole concept even fit this hackathon?"

Yes, better than expected. The brief (SDP University Hackathon 2026, "Township of Tomorrow") puts **Planet, item 3: Energy efficiency** on its list, and promises winners are reviewed for real pilots. A no-capex software layer is one of the few student ideas that could pilot in months, because the assets already exist (CREAM, GSPARX, malls, EECA exposure). Two gaps we fixed: a residents/township framing slide (people, businesses, planet language), and pitching it as a township operating layer, not a mall bill-cutter.

## "Solar prediction vs energy scheduler, what's the difference?"

WATTWISE-1 **predicts** (solar output + building demand, 30 min to 3 h ahead). WATTWISE-2 **acts** (stages flexible loads based on the forecast). The lock: you cannot preempt a peak you don't predict, which is why the forecasting model covers demand as well as solar, not just generation.

## "What's the difference between the detailed and simplified flowcharts?"

Audience. The detailed one (township energy in, the four-step loop, value out, with tariff numbers and protocol-level detail) is for judges and Q&A. The simple one ("the building that follows the sun": sunlight becomes power, WattWise picks the moment, everyone saves; 6am cool early / 12pm soak sunshine / 3pm coast through the peak; "NO GADGETS") is for everyone else: residents, tenants, non-technical mentors. In a live pitch: show the simple one while talking, keep the detailed one for the appendix.

## "But then the reduction is kinda small for a developer, huh?"

It looks small if you compare it to the wrong thing. Three reframes:

1. **The 21% (717->565 kW) is WattWise vs a battery building.** Against doing nothing, the modelled cut is bigger: unmanaged peak ~950 kW -> 565 kW, roughly 40%. We quote 10-15% publicly as the conservative claim; the 717->565 figure is literally our worst-case comparison, against the multi-million-ringgit hardware alternative.
2. **Property people think in asset value, not savings.** RM176k/year off the bill is RM176k straight onto net operating income, with nothing new bought. Capitalised at a typical ~5% cap rate, one building gains ~RM3.5 million in value. Across five malls plus commercial stock, that moves portfolio valuations, the language SDP leadership actually reports in. And the saving compounds with every tariff revision instead of depreciating like hardware.
3. **The bill was never the whole product.** The same subscription carries EECA compliance (energy manager tooling, audit trails, legally required reports), tenant green billing, and making the CREAM solar SDP already paid for actually usable. The RM176k is the acquisition hook; the rest is why they never cancel.

Honest ceiling, so we never oversell: this is an optimisation, not a rescue. SDP's revenue is billions; RM2-4M/year portfolio-wide is a rounding error on turnover. The line that survives that fact: **high-margin recurring income on assets that already exist, with zero capex, that also happens to be the compliance layer the law now requires.** Small money, but nearly free money, on every building they own, forever.

## "Why does the demand charge still exist after WattWise? (RM69,584 -> RM54,862)"

Because the charge isn't a punishment you can eliminate, it's payment for a real thing: **reserved capacity**. TNB must build and maintain enough generation, transmission and wires to serve each customer's single worst moment. A building spiking to 717 kW for one half hour forces TNB to hold 717 kW of capacity ready all year, even though the building averages a third of that. Grid-scale electricity can't be meaningfully stored, so that capacity sits ready whether it's used or not. The demand charge is rent on the chunk of the grid you reserve. Buffet rule: you're billed for your biggest mouthful, and as long as you keep eating, there's always a biggest mouthful.

WattWise shrinks the mouthful, it can't delete it. Flexible loads (cooling, pumps) moved out of the danger window still leave the building running: lights, lifts, tenants' equipment, servers. Those inflexible loads stack to a peak of their own, ~565 kW in the model, and that half hour now sets the bill. 717->565 is the shave; 565 is the floor an occupied building can't go below without batteries or turning things off. Stage phrasing: **we don't remove the demand charge, we compress it toward the building's inflexible floor.** The gap between old peak and floor, times RM97.06/kW/month, is the entire revenue stream.

## "If you were a professional, how would you rework WattWise to be more impactful?"

The move isn't a better scheduler, it's realising the scheduler was never the product, it was the **wedge**. The staircase:

1. **Wedge (demand charge).** Start small: cut each building's bill by shifting cooling to cheap hours. Pays for itself immediately, and every building we enter gives us the two things needed for later: **its data** and **control of its equipment**.
2. **Moat (LEGA operating layer).** CREAM made SDP the first Local Energy Generation Aggregator in the country. A LEGA has to match rooftop supply to local demand, manage LGC contracts, settle through TNB with Community Access Charges, and prove green attributes — and there is no software for any of that because the role didn't exist until last year. Regulation-mandated demand, zero incumbents, and SDP's competitors will become LEGAs too. Tanand can copy a scheduler; they can't copy "first into a regulatory niche". By step 1 we're already connected to every building, so running CREAM on top is natural for us and unnatural for anyone else.
3. **Market (flexibility revenue).** Once we coordinate hundreds of buildings' cooling, batteries, and solar at once, that portfolio is valuable to the grid itself. On a tight afternoon TNB would rather pay us to dial down a township for an hour than fire up an expensive backup plant (this is demand response / NEDA territory, exactly what grid operators said they want in the Eco-Business piece: "flexibility is just as important as capacity"). Same software, but now money comes *from* the grid, not just the buildings. A kW shaved is invisible; a township the grid can call on is policy-visible.

Beyond step 3, the long game: aggregate everything SDP already bought (Elmina Ridge home batteries, community energy storage, commercial plant, future EV chargers) into one township virtual power plant, and move upstream into designing solar/storage/plant sizing for the ~36,600 Elmina homes still unbuilt, because optimising capex at design beats optimising opex forever. And note the buyer changes too: not mall O&M (no budget, split incentive) but the entity that owns CREAM and the NETR commitments, which reports progress in exactly the language WattWise outputs.

One sentence: **start by saving buildings money, use that to become the operating system for the township's green energy, then sell the whole coordinated lump back to the grid as a giant virtual battery.** Each step only works because you climbed the previous one.

## "Does WattWise work as a selling point to SDP's property buyers?"

Weak as a direct selling point, real as a supporting one. What a buyer actually cares about: price, location, schools, appreciation, monthly costs. WattWise touches none of those — it's invisible software running on the *commercial* buildings, not inside the terrace house they're touring. A family choosing between Elmina and a competitor's township doesn't pay a premium because a mall 2 km away has a smarter chiller schedule. Anyone claiming it sells houses directly sounds naive.

But it works indirectly, three ways:

1. **It defends the service charge, which buyers DO feel.** PPK data (verified): mall operating costs outrun recoverable charges by 27%, and that gap pressures assessments across the whole township. WattWise keeping commercial operating costs down keeps that pressure off the service charges and quit rents residents actually pay monthly. "Your maintenance fees stay low because the township runs efficiently" is a real line, two steps removed from the product.
2. **It's proof of the smart-township promise, which is SDP's actual differentiator.** Every developer claims "township of tomorrow"; buyers have heard it. The difference between a slogan and a believable one is visible machinery: CREAM rooftops earning income, Elmina Ridge batteries, and now a layer that coordinates it all. WattWise is connective tissue that makes the existing green story credible rather than decorative. It sells the story's integrity, not a feature.
3. **CREAM income is the direct resident touchpoint, and WattWise protects it.** Homeowners leasing rooftops earn monthly income; WattWise keeps that energy usable so the programme stays healthy and expandable. "The township where your roof pays you" is a genuine hook, and it's already SDP's — WattWise keeps it sharp.

Deck framing: don't claim WattWise sells houses. Claim it *protects what SDP already sells houses on*: the township premium, the service-charge story, and the CREAM income programme. One-liner: **"buyers choose Elmina for the green township promise; WattWise is part of what keeps that promise true after the sales gallery closes."** If a judge asks the commercial question from the property side: WattWise isn't a marketing feature, it's what stops the green marketing becoming a liability when tariffs rise and EECA bites.

## "What happens if Schneider (or Tanand, or Solarvest) copies you?"

By the time they notice, you're not selling the scheduler anymore, you're selling the thing the scheduler grew into. The staircase is the answer: copying step 1 (a load-shifting scheduler) is trivial for Schneider, and we concede that openly. But step 2 (the LEGA/CREAM operating layer) is only copyable by someone already inside the buildings with the data and the control hooks, which is what step 1 bought. And step 3 (grid flexibility revenue) accrues to whoever aggregates the portfolio first. Big vendors copy products; they rarely do land-grabs into a months-old regulatory niche for one customer segment. The realistic copy threat is Tanand or GSPARX bolting this on, which is why the actual moat was always *being first on SDP's own data*, not the algorithm. Also worth saying out loud if asked: if Schneider does eventually ship a better version, SDP has still gained years of savings and a compliance layer in the meantime, and the winning move then is integration, not competition.

## "What's the ELI5 of the entire thing?"

A buffet that charges you for your single biggest mouthful of the month, not how much you ate. The sun works at lunch, the bill punishes breakfast, and WattWise reschedules the building so lunch pays for breakfast. Cold is the battery: the walls hold it like a thermos holds soup.
