# Forecasting Without Order Flow Data

*The outside-in procedure: no CRM, no pipeline, no entitlement file. Only public disclosure, alternative
data, and arithmetic. This is the analyst's, investor's, competitor's, and board-observer's situation —
and it is also the right starting point even when you do have order flow, because it produces the
reconciliation checks that catch errors in the internal model.*

**Compiled 2026-07-27.** All arithmetic in the worked examples is reproducible;
`engine/example_outside_in.py` executes it.

---

## 1. The central insight

Without order flow you cannot forecast *bookings*. You can, however, forecast *revenue* rather well,
because most of next year's revenue is already contracted and the vendor tells you so.

For Rubrik at 30 Apr 2026, RPO was ~$2.44B with ~53% expected to be recognized within twelve months —
approximately **$1.29B of the next twelve months' revenue is already under non-cancellable contract**
against a TTM revenue of $1.42B and an FY27 revenue guide of $1.638–1.648B. Roughly 79% of the guided
year is contracted. The forecasting problem is therefore not "what will demand be" but:

1. What is the run-off schedule of the contracted base? (Nearly deterministic; disclosed.)
2. What fraction of the remainder is renewals of contracts expiring in-period? (Estimable from ARR and
   duration mix; high retention.)
3. What is genuinely new? (Small share of in-year revenue, large share of the uncertainty.)

**Compute the visibility ratio before you model anything.** It tells you how much of your interval width
is even legitimate. A model that puts a ±15% interval around a year that is 79% contracted is not
humble, it is wrong.

---

## 2. Inventory: what public disclosure actually gives you

| Available | Vendor examples | Use |
|---|---|---|
| Revenue disaggregated by stream | Commvault (5 lines), Rubrik (2 lines) | Per-stream recognition and gross margin |
| ARR and components | Commvault total/subscription/SaaS; Rubrik subscription/cloud | Waterfall state variable |
| NRR | Commvault SaaS 122%; Rubrik ~120% trailing-4-qtr | Expansion + churn combined |
| RPO, % within 12 months | Commvault $1,041.2M/~59%; Rubrik ~$2.44B/~53% | The contracted floor and the reconciliation anchor |
| Deferred revenue, current/non-current | Both | Billings derivation, cash timing |
| Customer counts and cohorts | Rubrik ≥$100K ARR cohort | Cross-check on new-logo velocity |
| Guidance and its history | Both, quarterly and annual | **Realization-ratio modelling — see §6** |
| Headcount | Commvault ~3,300; Rubrik ~3,797 | Capacity and opex |
| Constant-currency restatements | Commvault (both revenue and ARR) | Strip FX before trend fitting |

| Not available anywhere in this category | Consequence |
|---|---|
| Gross retention rate | Cannot separate churn from expansion. Must assume; 90–93% for enterprise data protection |
| Quota-carrying rep counts | No capacity model. Proxy with job postings (see demand-drivers §C) |
| Bookings, ACV added, or TCV | Cannot invert revenue to demand except through the RPO identity |
| Average discount | Cannot model channel price realization |
| Backlog composition by term length | Duration-mix shifts are invisible until they show up in the revenue line |
| Anything at all for Veeam and Cohesity beyond an occasional ARR headline | See §7 |

---

## 3. The procedure

### Step 1 — Rebase the history

Strip FX and definitional changes *before* fitting anything. Commvault's FY26 reported revenue growth of
19% was 16% in constant currency, and reported net-new ARR diverges sharply from constant-currency
net-new ARR in individual quarters (Q1 FY26: $66.2M reported vs $39.6M cc). If a recast has occurred,
rebuild the entire series on the new definition first — Commvault's FY27 subscription recast lifted the
FY26 subscription base by $202.2M with no change to total revenue.

### Step 2 — Compute the visibility ratio

```
contracted_next_12m = RPO × pct_within_12m
visibility          = contracted_next_12m / forecast_revenue_next_12m
```

Rubrik at 4/30/26: 2,440 × 0.53 = **$1,293M** contracted, against an FY27 guide midpoint of $1,643M ⇒
**visibility ≈ 79%**. Commvault at 3/31/26: 1,041.2 × 0.59 = **$614.3M** against an FY27 guide midpoint
of $1,305M ⇒ **visibility ≈ 47%**.

That difference is the single most important structural fact distinguishing the two companies, and it
falls directly out of the recognition models: Rubrik's ratable single-performance-obligation bundle puts
almost everything into RPO; Commvault's point-in-time term license does not. **Commvault's forecast
interval must be roughly twice as wide as Rubrik's**, and any model that gives them similar intervals has
a bug.

### Step 3 — Forecast the ARR waterfall per stream

```
ARR_close[s] = ARR_open[s] × GRR[s] × (1 + uplift[s])   (retained + uplift)
             + expansion[s]                              (cross-sell, seat/capacity growth)
             + new_logo[s]                               (the uncertain layer)
             − migration_out[s]                          (e.g. perpetual → subscription cannibalization)
```

Where only NRR is disclosed, collapse the first three retention terms:
`ARR_close = ARR_open × NRR + new_logo`. New-logo ARR is then the residual you must estimate — do it from
the customer-count series where it exists (Rubrik's ≥$100K cohort grew 24% Y/Y), and from job postings
and partner-directory growth where it does not.

Anchor: Commvault's SaaS ARR went $281.045M → $400.157M in FY26, net-new $119.1M, distributed
$25.8M / $28.8M / $28.1M / $36.4M across Q1–Q4 — visibly back-loaded, consistent with the disclosed
seasonality.

### Step 4 — Convert ARR to revenue with an empirically fitted conversion factor

For a **ratable** stream, revenue in a period is approximately the mean of opening and closing ARR
(mid-period convention on net-new), times a factor that absorbs intra-period timing:

```
rev_ratable ≈ k × (ARR_open + ARR_close)/2
```

Fit `k` from history rather than assuming 1.0. Commvault FY26 SaaS: revenue $332.981M against
(281.045 + 400.157)/2 = $340.601M ⇒ **k = 0.9776**. The shortfall from 1.0 is exactly what you would
expect from back-loaded net-new ARR. Refit `k` each year and treat a moving `k` as a signal that
seasonality or the net-new profile has changed.

For a **point-in-time** stream (term license), this method does not work, because revenue is driven by
in-period bookings and duration mix, neither of which is observable. This is the hardest line in
outside-in forecasting and it is exactly the line that caused Commvault's only recent guidance miss
(term license fell from $109.3M in Q1 FY26 to $92.6M in Q2 FY26). Three partial approaches, in order of
preference:

1. **Bound it with the guidance decomposition** (§5). If management guides total revenue and you can
   model every other line, the term-license line is the residual — and you have learned what management
   is assuming.
2. **Ratio to the term-related ARR base**, validated for stability over at least three years before use.
   FY26: term-license revenue $435.324M ÷ mean term-related ARR ((499.053 + 589.137)/2 = $544.095M) =
   **0.800**. One observation is not a stability check. Do not use this ratio until you have three.
3. **Model it as the most volatile component** and let it carry most of the interval width.

### Step 5 — Roll the recognition schedule forward and reconcile

Your model must reproduce the disclosed balance-sheet and RPO figures. Run all three checks every quarter:

```
RPO_end  = RPO_begin + new bookings TCV − revenue recognized from contracted amounts ± FX ± cancellations
cRPO_end = implied by your recognition schedule           vs disclosed % within 12 months
DR_end   = implied by your billing-schedule assumptions   vs disclosed deferred revenue
Billings = revenue + Δ deferred revenue                   (approximation; exact only when all billed in advance)
```

Interpretation of a failed check is diagnostic, not cosmetic:

- **RPO residual > 2–3%** ⇒ the bookings-to-RPO mapping is wrong, usually renewals or co-terms
  double-counted.
- **RPO right, DR wrong** ⇒ billing-term assumptions are wrong (annual vs prepaid multi-year mix), not
  demand.
- **DR right, revenue wrong** ⇒ the recognition split (upfront vs ratable) is wrong, i.e. duration or
  product mix.

The corrected identity when upfront license revenue is billed in installments is
`Rev = Billings − ΔDR + ΔCA`, where CA is contract assets. The naive `Rev = DR_begin + Billings − DR_end`
holds only when everything is billed in advance; NetApp uses it in reverse to approximate billings and
says so explicitly.

### Step 6 — Build the P&L by stream, not by blended margin

See `profit-levers.md` §D. The two lines that matter most for cash are Δ deferred revenue and SBC; capex
is noise at 0.6% of revenue unless the vendor moves off hyperscalers.

### Step 7 — Simulate, score, and state the interval

Run `engine/dpforecast.py`. The uncertainty budget for an outside-in forecast decomposes into:

| Source | Typical share of variance | How to size it |
|---|---|---|
| New-logo/expansion ARR | Largest | From the historical dispersion of net-new ARR at the same fiscal quarter |
| Point-in-time license timing and duration mix | Large for term-license vendors, ~zero for ratable ones | From the historical quarter-over-quarter volatility of that line |
| FX | 2–3 pts of growth | From disclosed cc restatements |
| Retention | Small in year 1, dominant in terminal value | From the GRR assumption range |
| Consumption overage | Small | From the disclosed consumption share |

---

## 4. Estimating the unobservables

**Gross retention.** Not disclosed by any public vendor in the category. Bound it: NRR = GRR + expansion,
and expansion cannot plausibly exceed the growth of the same-customer cohort's product attach. With NRR
at 120–122% and enterprise sales-led private-company median GRR at 88% (Benchmarkit CY2025, with the
$50–100K ACV cohort at 91%), a range of **90–93%** is defensible for enterprise data protection. Carry it
as a stated range, not a point, and note that it barely affects year 1 while it dominates terminal value
(GRR 92% ⇒ 5.56× ARR; GRR 88% ⇒ 4.55×, a 22% spread).

**New-logo ARR.** Residual of the waterfall. Cross-check against the customer-count series where
disclosed: if the ≥$100K cohort grew 24% and total subscription ARR grew 32%, the difference is expansion
within existing large customers plus growth in the sub-$100K tail.

**Sales capacity.** No vendor discloses rep counts. Quota-carrying job postings are the best-evidenced
external proxy — postings predict one-year-ahead growth in headcount, SG&A, sales and earnings
([Gutierrez, Lourie, Nekrasov & Shevlin, *Management Science*](https://doi.org/10.1287/mnsc.2019.3450)) —
with the caveat that you must separate growth hiring from replacement hiring.

**Bookings.** Invert the RPO identity: `new bookings TCV ≈ ΔRPO + revenue recognized from contracted
amounts`. This is noisy because of FX, cancellations, and the fact that RPO excludes cancellable
arrangements, but it is directionally usable and it is the only bookings signal available externally.

---

## 5. Decomposing guidance — a worked example

Outside-in forecasting is at its most valuable when you use your own model to work out *what management
must be assuming*. Commvault's FY27 guidance (issued 28 Apr 2026, on recast definitions): total revenue
**$1,300–1,310M**, midpoint $1,305M.

Build up every line you can model, and take the term-license line as the residual:

| Line | FY26 actual | FY27 method | FY27 estimate |
|---|---|---|---|
| SaaS | 332.981 | Net-new SaaS ARR $119.1M × 1.10 = $131.0M ⇒ exit ARR $531.2M; revenue = 0.9776 × mean(400.157, 531.2) | **455.4** |
| Perpetual license | 43.212 | Continue the −22% decay at −20% | **34.6** |
| Other services | 51.747 | +10% | **56.9** |
| Customer support | 320.426 | +3% | **330.0** |
| **Term-based license** | 435.324 | **residual** = 1,305 − 455.4 − 34.6 − 56.9 − 330.0 | **428.1** |

**The guidance implies term-license revenue of roughly $428M, or −1.7% year over year.** That is the
whole story of the guide: management is assuming the point-in-time license line stops growing while SaaS
carries everything. It is consistent with the disclosed mix shift, with the Q2 FY26 term-license decline,
and with the arithmetic in `profit-levers.md` §C row 8 — and it is a far more useful output than "revenue
will be $1.3B," because it is a falsifiable statement you can track quarter by quarter.

**Sensitivity of the conclusion.** The residual absorbs every error in the other four lines. Move support
growth from +3% to +5% and the implied term license falls to $421.7M (−3.1% Y/Y); move it to +1% and the
implied line rises to $434.5M (−0.2% Y/Y). State the range, not the point.

---

## 6. Model the guidance realization ratio — do not take guidance at face value

Vendors sandbag, and they sandbag with remarkable consistency. Fit the ratio of actual to guidance
midpoint over the available history and use it as a multiplicative correction with its own dispersion.

**Rubrik, quarterly total revenue, actual ÷ guidance midpoint:**

| Quarter | Guide midpoint | Actual | Ratio |
|---|---|---|---|
| Q1 FY26 | 260 | 278.5 | 1.0712 |
| Q2 FY26 | 282 | 309.9 | 1.0989 |
| Q3 FY26 | 320 | 350.2 | 1.0944 |
| Q4 FY26 | 342 | 377.7 | 1.1044 |
| Q1 FY27 | 366 | 387.1 | 1.0576 |

Mean **1.0853**, standard deviation **0.0201**. Rubrik has beaten its quarterly revenue guide by
5.8–10.4% in five consecutive quarters. **A forecaster who adopts guidance as the median will
systematically under-forecast Rubrik by roughly 8–9%, every quarter.** The correct treatment is
`revenue ~ guidance_midpoint × Normal(1.085, 0.020)`, refitted each quarter, with an explicit note that
the ratio itself can regime-shift when a company decides to guide more aggressively.

**Commvault, same construction:**

| Quarter | Guide midpoint | Actual | Ratio |
|---|---|---|---|
| Q3 FY25 | 245 | 262.6 | 1.0718 |
| Q4 FY25 | 262 | 275.0 | 1.0496 |
| Q1 FY26 | 268 | 282.0 | 1.0522 |
| Q2 FY26 | 273 | 276.2 | 1.0117 |
| Q3 FY26 | 299 | 313.8 | 1.0495 |
| Q4 FY26 | 306.5 | 311.7 | 1.0170 |

Mean **1.0420**, standard deviation **0.0225**. Smaller and noisier beats than Rubrik — consistent with
the lower visibility ratio from §2. Note that the two smallest beats (Q2 FY26, Q4 FY26) bracket the
restructuring period and the quarter with the subscription-revenue miss; realization ratios are not
stationary across strategy changes.

Two disciplines apply. First, the ratio must be fitted on the **initial** guide for the period, not on a
raised guide, and you must be consistent about which. Second, treat any guidance-philosophy change (new
CFO, first year post-IPO, a change in what is guided) as a structural break and reset the window.

---

## 7. Private vendors with near-zero disclosure

Veeam and Cohesity publish an ARR headline every year or two and nothing else. Do not pretend to a
precision you do not have. The honest procedure:

1. **Anchor on the disclosed ARR points and their dates.** Veeam: $1.7B at Sep 2024 (+18% Y/Y);
   ">$2 billion" stated 30 Jun 2026. Cohesity: $1.5B pro forma for FY ending July 2024, never updated.
2. **Compute the implied CAGR between anchors and state it as a band, not a rate.** Veeam's $1.7B →
   ">$2B" over ~21 months implies a lower bound of ~9.6% annualized, but ">$2B" is an unqualified floor
   and the Securiti AI acquisition (closed 11 Dec 2025) contributes an undecomposable amount. The
   defensible statement is "somewhere between roughly 10% and the ~18% last quantified," not a number.
3. **Cross-check with the market share series.** Veeam at 13.6% share of a market growing 8.8%
   half-over-half, with 11.5% sequential growth of its own, is a coherent picture; use IDC's tracker as
   the constraint that keeps the vendor's own claims honest.
4. **Use headcount and partner counts as the growth proxy.** Veeam went from 5,000+ employees across 34+
   countries (2024) to 6,600+ across 60+ (2025) — though the Securiti acquisition brought ~600 of that.
5. **Never impute a public vendor's metrics onto a private one.** Cohesity's disclosed 28% adjusted cash
   EBITDA margin is pro forma for a period before the merger closed, and the "Veritas" revenue pool it
   refers to no longer maps to a single entity after the Arctera carve-out was sold to Cloud Software
   Group.

For a private vendor, the deliverable is a wide interval with an explicit statement of what would narrow
it (an S-1, a new ARR disclosure, an IDC tracker edition) — not a false point estimate.

---

## 8. Seasonality and the fiscal calendar

All three of the anchor vendors have different fiscal year ends (Commvault March, Rubrik January,
Cohesity July), so calendar-quarter comparisons across them are structurally misaligned. Within a vendor:

- **Commvault:** Q3 and Q4 strongest, Q1/Q2 weakest — though FY26 broke the pattern with Q3 > Q4, and Q2
  FY26 declined *sequentially* on the term-license line.
- **Rubrik:** Q4 strongest, Q1 weakest, with clean sequential growth every quarter. Net-new subscription
  ARR is far more seasonal than revenue: a record $115M in Q4 FY26 versus ~$103M in Q1 FY27.

Fit seasonality on the ARR/bookings series, not on the revenue series, for ratable vendors — ratable
revenue smooths the underlying seasonality and will make you think it is smaller than it is.

---

## 9. What not to do

| Don't | Why | Instead |
|---|---|---|
| Extrapolate a revenue growth rate | Ignores mix, duration, and recognition; the two anchor vendors' ARR-to-revenue wedges point in *opposite* directions | Roll the ARR waterfall and recognize it |
| Compare two vendors' ARR | Commvault's includes perpetual-license support; Rubrik's excludes perpetual maintenance | Rebase to a common definition or don't compare |
| Take guidance as the median | Rubrik has beaten by 5.8–10.4% for five straight quarters | Fit the realization ratio (§6) |
| Use TAM × share to size a vendor | The IDC $12.3B market figure is a 2024 vintage and vendor TAM claims are 3× larger | Use the market series as a *constraint* on implied share gain, not as a driver |
| Model data growth as revenue growth | IDC's DataSphere measures data *created*, not stored; dedup, tiering and pricing-model shifts break the link | Use it as a qualitative floor argument |
| Give a ratable and a point-in-time vendor the same interval width | Visibility is 79% vs 47% | Size the interval from the visibility ratio |
| Report a P90 for the total as the sum of segment P90s | Quantiles do not add | Aggregate the simulation draws, then take quantiles |
| Treat a definitional recast as growth | Commvault's subscription line jumped +$202.2M by definition alone | Rebase the entire series first |
