# Forecasting With Order Flow Data

*Scope: the forecaster has internal or near-internal transactional data — CRM, CPQ, order-to-cash,
channel POS, entitlement, product telemetry. Vendors in scope: Veeam, Commvault, Cohesity/Veritas,
Rubrik, Druva, Dell Data Protection, IBM Storage Defender.*

*Compiled 2026-07-27. Every empirical claim carries a source. Values marked as illustrative are
placeholders chosen to make arithmetic legible, not benchmarks.*

---

## 0. The identity chain you are actually forecasting

Every defensible model in this domain is a chain of four distinct quantities. Confusing any two of
them is the dominant source of large errors (see §7).

```
demand signal → pipeline → BOOKINGS (TCV, ACV/ARR) → BILLINGS (invoiced) → REVENUE (ASC 606) → CASH
```

Definitions to fix before modeling:

| Quantity | Definition | Period recognized |
|---|---|---|
| ACV / ARR added | annualized contract value of new/expansion/renewal | booking date |
| TCV | ACV × term years (+ services) | booking date |
| Billings | invoiced amount | per billing schedule (annual, prepaid multi-year) |
| Revenue | ASC 606 performance-obligation satisfaction | mixed: point-in-time license + ratable support/SaaS |

Commvault illustrates why the split matters: term-based software licenses are recognized "upon
shipment or made available for download (point in time)," SaaS and support ratably, with license
standalone selling price set by the **residual approach**
([Commvault 10-Q, Rev Rec tables](https://www.sec.gov/Archives/edgar/data/1169561/000116956126000006/R23.htm)).
Rubrik recognizes an upfront portion of subscription term-based licenses and the remainder ratably
over the support period
([Rubrik FY26 10-K](https://www.sec.gov/Archives/edgar/data/1943896/000194389626000047/rbrk-20260430.htm)).
A single bookings forecast therefore maps to *different* revenue depending on product and duration mix.

---

## 1. Order flow data sources and schemas

### 1.1 CRM opportunity object (Salesforce-style)

Minimum viable fact table. Store **daily snapshots**, not current state (§7.3).

```sql
CREATE TABLE opp_snapshot (
  snapshot_date       date,        -- PK part 1: point-in-time correctness
  opp_id              text,        -- PK part 2
  account_id          text,
  created_date        date,
  stage               text,        -- Discovery..Negotiation/Review, Closed Won/Lost
  forecast_category   text,        -- Pipeline | Best Case | (Most Likely) | Commit | Closed | Omitted
  crm_probability     numeric,     -- stage-default probability (usually miscalibrated)
  close_date          date,        -- salesrep-asserted
  close_date_orig     date,        -- first-ever asserted close date (for slip measurement)
  amount_tcv_local    numeric,
  amount_acv_usd      numeric,     -- ACV at snapshot FX rate AND at plan rate (store both)
  fx_rate_snapshot    numeric,
  fx_rate_plan        numeric,
  term_months         int,         -- 12/36/60; drives TCV<->ACV and 606 split
  billing_schedule    text,        -- annual | prepaid_multiyear | monthly | milestone
  type                text,        -- new | expansion | renewal | co-term_uplift | migration
  product_mix         jsonb,       -- {VDP_advanced: .6, vault_TB: 300, m365_seats: 5000}
  motion              text,        -- direct | partner_led | distributor | marketplace | VCSP
  deal_reg_id         text,        -- links to channel deal registration
  partner_id          text, distributor_id text,
  segment             text,        -- SMB | commercial | enterprise | public_sector
  region text, rep_id text, manager_id text,
  split_pct           numeric,     -- credit splits: SUM over rows must be handled
  competitor          text, incumbent_vendor text,
  discount_pct        numeric, approval_level text
);
```

Non-negotiable derived fields: `days_to_close_asserted`, `stage_age_days`, `n_pushes` (count of
close-date changes to a later date), `amount_changes`, `dq_flags`. Salesforce's standard forecast
categories are Pipeline / Best Case / Commit / Closed / Omitted (plus optional Most Likely), mapped
from stage but **user-overridable without changing stage** — so category and stage carry different
information and must both be kept as features
([Salesforce Forecasts guide](https://resources.docs.salesforce.com/248/latest/en-us/sfdc/pdf/forecasts.pdf)).

### 1.2 Two-tier channel: sell-in, sell-through, deal registration, inventory, rebates

This sector is overwhelmingly indirect: Commvault reports ~90% of revenue through indirect channels,
with a single distribution partner at ~32% of total revenue
([Commvault 10-Q MD&A](https://www.sec.gov/Archives/edgar/data/1169561/000116956126000006/cvlt-20251231.htm)).
Veeam sells effectively 100% through the ProPartner Network with distributor-mediated fulfillment and
deal-registration discounts (reported at 25% for Veeam Data Cloud and 15% for other products in the
2025 program, [IT Europa](https://www.iteuropa.com/news/veeam-partners-promised-golden-goose-data-protection-channel);
program mechanics in the [ProPartner overview](https://techdataukinfo.co.uk/landingpages/JAN098-16_Veeam_training/Veeam_ProPartner_Program_Program%20overview_2016.pdf)).

Three separate clocks, which you must model separately:

```
t0  deal_reg submitted (lead time indicator; 15+ days before expected close in typical programs)
t1  end-user PO to reseller
t2  reseller PO to distributor  -> distributor PO to vendor = SELL-IN (vendor booking/billing)
t3  distributor POS report      = SELL-THROUGH (weekly/monthly, lagged 1-4 weeks)
```

For pure-software data protection, sell-in and sell-through are usually near-simultaneous (license
keys are not stocked), so channel inventory is small; for appliance-attached business (Rubrik-branded
appliances historically, Cohesity/Dell hardware) it is not.

```sql
CREATE TABLE pos_line (            -- distributor point-of-sale feed
  pos_report_date date, distributor_id text, reseller_id text,
  end_customer_name_raw text, end_customer_id_matched text,
  sku text, qty numeric, ext_price_usd numeric,
  vendor_order_id text,           -- ties POS back to sell-in order
  deal_reg_id text, invoice_date date, ship_date date);

CREATE TABLE channel_inventory (   -- weekly distributor stock report
  as_of date, distributor_id text, sku text, qty_on_hand numeric, weeks_of_supply numeric);

CREATE TABLE rebate_accrual (      -- VIR / MDF / backend rebates = variable consideration
  period date, partner_id text, program text,     -- VIR tier, growth accelerator, MDF
  attainment_pct numeric, accrual_rate numeric, accrued_usd numeric, paid_usd numeric);
```

Rebates and VIRs are **variable consideration** under ASC 606: the transaction price includes
estimated rebates only to the extent a significant revenue reversal is not probable, estimated at
inception and re-assessed each reporting date
([PwC Revenue guide 4.3](https://viewpoint.pwc.com/dt/us/en/pwc/accounting_guides/revenue_from_contrac/revenue_from_contrac_US/chapter_4_determinin_US/43variable_considera_US.html)).
Forecast implication: gross bookings and *net* revenue diverge when partner attainment moves across
VIR tiers, most often in Q4. Model net revenue as `gross_sellin × (1 − r̂_rebate)` with `r̂` a
partner-tier-weighted rate, and back-test `r̂` against the actual accrual true-ups.

Lag structure. Let `POS_t` be weekly sell-through and `SI_t` sell-in. Fit a small distributed-lag
model to convert POS into vendor revenue expectation, and to detect stuffing:

```python
import numpy as np
def dlag_fit(y, x, lags=6):                     # y=sell-in, x=POS
    X = np.column_stack([np.ones(len(y)-lags)] +
                        [x[lags-k:len(x)-k] for k in range(lags+1)])
    beta, *_ = np.linalg.lstsq(X, y[lags:], rcond=None)
    return beta                                 # beta[1:] = lag weights
```

A rising ratio `cum(SI)/cum(POS)` with rising `weeks_of_supply` is the quantitative signature of
channel loading; treat it as a *negative* leading indicator for next-quarter sell-in.

### 1.3 Renewal calendar / installed-base entitlement

For Veeam-class vendors the renewal book is the single largest and most predictable order-flow
component; Veeam reported enterprise gross retention ~95% and net retention ~125% exiting 2024
([CRN interview with CEO](https://www.crn.com/news/storage/2025/veeam-ceo-on-expanding-microsoft-ai-relationship-microsoft-s-veeam-investment-and-ipo));
Rubrik reported ~120% average subscription dollar-based net retention as of April 30, 2026
([FY26 10-K](https://www.sec.gov/Archives/edgar/data/1943896/000194389626000047/rbrk-20260430.htm)).

```sql
CREATE TABLE entitlement (
  contract_id text, account_id text, product_family text,
  start_date date, end_date date, term_months int,
  acv_usd numeric, auto_renew boolean, notice_days int,
  coterm_parent_id text,           -- co-termed add-ons roll into parent end_date
  licensed_units numeric, unit_type text,  -- instances/VUL, TB, seats, front-end TB
  support_tier text, price_uplift_pct numeric, partner_of_record text);
```

Renewal forecast per contract: `E[renewal_ACV] = ACV × p_renew(features) × E[uplift | renew]`, where
`p_renew` is fitted on the same-quarter cohort of expiring contracts (features: size, tenure, product,
partner incumbency, support-ticket volume, usage trend, prior expansion). Co-terming is a trap: a
mid-term add-on that co-terms into a parent contract creates a **partial-year** booking, so ACV added
≠ TCV/term for that order.

### 1.4 Consumption telemetry

For consumption-priced offerings (cloud vault storage, BaaS, per-TB protected), bookings ≠ revenue:
Commvault recognizes usage/consumption arrangements "as the services are consumed," and includes only
the fixed commitment portion in ARR
([Commvault Q4 FY26 release](https://www.commvault.com/news/commvault-announces-fourth-quarter-fiscal-2026-financial-results)).

```sql
CREATE TABLE usage_daily (
  usage_date date, account_id text, subscription_id text, sku text,
  protected_tb numeric, stored_tb_logical numeric, stored_tb_after_dedup numeric,
  vm_count int, workload_count int, m365_seats int, egress_gb numeric,
  committed_units numeric, overage_units numeric, credit_balance numeric);
```

Forecast consumption revenue as `Σ_accounts max(commit_draw, metered)` with a per-account growth model
on `stored_tb_after_dedup` (typically smooth, log-linear, seasonally weak) plus a discrete term for
onboarding cohorts. Commit burn-down rate is the key state variable: accounts under-consuming their
commit generate *no incremental* revenue upside but do generate renewal downgrade risk.

### 1.5 Quote/CPQ and order-to-cash

`quote(quote_id, opp_id, created_ts, version, list_total, net_total, discount_pct, approval_state,
expires_on)` — quote creation is a high-value, hard-to-game leading indicator (a rep cannot fabricate
a quote with an approved non-standard discount).
`order(order_id, opp_id, booked_ts, tcv, term, billing_schedule, po_number, license_keys_issued_ts,
provisioned_ts, backlog_flag)`. Backlog = booked but not yet delivered/provisioned; for software it is
small but non-zero (delayed key issuance, pending tenant provisioning, hardware-attached SKUs).
Revenue timing depends on `license_keys_issued_ts` / `provisioned_ts`, **not** `booked_ts`.

### 1.6 Product-led and web signals

Veeam Community Edition (free, capped at 10 workloads) and trial downloads create a measurable
top-of-funnel: `download(ts, email_domain, edition, product, geo)`,
`trial(start_ts, license_expiry, workloads_protected, converted_opp_id)`, plus support-portal
entitlement lookups. Model conversion as a cohort curve (`P(paid order within h days | download
cohort)`), fit separately by firmographic tier — domain-matched enterprise downloads convert at
materially different rates than consumer/lab downloads. These series matter most for SMB/run-rate and
for the "unmodeled tail" in §4.

---

## 2. Pipeline conversion modeling

### 2.1 Stage-based vs. cohort/time-based conversion

**Stage-based (snapshot) model.** For open pipeline at snapshot date `s` with quarter-end `T`:

```
B_modeled = Σ_i A_i · p_i^win · p_i^in-quarter · m_i
```

where `A_i` = CRM amount, `p_win` = calibrated win probability, `p_in-quarter` = P(closes by `T` |
wins), `m` = amount realization multiplier (`realized/CRM amount`, typically <1 because of quarter-end
discounting; Larkin measured average realized discounts of 34.8% off list with "pulled" deals
discounted ~6 points *more* than timing-indifferent deals,
[Larkin 2014](https://www.hbs.edu/ris/Publication%20Files/13-073_cbb24c28-9e84-47d9-8a32-f01b73cfda13.pdf)).

**Cohort model.** Independent and complementary: pipeline *created* in week `t` converts over horizon
`h`. Fit `C(h) = E[won$ within h days] / created$`. This avoids stage-hygiene contamination entirely
because creation is timestamped and hard to backdate. Use it to forecast quarters 2–4 out, where
today's open pipeline is not yet the binding constraint.

```python
import pandas as pd, numpy as np

def stage_conversion_from_snapshots(snap: pd.DataFrame, horizon_days=90):
    """snap: snapshot_date, opp_id, stage, amount_acv_usd, outcome, outcome_date.
       Returns empirical P(win within horizon) by stage - point-in-time correct."""
    s = snap.copy()
    s['won_in_h'] = ((s.outcome == 'won') &
                     ((s.outcome_date - s.snapshot_date).dt.days <= horizon_days)).astype(int)
    g = s.groupby('stage').agg(n=('opp_id', 'size'), p=('won_in_h', 'mean'),
                               dollar_w=('amount_acv_usd', 'sum'))
    g['p_dollar'] = (s.assign(w=s.won_in_h * s.amount_acv_usd)
                      .groupby('stage').w.sum() / g.dollar_w)
    return g   # always report BOTH unit-weighted and dollar-weighted conversion
```

Always compute dollar-weighted conversion: unit win rates and dollar win rates diverge because large
deals convert at lower rates and slip more.

### 2.2 Hazard / survival with competing risks

A deal has three exits: won, lost, still-open-and-slipped. Model as discrete-time competing risks.
Let `k` index weeks since snapshot:

```
h_k^win  = P(win in week k  | open at k)
h_k^lose = P(lose in week k | open at k)
S_k      = Π_{j<k} (1 − h_j^win − h_j^lose)
P(win by K) = Σ_{k≤K} S_k · h_k^win
```

Fit with a multinomial logit on person-period rows (one row per open deal per week) — the
discrete-time analogue of a cause-specific hazard model, which handles time-varying covariates
(stage, days-in-stage, quote issued, exec engaged, day-of-quarter) naturally. For direct modeling of
the cumulative incidence of "won," use the Fine–Gray subdistribution hazard
([Fine & Gray 1999](https://doi.org/10.1080/01621459.1999.10474144)).

```python
from sklearn.linear_model import LogisticRegression
def expand_person_period(open_deals, weeks=13):
    rows = []
    for d in open_deals.itertuples():
        for k in range(1, weeks + 1):
            rows.append(dict(opp_id=d.opp_id, k=k, stage=d.stage, log_amt=np.log(d.amount_acv_usd),
                             dow_q=d.day_of_quarter + 7 * k, days_in_stage=d.days_in_stage + 7 * k))
    return pd.DataFrame(rows)
# label each row: 1 win / 2 loss / 0 survive in that week; fit multinomial, then chain hazards
```

Day-of-quarter must enter the hazard as a covariate, otherwise the model will not reproduce the
quarter-end spike (§2.5).

### 2.3 Coverage ratio: calibrate, do not assume

The "3× coverage" heuristic is folklore. **Flag as rule of thumb — no primary source.** The defensible
version is the identity: required coverage = 1 / (dollar-weighted conversion of the pipeline you
actually hold, at the snapshot date and stage mix you actually have).

The best publicly available empirical anchor is the Ebsta × Pavilion GTM Benchmarks, built from
~655,000 real CRM opportunities (~$48B pipeline): average B2B win rate **19% in the 2025 report, down
from 29% in 2024** — arithmetically implying ~5.3× coverage at that win rate
([report PDF](https://www.joinpavilion.com/hubfs/Ebsta%20x%20Pavilion%202025%20GTM%20Benchmarks%20Report.pdf);
[summary](https://www.saasletter.com/p/ebsta-2025-gtm-benchmarks)). Caveats: cross-industry,
self-selected sample of Ebsta customers, opportunity-count-weighted, and the year-over-year drop is
large enough that measurement changes cannot be excluded. Use it as a sanity band, not as your prior.
The same source reports expansion deals closing in ~52 days vs ~91 for new logos — motivating separate
conversion models per `type`.

```
Coverage_required = Q_target / Σ_i A_i = 1 / c̄
c̄ = Σ_i A_i · p_i^win · p_i^inq · m_i / Σ_i A_i
```

Track `c̄` weekly. A stable coverage ratio with deteriorating `c̄` (aging, stage-stuffed pipeline) is a
miss in progress.

### 2.4 Pipeline hygiene pathologies and detection

| Pathology | Signature in snapshot data | Correction |
|---|---|---|
| Stage inflation | stage advanced without quote/CPQ record, no exec contact, `days_in_stage` low but stage high | fit win model on *observable* evidence (quote, deal-reg, security review) not stage; recalibrate stage probabilities (§3.4) |
| Sandbagging | rep's Commit realization systematically >1.0; deals closing that were in "Pipeline" 7 days prior | rep-level realization multiplier with shrinkage (§3.2) |
| Push / slip | `close_date > close_date_orig`; count `n_pushes` | slip hazard model; Ebsta reports late-stage slippage past two months associated with sharply lower win rates |
| Date-stuffing at quarter end | mass of `close_date` on the final 1–2 days; close-date changes clustered in the last week | model `p_in-quarter` from the *hazard*, ignore asserted close date except as a feature |
| Zombie deals | open, no field changes for >2× median stage duration | auto-decay `p_win` toward the "stale" empirical rate; do not delete (destroys backtest) |

Quantify slip with a transition matrix estimated from consecutive snapshots:
`P(quarter-of-close_{t+1} | quarter-of-close_t)`.

### 2.5 Quarter-end linearity and the intra-quarter pace model

The strongest sourced evidence on enterprise-software linearity: in Larkin's dataset of 7,912 deals
over 28 quarters at a major enterprise software vendor, **67% of deals closed on the final day of the
fiscal quarter**, 4% elsewhere in the final week, 21% across the middle eleven weeks, and 8% in the
first two weeks
([Larkin 2014, Table 2](https://www.hbs.edu/ris/Publication%20Files/13-073_cbb24c28-9e84-47d9-8a32-f01b73cfda13.pdf)).
This is one vendor with ~$550k average deal size and an accelerating commission scheme, so treat 67%
as an upper bound rather than a sector norm — but the mechanism is general and pre-dates SaaS: Oyer
showed fiscal-year-end revenue spikes and beginning-of-year troughs driven by non-linear incentive
contracts ([Oyer 1998, QJE](https://doi.org/10.1162/003355398555559)).

Pace ("day-of-quarter completion curve") model. Let `g(t) = E[C_t / Q]` where `C_t` = cumulative
closed-won at day `t` and `Q` = final quarter bookings. Estimate `g` from ≥8 prior quarters using
**day-of-quarter indexing** (align on business-day index, not calendar date, and handle 4-5-4 /
13-week fiscal calendars and the 14-week quarter). Then:

```
Q̂_t = C_t / ĝ(t)
log Q̂_t ~ Normal( log C_t − log ĝ(t), σ_t² )
```

with `σ_t` decreasing in `t` (estimated from historical residuals). Fit `g` separately for run-rate
and enterprise segments — the run-rate curve is nearly linear, the enterprise curve is convex and
back-loaded, and averaging them produces a curve that fits neither.

### 2.6 Deal-size stratification

Split the book at a size threshold where the strata differ statistically (test with a
Kolmogorov–Smirnov comparison of conversion and slip distributions, not a round number).

- **Run-rate / transactional** (high N, low variance, partner-fulfilled, short cycle): forecast in
  aggregate with a pace + cohort model. Poisson-gamma or log-normal aggregate; deal-level simulation
  adds nothing.
- **Enterprise / strategic** (low N, lumpy, 6–12 month cycles, exec-sponsored): forecast deal-by-deal
  with named-deal probabilities, and simulate (§4). A handful of $5M+ TCV deals can swing a quarter by
  more than the entire modeling error of the run-rate book.

Rubrik notes contracts are generally three years with the *majority* of new business sold as
three-year terms paid upfront, renewing on one-year terms — this makes large-deal duration a
first-order driver of both revenue and cash
([FY26 10-K](https://www.sec.gov/Archives/edgar/data/1943896/000194389626000047/rbrk-20260430.htm)).

---

## 3. Judgmental forecast calibration

### 3.1 Realization rates by forecast category and entity

Define realization for entity `e` (rep/region/segment) and category `c`:

```
r_{e,c} = actual closed-won $ in quarter from deals in (e,c) at lock date
          ÷ submitted $ in (e,c) at lock date
```

Always compute from the **forecast-lock snapshot** (a fixed day-of-quarter, e.g. day 15), never from
end-of-quarter state. Then the calibrated judgmental forecast is `B̂_judg = Σ_c r̂_c · V_c`.

Worked example (illustrative values, not benchmarks): Commit $12.0M × 0.93 + Best Case $8.0M × 0.55 +
Pipeline $26.0M × 0.14 = **$19.2M**. Realization above 1.0 in Commit is common where reps sandbag;
realization is a *ratio*, not a probability, because in-quarter net-new deals land in the numerator.

### 3.2 Bias correction and shrinkage for low-N entities

Rep-level realization is estimated from a handful of quarters and is dominated by noise. Use
empirical-Bayes / hierarchical partial pooling:

```
r̂_e^EB = w_e · r_e + (1 − w_e) · r̄
w_e     = n_e / (n_e + σ²_within / τ²_between)
```

where `τ²` is the between-rep variance of true realization and `σ²` the within-rep sampling variance
(both estimable by method of moments from the panel).

```python
def eb_shrink(r, n, r_pool, sig2_within, tau2_between):
    w = n / (n + sig2_within / tau2_between)
    return w * r + (1 - w) * r_pool, w

# tau2=0.04, sig2=0.09, pool mean 0.85
eb_shrink(1.30,  6, 0.85, 0.09, 0.04)   # -> (1.177, 0.727)
eb_shrink(1.30, 25, 0.85, 0.09, 0.04)   # -> (1.263, 0.917)
eb_shrink(0.40,  6, 0.85, 0.09, 0.04)   # -> (0.523, 0.727)
```

Verified output: a rep with 6 observations and raw realization 1.30 shrinks to **1.177**; with 25
observations, to **1.263**. Fit the hierarchy at three levels (rep ⊂ manager ⊂ region) so a new rep
inherits their team's prior. Correct *level* bias only where it is statistically detectable and stable
across at least 4–6 quarters; ephemeral optimism should be absorbed by the shrinkage, not modeled.

### 3.3 Combining judgmental and statistical forecasts

```
B̂_pool = α · B̂_judg + (1 − α) · B̂_model + β_0
```

Estimate `α` by constrained least squares (or ridge) on ≥12 historical quarters of *lock-date*
forecast pairs. Expect `α` unstable and the equal-weight combination hard to beat — the classic
forecast-combination puzzle: simple combinations that ignore error correlations frequently dominate
estimated-optimal weights because weight estimation error swamps the theoretical gain
([Timmermann, *Forecast Combinations*](https://ideas.repec.org/h/eee/ecofch/1-04.html);
[Bates & Granger via Stock & Watson](https://www.princeton.edu/~mwatson/papers/Stock_Watson_HOF_2006.pdf)).
Default: `α = 0.5` with a bias intercept; upgrade to estimated weights only when you have ≥16 quarters
and a documented accuracy gap.

For **distributional** pooling, use vincentization (quantile averaging) rather than mixture-of-densities:
mixtures are over-dispersed, quantile averages are not.

### 3.4 Scoring and recalibration

Score deal-level probabilities and quarter-level distributions with strictly proper rules
([Gneiting & Raftery 2007](https://doi.org/10.1198/016214506000001437)):

- Deal-level win probability: **Brier score** `(p − y)²`, plus a reliability curve of observed win
  rate vs predicted decile.
- Quarter distribution: **pinball loss** at quantiles τ, `L_τ(q,y) = max(τ(y−q), (τ−1)(y−q))`, and
  **CRPS**, `CRPS(F,y) = ∫ (F(x) − 1{x≥y})² dx`. Sample-based CRPS from a Monte Carlo ensemble uses
  the energy form `E|X−y| − ½E|X−X'|`.

```python
import numpy as np
def pinball(q, y, tau):     return np.maximum(tau*(y-q), (tau-1)*(y-q))
def crps_ensemble(x, y):    # x: MC sample of forecast, y: realized scalar
    x = np.sort(np.asarray(x, float)); n = x.size
    t1 = np.abs(x - y).mean()
    t2 = (2.0/(n*n)) * np.sum((2*np.arange(1, n+1) - n - 1) * x)  # = E|X-X'|
    return t1 - 0.5*t2
def brier(p, y):            return np.mean((np.asarray(p)-np.asarray(y))**2)
```

Recalibrate CRM stage probabilities — they are systematically miscalibrated because they are policy
defaults, not estimates. Use **Platt scaling** (logistic on the logit of the raw score) when data are
scarce and the distortion is sigmoidal, **isotonic regression** (pool-adjacent-violators) when you have
thousands of resolved opportunities; isotonic corrects any monotone distortion but overfits on small
samples ([Niculescu-Mizil & Caruana 2005](https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf);
[Zadrozny & Elkan 2002](https://www.cs.columbia.edu/~djhsu/coms4771-f25/handouts/zadrozny2002kdd.pdf)).

```python
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
def recalibrate(raw_p, y, method='isotonic'):
    raw_p = np.clip(np.asarray(raw_p, float), 1e-6, 1-1e-6)
    if method == 'isotonic':
        return IsotonicRegression(out_of_bounds='clip', y_min=0, y_max=1).fit(raw_p, y)
    z = np.log(raw_p/(1-raw_p)).reshape(-1, 1)      # Platt: logistic on logits
    return LogisticRegression().fit(z, y)
```

Fit recalibration on strictly earlier quarters than you evaluate on (§7.3). Deal-level win-propensity
modeling on pipeline data is a documented industrial practice with published methodology; see IBM's
deployed pipeline models ([AAAI 2015](https://ojs.aaai.org/index.php/AAAI/article/view/9455);
[regression approach, arXiv](https://arxiv.org/pdf/1502.06229)).

---

## 4. Monte Carlo over the deal list

### 4.1 Structure

For each open deal `i`: win indicator `W_i ~ Bernoulli(p_i)`, in-quarter timing `T_i ~ Bernoulli(q_i)`
(or a hazard-derived date), amount `A_i · M_i` with `M_i` lognormal (median <1 to capture quarter-end
discounting). Quarter bookings:

```
B = Σ_i W_i · T_i · A_i · M_i   +   U
    \________modeled pipeline________/   \_unmodeled tail_/
```

### 4.2 Correlation is not optional

Independent Bernoullis understate variance badly: the same macro shock, a security-budget freeze, a
competitor's aggressive quarter, or a CFO-level spending pause hits many deals at once. Impose a
one-factor Gaussian copula:

```
Z_i = √ρ · F + √(1−ρ) · ε_i,    F, ε_i ~ N(0,1)
W_i = 1{ Z_i < Φ⁻¹(p_i) }
```

This preserves marginal probabilities exactly while inducing pairwise correlation. Equivalent
alternatives: beta-binomial overdispersion for homogeneous run-rate cohorts (`p ~ Beta(a,b)` drawn once
per simulation), or a hierarchical factor structure with region/segment factors nested under a global
factor.

**Two traps in estimating ρ, both of which the engine handles explicitly.**

*Trap 1 — the latent ρ is not the indicator ρ.* The over-dispersion formula everyone reaches for,
`Var(win count) ≈ n·p·(1−p)·[1 + (n−1)·ρ]`, is written in terms of the correlation of the **win/lose
indicators**. The `ρ` in the copula above is the correlation of the **latent** normals, and it is always
the larger of the two. At `p = 0.30`, a latent `ρ = 0.20` produces an indicator correlation of just
**0.119** (`dpforecast.indicator_correlation`, verified against a 4-million-draw simulation at 0.1185).
Substituting the latent value into the variance formula overstates the spread substantially. Fit in
indicator space, then convert with `latent_rho_from_indicator` before handing the number to the copula —
or skip the algebra entirely and bisect on the simulation with `fit_rho_to_target_sd`.

*Trap 2 — use the effective deal count, not the deal count.* The inflation factor
`√(1 + (n−1)·ρ_indicator)` grows without bound in `n`, because idiosyncratic deal risk diversifies across
a large pipeline while the common factor does not. That makes the copula *more* important on a big
pipeline, not less — the opposite of most people's intuition. But `n` here is the concentration-adjusted
count `n_eff = (Σaᵢ)² / Σaᵢ²`, and with the heavy-tailed deal sizes normal in this category `n_eff` is
typically a third of the raw count. The §4.4 example below has 68 deals and `n_eff = 22.8`.

| Effective deal count | sd inflation at ρ_indicator = 0.12 |
|---|---|
| 10 | 1.44× |
| 23 | 1.91× |
| 50 | 2.62× |
| 200 | 4.99× |

### 4.3 The unmodeled tail

Deals that close in-quarter but do not exist in today's pipeline ("created-and-closed same quarter")
are a large, stable share of run-rate and renewal-adjacent business in this sector. Estimate its
distribution from history at the *same day-of-quarter*: `U_t ~ LogNormal(μ_t, σ_t)`, fitted on ≥8 prior
quarters at day `t`. Fit on the residual `actual − (closed-to-date + realized value of deals open at
day t)`, which is the direct empirical definition of the tail and avoids double counting.

### 4.4 Worked example (executed code, verified output)

```python
import numpy as np
from scipy.stats import norm

N = 20_000
amount = np.concatenate([np.full(8, 1_200_000.0), np.full(60, 120_000.0)])
p_win  = np.concatenate([np.full(8, 0.45),        np.full(60, 0.60)])
p_inq  = np.concatenate([np.full(8, 0.70),        np.full(60, 0.85)])
p_eff  = p_win * p_inq

def simulate(rho, seed=7):
    r = np.random.default_rng(seed)
    thr  = norm.ppf(p_eff)
    f    = r.standard_normal((N, 1))                       # common macro factor
    e    = r.standard_normal((N, amount.size))
    won  = (np.sqrt(rho)*f + np.sqrt(1-rho)*e) < thr
    mult = np.exp(np.log(0.95) + 0.25*r.standard_normal((N, amount.size)))
    modeled = (won * amount * mult).sum(axis=1)
    tail    = np.exp(np.log(2_600_000) + 0.30*r.standard_normal(N))
    return modeled + tail
```

| ρ | mean | sd | P05 | P10 | P25 | P50 | P75 | P90 | P95 | P(B < $8.0M) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.00 | 9.29 | 1.88 | 6.41 | 6.94 | 7.93 | 9.19 | 10.51 | 11.74 | 12.54 | 26.3% |
| 0.20 | 9.31 | 3.30 | 4.35 | 5.16 | 6.82 | 9.04 | 11.54 | 13.82 | 15.19 | 38.1% |

All $ millions, reproduced by `engine/test_dpforecast.py`. Adding a modest common factor (latent
ρ = 0.20, indicator ρ = 0.12) leaves the mean unchanged at ~$9.3M but inflates the standard deviation by
1.76× (1.88 → 3.30) and raises the probability of missing an $8.0M commitment from 26% to 38%.
**Reporting an independent-Bernoulli interval to a CFO is the single most common technical error in
deal-level simulation.**

Note that 1.76× is specific to this pipeline's shape. With 68 deals but `n_eff = 22.8`, §4.2 predicts
1.91× before the realization-multiplier noise dilutes it further. On a flatter, 200-effective-deal
run-rate quarter the same ρ would inflate the sd roughly 5×. Never carry a correlation adjustment across
pipelines of different shape — recompute it.

The expected modeled contribution here is $6.56M and the tail contributes $2.72M on average — 29% of the
forecast comes from business that does not yet exist in CRM, which is why the tail must be modeled
explicitly rather than folded into a fudge factor.

---

## 5. Bookings → revenue bridge (ASC 606)

### 5.1 Recognition patterns by product archetype

| Archetype | Revenue pattern | Primary-source example |
|---|---|---|
| Term license + support | license point-in-time on delivery; support ratable over term | Commvault: term licenses "upon shipment or made available for download (point in time)", SSP by **residual approach** ([R23](https://www.sec.gov/Archives/edgar/data/1169561/000116956126000006/R23.htm)) |
| Hybrid subscription (license + hosted) | may be a **single** PO if not separately identifiable → fully ratable | Rubrik RSC accounted for as one performance obligation ([10-K](https://www.sec.gov/Archives/edgar/data/1943896/000194389626000047/rbrk-20260430.htm)) |
| SaaS / BaaS | ratable from service availability | Commvault, Rubrik (as above) |
| Perpetual + maintenance | license upfront, maintenance ratable (typically 1 yr) | Commvault perpetual license + customer support |
| Consumption | as consumed | Commvault: "recognized as the services are consumed" |

Two rules with outsized forecast impact: (a) renewals of term licenses cannot be recognized before the
renewal period begins (Rubrik states this explicitly), so an early-signed renewal adds RPO and possibly
billings but **no revenue**; (b) the same dollar of ACV produces wildly different current-quarter
revenue depending on whether it lands as term license or SaaS.

### 5.2 Splitting term-license TCV: SSP allocation and duration mix

Relative-SSP allocation: for performance obligations `j` with standalone selling prices `SSP_j`,
allocate `TCV_j = TCV × SSP_j / ΣSSP`. Under the residual approach (observable support renewal rates,
license as residual), for a bundle priced at `P` per year with observable support SSP `s` per year and
term `n` years:

```
License_upfront  = n·P − n·s
Support_ratable  = n·s
```

**Worked example.** Bundle at $120k/yr, support SSP $30k/yr, mid-quarter start (45 of 91 days remaining):

- 3-year deal: TCV $360k → license **$270k upfront**, support $90k over 1,095 days = $82.19/day →
  $3,699 in the booking quarter → **$273,699 recognized**, vs $120k billed. The $153.7k excess creates
  a **contract asset / unbilled receivable**, not deferred revenue.
- 1-year deal: TCV $120k → license $90k upfront + $3,699 support.

**Duration mix with flat ARR** (verified arithmetic): 100 deals of $120k ACV each = $12.0M ACV added in
both scenarios.

| Mix | In-quarter license revenue | ACV added |
|---|---|---|
| 70% three-year / 30% one-year | 70×$270k + 30×$90k = **$21.6M** | $12.0M |
| 40% three-year / 60% one-year | 40×$270k + 60×$90k = **$16.2M** | $12.0M |

A 30-point shift in duration mix moves recognized license revenue **−25%** with *zero* change in ARR.
This is the mechanism behind term-license vendors' revenue volatility and the reason ARR/RPO are the
better demand signals. Rubrik makes the cash-flow analogue explicit: "the mix of annual versus upfront
payment terms on our multi-year contracts" is a primary driver of free cash flow.

### 5.3 Revenue waterfall

```
Rev_q = Rev_q^backlog                                   (from RPO/DR schedule)
      + Σ_new deals [ License_i + Support_i · d_i / D_i ]  (in-quarter contribution of new bookings)
      + Consumption_q
```

where `d_i` = days of service delivered in-quarter and `D_i` = total service days. Implementation:
expand every contract into a daily/monthly recognition schedule once at booking, then the quarter's
revenue is a simple sum over schedules — never a growth rate applied to last quarter's revenue.

```python
import pandas as pd
def schedule(bookings, quarter_start, quarter_end):
    """bookings: booked_date, start_date, term_months, tcv, support_ssp_per_yr, kind"""
    out = []
    for b in bookings.itertuples():
        n_days = int((b.start_date + pd.DateOffset(months=b.term_months) - b.start_date).days)
        support = b.support_ssp_per_yr * b.term_months / 12.0
        license_up = 0.0 if b.kind in ('saas', 'hybrid_single_po') else max(b.tcv - support, 0.0)
        ratable = b.tcv - license_up
        days_in_q = max(0, (min(quarter_end, b.start_date + pd.Timedelta(days=n_days))
                            - max(quarter_start, b.start_date)).days)
        rec_up = license_up if quarter_start <= max(b.booked_date, b.start_date) <= quarter_end else 0.0
        out.append(dict(opp=b.Index, upfront=rec_up, ratable=ratable * days_in_q / n_days))
    return pd.DataFrame(out)
```

### 5.4 Reconciliation identities and their limits

The naive identity holds only when everything is billed in advance:

```
Rev = DR_begin + Billings − DR_end
```

NetApp uses exactly this construction in reverse to *approximate* billings from reported figures:
billings ≈ net revenue + change in total deferred revenue
([NetApp Q2 FY26 release](https://investors.netapp.com/news/news-details/2025/NetApp-Reports-Second-Quarter-of-Fiscal-Year-2026-Results/)).
The corrected identity when upfront license revenue is billed in installments:

```
Rev = Billings − ΔDR + ΔCA          (CA = contract assets)
```

Check against §5.2: $120k billed − $0 ΔDR + $153.7k ΔCA = $273.7k ✓.

**Validation against disclosed metrics.** RPO includes both billed (deferred revenue) and unbilled
contracted amounts. Rubrik disclosed total non-cancellable RPO of ~$2.44B as of April 30, 2026, with
~53% expected to be recognized in the next 12 months (~$1.86B and 52% a year earlier)
([FY26](https://www.sec.gov/Archives/edgar/data/1943896/000194389626000047/rbrk-20260430.htm),
[FY25](https://www.sec.gov/Archives/edgar/data/1943896/000194389625000030/rbrk-20250430.htm)).
Three checks to run every quarter:

1. `RPO_end = RPO_begin + new bookings TCV − revenue recognized from contracted amounts ± FX ±
   cancellations`. Residual >2–3% of RPO means your bookings-to-RPO mapping is wrong (usually renewals
   or co-terms double-counted).
2. `cRPO_end` implied by your recognition schedule vs disclosed cRPO.
3. `DR_end` implied by your billing schedules vs actual DR. DR misses with correct RPO ⇒ billing-term
   assumptions are wrong (annual vs prepaid mix), not demand.

RPO's limits: it excludes cancellable and month-to-month arrangements, excludes usage above
commitments, and its 12-month split is an estimate. Never treat RPO as a hard floor for revenue.

---

## 6. Nowcasting and in-quarter tracking

### 6.1 Weekly flash with day-of-quarter indexing

The only valid comparison is same-business-day-of-quarter across years:

```
Index_t = C_t^this-yr / C_t^same-DOQ-last-yr
Q̂_t     = C_t + R̂_t
```

where `R̂_t` = expected remainder = (modeled open pipeline contribution over remaining days, from the
hazard model) + (unmodeled tail conditional on `t`). Publish both the pace-ratio estimate `C_t/ĝ(t)`
and the bottom-up `C_t + R̂_t`; their divergence is itself a signal (pace above bottom-up ⇒
pull-forward, likely borrowing from next quarter).

### 6.2 Bayesian updating through the quarter

```
log Q ~ N(μ_0, τ²)                              prior: pipeline/deal-list model at day 0
log C_t = log g(t) + log Q + ε_t,  ε_t ~ N(0, σ_t²)
μ_post  = [ μ_0/τ² + (log C_t − log g(t))/σ_t² ] / [ 1/τ² + 1/σ_t² ]
σ²_post = ( τ⁻² + σ_t⁻² )⁻¹
```

**Worked example (verified).** Prior median $11.5M, τ = 0.12; at day 60 `C_60 = $5.10M` with
`g(60) = 0.42` and `σ_60 = 0.18`. Naive pace estimate = $12.14M; posterior median = **$11.69M**, 80%
interval **$10.29M – $13.29M**. The prior pulls the naive estimate down because the pace signal is
noisier than the pipeline model at day 60. `σ_t` must be estimated empirically and collapses sharply
in the final two weeks — under Larkin-like linearity, `g(t)` is nearly flat until the final days, so
pace-based nowcasting has *very low* information content until late in the quarter. **This is the
central practical limitation of nowcasting enterprise software bookings.**

```python
import numpy as np
def bayes_nowcast(C_t, g_t, mu0, tau, sigma_t):
    y  = np.log(C_t) - np.log(g_t)
    v  = 1.0/(1.0/tau**2 + 1.0/sigma_t**2)
    mu = v*(mu0/tau**2 + y/sigma_t**2)
    return np.exp(mu), np.exp(mu - 1.2816*np.sqrt(v)), np.exp(mu + 1.2816*np.sqrt(v))
bayes_nowcast(5.10e6, 0.42, np.log(11.5e6), 0.12, 0.18)
# -> (11_694_091, 10_289_470, 13_290_458)
```

### 6.3 Leading indicators and their lead times

| Indicator | Typical lead | Why it is hard to game |
|---|---|---|
| Deal registration submissions | weeks-to-months (programs require submission a set number of days before close) | requires distributor/vendor approval, ties to end customer |
| Distributor POS / sell-through | trailing 1–4 weeks, leads *next* period sell-in | third-party reported |
| Quote/CPQ volume and non-standard discount approvals | days-to-weeks | approval workflow leaves an audit trail |
| Trial starts / free-edition downloads (Veeam Community Edition, capped at 10 workloads) | months for SMB, longer for enterprise | third-party/product telemetry |
| Support-entitlement lookups, license-key activations | weeks | product telemetry |
| Usage/consumption growth vs commit burn-down | 1–2 quarters for expansion | product telemetry |

Estimate lead times by cross-correlation on weekly series, then **only** use lags where the
relationship survives out-of-sample. Published lead-time estimates for data-protection channel
indicators specifically are thin to nonexistent — fit them on the vendor's own history rather than
importing them.

---

## 7. Failure modes and controls

### 7.1 Data quality

- **Duplicate opportunities**: same account + similar amount + overlapping dates; dedupe by fuzzy key
  and *keep the mapping table* so backtests reproduce.
- **Currency**: store amounts at both snapshot FX and plan FX. Reporting bookings growth at snapshot
  rates and revenue at plan rates produces phantom variance.
- **Split credit**: `split_pct` rows double-count if summed naively; forecast on a de-duplicated
  opportunity grain and allocate to reps only for reporting.
- **Renewals booked as new**: inflates new-business conversion rates and destroys the renewal model.
  Detect by joining opportunity to `entitlement` on account + product + expiring window; a "new" deal
  at an account with a contract expiring within 90 days is almost always a renewal or expansion.
- **Partner-of-record churn**: same end customer appearing under different resellers across renewals
  breaks account-level history unless you resolve on end customer, not partner.
- **Channel-inventory blindness**: sell-in without POS reconciliation lets a quarter be made by loading
  distributors and reverses next quarter.

### 7.2 The single biggest structural error

**Mixing ACV/ARR, TCV, billings, and revenue in one series.** Concretely: `TCV = ACV × term_years`, so a
shift from one-year to three-year terms triples reported TCV bookings with no change in ARR; and a
shift from term license to SaaS collapses in-quarter revenue with no change in ARR (§5.2). Enforce a
single-typed schema: every stored measure carries `measure_type ∈ {acv, arr, tcv, billings, revenue}`
and `fx_basis`, and any aggregation across mismatched types raises an error rather than silently
summing. Vendors' own metric definitions differ — Commvault's ARR includes support attached to
perpetual and term licenses and only the fixed-commitment portion of consumption deals
([Q4 FY26 release](https://www.commvault.com/news/commvault-announces-fourth-quarter-fiscal-2026-financial-results))
— so cross-vendor ARR comparisons need re-basing before use as priors.

### 7.3 Governance: locks, snapshots, and leakage

- **Forecast lock dates**: a fixed day-of-quarter (e.g., day 15 and day 45) at which every submission
  and pipeline state is frozen and archived. Without a lock you cannot measure realization rates,
  because the denominator moves.
- **Daily snapshots are mandatory.** CRM objects are mutated in place: stages, amounts, and close dates
  are overwritten and history objects are often incomplete or purged. Conversion, slip, and calibration
  models require the pipeline *as it appeared* on day `t`. If you have no snapshot history, start
  capturing it today and expect ~8 quarters before hierarchical conversion models are usable.
- **Point-in-time correctness / no leakage.** All features must be computable from data available at
  the snapshot timestamp. Common leaks: using final `amount` instead of snapshot `amount`; using
  `close_date` (which is updated after slips) as a feature; fitting recalibration on quarters that
  overlap the evaluation quarter; using account-level features derived from post-snapshot renewals.
- **Backtest protocol**: rolling-origin evaluation, train on quarters `≤ q−1`, evaluate on `q`, refit
  every quarter; report pinball loss at τ ∈ {0.1, 0.25, 0.5, 0.75, 0.9}, CRPS, and calibration coverage
  (fraction of quarters inside the 80% interval — should be ~0.8, and is usually ~0.5 in practice,
  indicating overconfident intervals).
- **Incentive-aware skepticism**: the timing and pricing of deals are endogenous to compensation
  design. Larkin found gaming-driven mispricing costing 6–8% of revenue, and pulled deals discounted ~6
  points more than timing-indifferent deals. When commission plans, accelerators, or quota-relief rules
  change, **the pace curve `g(t)`, the amount multiplier `m`, and slip rates all change** — treat plan
  changes as structural breaks and reset the estimation window rather than averaging across the break.

---

## Sources

**Primary filings and vendor disclosures**

- Rubrik FY2026 Form 10-K / Q1 FY27 10-Q (revenue recognition, RSC single performance obligation, RPO $2.44B with ~53% in next 12 months, ~120% subscription net retention, three-year terms with upfront payment): https://www.sec.gov/Archives/edgar/data/1943896/000194389626000047/rbrk-20260430.htm
- Rubrik FY2025 Form 10-K (RPO ~$1,857.7M, ~52% in next 12 months): https://www.sec.gov/Archives/edgar/data/1943896/000194389625000030/rbrk-20250430.htm
- Commvault Form 10-Q (Dec 31, 2025) — performance obligation table, term license point-in-time, residual approach for SSP; ~90% indirect revenue; Partner A ~32% of revenue: https://www.sec.gov/Archives/edgar/data/1169561/000116956126000006/cvlt-20251231.htm and https://www.sec.gov/Archives/edgar/data/1169561/000116956126000006/R23.htm
- Commvault revenue disaggregation detail: https://www.sec.gov/Archives/edgar/data/1169561/000116956126000017/R29.htm
- Commvault SEC comment-letter response on disaggregating term license vs SaaS revenue: https://ir.commvault.com/static-files/3e02ca3c-d988-4a76-80af-8957b5e9acbd
- Commvault Q4 FY2026 results (ARR definition incl. support and fixed consumption commitments): https://www.commvault.com/news/commvault-announces-fourth-quarter-fiscal-2026-financial-results
- NetApp Q2 FY2026 results (billings ≈ revenue + change in deferred revenue): https://investors.netapp.com/news/news-details/2025/NetApp-Reports-Second-Quarter-of-Fiscal-Year-2026-Results/
- Pure Storage FY2026 Form 10-K (two-tier distribution; late-in-quarter revenue timing risk): https://www.sec.gov/Archives/edgar/data/1474432/000147443226000027/pstg-20260201.htm
- Veeam $1.7B ARR / $15B valuation announcement (Sept 2024 ARR, 18% YoY, 31% subscription growth): https://www.businesswire.com/news/home/20241204720183/en/Veeam-the-Worlds-1-Leader-in-Data-Resilience-Welcomes-New-Investors-with-a-15-Billion-Valuation
- Veeam CEO interview (>$1.74B ARR FY2024; enterprise gross retention ~95%, net retention ~125%): https://www.crn.com/news/storage/2025/veeam-ceo-on-expanding-microsoft-ai-relationship-microsoft-s-veeam-investment-and-ipo
- Veeam ProPartner program overview (deal registration, tiers, distributor-only fulfillment): https://techdataukinfo.co.uk/landingpages/JAN098-16_Veeam_training/Veeam_ProPartner_Program_Program%20overview_2016.pdf
- Veeam 2025 partner program / deal-reg discounts (25% VDC, 15% other): https://www.iteuropa.com/news/veeam-partners-promised-golden-goose-data-protection-channel
- Salesforce Collaborative Forecasts guide (forecast categories; stage→category mapping): https://resources.docs.salesforce.com/248/latest/en-us/sfdc/pdf/forecasts.pdf
- PwC Revenue guide §4.3, variable consideration and rebates (channel VIR/MDF accounting): https://viewpoint.pwc.com/dt/us/en/pwc/accounting_guides/revenue_from_contrac/revenue_from_contrac_US/chapter_4_determinin_US/43variable_considera_US.html

**Academic and methodological**

- Larkin, I. (2014), "The Cost of High-Powered Incentives: Employee Gaming in Enterprise Software Sales," *Journal of Labor Economics* 32(2) — 67% of 7,912 deals closed on the last day of the quarter; 6–8% of revenue lost to timing-driven mispricing: https://www.hbs.edu/ris/Publication%20Files/13-073_cbb24c28-9e84-47d9-8a32-f01b73cfda13.pdf
- Oyer, P. (1998), "Fiscal Year Ends and Nonlinear Incentive Contracts," *QJE* 113(1): https://doi.org/10.1162/003355398555559
- Gneiting, T. & Raftery, A. (2007), "Strictly Proper Scoring Rules, Prediction, and Estimation," *JASA* 102(477): https://doi.org/10.1198/016214506000001437
- Zadrozny, B. & Elkan, C. (2002), "Transforming Classifier Scores into Accurate Multiclass Probability Estimates": https://www.cs.columbia.edu/~djhsu/coms4771-f25/handouts/zadrozny2002kdd.pdf
- Niculescu-Mizil, A. & Caruana, R. (2005), "Predicting Good Probabilities With Supervised Learning": https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf
- Fine, J. & Gray, R. (1999), "A Proportional Hazards Model for the Subdistribution of a Competing Risk," *JASA* 94(446): https://doi.org/10.1080/01621459.1999.10474144
- Timmermann, A. (2006), "Forecast Combinations," *Handbook of Economic Forecasting* ch. 4: https://ideas.repec.org/h/eee/ecofch/1-04.html
- Stock, J. & Watson, M. (2006), "Forecasting with Many Predictors": https://www.princeton.edu/~mwatson/papers/Stock_Watson_HOF_2006.pdf
- Yan, J. et al. (2015), "On Machine Learning towards Predictive Sales Pipeline Analytics," AAAI: https://ojs.aaai.org/index.php/AAAI/article/view/9455
- IBM Research, "Sales pipeline win propensity prediction: a regression approach": https://arxiv.org/pdf/1502.06229

**Benchmark reports (secondary; sample-selection caveats apply)**

- Ebsta × Pavilion 2025 GTM Benchmarks (655K opportunities, ~$48B pipeline; 19% average win rate vs 29% prior year; expansion 52-day vs new-logo 91-day cycles): https://www.joinpavilion.com/hubfs/Ebsta%20x%20Pavilion%202025%20GTM%20Benchmarks%20Report.pdf
- Commentary deriving ~5.3× implied coverage from a 19% win rate: https://www.saasletter.com/p/ebsta-2025-gtm-benchmarks

**Explicitly flagged as rules of thumb with no primary source** (fit per vendor, do not assume): 3×
pipeline coverage; the illustrative `g(60) = 0.42` pace value and `σ_t` in §6.2; the shrinkage variance
components (`τ² = 0.04`, `σ² = 0.09`); realization rates (0.93 / 0.55 / 0.14); amount-multiplier
parameters (median 0.95, σ = 0.25); correlation ρ = 0.20; and the tail parameters in §4.4. **Literature
is genuinely thin** on published day-of-quarter completion curves for software bookings (Larkin's
single-vendor distribution is the best public evidence found), on deal-correlation (ρ) estimates for
B2B pipelines, and on lead-time estimates for channel indicators in data protection specifically.
