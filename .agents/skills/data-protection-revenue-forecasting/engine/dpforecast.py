"""Probabilistic revenue forecasting engine for data-protection / storage-software vendors.

Dependency-light (numpy only; uses scipy for the normal CDF/quantile when available and
falls back to an accurate rational approximation when it is not).

The module follows the identity chain documented in SKILL.md::

    demand -> pipeline -> BOOKINGS (ACV/ARR, TCV) -> BILLINGS -> REVENUE (ASC 606) -> CASH

Sections
--------
1.  Measure-type safety            Quantity, sum_quantities, tcv_from_acv
2.  Distributions                  Point, Normal, LogNormal, Beta, Triangular, TruncNormal
3.  Baseline                       fit_ar1, ar1_paths, visibility_ratio
4.  Order flow                     Deal, simulate_deal_list, fit_rho_to_target_sd,
                                   category_forecast, pace_nowcast
5.  Calibration of inputs          platt_fit/platt_apply, isotonic_fit/isotonic_apply,
                                   shrink_binomial, shrink_normal
6.  ARR waterfall                  WaterfallSpec, simulate_arr_waterfall
7.  ASC 606                        Contract, recognize_contracts, Schedule
8.  Reconciliation                 revenue_identity_residual, rpo_rollforward_residual
9.  P&L and cash                   pnl_by_stream, fcf_bridge
10. Closed-form levers             price_lever, discount_lever, prepaid_cash_lever,
                                   operating_margin_from_growth_gap, magic_number,
                                   cac_payback_months, arr_half_life, steady_state_arr,
                                   required_pipeline_coverage
11. Scoring and calibration        crps_ensemble, crps_normal, pinball_loss, brier_score,
                                   log_score_ensemble, pit_values, interval_coverage,
                                   pit_uniformity_chisq, skill_score, quantiles,
                                   quantile_sum_error
12. Sensitivity                    rank_levers

Every simulator returns *draws*, not summaries. Aggregate draws and then take quantiles;
never sum quantiles (see ``quantile_sum_error``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

__all__ = [
    # 1
    "MEASURES", "Quantity", "sum_quantities", "tcv_from_acv", "acv_from_tcv",
    # 2
    "Dist", "Point", "Normal", "LogNormal", "Beta", "Triangular", "TruncNormal", "as_dist",
    # 3
    "fit_ar1", "ar1_paths", "visibility_ratio",
    # 4
    "Deal", "simulate_deal_list", "fit_rho_to_target_sd", "category_forecast", "pace_nowcast",
    "bvn_cdf", "indicator_correlation", "latent_rho_from_indicator", "exchangeable_sd_inflation",
    "effective_deal_count",
    # 5
    "platt_fit", "platt_apply", "isotonic_fit", "isotonic_apply",
    "shrink_binomial", "shrink_normal",
    # 6
    "WaterfallSpec", "simulate_arr_waterfall",
    # 7
    "Contract", "Schedule", "recognize_contracts",
    # 8
    "revenue_identity_residual", "rpo_rollforward_residual",
    # 9
    "pnl_by_stream", "fcf_bridge",
    # 10
    "price_lever", "discount_lever", "prepaid_cash_lever",
    "operating_margin_from_growth_gap", "magic_number", "cac_payback_months",
    "arr_half_life", "steady_state_arr", "required_pipeline_coverage",
    # 11
    "crps_ensemble", "crps_normal", "pinball_loss", "brier_score", "log_score_ensemble",
    "pit_values", "interval_coverage", "pit_uniformity_chisq", "skill_score",
    "quantiles", "quantile_sum_error",
    # 12
    "rank_levers",
]


# ---------------------------------------------------------------------------
# 0. Numerics: normal CDF / quantile without a hard scipy dependency
# ---------------------------------------------------------------------------

try:  # pragma: no cover - exercised only by whichever branch the host provides
    from scipy.special import ndtr as _ndtr_impl, ndtri as _ndtri_impl

    HAVE_SCIPY = True
except Exception:  # pragma: no cover
    HAVE_SCIPY = False

    _erf_vec = np.frompyfunc(math.erf, 1, 1)

    def _ndtr_impl(x):
        x = np.asarray(x, dtype=float)
        return np.asarray(_erf_vec(x / math.sqrt(2.0)), dtype=float) * 0.5 + 0.5

    # Acklam's inverse normal CDF: relative error < 1.15e-9 over (0, 1).
    _A = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
          1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    _B = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
          6.680131188771972e+01, -1.328068155288572e+01)
    _C = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
          -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    _D = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
          3.754408661907416e+00)

    def _ndtri_impl(p):
        p = np.asarray(p, dtype=float)
        out = np.empty_like(p)
        lo, hi = 0.02425, 1.0 - 0.02425
        left, right = p < lo, p > hi
        mid = ~(left | right)

        q = np.sqrt(-2.0 * np.log(np.where(left, p, 0.5)))
        out = np.where(
            left,
            (((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5])
            / ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0),
            out,
        )
        q = np.sqrt(-2.0 * np.log(np.where(right, 1.0 - p, 0.5)))
        out = np.where(
            right,
            -(((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5])
            / ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0),
            out,
        )
        q = np.where(mid, p, 0.5) - 0.5
        r = q * q
        out = np.where(
            mid,
            (((((_A[0] * r + _A[1]) * r + _A[2]) * r + _A[3]) * r + _A[4]) * r + _A[5]) * q
            / (((((_B[0] * r + _B[1]) * r + _B[2]) * r + _B[3]) * r + _B[4]) * r + 1.0),
            out,
        )
        out = np.where(p <= 0.0, -np.inf, out)
        out = np.where(p >= 1.0, np.inf, out)
        return out


def norm_cdf(x) -> np.ndarray:
    """Standard normal CDF."""
    return np.asarray(_ndtr_impl(np.asarray(x, dtype=float)), dtype=float)


def norm_ppf(p) -> np.ndarray:
    """Standard normal quantile function."""
    return np.asarray(_ndtri_impl(np.asarray(p, dtype=float)), dtype=float)


def norm_pdf(x) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return np.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


# ---------------------------------------------------------------------------
# 1. Measure-type safety — Iron Rule #1
# ---------------------------------------------------------------------------

MEASURES = frozenset(
    {"count", "rate", "ratio", "acv", "arr", "tcv", "billings", "revenue", "cash", "days"}
)


class MeasureError(TypeError):
    """Raised when two incompatible measure types are combined."""


@dataclass(frozen=True)
class Quantity:
    """A number that knows what kind of number it is.

    ``TCV = ACV x term_years``, so a 1-year to 3-year term-mix shift triples reported TCV
    bookings with zero change in ARR. Tagging prevents that from being summed away.
    """

    value: float
    measure: str
    period: str = ""
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.measure not in MEASURES:
            raise MeasureError(f"unknown measure {self.measure!r}; expected one of {sorted(MEASURES)}")

    def _check(self, other: "Quantity") -> None:
        if not isinstance(other, Quantity):
            raise MeasureError("can only combine Quantity with Quantity")
        if self.measure != other.measure:
            raise MeasureError(f"cannot combine {self.measure} with {other.measure}")
        if self.currency != other.currency:
            raise MeasureError(f"cannot combine {self.currency} with {other.currency}")
        if self.period and other.period and self.period != other.period:
            raise MeasureError(f"cannot combine period {self.period} with {other.period}")

    def __add__(self, other: "Quantity") -> "Quantity":
        self._check(other)
        return Quantity(self.value + other.value, self.measure, self.period or other.period, self.currency)

    def __sub__(self, other: "Quantity") -> "Quantity":
        self._check(other)
        return Quantity(self.value - other.value, self.measure, self.period or other.period, self.currency)

    def __mul__(self, k: float) -> "Quantity":
        if isinstance(k, Quantity):
            raise MeasureError("multiply a Quantity by a scalar, not by another Quantity")
        return Quantity(self.value * float(k), self.measure, self.period, self.currency)

    __rmul__ = __mul__

    def as_measure(self, measure: str, factor: float = 1.0) -> "Quantity":
        """Explicit, auditable conversion between measure types."""
        return Quantity(self.value * factor, measure, self.period, self.currency)


def sum_quantities(items: Iterable[Quantity]) -> Quantity:
    items = list(items)
    if not items:
        raise ValueError("nothing to sum")
    total = items[0]
    for q in items[1:]:
        total = total + q
    return total


def tcv_from_acv(acv: float, term_years: float) -> float:
    return float(acv) * float(term_years)


def acv_from_tcv(tcv: float, term_years: float) -> float:
    if term_years <= 0:
        raise ValueError("term_years must be positive")
    return float(tcv) / float(term_years)


# ---------------------------------------------------------------------------
# 2. Distributions
# ---------------------------------------------------------------------------


class Dist:
    """Minimal sampling interface so every uncertain input can be swapped freely."""

    def sample(self, rng: np.random.Generator, size) -> np.ndarray:  # pragma: no cover - abstract
        raise NotImplementedError

    @property
    def mean(self) -> float:  # pragma: no cover - abstract
        raise NotImplementedError


@dataclass(frozen=True)
class Point(Dist):
    value: float

    def sample(self, rng, size):
        return np.full(size, float(self.value))

    @property
    def mean(self):
        return float(self.value)


@dataclass(frozen=True)
class Normal(Dist):
    mu: float
    sd: float

    def sample(self, rng, size):
        return rng.normal(self.mu, self.sd, size)

    @property
    def mean(self):
        return float(self.mu)


@dataclass(frozen=True)
class LogNormal(Dist):
    """Parameterised by the *median* and the log-scale sigma."""

    median: float
    sigma: float

    def sample(self, rng, size):
        if self.median <= 0:
            return np.zeros(size)
        return np.exp(np.log(self.median) + self.sigma * rng.standard_normal(size))

    @property
    def mean(self):
        return float(self.median * math.exp(0.5 * self.sigma ** 2))


@dataclass(frozen=True)
class Beta(Dist):
    """Beta distribution specified by mean and sd — the natural form for rates."""

    mean_: float
    sd: float

    def __post_init__(self):
        m, s = self.mean_, self.sd
        if not 0.0 < m < 1.0:
            raise ValueError("Beta mean must be in (0, 1)")
        if s <= 0 or s ** 2 >= m * (1 - m):
            raise ValueError("Beta sd too large for that mean")

    def _ab(self) -> Tuple[float, float]:
        m, v = self.mean_, self.sd ** 2
        k = m * (1 - m) / v - 1.0
        return m * k, (1 - m) * k

    def sample(self, rng, size):
        a, b = self._ab()
        return rng.beta(a, b, size)

    @property
    def mean(self):
        return float(self.mean_)


@dataclass(frozen=True)
class Triangular(Dist):
    low: float
    mode: float
    high: float

    def sample(self, rng, size):
        return rng.triangular(self.low, self.mode, self.high, size)

    @property
    def mean(self):
        return float((self.low + self.mode + self.high) / 3.0)


@dataclass(frozen=True)
class TruncNormal(Dist):
    mu: float
    sd: float
    low: float = -np.inf
    high: float = np.inf

    def sample(self, rng, size):
        return np.clip(rng.normal(self.mu, self.sd, size), self.low, self.high)

    @property
    def mean(self):
        return float(min(max(self.mu, self.low), self.high))


def as_dist(x) -> Dist:
    """Coerce a scalar or (mu, sd) pair into a Dist. Scalars become Point."""
    if isinstance(x, Dist):
        return x
    if isinstance(x, (int, float, np.floating, np.integer)):
        return Point(float(x))
    if isinstance(x, tuple) and len(x) == 2:
        return Normal(float(x[0]), float(x[1]))
    raise TypeError(f"cannot interpret {x!r} as a distribution")


# ---------------------------------------------------------------------------
# 3. Baseline — establish it before reading any driver research (Iron Rule #3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AR1Fit:
    alpha: float
    beta: float
    sigma: float
    n: int
    r2: float

    @property
    def long_run_mean(self) -> float:
        if abs(self.beta) >= 1.0:
            return float("nan")
        return self.alpha / (1.0 - self.beta)

    def forecast(self, g_last: float, horizon: int) -> np.ndarray:
        out, g = np.empty(horizon), float(g_last)
        for h in range(horizon):
            g = self.alpha + self.beta * g
            out[h] = g
        return out


def fit_ar1(growth: Sequence[float], shrink_beta_to: Optional[float] = None,
            shrink_weight: float = 0.0) -> AR1Fit:
    """Fit ``g_t = alpha + beta*g_{t-1} + eps``.

    ``shrink_beta_to`` / ``shrink_weight`` implement the peer-shrinkage step from SKILL.md
    step 3: with 8-12 quarters the own-history beta is noisy, so pull it toward a comparable
    set estimate. weight 0 = pure own history, 1 = pure peer prior.
    """
    g = np.asarray(growth, dtype=float)
    if g.size < 4:
        raise ValueError("need at least 4 growth observations for an AR(1)")
    y, x = g[1:], g[:-1]
    X = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    alpha, beta = float(coef[0]), float(coef[1])
    if shrink_beta_to is not None and shrink_weight > 0:
        w = float(np.clip(shrink_weight, 0.0, 1.0))
        beta_s = (1 - w) * beta + w * float(shrink_beta_to)
        alpha = float(np.mean(y) - beta_s * np.mean(x))
        beta = beta_s
    resid = y - (alpha + beta * x)
    dof = max(len(y) - 2, 1)
    sigma = float(np.sqrt(np.sum(resid ** 2) / dof))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = float(1.0 - np.sum(resid ** 2) / ss_tot) if ss_tot > 0 else float("nan")
    return AR1Fit(alpha, beta, sigma, len(y), r2)


def ar1_paths(fit: AR1Fit, g_last: float, horizon: int, n_sims: int = 20000,
              seed: int = 0) -> np.ndarray:
    """Simulate growth-rate paths. Shape ``(n_sims, horizon)``."""
    rng = np.random.default_rng(seed)
    out = np.empty((n_sims, horizon))
    g = np.full(n_sims, float(g_last))
    for h in range(horizon):
        g = fit.alpha + fit.beta * g + rng.normal(0.0, fit.sigma, n_sims)
        out[:, h] = g
    return out


def visibility_ratio(contracted_revenue: float, total_forecast_revenue: float) -> float:
    """Contracted / total. Bounds the accuracy you can possibly achieve (SKILL.md step 2)."""
    if total_forecast_revenue <= 0:
        raise ValueError("total_forecast_revenue must be positive")
    return float(contracted_revenue) / float(total_forecast_revenue)


# ---------------------------------------------------------------------------
# 4. Order flow — deal-level simulation
# ---------------------------------------------------------------------------


@dataclass
class Deal:
    """One open opportunity as of the snapshot date.

    ``amount`` should already be expressed in the measure you intend to aggregate
    (ACV *or* TCV — pick one and stay in it). ``p_win`` must be the *recalibrated*
    probability, not the CRM stage default (see ``platt_fit`` / ``isotonic_fit``).
    """

    deal_id: str
    amount: float
    p_win: float
    realization_median: float = 0.95
    realization_sigma: float = 0.25
    rho: Optional[float] = None  # per-deal factor loading override
    segment: str = ""


@dataclass
class DealListResult:
    draws: np.ndarray
    modeled_draws: np.ndarray
    tail_draws: np.ndarray
    expected_independent_sd: float

    def summary(self, qs: Sequence[float] = (0.1, 0.25, 0.5, 0.75, 0.9)) -> Dict[str, float]:
        out = {"mean": float(self.draws.mean()), "sd": float(self.draws.std(ddof=1))}
        out.update({f"p{int(q * 100)}": float(v) for q, v in zip(qs, np.quantile(self.draws, qs))})
        return out


def simulate_deal_list(
    deals: Sequence[Deal],
    rho: float = 0.15,
    n_sims: int = 20000,
    seed: int = 0,
    tail_median: float = 0.0,
    tail_sigma: float = 0.30,
    chunk: int = 4000,
) -> DealListResult:
    """Correlated deal-list Monte Carlo (one-factor Gaussian copula).

    Independent Bernoulli draws understate quarter-end variance badly: a budget freeze, a
    macro shock or a competitor's price move hits many deals at once. The single common
    factor with loading ``sqrt(rho)`` reproduces the historical over-dispersion with one
    parameter you can actually fit (``fit_rho_to_target_sd``).

    ``tail_median`` is the *unmodeled* created-and-closed-in-quarter business, which can be
    a third of a quarter. Model it explicitly as a lognormal add-on; never as a fudge factor
    inside the deal probabilities.
    """
    if not deals:
        raise ValueError("deal list is empty")
    if not 0.0 <= rho < 1.0:
        raise ValueError("rho must be in [0, 1)")

    amount = np.array([d.amount for d in deals], dtype=float)
    p = np.clip(np.array([d.p_win for d in deals], dtype=float), 1e-9, 1 - 1e-9)
    r_med = np.array([d.realization_median for d in deals], dtype=float)
    r_sig = np.array([d.realization_sigma for d in deals], dtype=float)
    load = np.array([rho if d.rho is None else d.rho for d in deals], dtype=float)
    if np.any((load < 0) | (load >= 1)):
        raise ValueError("per-deal rho must be in [0, 1)")

    thr = norm_ppf(p)
    a, b = np.sqrt(load), np.sqrt(1.0 - load)
    rng = np.random.default_rng(seed)

    modeled = np.empty(n_sims)
    done = 0
    while done < n_sims:
        m = min(chunk, n_sims - done)
        f = rng.standard_normal((m, 1))
        e = rng.standard_normal((m, amount.size))
        won = (a * f + b * e) < thr
        mult = np.exp(np.log(np.where(r_med > 0, r_med, 1e-12)) + r_sig * rng.standard_normal((m, amount.size)))
        modeled[done:done + m] = (won * amount * mult).sum(axis=1)
        done += m

    if tail_median > 0:
        tail = np.exp(np.log(tail_median) + tail_sigma * rng.standard_normal(n_sims))
    else:
        tail = np.zeros(n_sims)

    # Reference sd if outcomes were independent and amounts realized exactly.
    indep_sd = float(np.sqrt(np.sum((amount ** 2) * p * (1 - p))))
    return DealListResult(modeled + tail, modeled, tail, indep_sd)


def fit_rho_to_target_sd(
    deals: Sequence[Deal],
    target_sd: float,
    n_sims: int = 8000,
    seed: int = 0,
    lo: float = 0.0,
    hi: float = 0.9,
    tol: float = 1e-3,
    max_iter: int = 30,
) -> float:
    """Bisect on rho until the simulated sd of the bookings total matches history.

    ``target_sd`` is the standard deviation of (actual bookings - model mean) over your
    backtest quarters. There is no published estimate of B2B deal-outcome correlation, so
    this is the honest way to get one: fit it to your own over-dispersion.
    """
    def sd_at(r: float) -> float:
        return float(simulate_deal_list(deals, rho=r, n_sims=n_sims, seed=seed).modeled_draws.std(ddof=1))

    sd_lo, sd_hi = sd_at(lo), sd_at(hi)
    if target_sd <= sd_lo:
        return lo
    if target_sd >= sd_hi:
        return hi
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        s = sd_at(mid)
        if abs(s - target_sd) / target_sd < tol:
            return mid
        if s < target_sd:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def bvn_cdf(h: float, k: float, rho: float, n_nodes: int = 60) -> float:
    """Bivariate standard normal CDF via Gauss-Legendre integration of Plackett's identity.

    ``Phi2(h,k;rho) = Phi(h)Phi(k) + integral_0^rho phi2(h,k;r) dr``. Accurate to ~1e-12 for
    |rho| < 0.99, which is all we need to translate copula parameters into indicator
    correlations.
    """
    if not -1.0 < rho < 1.0:
        raise ValueError("rho must be in (-1, 1)")
    base = float(norm_cdf(h) * norm_cdf(k))
    if rho == 0.0:
        return base
    x, w = np.polynomial.legendre.leggauss(n_nodes)
    r = 0.5 * rho * (x + 1.0)
    jac = 0.5 * rho
    one_m = 1.0 - r * r
    dens = np.exp(-(h * h - 2 * r * h * k + k * k) / (2 * one_m)) / (2 * math.pi * np.sqrt(one_m))
    return float(base + jac * np.sum(w * dens))


def indicator_correlation(p1: float, p2: float, rho_latent: float) -> float:
    """Correlation of the *win/lose indicators* implied by a latent Gaussian copula rho.

    These are not the same number and confusing them is a real trap. The textbook
    exchangeable-Bernoulli variance formula
    ``Var(wins) = n*p*(1-p)*[1 + (n-1)*rho]`` takes the **indicator** correlation. The copula
    parameter passed to ``simulate_deal_list`` is the **latent** one, and it is always the
    larger of the two: at p = 0.30, a latent rho of 0.20 is an indicator correlation of
    0.119. Feeding a latent rho into the variance formula overstates the spread.
    """
    h, k = float(norm_ppf(p1)), float(norm_ppf(p2))
    joint = bvn_cdf(h, k, rho_latent)
    cov = joint - p1 * p2
    denom = math.sqrt(p1 * (1 - p1) * p2 * (1 - p2))
    return float(cov / denom) if denom > 0 else float("nan")


def latent_rho_from_indicator(p: float, rho_indicator: float, tol: float = 1e-10) -> float:
    """Invert ``indicator_correlation`` at equal marginals — the parameter to hand the copula."""
    if rho_indicator <= 0:
        return 0.0
    lo, hi = 0.0, 0.999
    if indicator_correlation(p, p, hi) < rho_indicator:
        return hi
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if indicator_correlation(p, p, mid) < rho_indicator:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def effective_deal_count(amounts: Sequence[float]) -> float:
    """``(sum a)^2 / sum a^2`` — the concentration-adjusted number of deals.

    Deal sizes in this category are heavy-tailed, so the headline deal count badly overstates
    how much diversification a pipeline actually has. A quarter with 8 deals at $1.2M and 60
    at $120K has 68 deals but an effective count of 23, and it is the effective count that
    governs how much a common factor widens the total.
    """
    a = np.asarray(amounts, dtype=float)
    s2 = float(np.sum(a ** 2))
    if s2 <= 0:
        raise ValueError("amounts must contain a positive value")
    return float(np.sum(a) ** 2 / s2)


def exchangeable_sd_inflation(n_deals: float, rho_indicator: float) -> float:
    """``sqrt(1 + (n-1)*rho_indicator)`` — how much correlation widens a bookings total.

    The point most people miss: this grows without bound in ``n``. The idiosyncratic part of
    deal risk diversifies away across a large pipeline; the common factor does not. On a
    30-deal quarter a modest correlation roughly doubles the standard deviation, but on a
    200-deal quarter the same correlation quadruples it, and the copula stops being a
    refinement and becomes the dominant term.

    Pass ``effective_deal_count(amounts)`` rather than the raw count when deal sizes are
    unequal, which they always are.
    """
    if n_deals < 1:
        raise ValueError("n_deals must be >= 1")
    return float(math.sqrt(max(1.0 + (n_deals - 1) * rho_indicator, 0.0)))


def category_forecast(
    category_dollars: Mapping[str, float],
    realization: Mapping[str, Tuple[float, float]],
    n_sims: int = 20000,
    seed: int = 0,
    rho: float = 0.3,
) -> np.ndarray:
    """Judgmental forecast rolled up from forecast categories with *fitted* realization rates.

    ``realization[c] = (mean, sd)`` of the historical realized fraction of dollars in
    category ``c`` (Commit, Best Case, Pipeline, ...). Never use the CRM's stated category
    probabilities: they are policy defaults. Fit these from forecast-lock snapshots and
    shrink low-N reps with ``shrink_binomial``.

    Categories share a common factor because a rep who sandbags Commit usually sandbags Best
    Case in the same quarter.
    """
    cats = list(category_dollars)
    rng = np.random.default_rng(seed)
    f = rng.standard_normal((n_sims, 1))
    total = np.zeros(n_sims)
    for j, c in enumerate(cats):
        mu, sd = realization[c]
        z = math.sqrt(rho) * f[:, 0] + math.sqrt(1 - rho) * rng.standard_normal(n_sims)
        r = np.clip(mu + sd * z, 0.0, 1.5)
        total += r * float(category_dollars[c])
    return total


def pace_nowcast(
    day_index: int,
    days_in_quarter: int,
    booked_to_date: float,
    pace_curve: Sequence[float],
    residual_sd_frac: float = 0.15,
    n_sims: int = 20000,
    seed: int = 0,
) -> np.ndarray:
    """Scale intra-quarter bookings by the historical cumulative pace curve.

    ``pace_curve[t]`` is the historical mean cumulative share of the quarter booked by day
    ``t`` (length ``days_in_quarter + 1``, ending at 1.0). Backloaded enterprise quarters make
    naive linear run-rates wildly pessimistic early and wildly optimistic late; the curve is
    the fix. ``residual_sd_frac`` is the multiplicative dispersion of the scaling, which
    should shrink as the quarter progresses — fit it per day-bucket from history.
    """
    curve = np.asarray(pace_curve, dtype=float)
    if curve.size != days_in_quarter + 1:
        raise ValueError("pace_curve must have days_in_quarter + 1 entries")
    if not 0 <= day_index <= days_in_quarter:
        raise ValueError("day_index out of range")
    share = float(curve[day_index])
    if share <= 1e-6:
        raise ValueError("pace share at this day is ~0; nowcast is uninformative")
    rng = np.random.default_rng(seed)
    point = booked_to_date / share
    return point * np.exp(residual_sd_frac * rng.standard_normal(n_sims) - 0.5 * residual_sd_frac ** 2)


# ---------------------------------------------------------------------------
# 5. Calibrating the inputs
# ---------------------------------------------------------------------------


def platt_fit(scores: Sequence[float], outcomes: Sequence[int], max_iter: int = 100,
              tol: float = 1e-10) -> Tuple[float, float]:
    """Platt scaling: logistic regression of won/lost on the logit of the raw probability.

    Returns ``(a, b)`` for ``p_cal = sigmoid(a * logit(p_raw) + b)``. Pass raw probabilities
    as ``scores``; the logit transform is applied here.
    """
    s = np.clip(np.asarray(scores, dtype=float), 1e-6, 1 - 1e-6)
    x = np.log(s / (1 - s))
    y = np.asarray(outcomes, dtype=float)
    if x.size != y.size:
        raise ValueError("scores and outcomes must be the same length")
    beta = np.zeros(2)
    X = np.column_stack([x, np.ones_like(x)])
    for _ in range(max_iter):
        eta = X @ beta
        mu = 1.0 / (1.0 + np.exp(-eta))
        w = np.clip(mu * (1 - mu), 1e-9, None)
        z = eta + (y - mu) / w
        XtW = X.T * w
        step = np.linalg.solve(XtW @ X + 1e-9 * np.eye(2), XtW @ z)
        if np.max(np.abs(step - beta)) < tol:
            beta = step
            break
        beta = step
    return float(beta[0]), float(beta[1])


def platt_apply(scores: Sequence[float], a: float, b: float) -> np.ndarray:
    s = np.clip(np.asarray(scores, dtype=float), 1e-6, 1 - 1e-6)
    return 1.0 / (1.0 + np.exp(-(a * np.log(s / (1 - s)) + b)))


def isotonic_fit(scores: Sequence[float], outcomes: Sequence[float],
                 weights: Optional[Sequence[float]] = None) -> Tuple[np.ndarray, np.ndarray]:
    """Pool-adjacent-violators isotonic regression. Returns ``(x_knots, y_fitted)``.

    Non-parametric and monotone, so it cannot invert the ordering of your stages but can
    flatten a stage that carries no information. Needs more resolved deals than Platt;
    with <300 resolved deals prefer Platt.
    """
    x = np.asarray(scores, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    w = np.ones_like(x) if weights is None else np.asarray(weights, dtype=float)
    order = np.argsort(x, kind="mergesort")
    x, y, w = x[order], y[order], w[order]

    vals: List[float] = []
    wts: List[float] = []
    cnt: List[int] = []
    for yi, wi in zip(y, w):
        vals.append(float(yi))
        wts.append(float(wi))
        cnt.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            v2, w2, c2 = vals.pop(), wts.pop(), cnt.pop()
            v1, w1, c1 = vals.pop(), wts.pop(), cnt.pop()
            vals.append((v1 * w1 + v2 * w2) / (w1 + w2))
            wts.append(w1 + w2)
            cnt.append(c1 + c2)
    fitted = np.repeat(np.array(vals), np.array(cnt))
    return x, fitted


def isotonic_apply(x_knots: np.ndarray, y_fitted: np.ndarray, scores: Sequence[float]) -> np.ndarray:
    return np.interp(np.asarray(scores, dtype=float), x_knots, y_fitted,
                     left=float(y_fitted[0]), right=float(y_fitted[-1]))


def shrink_binomial(successes: Sequence[float], trials: Sequence[float]) -> Dict[str, np.ndarray]:
    """Empirical-Bayes (beta-binomial) shrinkage of per-rep / per-segment win rates.

    A rep with 3 of 4 wins does not have a 75% win rate. Method-of-moments prior fitted on
    the pooled rates, then posterior mean ``(k + alpha) / (n + alpha + beta)``.
    """
    k = np.asarray(successes, dtype=float)
    n = np.asarray(trials, dtype=float)
    if np.any(n <= 0):
        raise ValueError("trials must be positive")
    p_hat = k / n
    p_bar = float(np.sum(k) / np.sum(n))
    # Between-group variance net of binomial sampling noise.
    w = n / np.sum(n)
    total_var = float(np.sum(w * (p_hat - p_bar) ** 2))
    within = float(np.sum(w * p_bar * (1 - p_bar) / n))
    between = max(total_var - within, 1e-9)
    kappa = max(p_bar * (1 - p_bar) / between - 1.0, 1e-6)
    alpha, beta = p_bar * kappa, (1 - p_bar) * kappa
    post = (k + alpha) / (n + alpha + beta)
    return {
        "shrunk": post,
        "raw": p_hat,
        "prior_mean": np.array(p_bar),
        "alpha": np.array(alpha),
        "beta": np.array(beta),
        "shrinkage_weight": (alpha + beta) / (n + alpha + beta),
    }


def shrink_normal(estimates: Sequence[float], std_errors: Sequence[float]) -> Dict[str, np.ndarray]:
    """James-Stein / normal-normal shrinkage for continuous rates (realization multipliers)."""
    y = np.asarray(estimates, dtype=float)
    se = np.asarray(std_errors, dtype=float)
    if np.any(se <= 0):
        raise ValueError("std_errors must be positive")
    grand = float(np.mean(y))
    tau2 = max(float(np.var(y, ddof=1) - np.mean(se ** 2)), 1e-12)
    w = tau2 / (tau2 + se ** 2)
    return {"shrunk": grand + w * (y - grand), "raw": y, "prior_mean": np.array(grand),
            "tau2": np.array(tau2), "weight": w}


# ---------------------------------------------------------------------------
# 6. ARR waterfall
# ---------------------------------------------------------------------------


@dataclass
class WaterfallSpec:
    """Per-period ARR waterfall inputs. Rates are annual unless ``periods_per_year`` says otherwise.

    ``grr`` is the annual gross retention rate applied to the opening base; ``expansion`` is
    the annual expansion rate on the surviving base (NRR - GRR); ``new_logo_arr`` is the
    absolute new-logo ARR added per period.
    """

    opening_arr: float
    grr: Dist
    expansion: Dist
    new_logo_arr: Dist
    periods_per_year: int = 4
    rho: float = 0.35  # common factor across periods: a bad year is bad in all four quarters


@dataclass
class WaterfallResult:
    arr: np.ndarray            # (n_sims, n_periods + 1)
    churn: np.ndarray          # (n_sims, n_periods)
    expansion: np.ndarray
    new_logo: np.ndarray

    @property
    def closing(self) -> np.ndarray:
        return self.arr[:, -1]

    def mean_bridge(self) -> Dict[str, float]:
        return {
            "opening_arr": float(self.arr[:, 0].mean()),
            "churn": float(-self.churn.sum(axis=1).mean()),
            "expansion": float(self.expansion.sum(axis=1).mean()),
            "new_logo": float(self.new_logo.sum(axis=1).mean()),
            "closing_arr": float(self.arr[:, -1].mean()),
        }


def simulate_arr_waterfall(spec: WaterfallSpec, n_periods: int, n_sims: int = 20000,
                           seed: int = 0) -> WaterfallResult:
    """Opening ARR -> churn -> expansion -> new logos -> closing ARR, simulated.

    Churn and expansion are applied to the opening base of each period; new logos are added
    at period end so they contribute no expansion in their first period. A single common
    factor correlates the periods within a run: real ARR years are persistent, not four
    independent coin flips.
    """
    rng = np.random.default_rng(seed)
    ppy = spec.periods_per_year
    arr = np.empty((n_sims, n_periods + 1))
    arr[:, 0] = spec.opening_arr
    churn = np.empty((n_sims, n_periods))
    expan = np.empty((n_sims, n_periods))
    newlg = np.empty((n_sims, n_periods))

    f = rng.standard_normal(n_sims)
    a, b = math.sqrt(spec.rho), math.sqrt(1.0 - spec.rho)

    def corr_sample(dist: Dist, size: int) -> np.ndarray:
        """Sample the dist, then re-couple it to the common factor via a rank-preserving map."""
        raw = dist.sample(rng, size)
        if isinstance(dist, Point) or spec.rho <= 0:
            return raw
        z = a * f + b * rng.standard_normal(size)
        u = norm_cdf(z)
        return np.quantile(raw, np.clip(u, 1e-6, 1 - 1e-6))

    for t in range(n_periods):
        grr_a = np.clip(corr_sample(spec.grr, n_sims), 0.0, 1.0)
        exp_a = np.clip(corr_sample(spec.expansion, n_sims), -0.5, 1.0)
        nl = np.maximum(corr_sample(spec.new_logo_arr, n_sims), 0.0)

        grr_p = grr_a ** (1.0 / ppy)
        exp_p = (1.0 + exp_a) ** (1.0 / ppy) - 1.0

        base = arr[:, t]
        survived = base * grr_p
        churn[:, t] = base - survived
        expan[:, t] = survived * exp_p
        newlg[:, t] = nl
        arr[:, t + 1] = survived + expan[:, t] + nl

    return WaterfallResult(arr, churn, expan, newlg)


# ---------------------------------------------------------------------------
# 7. ASC 606 recognition
# ---------------------------------------------------------------------------

RECOGNITION_KINDS = ("term_license", "saas", "support", "perpetual", "services", "consumption")


@dataclass
class Contract:
    """One booked contract, in months from an arbitrary origin.

    ``kind`` determines the recognition pattern, and getting it wrong is the single most
    expensive modeling error in this category:

    * ``term_license`` — the license is a distinct performance obligation satisfied at a
      point in time. ``license_share`` of TCV lands in the booking month; the rest (support)
      is ratable. Commvault's term licenses work this way.
    * ``saas`` — a single combined performance obligation, fully ratable. Rubrik's RSC works
      this way. Never model it like a term license.
    * ``support``/``consumption`` — ratable.
    * ``perpetual`` — 100% at the booking month.
    * ``services`` — ratable over ``delivery_months`` if given, else the term.
    """

    contract_id: str
    start_month: int
    term_months: int
    acv: float
    kind: str = "saas"
    license_share: float = 0.0
    billing: str = "annual"  # annual | prepaid | quarterly | monthly
    delivery_months: Optional[int] = None
    cancellable: bool = False  # cancellable arrangements are excluded from RPO

    def __post_init__(self) -> None:
        if self.kind not in RECOGNITION_KINDS:
            raise ValueError(f"unknown kind {self.kind!r}; expected one of {RECOGNITION_KINDS}")
        if self.term_months <= 0:
            raise ValueError("term_months must be positive")
        if self.kind == "term_license" and not 0.0 <= self.license_share <= 1.0:
            raise ValueError("license_share must be in [0, 1]")
        if self.billing not in ("annual", "prepaid", "quarterly", "monthly"):
            raise ValueError(f"unknown billing schedule {self.billing!r}")

    @property
    def term_years(self) -> float:
        return self.term_months / 12.0

    @property
    def tcv(self) -> float:
        return self.acv * self.term_years


@dataclass
class Schedule:
    """Monthly flows and end-of-month stocks produced by ``recognize_contracts``."""

    n_months: int
    revenue_by_kind: Dict[str, np.ndarray]
    billings: np.ndarray
    rpo: np.ndarray
    crpo: np.ndarray
    deferred_revenue: np.ndarray
    contract_assets: np.ndarray

    @property
    def revenue(self) -> np.ndarray:
        return sum(self.revenue_by_kind.values())

    def to_periods(self, months_per_period: int = 3) -> "Schedule":
        """Roll monthly detail up to quarters (flows summed, stocks taken at period end)."""
        n = self.n_months // months_per_period
        if n == 0:
            raise ValueError("horizon shorter than one period")

        def flow(a):
            return a[: n * months_per_period].reshape(n, months_per_period).sum(axis=1)

        def stock(a):
            return a[: n * months_per_period].reshape(n, months_per_period)[:, -1]

        return Schedule(
            n_months=n,
            revenue_by_kind={k: flow(v) for k, v in self.revenue_by_kind.items()},
            billings=flow(self.billings),
            rpo=stock(self.rpo),
            crpo=stock(self.crpo),
            deferred_revenue=stock(self.deferred_revenue),
            contract_assets=stock(self.contract_assets),
        )


def recognize_contracts(contracts: Sequence[Contract], n_months: int) -> Schedule:
    """Bridge bookings to revenue on a schedule, per contract, under ASC 606.

    Never apply a growth rate to last quarter's revenue instead of doing this: a term-mix or
    a term-license-to-SaaS shift changes reported revenue with no change in ARR at all, and
    only a per-contract schedule catches it.
    """
    rev = {k: np.zeros(n_months) for k in RECOGNITION_KINDS}
    bill = np.zeros(n_months)
    # Full recognition profile extended past the horizon so RPO/cRPO stay correct at the edge.
    horizon = n_months + max((c.start_month + c.term_months for c in contracts), default=0) + 13
    rev_all = np.zeros(horizon)
    rev_noncancellable = np.zeros(horizon)

    for c in contracts:
        s, m = c.start_month, c.term_months
        tcv = c.tcv
        prof = np.zeros(horizon)

        if c.kind == "perpetual":
            if 0 <= s < horizon:
                prof[s] += tcv
        elif c.kind == "term_license":
            upfront = tcv * c.license_share
            if 0 <= s < horizon:
                prof[s] += upfront
            end = min(s + m, horizon)
            if end > s:
                prof[s:end] += (tcv - upfront) / m
        elif c.kind == "services":
            d = c.delivery_months or m
            end = min(s + d, horizon)
            if end > s:
                prof[s:end] += tcv / d
        else:  # saas, support, consumption
            end = min(s + m, horizon)
            if end > s:
                prof[s:end] += tcv / m

        rev_all += prof
        if not c.cancellable:
            rev_noncancellable += prof
        rev[c.kind][:n_months] += prof[:n_months]

        # Billings
        if c.billing == "prepaid":
            if 0 <= s < n_months:
                bill[s] += tcv
        elif c.billing == "annual":
            k = 0
            while k * 12 < m:
                months_this = min(12, m - k * 12)
                idx = s + k * 12
                if 0 <= idx < n_months:
                    bill[idx] += c.acv * months_this / 12.0
                k += 1
        elif c.billing == "quarterly":
            k = 0
            while k * 3 < m:
                months_this = min(3, m - k * 3)
                idx = s + k * 3
                if 0 <= idx < n_months:
                    bill[idx] += c.acv * months_this / 12.0
                k += 1
        else:  # monthly
            for k in range(m):
                idx = s + k
                if 0 <= idx < n_months:
                    bill[idx] += c.acv / 12.0

    cum_rev = np.cumsum(rev_all)
    total_noncancellable = float(rev_noncancellable.sum())
    cum_rev_nc = np.cumsum(rev_noncancellable)

    rpo = np.maximum(total_noncancellable - cum_rev_nc[:n_months], 0.0)
    crpo = np.array([rev_noncancellable[t + 1: t + 13].sum() for t in range(n_months)])

    cum_bill = np.cumsum(bill)
    net = cum_bill - cum_rev[:n_months]
    deferred = np.maximum(net, 0.0)
    assets = np.maximum(-net, 0.0)

    return Schedule(n_months, {k: v for k, v in rev.items()}, bill, rpo, crpo, deferred, assets)


# ---------------------------------------------------------------------------
# 8. Reconciliation to disclosed metrics
# ---------------------------------------------------------------------------


def revenue_identity_residual(billings: float, delta_deferred_revenue: float,
                              delta_contract_assets: float, revenue: float) -> Dict[str, float]:
    """``Revenue = Billings - dDeferredRevenue + dContractAssets``.

    The two-term version (``Rev = Billings - dDR``) silently breaks whenever the vendor bills
    in arrears or has unbilled receivables from multi-year deals. A residual above ~2-3% of
    revenue means your bookings-to-billings mapping is wrong, not that the identity is soft.
    """
    implied = billings - delta_deferred_revenue + delta_contract_assets
    resid = revenue - implied
    return {
        "implied_revenue": float(implied),
        "reported_revenue": float(revenue),
        "residual": float(resid),
        "residual_pct_of_revenue": float(resid / revenue) if revenue else float("nan"),
    }


def rpo_rollforward_residual(opening_rpo: float, bookings_tcv: float, revenue: float,
                             closing_rpo: float, fx_and_other: float = 0.0) -> Dict[str, float]:
    """``closing RPO = opening RPO + bookings TCV - revenue + FX/other``.

    RPO excludes cancellable arrangements, so it is never a hard revenue floor — but the
    roll-forward still has to close. Residual above ~2-3% of RPO means the bookings mapping,
    the term-mix assumption, or the cancellability treatment is wrong.
    """
    implied = opening_rpo + bookings_tcv - revenue + fx_and_other
    resid = closing_rpo - implied
    return {
        "implied_closing_rpo": float(implied),
        "reported_closing_rpo": float(closing_rpo),
        "residual": float(resid),
        "residual_pct_of_rpo": float(resid / closing_rpo) if closing_rpo else float("nan"),
        "passes_3pct_check": bool(closing_rpo and abs(resid / closing_rpo) <= 0.03),
    }


# ---------------------------------------------------------------------------
# 9. P&L and cash
# ---------------------------------------------------------------------------


def pnl_by_stream(revenue: Mapping[str, float], gross_margin: Mapping[str, float],
                  opex: Mapping[str, float]) -> Dict[str, float]:
    """Build gross profit stream by stream, never from a blended margin.

    The spread between a term license (~97.6% GM) and SaaS (~64.5% GM) is 33 points. A
    blended margin bakes today's mix into every forecast period and therefore cannot
    represent the one mix shift that matters most.
    """
    missing = set(revenue) - set(gross_margin)
    if missing:
        raise KeyError(f"no gross margin supplied for stream(s): {sorted(missing)}")
    rev_total = float(sum(revenue.values()))
    gp = float(sum(v * gross_margin[k] for k, v in revenue.items()))
    opex_total = float(sum(opex.values()))
    oi = gp - opex_total
    out = {
        "revenue": rev_total,
        "cogs": rev_total - gp,
        "gross_profit": gp,
        "gross_margin": gp / rev_total if rev_total else float("nan"),
        "opex": opex_total,
        "operating_income": oi,
        "operating_margin": oi / rev_total if rev_total else float("nan"),
    }
    for k, v in revenue.items():
        out[f"gross_profit_{k}"] = float(v * gross_margin[k])
    for k, v in opex.items():
        out[f"opex_{k}_pct"] = float(v / rev_total) if rev_total else float("nan")
    return out


def fcf_bridge(operating_income: float, depreciation_amortization: float = 0.0,
               stock_based_comp: float = 0.0, delta_deferred_revenue: float = 0.0,
               delta_receivables: float = 0.0, delta_deferred_commissions: float = 0.0,
               delta_other_wc: float = 0.0, cash_taxes: float = 0.0,
               cash_interest: float = 0.0, capex: float = 0.0,
               buyback_to_offset_dilution: float = 0.0) -> Dict[str, float]:
    """GAAP operating income to free cash flow, with the SBC trap made explicit.

    Adding SBC back and stopping there overstates economic cash generation: at vendors that
    repurchase to offset dilution, the buyback *is* the cash cost of the SBC. Pass
    ``buyback_to_offset_dilution`` to get the honest number alongside the conventional one.
    Delta deferred revenue is usually the largest single line here.
    """
    ocf = (operating_income + depreciation_amortization + stock_based_comp
           + delta_deferred_revenue - delta_receivables - delta_deferred_commissions
           + delta_other_wc - cash_taxes - cash_interest)
    fcf = ocf - capex
    return {
        "operating_cash_flow": float(ocf),
        "free_cash_flow": float(fcf),
        "fcf_after_dilution_offset": float(fcf - buyback_to_offset_dilution),
        "sbc_addback": float(stock_based_comp),
        "deferred_revenue_contribution": float(delta_deferred_revenue),
    }


# ---------------------------------------------------------------------------
# 10. Closed-form levers — the "what moves the needle" arithmetic
# ---------------------------------------------------------------------------


def price_lever(revenue: float, price_pts: float, gross_margin: float,
                operating_margin: float, volume_elasticity: float = 0.0) -> Dict[str, float]:
    """Effect of a price change. Price flows to gross profit at ~100% absent volume loss.

    ``volume_elasticity`` is dVolume% / dPrice% (negative). No published elasticity exists for
    this category; the breakeven volume loss is ``gross_margin / (1 - ...)`` — reported below
    so you can sanity-check any elasticity you assume.
    """
    p = price_pts / 100.0
    vol = p * volume_elasticity
    new_rev = revenue * (1 + p) * (1 + vol)
    d_rev = new_rev - revenue
    # Price is pure margin; volume moves revenue at the gross margin rate.
    d_gp = revenue * p * (1 + vol) + revenue * vol * gross_margin
    new_oi = revenue * operating_margin + d_gp
    return {
        "revenue_delta": float(d_rev),
        "revenue_pct": float(d_rev / revenue),
        "gross_profit_delta": float(d_gp),
        "operating_margin_new": float(new_oi / new_rev) if new_rev else float("nan"),
        "operating_margin_delta_pts": float((new_oi / new_rev - operating_margin) * 100) if new_rev else float("nan"),
        "breakeven_volume_loss_pct_per_pt_price": float(1.0 / gross_margin) if gross_margin else float("nan"),
    }


def discount_lever(base_discount: float, pts_recovered: float) -> Dict[str, float]:
    """Net-price effect of tightening discount discipline.

    Taking 1 point off a 30% average discount raises net price by 1/(1-0.30) = 1.43%, not 1%.
    The denominator is what people forget.
    """
    if not 0 <= base_discount < 1:
        raise ValueError("base_discount must be in [0, 1)")
    d = pts_recovered / 100.0
    return {
        "net_price_pct": float(d / (1 - base_discount)),
        "new_discount": float(base_discount - d),
    }


def prepaid_cash_lever(arr_moved: float, extra_years_prepaid: float,
                       collection_efficiency: float = 1.0) -> Dict[str, float]:
    """One-time cash from moving customers to multi-year prepaid. Revenue effect: exactly zero.

    Worth stating loudly, because it is routinely presented as growth. It is a balance-sheet
    trade: cash now against cash later, and it does not repeat.
    """
    cash = arr_moved * extra_years_prepaid * collection_efficiency
    return {
        "one_time_cash": float(cash),
        "revenue_effect": 0.0,
        "recurring": False,
        "deferred_revenue_increase": float(cash),
    }


def operating_margin_from_growth_gap(revenue_growth: float, opex_growth: float,
                                     opex_ratio: float, gross_margin: float) -> Dict[str, float]:
    """The identity behind "0.6 pt of operating margin per point of growth gap".

    Holding gross margin flat, next period's opex ratio is
    ``opex_ratio * (1 + g_opex) / (1 + g_rev)``. Nothing about demand is involved, which is
    exactly why this is the most reliable margin lever on the list.
    """
    new_ratio = opex_ratio * (1 + opex_growth) / (1 + revenue_growth)
    old_margin = gross_margin - opex_ratio
    new_margin = gross_margin - new_ratio
    gap_pts = (revenue_growth - opex_growth) * 100
    return {
        "opex_ratio_new": float(new_ratio),
        "operating_margin_old": float(old_margin),
        "operating_margin_new": float(new_margin),
        "operating_margin_delta_pts": float((new_margin - old_margin) * 100),
        "gap_pts": float(gap_pts),
        "pts_per_gap_pt": float((new_margin - old_margin) * 100 / gap_pts) if gap_pts else float("nan"),
    }


def magic_number(net_new_arr: float, prior_period_sm_expense: float,
                 gross_margin: Optional[float] = None) -> float:
    """S&M efficiency. Supply ``gross_margin`` for the gross-margin-adjusted version."""
    if prior_period_sm_expense <= 0:
        raise ValueError("prior_period_sm_expense must be positive")
    mn = net_new_arr / prior_period_sm_expense
    return float(mn * gross_margin) if gross_margin is not None else float(mn)


def cac_payback_months(sm_expense: float, net_new_arr: float, gross_margin: float) -> float:
    """Months of gross profit on the new ARR needed to repay the S&M that produced it."""
    if net_new_arr <= 0 or gross_margin <= 0:
        return float("inf")
    return float(12.0 * sm_expense / (net_new_arr * gross_margin))


def arr_half_life(grr: float) -> float:
    """Years for the installed base to halve absent expansion and new logos."""
    if not 0 < grr < 1:
        raise ValueError("grr must be in (0, 1)")
    return float(math.log(0.5) / math.log(grr))


def steady_state_arr(new_logo_arr_per_year: float, nrr: float) -> float:
    """Equilibrium ARR at constant new-logo intake. Unbounded when NRR >= 1."""
    if nrr >= 1.0:
        return float("inf")
    return float(new_logo_arr_per_year / (1.0 - nrr))


def required_pipeline_coverage(win_rate: float, safety: float = 1.0) -> float:
    """Coverage is 1/win-rate, not "3x". At a 19% win rate you need ~5.3x."""
    if not 0 < win_rate <= 1:
        raise ValueError("win_rate must be in (0, 1]")
    return float(safety / win_rate)


# ---------------------------------------------------------------------------
# 11. Scoring and calibration
# ---------------------------------------------------------------------------


def crps_ensemble(draws: Sequence[float], observation: float) -> float:
    """CRPS of an ensemble forecast: ``E|X - y| - 0.5 * E|X - X'|``.

    Computed in O(n log n) from the sorted sample. Lower is better; CRPS reduces to MAE for
    a deterministic forecast, so a point forecast and a distribution are directly comparable.
    """
    x = np.sort(np.asarray(draws, dtype=float))
    n = x.size
    if n == 0:
        raise ValueError("empty ensemble")
    y = float(observation)
    term1 = float(np.mean(np.abs(x - y)))
    i = np.arange(1, n + 1, dtype=float)
    term2 = float(np.sum((2 * i - n - 1) * x)) / (n * n)
    return term1 - term2


def crps_normal(mu: float, sigma: float, observation: float) -> float:
    """Closed-form CRPS for a normal predictive distribution (useful as a reference)."""
    if sigma <= 0:
        return abs(observation - mu)
    z = (observation - mu) / sigma
    return float(sigma * (z * (2 * norm_cdf(z) - 1) + 2 * norm_pdf(z) - 1 / math.sqrt(math.pi)))


def pinball_loss(quantile_values: Mapping[float, float], observation: float) -> Dict[str, float]:
    """Pinball (quantile) loss, per tau and averaged. Keys of the mapping are the taus."""
    y = float(observation)
    per = {}
    for tau, q in quantile_values.items():
        if not 0 < tau < 1:
            raise ValueError("tau must be in (0, 1)")
        per[tau] = float((y - q) * tau if y >= q else (q - y) * (1 - tau))
    return {"per_tau": per, "mean": float(np.mean(list(per.values())))}


def brier_score(probabilities: Sequence[float], outcomes: Sequence[int]) -> Dict[str, float]:
    """Brier score with the Murphy decomposition into reliability, resolution, uncertainty."""
    p = np.asarray(probabilities, dtype=float)
    o = np.asarray(outcomes, dtype=float)
    if p.size != o.size:
        raise ValueError("length mismatch")
    bs = float(np.mean((p - o) ** 2))
    obar = float(np.mean(o))
    bins = np.clip((p * 10).astype(int), 0, 9)
    rel = res = 0.0
    for b in range(10):
        m = bins == b
        nk = int(m.sum())
        if nk == 0:
            continue
        pk, ok = float(p[m].mean()), float(o[m].mean())
        rel += nk * (pk - ok) ** 2
        res += nk * (ok - obar) ** 2
    n = p.size
    return {
        "brier": bs,
        "reliability": rel / n,
        "resolution": res / n,
        "uncertainty": obar * (1 - obar),
        "skill_vs_base_rate": float(1 - bs / (obar * (1 - obar))) if 0 < obar < 1 else float("nan"),
    }


def log_score_ensemble(draws: Sequence[float], observation: float,
                       bandwidth: Optional[float] = None) -> float:
    """Negative log predictive density via a Gaussian kernel density estimate of the ensemble.

    Sensitive to the tails by construction, which is a feature when a blown tail is what
    actually hurts. Prefer CRPS for headline reporting; use this as the tail cross-check.
    """
    x = np.asarray(draws, dtype=float)
    n = x.size
    sd = float(x.std(ddof=1))
    if bandwidth is None:
        iqr = float(np.subtract(*np.percentile(x, [75, 25])))
        bandwidth = 0.9 * min(sd, iqr / 1.349 if iqr > 0 else sd) * n ** (-0.2)
    bandwidth = max(bandwidth, 1e-12)
    z = (float(observation) - x) / bandwidth
    dens = float(np.mean(np.exp(-0.5 * z * z)) / (bandwidth * math.sqrt(2 * math.pi)))
    return float(-math.log(max(dens, 1e-300)))


def pit_values(draws_list: Sequence[Sequence[float]], observations: Sequence[float],
               rng_seed: int = 0) -> np.ndarray:
    """Randomized probability integral transform, one value per resolved forecast.

    Uniform PIT = calibrated. U-shaped = intervals too narrow (the usual finding).
    Hump-shaped = too wide. Sloped = biased.
    """
    rng = np.random.default_rng(rng_seed)
    out = np.empty(len(observations))
    for i, (d, y) in enumerate(zip(draws_list, observations)):
        x = np.asarray(d, dtype=float)
        below = float(np.mean(x < y))
        equal = float(np.mean(x == y))
        out[i] = below + rng.uniform() * equal
    return out


def interval_coverage(draws_list: Sequence[Sequence[float]], observations: Sequence[float],
                      level: float = 0.80) -> Dict[str, float]:
    """Empirical coverage of the central interval at ``level``. Should equal ``level``."""
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    hits, widths = [], []
    for d, y in zip(draws_list, observations):
        lo, hi = np.quantile(np.asarray(d, dtype=float), [lo_q, hi_q])
        hits.append(lo <= y <= hi)
        widths.append(hi - lo)
    return {
        "nominal": float(level),
        "empirical": float(np.mean(hits)),
        "n": len(hits),
        "mean_width": float(np.mean(widths)),
        "verdict": ("overconfident" if np.mean(hits) < level - 0.05
                    else "underconfident" if np.mean(hits) > level + 0.05 else "calibrated"),
    }


def pit_uniformity_chisq(pit: Sequence[float], n_bins: int = 10) -> Dict[str, float]:
    """Chi-square test of PIT uniformity. Large statistic relative to dof = miscalibrated."""
    u = np.asarray(pit, dtype=float)
    counts, _ = np.histogram(u, bins=n_bins, range=(0.0, 1.0))
    expected = u.size / n_bins
    stat = float(np.sum((counts - expected) ** 2) / expected) if expected > 0 else float("nan")
    dof = n_bins - 1
    return {
        "statistic": stat,
        "dof": dof,
        "ratio_to_dof": stat / dof if dof else float("nan"),
        "n": int(u.size),
        "note": "ratio_to_dof >> 1 indicates miscalibration; with n < 20 this test is weak",
    }


def skill_score(score_model: float, score_benchmark: float) -> float:
    """1 - model/benchmark. Positive = you beat the benchmark. Name the benchmark explicitly."""
    if score_benchmark == 0:
        return float("nan")
    return float(1.0 - score_model / score_benchmark)


def quantiles(draws: Sequence[float], qs: Sequence[float] = (0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95)
              ) -> Dict[str, float]:
    x = np.asarray(draws, dtype=float)
    return {f"p{q * 100:g}": float(v) for q, v in zip(qs, np.quantile(x, qs))}


def quantile_sum_error(draws_by_segment: Sequence[Sequence[float]], q: float = 0.9) -> Dict[str, float]:
    """Demonstrate that the P90 of a total is not the sum of segment P90s.

    Call this once on your own segments before anyone builds a spreadsheet that adds up
    P90 columns. The overstatement grows with the number of segments and shrinks with their
    correlation.
    """
    mats = [np.asarray(d, dtype=float) for d in draws_by_segment]
    n = min(m.size for m in mats)
    total = np.sum([m[:n] for m in mats], axis=0)
    correct = float(np.quantile(total, q))
    naive = float(sum(np.quantile(m, q) for m in mats))
    return {
        "correct_aggregate_quantile": correct,
        "naive_sum_of_quantiles": naive,
        "overstatement": naive - correct,
        "overstatement_pct": (naive - correct) / correct if correct else float("nan"),
    }


# ---------------------------------------------------------------------------
# 12. Sensitivity — the "three to five variables" section of the output contract
# ---------------------------------------------------------------------------


@dataclass
class LeverEffect:
    name: str
    low_value: float
    high_value: float
    low_output: float
    high_output: float
    base_output: float

    @property
    def swing(self) -> float:
        return abs(self.high_output - self.low_output)

    @property
    def swing_pct(self) -> float:
        return self.swing / abs(self.base_output) if self.base_output else float("nan")


def rank_levers(fn: Callable[[Mapping[str, float]], float], base: Mapping[str, float],
                ranges: Mapping[str, Tuple[float, float]]) -> List[LeverEffect]:
    """One-at-a-time tornado over plausible ranges, sorted by swing.

    Deliberately not a variance decomposition: the deliverable asks which *assumptions* a
    reader should argue with, and a one-at-a-time swing over an honest range answers that
    directly. Interactions belong in the Monte Carlo, not here.
    """
    base_out = float(fn(dict(base)))
    effects: List[LeverEffect] = []
    for name, (lo, hi) in ranges.items():
        if name not in base:
            raise KeyError(f"lever {name!r} is not in the base case")
        lo_in, hi_in = dict(base), dict(base)
        lo_in[name], hi_in[name] = lo, hi
        effects.append(LeverEffect(name, lo, hi, float(fn(lo_in)), float(fn(hi_in)), base_out))
    return sorted(effects, key=lambda e: e.swing, reverse=True)


# ---------------------------------------------------------------------------


def _api_summary() -> str:
    lines = [
        "dpforecast — probabilistic revenue forecasting for data-protection vendors",
        f"  numpy {np.__version__}; normal functions via {'scipy' if HAVE_SCIPY else 'builtin approximation'}",
        "",
        "Run the self-tests:   python3 test_dpforecast.py",
        "Run a worked example: python3 example_outside_in.py",
        "",
        "Public API:",
    ]
    for name in __all__:
        obj = globals()[name]
        doc = (obj.__doc__ or "").strip().splitlines()
        lines.append(f"  {name:36s} {doc[0] if doc else ''}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_api_summary())
