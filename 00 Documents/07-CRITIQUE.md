# 07 — CRITIQUE: Red-Team Review of WattWise

> Isolated critic, fresh context, source-verified. Dispatched 11 Oct 2026, ~9 min run.
> Method: steelmanned all 9 claims, then attacked. Independently pulled the live hackathon
> site (judging criteria, prize structure, 1,000+ student field, Innovation Day December),
> TNB ToU structure, and ran arithmetic on load-factor ceilings, savings sensitivity,
> monthly-max capture probability, and the EECA threshold.
>
> Status of each point: PENDING (Sheri has not yet defended or revised). This file gets
> updated as rounds complete. Verdict scale: SURVIVED / REVISED / DROPPED.

---

## The 9 claims that were attacked

1. WattWise is a finalist-worthy hackathon entry (top-10 on rigor alone; top-3 with a working demo; champion possible with a pilot-friendly judge).
2. The problem is real, current, and money-shaped: tariff near-tripled, billed peak lands in the morning while solar peaks at midday, EECA is a live legal clock, SDP uniquely exposed.
3. The mechanism is proven engineering: pre-cooling and load staging are textbook DSM; NREL demonstrated ~20% peak cuts via RL on a real building.
4. The concept fits the brief precisely (Planet track energy-efficiency; effortless sustainability; one mechanism benefiting people, businesses, nature).
5. The economics are meaningful: ~RM176k/year per modelled building, ~RM3.5M asset-value gain at 5% cap rate.
6. The no-capex angle makes WattWise uniquely pilotable by Innovation Day.
7. Novelty is defensible as business-model innovation (forecast + scheduler + tenant billing + EECA at township scale).
8. Risks are manageable via scoping: "read-only pilot first, prove the forecast before touching a valve".
9. The one-liner is accurate and defensible.

---

## FATAL objections

### F1. The modelled shave violates the physics of the target building class
**Hits claims 1, 3, 5. Status: PENDING.**

- Software moves load in time; it cannot destroy it. Ceiling on the shave = `1 − load factor` (plus a bounded pre-08:00 dumping term limited by thermal mass and comfort, order 1–3 kWh/m²).
- Our own cited mall study (AIP 2019): mall chiller-circuit load factor **0.858 → hard ceiling ≈ 14.2%**.
- Even at TNB's recommended LF 0.6 the ceiling is 40% — i.e. our modelled 950→565 kW (**40.5%**) assumes essentially *perfect leveling plus* pre-08:00 dumping: the theoretical optimum, not a working controller's output.
- Our "conservative public estimate" of 10–15% sits at or above the hard ceiling for a flat mall.
- Benchmark triangulation: NREL real RL controller ~20%; our own model's battery case 24.5%; every independent number clusters near 20. Only WattWise-software claims 40.5 — and claims to *beat a battery*, which is impossible in general (a battery can do everything load-shifting does **plus** discharge below the consumption floor). Software > BESS on the same building means the BESS is mis-sized or the software number is inflated.
- **Honest re-scope (critic's arithmetic): 5–7% shave → RM54k–82k/year; asset-value gain ~RM1.1–1.6M, not RM3.5M.**
- The subscription (RM12–24k/yr) still clears comfortably at honest numbers → fatal to the stated *magnitude*, not to viability. But every deck number derived from 40.5% is dead on arrival with a technically literate judge.

### F2. The monthly-max ratchet makes the savings structurally fragile even at honest shave levels
**Hits claims 5, 2. Status: PENDING.**

- MD = single highest 30-min interval of the month, over ~840 charged intervals (14h × 2/half-hour × 30 days).
- A controller with **99.9% per-interval reliability still has ~57% chance of at least one exceedance per month**; at 99.99%, ~8%.
- One hot morning, one occupancy surge, one forecast miss — that month's MD and the marginal kW you were shaving are set by the miss.
- Expected savings must be discounted by controller reliability and tail weather.
- The R² 0.957 / nRMSE 6.75% benchmark is for **rooftop PV output, not building demand under closed-loop intervention**. MISSING: any published Malaysian benchmark for 30-min building-demand forecasting under active control.
- We cannot currently claim a validated forecast on the load we intend to control.

---

## STRONG objections

### S1. Split-incentive problem unaddressed; the payer is unverified
**Hits claims 5, 2. Status: PENDING.**

- In Malaysian malls, tenant electricity is commonly metered and recharged (or tenant-supplied); landlord MD exposure is often limited to common area + central plant, passed through service charges.
- If that holds at SDP malls: RM176k (or honest RM54–82k) accrues to tenants or dissolves into the service charge — **not SDP's P&L — while SDP pays our subscription**.
- The "asset value at 5% cap" line additionally requires savings to stick to the owner-billed line.
- MISSING: SDP mall lease/charging structure; which entity pays the MD line today. **The single most important unverified commercial fact in the deck, and it is not in our acknowledged-risk list.**

### S2. The pitch straddles two tariff structures and merges two different mechanisms
**Hits claims 2, 9. Status: PENDING.**

- **C1 general**: chargeable MD window 08:00–22:00, documented peaks 8:30–10:30am → MD is cut by pre-cooling *before 08:00*; midday solar absorption saves **energy charges (sen/kWh), not the morning MD**.
- **C2 ToU** (critic verified: peak 14:00–22:00 weekdays, off-peak MD uncharged): the morning-peak problem **literally does not exist**; midday pre-cooling for the 2pm peak is exactly right.
- "Absorb midday solar AND shift away from the morning peak" as one mechanism is half-true under each tariff.
- MISSING: which tariff category the pilot malls are on. The one-liner ("when power is cheap or free") inherits the blur. A TNB-literate judge catches it in Q&A.

### S3. The core is occupied ground in Malaysia today; novelty rests on the wrapper
**Hits claims 7, 1. Status: PENDING.**

- Tanand (Easi EMS) sells MD reduction in Malaysia now. Solarvest sells BESS-plus-MD-shaving claiming 20–65% cuts. GSPARX already owns the solar relationship with our target customer.
- The genuinely newer pieces — EECA reporting automation, CREAM/LEGA wheeled-solar coordination, township-scale tenant green billing — are **under-weighted** in the pitch relative to forecast+scheduler, the *least* novel component.
- Judging criterion #1 on the official site is "innovative... original thinking"; SDP judges know their existing vendor stack.

### S4. Theme fit is weaker than claimed
**Hits claims 4, 1. Status: PENDING.**

- Official Planet framing: "practical ways to encourage sustainable living and support environmental regeneration", "making sustainable living more effortless for **communities, residents and businesses**"; press adds solutions are expected to "combine **community-based approaches** with technology, data or AI".
- WattWise is a B2B plant-operations tool; residents never encounter it. "Invisible" is not a feature here — it is the *absence* of the resident/community dimension the brief foregrounds.
- Clears "businesses" and arguably the letter of an energy-efficiency item, but "fits the brief precisely" is an overclaim. Expect a theme-relevance scoring haircut against resident-facing entries.

### S5. "Uniquely exposed" is false as stated
**Hits claims 2, 5. Status: PENDING.**

- Any large Malaysian mall portfolio faces the same RP4 MD repricing, the same EECA clock (a 1,000 kW-MD mall at LF 0.86 consumes ~27,100 GJ/yr, comfortably over the 21,600 GJ threshold — cuts in our favour on problem-realism), the same physics.
- SDP's actual differentiation: CREAM first-mover status + the GSPARX relationship.
- Fix: drop "uniquely" or tie it explicitly to CREAM.

### S6. A read-only pilot proves a forecast dashboard, not value
**Hits claim 6. Status: PENDING.**

- MD falls only when loads actually move; read-only access yields **zero bill savings by construction**.
- "Uniquely pilotable by Innovation Day" demonstrates data-integration speed while the product's entire value stays locked behind the write-access problem we ourselves flag as the hard part.
- MISSING: any SDP commitment to grant meter data access to a student team at all — pilot consideration is the *prize*, not a default, per the official rules.

### S7. The binding risk is misidentified
**Hits claims 8, 1. Status: PENDING.**

- Official judging criteria explicitly include "the technical execution of your **prototype**." No prototype exists, 12 days before the proposal deadline, solo, against a 1,000+ student field (press-sourced).
- The near-term execution risk dwarfs the post-hackathon BMS write-access risk.
- MISSING: whether **solo entries are even permitted** — the site's FAQ speaks in teams. If teams are mandatory this is fatal to entry logistics, not just scoring. **CHECK IMMEDIATELY.**

---

## WEAK objections (real, manageable)

### W1. "Zero behaviour change / effortless" vs pre-cooling comfort drift
Pre-cooling is a *felt* comfort change (colder mornings, warmer late afternoons). Our reward function already prices comfort penalties → pitch-wording risk, not a design hole.

### W2. Closed-loop distribution shift
An LSTM trained on historical load predicts the no-intervention distribution; once the scheduler acts, training data is stale (off-policy problem). Bites the deep-RL roadmap, not rule-based v0. MISSING: a twin-validation plan for the counterfactual.

### W3. "Batteries cost millions"
Directionally true at commercial scale; no Malaysian list pricing verified. Critic concedes the comparison line survives. **Status: CONCEDED by critic.**

---

## Conceded permanently by the critic

- The **mechanism class** (claim 3) is proven engineering.
- The **problem is real, current, money-shaped** in its C1 form (claim 2, minus "uniquely").
- The **EECA arithmetic** for large malls checks out.
- The **one-liner survives** with the tariff-blur caveat (claim 9, mostly).

---

## Verdict on claim 1 (finalist-worthy)

**Survives only in weakened form.**

In favour (verifiably true):
- Sourcing rigor is a real differentiator against a typical student field; the problem is quantified in RM/kW against a public-record tariff shock.
- Finals 14 Nov + Innovation Day December give a working demo ~5 extra weeks of runway after the 23 Oct proposal.

Against (verifiably true):
- Judging criteria score "technical execution of your prototype" — there is no prototype.
- The field is 1,000+ students, not a cozy cohort.
- The technical core is sold in-market today by named Malaysian competitors.
- The brief foregrounds residents and communities, where WattWise is silent.
- Top-10 "on rigor alone" is plausible but **not the near-certainty we implied**: rigor buys credibility with technical judges, and the numbers currently on the deck (F1) would not survive a competent engineer's first pass — converting the rigor advantage into a **rigor liability** the moment someone recomputes the load-factor ceiling.

**As pitched today: credible semi-finalist, non-credible champion.**

Top-3 becomes achievable only if, before 23 Oct:
1. A running demo (even simulated data through the real pipeline).
2. Economics re-scoped to **5–7% shave / RM54–82k per building**, RM3.5M line retired or restated as ~RM1.1–1.6M.
3. An explicit tariff-category commitment (**C1 vs C2**) with the mechanism matched to it.

Champion-tier additionally requires the **community dimension** promoted from footnote to headline — the CREAM wheeled-solar + tenant green billing angle is the piece that actually speaks the brief's language.

---

## Action items triggered by this review (not part of critic output)

- [ ] **URGENT: check whether solo entries are permitted** (official rules/FAQ). If teams mandatory → recruit teammates NOW.
- [ ] Verify who pays the MD line at SDP malls (lease/charging structure) — biggest unlisted commercial risk (S1).
- [ ] Re-run the deck economics at 5–7% shave; retire RM3.5M or restate (F1).
- [ ] Commit to C1 or C2 for the pilot sites; align the mechanism story and the one-liner (S2).
- [ ] Promote CREAM/tenant-billing community angle from footnote to headline (S4, and champion path).
- [ ] Build the demo: synthetic 30-min data through the real pipeline (S7, F1 credibility repair).
- [ ] Add reliability/tail-weather discount language to any savings claim (F2).
