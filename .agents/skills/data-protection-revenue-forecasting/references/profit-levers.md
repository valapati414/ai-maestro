# Profit Levers, Unit Economics, and What Moves the Needle

*Anchor vendors: Commvault (CVLT, FY ends 31 Mar), Rubrik (RBRK, FY ends 31 Jan). Private comparators:
Veeam, Cohesity/Veritas, Druva. **As of 2026-07-27.***

Convention: every derived number shows its arithmetic. Rules of thumb are tagged **[ROT]**. Unsourced
structural assumptions are tagged **[ASSUMPTION]**.

---

## A. The margin structure of a data-protection vendor

### A.1 Cost of revenue decomposition — the one industry where COGS is a real forecast variable

Commvault is the only vendor in the category that discloses cost of revenue by stream. FY2026 (year
ended 31 Mar 2026), $ thousands, from the
[Q4 FY26 press release](https://ir.commvault.com/news-releases/news-release-details/commvault-announces-fourth-quarter-fiscal-2026-financial-results):

| Stream | Revenue | Cost of revenue | Gross margin | % of revenue |
|---|---|---|---|---|
| Term-based license | 435,324 | 10,662 | **97.6%** | 36.8% |
| SaaS | 332,981 | 118,301 | **64.5%** | 28.1% |
| Perpetual license | 43,212 | 531 | **98.8%** | 3.7% |
| Customer support | 320,426 | 58,879 | **81.6%** | 27.1% |
| Other services (PS) | 51,747 | 34,747 | **32.9%** | 4.4% |
| **Total** | **1,183,690** | **223,120** | **81.2%** | 100% |

Arithmetic check: 1,183,690 − 223,120 = 960,570; 960,570 / 1,183,690 = 81.15%, matching the disclosed
81.2% GAAP gross margin.

Structural facts a forecast must respect: term and perpetual license COGS are ~2–3% of revenue
(royalties and amortized acquired technology, essentially zero marginal cost); support runs a stable
~82%; professional services runs 33% and is a customer-acquisition subsidy, not a profit center; and
**SaaS at 64.5% is 33 points below term license.** A single blended gross margin destroys the model,
because SaaS is the fastest-growing stream (+52% in FY26) and the lowest-margin one.

### A.2 Why data-protection SaaS gross margin is structurally lower than application SaaS

The vendor is the custodian of the customer's backup copies. Storage capacity under management grows
monotonically with retention policies — it does not scale with seats or transactions — and it is billed
to the vendor monthly by a hyperscaler. Reference costs:
[AWS S3 Standard at $0.023/GB-month](https://aws.amazon.com/s3/pricing/) = **$23.55/TB-month ≈
$283/TB-year**; S3 Glacier Deep Archive at $0.00099/GB-month ≈ **$1.01/TB-month**, a 23× spread. Egress
is $0.09/GB, so a large restore is a direct COGS event. Independent object storage is cheaper still
([Backblaze B2 at $6.95/TB-month](https://www.backblaze.com/cloud-storage/pricing)).

**Commvault's disclosed SaaS trajectory** ($ thousands):

| | Q1 FY26 | Q2 FY26 | Q3 FY26 | Q4 FY26 | FY25 | FY26 |
|---|---|---|---|---|---|---|
| SaaS revenue | 72,445 | 80,018 | 87,379 | 93,139 | 219,256 | 332,981 |
| SaaS cost of revenue | 25,972 | 29,187 | 31,587 | 31,555 | 79,341 | 118,301 |
| **SaaS gross margin** | **64.2%** | **63.5%** | **63.9%** | **66.1%** | **63.8%** | **64.5%** |

The full-year improvement is only +0.7 points, but Q4 inflected +2.3 points sequentially. Management
attributes this to "SaaS hosting margins driven by scale efficiencies and ongoing product optimization"
and states the internal target is "well north of 70% … over the next couple of years"
([Q4 FY26 earnings call, 28 Apr 2026](https://www.fool.com/earnings/call-transcripts/2026/04/28/commvault-cvlt-q4-2026-earnings-transcript/)).
Unit cost check: FY26 SaaS COGS ÷ average SaaS ARR = 118,301 ÷ ((281,045 + 400,157)/2 = 340,601) =
**$0.347 of delivery cost per $1 of SaaS ARR**. Reaching 70%+ means driving that below $0.30.

**Rubrik does not disaggregate hosting cost.** Only aggregate subscription cost of revenue is disclosed:
$229,741K in FY26 and $66,723K in Q1 FY27. Q1 FY27 subscription gross margin =
(374,200 − 66,723) / 374,200 = **82.2%**, versus 80.4% a year earlier — ~18 points above Commvault's
SaaS margin. The explanation is architectural, not operational: Rubrik's RSC is a hybrid subscription in
which "the software hosted from the cloud (as a service) and the on-premise software licenses" form a
single performance obligation
([Rubrik FY2026 10-K](https://s203.q4cdn.com/667520861/files/doc_financials/2026/q4/96d7d947-6d19-4543-a70a-f5184d1370e8.pdf)),
and much protected data remains on customer-side clusters. Commvault Cloud's backup-as-a-service stores
the data in Commvault's own tenancy. Subscription COGS per $1 of Cloud ARR: Rubrik 229,741 ÷ 1,293,300 =
**$0.178**; Commvault 118,301 ÷ 400,157 = **$0.296**. **Do not treat these two "SaaS" gross margins as
comparable.** Druva, a pure BaaS vendor, publishes no gross margin — no published evidence found.

**Sensitivity: 10 points of SaaS gross margin.** Effect on total operating margin = 10 pts × SaaS share
of revenue. At Commvault's FY26 mix (28.1%): **+2.81 points** ($33.3M of gross profit on $1,183.7M). At
the FY27 guided mix (~34–35% of revenue): **+3.45 points**. Feasibility check: +10 points at FY26 scale
requires cutting SaaS COGS by $33.3M from $118.3M — a **28% cost reduction** — which is why the CFO
frames it as a multi-year program.

### A.3 Opex structure benchmarks from actual filings

All GAAP, as % of revenue, most recent completed fiscal year:

| Company | Period | Revenue | S&M | R&D | G&A | GAAP op margin | Non-GAAP op margin | Rev growth |
|---|---|---|---|---|---|---|---|---|
| Commvault | FY26 (3/26) | $1,184M | 43.9% | 13.7% | 13.7% | 6.3% | 20.1% | 19% |
| Rubrik | FY26 (1/26) | $1,316M | 58.4% | 28.4% | 19.5% | (26.2)% | (0.5)% | 48% |
| Rubrik | Q1 FY27 (4/26) | $387M | 49.9% | 29.5% | 14.7% | (13.6)% | +6.4% | 39% |
| Nutanix | FY25 (7/25) | $2,540M | 41.6% | 29.0% | 9.3% | 6.8% | 21.1% | 18% |
| Pure Storage (now Everpure) | FY26 (2/26) | $3,663M | — | — | — | 3.1% | 17.3% | 16% |
| Zscaler | FY25 (7/25) | $2,673M | 47.1% | 25.2% | 9.4% | (5)% | 22% | 23% |
| Datadog | FY25 (12/25) | $3,427M | 27.9% | 45.2% | 8.2% | (1)% | 22% | 28% |

Sources: [Commvault Q4 FY26](https://ir.commvault.com/news-releases/news-release-details/commvault-announces-fourth-quarter-fiscal-2026-financial-results);
[Rubrik Q4 FY26](https://s203.q4cdn.com/667520861/files/doc_financials/2026/q4/Rubrik-Inc-99-1-Press-Release-1-31-2026_FINAL.pdf)
and [Q1 FY27](https://s203.q4cdn.com/667520861/files/doc_financials/2027/q1/Rubrik-Inc-99-1-Press-Release-4-30-2026_FINAL.pdf);
[Nutanix Q4 FY25](https://ir.nutanix.com/news-releases/news-release-details/nutanix-reports-fourth-quarter-and-fiscal-2025-financial-results);
[Everpure/Pure Q4 FY26](https://investor.everpuredata.com/news-and-events/press-releases/press-release-details/2026/Everpure-Announces-Fiscal-Fourth-Quarter-and-Full-Year-2026-Financial-Results/default.aspx);
[Zscaler Q4 FY25](https://ir.zscaler.com/news-releases/news-release-details/zscaler-reports-fourth-quarter-and-fiscal-2025-financial-results);
[Datadog Q4 FY25](https://investors.datadoghq.com/news-releases/news-release-details/datadog-announces-fourth-quarter-and-fiscal-year-2025-financial).

Three patterns to use as priors. (1) At $1–1.2B revenue and high-teens growth, **infrastructure-software
S&M lands at 42–44% and R&D at 13–29%** — the R&D spread is the largest structural difference between a
mature vendor (Commvault 13.7%) and a scaling one (Rubrik 28.4%). (2) The GAAP-to-non-GAAP gap is almost
entirely stock compensation and is 14 points at Commvault versus 26 at Rubrik. (3) Private-company
medians for CY2025 are R&D 27% of revenue and software gross margin 80%
([Benchmarkit / Aleph, 2026 B2B SaaS & AI-Native Performance Benchmarks, n=342, 1 Jun 2026](https://www.benchmarkit.ai/_files/ugd/2a084b_f19d7f96a9e24aba9202e01224d0dbcc.pdf))
— the public data-protection vendors are not outliers on gross margin but are heavier on S&M.

---

## B. Unit economics, defined precisely

### B.1 Rule of 40 and its variants

Three variants that give materially different answers:

| Variant | Commvault FY26 | Rubrik FY26 | Rubrik guided FY27 | Commvault guided FY27 |
|---|---|---|---|---|
| Revenue growth + FCF margin | 18.9 + 20.0 = **38.9** | 48.5 + 18.1 = **66.6** | 24.8 + 18.1 = **42.9** | 10.2 + 19.5 = **29.7** |
| Revenue growth + non-GAAP op margin | 18.9 + 20.1 = **39.0** | 48.5 + (0.5) = **48.0** | — | 10.2 + 20.5 = **30.7** |
| Revenue growth + GAAP op margin | 18.9 + 6.3 = **25.2** | 48.5 + (26.2) = **22.3** | — | — |
| ARR growth + FCF margin | 21.0 + 20.0 = **41.0** | 33.8 + 18.1 = **51.9** | 26.9 + 18.1 = **45.0** | 18.5 + 19.5 = **38.0** |

Arithmetic: Commvault revenue growth 1,183,690/995,619 − 1 = 18.9%; FCF margin 237,151/1,183,690 = 20.0%.
Rubrik 1,316,191/886,544 − 1 = 48.5%; FCF 237,840/1,316,191 = 18.1%; subscription ARR 1,462,092/1,092,584
− 1 = 33.8%. FY27 guides: Rubrik revenue mid $1,643M (+24.8%), FCF mid $298M (18.1%), subscription ARR
mid $1,858M (+27.1%); Commvault revenue mid $1,305M (+10.2%), FCF mid $255M (19.5%), subscription ARR mid
$1,205M (+18.5% on the recast basis).

The 11-point gap between Commvault's revenue-based (29.7) and ARR-based (38.0) FY27 Rule of 40 is the
whole forecasting problem in one number. Median private-company Rule of 40 for CY2025 was 25%, top
quartile 43% ([Benchmarkit 2026](https://www.benchmarkit.ai/_files/ugd/2a084b_f19d7f96a9e24aba9202e01224d0dbcc.pdf)).
**Always state which variant you used.**

### B.2 Magic number, CAC payback, LTV/CAC

```
MN     = ΔARR / S&M                        (annual form, current-period S&M)
MN_gm  = (ΔARR × gross margin) / S&M
payback_months = 12 / MN_gm
LTV/CAC = (ACV × gross margin / annual churn) / CAC
```

**Rubrik FY26:** ΔSubscription ARR = 1,462,092 − 1,092,584 = 369,508. Non-GAAP S&M = 653,167.
MN = 0.566. MN_gm = 369,508 × 0.823 / 653,167 = **0.466** → payback = 12/0.466 = **25.8 months**.
**Commvault FY26:** ΔSubscription ARR = 989,294 − 780,098 = 209,196. S&M = 519,688. MN = 0.403.
MN_gm = 209,196 × 0.816 / 519,688 = **0.329** → payback = **36.5 months**.

Both look poor against the CY2025 median of 16 months and top quartile of ≤6 months
([Benchmarkit 2026](https://www.getaleph.com/answers/cac-payback-period-saas-2026)) — because a fully
blended magic number charges *all* S&M (including renewal management of a large installed base and, at
Commvault, support of a shrinking perpetual estate) against *net* new ARR. **[ROT]** For a vendor with a
large installed base, expect blended payback 1.5–2.5× the survey median; use the ratio directionally
across years for the same company, never cross-sectionally.

Median magic number CY2025 was 1.37, blended CAC ratio $1.30, new-name CAC ratio $1.63, expansion CAC
ratio ~$1.00 ([Benchmarkit 2026](https://www.getaleph.com/answers/saas-magic-number-2026)). Private
median LTV/CAC 3.3×.

### B.3 GRR, NRR, and the steady-state identity

**NRR = GRR + expansion rate.** With no new logos, ARR compounds at NRR: `ARR_t = ARR_0 × NRR^t`. With
new logos, `ARR_{t+1} = ARR_t × NRR + NewLogo_{t+1}`. Two consequences:

- **Terminal value depends on GRR, not NRR.** Value the installed base as an annuity decaying at
  (1 − GRR): `PV = ARR / (r + churn)`. At r = 10% and GRR = 90%, multiple = 1/(0.10+0.10) = **5.0× ARR**;
  at GRR 92%, 1/0.18 = **5.56×** (+11%); at GRR 88%, 1/0.22 = **4.55×** (−9%). Expansion (the NRR
  premium) is discretionary customer budget and can go to zero in a downturn; contractual churn cannot
  be recovered.
- **Half-life of the base** = ln(0.5)/ln(GRR). GRR 84% → 4.0 years. 90% → 6.6 years. 95% → 13.5 years.

Disclosed values: Commvault **SaaS NRR 122%** as of 31 Mar 2026; Rubrik **average subscription
dollar-based NRR "over 120%"** at 31 Jan 2026 and 2025. Neither discloses GRR — **no published evidence
found**; it must be inferred. Private-company median GRR fell from 88% to 84% in CY2025, with the 75th
percentile falling 95% → 91%; sales-led vendors ran 88% median versus 79% for PLG, and $50–100K ACV
cohorts ran 91% ([Benchmarkit 2026](https://www.benchmarkit.ai/_files/ugd/2a084b_f19d7f96a9e24aba9202e01224d0dbcc.pdf)).
**[ASSUMPTION]** For enterprise data protection, GRR of 90–93% is the defensible modelling range.

### B.4 ARR per employee

- **Commvault:** 1,121,571 ÷ 3,295 employees at 31 Mar 2026
  ([FY26 ESG report](https://commvault.gcs-web.com/static-files/4f9b99e4-bc68-46b7-9ec1-5d74bc5e4dad))
  = **$340.4K total ARR/employee**; subscription ARR 989,294 ÷ 3,295 = **$300.2K**; revenue 1,183,690 ÷
  3,295 = **$359.2K**. (The 10-K rounds headcount to ~3,300.)
- **Rubrik:** 1,565,141 ÷ 3,797 employees at 31 Jan 2026 = **$412.2K** — but the ARR is dated 30 Apr 2026
  and the headcount 31 Jan 2026; on matched dates (ARR 1,462,092) it is **$385.1K**. Revenue/employee =
  1,316,191 ÷ 3,797 = **$346.6K**.

Benchmark: CY2025 median **$193K** ARR/employee, top quartile **$278.8K**, up 29% YoY (n=96, Benchmarkit
2026 — note the same report's executive summary quotes $175K median, an internal inconsistency; cite the
section figure). Both anchor vendors are well above the top quartile, consistent with high-ACV enterprise
motions. **ARR per quota-carrying rep: neither vendor discloses rep counts — no published evidence
found.** Any rep-productivity model is an assumption, not a source.

### B.5 The growth-versus-profit arithmetic

Incremental S&M converts to ARR at the marginal magic number, which is below the average one. Value is
created while:

```
ΔARR/ΔS&M × gross margin × 1/(r + churn) > 1
```

At GRR 90%, r 10%, GM 82%: the threshold marginal magic number is 1/(0.82 × 5.0) = **0.244**. Both
vendors' blended MN_gm (0.47 and 0.33) clear it, which says the *average* S&M dollar is value-creating.
The trap is that the *marginal* dollar is not the average dollar: at 0.244, a vendor is buying $1.00 of
ARR for $4.10 of S&M, and any further degradation is destructive. **[ROT]** Stop adding capacity when
marginal MN_gm falls below ~0.25–0.30 at enterprise churn rates.

---

## C. Ranked sensitivity table: what actually moves the needle

Reference vendor = Commvault FY26 actuals: revenue $1,183.7M, total ARR $1,121.6M, SaaS ARR $400.2M,
gross margin 81.2%, opex (S&M+R&D+G&A+D&A) $855.0M = 72.2% of revenue, GAAP op margin 6.3%, non-GAAP
20.1%, FCF margin 20.0%.

| Rank | Lever | Realistic 1-yr move | Revenue effect | Op margin / FCF effect | Confidence |
|---|---|---|---|---|---|
| 1 | **Opex growth vs revenue growth gap** | 0–10 pts of gap | none | **0.60 pt of op margin per pt of gap**; 20%/10% = +6.1 pts | **High** (identity) |
| 2 | **Price / renewal uplift** | +1 to +3 pts | +$11.8M to +$35.5M (+1.0–3.0%) | +0.95 to +2.85 pts; = +15% to +45% of GAAP EBIT | **High** on arithmetic, Med on volume |
| 3 | **Channel discount discipline** | 1 pt off a 30% avg discount | +1.43% = +$16.9M | +1.36 pts | Med (discount level undisclosed) |
| 4 | **Payment terms: annual → 3-yr prepaid** | 10% of ARR | **zero** | **+$240M one-time FCF** (101% of FY26 FCF); no repeat | **High** on math, Low on adoption |
| 5 | **SaaS gross margin** | +3 to +10 pts | none | +0.8 to +2.8 pts at 28% SaaS mix | Med-High (Q4 already +2.3 pts) |
| 6 | **Cross-sell / attach mix** | shift $50M net new ARR from new-logo to expansion | none (same ARR) | S&M saving $31.5M = **+2.7 pts** | Med |
| 7 | **NRR ±5 pts** | 117% ↔ 127% on SaaS | yr-1 ±$10M (±0.85%) | ±0.55 pt; **3-yr ARR ±$86–93M** | Med-High |
| 8 | **Mix shift term-license → SaaS** | +10 pts of revenue mix | reported growth **−8.5 pts** vs ARR growth | gross margin **−3.3 pts**; ARR neutral | **High** |
| 9 | **Storage cost per TB** | dedup 5:1→6:1; tier 30% to archive | none | +0.9 pt and +1.6 pt of total margin respectively | **Low** (all inputs undisclosed) |
| 10 | **GRR ±2 pts** | 88% ↔ 92% | yr-1 ∓$12M | ∓0.7 pt in yr 1; **terminal value +11%/−9%** | Med |
| 11 | **Sales capacity (+10% reps)** | 6-mo ramp | +$9.4M in-yr revenue | ≈ margin-neutral yr 1, accretive yr 2 | **Low** (rep counts undisclosed) |
| 12 | **FX** | ±3 pts of reported growth | FY26: FX added **$29.5M** | partial natural hedge via intl. cost base | **High** (disclosed) |
| 13 | **SBC** | 10% → 12% of revenue | none | GAAP only; zero FCF; drives buyback cash | **High** |
| 14 | **AI cost reduction in support/R&D** | claimed | none | **not quantified by either vendor** | **Very low** |

### Arithmetic behind each row

**1. Operating leverage identity.** `OM_new = GM − opex_ratio × (1 + g_opex)/(1 + g_rev)`. With GM
81.15%, opex ratio 72.23%, revenue +20%, opex +10%: 81.15 − 72.23 × 1.10/1.20 = 81.15 − 66.21 =
**14.94%**, versus 8.92% base (pre-restructuring) — **+6.0 points in one year**. If opex also grows 20%:
81.15 − 72.23 = 8.92%, i.e. flat. Derivative: 72.23/1.20 = **0.60 point of margin per point of
growth-rate gap**. Headcount translation: opex ÷ headcount = 854,971 ÷ 3,295 = **$259.5K of fully loaded
opex per employee**, so 100 net heads ≈ $26M ≈ 2.2 points of margin. Rubrik's equivalent: non-GAAP opex
1,089,286 ÷ 3,797 = **$286.9K**.

**2. Pricing.** The famous multiplier is just the reciprocal of operating margin. Marn & Rosiello found a
1% price improvement lifts operating profit **11.1%** for the average of 2,463 Compustat companies,
versus 7.8% for variable cost, 3.3% for volume and 2.3% for fixed cost
([*Managing Price, Gaining Profit*, HBR, Sep–Oct 1992](https://pages.charlotte.edu/wp-content/uploads/sites/868/2014/12/ManagingPrice.pdf));
1/0.111 = 9.0%, which is that sample's average operating margin. Applying the same logic here: at
Commvault's 6.3% GAAP margin, 1% price = **+15.9% of operating profit**; at the 20.1% non-GAAP margin,
**+5.0%**. More recent restatements are lower (McKinsey: **6.0%** for a typical midsize US company —
[*Pricing: the next frontier of value creation in private equity*](https://www.mckinsey.com/capabilities/growth-marketing-and-sales/our-insights/pricing-the-next-frontier-of-value-creation-in-private-equity)),
because margins are higher now. **Breakeven elasticity:** at 81.2% gross margin, a 1% price increase
stays gross-profit-neutral even if you lose **1.22% of volume** — solve (1−x)(1.01 − 0.188) = 0.812 →
x = 1.22%. That asymmetry is why pricing is the highest-ROI revenue lever in this category.

**3. Discount.** If net revenue = list × (1 − d) and d falls from 30% to 29%, net price rises
0.71/0.70 − 1 = **+1.43%**. A point of discount is worth 1.43× a point of list price at a 30% discount,
and 1.67× at 40%. **[ASSUMPTION]** two-tier distribution discounts of 25–40%; neither vendor discloses
average discount.

**4. Payment terms.** 10% of $1,121.6M ARR = $112.2M annual billings; collected as a 3-year prepaid =
$336.5M, so **+$224–240M of one-time cash** with zero revenue effect (ASC 606 recognition is unchanged).
The forecasting trap: it is non-recurring and creates a collections air pocket in years 2–3. Evidence
that this line dominates FCF: Commvault's FY26 deferred revenue increased **$136.4M = 11.5% of revenue**;
Rubrik's increased **$425.8M = 32.4% of revenue**.

**6. Cross-sell.** Expansion ARR costs $1.00 of S&M per $1 versus $1.63 for new-name ARR (Benchmarkit
2026). Shifting $50M of net new ARR from new-logo to expansion saves 50 × (1.63 − 1.00) = **$31.5M** =
2.66 points of margin at constant ARR. Corroborated on the revenue side by Commvault's 122% SaaS NRR and
Rubrik's 2,805 customers above $100K ARR (+25% YoY), both driven by multi-product adoption.

**7. NRR compounding.** On SaaS ARR of $400.157M, ignoring new logos: at 122%, 1.22³ = 1.815848 →
**$726.7M**; at 127%, 1.27³ = 2.048383 → **$819.7M** (+$93.0M); at 117%, 1.17³ = 1.601613 → **$640.9M**
(−$85.8M). Spread between +5 and −5 = **$178.8M = 44.7% of today's SaaS ARR.** Year-1 P&L effect is far
smaller: +5 pts on a $400M base = +$20M of ARR, of which roughly half lands in-year revenue (+$10M, 0.85%
of total revenue), and at ~65% SaaS gross margin with near-zero incremental S&M that is **+$6.5M ≈ +0.55
point of margin**. NRR is a valuation lever with a slow P&L fuse.

**8. Mix shift.** Same $1 of ARR, different reported revenue: a 3-year term license recognizes its
license component upfront, SaaS recognizes ratably. The empirical signature is in Commvault's FY27
guidance: **total revenue +10.2% against subscription ARR +18.5%** — an 8.3-point wedge that is pure
accounting, not demand. Gross margin cost: 10 points of revenue mix moved from term license (97.6%) to
SaaS (64.5%) = 10% × 33.1 = **−3.3 points of blended gross margin**. Rubrik shows the same phenomenon in
reverse: FY26 revenue grew 48.5% while subscription ARR grew 33.8%, inflated by upfront recognition and
by "material rights" (Subscription Credits) — Q4 FY26 revenue included **$18M of material rights**, and
growth excluding them was 43% versus 46% reported.

**9. Storage COGS.** **[ASSUMPTION]** storage ≈ 55% of Commvault's $118.3M SaaS COGS ≈ $65M. Improving
global dedup/compression from 5:1 to 6:1 reduces stored bytes 16.7% → saves $10.9M → SaaS GM +3.3 pts →
total GM **+0.92 pt**. Tiering 30% of capacity from Standard to Deep Archive removes
30% × (1 − 1/23) = 28.7% of storage cost → $18.7M → SaaS GM +5.6 pts → total GM **+1.58 pt**. Constraint
that caps this lever: Deep Archive retrieval takes up to 12 hours and costs $0.02/GB = $20.48/TB
([AWS S3 pricing](https://aws.amazon.com/s3/pricing/)), incompatible with recovery SLAs for anything but
long-term compliance copies. Neither vendor discloses dedup ratios, capacity under management, or
reserved-capacity commitments — no published evidence found.

**12. FX.** Commvault FY26 revenue was $29.5M higher than at prior-year rates: reported growth 19% versus
16% constant currency; total ARR +21% reported versus +18% cc. FX moved ~3 points of headline growth —
larger than most of the operational levers above.

**13. SBC and dilution.** Commvault FY26 SBC $118.9M = **10.0% of revenue**; Rubrik $329.4M = **25.0%** in
FY26 and $73.4M = **19.0%** in Q1 FY27. Rubrik's entire GAAP-to-non-GAAP gap (−26.2% → −0.5%) is SBC.
Dilution: Rubrik weighted diluted shares 196.5M in FY26 versus ~228M guided for FY27 = **+16%**.
Commvault instead repurchased ~4M shares for **$446M** in FY26 — 188% of its $237M FCF — which is where
SBC's true cash cost appears. Never model SBC as free.

**14. AI.** Best available evidence is indirect and none of it is a data-protection vendor's own P&L.
Intercom reports Fin resolving **81% of its support volume**, avoiding ~100 CS hires for **$7.5–9M of
annual savings** — self-reported by the vendor of the product
([Intercom, Mar 2026](https://www.intercom.com/blog/automate-customer-service-while-improving-customer-experience/)).
Equifax doubled its AI savings forecast to **$150M run-rate over 2026–2028**
([PYMNTS, Jul 2026](https://www.pymnts.com/earnings/2026/early-ai-gains-prompt-equiax-double-savings-forecast-150-million-dollars/)).
Sector-wide, median R&D fell from 35% to 27% of revenue and ARR/employee rose 29% in CY2025, attributed
partly to AI (Benchmarkit 2026) — but the same report notes this coincided with headcount rationalisation
and a 4-point GRR decline, so attribution is unproven. Commvault's CFO says AI "will give us great
operating leverage opportunity" while guiding FY27 non-GAAP EBIT to 20.5% versus 20.1% actual — **+0.4
point**, i.e. guidance embeds no material AI savings. **For data-protection vendors specifically: no
published evidence of realized, quantified AI cost savings. Model it as zero and treat any claim as
upside.**

Private-vendor context for calibration: Veeam has disclosed ARR "more than $2 billion" (June 2026 press
release) with a **$2.1B** figure quoted at VeeamON 2026
([Techzine](https://www.techzine.eu/blogs/data-management/142368/anand-eswaran-veeam-from-backup-champ-to-data-ai-trust-layer/));
Cohesity/Veritas disclosed **$1.5B ARR** and a **28% adjusted cash EBITDA margin** on >$1.7B pro-forma
revenue for FY ending July 2024 — the only profitability datapoint available for a private vendor in the
category.

---

## D. The profit forecasting model

### D.1 Driver-based P&L construction

Build in this order, never top-down from a blended margin:

1. **Revenue by stream** from the ARR roll-forward. Opening ARR × NRR + new-logo ARR = closing ARR, run
   separately for term license, SaaS, and support. Then convert each ARR stream to revenue with its own
   recognition rule: SaaS ratably (mid-period convention on net new), term license split between upfront
   license and ratable support per the vendor's allocation, perpetual support ratably.
2. **Gross profit by stream** using the stream margins in §A.1, with SaaS margin on its own improvement
   path. Recompute blended gross margin as an *output*.
3. **Opex from headcount.** Headcount is driven by the bookings target divided by capacity per rep (with
   ramp), plus support headcount driven by installed base, plus R&D as a policy input. Cost per head:
   **$259K** fully loaded at Commvault, **$287K** non-GAAP at Rubrik.
4. **Operating income**, then the FCF bridge below.

### D.2 ASC 340-40 deferred commissions

Commvault capitalises commissions allocated to SaaS, updates and support on *initial* term-license
transactions over **~5 years**, and on *renewals* over the contractual term; commissions allocated to the
license itself are expensed at the point of sale
([Commvault 10-Q, quarter ended 30 Jun 2025](https://www.sec.gov/Archives/edgar/data/1169561/000116956125000069/cvlt-20250630.htm)).
Rubrik amortises over the expected period of benefit, "generally one to five years," with a majority of
contracts at three years.

FY26 flows: Commvault capitalised **$73.7M** and amortised **$47.7M** (asset $103.9M = 8.8% of revenue).
Rubrik capitalised **$153.8M** and amortised **$110.0M** (asset $268.2M = 20.4% of revenue).

**Why a bookings surge hurts cash more than GAAP:** an extra $100M of capitalised commission hits year-1
GAAP expense by only ~$20M on 5-year straight-line (~$10M with a mid-year convention) but consumes $100M
of cash immediately. A strong booking quarter *raises* reported operating margin relative to cash margin.
Forecast the two separately.

### D.3 The FCF bridge, and which line dominates

```
Net income
  + SBC
  + D&A
  + Δ deferred revenue
  + amortisation of deferred commissions − commissions capitalised
  ± other working capital
  − capex and capitalised software
  = FCF
```

**Rubrik FY26**, as % of revenue: net loss −26.5% (−348,828/1,316,191); +SBC 25.0%; +Δ deferred revenue
32.4%; net deferred commissions −3.3% ((109,951 − 153,810)/1,316,191). Those four lines alone take −26.5%
to **+27.6%**; reported operating cash flow margin was 21.5% and FCF margin 18.1% after other working
capital and $45.1M of capex plus capitalised software. **Two lines — SBC and deferred revenue — explain
the entire sign flip from a $349M net loss to $238M of FCF.**

**Commvault FY26:** net income $70.7M, +SBC $123.4M, +D&A $10.3M, +deferred commission amortisation
$47.7M, −commissions capitalised $73.7M, +Δ deferred revenue $136.4M, other working capital negative
(AR −$74.0M) → operating cash flow $244.7M, less capex $7.5M = **FCF $237.2M**. Capex is 0.6% of revenue —
immaterial.

**[ROT]** For asset-light data-protection vendors, deferred revenue is the dominant FCF line and SBC the
second; capex is noise. For a vendor that migrates off hyperscalers onto owned infrastructure, that
changes — capex would move from 0.6% to Zscaler-like levels (property and equipment plus capitalised
software = 9% of revenue in FY25), which is the hidden cost of the "own your own storage" gross-margin
strategy.

### D.4 Common errors

- **Single blended gross margin.** The 33-point spread between term license (97.6%) and SaaS (64.5%)
  means a 10-point mix error is a 3.3-point gross margin error, which at Commvault's GAAP margin is half
  of operating income.
- **Treating ARR growth as revenue growth.** Commvault FY27: subscription ARR +18.5%, total revenue
  +10.2%. Rubrik FY26: subscription ARR +33.8%, revenue +48.5%. The sign of the wedge flips depending on
  where the vendor sits in its recognition transition.
- **Ignoring FX on both sides.** FX added ~3 points to Commvault's FY26 reported growth. A revenue-only FX
  adjustment overstates the margin impact, because roughly half the cost base is also non-USD.
- **Treating non-GAAP operating margin as cash.** Commvault FY27 guides 20.5% non-GAAP EBIT and 19.2% FCF
  margin ($255M/$1,305M) — close, but coincidentally so: the non-GAAP margin excludes $120M+ of SBC that
  costs real cash through buybacks ($446M in FY26), while the FCF margin includes a $136M deferred-revenue
  tailwind that is a billings-timing artifact.
- **Applying survey CAC-payback benchmarks to a blended magic number.** 26–37 months computed from filings
  is not evidence of broken unit economics; it is evidence that the denominator includes installed-base S&M.
- **Extrapolating a one-time prepayment.** Multi-year prepaid cash and material-rights revenue both boost
  a single year and then reverse.
