# WattWise - Facts and Sources

Every number the deck claims, with status. Two rules: **verified** means we opened the source this cycle; **illustrative** means it is model output and must be labelled as such on any slide.

## Tariff (TNB RP4, effective 1 July 2025, in force through 2026)

| Claim | Value | Status | Source |
|---|---|---|---|
| MD = highest 30-min interval, kWh x2 | - | Verified | [TNB Tariff Booklet (PDF)](https://www.tnb.com.my/assets/files/Tariff_booklet.pdf); [TNB Maximum Demand page](https://www.tnb.com.my/commercial-industrial/maximum-demand); [SEDA NEM 2024 guidelines (PDF)](https://www.seda.gov.my/reportal/wp-content/uploads/2024/12/NEM-2024_Rakyat_2211.pdf) |
| MV general demand charge | RM89.27/kW/mo (C1: 29.43 capacity + 59.84 network) | Verified | [TNB tariff via PlusXnergy guide (updated Aug 2026)](https://plusxnergy.com/july-2025-tnb-tariff-update-what-malaysian-businesses-need-to-know); [aq.energy BESS guide](https://aq.energy/blog/bess-commercial-industrial-malaysia); [Edge Malaysia](https://theedgemalaysia.com/content/advertise/evcs-zero-capex-bess-programme-gamechanger-for-commercials--industrials) |
| MV ToU demand charge | RM97.06/kW/mo (C2: 30.19 + 66.87) | Verified | same |
| Old charges | C1 RM30.30, C2 RM45.10 | Verified | [Energies MD-shaving review](https://exa.ai/library/publication/lfctjk6cvhm); [IET Wisma R&D paper](https://doi.org/10.1049/cp.2018.1305) |
| Increase multiples | C1 2.95x, C2 2.15x ("close to tripled" only for general) | Verified, derived | same |
| Per kW-year saved | RM1,071-1,165 | Verified, derived | arithmetic |
| Energy rate C1 | RM0.2983/kWh | Verified | [PlusXnergy guide](https://plusxnergy.com/july-2025-tnb-tariff-update-what-malaysian-businesses-need-to-know) |

## When the peak lands

| Claim | Value | Status | Source |
|---|---|---|---|
| Commercial MD captured 8:30-10:30am | - | Verified | [Energies 2019, 12(18), 3531 - MDRed paper](https://www.mdpi.com/1996-1073/12/18/3531) |
| C1 MD 1,290 kW at 9:00am, RM39,087 demand / RM129,330 energy | Nov 2015 case | Verified | [Energies MD-shaving review](https://exa.ai/library/publication/lfctjk6cvhm) |
| Peak "often occurs early in the morning... PV slowly increased" | quote | Verified | [MDRed paper](https://www.mdpi.com/1996-1073/12/18/3531) |
| Solar cuts kWh but "often has little effect on MD (kW) charges" | quote | Verified | MDRed paper |
| ToU peak window (non-domestic) | 2pm-10pm weekdays per some sources; MD measurement window 8am-10pm per MDRed paper | **CONTESTED - verify on [mytnb.com.my/tariff](https://www.mytnb.com.my/tariff) before use** | [aq.energy](https://aq.energy/blog/bess-commercial-industrial-malaysia) vs [MDRed](https://www.mdpi.com/1996-1073/12/18/3531) |
| MD not charged during off-peak (22:00-08:00) for peak/off-peak tariffs | - | Verified | [TNB Tariff Booklet (PDF)](https://www.tnb.com.my/assets/files/Tariff_booklet.pdf) |

## Measured building performance

| Claim | Value | Status | Source |
|---|---|---|---|
| Wisma R&D UM: MD 628-1,001 kW vs average 220-340 kW over 3 years | load factor 0.22-0.54, below TNB's 0.6 | Verified | [IET 2018, doi:10.1049/cp.2018.1305](https://doi.org/10.1049/cp.2018.1305) |
| Large mall: chiller plant 26.1% of building energy, 7,158 MWh/yr, BEI 459.89 kWh/m2/yr | - | Verified | [AIP Conf Proc 2187, 020042 (2019), doi:10.1063/1.5138297](https://doi.org/10.1063/1.5138297) |
| Same mall: load factor 85.8% | flat load, little to shave | Verified | same |
| Cooling share: 42% across 12 commercial sub-sectors; 49% ACMV in offices | - | Verified | [ERIA technical guidelines ch.2 (PDF)](https://www.eria.org/uploads/media/Research-Project-Report/2021-14-Technical-Guideline-Energy-Efficiency-Commercial-Buildings/8_ch.2-Fundamentals.pdf) |
| Cooling share range across studies | 26-58% | Verified | [AIP 2187](https://doi.org/10.1063/1.5138297); [ERIA ch.2](https://www.eria.org/uploads/media/Research-Project-Report/2021-14-Technical-Guideline-Energy-Efficiency-Commercial-Buildings/8_ch.2-Fundamentals.pdf); IEN Consultants (Setia City Mall) 45-50%; Rismanchi (UM) 57%; [AIP 1.4960941](https://doi.org/10.1063/1.4960941) 58% |
| GCPV commercial rooftop: 232.5 kWp, PR 85.4%, CUF 14.85%, 301.5 MWh in 2019 | 5-min data | Verified | [Renewable Energy 2021, Monash Malaysia](https://www.sciencedirect.com/science/article/abs/pii/S0960148121002871) |

## Solar forecasting (WATTWISE-1 benchmarks)

| Claim | Value | Status | Source |
|---|---|---|---|
| LSTM rooftop PV 30-min ahead | nRMSE 6.75%, R2 0.957 (vs SVR 7.28%) | Verified | [IJIE 17(2) 2025, Penang, 22,513 intervals](https://journal.uthm.edu.my/index.php/ijie/article/download/17144/7422/103525) |
| Four input features (GHI, module temp, ambient temp, wind) PCC 0.51-0.96 | - | Verified | same |
| LSTM + MET weather, 8 MWp Ayer Keroh | R2 0.92-0.94 | Verified | [Malacca case study](https://exa.ai/library/publication/5sjhrt2fcfs) |
| Sliding-window LSTM, 25 MWac Pasir Gudang | up to 30.7% MAE reduction | Verified | [RAST 2025](https://ph01.tci-thaijo.org/index.php/RAST/article/view/263014) |

## Scheduler (WATTWISE-2 benchmarks)

| Claim | Value | Status | Source |
|---|---|---|---|
| Deep-RL on real 40-floor NYC building, 4 chillers | 20% peak cut, 20% bill cut, within 10% of MPC; learned pre-cooling by itself | Verified | [NREL/DOE BTO peer review 2023 poster (PDF)](https://www.energy.gov/sites/default/files/2023-05/bto-peer-2023-andreybernstein-modrlc.pdf) |
| DQN multi-zone HVAC | 23% cost reduction, learned pre-heating | Verified | [OSTI: Intelligent HVAC Load Management with Deep RL](https://www.osti.gov/pages/servlets/purl/1866667) |
| Solarvest BESS marketing claim | 20-65% MD reduction (with batteries) | Verified | [solarvest.com BESS page](https://solarvest.com/battery-energy-storage-system-malaysia) |

## Regulation

| Claim | Value | Status | Source |
|---|---|---|---|
| EECA 2024 (Act 861) in force 1 Jan 2025 | - | Verified | [ST EECA page](https://www.st.gov.my/stakeholders/energy-efficiency/energy-efficiency-and-conservation-act-eeca-2024) |
| Threshold: 21,600 GJ in any 12 consecutive months | - | Verified | [P.U.(A) 466/2024 Regulations (PDF)](https://www.st.gov.my/sites/default/files/2026-02/PUA466_2024-UNUU-%28ENG%29.pdf), reg. 3 |
| Duties: REM within 3 months of notice; EnMS within 1 year; annual EE&C reports; audit within 1 year then every 5 years | - | Verified | [ST Energy Consumer page](https://www.st.gov.my/stakeholders/energy-efficiency/energy-efficiency-and-conservation-act-eeca-2024/energy-consumer); gazette |
| Fine for practising unregistered as REM/REA | up to RM20,000 | Verified | [Act 861 (PDF)](https://www.st.gov.my/sites/default/files/2026-04/Energy-Efficiency-and-Conservation-Act-2024---Act-861.pdf) s.25(3) |
| Fine for missing audit/compliance | RM50,000 | **UNVERIFIED - do not quote until checked** | - |

## CREAM / SDP

| Claim | Value | Status | Source |
|---|---|---|---|
| SDP first LEGA under CREAM (framework Mar 2025), announced 28 Apr 2025 | - | Verified | [SDP press release](https://www.simedarbyproperty.com/press-releases/sime-darby-property-leads-nations-first-community-solar-rollout-under-netr-tnb); [The Edge](https://theedgemalaysia.com/node/753254); [EdgeProp](https://api.edgeprop.my/content/1912387/sime-darby-property-leads-nation%E2%80%99s-first-community-solar-rollout-under-netr-tnb) |
| Pilot launched 26 Sep 2025 at City of Elmina, officiated by DPM/PETRA minister | - | Verified | [SDP press release](https://www.simedarbyproperty.com/press-releases/sime-darby-property-launches-nations-first-residential-solar-project-under-netr); [SDP Q3 FY2025 results (PDF)](https://www.simedarbyproperty.com/sites/default/files/2025-11/[ANALYST]%20Q3%20FY2025%20Financial%20Results%20Briefings.pdf) |
| Wheeled via TNB grid, 5 km radius, LGC = Elmina Innovation Park | - | Verified | [SDP Sep 2025 release](https://www.simedarbyproperty.com/press-releases/sime-darby-property-launches-nations-first-residential-solar-project-under-netr); [ASEAN Energy CREAM policy insight (PDF)](https://aseanenergy.org/index.php/publications/policy-insight-malaysia-guideline-on-corporate-renewable-energy-aggregation-mechanism-cream/download) (Community Access Charge under NEDA) |
| GSPARX JV July 2024 (rooftop solar across SDP assets) | - | Verified | [SDP releases](https://www.simedarbyproperty.com/press-releases/sime-darby-property-implements-solar-solutions-its-township-developments) |
| SDP first developer in Malaysia with expandable BESS in homes (Elmina Ridge, Nov 2024, 122 units, GDV RM201.7m); testing repurposed EV batteries to cut BESS cost ~40%; first Community Energy Storage System at Elmina (Sep 2025) - all residential/community scale, none commercial MD shaving | - | Verified | [SDP press release](https://simedarbyproperty.com/press-releases/sime-darby-property-leads-way-malaysias-first-solar-powered-homes); [The Edge](https://theedgemalaysia.com/node/734558) |
| SDP: 40% Scope 1+2 cut by 2030, net zero 2050 | - | Verified | SDP releases |
| SDP: 5 malls, RM1.5bn investment portfolio (Dec 2024) | - | Verified | [simedarbyproperty.com](https://www.simedarbyproperty.com); Bursa filing 26 Feb 2025 |
| KL East Mall: 402,206 sq ft NLA, 170+ retailers, 1,300 bays | - | Verified | [simedarbyproperty.com](https://www.simedarbyproperty.com) |
| Indicative KL East Mall consumption ~17 GWh/yr at measured BEI | derived (2.9x EECA trigger) | **Illustrative - label the derivation** | our arithmetic on [AIP 2187](https://doi.org/10.1063/1.5138297) BEI |

## Market context

| Claim | Value | Status | Source |
|---|---|---|---|
| Data centres 9.28% of national electricity (2026) | - | Verified | [Eco-Business panel report](https://www.eco-business.com/news/malaysias-power-grid-strains-under-data-centre-boom-and-renewables-growth/) (TNB/GSO/Huawei) |
| National peak 20.75 GW (May 2025), demand growth 3.5-4.5% | - | Verified | The Malaysian Reserve |
| PPK: RM5m/yr added cost for 500k sq ft mall; cost-recovery gap 27% vs 13.4% (2022) | - | Verified | PPK via The Star/FMT/The Edge |
| Battery cells US$110-130/kWh, ~$80-90 by 2030; solar+BESS costs fell 70-80% in a decade | - | Verified | [The Edge: Solarvest VP Jack Tan](https://theedgemalaysia.com/node/806881) |

## Battery comparison (for the benefits slide)

| Claim | Value | Status |
|---|---|---|
| 500 kWh BESS cells | US$55-65k | Verified arithmetic on [$/kWh from The Edge](https://theedgemalaysia.com/node/806881) |
| Installed system cost | typically 2-3x cells | Verified (industry standard) |
| Surplus solar redirected | 30-40 kWh/day average (100 kWh/day only on low-occupancy days) | Illustrative, honest band |
| Worked example: 1,000 kW site, 10% shave | RM116,472/yr | Illustrative, derived |
| WattWise hardware | "no new major equipment" (NOT "RM0": older buildings may need a small data gateway) | Verified with caveat |

## DO-NOT-USE list (known wrong or unverified)

1. **RM186.33/kW** - double-counts capacity + network and mixes C1/C2 rates. Circulating on some solar blogs; [PlusXnergy](https://plusxnergy.com/july-2025-tnb-tariff-update-what-malaysian-businesses-need-to-know), [aq.energy](https://aq.energy/blog/bess-commercial-industrial-malaysia) and [Edge Malaysia](https://theedgemalaysia.com/content/advertise/evcs-zero-capex-bess-programme-gamechanger-for-commercials--industrials) all contradict it.
2. **51% chiller share for malls** - came from a secondary blog; the primary paper says 26.1%. Use the 26-58% range with per-study labels.
3. **RM50,000 EECA fine** - unverified; the verified fine (RM20,000) is for unregistered practice, not missed audits.
4. **"Tripled" for both tariffs** - only true for general supply (2.95x). ToU is 2.15x. Say "close to tripled" or scope it.
5. **"TNB fines/penalties"** - vocabulary error. It is a charge, not a fine. A utility judge will correct this out loud.
6. **"Embedded in smart meters" / "passive layer"** - both architecturally wrong (see QA crib sheet).
7. **Any exact load curve presented as measured** - ours is modelled until real interval data arrives. Label every curve "illustrative".
8. **"Exported solar is illegal"** - loose. Under SELCO it is a compliance condition breach (prohibited export), not a crime.
9. **RM0 hardware** - overclaim; older buildings may need a cheap gateway. Say "no new major equipment".
