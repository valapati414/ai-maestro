# Probabilistic Revenue Forecasting: Predictability, Calibration, and Scoring

**A methodology reference for forecasting enterprise-software revenue.**
Compiled 2026-07-27. Every formula below is either quoted from a cited source or derived and
numerically verified against the reference implementation described in the appendix.

The organizing premise: **a revenue forecast is worthless until you know (a) how forecastable the
series is at all, and (b) whether your stated uncertainty is calibrated.** Point estimates without
either are decoration. This document treats *predictability* as a measurable property of the data
and *probability* as a falsifiable claim that must be scored.

---

## Table of contents

- [Part A — Quantifying predictability itself](#part-a--quantifying-predictability-itself)
  - [A.1 The three questions, in order](#a1-the-three-questions-in-order)
  - [A.2 Entropy-based forecastability](#a2-entropy-based-forecastability)
  - [A.3 Variability, memory, and signal-to-noise](#a3-variability-memory-and-signal-to-noise)
  - [A.4 Skill over a benchmark: the only measure that means anything](#a4-skill-over-a-benchmark-the-only-measure-that-means-anything)
  - [A.5 The irreducible error floor](#a5-the-irreducible-error-floor)
  - [A.6 The ADI / CV² quadrant and its enterprise adaptation](#a6-the-adi--cv-quadrant-and-its-enterprise-adaptation)
  - [A.7 Contracted vs at-risk revenue: the visibility ratio](#a7-contracted-vs-at-risk-revenue-the-visibility-ratio)
  - [A.8 The benchmark hierarchy you must report](#a8-the-benchmark-hierarchy-you-must-report)
- [Part B — Producing calibrated probabilistic forecasts](#part-b--producing-calibrated-probabilistic-forecasts)
  - [B.1 Method selection](#b1-method-selection)
  - [B.2 Monte Carlo over driver distributions](#b2-monte-carlo-over-driver-distributions)
  - [B.3 Choosing driver distributions](#b3-choosing-driver-distributions)
  - [B.4 Heavy-tailed deal sizes and why the pipeline mean is a bad point estimate](#b4-heavy-tailed-deal-sizes-and-why-the-pipeline-mean-is-a-bad-point-estimate)
  - [B.5 Correlation: the single largest source of understated tail risk](#b5-correlation-the-single-largest-source-of-understated-tail-risk)
  - [B.6 Quantile regression and quantile regression forests](#b6-quantile-regression-and-quantile-regression-forests)
  - [B.7 Conformal prediction](#b7-conformal-prediction)
  - [B.8 Bayesian hierarchical models and posterior predictive distributions](#b8-bayesian-hierarchical-models-and-posterior-predictive-distributions)
  - [B.9 Bootstrapping residuals](#b9-bootstrapping-residuals)
  - [B.10 Ensembles and mixture distributions](#b10-ensembles-and-mixture-distributions)
  - [B.11 Scenario trees with explicit probability weights](#b11-scenario-trees-with-explicit-probability-weights)
  - [B.12 Aggregation: the sum-of-quantiles trap](#b12-aggregation-the-sum-of-quantiles-trap)
- [Part C — Scoring, calibration, and backtesting](#part-c--scoring-calibration-and-backtesting)
  - [C.1 Proper scoring rules](#c1-proper-scoring-rules)
  - [C.2 Point-error metrics and the specific pathologies of MAPE](#c2-point-error-metrics-and-the-specific-pathologies-of-mape)
  - [C.3 Calibration diagnostics and recalibration](#c3-calibration-diagnostics-and-recalibration)
  - [C.4 Backtesting protocol for quarterly financial forecasts](#c4-backtesting-protocol-for-quarterly-financial-forecasts)
  - [C.5 Track-record accounting](#c5-track-record-accounting)
- [Part D — Judgmental forecasts and debiasing](#part-d--judgmental-forecasts-and-debiasing)
  - [D.1 Documented biases in pipeline and management forecasts](#d1-documented-biases-in-pipeline-and-management-forecasts)
  - [D.2 Fitted stage realization rates, not nominal probabilities](#d2-fitted-stage-realization-rates-not-nominal-probabilities)
  - [D.3 Mechanical debiasing](#d3-mechanical-debiasing)
  - [D.4 Forecast combination](#d4-forecast-combination)
  - [D.5 Calibration practices from forecasting tournaments](#d5-calibration-practices-from-forecasting-tournaments)
- [Scoring cheat sheet](#scoring-cheat-sheet)
- [Appendix — verification notes](#appendix--verification-notes)
- [Sources](#sources)

---

# Part A — Quantifying predictability itself

## A.1 The three questions, in order

Before any model is fit, answer these in sequence. Skipping to question 3 is the most common failure
mode in revenue forecasting.

1. **How much of next quarter's revenue is already determined?** (contracted backlog — Section A.7)
2. **Of the remainder, how much structure is there to exploit?** (entropy, autocorrelation, ADI/CV² —
   Sections A.2, A.3, A.6)
3. **Does my model beat the dumbest defensible baseline?** (skill score — Section A.4)

A company whose next-quarter revenue is 92% contracted has a *structurally* different forecasting
problem from one at 40%, and no amount of modeling sophistication changes that. Quantify the
constraint first, then work inside it.

## A.2 Entropy-based forecastability

### Spectral entropy

Hyndman's `tsfeatures` package uses spectral entropy explicitly as a "forecastability" feature. It
is the Shannon entropy of the normalized spectral density of a stationary process:

```
                 π
H_s(x_t) = -  ∫    f_x(λ) · log f_x(λ) dλ,        subject to  ∫ f_x(λ) dλ = 1
                -π
```

The spectral density is estimated with an AR model (Burg method); the implementation normalizes
`H_s` to `[0, 1]`. Interpretation, quoting the package vignette directly: *"This measures the
'forecastability' of a time series, where low values indicate a high signal-to-noise ratio, and
large values occur when a series is difficult to forecast."*

Reference points from the package documentation: `entropy(rnorm(1000)) = 1.0` (white noise, flat
periodogram, unforecastable), `entropy(lynx) = 0.733`, `entropy(sin(1:20)) = 0.0035` (pure
periodic, perfectly forecastable).

- <https://pkg.robjhyndman.com/tsfeatures/reference/entropy.html>
- <https://github.com/robjhyndman/tsfeatures/blob/master/vignettes/tsfeatures.Rmd>
- Underlying theory: Goerg, "Forecastable Component Analysis," ICML 2013 —
  <https://proceedings.mlr.press/v28/goerg13.html>

**Caveat that matters for revenue:** spectral entropy assumes stationarity and measures only how
concentrated the *linear* spectral content is. A cleanly trending series with a single dominant
frequency scores as highly forecastable; a regime-shifting series may score deceptively well within
each regime. Compute it on the *seasonally-and-trend-adjusted residual* of a revenue series, not on
the raw level, or you will mostly be measuring the trend.

### Permutation entropy

Bandt & Pompe's permutation entropy is the model-free, ordinal-pattern alternative. It is robust to
observational noise, invariant under monotone transformations, and cheap to compute — properties
that matter when you have 30 noisy quarterly observations.

For embedding dimension `m` and delay `τ`, form all `(T - (m-1)τ)` windows, replace each window by
the permutation `π` that sorts it, and take the Shannon entropy of the ordinal-pattern distribution:

```
H(m) = - Σ_π  p(π) · log p(π)

Normalized:      H_norm(m) = H(m) / log(m!)          ∈ [0, 1]
Redundancy:      R(m)      = 1 - H(m) / log₂(m!)     ("predictable structure")
```

`H_norm → 1` means every ordinal pattern is equally likely (no exploitable structure);
`H_norm → 0` means strong deterministic structure. Garland et al. show weighted permutation entropy
correlates with achievable prediction accuracy, and the ecology literature uses PE explicitly as a
proxy for *intrinsic predictability* — "the highest achievable predictability" — so that
`intrinsic − realized` tells you how much headroom your model has left.

- Bandt & Pompe, *Phys. Rev. Lett.* 88:174102 (2002) — <https://doi.org/10.1103/physrevlett.88.174102>
- Garland et al., "Model-free quantification of time-series predictability" —
  <https://ar5iv.labs.arxiv.org/html/1404.6823>
- Pennekamp et al., *Ecological Monographs* — <https://esajournals.onlinelibrary.wiley.com/doi/10.1002/ecm.1359>
- Practical parameter guidance (choose `m` in 3–7; require `T >> m!`): Riedl, Müller & Wessel —
  <https://people.physik.hu-berlin.de/~wessel/cvp/pubs/Riedl_epjst_2013.pdf>
- PE variants and comparison to ACF / mutual information —
  <https://onlinelibrary.wiley.com/doi/10.1111/anzs.12376>

**Hard constraint for quarterly data:** with `m = 3` there are `3! = 6` patterns and you need
`T >> 6`; with 30 quarters you can just about support `m = 3`, and `m = 4` (24 patterns) is already
overfitting the ordinal histogram. Use `m = 3` on quarterly revenue, or compute PE on *monthly*
bookings if available.

## A.3 Variability, memory, and signal-to-noise

| Measure | Formula | What it tells you about revenue |
|---|---|---|
| CV of level | `CV = σ(y) / μ(y)` | Dominated by trend for a growing SaaS business — nearly useless raw |
| CV of first differences | `CV_Δ = σ(Δy) / μ(Δy)` | The *useful* one: how stable is sequential net-new revenue |
| CV of YoY growth rate | `σ(g) / μ(g)`, `g_t = y_t/y_{t-4} − 1` | Best single scalar for "how tight can a growth-rate forecast be" |
| ACF | `ρ_k = Cov(y_t, y_{t-k}) / Var(y_t)` | On differenced/deseasonalized series: exploitable linear memory |
| Seasonal strength | `1 − Var(remainder) / Var(remainder + seasonal)` (STL) | Q4-heavy enterprise selling shows up here |
| Trend strength | `1 − Var(remainder) / Var(remainder + trend)` | High values → naive-with-drift is a strong baseline |
| Hurst exponent | `E[R(n)/S(n)] = C·n^H` | `H ≈ 0.5` random walk, `0.5 < H < 1` persistent, `H < 0.5` mean-reverting |
| Signal-to-noise | `SNR = Var(signal) / Var(noise)`, from a decomposition | Directly bounds achievable `R²` |

Trend/seasonal strength definitions are from `tsfeatures`/`stl_features`
(<https://robjhyndman.r-universe.dev/tsfeatures/doc/manual.html>).

### Hurst exponent, with a warning

`R/S` analysis: split a length-`N` series into non-overlapping blocks of length `n`, compute the
rescaled range `R(n)/S(n)` in each (range of cumulative mean-deviations divided by block standard
deviation), average, then regress `log(R/S)` on `log n` — the slope estimates `H`.

- <https://en.wikipedia.org/wiki/Hurst_exponent>
- <https://pubsonline.informs.org/do/10.1287/LYTX.2012.04.05/full/>

**Do not report a Hurst exponent from 30 quarterly observations.** `R/S` is known to systematically
overestimate `H` in finite samples, and the Anis–Lloyd correction exists precisely because of this;
Kristoufek's simulation study documents the bias and its dependence on series length.
Detrended fluctuation analysis (DFA) is the usual replacement but introduces its own finite-size
artifacts under nonlinear trends. Reserve Hurst for daily/weekly bookings series with thousands of
points.

- Finite-sample properties of R/S vs DFA — <https://mpra.ub.uni-muenchen.de/16446/1/MPRA_paper_16446.pdf>
- DFA artifacts under nonlinear trends — <https://doi.org/10.1038/srep00315>

## A.4 Skill over a benchmark: the only measure that means anything

An absolute error number is uninterpretable. Every accuracy claim must be expressed as skill over a
named baseline. Hyndman & Koehler's scaled-error framework is the standard:

```
Scaled error (non-seasonal, naive scaling):

              e_j                                    1     T
    q_j = ─────────────────────,     where   d =  ─────  Σ   | y_t − y_{t−1} |
              d                                   T − 1  t=2

    MASE  = mean( |q_j| )
    RMSSE = sqrt( mean( q_j² ) )      with  q²_j = e²_j / [ (1/(T−m)) Σ (y_t − y_{t−m})² ]
```

For seasonal data set the denominator to the in-sample **seasonal** naive MAE with `m = 4` for
quarterly revenue. `MASE < 1` means you beat the in-sample one-step naive; `MASE > 1` means last
period's value would have been better.

- Hyndman & Koehler, *IJF* 22(4):679–688 (2006) — <https://robjhyndman.com/papers/mase.pdf>,
  <https://doi.org/10.1016/j.ijforecast.2006.03.001>
- fpp3 §5.8 — <https://otexts.com/fpp3/accuracy.html>

Related benchmark ratios:

```
Relative MAE      = MAE_model / MAE_benchmark          (< 1 is better)
Theil's U2        = sqrt(Σ (ŷ_t − y_t)²) / sqrt(Σ (y^naive_t − y_t)²)
Skill score       = 1 − S_model / S_benchmark          (0 = no skill, 1 = perfect)
```

The skill-score form generalizes to *any* proper score. Gneiting & Raftery introduce skill scores
for exactly this purpose; the probabilistic analogue you should actually report is

```
CRPSS = 1 − CRPS_model / CRPS_benchmark
```

where the benchmark is the *climatological* forecast — for revenue, the empirical distribution of
historical YoY growth rates applied to the current base. A model that cannot beat "the distribution
of the last 12 quarters of growth rates" has demonstrated nothing.

- Gneiting & Raftery, *JASA* 102(477):359–378 (2007) —
  <https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf>

## A.5 The irreducible error floor

Decompose realized squared error into three parts:

```
E[(y − ŷ)²]  =  bias²  +  estimation variance  +  irreducible noise σ²_ε
                └──── reducible by better modeling ────┘   └─ floor ─┘
```

Three practical ways to estimate the floor for a revenue series:

1. **Residual variance of the best-fitting in-sample decomposition.** Fit STL or a state-space model
   on the full history; `Var(remainder)` is an *optimistic* (downward-biased) floor estimate because
   it is in-sample.
2. **Intrinsic-predictability proxy.** Compute normalized permutation entropy on the differenced,
   deseasonalized series. `H_norm` near 1 says the floor is near the total variance regardless of
   model. This is the Garland/Pennekamp "intrinsic vs realized predictability" gap.
3. **Contracted-share bound.** The analytically cleanest one, and specific to enterprise software.
   See the next section — if 90% of next quarter is contracted and the uncontracted 10% has a 30%
   coefficient of variation, the total revenue CV cannot exceed 3.0% no matter what you do, and
   *should not be reported as lower than that either.*

**Report the floor alongside the model error.** A model with 4% MAPE on a series whose floor is 3.5%
is near-optimal; the same 4% on a series with a 1% floor is a bad model. Absent the floor, the two
are indistinguishable.

## A.6 The ADI / CV² quadrant and its enterprise adaptation

Syntetos, Boylan & Croston classify demand series on two statistics:

```
Average Demand Interval:        ADI  = T / N        (T = periods, N = periods with nonzero demand)
Squared coeff. of variation:    CV²  = ( σ(z) / μ(z) )²     over the NONZERO demand sizes z
```

Cutoffs `ADI = 1.32`, `CV² = 0.49`:

| | `CV² ≤ 0.49` | `CV² > 0.49` |
|---|---|---|
| **`ADI ≤ 1.32`** | **Smooth** | **Erratic** |
| **`ADI > 1.32`** | **Intermittent** | **Lumpy** |

- Syntetos, Boylan & Croston, "On the categorization of demand patterns," and Boylan & Syntetos,
  "The accuracy of intermittent demand estimates," *IJF* (2005)
- Reference implementation with these exact defaults —
  <https://www.sktime.net/en/v0.32.2/api_reference/auto_generated/sktime.transformations.series.adi_cv.ADICVTransformer.html>
- Empirical review of the cutoffs — <http://www.msc-les.org/proceedings/mas/2014/MAS2014_205.pdf>

**Two honest caveats before you use this.** First, the 1.32/0.49 boundaries were derived from the
MSE crossover between Croston's method and the Syntetos–Boylan Approximation — they are *method
selection* boundaries, not universal descriptions of demand. Kostenko & Hyndman (2006) showed the
true boundary is a non-rectangular curve. Second, the scheme assumes ADI and CV² are stable over
time, which fails for a business whose deal flow is ramping or decaying.

- Both caveats, stated by practitioners close to the original work —
  <https://openforecast.org/2024/07/16/intermittent-demand-classifications-is-that-what-you-need/>

### Adapting the quadrant to enterprise deal flow

Aggregate quarterly *revenue* for a company of any size is almost never intermittent — subscription
recognition smooths it. Apply the classification to the right series:

| Series to classify | Why | Typical quadrant |
|---|---|---|
| Quarterly total revenue | Smoothed by ratable recognition | Smooth |
| Quarterly **net new ARR** | The actual forecasting problem | Erratic |
| Quarterly bookings in a **single segment/geo/product** | Where lumpiness lives | Erratic → Lumpy |
| Quarterly count of **deals above a threshold** (e.g. >$1M ACV) | The genuinely intermittent series | Intermittent → Lumpy |
| Per-account expansion revenue | Sparse renewal calendar | Lumpy |

Practical adaptations:

- **Redefine the "demand event."** For enterprise, the event is a *closed deal above a materiality
  threshold*, not "a period with nonzero revenue." `ADI` then means average quarters between
  material deals, which is the quantity that actually drives lumpiness.
- **Compute CV² on log deal size.** Enterprise ACV is right-skewed enough that raw `CV²` is
  dominated by the single largest deal and is unstable quarter to quarter. Report both
  `CV²(z)` and `CV²(log z)`; a large gap is itself the diagnostic for heavy tails (Section B.4).
- **Add a concentration axis.** The quadrant misses the dimension that matters most in enterprise:
  the Herfindahl index of quarterly bookings by deal, `HHI = Σ (z_i / Σz)²`. An `HHI` of 0.3 means
  effectively 3 deals determine the quarter, so the quarter's distribution is a mixture over
  discrete win/loss outcomes, not a smooth continuum. **This is the flag for "use a Monte Carlo /
  scenario-tree method, not a time-series model."**
- **Aggregate temporally to escape lumpiness.** Temporal aggregation is the standard remedy for
  lumpy series; forecast semi-annual or annual bookings and disaggregate, rather than forcing a
  quarterly model onto a lumpy series.

Threshold guidance for the concentration axis (heuristic, calibrate on your own history): `HHI < 0.05`
→ law of large numbers applies, use continuous models; `0.05–0.20` → hybrid, model the top-N deals
discretely and the tail continuously; `> 0.20` → the quarter *is* a handful of binary events, and a
Bernoulli-mixture Monte Carlo is the only honest representation.

## A.7 Contracted vs at-risk revenue: the visibility ratio

This is the highest-leverage structural decomposition available for enterprise software, and it is
disclosed under GAAP.

### The disclosure

Under ASC 606, companies disclose **Remaining Performance Obligations (RPO)**: the total transaction
price allocated to performance obligations not yet satisfied. It comprises deferred revenue
(invoiced, not yet recognized) plus non-cancelable contracted-but-unbilled amounts. **Current RPO
(cRPO)** is the portion expected to be recognized within 12 months. Both appear in the revenue
footnote of every 10-Q and 10-K since 2018.

- <https://ordwaylabs.com/blog/how-saas-companies-define-rpos/>
- <https://www.gsquaredcfo.com/blog/rpo-in-saas-explained-quick-guide-to-remaining-performance-obligations>
- <https://saasdb.app/learn/financials/rpo-and-backlog/>
- <https://getpacerai.com/blog/what-is-current-performance-obligation/>

### The decomposition

```
R_{t+1}  =  C_{t+1}  +  U_{t+1}

  C = contracted / locked   (from cRPO + deferred revenue scheduled into t+1)
  U = uncontracted / at-risk (new bookings closing and recognizing in-period,
                              usage/consumption overage, renewals not yet signed,
                              professional services, minus churn on uncontracted base)
```

### Ratios to compute

```
Coverage ratio          κ  =  C_{t+1} / E[R_{t+1}]                    (0 to 1)
Consensus coverage      κ_c = C_{t+1} / consensus_revenue_{t+1}
Visibility ratio (annual)   = cRPO_t / (next four quarters' revenue)
RPO duration                = total RPO_t / TTM revenue               (years contracted)
Book-to-recognition spread  = billings growth − revenue growth        (basis points)
```

`κ` is the single most useful predictability statistic for an enterprise software company, and it is
directly comparable across companies.

**Estimating `C_{t+1}` from public filings.** cRPO is a 12-month figure, not quarterly. Two
approaches: (i) a **roll-forward** — `cRPO_t` less the portion already recognized, allocated across
the next four quarters using the company's historical recognition pattern, which for ratable
subscription revenue is close to uniform with a Q4-renewal skew; (ii) a **regression** of realized
`R_{t+1}` on `cRPO_t / 4` across the peer panel, whose slope is the empirical conversion factor.
Practitioner rule of thumb: cRPO converts to GAAP revenue at roughly 90–100% within 12 months, with
slippage from contract extensions and attrition (<https://saasdb.app/learn/financials/rpo-and-backlog/>).

Treat `C_{t+1}` as *nearly* certain, not certain: contract modifications, early terminations, and
credits do occur. Model `C` as a tight distribution (`CV_C` on the order of 0.5–2%, fitted from your
own backtest residuals on the contracted component) rather than a scalar.

### Deriving the accuracy bound

Let `c = E[C] / E[R]` be the contracted share and `CV_U = σ_U / E[U]` the coefficient of variation
of the uncontracted component. If `C` is known exactly (`σ_C = 0`) and independent of `U`:

```
σ_R  = σ_U                                   (C contributes no variance)
E[R] = E[C] + E[U]

              σ_U         σ_U       E[U]
CV_R  =  ─────────────  = ─────  ·  ─────  =  (1 − c) · CV_U
          E[C] + E[U]      E[U]      E[R]
```

**`CV_R = (1 − c) · CV_U`.** This is the accuracy ceiling. If the uncontracted component's growth is
irreducibly 30% volatile, then:

| Contracted share `c` | Implied total `CV_R` | Expected \|error\| as % of revenue | 80% interval half-width |
|---|---|---|---|
| 0.00 | 30.0% | 23.9% | ±38.4% |
| 0.50 | 15.0% | 12.0% | ±19.2% |
| 0.75 | 7.5% | 6.0% | ±9.6% |
| 0.90 | 3.0% | 2.4% | ±3.8% |
| 0.95 | 1.5% | 1.2% | ±1.9% |

The third column uses the Gaussian relation `E|Z| = σ·√(2/π)`, so **expected MAPE ≈ 0.798 · CV_R**;
the fourth uses `1.2816 · CV_R` for the 10th–90th percentile half-width. Relaxing the exactness of
`C`:

```
CV_R  =  sqrt( c² · CV_C²  +  (1 − c)² · CV_U²  +  2 ρ c (1−c) CV_C CV_U )
```

**Two ways this bound is used, and both matter.**

*As a floor:* if your model reports a tighter interval than `(1−c)·CV_U` allows, you are
overconfident and your PIT histogram will be U-shaped. Check this before you ship.

*As a ceiling on model value:* the reducible portion of total variance is only `(1−c)²` of the
uncontracted variance. At `c = 0.9`, a heroic 30% reduction in uncontracted-component error buys you
a 0.7pp improvement in total revenue MAPE. **Spend your modeling effort proportional to
`(1 − c)`,** and spend the rest on getting `C` right.

## A.8 The benchmark hierarchy you must report

Every forecast must be scored against this ladder, in order, and the report must show all of them.
A model is only interesting if it beats the tier above it.

| Tier | Baseline | Definition (quarterly revenue) | Purpose |
|---|---|---|---|
| 0 | Random walk | `ŷ_{t+h} = y_t` | Absolute floor |
| 1 | Seasonal naive | `ŷ_{t+h} = y_{t+h−4}` | Handles Q4 skew |
| 2 | Naive with drift | `ŷ_{t+h} = y_t + h·(y_t − y_1)/(T−1)` | Handles trend |
| 3 | Constant YoY growth | `ŷ_{t+h} = y_{t+h−4} · (y_t / y_{t−4})` | **The real baseline for SaaS.** Very hard to beat. |
| 4 | Damped growth | `ŷ = y_{t+h−4} · (1 + φ^h · g_t)`, `φ ≈ 0.8–0.95` | Encodes growth-rate decay |
| 5 | Contracted-only | `ŷ_{t+1} = Ĉ_{t+1} / κ̄`, `κ̄` = historical mean coverage | Tests whether pipeline data adds anything |
| 6 | Consensus / management guidance | Published estimate | The economically relevant benchmark |
| 7 | Your model | | Must beat 3, 5, **and** 6 |

For probabilistic forecasts each tier needs a distributional version: tier 0–4 via bootstrapped
residuals (Section B.9), tier 5 via the `CV_R` formula above, tier 6 via the historical distribution
of guidance-to-actual ratios.

**Report as a table of skill scores, not raw errors:**

```
                    MASE   CRPS   CRPSS vs T3   90% coverage   PIT KS p-value
T3 constant YoY     1.00   ....       0.000         0.87          0.31
T6 consensus        0.84   ....      +0.14          0.91          0.44
Model               0.71   ....      +0.28          0.90          0.62
```

The M4 competition's headline finding is the relevant prior here: 12 of the 17 most accurate methods
were *combinations* of mostly statistical approaches, the winner beat the combination benchmark by
9.4% sMAPE, and six pure-ML entries all failed to beat that benchmark. Expect single-digit-percent
improvements over a good baseline, not step changes.

- Makridakis, Spiliotis & Assimakopoulos, "The M4 Competition: 100,000 time series and 61
  forecasting methods," *IJF* 36(1):54–74 —
  <https://www.sciencedirect.com/science/article/pii/S0169207019301128>
- Findings summary — <https://ideas.repec.org/a/eee/intfor/v34y2018i4p802-808.html>,
  <https://purehost.bath.ac.uk/ws/portalfiles/portal/192035784/IJF_2019_M4_Conclusions_post_print_.pdf>

---

# Part B — Producing calibrated probabilistic forecasts

## B.1 Method selection

| Method | Use when | Gives you | Cost / risk |
|---|---|---|---|
| Monte Carlo over drivers | Business structure is known; drivers are separately estimable; concentration `HHI` high | Full joint distribution, attribution by driver | Garbage-in; correlation must be modeled explicitly |
| Bootstrapped residuals | You have a fitted point model and ≥30 residuals | Distribution-free, asymmetric intervals | Assumes residuals i.i.d. and stationary |
| Quantile regression / QRF | Covariates available; heteroscedasticity | Conditional quantiles | Quantile crossing; no coverage guarantee |
| Conformal (split / CQR / ACI / EnbPI) | You need a *coverage guarantee* | Finite-sample marginal coverage | Needs a calibration set; marginal not conditional |
| Bayesian hierarchical | Short series, peer panel available | Posterior predictive incl. parameter uncertainty | Prior sensitivity; compute |
| Ensemble / mixture | Multiple credible models | Robustness; usually best score | Must mix distributions, not quantiles |
| Scenario tree | Discrete regime risk (a mega-deal, a reorg, a macro break) | Explicit, auditable, communicable | Weights are judgmental — score them |

**Default recommendation for enterprise revenue:** a *mixture* of (i) a driver-level Monte Carlo for
the uncontracted component added to a tight distribution for the contracted component, and (ii) a
time-series model with bootstrapped or conformalized intervals — combined with equal weights, then
conformally recalibrated on a rolling-origin backtest. Rationale in Sections B.10, B.7, D.4.

## B.2 Monte Carlo over driver distributions

Structure for enterprise software, per segment `s` and quarter `t+h`:

```
R_s  =  C_s                                          contracted (tight distribution)
      + Σ_{i ∈ topN_s}  W_i · Z_i                    named deals: Bernoulli win × size
      + N_s · Z̄_s                                    tail deals: count × size
      + B_s · ρ_s · P_s                              renewals: base × retention × price
      + O_s                                          usage/overage
      − K_s                                          churn on uncontracted base

R_total = Σ_s R_s
```

```python
import numpy as np

def simulate_quarter(cfg, n_sims=200_000, rng=None):
    """One segment-quarter. Returns an array of n_sims revenue draws."""
    rng = rng or np.random.default_rng(0)

    # Contracted: tight, slightly left-skewed (modifications reduce, rarely increase)
    C = cfg["C_mean"] * (1 - rng.gamma(2.0, cfg["C_slip_scale"], n_sims))

    # Named large deals: Bernoulli(win) x lognormal(size)
    named = np.zeros(n_sims)
    for d in cfg["named_deals"]:
        win = rng.random(n_sims) < d["p_win"]
        size = rng.lognormal(d["log_mu"], d["log_sigma"], n_sims)
        named += win * size

    # Tail deals: negative binomial count x lognormal size, summed
    #   NB parameterized by mean m and dispersion k:  var = m + m^2/k
    m, k = cfg["tail_count_mean"], cfg["tail_count_disp"]
    p = k / (k + m)
    counts = rng.negative_binomial(k, p, n_sims)
    tail = np.array([
        rng.lognormal(cfg["tail_log_mu"], cfg["tail_log_sigma"], c).sum() if c else 0.0
        for c in counts
    ])

    # Renewals: beta retention x lognormal price uplift
    retention = rng.beta(cfg["ret_a"], cfg["ret_b"], n_sims)
    uplift = rng.lognormal(cfg["uplift_log_mu"], cfg["uplift_log_sigma"], n_sims)
    renewals = cfg["renewal_base"] * retention * uplift

    overage = rng.gamma(cfg["over_shape"], cfg["over_scale"], n_sims)
    churn = cfg["churn_base"] * rng.beta(cfg["churn_a"], cfg["churn_b"], n_sims)

    return C + named + tail + renewals + overage - churn
```

Two rules that are violated constantly:

1. **Never sample a driver independently that is not independent.** Apply Iman–Conover (Section B.5)
   to the matrix of driver draws before combining. The measured effect is large.
2. **Never simulate segments independently and add.** Same fix, applied at the segment level with a
   common macro shock (Section B.5).

## B.3 Choosing driver distributions

| Driver | Distribution | Why | Parameterization from data |
|---|---|---|---|
| Deal / contract size | **Lognormal** | Multiplicative price × seats × term; strictly positive; right-skewed | `μ, σ` = mean/sd of `log(ACV)` on won deals |
| Very large deal sizes (tail beyond ~p95) | **Pareto / generalized Pareto** | Empirical ACV tails are heavier than lognormal | Hill estimator on exceedances above a threshold |
| Number of deals closed | **Poisson** if `Var ≈ mean` | Independent arrivals | `λ` = mean count |
| Number of deals closed (usual case) | **Negative binomial** | Real bookings counts are over-dispersed | `mean m`, `dispersion k`; `Var = m + m²/k` |
| Win probability of a named deal | **Bernoulli**, `p` from fitted stage rate | Binary event | Section D.2 |
| Retention / renewal rate | **Beta** | Bounded on `[0,1]` | Method of moments from historical GRR |
| Net revenue retention (can exceed 1) | **Shifted lognormal** or **gamma** | Unbounded above, positive | Fit to historical NRR |
| Price uplift on renewal | **Lognormal** | Multiplicative, positive | Fit to `log(1 + uplift)` |
| Usage / consumption overage | **Gamma** | Positive, continuous, flexible skew | `shape, scale` by MoM |
| Macro / common shock | **Normal** or **Student-t (ν≈4–6)** | `t` if you want fat joint tails | Fit to a macro index or to the residual common factor |
| FX impact | **Normal on log FX** | Approximately random walk | From currency vol |
| Churn events | **Bernoulli per account** or **beta on rate** | Binary at account level | Historical logo churn |

The M5 uncertainty literature is direct on the count-distribution question: the winning gradient-
boosting entries' default objectives *failed* to address over-dispersion and sporadic demand, and
distributional approaches (GAMLSS with negative binomial location–scale) were the appropriate fix.
Zero-inflation was needed for only ~6% of items; **over-dispersion, not zero-inflation, was the
dominant issue.** Same holds for enterprise deal counts.

- Ziel, "M5 competition uncertainty: Overdispersion, distributional forecasting, GAMLSS, and beyond,"
  *IJF* — <https://doi.org/10.1016/j.ijforecast.2021.09.008>

## B.4 Heavy-tailed deal sizes and why the pipeline mean is a bad point estimate

For a lognormal deal size `Z ~ LN(μ, σ²)`:

```
E[Z]      = exp(μ + σ²/2)
Median[Z] = exp(μ)
Mode[Z]   = exp(μ − σ²)

E[Z] / Median[Z] = exp(σ²/2)
```

With `σ = 1.0` (entirely normal for enterprise ACV), the mean is `exp(0.5) = 1.65×` the median.
**More than half of all deals come in below the "expected" deal size.** Consequences:

- **`Σ (probability × amount)` — the weighted-pipeline point estimate — is the mean of a
  right-skewed, low-count sum.** It sits well above the median outcome. A sales organization
  reporting weighted pipeline of $10M will most often land below $10M, and this is arithmetic, not
  sandbagging.
- **The mean is not the decision-relevant summary.** If the question is "will we hit the guide," you
  need `P(R ≥ guide)`, which requires the distribution. If the question is "what number do we
  commit," the answer is a quantile chosen from the asymmetric cost of missing versus sandbagging.
- **Low deal counts break the central limit theorem.** With `HHI > 0.2` (Section A.6), the quarter's
  distribution is multimodal — visible bumps where the mega-deal lands or does not. Reporting a mean
  ± symmetric interval erases the exact feature that matters.
- **Tail fitting.** Fit a lognormal body and a generalized Pareto tail above a threshold `u` chosen
  by mean-excess plot. The rationale is standard extreme-value practice; the risk-management
  literature on heavy tails and correlation applies directly (Embrechts, McNeil & Straumann,
  "Correlation and dependence in risk management: properties and pitfalls" —
  <https://people.math.ethz.ch/~embrecht/ftp/pitfalls.pdf>).

**Always report the median and the mean, and the ratio between them.** The ratio is a compact
lumpiness diagnostic and pre-empts the "your forecast is below the pipeline" conversation.

## B.5 Correlation: the single largest source of understated tail risk

### Why independence is dangerous

For `n` segments each with standard deviation `σ` and pairwise correlation `ρ`:

```
Var( Σ R_s ) = n σ² + n(n−1) ρ σ²        →       SD = σ · sqrt( n + n(n−1)ρ )
```

Independence (`ρ = 0`) gives `σ√n`. The understatement factor is `sqrt(1 + (n−1)ρ)`.

**Measured on 5 lognormal segments with `ρ = 0.6` (400k draws, Iman–Conover induced):**

| | Mean | SD | q95 | q99 |
|---|---|---|---|---|
| Independent | 531.7 | 85.9 | 683.9 | 764.2 |
| `ρ = 0.6` | 531.7 | **157.0** | **820.4** | **1000.0** |

The mean is unchanged; the standard deviation grows 1.83× and the 99th percentile by 31%. An
independence assumption here does not make the forecast slightly optimistic — it makes the stated
tail risk wrong by a third.

Sources of real correlation in enterprise revenue, all of which should be in the model:

- **Macro / budget cycle.** A demand shock hits every segment. Model as a common multiplicative
  factor, not as pairwise correlations.
- **Quarter-end dynamics.** Deals slip together (procurement freezes, holiday calendars).
- **Sales capacity.** A shared quota-bearing headcount pool couples segment outcomes.
- **Pricing/packaging changes.** One decision moves every segment's ASP.
- **Win/loss correlation against a common competitor.**

### Practical approaches, in increasing order of fidelity

**(1) Common-factor / macro shock — do this first.** Simplest, most interpretable, hardest to get
wrong:

```
R_s = f(drivers_s) · (1 + β_s · M),        M ~ Normal(0, σ_M)  or  Student-t(ν)
```

This induces `Corr(R_s, R_s') ≈ β_s β_s' σ_M² / (σ_s σ_s')` automatically, and the `β_s` are
estimable by regressing historical segment growth on a macro index. Using Student-t for `M` gives
joint tail dependence, which Gaussian factors cannot produce.

**(2) Correlation matrix on driver shocks + Iman–Conover.** Preserves your chosen marginals exactly
while inducing a target rank-correlation matrix. Algorithm below.

**(3) Copulas.** Needed when the *shape* of dependence matters, not just its strength — specifically
when you need upper tail dependence (segments crashing together). Gaussian copulas have **zero tail
dependence unless correlation is exactly 1**, which is precisely why they understate simultaneous
extremes. Use a `t`-copula (symmetric tail dependence) or a Gumbel copula (upper tail dependence
`λ_U = 2 − 2^{1/θ}`).

- Embrechts, McNeil & Straumann on why linear correlation is the wrong dependence measure for
  skewed, heavy-tailed risks — <https://people.math.ethz.ch/~embrecht/ftp/pitfalls.pdf>
- Tail dependence and why many copulas understate simultaneous extremes —
  <https://www.casact.org/sites/default/files/database/forum_10fforumpt2_staudt.pdf>
- Risk aggregation via copulas vs linear correlation —
  <https://doi.org/10.4236/jmf.2011.13007>
- Rank correlation and copula practitioner note —
  <https://ndic.gov.ng/wp-content/uploads/2024/05/Technical-Note-on-Correlation-and-Copula-Models-for-Dependence-Modelling.pdf>

### The Iman–Conover method

Iman & Conover (1982) give a distribution-free reordering that induces an approximate target rank
correlation **while preserving each marginal distribution exactly** — the output columns are
permutations of the input columns. That property is what makes it ideal for driver-level Monte
Carlo: you choose each driver's distribution on business grounds and impose dependence afterward
without disturbing them.

- Iman & Conover, *Comm. Statist. Simula. Computa.* 11(3):311–334 (1982) —
  <https://doi.org/10.1080/03610918208812265>
- Step-by-step exposition — <https://blogs.sas.com/content/iml/2021/06/14/simulate-iman-conover-transformation.html>
- Geometry of the four transformations — <https://blogs.sas.com/content/iml/2021/06/16/geometry-iman-conover-transformation.html>
- Formal algorithm statement — <https://aggregate.readthedocs.io/en/latest/5_technical_guides/5_x_iman_conover.html>

**Algorithm.** Input: `X` (`n × k`, each column an independent sample from its marginal),
`C` (`k × k` target rank-correlation matrix, symmetric positive definite).

1. **Normal scores.** For each column `j`, compute average ranks `r_ij` and set
   `S_ij = Φ⁻¹( r_ij / (n+1) )` (van der Waerden scores). `S` has the same rank structure as `X`
   but Gaussian marginals.
2. **Decorrelate.** Let `E = corr(S)` and `E = Q Qᵀ` (Cholesky). Set `Z = S (Q⁻¹)ᵀ`, which has
   approximately identity correlation.
3. **Recorrelate to target.** Let `C = P Pᵀ` (Cholesky). Set `T = Z Pᵀ`. Now `corr(T) ≈ C`.
4. **Reorder.** For each column `j`, permute the *sorted* values of `X[:,j]` so their rank order
   matches the rank order of `T[:,j]`. Because any two matrices whose columns share rank orderings
   share the same rank correlation, the result has `rank-corr ≈ C` and unchanged marginals.

Step 2 is what makes the method work in finite samples: the sample correlation of the scores is not
exactly identity, and removing it first is why the achieved correlation lands close to target.

```python
import numpy as np
from scipy import stats

def iman_conover(X, C):
    """Reorder columns of X to induce target rank correlation C.

    X : (n, k) each column an independent sample from its own marginal
    C : (k, k) target rank-correlation matrix, symmetric positive definite
    Returns W: (n, k) column-wise permutation of X with rank-corr(W) ~= C.
    """
    X = np.asarray(X, dtype=float)
    n, k = X.shape

    # 1. van der Waerden normal scores
    S = np.column_stack([
        stats.norm.ppf(stats.rankdata(X[:, j], method="average") / (n + 1))
        for j in range(k)
    ])

    # 2. remove the sample correlation of the scores
    Q = np.linalg.cholesky(np.corrcoef(S, rowvar=False))
    Z = S @ np.linalg.inv(Q).T

    # 3. impose the target
    T = Z @ np.linalg.cholesky(C).T

    # 4. reorder each column of X to T's rank pattern
    return np.column_stack([
        np.sort(X[:, j])[np.argsort(np.argsort(T[:, j]))]
        for j in range(k)
    ])
```

**Verified behavior** (20,000 draws; lognormal deal size, gamma macro multiplier, beta retention;
target off-diagonals 0.6 / 0.3 / 0.5):

```
target   Spearman off-diagonals:  0.600  0.300  0.500
achieved Spearman off-diagonals:  0.584  0.284  0.482
marginals preserved exactly:      True
```

Note the systematic mild attenuation — achieved rank correlation is a few points below target. This
is a known property of the method (it induces the target on the *scores*, and the rank-to-linear
correlation relationship is not exact). If you need the target hit precisely, iterate: inflate the
target slightly and re-run, or verify and adjust. `C` must be positive definite or the Cholesky
step fails; repair a non-PD elicited matrix with nearest-correlation-matrix projection first.

## B.6 Quantile regression and quantile regression forests

**Linear quantile regression** estimates the conditional `τ`-quantile by minimizing pinball loss:

```
β̂(τ) = argmin_β  Σ_i  ρ_τ( y_i − x_iᵀ β ),     ρ_τ(u) = u·(τ − 1{u < 0})
```

**Quantile regression forests** (Meinshausen 2006) extend random forests from the conditional mean
to the full conditional distribution. The key observation: a forest's leaf memberships define an
adaptive nearest-neighbor weighting `w_i(x)`, and the conditional CDF estimate is

```
F̂(y | X = x) = Σ_i  w_i(x) · 1{ y_i ≤ y }
```

from which any quantile follows. The algorithm is proven consistent. Crucially it retains *all*
observations in each leaf rather than only their mean.

- Meinshausen, *JMLR* 7:983–999 (2006) — <https://jmlr.org/papers/volume7/meinshausen06a/meinshausen06a.pdf>,
  <https://www.jmlr.org/papers/v7/meinshausen06a.html>
- Python: `quantile-forest` (`RandomForestQuantileRegressor.predict(X, quantiles=[...])`)

**For quarterly revenue with 20–40 observations, do not use QRF on the revenue series itself** —
there is nowhere near enough data. QRF is appropriate on the *deal-level* or *account-level* panel,
where you have thousands of rows: predict the conditional distribution of deal ACV or of
account-level expansion given features, then aggregate (Section B.12).

**Known failure mode: quantile crossing.** Separately-fitted quantile models can produce
`q̂_{0.9} < q̂_{0.8}`. Fix by monotone rearrangement (sort the predicted quantile vector) or by
joint estimation. Reconciliation methods that calibrate quantiles simultaneously also mitigate it.

## B.7 Conformal prediction

Conformal prediction gives **finite-sample, distribution-free marginal coverage** under
exchangeability, wrapping any point or quantile predictor. This is the right tool when you must be
able to state a coverage guarantee rather than hope for one.

### Split (inductive) conformal

Split the data into a proper training set `I₁` and a calibration set `I₂`. Fit `μ̂` on `I₁`.
Compute absolute residuals on `I₂`, then:

```
r_i = | y_i − μ̂(x_i) |,   i ∈ I₂,   m = |I₂|

q̂ = the  ⌈(m+1)(1−α)⌉ / m   empirical quantile of { r_i }

C(x) = [ μ̂(x) − q̂ ,  μ̂(x) + q̂ ]        with   P( Y ∈ C(X) ) ≥ 1 − α
```

The `⌈(m+1)(1−α)⌉/m` inflation (rather than plain `1−α`) is what delivers the finite-sample
guarantee.

```python
import numpy as np

def split_conformal_qhat(cal_residuals, alpha=0.10):
    """Conformal radius from calibration absolute residuals."""
    r = np.abs(np.asarray(cal_residuals, dtype=float))
    m = r.size
    level = min(1.0, np.ceil((m + 1) * (1 - alpha)) / m)
    return np.quantile(r, level, method="higher")

def split_conformal_interval(point_pred, qhat):
    return point_pred - qhat, point_pred + qhat
```

**Verified:** with a 200-point calibration set and `α = 0.10`, mean coverage over 2,000
independent calibration draws was **0.9056** against the 0.9000 target. Coverage is guaranteed
*marginally over the calibration draw*, so any single realized interval may under-cover slightly —
in one draw above, realized coverage was 0.8954. Do not over-interpret a single backtest's coverage.

### Conformalized quantile regression (CQR)

Split conformal produces constant-width intervals. CQR (Romano, Patterson & Candès, NeurIPS 2019)
makes width adapt to `x` while keeping the guarantee. Fit lower and upper quantile models
`q̂_lo, q̂_hi` at levels `α/2, 1−α/2` on `I₁`, then on `I₂` compute the *signed* conformity score:

```
E_i = max{  q̂_lo(x_i) − y_i ,  y_i − q̂_hi(x_i)  }

    (negative when y_i is comfortably inside; positive when outside)

Q = the ⌈(m+1)(1−α)⌉/m empirical quantile of { E_i }

C(x) = [ q̂_lo(x) − Q ,  q̂_hi(x) + Q ]
```

`Q` can be negative, in which case the interval *shrinks* — the quantile models were conservative.
The interval inherits heteroscedastic width from the quantile models and exact coverage from
conformal calibration, and CQR empirically produces shorter intervals than other conformal methods.

- Romano, Patterson & Candès, NeurIPS 32 —
  <https://proceedings.neurips.cc/paper/2019/file/5103c3584b063c431bd1268e9b5e76fb-Paper.pdf>,
  <https://arxiv.org/pdf/1905.03222>
- Reference implementation — <https://github.com/yromano/cqr>

### Time series: exchangeability is violated

Quarterly revenue is neither i.i.d. nor exchangeable — there is trend, seasonality, and regime
change. Two adaptations:

**Adaptive Conformal Inference (ACI)** (Gibbs & Candès, NeurIPS 2021). Treat the miscoverage level
as an online-learned parameter. After each period, observe whether the interval covered
(`err_t ∈ {0,1}`) and update:

```
α_{t+1} = α_t + γ · ( α − err_t ),        γ > 0
```

If you just missed (`err_t = 1`), `α_{t+1}` decreases → next interval widens. If you covered,
`α_{t+1}` increases → interval narrows. Long-run empirical coverage converges to `1 − α`
*irrespective of the data-generating process*, which is exactly the robustness you need across a
regime break.

- <https://papers.neurips.cc/paper/2021/file/0d441de75945e5acbc865406fc9a2559-Paper.pdf>,
  <https://doi.org/10.48550/arxiv.2106.00170>
- Analysis of the width cost relative to split conformal —
  <https://icml.cc/media/icml-2022/Slides/17818.pdf>

```python
def aci_update(alpha_t, covered, alpha_target=0.10, gamma=0.02):
    """One ACI step. `covered` is True if the last interval contained the actual."""
    err = 0.0 if covered else 1.0
    return float(np.clip(alpha_t + gamma * (alpha_target - err), 1e-4, 1 - 1e-4))
```

Choose `γ` by the timescale you want to adapt over: `γ ≈ 0.02–0.05` for quarterly data adapts across
roughly 20–50 quarters; larger `γ` tracks faster but adds interval-width volatility.

**EnbPI** (Xu & Xie, ICML 2021). Wraps a bootstrap ensemble to produce sequential prediction
intervals with approximately valid marginal coverage under *strongly mixing* errors rather than
exchangeability, and requires neither data splitting nor training multiple ensembles from scratch —
it aggregates already-trained bootstrap estimators. Well suited when you can afford an ensemble and
want to avoid sacrificing observations to a calibration set, which is a real concern at `T = 30`.

- <https://proceedings.mlr.press/v139/xu21h.html>

**Newer conformal-control variants** refine the ACI controller (Angelopoulos–Candès–Tibshirani;
Gibbs–Candès 2024; Zaffran et al.; neural conformal control). Survey with the lineage:
<https://ojs.aaai.org/index.php/AAAI/article/view/34029/36184>

**Practical guidance at `T = 30`:** you cannot afford a 200-point calibration set. Use ACI on the
rolling-origin backtest residuals (each fold supplies one calibration point, and ACI needs no held-
out block), or pool calibration residuals across peer companies (Section C.4), or use EnbPI.

## B.8 Bayesian hierarchical models and posterior predictive distributions

The posterior predictive distribution is the natural probabilistic forecast, and it is the only
method here that propagates *parameter* uncertainty properly — which is precisely what dominates
when `T = 30`:

```
p( ỹ | y )  =  ∫  p( ỹ | θ ) · p( θ | y )  dθ
```

Hierarchical structure for a peer panel of enterprise-software companies:

```
  y_{i,t}   ~  Normal( μ_{i,t}, σ_i² )              company i, quarter t
  μ_{i,t}   =  level_{i,t} + seasonal_{i,t}
  growth_i  ~  Normal( γ, τ² )                      partial pooling across companies
  γ         ~  Normal( g₀, s₀² )                    population prior
  τ, σ_i    ~  half-Normal / half-t
```

The population prior `p(φ)` shrinks extreme or uncertain company-level estimates toward the
population mean while allowing genuine heterogeneity — "particularly valuable for series with noisy
or incomplete data, as they can be informed by the related series." This is the mechanism by which a
company with 20 quarters borrows effective sample size from 40 peers.

- Hierarchical Bayes for level-focused probabilistic forecasting, with partial pooling and
  reconciliation — <https://arxiv.org/html/2606.23009>
- Bayesian grouped random effects for firm panels; failing to pool "severely deteriorates the
  results for both estimation and forecasting" — <https://doi.org/10.2139/ssrn.3681672>
- Bayesian panel local projections with hierarchical partial pooling across units —
  <https://www.marcoschwarzbach.de/uploads/BayesianPanelLocalProjections.pdf>

**The shrinkage caveat, stated plainly.** Pooling trades variance for bias. If your target company
genuinely differs from the panel — a category leader, a hypergrowth outlier, a company mid-
transition — shrinking its growth rate toward the peer mean makes the forecast *worse*. The
literature calls this the "tyranny of the majority." Remedies: (i) let the data choose the pooling
weight via a hierarchical variance parameter rather than fixing it; (ii) use individual-weight
shrinkage that targets per-company rather than group accuracy and requires no distributional
assumption, which is explicitly advantageous under heavy tails; (iii) pool within tight cohorts
(similar growth band, ACV band, go-to-market motion), not across the whole universe.

- Individual shrinkage for random effects, short-`T` panels —
  <https://doi.org/10.48550/arxiv.2308.01596>

## B.9 Bootstrapping residuals

The cheapest defensible route from a point model to a distribution, requiring only that residuals be
uncorrelated with constant variance — no normality.

For a fitted model with one-step residuals `{e_t}`, simulate forward by resampling:

```
y*_{T+1} = ŷ_{T+1|T} + e*_{T+1}
y*_{T+2} = ŷ_{T+2|T+1}( with y*_{T+1} substituted ) + e*_{T+2}
...
```

Repeat `B` times (fpp3 uses 5,000 by default) and take percentiles of the sample paths at each
horizon. Intervals are automatically **asymmetric** — a large advantage for revenue, whose downside
and upside risk genuinely differ.

- fpp3 §5.5 — <https://otexts.com/fpp3/prediction-intervals.html>
- Python equivalent — <https://otexts.com/fpppy/05-toolbox.html>

```python
def bootstrap_paths(y, fit_predict_one_step, resid, h=8, B=5000, rng=None):
    """fit_predict_one_step(history) -> next-period point forecast."""
    rng = rng or np.random.default_rng(0)
    resid = np.asarray(resid, dtype=float)
    resid = resid - resid.mean()            # centre: bootstrap must not import bias
    paths = np.empty((B, h))
    for b in range(B):
        hist = list(y)
        for j in range(h):
            nxt = fit_predict_one_step(np.asarray(hist)) + rng.choice(resid)
            paths[b, j] = nxt
            hist.append(nxt)
    return paths      # np.quantile(paths, q, axis=0) -> quantile fan
```

**Two adjustments for quarterly revenue.**

*Block bootstrap.* Quarterly residuals are frequently serially correlated (a missed quarter tends to
be followed by another). Resampling i.i.d. destroys that structure and understates multi-quarter
risk. Use a moving-block bootstrap with block length 2–4 quarters.

*Do not resample across a regime break.* Residuals from a 40%-growth era are not exchangeable with
residuals from a 15%-growth era. Either resample only from the recent regime (accepting a smaller
residual pool) or model the level shift explicitly.

## B.10 Ensembles and mixture distributions

**The correct way to combine probabilistic forecasts is a mixture of the distributions, not an
average of their quantiles.** For component CDFs `F_k` with weights `w_k`:

```
Linear pool:      F̄(y) = Σ_k  w_k · F_k(y)         ← correct (average the CDFs vertically)
Vincentization:   q̄(τ) = Σ_k  w_k · q_k(τ)          ← averages the quantiles horizontally
```

These differ. The linear pool is generally *wider* than any component — it adds between-model
disagreement to within-model uncertainty, which is what you want when models genuinely disagree.
Quantile averaging suppresses that disagreement. In sampling terms, the linear pool is trivial:
concatenate the samples from each model in proportion to `w_k`.

```python
def linear_pool(sample_sets, weights, n_out=200_000, rng=None):
    """Mixture (linear pool) of predictive distributions given as sample arrays."""
    rng = rng or np.random.default_rng(0)
    w = np.asarray(weights, dtype=float); w = w / w.sum()
    counts = rng.multinomial(n_out, w)
    return np.concatenate([
        rng.choice(s, size=c, replace=True) for s, c in zip(sample_sets, counts) if c
    ])
```

Empirical support for combining *intervals* specifically: the M4 interval submissions overall
"fail to estimate the uncertainty properly," but interval aggregation improved **both calibration
and accuracy**, with the median and interior-trimmed average being robust aggregators across all
100,000 series.

- Grushka-Cockayne & Jose, "Combining Prediction Intervals in the M4 Competition" —
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3329413>

## B.11 Scenario trees with explicit probability weights

Use when the dominant uncertainty is discrete and nameable — a specific mega-deal, a reorganization,
a pending regulatory decision, a macro regime break. Scenario trees are auditable and communicable
in a way Monte Carlo output is not.

Discipline requirements:

1. **Weights must sum to 1 and be stated numerically.** "Base / bull / bear" without numbers is not
   a probabilistic forecast.
2. **Weights must be scored.** Log them, resolve them, and compute the Brier score of the scenario
   that materialized. Unscored scenario weights drift toward whatever is politically comfortable.
3. **Each leaf carries a distribution, not a point.** The tree captures discrete risk; continuous
   uncertainty still lives inside each branch. The overall forecast is the linear pool over leaves —
   `F(y) = Σ_leaves p_leaf · F_leaf(y)` — which is exactly Section B.10.
4. **Use base rates for the weights, not vibes.** "What fraction of deals at this stage, this size,
   with this competitor, closed in the quarter historically?" (Sections D.2, D.5.)
5. **Keep the tree small.** 3–5 leaves. Beyond that, elicited weights are noise and you should be
   running Monte Carlo instead.

A well-built scenario tree and a Monte Carlo are the same object at different resolutions; choose by
whether the dominant risk is discrete (tree) or diffuse (simulation), and use a tree-of-simulations
when it is both — which for high-`HHI` enterprise quarters, it usually is.

## B.12 Aggregation: the sum-of-quantiles trap

### The trap

**`Σ_s q_τ(R_s) ≠ q_τ( Σ_s R_s )` for `τ ≠ 0.5`, and the error is large.** The quantile operator is
not additive. Han et al. state and prove the non-additive property formally: for independent
`X₁ ~ N(μ₁,σ₁²)`, `X₂ ~ N(μ₂,σ₂²)` and `Y = X₁ + X₂`, `Q_Y(τ) ≠ Q_{X₁}(τ) + Q_{X₂}(τ)`.

Intuition: for the sum to hit its 90th percentile, *not every* segment must hit its own 90th
percentile — some over-perform while others under-perform, and the diversification cancels. Adding
per-segment `q_{0.9}` values silently assumes every segment simultaneously lands at its own 90th
percentile, which is a near-comonotonic scenario, not a 90th-percentile scenario.

**Measured** (5 independent lognormal segments, mean 100 each, `σ_log = 0.35`, 200,000 draws):

```
Σ of per-segment q₀.₉₀     =  782.37
q₀.₉₀ of the summed draws  =  643.91          →  overstatement of  21.5%
```

Summing quantiles overstated the 90th percentile of total revenue by 21.5%. This error is in the
*conservative* direction for an upper quantile and the *anti*-conservative direction for a lower
quantile (`Σ q_{0.1}` is too low). Either way the reported interval is far too wide, the model looks
badly over-dispersed, and its PIT histogram will be hump-shaped for reasons that have nothing to do
with the model.

- Non-additivity theorem — <https://proceedings.mlr.press/v130/han21a/han21a-supp.pdf>
  (main paper: <https://proceedings.mlr.press/v130/han21a/han21a.pdf>)

### The correct approach

**Aggregate at the sample-path level, then take quantiles.** Never aggregate quantiles.

```python
def aggregate_segments(segment_samples, corr_matrix=None):
    """segment_samples: list of (n_sims,) arrays, all the SAME length, paired draw-for-draw.
    Returns (n_sims,) total-revenue draws.
    """
    X = np.column_stack(segment_samples)
    if corr_matrix is not None:
        X = iman_conover(X, corr_matrix)      # couple the segments BEFORE summing
    return X.sum(axis=1)

# then, and only then:
#   total = aggregate_segments(...)
#   quantiles = np.quantile(total, [0.05, 0.25, 0.50, 0.75, 0.95])
```

The critical detail is that draw `i` of every segment must represent *the same simulated world*.
Independent simulation and column-wise pairing implicitly assumes independence; Iman–Conover or a
shared macro factor is what makes the pairing meaningful.

### If you only have quantiles and cannot re-simulate

1. **Reconstruct a distribution per segment** from its quantiles (monotone spline / piecewise-
   linear on the quantile function), sample from each, couple, and sum. This is the standard fix.
2. **Analytic approximation.** If segments are approximately lognormal, use a Fenton–Wilkinson
   moment match on the sum. Adequate for a sanity check, not for tails.
3. **Copula-based reordering.** Ben Taieb, Taylor & Hyndman construct coherent hierarchical
   probabilistic forecasts bottom-up by reordering quantile forecasts to model inter-node
   dependence — <https://proceedings.mlr.press/v70/taieb17a/taieb17a.pdf>

### Coherent hierarchical reconciliation

If you forecast at multiple levels (total, segment, geography) the forecasts must be **coherent** —
satisfy the aggregation constraints. Independently produced forecasts never are: "independent series
cannot be coherent since the aggregation constraint induces dependence between the variables."

The general point-forecast machinery is `ỹ = S P ŷ`, with `MinT` choosing
`P = (Sᵀ W_h⁻¹ S)⁻¹ Sᵀ W_h⁻¹` to minimize the sum of reconciled error variances. For
*probabilistic* reconciliation, the operationally simple result is:

> Simulate `B` sample paths from the base models, reconcile **each path**, and read percentiles off
> the reconciled paths. If `(ŷ_h^{(1)}, …, ŷ_h^{(B)})` are simulated paths, then
> `(S G ŷ_h^{(1)}, …, S G ŷ_h^{(B)})` are reconciled paths from which coherent prediction intervals
> follow.

- fpp3 §11.5 (reconciled distributional forecasts) — <https://otexts.com/fpp3/rec-prob.html>
- Panagiotelis et al. probabilistic reconciliation results, implemented in `reconcile()`
- Ben Taieb, Taylor & Hyndman (ICML 2017) — <https://proceedings.mlr.press/v70/taieb17a/taieb17a.pdf>
- Jeon, Panagiotelis & Petropoulos, probabilistic reconciliation —
  <https://www.sciencedirect.com/science/article/abs/pii/S0377221719304242>
- MinT and end-to-end coherent learning — <https://proceedings.mlr.press/v139/rangapuram21a/rangapuram21a.pdf>

**One warning from the reconciliation literature:** hard coherence constraints can make accuracy
*worse* than the base forecasts. Check reconciled scores against unreconciled ones before adopting.

---

# Part C — Scoring, calibration, and backtesting

## C.1 Proper scoring rules

### Definition and why propriety is non-negotiable

A scoring rule `S(P, x)` assigns a number to predictive distribution `P` and realized outcome `x`.
Writing it as a **loss** to be minimized, `S` is **proper** relative to a class `P` if

```
S(Q, Q)  ≤  S(P, Q)      for all  P, Q ∈ P
```

and **strictly proper** if equality holds only when `P = Q`. Propriety means a forecaster's expected
score is optimized by reporting their true belief; an improper rule can be gamed by reporting
something other than what you believe. Gneiting & Raftery present a case study showing "a striking
example of the potential issues that result from the use of intuitively appealing but improper
scoring rules."

- Gneiting & Raftery, *JASA* 102(477):359–378 —
  <https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf>
- Modern review — <https://arxiv.org/html/2504.01781v1>,
  <https://www.annualreviews.org/content/journals/10.1146/annurev-statistics-042424-050626>
- `scoringRules` software paper — <https://doi.org/10.18637/jss.v090.i12>

### CRPS — continuous ranked probability score

The default score for real-valued probabilistic forecasts. Gneiting & Raftery: it "enjoys appealing
properties and might serve as a standard score in evaluating probabilistic forecasts of real-valued
variables."

```
                  ∞
CRPS(F, x)  =   ∫    ( F(y) − 1{ y ≥ x } )² dy                         (integral form, Eq. 20)
                 −∞
```

It is the integral of the Brier score over all real-valued thresholds. Closed forms:

```
CRPS(F, x)  =  E_F | X − x |  −  ½ · E_F | X − X' |                     (energy form, Eq. 21)

               where X, X' are independent copies from F with finite first moment

CRPS( N(μ, σ²), x )  =  σ · [  z ( 2Φ(z) − 1 )  +  2φ(z)  −  1/√π  ],   z = (x − μ)/σ
```

Properties that matter:

- **Same units as the data** (dollars), so it is directly interpretable and reportable.
- **Reduces to absolute error** when `F` is a point mass. So CRPS is a strict generalization of MAE:
  you can compare a probabilistic model to a point forecast on one scale.
- **Strictly proper** for all `F` with finite first moment — `F` need not have a density.
- **Distance-sensitive**, rewarding probability mass placed near the outcome; contrast the
  logarithmic score, which "assigns harsh penalties regardless of the overall closeness of the
  forecast to the observations if the forecast density at any of the observations is too low."

```python
import numpy as np

def crps_sample(samples, y):
    """Sample-based CRPS via the energy form. O(n log n).

    CRPS = E|X - y| - 0.5 * E|X - X'|
    For the empirical distribution of sorted x:
        E|X - X'| = (2/n^2) * sum_i (2i - n + 1) * x_i    (i zero-indexed)
    """
    x = np.sort(np.asarray(samples, dtype=float))
    n = x.size
    i = np.arange(n)
    e_xy = np.mean(np.abs(x - y))
    e_xx = (2.0 / n**2) * np.sum((2 * i - n + 1) * x)
    return e_xy - 0.5 * e_xx

def crps_gaussian(mu, sigma, y):
    from scipy import stats
    z = (y - mu) / sigma
    return sigma * (z * (2 * stats.norm.cdf(z) - 1) + 2 * stats.norm.pdf(z) - 1 / np.sqrt(np.pi))
```

**Verified:** for `N(100, 12²)` and `x = 108`, the sample estimator over 400,000 draws gave
**4.8565**; the closed form gave **4.8566**.

### Pinball loss (quantile loss) and its relationship to CRPS

For quantile level `τ` and quantile forecast `q`:

```
L_τ(y, q)  =  ( y − q ) · τ            if  y ≥ q
              ( q − y ) · ( 1 − τ )    if  y <  q

equivalently   L_τ(y, q) = ρ_τ(y − q),   ρ_τ(u) = u·( τ − 1{u < 0} )
```

Minimized in expectation by the true `τ`-quantile — so it is proper for quantile elicitation.
The connection to CRPS:

```
                  1
CRPS(F, x)  =  2 ∫   L_τ( x, F⁻¹(τ) ) dτ
                 0
```

**Verified:** the same `N(100,12²)`, `x = 108` case gave `2 × mean(pinball over 2,000 τ values) =
4.859` against CRPS `4.857`. **A weighted average of pinball losses across a quantile grid is a
discrete approximation to CRPS.** If you report quantiles rather than full distributions, average
pinball loss is the right score and it is a proper one.

```python
def pinball_loss(y, q, tau):
    d = np.asarray(y, dtype=float) - np.asarray(q, dtype=float)
    tau = np.asarray(tau, dtype=float)
    return np.where(d >= 0, tau * d, (tau - 1.0) * d)

def mean_pinball_over_grid(y, quantile_preds, taus):
    """quantile_preds: (n_obs, n_taus). Discrete CRPS approximation = 2 * this."""
    y = np.asarray(y, dtype=float)[:, None]
    return pinball_loss(y, np.asarray(quantile_preds, dtype=float), np.asarray(taus)[None, :]).mean()
```

### Scaled pinball loss (SPL / WSPL) — the M5 metric

M5 required nine quantiles — `0.005, 0.025, 0.165, 0.250, 0.500, 0.750, 0.835, 0.975, 0.995` —
corresponding to the median plus the 50%, 67%, 95%, and 99% intervals:

```
                (1/h) Σ_{t=n+1}^{n+h} [ τ (y_t − q_t(τ)) 1{q_t(τ) ≤ y_t}
                                        + (1−τ)(q_t(τ) − y_t) 1{q_t(τ) > y_t} ]
SPL_i(τ)  =  ────────────────────────────────────────────────────────────────────
                          (1/(n−1)) Σ_{t=2}^{n} | y_t − y_{t−1} |

                N            1   Q
WSPL      =    Σ    w_i  ·  ───  Σ   SPL_i(τ_j)
               i=1           Q  j=1
```

The denominator is the in-sample one-step naive MAE — the same scaling idea as MASE, making SPL
comparable across series of different magnitudes.

- Makridakis et al., "The M5 uncertainty competition: Results, findings and conclusions," *IJF*
  38(4):1365–1385 — <https://doi.org/10.1016/j.ijforecast.2021.10.009>
- Formula as implemented by competitors — <https://doi.org/10.1016/j.ijforecast.2022.01.001>,
  <https://arxiv.org/pdf/2311.00993>

**For an enterprise revenue skill, adopt exactly the M5 quantile grid.** It gives the median plus
four nested intervals, is standard, and lets you compute a proper score, coverage at four levels,
and PIT diagnostics from the same nine numbers.

### Logarithmic score

```
LogS(f, x)  =  − log f(x)
```

Strictly proper; equals negative predictive log-likelihood; the score whose expectation is minimized
at the true density and whose sample average underlies Bayes factors and cross-validation.

**Do not use it as the primary score for revenue.** It is not distance-sensitive and is infinitely
harsh: a single outcome in a region where your predictive density is ~0 gives `+∞`. With one
regime-breaking quarter in a 24-fold backtest, log score is unusable. Report it as a secondary
diagnostic; rank on CRPS.

### Brier score (binary events)

```
BS  =  (1/n) Σ_i  ( p_i − o_i )²,        o_i ∈ {0, 1}
```

Strictly proper. Use for the binary sub-forecasts inside a revenue model: *will this named deal
close this quarter*, *will we beat guidance*, *will this account churn*, *will the scenario
materialize*. Murphy's decomposition:

```
BS  =  reliability  −  resolution  +  uncertainty
        (calibration)   (discrimination)  (base-rate difficulty, irreducible)
```

`reliability` is what calibration training reduces; `resolution` is what genuine information buys;
`uncertainty = p̄(1−p̄)` is the base-rate floor and is not yours to improve. This decomposition is
the accountability framework used in the Good Judgment Project — good calibration means average
confidence matches hit rate; good resolution means being decisively right rather than hedging at
40–60%.

- <https://commoncog.com/how-do-you-evaluate-your-own-predictions/>

### Interval / Winkler score

For a central `(1−α)·100%` interval with endpoints `l` (the `α/2` quantile) and `u` (the `1−α/2`
quantile), the negatively-oriented interval score (Gneiting & Raftery Eq. 43; traceable to
Dunsmore 1968 and Winkler 1972):

```
S^int_α( l, u; x )  =  ( u − l )  +  (2/α)( l − x ) 1{ x < l }  +  (2/α)( x − u ) 1{ x > u }
```

Proper, and it addresses **width as well as coverage** in one number: the forecaster is rewarded for
narrow intervals and penalized proportionally to how far outside the interval the outcome fell, with
penalty severity scaling as `2/α`. At `α = 0.05` an excursion is penalized at 40× the excursion
amount — which is exactly the property that stops you from gaming coverage with absurdly wide
intervals.

The M4 scaled version (MSIS) divides by the in-sample mean absolute seasonal difference:

```
                (1/h) Σ_t [ (u_t − l_t) + (2/α)(l_t − y_t)1{y_t < l_t} + (2/α)(y_t − u_t)1{y_t > u_t} ]
MSIS   =   ──────────────────────────────────────────────────────────────────────────────────────────────
                                (1/(T−m)) Σ_{t=m+1}^{T} | z_t − z_{t−m} |
```

M4 used `α = 0.05`.

- <https://doi.org/10.3390/forecast3010010>
- <https://mlr3forecast.mlr-org.com/reference/mlr_measures_fcst.msis.html>
- <https://usermanual.wiki/Document/M4CompetitorsGuide.1491768831/html>

```python
def interval_score(y, lower, upper, alpha):
    y, lower, upper = map(lambda a: np.asarray(a, dtype=float), (y, lower, upper))
    return ((upper - lower)
            + (2.0 / alpha) * (lower - y) * (y < lower)
            + (2.0 / alpha) * (y - upper) * (y > upper))

def msis(y, lower, upper, alpha, train, m=4):
    denom = np.mean(np.abs(np.asarray(train[m:], dtype=float) - np.asarray(train[:-m], dtype=float)))
    return interval_score(y, lower, upper, alpha).mean() / denom
```

## C.2 Point-error metrics and the specific pathologies of MAPE

### Definitions

```
MAE    = mean( |y_t − ŷ_t| )
RMSE   = sqrt( mean( (y_t − ŷ_t)² ) )                 minimized by the MEAN
MdAE   = median( |y_t − ŷ_t| )                        robust to one bad quarter
MAPE   = 100 · mean( |y_t − ŷ_t| / |y_t| )
sMAPE  = 200 · mean( |y_t − ŷ_t| / (|y_t| + |ŷ_t|) )
WAPE   = Σ |y_t − ŷ_t| / Σ |y_t|                      a.k.a. MAD/Mean ratio
MASE   = mean( |e_t| ) / [ (1/(T−m)) Σ_{t=m+1}^{T} |y_t − y_{t−m}| ]
RMSSE  = sqrt( mean(e_t²) / [ (1/(T−m)) Σ (y_t − y_{t−m})² ] )
ME     = mean( y_t − ŷ_t )                            BIAS — always report this
MPE    = 100 · mean( (y_t − ŷ_t) / y_t )              percentage bias
```

`MAE` is minimized by the conditional *median*, `RMSE` by the conditional *mean*. If you optimize
`MAE` and then report the mean, you have a mismatch. State which functional you are targeting.

### Why point metrics alone are inadequate

1. **They score a summary, not the forecast.** Two models with identical MAE can differ completely
   in stated uncertainty — one honest, one wildly overconfident. Point metrics cannot distinguish
   them. Only a proper score over the full distribution can.
2. **They are not decision-relevant.** Revenue decisions (guidance, hiring, capacity) depend on
   `P(R < threshold)`, not on `E[R]`.
3. **They reward the wrong behavior under asymmetric loss.** If missing guidance is worse than
   sandbagging, the optimal *decision* is a quantile, not a mean, and MAE ranks it as worse.
4. **They hide bias.** A model with `+5%` bias and one with `±5%` symmetric noise can share the same
   MAE. Always report `ME`/`MPE` alongside.

### The specific pathologies of MAPE

Hyndman & Koehler's finding is blunt: the measures used in the M-competition and M3 "are found to be
degenerate in commonly occurring situations."

| # | Pathology | Consequence for revenue forecasting |
|---|---|---|
| 1 | **Undefined / infinite when `y_t = 0`; explodes when `y_t` is small** | Fatal for new-product lines, new geos, per-segment forecasts with early-stage segments |
| 2 | **Asymmetric: penalizes over-forecasts more than under-forecasts** | `y=100, ŷ=150` → MAPE 50%. `y=100, ŷ=50` → MAPE 50%. But `y=50, ŷ=100` → **100%**. Optimizing MAPE systematically biases forecasts *downward*. This alone disqualifies it as an objective. |
| 3 | **No meaningful zero point required** | "Percentage error makes no sense when the unit of measurement has an arbitrary zero" — e.g. any net or delta measure (net new ARR, which can be negative) |
| 4 | **Unbounded above, bounded below by 0** | The mean is dominated by a handful of small-denominator quarters |
| 5 | **Diebold–Mariano statistic does not follow its asymptotic distribution** | You cannot do valid significance testing on MAPE differences. MASE has been shown empirically to approximate the distribution; MRAE, MAPE and sMAPE do not. |
| 6 | **Cross-series comparison is misleading** | A high-growth company's MAPE is not comparable to a mature company's, because the denominator is systematically moving |

sMAPE was designed to fix asymmetry and **does not**: fpp3 states outright that "the sMAPE not be
used. It is included here only because it is widely used." It fails the equal-penalty-for-large-and-
small-forecasts criterion, is unstable when both `y` and `ŷ` approach zero, and can be negative.

- Hyndman & Koehler — <https://robjhyndman.com/papers/mase.pdf>
- fpp3 §5.8 — <https://otexts.com/fpp3/accuracy.html>
- Properties incl. the DM-distribution point — <https://en.wikipedia.org/wiki/Mean_absolute_scaled_error>

### When each is appropriate

| Metric | Use it when | Avoid when |
|---|---|---|
| **MASE** | Comparing across series/companies/scales; the default point metric | All historical observations equal (denominator 0) |
| **RMSSE** | Same, but you care about large errors (M5 point track used it) | Heavy-tailed errors dominate the average |
| **WAPE** | Aggregating across many segments of different sizes; naturally revenue-weighted | Individual small segments matter for the decision |
| **MAE** | All series on the same scale, single company, audience wants dollars | Cross-series comparison |
| **RMSE** | You are targeting the conditional mean and large misses are disproportionately costly | Outlier quarters (one restatement dominates) |
| **MdAE** | Short backtests with a known outlier quarter | You need a differentiable objective |
| **MAPE** | Only when all values are strictly positive and far from zero, and the audience insists | Anything with zeros, negatives, or near-zeros; **never as an optimization objective** |
| **sMAPE** | Reproducing M4-comparable numbers only | Everything else |
| **ME / MPE** | Always, as a companion to any of the above | Never omit |

Hyndman & Koehler's own concession is worth quoting for honesty: "if all series are on the same
scale, then the MAE may be preferred because it is simpler to explain. If all data are positive and
much greater than zero, the MAPE may still be preferred for reasons of simplicity."

## C.3 Calibration diagnostics and recalibration

### The organizing principle

Gneiting, Balabdaoui & Raftery: **the goal of probabilistic forecasting is to maximize the sharpness
of the predictive distributions subject to calibration.**

- **Calibration** = statistical consistency between forecasts and observations. A *joint* property
  of forecasts and outcomes. **A necessary condition — a miscalibrated forecast is untrustworthy no
  matter how sharp.**
- **Sharpness** = concentration of the predictive distributions. A property of the forecasts *only*.
  The tie-breaker among calibrated forecasts.

The paper distinguishes **probabilistic**, **exceedance**, and **marginal** calibration, and
proposes the PIT histogram, marginal calibration plots, sharpness diagrams, and proper scoring rules
as the diagnostic toolkit.

- Gneiting, Balabdaoui & Raftery, *JRSS-B* 69(2):243–268 (2007) —
  <https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jrssb.pdf>,
  <https://doi.org/10.1111/j.1467-9868.2007.00587.x>

### PIT histogram

For predictive CDF `F_t` and outcome `y_t`, the probability integral transform is `p_t = F_t(y_t)`.
If the forecasts are probabilistically calibrated, `{p_t}` is i.i.d. **Uniform(0,1)**. Plot the
histogram and look for departures from flat:

| PIT histogram shape | Diagnosis | Fix |
|---|---|---|
| **Flat / uniform** | Calibrated | Now maximize sharpness |
| **∪-shaped** (mass at both ends) | Predictive distributions **too narrow** — under-dispersed, overconfident | Inflate variance / widen intervals |
| **∩-shaped** (hump in middle) | Predictive distributions **too wide** — over-dispersed, underconfident | Deflate variance / sharpen |
| **Triangular / sloped** | **Biased** predictive distributions | Correct the location first |

Two summary statistics make this quantitative:

```
E[PIT]   should be  1/2       — any departure indicates BIAS
Var[PIT] should be  1/12 ≈ 0.0833  — the variance of Uniform(0,1)
         > 1/12  →  UNDER-dispersion (too narrow)
         < 1/12  →  OVER-dispersion (too wide)
```

- Shape interpretation, quoted from the source: "Hump-shaped histograms indicate overdispersed
  predictive distributions with prediction intervals that are too wide on average. U-shaped
  histograms often correspond to predictive distributions that are too narrow. Triangle-shaped
  histograms are seen when the predictive distributions are biased."
- `E[PIT]`/`Var[PIT]` diagnostics — <https://rdrr.io/github/jobstdavid/eppverification/man/pit.hist.html>
- Miscalibration quantified as KL divergence from uniform (equivalently negentropy of the PIT
  distribution) — <https://www.stat.cmu.edu/~ryantibs/papers/recalib.pdf>

**Verified** (5,000 draws from `N(0,5)`, scored under three predictive distributions):

```
                E[PIT]   Var[PIT]   KS p-value    diagnosis
sigma = 3        0.508    0.1318      5e-73       under-dispersed  (Var >> 1/12)
sigma = 5        0.507    0.0833      0.177       calibrated
sigma = 9        0.504    0.0378      2e-94       over-dispersed   (Var << 1/12)
```

```python
import numpy as np
from scipy import stats

def pit_values_from_samples(y, sample_matrix):
    """y: (n,) actuals. sample_matrix: (n, n_sims) predictive draws per observation.
    Randomized PIT handles ties/atoms; for continuous forecasts the jitter is negligible.
    """
    y = np.asarray(y, dtype=float)
    S = np.asarray(sample_matrix, dtype=float)
    below = (S < y[:, None]).mean(axis=1)
    equal = (S == y[:, None]).mean(axis=1)
    u = np.random.default_rng(0).random(y.size)
    return below + u * equal

def pit_report(pit, n_bins=10):
    pit = np.asarray(pit, dtype=float)
    counts, edges = np.histogram(pit, bins=n_bins, range=(0.0, 1.0))
    expected = pit.size / n_bins
    chi2 = ((counts - expected) ** 2 / expected).sum()
    return {
        "n": int(pit.size),
        "mean": float(pit.mean()),                 # target 0.5      -> bias
        "var": float(pit.var()),                   # target 0.08333  -> dispersion
        "ks_pvalue": float(stats.kstest(pit, "uniform").pvalue),
        "chi2": float(chi2),
        "chi2_pvalue": float(stats.chi2.sf(chi2, n_bins - 1)),
        "counts": counts.tolist(),
        "diagnosis": (
            "biased"           if abs(pit.mean() - 0.5) > 0.06 else
            "under-dispersed"  if pit.var() > 0.095 else
            "over-dispersed"   if pit.var() < 0.072 else
            "calibrated"
        ),
    }
```

**Order of operations, and this trips people up.** Bias masquerades as over-dispersion in
`Var[PIT]`. Verified: errors drawn from `N(−9, 10²)` but scored against a correctly-scaled
`N(0, 10²)` gave `Var[PIT] = 0.0619` (apparent over-dispersion) with `E[PIT] = 0.267`. After
centering the predictive mean on the empirical error mean, `Var[PIT] = 0.0849` and `E[PIT] = 0.500`
— revealing the dispersion was fine all along. **Always check `E[PIT]` and correct bias before
touching dispersion.**

With `K = 20–30` backtest folds, a PIT histogram has 2–3 observations per decile bin. Use `n_bins`
of 4 or 5, rely on the KS test and the two summary statistics rather than eyeballing the shape, and
report the sample size next to the diagnosis.

### Reliability diagram (binary events)

For binary sub-forecasts (deal closes, guidance beat, churn), bin forecasts by predicted
probability and plot observed frequency against mean predicted probability in each bin. The 45°
line is perfect calibration; below it is overconfidence. Report **Expected Calibration Error**:

```
ECE  =  Σ_b  ( n_b / n ) · | ō_b − p̄_b |
```

### Coverage of prediction intervals

For each nominal level, report empirical coverage and the deviation:

```
coverage(1−α)  =  (1/n) Σ_t  1{ l_t ≤ y_t ≤ u_t }
coverage difference  =  coverage(1−α)  −  (1−α)
```

M4 used exactly this alongside MSIS: "For a 95% pointwise interval, we aim to be outside in about 5%
of cases, corresponding to a coverage difference of close to zero."

**Never report coverage without interval width.** Coverage is trivially gamed by widening. The
interval score (Section C.1) combines both, which is why it is the score and coverage is the
diagnostic.

**Coverage at `K = 24` folds is a noisy statistic.** For nominal 90%, the standard error of
empirical coverage is `sqrt(0.9·0.1/24) ≈ 6.1pp`, so realized coverage between roughly 78% and 100%
is consistent with a correctly-calibrated model. Do not "fix" calibration on the basis of one
backtest's coverage number.

### Recalibration

**(1) Variance inflation.** Simplest; assumes the distributional shape is right and only the scale
is wrong. Estimate on held-out data:

```
λ  =  sqrt(  mean_t  [ ( y_t − μ_t )² / σ_t² ]  )

then use  σ'_t = λ · σ_t
```

**Verified:** with true error sd 10 and model `σ = 6` (under-dispersed, `Var[PIT] = 0.1312`),
`λ = 1.666` restored `Var[PIT] = 0.0833` exactly. With model `σ = 18` (over-dispersed,
`Var[PIT] = 0.0379`), `λ = 0.555` also restored `0.0833`. Bias must be removed first.

```python
def variance_inflation_factor(actuals, mus, sigmas):
    a, m, s = (np.asarray(v, dtype=float) for v in (actuals, mus, sigmas))
    return float(np.sqrt(np.mean(((a - m) / s) ** 2)))
```

**(2) Isotonic / Platt recalibration (Kuleshov, Fenner & Ermon, ICML 2018).** Distribution-free and
guaranteed calibrated given enough data. Fit an auxiliary monotone map `R` on a held-out calibration
set:

```
Build the dataset   { ( F_t(y_t) ,  P̂[ PIT ≤ F_t(y_t) ] ) }_{t=1..n}
   i.e. { ( p_t , empirical CDF of the PIT values at p_t ) }

Fit  R : [0,1] → [0,1]  by ISOTONIC regression   (monotone, non-parametric)

Recalibrated forecast:   F'_t  =  R ∘ F_t
```

The authors specifically recommend isotonic regression over a sigmoid because the true map
`P(Y ≤ F_X⁻¹(p))` is monotonically increasing and isotonic regression is non-parametric, so it
converges to the truth given enough i.i.d. data. Platt scaling — a sigmoid fit — is the parametric
alternative, cheaper in data and appropriate when you have very few folds. Fit `R` on a *separate*
calibration set, or use `K`-fold with the held-out fold as calibration set and average the `K`
recalibrated outputs at prediction time.

- <https://proceedings.mlr.press/v80/kuleshov18a/kuleshov18a.pdf>, <https://arxiv.org/pdf/1807.00263>

```python
def fit_isotonic_recalibrator(pit_values):
    """Returns R: array of PIT levels -> calibrated CDF values (Kuleshov et al. 2018)."""
    from sklearn.isotonic import IsotonicRegression
    p = np.sort(np.asarray(pit_values, dtype=float))
    empirical = np.arange(1, p.size + 1) / p.size
    return IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(p, empirical)

def recalibrated_quantile(iso, sample_draws, tau):
    """Invert R o F at level tau: find the raw PIT level p with R(p)=tau, then read F^-1(p)."""
    grid = np.linspace(1e-4, 1 - 1e-4, 4000)
    p_star = grid[np.searchsorted(iso.predict(grid), tau, side="left").clip(0, grid.size - 1)]
    return float(np.quantile(sample_draws, p_star))
```

**(3) Conformal adjustment.** The strongest option because it comes with a finite-sample guarantee
rather than an asymptotic one. Apply split conformal or CQR (Section B.7) to your model's intervals;
for a non-stationary quarterly series use ACI, which self-corrects coverage online and needs no
held-out block. **This is the recommended primary recalibration route for a quarterly revenue skill
precisely because it works at small `K`.**

**Choosing among the three at realistic sample sizes:**

| Folds available | Recommended |
|---|---|
| `K < 12` | Variance inflation (1 parameter) + report wide honest uncertainty about the calibration itself |
| `12 ≤ K < 40` | ACI (1 parameter, online, no held-out block) or Platt scaling |
| `K ≥ 40`, or pooled across peers | Isotonic recalibration, or split conformal / CQR with a real calibration block |

## C.4 Backtesting protocol for quarterly financial forecasts

### Rolling-origin evaluation

The only time-respecting validation. fpp3 calls it "evaluation on a rolling forecasting origin":
a series of test sets, each training set containing **only** observations prior to its test
observation, with accuracy averaged over test sets.

- fpp3 §5.10 — <https://otexts.com/fpp3/tscv.html>
- `stretch_tsibble()` / `slide_tsibble()` / `tile_tsibble()` for expanding / sliding / non-
  overlapping windows — <https://robjhyndman.com/hyndsight/tscv-fable/>
- Worked multi-origin example — <https://r-statistics.co/Backtesting-Forecasts-in-R.html>

fpp3 also demonstrates exactly the horizon analysis you need: evaluating 1- to 8-step-ahead
forecasts and plotting RMSE against `h`, which rises with horizon as expected.

```python
import numpy as np

def rolling_origin_backtest(y, model_fn, min_train=16, H=8, window="expanding",
                            window_len=None, as_of_data=None):
    """Rolling-origin backtest returning one row per (origin, horizon).

    y         : (T,) realized target series (POINT-IN-TIME first-reported values)
    model_fn  : (train_y, train_X, h) -> dict with 'point' and optional
                'samples' (n_sims,) / 'quantiles' {tau: value}
    window    : 'expanding' (all history) or 'sliding' (last `window_len`)
    as_of_data: optional callable(origin_index) -> exogenous features KNOWN at that origin.
                This is where look-ahead bias is prevented or introduced.
    """
    y = np.asarray(y, dtype=float)
    T = y.size
    rows = []
    for origin in range(min_train, T):
        start = 0 if window == "expanding" else max(0, origin - (window_len or min_train))
        train_y = y[start:origin]
        train_X = as_of_data(origin) if as_of_data else None
        for h in range(1, H + 1):
            t_target = origin + h - 1
            if t_target >= T:
                break
            out = model_fn(train_y, train_X, h)
            rows.append({
                "origin": origin,
                "h": h,
                "t_target": t_target,
                "actual": y[t_target],
                "point": out["point"],
                "error": out["point"] - y[t_target],
                "samples": out.get("samples"),
                "quantiles": out.get("quantiles"),
            })
    return rows
```

**Verified** on a 40-quarter synthetic series (`min_train=16`, `H=8`): 24 folds, 164
`(origin, horizon)` pairs, `MASE` 3.155 for seasonal naive and 1.140 for naive-with-drift, giving
drift a `+0.639` skill score over seasonal naive.

### Expanding vs sliding window

| | Expanding | Sliding (fixed length) |
|---|---|---|
| Training data | All history to the origin | Last `L` periods only |
| Use when | Data-generating process is stable; you are data-starved | Regime change (post-IPO, post-pivot, post-macro-break) |
| Bias/variance | Lower variance, higher bias if the regime changed | Higher variance, adapts to regime |
| Fold comparability | Later folds have more data — confounds "later" with "better" | Every fold sees the same amount of data — cleaner comparison |
| Quarterly recommendation | **Default** at `T < 40` | Run as a robustness check with `L = 16–20`; if it wins, you have a regime break |

Run both. Divergence between expanding and sliding results is itself the diagnostic that your
history is not homogeneous — which is information you need before you trust either.

### Horizons `h = 1..8`

Report every metric **conditioned on `h`**. A single pooled number hides that `h=1` may be
excellent (mostly contracted) while `h=8` is worthless. Expect the coverage ratio `κ` to decay with
`h` and error to grow correspondingly; the two should track. If they do not, one of them is wrong.

Enterprise-specific structure to expect: `h=1` is dominated by the contracted component, so error is
small and calibration is easy. `h=2–4` is where pipeline data earns its keep. `h=5–8` is a
growth-rate forecast in disguise — the constant-YoY baseline (tier 3) is very hard to beat there,
and honest intervals get wide fast.

### Point-in-time data discipline

This is where financial backtests go wrong most often, and the errors are invisible from inside the
backtest.

**Three distinct leakage mechanisms:**

1. **Publication lag.** `datadate` (fiscal period end) is *not* the date the number was knowable.
   Filing dates lag period ends materially — one measured dataset reports a median gap on the order
   of two months, with large caps filing fastest. Use the actual filing / announcement date.
2. **Revision bias (restatements).** Most databases store one mutable value per period and silently
   overwrite it when a restatement lands. Your backtest then reads the *corrected* number stamped
   with the *original* filing date — information that did not exist on that date. One vendor
   reports 18,529 rows where a later filing revised a previously reported value by more than 0.5% on
   the same XBRL tag. This leak is "concentrated exactly where it hurts: in the companies whose
   numbers turned out to be wrong."
3. **Non-financial as-of leakage.** Consensus estimates, pipeline snapshots, headcount, and
   competitive data all have as-of dates. A pipeline snapshot must be the one that existed at the
   forecast origin — not the cleaned-up version after the quarter closed and stages were
   retroactively corrected.

- <https://tradevodata.com/blog/lookahead-bias-fundamental-backtests>
- <https://bagelquant.com/pit-equity-database/>
- <https://arkolith.com/blog/point-in-time-data-explained>
- <https://developer.stockfit.io/blog/point-in-time-data-backtesting>

**Required practices:**

- **Bitemporal storage.** Keep *event time* (which fiscal period) and *knowledge time* (when the
  fact entered the public record) as separate axes. Query with an explicit as-of date.
- **Backtest on `original_value`, not `latest_value`.** The original as-first-reported figure is what
  the market saw. Reserve restated values for present-day screening.
- **Availability date = `max(announcement_date, publication_date)`.** For Compustat-style data,
  `start_date = max(rdq, pdate)`; `datadate` is a fiscal period end, not a PIT date. Fallback order
  for missing announcement dates: `rdq` → `report_dt` → estimate from the next quarter.
- **Backward `merge_asof` for joins,** never a plain key join:

```python
joined = pd.merge_asof(
    daily.sort_values(["entity", "date"]),
    facts.sort_values(["entity", "available_date"]),
    by="entity", left_on="date", right_on="available_date",
    direction="backward",          # only facts already available
)
joined = joined[joined["date"] <= joined["valid_through"]]
```

- **Assert no leakage as a unit test:**

```python
assert (joined["date"] >= joined["available_date"]).all()
assert (facts["start_date"] <= facts["end_date"]).all()
```

- **Expect performance to drop when you fix this.** If your backtest metrics do not degrade after
  introducing PIT discipline, you have not actually introduced it.

### The small-sample problem, stated honestly

With 20–40 quarterly observations, `min_train = 16`, and `H = 8`, you get roughly `K = 20` origins.
Here is what that does and does not support.

**How many folds do you need?** For a Diebold–Mariano-style test on the mean loss differential, the
number of *independent* folds needed to detect a standardized effect size `d = |E[Δloss]|/sd(Δloss)`
at 80% power and `α = 0.05` is:

```
n  ≈  ( z_{0.025} + z_{0.20} )² / d²  =  ( 1.96 + 0.84 )² / d²  =  7.84 / d²

    d = 0.8 (large)     →  n ≈ 12
    d = 0.5 (medium)    →  n ≈ 31
    d = 0.3 (small)     →  n ≈ 87
    d = 0.2             →  n ≈ 196
```

**And overlapping multi-step forecasts are not independent.** `h`-step forecasts from consecutive
origins share `h−1` periods, inducing serial correlation in the loss differential that inflates its
variance by roughly a factor of `h`. Effective independent folds are approximately `K/h`. At
`K = 20` and `h = 4`, you have about **5 effective observations.**

**Therefore, from ~20 quarters of a single company:**

| Can conclude | Cannot conclude |
|---|---|
| Your model beats a *naive* baseline (large `d`, `d > 0.8`) | Model A beats model B when both are decent (`d < 0.5`) |
| A gross calibration failure (coverage 60% at nominal 90%) | Fine calibration (coverage 87% vs 90%) |
| Bias direction, if consistent and large | Anything about the tails — you have ~1 observation beyond the 95th percentile |
| The rank ordering of *very* different approaches | A stable estimate of the 99th percentile |
| Order-of-magnitude horizon decay in accuracy | A precise `h=7` vs `h=8` difference |

**Use the corrected test, not the raw one.** The Diebold–Mariano statistic is only asymptotically
normal and over-rejects the null of equal accuracy in short samples and for multi-step forecasts.
Harvey, Leybourne & Newbold (1997) rescale it and refer it to a `t` distribution:

```
DM   =  d̄ / sqrt( V̂(d̄) ),        d_t = L(e^A_t) − L(e^B_t)

HLN correction factor  =  sqrt(  ( n + 1 − 2h + h(h−1)/n ) / n  )

HLN statistic = correction × DM,   compared to  t_{n−1}
```

- Diebold & Mariano, *JBES* 13:253–263 (1995) — <https://www.sas.upenn.edu/~fdiebold/papers/paper68/pa.dm.pdf>
- Harvey, Leybourne & Newbold, *IJF* 13(2):281–291 (1997)
- `forecast::dm.test()` implements the HLN modification —
  <https://pkg.robjhyndman.com/forecast/reference/dm.test.html>
- On negative long-run variance estimates in small samples —
  <https://www.sciencedirect.com/science/article/abs/pii/S0169207017300559>

```python
def dm_test_hln(e1, e2, h=1, power=2):
    """Harvey-Leybourne-Newbold-corrected Diebold-Mariano. Negative favours forecast 1."""
    from scipy import stats
    e1, e2 = np.asarray(e1, dtype=float), np.asarray(e2, dtype=float)
    d = np.abs(e1) ** power - np.abs(e2) ** power
    n = d.size
    dbar = d.mean()
    dc = d - dbar
    gamma0 = (dc @ dc) / n
    gamma = [(dc[k:] @ dc[:-k]) / n for k in range(1, h)]
    v = (gamma0 + 2 * sum(gamma)) / n
    if v <= 0:
        return {"stat": np.nan, "pvalue": np.nan, "note": "negative variance estimate"}
    stat = dbar / np.sqrt(v)
    corr = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    stat *= corr
    return {"stat": float(stat),
            "pvalue": float(2 * stats.t.sf(abs(stat), df=n - 1)),
            "n": int(n), "effective_n": int(max(1, n // max(h, 1)))}
```

**Report the power you actually have.** State: "with `K` effective folds, this backtest can detect a
standardized loss difference of `d ≥ sqrt(7.84/K)` at 80% power; observed `d` was X." That sentence
is the difference between an honest evaluation and a misleading one.

### Pooling across peer companies

The only real way to buy effective sample size. Three mechanisms, in increasing sophistication:

**(1) Pooled scoring.** Fit and evaluate the *same method* across `N` peer companies and pool the
scores. `N = 40` companies × `K = 20` folds gives 800 scored forecasts. Use scale-free metrics
(MASE, RMSSE, SPL) so pooling is meaningful, and cluster standard errors by company — the folds
within a company are not independent, and ignoring that will make you overconfident about method
rankings.

**(2) Hierarchical shrinkage of parameters.** Estimate company-specific parameters with a population
prior (Section B.8). Failing to pool "severely deteriorates the results for both estimation and
forecasting."

**(3) Pooled calibration.** The highest-value application for a probabilistic skill: pool *PIT
values* and *conformal calibration residuals* across the peer panel. Calibration structure —
"models of this type are 1.4× too narrow at `h=4`" — is far more transferable across similar
companies than point-forecast parameters are. This is what makes conformal prediction viable at
`T = 30`: borrow the calibration set from peers even when you cannot borrow the model.

**Cohort construction rules.** Pool within cohorts, not across the universe: similar growth band
(e.g. `<15%`, `15–30%`, `>30%` YoY), similar coverage ratio `κ` (contracted share drives the whole
error structure — this is the most important axis), similar ACV band and go-to-market motion, and
overlapping time period so macro conditions are shared. Then verify pooling helped: run the backtest
with and without shrinkage and compare pooled CRPS. **If shrinkage does not improve out-of-sample
score, do not use it** — you are in the "tyranny of the majority" regime.

## C.5 Track-record accounting

### The forecast log

An append-only, immutable record. One row per `(as_of_date, target_period, model, quantile_set)`.
Nothing may be edited after `as_of_date`; corrections are new rows with a `supersedes` pointer.

```python
FORECAST_LOG_SCHEMA = {
    # --- identity ---
    "forecast_id":        "uuid",
    "as_of_date":         "date",       # when the forecast was MADE (immutable)
    "entity":             "str",        # company / segment / product
    "target_period":      "str",        # e.g. "2026Q4"
    "horizon_quarters":   "int",        # derived: target_period - as_of quarter
    "target_metric":      "str",        # total_revenue | subscription_revenue | net_new_arr | ...

    # --- the forecast ---
    "model_id":           "str",
    "model_version":      "str",        # git sha of the producing code
    "point_forecast":     "float",      # state which functional: mean or median
    "point_functional":   "str",        # "mean" | "median"
    "q005": "float", "q025": "float", "q165": "float", "q250": "float",
    "q500": "float", "q750": "float", "q835": "float", "q975": "float", "q995": "float",
    "n_sims":             "int",
    "samples_uri":        "str",        # pointer to the full draw array

    # --- predictability context (Part A) ---
    "contracted_component":   "float",  # C_{t+h}
    "coverage_ratio_kappa":   "float",  # C / point_forecast
    "implied_cv_floor":       "float",  # (1 - kappa) * cv_uncontracted
    "spectral_entropy":       "float",
    "perm_entropy_norm":      "float",
    "adi": "float", "cv2": "float", "adi_cv2_class": "str",
    "bookings_hhi":           "float",

    # --- inputs, as-of (for leakage audit) ---
    "pipeline_snapshot_id":   "str",
    "consensus_at_as_of":     "float",
    "guidance_at_as_of":      "float",
    "input_data_vintage":     "date",   # knowledge-time of the newest input fact

    # --- provenance ---
    "judgmental_override":    "bool",
    "override_rationale":     "str",
    "scenario_weights":       "json",
    "supersedes":             "uuid|null",

    # --- resolution (written ONCE, after the period closes) ---
    "actual_first_reported":  "float",  # <- score against THIS
    "actual_latest_restated": "float",  # for reference only
    "actual_report_date":     "date",
    "crps":               "float",
    "pinball_mean":       "float",
    "interval_score_95":  "float",
    "pit":                "float",
    "abs_pct_error":      "float",
    "signed_error":       "float",
    "mase_contrib":       "float",
    "covered_50": "bool", "covered_80": "bool", "covered_95": "bool",
}
```

Two details that make this log trustworthy rather than decorative: **`actual_first_reported` is the
scoring target** (scoring against a restated figure rewards you for information you did not have),
and **the predictability context is recorded at forecast time** so that you can later ask "was my
error large *given* `κ` at the time?" — which is the only version of that question with an answer.

### The scorecard

Aggregate the log. Report on a grid of `horizon × entity-cohort`, always with a benchmark column and
always with the fold count:

```
Entity: ACME  |  Model: mc_ensemble_v3  |  Folds: 22  |  Window: expanding

 h  n   MASE  MASE(T3)  skill   CRPS   CRPSS(T3)  cov50  cov80  cov95   E[PIT]  Var[PIT]  bias%
 1  22  0.61    1.00    +0.39   $12.1M   +0.31     0.50   0.82   0.95    0.49    0.081    -0.4%
 2  21  0.74    1.00    +0.26   $19.8M   +0.22     0.48   0.76   0.90    0.52    0.089    -1.1%
 4  19  0.89    1.00    +0.11   $34.2M   +0.09     0.42   0.68   0.84    0.56    0.101    -2.8%
 8  15  1.04    1.00    -0.04   $61.7M   -0.02     0.33   0.60   0.80    0.61    0.118    -6.2%

Detectable effect size at 80% power: d >= sqrt(7.84/n_effective)
  h=1: n_eff=22 -> d>=0.60      h=4: n_eff=5 -> d>=1.25      h=8: n_eff=2 -> d>=1.98
```

Read that example the way you should read a real one: the model adds genuine value at `h=1–2`, is
marginal at `h=4`, and at `h=8` it does not beat constant-YoY growth while being progressively
overconfident (`Var[PIT]` rising above `1/12`) and increasingly optimistic (bias growing negative,
i.e. forecast above actual). The honest conclusion is to ship `h=1–4` and fall back to the baseline
plus a wide interval beyond that. Note also that at `h=8` the detectable effect size is 1.98 — so
"the model is worse" is itself not statistically established, only "not established as better."

### Converting past errors into forward-looking intervals

The most robust and least assumption-laden route to calibrated intervals, and it works at small `K`.
Take the horizon-conditional empirical quantiles of *relative* error:

```
For each horizon h, collect   r_{t,h} = ( ŷ_{t,h} − y_{t,h} ) / y_{t,h}   over all folds

Then:      L_h(τ) = empirical τ-quantile of { r_{·,h} }

Interval:  [  ŷ_h / ( 1 + L_h(1 − α/2) )  ,   ŷ_h / ( 1 + L_h(α/2) )  ]
```

Note the division and the **swapped** quantile indices: a large positive `r` (over-forecast)
implies the *actual* was low, so the upper error quantile maps to the *lower* revenue bound. Getting
this backwards inverts the interval, which is a common and silent bug.

```python
def empirical_error_intervals(backtest_rows, horizon, alpha=0.20, min_n=8):
    """Horizon-conditional relative-error quantiles -> multiplicative interval factors."""
    r = np.array([(row["point"] - row["actual"]) / row["actual"]
                  for row in backtest_rows if row["h"] == horizon], dtype=float)
    if r.size < min_n:
        return None            # be explicit rather than reporting a 3-point quantile
    lo_err, hi_err = np.quantile(r, [alpha / 2, 1 - alpha / 2])
    return {
        "n": int(r.size),
        "median_bias": float(np.median(r)),
        "lower_factor": 1.0 / (1.0 + hi_err),   # large over-forecast -> low actual
        "upper_factor": 1.0 / (1.0 + lo_err),
    }
```

**Verified** on the 40-quarter synthetic series with a deliberately misspecified drift model — the
diagnostic correctly surfaced a growing systematic bias with horizon:

```
  h=1  n=24  p10=-0.0653  p50=-0.0148  p90=+0.0334
  h=2  n=23  p10=-0.0943  p50=-0.0246  p90=+0.0260
  h=4  n=21  p10=-0.0843  p50=-0.0637  p90=-0.0314
  h=8  n=17  p10=-0.1443  p50=-0.1267  p90=-0.1016
```

By `h=8` the entire 10th–90th interval is negative: the model under-forecasts *every time*
(a linear drift model on an exponentially growing series). **A one-sided error distribution at long
horizons is the signature of model misspecification, not of noise** — fix the model rather than
widening the interval.

Three constraints on this technique. It requires `min_n ≈ 8` per horizon to be meaningful; it
assumes the error distribution is stationary across the backtest window, which fails across a
regime break; and it cannot see tails — with 20 folds you have no information beyond roughly the
5th and 95th percentiles, so state the 99th percentile parametrically (or not at all) rather than
pretending to read it off 20 numbers.

---

# Part D — Judgmental forecasts and debiasing

## D.1 Documented biases in pipeline and management forecasts

### The empirical evidence on judgmental adjustment

Fildes, Goodwin, Lawrence & Nikolopoulos collected **more than 60,000 forecasts and outcomes from
four supply-chain companies** — the largest field study of judgmental adjustment. Findings, in their
own framing:

- Judgmental adjustment is pervasive: **up to 80% of forecasts adjusted** in some companies.
- In three of the four companies, adjustments increased accuracy *on average*.
- **Larger adjustments tended to improve accuracy; smaller adjustments often damaged it.**
- **Positive (upward) adjustments were much less likely to improve accuracy than negative ones**,
  and were more frequently made in the wrong direction — "suggesting a general bias towards
  optimism."

- Fildes, Goodwin, Lawrence & Nikolopoulos, *IJF* 25(1):3–23 (2009) —
  <https://www.sciencedirect.com/science/article/abs/pii/S0169207008001362>
- Goodwin & Fildes, "Forecasting in supply chain companies: Should you trust your judgment?" —
  <https://doi.org/10.1057/ori.2011.5>
- Replication under promotions, same optimism finding —
  <https://doi.org/10.1016/j.ijforecast.2012.10.002>
- Follow-on experimental work on the mechanism (asymmetric attention to favourable information) —
  <https://forecasters.org/wp-content/uploads/SAS-IIF-paper_PGoodwin-RFildes.pdf>

**Operational rule that follows directly: filter out small upward adjustments.** They are the
category with the worst empirical track record. fpp3's summary: "adjustments seem to be most
accurate when they are large. Small adjustments (especially in the positive direction promoting the
illusion of optimism) have been found to hinder accuracy, and should be avoided."

### The catalogue

| Bias | Mechanism | Signature in the data | Countermeasure |
|---|---|---|---|
| **Optimism / wishful thinking** | "It would be highly unlikely that a team working towards launching a new product would forecast its failure" | Positive mean error (forecast > actual); positive adjustments wrong more often | Fit and apply a bias correction (D.3); require negative-scenario documentation |
| **Sandbagging** | Rep compensated against a target they also forecast; low forecast → easy beat | Consistent under-forecasting by specific reps; late-quarter "surprise" upside | **Segregate forecasters from targets** — the core structural fix |
| **Anchoring** | Forecast anchored on last quarter, on the target, or on the first number in the room | Forecasts cluster near round numbers or near the prior period | Independent estimates *before* the group meeting; blind Delphi round |
| **Hockey stick** | Long-horizon forecasts assume back-loaded acceleration | Systematic negative bias increasing with `h`; long-run growth forecasts exceed short-run | Report bias by horizon (C.5); impose damped growth (baseline tier 4) |
| **Stage inflation** | Deals advanced without meeting exit criteria | Stage-level realization rates fall below nominal probabilities | Fitted stage rates (D.2); evidence-gated stage advancement |
| **Groupthink / escalation** | Enthusiasm compounds in a meeting; committed forecasts defended | Forecast revisions are one-directional through the quarter | Independent estimates first, then aggregate |
| **Recency** | Last quarter's outcome over-weighted | Forecast changes correlate with the previous period's error | Explicit base rates first (D.5) |

fpp3's structural framing of the root cause is worth stating precisely: *"Judgment can be clouded by
personal or political agendas, where targets and forecasts are not segregated."* The
countermeasure is organizational, not statistical — but the *detection* is statistical, and that is
what a forecasting skill can contribute.

- fpp3 Ch. 6 (judgmental forecasting) — <https://otexts.com/fpppy/06-judgmental.html>
- Fildes & Goodwin, "Against your better judgment? How organizations can improve their use of
  management judgment in forecasting," *Interfaces* 37(6):570–576 (2007)

## D.2 Fitted stage realization rates, not nominal probabilities

CRM default stage probabilities — 20/40/60/80 — are round numbers chosen for their roundness. Replace
them with rates estimated from your own closed-deal history.

### The correct estimator

```
                          # deals that ENTERED stage s and eventually closed-won
p̂(s)  =  ──────────────────────────────────────────────────────────────────────
                          # deals that ENTERED stage s (excluding still-open)
```

**Four estimation details, each of which changes the answer materially.**

1. **Denominator must be entries, not current occupancy.** Count deals that *ever entered* the
   stage, not deals sitting in it today.
2. **Use pipeline win rate, not win rate.** `closed_won / (all pipeline that entered)`, not
   `closed_won / (closed_won + closed_lost)`. The latter excludes deals that slipped to a later
   period and therefore **over-estimates the rate by exactly the slippage fraction** — a large error
   in enterprise, where slippage is the dominant failure mode, not loss.
3. **Rolling 12-month window.** Long enough for sample size, short enough to reflect current
   pricing, ICP, and macro conditions. Exclude still-open deals to avoid right-censoring bias.
4. **Segment before you estimate.** Enterprise, mid-market, and SMB have structurally different
   conversion curves. A blended rate hides the bottleneck.

- <https://crmcurator.com/articles/hubspot/hubspot-deal-stage-probability-calibration/>
- <https://www.kluster.com/blog/sales-forecasting-method-pipeline-stage> (the pipeline-win-rate point)
- <https://resources.rework.com/libraries/pipeline-management/weighted-pipeline>
- <https://resources.rework.com/libraries/pipeline-management/stage-based-forecasting>

### Reported cumulative rates (calibrate against your own, do not adopt)

Published practitioner benchmarks cluster in these ranges for cumulative win rate given stage entry:

```
Discovery reached      ~12%          Qualification to close    15-25%
Qualification reached  ~28%          Demo/Discovery to close   20-30%
Proposal reached       ~45%          Proposal to close         50-70%
Negotiation reached    ~68%          Negotiation to close      75-85%
Verbal commit reached  ~87%
```

Sources: <https://resources.rework.com/libraries/pipeline-management/weighted-pipeline>,
<https://resources.rework.com/libraries/pipeline-management/stage-based-forecasting>,
<https://pulserevops.com/knowledge/q12382>

**These are vendor-published practitioner figures, not peer-reviewed research.** Treat them as
plausibility bounds for your own fitted rates — if your fitted "Negotiation" rate is 30%, you likely
have a stage-definition problem rather than a uniquely bad sales team — but never substitute them
for fitted rates. The observed calibration gaps in the same sources are instructive: a nominal 60%
Proposal stage converting at 52.5%, a nominal 20% Discovery converting at 9% (a **2× overstatement**
of weighted pipeline).

### Beyond stage: a fitted win-probability model

Stage is one feature. With a deal-level history of a few thousand opportunities, fit a calibrated
classifier and use its output as the Bernoulli `p` in the Monte Carlo:

```
p̂ = P( won in target quarter | stage, age_in_stage, ACV_band, segment, source,
                               competitor, discount_requested, exec_sponsor,
                               n_stakeholders, days_to_stated_close, rep_tenure, quarter_of_year )
```

Then **calibrate it** — a classifier's raw score is not a probability. Fit isotonic regression or
Platt scaling on held-out deals, and validate with a reliability diagram and Brier score
decomposition (Section C.3). An uncalibrated classifier plugged into a Monte Carlo produces
confidently wrong revenue distributions.

Additional signals worth including, from the practitioner literature: **stage velocity** (won deals
that close quickly spend less time in early stages; deals lingering in Proposal beyond ~45 days
should have their probability reduced) and **stage-skipping** (a deal that jumped Discovery →
Proposal skipped two qualification gates; historical data treats it as having entered every stage
while live data reflects the skip, so count only sequential progressions when estimating rates).

### Calibrating rep-submitted commit / upside categories

Sales organizations produce categorical judgments — Commit, Most Likely, Upside, Pipeline. Treat
each as a probability forecast and score it:

```
For each category c and each rep (or team), over a rolling 8-quarter window:

    realization_rate(c)  =  Σ closed-won amount in c  /  Σ amount categorized c
    Brier(c)             =  mean( ( p̂(c) − outcome )² )   at the deal level
    bias(c)              =  realization_rate(c) − nominal_probability(c)
```

Then **use the fitted `realization_rate` in the forecast and show reps their own Brier score and
reliability diagram.** This is the sales-forecasting instantiation of the tournament feedback loop
in Section D.5, and it is the mechanism by which optimism bias actually shrinks — not by exhortation,
but by making each individual's calibration visible and scored. Expect meaningful heterogeneity: some
reps are well-calibrated, some are systematically optimistic, and a few sandbag. Per-rep correction
factors are more accurate than a single organization-wide haircut, though they need enough deals per
rep (roughly 30+) to be estimable.

## D.3 Mechanical debiasing

Fildes et al. explicitly "developed models to eradicate such biases." The basic form is a
Theil-style regression of actuals on forecasts, estimated on history and applied going forward:

```
y_t  =  a  +  b · f_t  +  ε_t

Debiased forecast:   f'_t  =  â  +  b̂ · f_t
```

`â ≠ 0` reveals a level bias; `b̂ < 1` reveals over-extrapolation (the forecast moves more than the
actual). Extensions worth fitting when data allows: separate coefficients by adjustment sign (the
Fildes finding is that positive and negative adjustments behave differently), and interaction with
adjustment magnitude (small adjustments are the harmful ones).

```
y_t = a + b·f_t + c·1{adj_t > 0}·adj_t + d·1{adj_t < 0}·adj_t + ε_t
```

**Guardrails.** With `K = 20` folds you are estimating 2–4 parameters from 20 points — shrink
towards `(a, b) = (0, 1)` rather than using the raw OLS fit, and validate on held-out folds. If the
debiasing regression does not improve out-of-sample CRPS, do not apply it.

Note that a bias correction changes the *location* of the distribution and therefore the PIT mean;
re-run the calibration diagnostics after applying it, in the order specified in Section C.3
(bias first, then dispersion).

## D.4 Forecast combination

### The forecast combination puzzle

The empirical regularity: **simple averages of forecasts repeatedly outperform sophisticated
weighted combinations.** Smith & Wallis provide the formal explanation — the effect of finite-sample
error in estimating the combining weights. Their conclusions:

> "a simple average of competing forecasts is expected to be more accurate, in terms of MSFE, than a
> combination based on estimated weights."

and the Monte Carlo evidence together with a large-sample approximation to the variance of the
combining weight "supports the popular recommendation to **ignore forecast error covariances in
estimating the weight**."

The mechanism, from the theoretical follow-up: estimating weights adds `var(w)·var(y₁−y₂)` to the
variance of the combination, shifting the whole variance curve upward, so that the equal-weights
point can have *lower* variance than the optimum-with-estimated-weights point.

- Smith & Wallis, *Oxford Bulletin of Economics and Statistics* 71(3):331–355 (2009) —
  <https://doi.org/10.1111/j.1468-0084.2008.00541.x>,
  <https://wrap-test.warwick.ac.uk/id/eprint/28157/>
- Claeskens, Magnus, Vasnev & Wang, "The forecast combination puzzle: A simple theoretical
  explanation," *IJF* — <https://janmagnus.nl/papers/JRM113a.pdf>,
  <https://www.sciencedirect.com/science/article/abs/pii/S0169207016000327>

**Smith & Wallis also caution against over-selling it:** in the Stock–Watson example they reappraise,
"the forecast combination puzzle rests on a gain in MSFE that has no practical significance." The
lesson is not that equal weights are magic; it is that **the expected gain from estimating weights
is smaller than the estimation noise it introduces, so the simple thing is the safe default.**

### How much improvement to expect

From M4, the most authoritative benchmark:

- **12 of the 17 most accurate methods were combinations** of mostly statistical approaches.
- The winning hybrid beat the combination benchmark by **~9.4% sMAPE**; the top 16 methods averaged
  **4.49%** better than that benchmark.
- For context, in M3 the best method beat the same combination benchmark by only 4%.
- **All six pure-ML entries failed to beat the combination benchmark**, and only one beat Naive2.

M5 shifted the picture toward ML — the great majority of the top 50 in both tracks used LightGBM,
deep networks, or combinations — but the top three performers "each employed ensembles, or
combinations, of separately-trained and tuned models." **Combination survived both competitions as
the robust finding.** M5 also found the ML advantage *diminished* at lower hierarchical levels and
**at the tails of the uncertainty distributions**, which is directly relevant: for a lumpy,
low-count enterprise series, you are permanently in the regime where the ML edge is smallest.

- <https://www.sciencedirect.com/science/article/pii/S0169207019301128>
- <https://doi.org/10.1016/j.ijforecast.2022.04.006> (M5 conclusions)
- <https://en.wikipedia.org/wiki/Makridakis_Competitions>
- <https://knowledge.insead.edu/operations/decision-makers-should-rely-hybrid-forecasting-models>

**Calibrated expectation for enterprise revenue: single-digit percentage improvement in point
accuracy from combination, and a larger, more reliable improvement in calibration.** The interval
result from M4 supports the second half: aggregating intervals improved both calibration and
accuracy, with median and interior-trimmed averages the robust aggregators
(<https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3329413>).

### Practical weighting scheme

```
1. Equal weights                      — the default; hard to beat
2. Trimmed mean                       — drop the top and bottom 1 of K; robust to one broken model
3. Median                             — maximally robust; the M4 interval work found it robust
4. Inverse-MSE weights                w_k ∝ 1 / MSE_k
5. Shrunk optimal weights             w = λ·w_optimal + (1−λ)·(1/K),  λ ≈ 0.3-0.5
6. Full optimal with covariances      — do NOT do this at small K
```

**Do not skip step 2/3.** With `K = 3–5` models, a single broken component destroys an equal-weighted
mean. Trimming or the median is nearly free insurance.

For *probabilistic* combination, remember Section B.10: form the **linear pool** of distributions
(concatenate samples in proportion to weights), not an average of quantiles. A linear pool of
disagreeing models is automatically wider than its components, which is the correct representation
of model uncertainty and is often the single largest calibration improvement available.

## D.5 Calibration practices from forecasting tournaments

The Good Judgment Project — Tetlock, Mellers & Moore, in the IARPA ACE tournament — is the best
available evidence on improving human probability judgment. Forecasts were scored with Brier scores;
top forecasters were "reportedly 30% better than intelligence officers with access to actual
classified information."

- Mellers et al., "Identifying and Cultivating Superforecasters as a Method of Improving
  Probabilistic Predictions," *Perspectives on Psychological Science* 10(3) (2015) —
  <https://journals.sagepub.com/doi/10.1177/1745691615577794>,
  <https://web.stanford.edu/~knutson/jdm/mellers15.pdf>
- <https://en.wikipedia.org/wiki/The_Good_Judgment_Project>
- <https://goodjudgment.com/>

### The practices, with the evidence

**1. Explicit base rates first.** Start from the outside view — the reference-class frequency — then
adjust for case specifics. For revenue: *before* looking at the pipeline, ask "what fraction of
quarters in the last 3 years did we beat our own internal forecast at this point in the quarter?"
Anchor on that, then adjust.

**2. Granular probability estimates.** The most concrete measured behavioral difference. Mellers et
al. found superforecasters used **57 unique probability values** on average versus 29–30 for
top-team individuals and everyone else — nearly twice as many. Others clustered on multiples of 10%;
superforecasters were most likely to use values divisible by 1% and *only* 1% (17%, 28%, 83%).
**Granularity is not false precision; it measured better.** For revenue: stop reporting
"high/medium/low confidence" and report `P(beat guidance) = 0.63`.

**3. Frequent updating.** Forecasters were "encouraged to update their beliefs as often as they
wished." Frequent belief revision in response to new information was a driver of accuracy. For
revenue: re-forecast weekly intra-quarter as the pipeline resolves, and **log every revision** — the
trajectory of revisions is itself diagnostic (monotone upward revisions through a quarter indicate
initial sandbagging; monotone downward indicate initial optimism).

**4. Brier-score feedback loops.** Scoring was continuous and visible, with status rewards tied to
accuracy. Brier decomposes into **calibration** (does average confidence match hit rate?) and
**resolution** (were you decisively right, or hedging at 40–60%?), and both were tracked.
Superforecasters showed significantly better calibration *and* higher resolution. The applied form:
give every forecaster (rep, manager, model) a scorecard with their own Brier score, calibration
curve, and resolution, updated every quarter.

**5. Team structure and aggregation.** The winning strategy was culling top performers into elite
teams. Mellers et al. attribute performance to four mutually reinforcing factors: cognitive
abilities and styles, task-specific skills, motivation and commitment, and enriched environments —
concluding superforecasters "are partly discovered and partly created." Notably, they **defied
regression toward the mean two years running**, so the effect is skill rather than luck. The
applicable pieces: identify your best-calibrated forecasters empirically and weight them more; and
have them work as a team with visible disagreement.

### Translation to a revenue forecasting protocol

| Tournament practice | Revenue implementation |
|---|---|
| Base rates first | Compute the tier-3 baseline and the coverage ratio `κ` *before* opening the pipeline |
| Granular probabilities | Report the M5 nine-quantile grid; report `P(beat guidance)` to two decimals |
| Frequent updating | Weekly intra-quarter re-forecast; every revision logged with its trigger |
| Brier feedback | Per-forecaster and per-model quarterly scorecard: Brier, calibration curve, resolution, CRPS |
| Team aggregation | Independent estimates *before* the forecast call; linear-pool them; discuss disagreement rather than converging to a single number |
| Discovered + created | Track individual calibration over ≥8 quarters; weight demonstrated calibration, and train the rest |

The through-line connecting Part D back to Parts A–C: **judgmental inputs are not the enemy — the
Fildes evidence is that large, well-motivated adjustments genuinely help. Unscored judgmental inputs
are the enemy.** Log them, resolve them, score them with a proper rule, fit their bias, and feed the
correction back. That loop is the entire methodology.

---

# Scoring cheat sheet

## Probabilistic scores (proper — rank models on these)

| Metric | Formula | What it measures | Units | Use when | Do not use when |
|---|---|---|---|---|---|
| **CRPS** | `∫ (F(y) − 1{y≥x})² dy` = `E\|X−x\| − ½E\|X−X'\|` | Overall quality of the full predictive distribution; jointly calibration + sharpness | Same as data ($) | **The default probabilistic score.** Reduces to MAE for point forecasts, so it compares probabilistic and point models on one scale | You only have a few quantiles (use mean pinball, its discrete analogue) |
| **Pinball / quantile loss** | `ρ_τ(y−q)`, `ρ_τ(u)=u(τ−1{u<0})` | Accuracy of one specific quantile | Same as data ($) | Forecast is delivered as quantiles; asymmetric cost of over/under | You need one number summarizing the whole distribution |
| **Mean pinball over a τ grid** | `mean_τ mean_t L_τ(y_t, q_t(τ))`; `2×` ≈ CRPS | Discrete CRPS approximation | Same as data ($) | Standard quantile grid (use M5's nine levels) | Very coarse grid (≤3 quantiles) |
| **SPL / WSPL** | Pinball ÷ in-sample naive MAE, then weighted | Scale-free quantile accuracy across many series | Dimensionless | Pooling across companies/segments; M5-comparable results | Series is constant (denominator → 0) |
| **Interval / Winkler score** | `(u−l) + (2/α)(l−x)1{x<l} + (2/α)(x−u)1{x>u}` | Interval width **and** coverage in one proper number | Same as data ($) | You report intervals, not full distributions. **The correct answer to "coverage or width?"** | You need to compare across scales (use MSIS) |
| **MSIS** | Interval score ÷ in-sample mean abs. seasonal difference | Scale-free interval quality | Dimensionless | Cross-series interval comparison; M4-comparable | Single series in native units (use interval score) |
| **Log score** | `−log f(x)` | Predictive density at the outcome; the likelihood-based score | Nats | Model selection, Bayes factors, secondary diagnostic | **Primary ranking with outlier risk** — one near-zero-density outcome gives `+∞` |
| **Brier score** | `(1/n)Σ(p_i − o_i)²` | Binary probability forecast quality | Dimensionless `[0,1]` | Deal-close, churn, beat-guidance, scenario weights | Continuous outcomes |
| **Brier decomposition** | `reliability − resolution + uncertainty` | Splits miscalibration from genuine discrimination from base-rate difficulty | Dimensionless | Diagnosing *why* a probability forecast is bad; forecaster feedback | You just need a single ranking |

## Skill scores (report these, not raw errors)

| Metric | Formula | Notes |
|---|---|---|
| **CRPSS** | `1 − CRPS_model / CRPS_ref` | The headline probabilistic number. Reference = climatological growth-rate distribution |
| **MASE** | `mean\|e\| ÷ in-sample seasonal-naive MAE` | `<1` beats naive. **The default point metric.** Its DM statistic approximates the reference distribution — MAPE's and sMAPE's do not |
| **RMSSE** | `sqrt( mean(e²) ÷ in-sample seasonal-naive MSE )` | MASE's squared-loss sibling; M5 point track |
| **Relative MAE** | `MAE_model / MAE_benchmark` | Simple, transparent, needs a named benchmark |
| **Theil's U2** | `sqrt(Σ(ŷ−y)²) / sqrt(Σ(y_naive−y)²)` | RMSE ratio vs naive; `<1` is skill |
| **Generic skill score** | `1 − S_model / S_benchmark` | Works with *any* proper score |

## Point-error metrics

| Metric | Formula | Minimized by | Use when | Do not use when |
|---|---|---|---|---|
| **MAE** | `mean\|y−ŷ\|` | Conditional **median** | Same scale, one company, dollars wanted | Cross-series comparison |
| **RMSE** | `sqrt(mean((y−ŷ)²))` | Conditional **mean** | Targeting the mean; big misses cost disproportionately | Heavy-tailed errors; one restatement dominates |
| **MdAE** | `median\|y−ŷ\|` | — | Short backtest with a known outlier quarter | You need a differentiable objective |
| **WAPE** | `Σ\|y−ŷ\| / Σ\|y\|` | — | Aggregating segments of very different sizes | Small segments matter individually |
| **MAPE** | `100·mean(\|y−ŷ\|/\|y\|)` | — | Only: all values strictly positive and far from 0, audience insists | Zeros/negatives/near-zeros; **never as an objective** (asymmetric → biases forecasts down) |
| **sMAPE** | `200·mean(\|y−ŷ\|/(\|y\|+\|ŷ\|))` | — | Reproducing M4-comparable numbers only | Everything else — fpp3 recommends it "not be used" |
| **ME / MPE** | `mean(y−ŷ)` / `100·mean((y−ŷ)/y)` | — | **Always, alongside any other metric** | Never omit — it is the only bias detector here |

## Calibration diagnostics (not scores — checks)

| Diagnostic | Target | Interpretation of departures |
|---|---|---|
| **PIT histogram** | Flat / uniform | **∪** = too narrow (overconfident); **∩** = too wide; **triangular/sloped** = biased |
| **E[PIT]** | `0.5` | Any departure = bias. **Check and fix this before dispersion** |
| **Var[PIT]** | `1/12 ≈ 0.0833` | `>1/12` under-dispersed; `<1/12` over-dispersed. Contaminated by bias — de-bias first |
| **KS / χ² on PIT** | `p > 0.05` | Formal uniformity test. Prefer to eyeballing the shape at small `K` |
| **Interval coverage** | Nominal `1−α` | **Meaningless without width.** SE at `K=24`, nominal 90%, is ~6.1pp |
| **Coverage difference** | `≈ 0` | M4's reported companion to MSIS |
| **Reliability diagram** | 45° line | Below the line = overconfident. For binary sub-forecasts |
| **ECE** | `0` | `Σ_b (n_b/n)·\|ō_b − p̄_b\|` |
| **Sharpness diagram** | Narrow, subject to calibration | Only compare sharpness *among calibrated* forecasts |

## Predictability diagnostics (compute before modeling)

| Diagnostic | Range | Interpretation |
|---|---|---|
| **Coverage ratio `κ`** | `[0,1]` | Contracted ÷ forecast revenue. **The single most useful predictability statistic for enterprise software** |
| **Implied CV floor** | `≥0` | `(1−κ)·CV_U`. Your interval cannot honestly be tighter than this |
| **Spectral entropy** | `[0,1]` | `→0` highly forecastable; `→1` white noise. Compute on the detrended/deseasonalized series |
| **Normalized permutation entropy** | `[0,1]` | Model-free intrinsic predictability. Use `m=3` at quarterly frequency |
| **ADI** | `≥1` | `T/N`. `>1.32` = intermittent side of the quadrant |
| **CV²** | `≥0` | Squared CV of nonzero sizes. `>0.49` = erratic side. Also report `CV²(log z)` |
| **Bookings HHI** | `(0,1]` | `Σ(z_i/Σz)²`. `>0.2` → the quarter is a few binary events → use Monte Carlo / scenario tree, not a time-series model |
| **Mean ÷ median deal size** | `≥1` | `exp(σ²/2)` for lognormal. Compact heavy-tail diagnostic; explains "forecast below pipeline" |
| **Hurst exponent** | `(0,1)` | `≈0.5` random walk. **Do not report from 30 quarterly points** — R/S overestimates in small samples |

## Statistical tests

| Test | Use | Caveat |
|---|---|---|
| **Diebold–Mariano** | Is the accuracy difference between two forecasts significant? | Asymptotic; **over-rejects in small samples and multi-step** |
| **HLN-corrected DM** | Same, small samples | Multiply DM by `sqrt((n+1−2h+h(h−1)/n)/n)`, refer to `t_{n−1}`. **Use this, not raw DM** |
| **Power check** | How large a difference *can* you detect? | `n ≈ 7.84/d²` for 80% power at `α=0.05`. Effective `n ≈ K/h` with overlapping horizons. **Report this next to every comparison** |

---

# Appendix — verification notes

Every numerical claim in this document was verified by direct computation (Python 3, NumPy 2.4.4,
SciPy 1.18.0). Verified results:

| Claim | Section | Verified result |
|---|---|---|
| Sample CRPS = Gaussian closed-form CRPS | C.1 | `N(100,12²)`, `x=108`: 4.8565 (400k samples) vs 4.8566 (closed form) |
| `CRPS = 2∫₀¹ pinball dτ` | C.1 | `2 × mean(pinball, 2000 τ)` = 4.859 vs CRPS 4.857 |
| Iman–Conover induces target rank correlation, preserves marginals | B.5 | Target 0.60/0.30/0.50 → achieved 0.584/0.284/0.482; marginals identical (exact permutation) |
| Correlation inflates the aggregate tail | B.5 | 5 lognormal segments, `ρ=0.6`: SD 85.9→157.0 (1.83×), q99 764→1000 (+31%) |
| Split conformal attains nominal coverage marginally | B.7 | `m=200`, `α=0.10`: mean coverage 0.9056 over 2,000 calibration draws (single-draw realization 0.8954) |
| PIT `Var` diagnoses dispersion | C.3 | `σ=3/5/9` vs truth `σ=5`: `Var[PIT]` = 0.1318 / 0.0833 / 0.0378 (target 0.0833) |
| Bias masquerades as over-dispersion in `Var[PIT]` | C.3 | `N(−9,10²)` errors scored vs `N(0,10²)`: `Var[PIT]`=0.0619, `E[PIT]`=0.267; after de-biasing 0.0849 / 0.500 |
| Variance inflation `λ` restores calibration | C.3 | `σ=6` (true 10): `λ=1.666` → `Var[PIT]` 0.1312→0.0833. `σ=18`: `λ=0.555` → 0.0379→0.0833 |
| `Σ q_τ ≠ q_τ(Σ)` | B.12 | 5 lognormal segments: `Σ q₀.₉₀`=782.37 vs `q₀.₉₀(Σ)`=643.91 → **21.5% overstatement** |
| `CV_R = (1−c)·CV_U` and `E\|err\|% = 0.798·CV_R` | A.7 | `CV_U=0.30`: `c`=0/0.5/0.75/0.9/0.95 → `CV_R`=30.0/15.0/7.5/3.0/1.5%, expected `\|err\|`=23.9/12.0/6.0/2.4/1.2% |
| Rolling-origin loop and skill scores | C.4 | 40 quarters, `min_train=16`, `H=8`: 24 folds, 164 pairs; MASE 3.155 (snaive) vs 1.140 (drift), skill +0.639 |
| Horizon-conditional error quantiles detect misspecification | C.5 | Drift model on exponential series: `h=8` p10/p50/p90 = −0.144/−0.127/−0.102, all negative |
| ADI/CV² classification | A.6 | 16-period lumpy bookings: ADI=3.20, CV²=0.88 → "lumpy" |

Caveats on the verifications: the Iman–Conover attenuation (achieved rank correlation a few points
below target) is a genuine property of the method, not a bug in the implementation. The split
conformal single-draw coverage of 0.8954 below nominal 0.90 is expected — the guarantee is marginal
over the calibration draw, and the 2,000-draw average of 0.9056 confirms it holds.

---

# Sources

## Proper scoring rules and calibration

- Gneiting & Raftery, "Strictly Proper Scoring Rules, Prediction, and Estimation," *JASA*
  102(477):359–378 (2007) — <https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf>
- Gneiting, Balabdaoui & Raftery, "Probabilistic forecasts, calibration and sharpness," *JRSS-B*
  69(2):243–268 (2007) — <https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jrssb.pdf>
  · <https://doi.org/10.1111/j.1467-9868.2007.00587.x>
- "Proper Scoring Rules for Estimation and Forecast Evaluation," *Annual Review of Statistics* —
  <https://www.annualreviews.org/content/journals/10.1146/annurev-statistics-042424-050626>
  · preprint <https://arxiv.org/html/2504.01781v1>
- Jordan, Krüger & Lerch, "Evaluating Probabilistic Forecasts with scoringRules," *JSS* 90(12) —
  <https://doi.org/10.18637/jss.v090.i12>
- Kuleshov, Fenner & Ermon, "Accurate Uncertainties for Deep Learning Using Calibrated Regression,"
  ICML 2018 — <https://proceedings.mlr.press/v80/kuleshov18a/kuleshov18a.pdf> · <https://arxiv.org/pdf/1807.00263>
- PIT histogram shape and `E`/`Var` diagnostics —
  <https://rdrr.io/github/jobstdavid/eppverification/man/pit.hist.html>
- Miscalibration as KL divergence from uniform — <https://www.stat.cmu.edu/~ryantibs/papers/recalib.pdf>

## Accuracy measures and benchmarking

- Hyndman & Koehler, "Another look at measures of forecast accuracy," *IJF* 22(4):679–688 (2006) —
  <https://robjhyndman.com/papers/mase.pdf> · <https://doi.org/10.1016/j.ijforecast.2006.03.001>
- Hyndman & Athanasopoulos, *Forecasting: Principles and Practice*, 3rd ed.
  §5.5 prediction intervals & bootstrap — <https://otexts.com/fpp3/prediction-intervals.html>
  · §5.8 accuracy — <https://otexts.com/fpp3/accuracy.html>
  · §5.10 time series cross-validation — <https://otexts.com/fpp3/tscv.html>
  · §11.5 reconciled distributional forecasts — <https://otexts.com/fpp3/rec-prob.html>
  · Python edition — <https://otexts.com/fpppy/05-toolbox.html>, <https://otexts.com/fpppy/06-judgmental.html>
- Hyndman, "Time series cross-validation using fable" — <https://robjhyndman.com/hyndsight/tscv-fable/>
- MASE properties incl. DM-distribution behavior — <https://en.wikipedia.org/wiki/Mean_absolute_scaled_error>
- Diebold & Mariano, "Comparing predictive accuracy," *JBES* 13:253–263 (1995) —
  <https://www.sas.upenn.edu/~fdiebold/papers/paper68/pa.dm.pdf>
- Harvey, Leybourne & Newbold (1997) finite-sample correction, implemented in `dm.test` —
  <https://pkg.robjhyndman.com/forecast/reference/dm.test.html>
- Small-sample forecast-evaluation tests and negative variance estimates —
  <https://www.sciencedirect.com/science/article/abs/pii/S0169207017300559>

## M-competitions

- Makridakis, Spiliotis & Assimakopoulos, "The M4 Competition: 100,000 time series and 61
  forecasting methods," *IJF* 36(1):54–74 — <https://www.sciencedirect.com/science/article/pii/S0169207019301128>
- M4 findings — <https://ideas.repec.org/a/eee/intfor/v34y2018i4p802-808.html>
  · <https://purehost.bath.ac.uk/ws/portalfiles/portal/192035784/IJF_2019_M4_Conclusions_post_print_.pdf>
  · <https://en.wikipedia.org/wiki/Makridakis_Competitions>
  · <https://knowledge.insead.edu/operations/decision-makers-should-rely-hybrid-forecasting-models>
- Makridakis et al., "The M5 uncertainty competition: Results, findings and conclusions," *IJF*
  38(4):1365–1385 — <https://doi.org/10.1016/j.ijforecast.2021.10.009>
  · <https://ideas.repec.org/a/eee/intfor/v38y2022i4p1365-1385.html>
- "The M5 competition: Conclusions," *IJF* — <https://doi.org/10.1016/j.ijforecast.2022.04.006>
- Ziel, "M5 competition uncertainty: Overdispersion, distributional forecasting, GAMLSS, and beyond,"
  *IJF* — <https://doi.org/10.1016/j.ijforecast.2021.09.008>
- M4 OWA and MSIS definitions — <https://doi.org/10.3390/forecast3010010>
  · <https://usermanual.wiki/Document/M4CompetitorsGuide.1491768831/html>
  · <https://mlr3forecast.mlr-org.com/reference/mlr_measures_fcst.msis.html>
- SPL/WSPL as implemented — <https://doi.org/10.1016/j.ijforecast.2022.01.001> · <https://arxiv.org/pdf/2311.00993>
- Grushka-Cockayne & Jose, "Combining Prediction Intervals in the M4 Competition" —
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3329413>
- Applicability of M5 to forecasting at Walmart —
  <https://www.sciencedirect.com/science/article/abs/pii/S0169207021001023>

## Forecastability and predictability measures

- `tsfeatures` spectral entropy — <https://pkg.robjhyndman.com/tsfeatures/reference/entropy.html>
  · vignette <https://github.com/robjhyndman/tsfeatures/blob/master/vignettes/tsfeatures.Rmd>
  · manual <https://robjhyndman.r-universe.dev/tsfeatures/doc/manual.html>
- Goerg, "Forecastable Component Analysis," ICML 2013 — <https://proceedings.mlr.press/v28/goerg13.html>
- Bandt & Pompe, "Permutation Entropy: A Natural Complexity Measure for Time Series," *PRL*
  88:174102 (2002) — <https://doi.org/10.1103/physrevlett.88.174102>
- Garland et al., "Model-free quantification of time-series predictability" —
  <https://ar5iv.labs.arxiv.org/html/1404.6823>
- Intrinsic vs realized predictability — <https://esajournals.onlinelibrary.wiley.com/doi/10.1002/ecm.1359>
- Riedl, Müller & Wessel, "Practical considerations of permutation entropy" —
  <https://people.physik.hu-berlin.de/~wessel/cvp/pubs/Riedl_epjst_2013.pdf>
- Permutation entropy variants vs ACF and mutual information —
  <https://onlinelibrary.wiley.com/doi/10.1111/anzs.12376>
- Hurst exponent and R/S — <https://en.wikipedia.org/wiki/Hurst_exponent>
  · <https://pubsonline.informs.org/do/10.1287/LYTX.2012.04.05/full/>
- Finite-sample bias of R/S vs DFA — <https://mpra.ub.uni-muenchen.de/16446/1/MPRA_paper_16446.pdf>
  · DFA artifacts <https://doi.org/10.1038/srep00315>

## Demand classification

- Syntetos, Boylan & Croston (2005); Boylan & Syntetos, "The Accuracy of Intermittent Demand
  Estimates," *IJF* — reference implementation with the 1.32 / 0.49 cutoffs:
  <https://www.sktime.net/en/v0.32.2/api_reference/auto_generated/sktime.transformations.series.adi_cv.ADICVTransformer.html>
- Empirical review of the cutoffs — <http://www.msc-les.org/proceedings/mas/2014/MAS2014_205.pdf>
- Critique (Kostenko & Hyndman curve; stability assumption) —
  <https://openforecast.org/2024/07/16/intermittent-demand-classifications-is-that-what-you-need/>
- SBA and temporal aggregation for lumpy demand — <https://metricgate.com/docs/intermittent-demand-syntetos/>

## Conformal prediction

- Romano, Patterson & Candès, "Conformalized Quantile Regression," NeurIPS 32 (2019) —
  <https://proceedings.neurips.cc/paper/2019/file/5103c3584b063c431bd1268e9b5e76fb-Paper.pdf>
  · <https://arxiv.org/pdf/1905.03222> · code <https://github.com/yromano/cqr>
- Gibbs & Candès, "Adaptive Conformal Inference Under Distribution Shift," NeurIPS 2021 —
  <https://papers.neurips.cc/paper/2021/file/0d441de75945e5acbc865406fc9a2559-Paper.pdf>
  · <https://doi.org/10.48550/arxiv.2106.00170>
- Zaffran et al., "Adaptive Conformal Predictions for Time Series," ICML 2022 —
  <https://icml.cc/media/icml-2022/Slides/17818.pdf>
- Xu & Xie, "Conformal prediction interval for dynamic time-series" (EnbPI), ICML 2021 —
  <https://proceedings.mlr.press/v139/xu21h.html>
- Conformal-control survey and lineage — <https://ojs.aaai.org/index.php/AAAI/article/view/34029/36184>

## Quantile and distributional regression

- Meinshausen, "Quantile Regression Forests," *JMLR* 7:983–999 (2006) —
  <https://jmlr.org/papers/volume7/meinshausen06a/meinshausen06a.pdf> · <https://www.jmlr.org/papers/v7/meinshausen06a.html>

## Correlation, copulas, and dependence

- Iman & Conover, "A distribution-free approach to inducing rank correlation among input variables,"
  *Comm. Statist. Simula. Computa.* 11(3):311–334 (1982) — <https://doi.org/10.1080/03610918208812265>
- Iman–Conover exposition and code — <https://blogs.sas.com/content/iml/2021/06/14/simulate-iman-conover-transformation.html>
  · geometry <https://blogs.sas.com/content/iml/2021/06/16/geometry-iman-conover-transformation.html>
  · formal algorithm <https://aggregate.readthedocs.io/en/latest/5_technical_guides/5_x_iman_conover.html>
  · cost-modeling application <https://www.iceaaonline.com/wp-content/uploads/2024/11/JCAPv10i1-CorrelatedInputVariablesMonteCarlo-Henke.pdf>
- Embrechts, McNeil & Straumann, "Correlation and dependence in risk management: properties and
  pitfalls" — <https://people.math.ethz.ch/~embrecht/ftp/pitfalls.pdf>
- Tail dependence and copula selection — <https://www.casact.org/sites/default/files/database/forum_10fforumpt2_staudt.pdf>
- Risk aggregation via copulas vs linear correlation — <https://doi.org/10.4236/jmf.2011.13007>
- Rank correlation and copula practitioner note —
  <https://ndic.gov.ng/wp-content/uploads/2024/05/Technical-Note-on-Correlation-and-Copula-Models-for-Dependence-Modelling.pdf>
- Normal-assumption risk understatement — <https://doi.org/10.12775/cjfa.2016.017>

## Hierarchical and probabilistic aggregation

- Han, Dasgupta & Ghosh, "Simultaneously Reconciled Quantile Forecasting of Hierarchically Related
  Time Series," AISTATS 2021 — <https://proceedings.mlr.press/v130/han21a/han21a.pdf>
  · **non-additivity proof** <https://proceedings.mlr.press/v130/han21a/han21a-supp.pdf>
- Ben Taieb, Taylor & Hyndman, "Coherent Probabilistic Forecasts for Hierarchical Time Series,"
  ICML 2017 — <https://proceedings.mlr.press/v70/taieb17a/taieb17a.pdf>
- Jeon, Panagiotelis & Petropoulos, "Probabilistic forecast reconciliation with applications to
  wind power and electric load" — <https://www.sciencedirect.com/science/article/abs/pii/S0377221719304242>
- Rangapuram et al., "End-to-End Learning of Coherent Probabilistic Forecasts for Hierarchical Time
  Series," ICML 2021 — <https://proceedings.mlr.press/v139/rangapuram21a/rangapuram21a.pdf>

## Bayesian hierarchical / panel forecasting

- Hierarchical Bayes meets hierarchical forecasting — <https://arxiv.org/html/2606.23009>
- Forecasting with Bayesian grouped random effects in panel data — <https://doi.org/10.2139/ssrn.3681672>
- Bayesian panel local projections with partial pooling —
  <https://www.marcoschwarzbach.de/uploads/BayesianPanelLocalProjections.pdf>
- Individual shrinkage for random effects in short panels — <https://doi.org/10.48550/arxiv.2308.01596>
- Bayesian panel VARs (`bpvars`) — <https://arxiv.org/pdf/2606.14143>

## Forecast combination

- Smith & Wallis, "A Simple Explanation of the Forecast Combination Puzzle," *Oxford Bulletin of
  Economics and Statistics* 71(3):331–355 (2009) — <https://doi.org/10.1111/j.1468-0084.2008.00541.x>
  · <https://wrap-test.warwick.ac.uk/id/eprint/28157/>
- Claeskens, Magnus, Vasnev & Wang, "The forecast combination puzzle: A simple theoretical
  explanation," *IJF* — <https://janmagnus.nl/papers/JRM113a.pdf>
  · <https://www.sciencedirect.com/science/article/abs/pii/S0169207016000327>

## Judgmental forecasting and debiasing

- Fildes, Goodwin, Lawrence & Nikolopoulos, "Effective forecasting and judgmental adjustments,"
  *IJF* 25(1):3–23 (2009) — <https://www.sciencedirect.com/science/article/abs/pii/S0169207008001362>
- Goodwin & Fildes, "Forecasting in supply chain companies: Should you trust your judgment?" —
  <https://doi.org/10.1057/ori.2011.5>
- Trapero, Pedregal, Fildes & Kourentzes, "Analysis of judgmental adjustments in the presence of
  promotions," *IJF* — <https://doi.org/10.1016/j.ijforecast.2012.10.002>
- Goodwin & Fildes, information use in judgmental forecasting (IIF/SAS) —
  <https://forecasters.org/wp-content/uploads/SAS-IIF-paper_PGoodwin-RFildes.pdf>
- Mellers et al., "Identifying and Cultivating Superforecasters," *Perspectives on Psychological
  Science* 10(3) (2015) — <https://journals.sagepub.com/doi/10.1177/1745691615577794>
  · <https://web.stanford.edu/~knutson/jdm/mellers15.pdf>
- Good Judgment Project — <https://en.wikipedia.org/wiki/The_Good_Judgment_Project> · <https://goodjudgment.com/>
- Brier calibration/resolution in practice — <https://commoncog.com/how-do-you-evaluate-your-own-predictions/>

## Enterprise software revenue structure (practitioner sources)

- RPO / cRPO definitions and disclosure practice — <https://ordwaylabs.com/blog/how-saas-companies-define-rpos/>
  · <https://www.gsquaredcfo.com/blog/rpo-in-saas-explained-quick-guide-to-remaining-performance-obligations>
  · <https://saasdb.app/learn/financials/rpo-and-backlog/> · <https://getpacerai.com/blog/what-is-current-performance-obligation/>
- RPO / deferred revenue roll-forward nowcasting —
  <https://stockalpha.ai/alpha-learning/rpo-and-deferred-revenue-rollforwards-a-nowcasting-framework-for-subscription-bu>
- Stage-probability calibration — <https://crmcurator.com/articles/hubspot/hubspot-deal-stage-probability-calibration/>
  · <https://resources.rework.com/libraries/pipeline-management/stage-based-forecasting>
  · <https://resources.rework.com/libraries/pipeline-management/weighted-pipeline>
  · <https://pulserevops.com/knowledge/q12382>
- Pipeline win rate vs win rate — <https://www.kluster.com/blog/sales-forecasting-method-pipeline-stage>

## Point-in-time data discipline

- <https://tradevodata.com/blog/lookahead-bias-fundamental-backtests>
- <https://bagelquant.com/pit-equity-database/>
- <https://arkolith.com/blog/point-in-time-data-explained>
- <https://developer.stockfit.io/blog/point-in-time-data-backtesting>
