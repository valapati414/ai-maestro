# Variable Taxonomy

*The complete list of variables that determine future revenue and profit for an enterprise
data-protection vendor, organized by family. For each: the symbol used in `engine/dpforecast.py`, its
measure type, where it is observable, where it enters the model, and an anchor value with its source.*

**Measure types** — these never mix (see the Iron Rules in SKILL.md):
`count` · `rate` (per period) · `ratio` (dimensionless) · `acv`/`arr` (annualized $) · `tcv` (contract $) ·
`billings` ($ invoiced) · `revenue` ($ recognized) · `cash` ($) · `days`

**Observability tiers:** **D** = disclosed by the vendor · **F** = derivable from filings ·
**I** = internal only (order flow) · **X** = external/alternative data · **A** = assumption, must be
labelled as such.

**How to use this file.** Walk it top to bottom and classify every variable as known, estimable, or
unknown for your specific vendor and situation. Do not silently drop the unknowns — they go in the
assumption register with an explicit range, and the width of that range is what your forecast interval
is made of.

---

## A. Installed base — the recurring engine

This family produces most of next year's revenue and almost none of its uncertainty. Get it exactly
right and stop refining it.

| Variable | Symbol | Type | Tier | Enters | Anchor / note |
|---|---|---|---|---|---|
| Opening ARR by stream (term license, SaaS, support, consumption) | `arr_open[s]` | arr | D | Waterfall start | Commvault total ARR $1,121.6M, SaaS $400.2M at 3/31/26 |
| Gross retention rate (GRR) | `grr` | ratio | A | Renewal survival | **Not disclosed by any public vendor.** Only datapoint: Veeam ~95% enterprise GRR (CEO interview). Model 90–93% for enterprise data protection |
| Net revenue retention (NRR) | `nrr` | ratio | D | Expansion + churn | Commvault SaaS NRR 122% (3/31/26); Rubrik ~120% trailing-4-qtr average. Definitions differ — read them |
| Expansion rate (NRR − GRR) | `expansion` | ratio | F | Waterfall | Derived. The discretionary half of NRR; goes to zero first in a downturn |
| Downsell/contraction rate | `contraction` | ratio | I | Waterfall | Distinct from churn: a customer who stays but shrinks |
| Renewal calendar by quarter (expiring ACV) | `expiring[q]` | acv | I | Renewal book | The single most forecastable quantity you have, if you have it |
| Auto-renew share and notice periods | `p_autorenew`, `notice_days` | ratio, days | I | Renewal probability | Auto-renew contracts have materially different `p_renew` |
| Contract tenure / cohort age | `tenure` | days | I | Renewal probability | Renewal probability rises with tenure; first renewal is the risk point |
| Renewal uplift at renewal | `uplift` | ratio | I/A | Renewal ACV | Price escalators plus true-up. See lever #2 in profit-levers.md |
| Co-term share | `p_coterm` | ratio | I | Partial-period bookings | Co-termed add-ons make ACV added ≠ TCV/term |
| Consumption/commit burn-down | `burn` | ratio | I | Consumption revenue | Under-consuming accounts have no upside but real downgrade risk |
| Customer counts and large-customer cohorts | `n_cust[tier]` | count | D | Cross-check | Rubrik: 2,946 customers ≥$100K ARR at 4/30/26 (+24%) |
| Perpetual-license support base (decaying) | `arr_perp_support` | arr | F | Runoff | Commvault perpetual license revenue −22% in FY26; support attached to it is in Total ARR |

**Derived diagnostics:** half-life of the base = `ln(0.5)/ln(GRR)` (GRR 90% → 6.6 years);
steady-state ARR with constant new logos = `NewLogo / (1 − NRR)` when NRR < 1, unbounded otherwise.

---

## B. New business acquisition — where the uncertainty lives

| Variable | Symbol | Type | Tier | Enters | Anchor / note |
|---|---|---|---|---|---|
| New-logo ARR added per period | `new_logo_arr` | arr | F | Waterfall | Derived: Δ ARR − (expansion − churn) |
| Quota-carrying rep count | `n_reps` | count | I/X | Capacity model | **Not disclosed by any vendor.** Proxy with job postings (documented predictive value, see demand-drivers §C) |
| Productivity per ramped rep | `prod_rep` | arr | I/A | Capacity model | ARR per employee is disclosable: Commvault $340.4K, Rubrik $385.1K (matched dates); rep-level is not |
| Ramp time to full productivity | `ramp_months` | days | I/A | Capacity model | Halves the in-year contribution of a hire; 6-month ramp ⇒ ~0.5 FTE-year in year 1 |
| Rep attrition | `attrition` | rate | I/X | Capacity model | Gross hiring ≠ net capacity |
| Pipeline coverage ratio | `coverage` | ratio | I | Conversion check | **Do not assume 3×.** Required coverage = 1/`c̄`. Ebsta/Pavilion 2025: 19% average B2B win rate ⇒ ~5.3× |
| Dollar-weighted win rate by stage | `p_win[stage]` | ratio | I | Deal simulation | Recalibrate; CRM stage defaults are policy, not estimates |
| In-quarter close probability | `p_inq` | ratio | I | Deal simulation | From the hazard model, not the asserted close date |
| Amount realization multiplier | `m` | ratio | I | Deal simulation | Realized ÷ CRM amount; typically <1. Larkin: pulled deals discounted ~6 pts more |
| Slip / push rate | `p_slip` | ratio | I | Timing | Count close-date changes to a later date |
| Sales cycle length by type | `cycle_days` | days | I | Cohort conversion | Ebsta: expansion ~52 days vs new logo ~91 |
| Deal-size distribution (heavy-tailed) | `A_i` | tcv | I | Deal simulation | Stratify; large deals convert lower and slip more |
| Deal-outcome correlation | `rho` | ratio | A | Deal simulation | **No published estimate for B2B pipelines.** Fit from historical over-dispersion. Effect size depends on the *effective* deal count `(Σa)²/Σa²`: latent ρ=0.20 inflates the sd ~1.9× at 23 effective deals and ~5× at 200. Latent ρ ≠ indicator ρ (0.20 → 0.119 at p=0.30) |
| Unmodeled tail (created-and-closed in-quarter) | `U` | acv | I | Deal simulation | Can be ~30% of a quarter. Model explicitly, never as a fudge factor |
| Day-of-quarter pace curve | `g(t)` | ratio | I | Nowcasting | Larkin: 67% of deals on the final day (one vendor, upper bound) |
| Judgmental realization by forecast category | `r[c]` | ratio | I | Judgmental forecast | Fit from forecast-lock snapshots; shrink for low-N reps |
| Trial / free-edition starts and conversion | `trials`, `p_conv` | count, ratio | I/X | Run-rate funnel | Veeam Community Edition capped at 10 workloads; **no conversion data published** |
| Deal registrations submitted | `dealregs` | count | I | Leading indicator | Weeks-to-months lead; hard to game |
| Distributor POS / sell-through | `pos` | billings | I | Leading indicator | Rising sell-in/POS ratio with rising weeks-of-supply = channel loading |

---

## C. Pricing and packaging

| Variable | Symbol | Type | Tier | Enters | Anchor / note |
|---|---|---|---|---|---|
| List price change | `dp_list` | ratio | A | Revenue, margin | Highest-ROI revenue lever. At 6.3% GAAP op margin, +1% price = +15.9% of operating profit |
| Average realized discount | `d` | ratio | I | Net price | **[ASSUMPTION]** 25–40% in two-tier distribution; not disclosed. 1 pt off a 30% discount = +1.43% net price |
| Deal-registration discount | `d_dealreg` | ratio | X | Channel economics | Veeam 2025: 25% for Veeam Data Cloud, 15% other products |
| Volume-incentive rebate / VIR accrual | `r_rebate` | ratio | I | Net revenue | ASC 606 variable consideration; tier crossings cluster in Q4 |
| Price metric (per-VM, per-workload, per-TB, per-seat) | — | — | D | Revenue↔capacity link | A shift from per-TB to per-workload **decouples revenue from data growth entirely** |
| Attach rate of add-on modules | `attach[m]` | ratio | I | Expansion | Cheapest growth: expansion CAC ratio ~$1.00 vs $1.63 new-name |
| Price elasticity of demand | `eps` | ratio | A | Volume response | **No published estimate for this category.** Breakeven volume loss at 81.2% GM is 1.22% per 1% price rise |

---

## D. Contract structure and revenue recognition

The family that converts identical demand into different reported revenue. Get this wrong and no amount
of demand modeling helps.

| Variable | Symbol | Type | Tier | Enters | Anchor / note |
|---|---|---|---|---|---|
| Term length mix (1 / 3 / 5 year) | `mix_term[n]` | ratio | D (qualitative) | 606 bridge | Rubrik: majority of new business 3-year, renewing 1-year. Commvault: 1–3 years |
| Upfront-license share of a term deal | `share_upfront` | ratio | F | 606 bridge | Residual approach: `License = n·P − n·s`. A 30-pt duration-mix shift moves license revenue −25% at flat ARR |
| Standalone selling price of support | `ssp_support` | acv | A | 606 allocation | Commvault uses the residual approach with observable support renewal rates |
| Performance-obligation determination (distinct vs bundled) | — | — | D | Recognition pattern | **Rubrik's RSC is a single PO ⇒ fully ratable. Commvault's term license is point-in-time.** Never model them the same way |
| Billing schedule mix (annual vs prepaid multi-year) | `mix_billing` | ratio | D (qualitative) | Cash, deferred revenue | Pure FCF lever, zero revenue effect. 10% of ARR moved to 3-yr prepaid ≈ +$240M one-time cash |
| Service start date vs booking date | `lag_start` | days | I | In-period revenue | Renewals cannot be recognized before the renewal period begins |
| Deferred revenue (current, non-current) | `dr_c`, `dr_nc` | revenue | D | Waterfall, reconciliation | Commvault 3/31/26: $485.0M / $293.7M |
| RPO and current RPO | `rpo`, `crpo` | tcv | D | Reconciliation | Rubrik ~$2.44B RPO at 4/30/26, ~53% within 12 months |
| Contract assets / unbilled receivables | `ca` | revenue | F | Reconciliation | Corrected identity: `Rev = Billings − ΔDR + ΔCA` |
| Material rights / customer options | `mr` | revenue | D | One-off revenue | Rubrik: $70.2M in FY26, $8.5M in Q1 FY27, declining sequentially |
| Cancellation / termination rights | — | — | D | RPO validity | RPO excludes cancellable arrangements — never a hard revenue floor |

---

## E. Product and portfolio mix

| Variable | Symbol | Type | Tier | Enters | Anchor / note |
|---|---|---|---|---|---|
| Revenue mix by stream | `mix_rev[s]` | ratio | D | Gross margin, growth | Commvault FY26: term 36.8%, SaaS 28.1%, perpetual 3.7%, support 27.1%, PS 4.4% |
| Term-license → SaaS transition rate | `d_mix_saas` | rate | F | Reported growth | +10 pts of mix ⇒ reported growth −8.5 pts vs ARR growth, gross margin −3.3 pts, **ARR neutral** |
| Workload coverage (VMware, Hyper-V, Proxmox, AHV, K8s, M365, SaaS apps, cloud-native, AI artifacts) | — | — | X | Addressable demand | Hypervisor coverage gates participation in the migration displacement window |
| Cyber-recovery / security SKU attach | `attach_cyber` | ratio | I | Expansion, ASP | The specification that cyber insurance and DORA actually force |
| Appliance / hardware attach | `mix_hw` | ratio | D | Gross margin | Appliance-attached vendors get revenue-positive, margin-negative from BOM inflation |
| Marketplace-transactable share | `mix_mktpl` | ratio | X | Deal size, cycle time | Private offers draw down committed cloud spend, moving the purchase out of a scrutinized software line |

---

## F. Route to market

| Variable | Symbol | Type | Tier | Enters | Anchor / note |
|---|---|---|---|---|---|
| Indirect share of revenue | `mix_indirect` | ratio | D | Discount, net price | Commvault ~90% indirect in FY26/25/24; Veeam effectively 100% |
| Distributor concentration | `conc_partner` | ratio | D | Concentration risk | Commvault Partner A = 32% of FY26 revenue; Rubrik Partners A/B = 27%/29% in Q1 FY27 |
| Active partner count and tier mix | `n_partners` | count | X | Capacity | Veeam 34,000+ partners (Dec 2024). Scrapeable from partner locators; stale listings are the pitfall |
| Channel inventory / weeks of supply | `woS` | days | I | Sell-in vs sell-through | Only material for appliance-attached business |
| MSP / service-provider (rental) share | `mix_msp` | ratio | D (qualitative) | Revenue pattern | Monthly rental changes both timing and retention behaviour |
| Geographic mix | `mix_geo` | ratio | D | FX, growth | Commvault FY26 Americas $702.9M / International $480.8M |

---

## G. Cost, capacity, and the profit side

| Variable | Symbol | Type | Tier | Enters | Anchor / note |
|---|---|---|---|---|---|
| Gross margin by stream | `gm[s]` | ratio | F | Gross profit | Commvault FY26: term 97.6%, SaaS 64.5%, perpetual 98.8%, support 81.6%, PS 32.9% |
| SaaS delivery cost per $1 of SaaS ARR | `cogs_per_arr` | ratio | F | SaaS margin path | Commvault $0.347; Rubrik (subscription/Cloud ARR) $0.178 — **architecturally different, not comparable** |
| Dedup + compression ratio | `dedup` | ratio | A | Storage COGS | **No independent published measurement.** 5:1→6:1 ≈ +0.9 pt of total gross margin |
| Storage tiering mix (hot / IA / archive) | `mix_tier` | ratio | A | Storage COGS | S3 Standard $23.55/TB-mo vs Deep Archive $1.01/TB-mo, a 23× spread; retrieval SLA caps the lever |
| Egress volume | `egress_gb` | count | I | COGS | $0.09/GB — a large restore is a direct COGS event |
| S&M / R&D / G&A as % of revenue | `opex_ratio[f]` | ratio | D | Operating income | Commvault FY26: 43.9 / 13.7 / 13.7. Rubrik FY26: 58.4 / 28.4 / 19.5 |
| Fully loaded cost per employee | `cost_head` | cash | F | Opex from headcount | Commvault $259.5K; Rubrik $286.9K non-GAAP |
| Headcount growth rate | `g_head` | rate | D | Opex | 100 net heads ≈ $26M ≈ 2.2 pts of margin at Commvault scale |
| Opex growth vs revenue growth gap | `gap` | ratio | F | Operating margin | **0.60 pt of operating margin per pt of gap.** The single largest controllable lever |
| Magic number (gross-margin adjusted) | `mn_gm` | ratio | F | S&M efficiency | Rubrik FY26 0.466 (25.8-mo payback); Commvault 0.329 (36.5 mo) |
| Deferred commissions capitalised / amortised | `dc_cap`, `dc_amort` | cash | D | FCF, GAAP margin | A bookings surge raises GAAP margin relative to cash margin |
| Stock-based compensation | `sbc` | cash | D | GAAP vs non-GAAP, dilution | Commvault 10.0% of revenue; Rubrik 25.0% (FY26). Never model SBC as free — Commvault bought back $446M |
| Capex + capitalised software | `capex` | cash | D | FCF | 0.6% of revenue at Commvault — noise, unless the vendor moves off hyperscalers (then ~9%, Zscaler-like) |
| Δ deferred revenue | `d_dr` | cash | D | FCF | Dominant FCF line: Commvault +$136.4M FY26; Rubrik +$425.8M |
| Realized AI cost savings | `ai_savings` | cash | A | Opex | **No published evidence at any data-protection vendor. Model as zero; treat claims as upside** |

---

## H. Exogenous demand drivers

Full treatment, with proxy series and honest predictive value, in `demand-drivers-and-alt-data.md`.
These enter as **bounded deviations from the baseline growth rate**, grouped into mutually exclusive
mechanism buckets so they cannot be double-counted.

| Bucket | Variables | Direction (as of 2026-07-27) |
|---|---|---|
| **Cyber-resilience budget** | Ransomware incidence and severity, cyber insurance underwriting requirements and premium trend, regulatory deadlines (DORA, NIS2, SEC, HIPAA) | **Mixed to weakening.** Incidence up; severity, payments, recovery cost and insurance premiums all down. Regulatory impulse weaker in 2026–27 than 2024–25 |
| **Platform-change forced decisions** | Broadcom/VMware migration, cloud migration and repatriation, M&A-driven renewal contests | **Positive but slow-diffusing.** 86% reducing VMware footprint, only 4% fully migrated after two years |
| **Workload expansion** | M365 and SaaS-app backup, Kubernetes, AI/ML artifacts, cloud-native | **Positive, unmeasurable.** M365 Backup GA at $0.15/GB-mo is a price floor and an ISV COGS line; K8s sizing estimates span 2× in the base year |
| **Pricing / ASP** | Hardware and media cost curves, M365 Backup price floor, competitive discounting | **Mixed.** HDD +46% since Sep 2025 helps software-only ROI cases, hurts appliance margins |
| **Macro / budget timing** | IT budget growth, enterprise software spend, corporate capex | **Positive headline, poor pass-through.** Gartner 2026 software +15.5%, but the acceleration is AI infrastructure, not infrastructure software |

Market baseline: IDC Semiannual Software Tracker 2H2025 market-average sequential growth **8.8%**;
the leader holds **13.6%** share. **No published elasticity of data-protection spend to any of these
drivers exists.** Use the revealed-preference ceiling: all drivers together produced ~8.8% half-over-half
in the most favorable ransomware environment on record, so no single driver is worth more than a few
points.

---

## I. Accounting and measurement artifacts

Not demand. They move reported numbers anyway, and they are the most common source of a "surprise."

| Variable | Type | Tier | Note |
|---|---|---|---|
| FX translation on revenue and on cost | ratio | D | Commvault FY26: +$29.5M, ~3 pts of headline growth — larger than most operational levers. Roughly half the cost base is also non-USD |
| Definitional recasts | — | D | Commvault's FY27 subscription recast added $202.2M to the FY26 subscription base with no revenue change |
| Acquisitions and their ARR contribution | arr | D | Acquired SaaS ARR is excluded from Commvault's NRR for ~12 months |
| Fiscal calendar (4-5-4, 13-week, 14-week quarters) | days | D | Day-of-quarter indexing is invalid without it |
| Convertible notes, buybacks, share count | count | D | Rubrik diluted shares 196.5M FY26 → ~228M guided FY27 (+16%) |
| Restructuring and one-time items | cash | D | Commvault's Q3 FY26 plan pulled FY26 FCF guidance down $10–15M |
| Guidance realization ratio | ratio | F | **Fit it.** Rubrik beat revenue guidance by 5–10% for five straight quarters; taking guidance at face value systematically under-forecasts |

---

## J. Meta-variables — measuring your own predictability

These are not inputs to the revenue number. They are inputs to the *interval*, and skipping them is how
forecasts become overconfident. Full treatment in `probability-and-calibration.md`.

| Variable | Definition | Why it matters |
|---|---|---|
| Visibility ratio | contracted revenue ÷ total forecast revenue | Bounds achievable accuracy. Compute before modeling |
| Growth autocorrelation β | from `g_t = α + β·g_{t−1} + ε_t` | High β in infrastructure software means smooth deceleration is the base rate, not driver-driven jumps |
| Benchmark skill score | your CRPS ÷ benchmark CRPS | The only accuracy measure that means anything. Benchmark = seasonal random walk or last-quarter-annualized |
| Interval coverage | fraction of periods inside the 80% interval | Should be ~0.8; is typically ~0.5 in practice, indicating overconfidence |
| PIT histogram | probability integral transform of realizations | Uniform = calibrated. U-shaped = intervals too narrow |
| Snapshot history depth | quarters of point-in-time pipeline data | Below ~8 quarters, conversion and calibration models are not fittable. Start capturing today |
