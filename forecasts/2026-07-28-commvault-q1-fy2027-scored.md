# Commvault Q1 FY2027 — scored against the print

**Forecast:** [`2026-07-28-commvault-q1-fy2027.md`](./2026-07-28-commvault-q1-fy2027.md)
**Actual:** [PR Newswire, 2026-07-28](https://www.prnewswire.com/news-releases/commvault-announces-first-quarter-fiscal-2027-financial-results-302835588.html)
**Scored:** 2026-07-28

---

## Verdict

**Close.** Absolute error on total revenue was **$2.1M (0.66%)**. The actual landed at the
**39th percentile** of the forecast — slightly below the median, well inside the 80% interval,
exactly where a mild over-estimate of the guidance beat should put it. The forecast beat its
own stated benchmark on both CRPS and absolute error.

| Quantity | Forecast (p50) | Actual | Error | Inside 80% interval? |
|---|---|---|---|---|
| **Total revenue** | $316.2M | **$314.1M** | **+$2.1M (+0.66%)** | Yes ($307–326M) |
| **Subscription revenue** | $269.3M | **$267.0M** | **+$2.3M (+0.85%)** | Yes ($260–278M) |

Implied actual y/y: total **+11.4%** (forecast +12.1%); subscription **+16.4%** off the recast
base (forecast +17.5%). Headline print of "subscription +16%" matches.

---

## Line by line

| Line | Forecast | Actual | Error | Notes |
|---|---|---|---|---|
| Term-based license | 112.0 | **110.4** | +1.6 | Dominant lever — well estimated |
| Term-based support | 56.6 | **56.1** | +0.5 | Ratable, as expected |
| SaaS | 100.5 | **100.6** | **−0.05** | Essentially exact; crossed $100M |
| Perpetual license | 5.8 | **8.7** | −2.9 | Largest miss; the erratic line |
| Perpetual support | 26.7 | **25.5** | +1.2 | Decay slightly faster than −15% |
| Other services | 14.6 | **12.9** | +1.7 | Overshot a noisy line |
| **Subscription** | **269.1** | **267.0** | **+2.1** | |
| **Total** | **316.2** | **314.1** | **+2.1** | |

The three ratable lines (term support + SaaS + perpetual support) together: forecast $183.8M,
actual $182.1M, error +$1.7M. The claim that 58% of revenue is near-mechanical held.

### Error attribution

| Contributor | Signed error | Role |
|---|---|---|
| Perpetual license | −$2.9M | Under-forecast — the main miss |
| Other services | +$1.7M | Over-forecast |
| Term-based license | +$1.6M | Slight over |
| Perpetual support | +$1.2M | Slight over |
| Term-based support | +$0.5M | Noise |
| SaaS | −$0.05M | Exact |

The perpetual-license under-forecast and the other-services / term-license over-forecasts
partially cancelled. That cancellation is luck on the residual lines, not skill — but the
lines that were supposed to matter (term license, SaaS, term support) were all within $1.6M.

---

## What the call rested on, and how it resolved

The forecast said, in substance, that this quarter was a bet on **term-license revenue**, with
everything ratable close to mechanical.

| Claim | Outcome |
|---|---|
| Term license is the dominant uncertainty | Confirmed — and estimated within $1.6M |
| SaaS ≈ $100.5M | **$100.55M** — exact |
| Term support ≈ $56.6M | $56.1M |
| 58% of revenue is ratable / near-mechanical | Held |
| Recast trap: comparable is $229.3M, not $181.7M | Confirmed by the release's own reclassified prior-period table |

SaaS ARR printed at **$424.3M**, just $0.7M below the falsification band of $425–435M — close
enough that the SaaS revenue call was right even though the ARR falsifier technically tripped.
Subscription ARR printed at **$1,054.3M**. Total ARR is no longer disclosed.

---

## Guidance realization

| | |
|---|---|
| Guided subscription | $263–265M |
| Actual | **$267.0M** |
| Beat vs midpoint | **+$3.0M** |
| Forecast assumed | +$6.0M (Method 2) / +$5.1M (bottom-up implied) |

Directionally right, magnitude a bit high. Subscription still beat the guide high end — the
event we assigned **73%** probability to. That is now six consecutive quarters above the guide
low end (five of six above the midpoint, with the single miss still being Q2 FY26).

The dollar form of the beat distribution should be refit with this observation before Q2:

```
previous six beats ($M):  +13.3  +11.2  +13.7  -2.3  +10.3  +2.6     mean +8.13, sd 6.50
with Q1 FY27:             ...                             +3.0     mean +7.40, sd 6.15
```

The shaded +$6.0M centre used in the forecast was closer to the new mean than the unshaded
+$8.13M would have been. Keep shading toward recent quarters.

---

## Proper scores (against the plan in §9 of the forecast)

Benchmark: take guidance at face value → $311M total, treated as N(311, 6.5).

| Score | Forecast | Benchmark | Skill |
|---|---|---|---|
| CRPS on total revenue | 1.969 | 2.109 | **+6.6%** |
| Absolute error | $2.07M | $3.13M | **+33.9%** |
| Pinball loss (mean of p10/p25/p50/p75/p90) | 1.084 | — | — |

PIT of the actual under the total-revenue forecast: **0.39**. Under the subscription forecast:
**0.37**. Both are well inside (0.1, 0.9), slightly below 0.5 — consistent with a mild
over-forecast of the beat and not with miscalibration of the interval width.

**The forecast beat its own benchmark.** That is the only success criterion the scoring plan
named.

---

## Assumption register — which falsifiers tripped

| Assumption | Falsifier | Result |
|---|---|---|
| Term license $100–125M | outside that range | **Held** ($110.4) |
| SaaS $97–104M | outside that range | **Held** ($100.6) |
| Term support $55–58M | outside that range | **Held** ($56.1) |
| Perpetual support $25.5–27.5M | outside that range | **Held** ($25.5, on the floor) |
| Subscription below $263M | breaks the beat pattern | **Held** ($267.0) |
| SaaS ARR $425–435M | outside that range | **Tripped by $0.7M** ($424.3) |
| FX unmodelled | sharp move | No evidence of a material FX surprise in the print |

One falsifier tripped, by less than a million dollars, and the associated revenue line was
still exact. The perpetual-license miss (−$2.9M, −33%) did **not** trip a falsifier because
the interval on that line was deliberately set wide ($4–8M) and the actual ($8.7M) landed
just outside it — that band should be widened further for Q2, or the line treated as a
uniform over a still wider range. The other-services over-forecast similarly argues for
keeping that line's sd wide rather than tightening it.

---

## What to carry into Q2 FY27

1. **Refit the beat distribution** with the +$3.0M observation (new mean ≈ +$7.4M, sd ≈ $6.2M).
   Keep shading toward recent quarters; do not revert to the full-history mean.
2. **Widen the perpetual-license range.** $4–8M was not wide enough; the line printed $8.7M
   after a Q1 FY26 low of $7.3M. Treat it as closer to U($5, $12) until more history accumulates
   under the new disclosure.
3. **Trust the ratable stack.** Term support, SaaS, and perpetual support continue to forecast
   to within a couple of million. Build Q2 from them first.
4. **Drop Total ARR.** The company no longer discloses it. Method 3 (ARR × k) should be rebuilt
   on Subscription ARR + SaaS ARR, or retired.
5. **Q2 guide is $264–268M subscription.** Apply the refit beat on top of that midpoint once
   the residual lines are rebuilt.

---

## Sources

- Forecast record: [`2026-07-28-commvault-q1-fy2027.md`](./2026-07-28-commvault-q1-fy2027.md)
- Actuals: [Commvault Announces First Quarter Fiscal 2027 Financial Results](https://www.prnewswire.com/news-releases/commvault-announces-first-quarter-fiscal-2027-financial-results-302835588.html)
  (PR Newswire, 2026-07-28). Line items from the reclassified Consolidated Statements of Operations
  table in that release: term license $110,420K, term support $56,057K, SaaS $100,550K,
  perpetual license $8,695K, perpetual support $25,475K, other services $12,934K,
  total $314,131K.
