"""Self-tests for dpforecast. No test framework required: ``python3 test_dpforecast.py``.

Every numeric claim the engine makes is checked against either a closed form, an analytic
identity, or a recovery experiment on synthetic data with known parameters.
"""

from __future__ import annotations

import math
import sys
import traceback

import numpy as np

import dpforecast as dp

_FAILURES: list[str] = []


def check(name):
    def deco(fn):
        try:
            fn()
        except Exception:
            _FAILURES.append(name)
            print(f"FAIL  {name}")
            traceback.print_exc()
        else:
            print(f"ok    {name}")
        return fn
    return deco


def close(a, b, rel=1e-9, abs_=1e-9):
    assert abs(a - b) <= max(abs_, rel * abs(b)), f"{a!r} != {b!r}"


# ---------------------------------------------------------------------------
# 1. Measure-type safety
# ---------------------------------------------------------------------------


@check("Quantity refuses to mix measure types")
def _():
    acv = dp.Quantity(100.0, "acv", "FY27")
    tcv = dp.Quantity(300.0, "tcv", "FY27")
    assert (acv + dp.Quantity(50.0, "acv", "FY27")).value == 150.0
    try:
        acv + tcv
    except dp.MeasureError:
        pass
    else:
        raise AssertionError("expected MeasureError adding acv to tcv")
    try:
        acv + dp.Quantity(1.0, "acv", "FY28")
    except dp.MeasureError:
        pass
    else:
        raise AssertionError("expected MeasureError adding across periods")
    try:
        dp.Quantity(1.0, "widgets")
    except dp.MeasureError:
        pass
    else:
        raise AssertionError("expected MeasureError for unknown measure")


@check("term-mix shift triples TCV with ARR unchanged")
def _():
    acv = 100.0
    close(dp.tcv_from_acv(acv, 1), 100.0)
    close(dp.tcv_from_acv(acv, 3), 300.0)
    close(dp.acv_from_tcv(300.0, 3), 100.0)


@check("explicit conversion is the only way across measures")
def _():
    acv = dp.Quantity(100.0, "acv", "FY27")
    tcv = acv.as_measure("tcv", factor=3.0)
    close(tcv.value, 300.0)
    assert tcv.measure == "tcv"


# ---------------------------------------------------------------------------
# 0/2. Numerics and distributions
# ---------------------------------------------------------------------------


@check("norm_ppf / norm_cdf round trip")
def _():
    p = np.array([0.001, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 0.999])
    back = dp.norm_cdf(dp.norm_ppf(p))
    assert np.max(np.abs(back - p)) < 1e-7, np.max(np.abs(back - p))
    close(float(dp.norm_ppf(0.975)), 1.959963985, rel=1e-6)
    close(float(dp.norm_cdf(0.0)), 0.5, rel=1e-12)


@check("distributions sample with the right means")
def _():
    rng = np.random.default_rng(1)
    close(float(dp.Point(3.0).sample(rng, 10).mean()), 3.0)
    ln = dp.LogNormal(median=0.95, sigma=0.25)
    close(float(ln.sample(rng, 400000).mean()), ln.mean, rel=0.01)
    b = dp.Beta(mean_=0.9, sd=0.03)
    s = b.sample(rng, 200000)
    close(float(s.mean()), 0.9, rel=0.01)
    close(float(s.std()), 0.03, rel=0.05)
    assert isinstance(dp.as_dist(0.5), dp.Point)
    assert isinstance(dp.as_dist((0.5, 0.1)), dp.Normal)


# ---------------------------------------------------------------------------
# 3. Baseline
# ---------------------------------------------------------------------------


@check("fit_ar1 recovers known alpha/beta/sigma")
def _():
    rng = np.random.default_rng(7)
    alpha, beta, sigma = 0.02, 0.75, 0.005
    g = [0.10]
    for _ in range(400):
        g.append(alpha + beta * g[-1] + rng.normal(0, sigma))
    fit = dp.fit_ar1(g)
    close(fit.beta, beta, abs_=0.06)
    close(fit.alpha, alpha, abs_=0.006)
    close(fit.sigma, sigma, rel=0.12)
    close(fit.long_run_mean, alpha / (1 - beta), abs_=0.02)
    assert 0 < fit.r2 < 1


@check("AR(1) shrinkage pulls beta toward the peer prior")
def _():
    g = [0.10, 0.12, 0.09, 0.11, 0.08, 0.10, 0.07, 0.09]
    own = dp.fit_ar1(g)
    shrunk = dp.fit_ar1(g, shrink_beta_to=0.8, shrink_weight=1.0)
    close(shrunk.beta, 0.8)
    half = dp.fit_ar1(g, shrink_beta_to=0.8, shrink_weight=0.5)
    close(half.beta, 0.5 * own.beta + 0.5 * 0.8, rel=1e-9)


@check("ar1_paths mean converges to the deterministic recursion")
def _():
    fit = dp.AR1Fit(alpha=0.02, beta=0.75, sigma=0.01, n=40, r2=0.5)
    paths = dp.ar1_paths(fit, g_last=0.10, horizon=4, n_sims=60000, seed=3)
    det = fit.forecast(0.10, 4)
    assert np.max(np.abs(paths.mean(axis=0) - det)) < 0.001


@check("visibility ratio")
def _():
    close(dp.visibility_ratio(830.0, 1000.0), 0.83)


# ---------------------------------------------------------------------------
# 4. Order flow
# ---------------------------------------------------------------------------


def _deals(n=200, seed=11, p=0.30, amt=100000.0, r_sigma=0.0, r_med=1.0):
    rng = np.random.default_rng(seed)
    return [
        dp.Deal(f"D{i}", amount=float(amt * math.exp(0.6 * rng.standard_normal())),
                p_win=p, realization_median=r_med, realization_sigma=r_sigma)
        for i in range(n)
    ]


@check("deal-list mean equals sum of amount x probability x E[realization]")
def _():
    deals = _deals(r_sigma=0.0, r_med=1.0)
    res = dp.simulate_deal_list(deals, rho=0.0, n_sims=40000, seed=5)
    expected = sum(d.amount * d.p_win for d in deals)
    close(float(res.draws.mean()), expected, rel=0.02)


@check("realization multiplier shifts the mean by its lognormal mean")
def _():
    deals = _deals(r_sigma=0.25, r_med=0.95)
    res = dp.simulate_deal_list(deals, rho=0.0, n_sims=40000, seed=5)
    mult_mean = 0.95 * math.exp(0.5 * 0.25 ** 2)
    expected = sum(d.amount * d.p_win for d in deals) * mult_mean
    close(float(res.draws.mean()), expected, rel=0.02)


@check("independent Bernoulli sd matches the analytic sd at rho=0")
def _():
    deals = _deals(r_sigma=0.0, r_med=1.0)
    res = dp.simulate_deal_list(deals, rho=0.0, n_sims=60000, seed=9)
    close(float(res.modeled_draws.std(ddof=1)), res.expected_independent_sd, rel=0.03)


@check("correlation widens the bookings distribution, monotonically in rho")
def _():
    deals = _deals(r_sigma=0.0, r_med=1.0)
    sds = [dp.simulate_deal_list(deals, rho=r, n_sims=40000, seed=2).modeled_draws.std(ddof=1)
           for r in (0.0, 0.05, 0.20, 0.50)]
    assert all(b > a for a, b in zip(sds, sds[1:])), sds
    assert sds[2] > 2 * sds[0], sds


@check("latent copula rho is not the indicator correlation")
def _():
    # At p = 0.30 a latent rho of 0.20 is an indicator correlation of 0.119 (verified against
    # a 4M-draw Monte Carlo, which gives 0.1185).
    ri = dp.indicator_correlation(0.30, 0.30, 0.20)
    close(ri, 0.11879, rel=1e-4)
    assert ri < 0.20
    close(dp.indicator_correlation(0.30, 0.30, 0.0), 0.0, abs_=1e-12)
    # Round trip through the inverse.
    close(dp.latent_rho_from_indicator(0.30, ri), 0.20, abs_=1e-6)
    # Bivariate normal CDF sanity: Phi2(0,0;rho) = 1/4 + arcsin(rho)/(2*pi).
    for r in (-0.7, -0.2, 0.0, 0.3, 0.9):
        close(dp.bvn_cdf(0.0, 0.0, r), 0.25 + math.asin(r) / (2 * math.pi), abs_=1e-10)
    close(dp.bvn_cdf(1.0, 1.0, 0.0), float(dp.norm_cdf(1.0)) ** 2, abs_=1e-12)


@check("sd inflation from correlation grows with pipeline size and matches the analytic form")
def _():
    # The idiosyncratic term diversifies across deals; the common factor does not. So the
    # same rho matters more on a bigger pipeline, contrary to the usual intuition.
    rho_latent = 0.20
    rho_ind = dp.indicator_correlation(0.30, 0.30, rho_latent)
    for n in (30, 100, 200):
        deals = _deals(n=n, seed=11, r_sigma=0.0, r_med=1.0)
        s0 = dp.simulate_deal_list(deals, rho=0.0, n_sims=40000, seed=2).modeled_draws.std(ddof=1)
        sr = dp.simulate_deal_list(deals, rho=rho_latent, n_sims=40000, seed=2).modeled_draws.std(ddof=1)
        predicted = dp.exchangeable_sd_inflation(n, rho_ind)
        # Amounts are lognormal rather than equal, so allow a wide-ish band on the analytic
        # equal-amount approximation; the point is the sqrt(1 + (n-1)*rho) scaling.
        assert 0.8 * predicted < sr / s0 < 1.25 * predicted, (n, sr / s0, predicted)
    close(dp.exchangeable_sd_inflation(1, 0.5), 1.0)
    assert dp.exchangeable_sd_inflation(200, rho_ind) > 2 * dp.exchangeable_sd_inflation(30, rho_ind)


@check("effective deal count explains the worked example's sd inflation")
def _():
    # The 68-deal example in references/with-order-flow.md: 8 x $1.2M plus 60 x $120K.
    amounts = np.concatenate([np.full(8, 1_200_000.0), np.full(60, 120_000.0)])
    n_eff = dp.effective_deal_count(amounts)
    close(n_eff, 22.79, rel=1e-3)
    assert n_eff < 68 / 2, n_eff
    close(dp.effective_deal_count(np.full(50, 7.0)), 50.0, rel=1e-12)  # equal amounts -> n

    p_eff = np.concatenate([np.full(8, 0.45 * 0.70), np.full(60, 0.60 * 0.85)])
    deals = [dp.Deal(f"d{i}", float(a), float(p), realization_median=0.95, realization_sigma=0.25)
             for i, (a, p) in enumerate(zip(amounts, p_eff))]
    sd0 = dp.simulate_deal_list(deals, rho=0.0, n_sims=20000, seed=7,
                                tail_median=2_600_000, tail_sigma=0.30).draws.std(ddof=1)
    sd2 = dp.simulate_deal_list(deals, rho=0.20, n_sims=20000, seed=7,
                                tail_median=2_600_000, tail_sigma=0.30).draws.std(ddof=1)
    observed = sd2 / sd0
    # Documented as 1.88 -> 3.30, i.e. ~1.76x.
    close(observed, 1.76, rel=0.06)
    # Using the raw count would predict ~3.0x; the effective count gets far closer.
    rho_ind = dp.indicator_correlation(0.315, 0.315, 0.20)
    naive = dp.exchangeable_sd_inflation(68, rho_ind)
    adjusted = dp.exchangeable_sd_inflation(n_eff, rho_ind)
    assert abs(adjusted - observed) < abs(naive - observed), (naive, adjusted, observed)


@check("the unmodeled tail adds its lognormal mean, not its median")
def _():
    deals = _deals(r_sigma=0.0, r_med=1.0)
    base = dp.simulate_deal_list(deals, rho=0.0, n_sims=60000, seed=4)
    with_tail = dp.simulate_deal_list(deals, rho=0.0, n_sims=60000, seed=4,
                                      tail_median=2_600_000, tail_sigma=0.30)
    added = float(with_tail.draws.mean() - base.draws.mean())
    close(added, 2_600_000 * math.exp(0.5 * 0.30 ** 2), rel=0.02)


@check("fit_rho_to_target_sd recovers the rho that generated the data")
def _():
    deals = _deals(n=150, r_sigma=0.0, r_med=1.0)
    true_rho = 0.25
    target = float(dp.simulate_deal_list(deals, rho=true_rho, n_sims=30000, seed=21)
                   .modeled_draws.std(ddof=1))
    fitted = dp.fit_rho_to_target_sd(deals, target_sd=target, n_sims=12000, seed=21)
    close(fitted, true_rho, abs_=0.06)


@check("category forecast applies fitted realization rates")
def _():
    dollars = {"commit": 40e6, "best_case": 30e6, "pipeline": 60e6}
    rates = {"commit": (0.93, 0.05), "best_case": (0.55, 0.12), "pipeline": (0.18, 0.08)}
    draws = dp.category_forecast(dollars, rates, n_sims=60000, seed=6, rho=0.3)
    expected = sum(dollars[c] * rates[c][0] for c in dollars)
    close(float(draws.mean()), expected, rel=0.01)
    # Correlated categories -> wider than the independent case.
    indep = dp.category_forecast(dollars, rates, n_sims=60000, seed=6, rho=0.0)
    assert draws.std() > indep.std()


@check("pace nowcast un-does a backloaded quarter")
def _():
    days = 90
    curve = np.concatenate([np.linspace(0, 0.35, 80, endpoint=False), np.linspace(0.35, 1.0, 11)])
    draws = dp.pace_nowcast(day_index=60, days_in_quarter=days, booked_to_date=30e6,
                            pace_curve=curve, residual_sd_frac=0.12, n_sims=40000, seed=8)
    naive_linear = 30e6 * days / 60
    point = 30e6 / float(curve[60])
    close(float(np.median(draws)), point, rel=0.02)
    assert point > naive_linear, "backloaded curve must imply more than the linear run-rate"


# ---------------------------------------------------------------------------
# 5. Calibration of inputs
# ---------------------------------------------------------------------------


@check("Platt scaling fixes systematically optimistic CRM probabilities")
def _():
    rng = np.random.default_rng(31)
    n = 4000
    raw = rng.uniform(0.05, 0.95, n)          # what the CRM asserts
    true = raw * 0.55                          # reality: reps are optimistic by ~45%
    won = (rng.uniform(size=n) < true).astype(int)
    a, b = dp.platt_fit(raw, won)
    cal = dp.platt_apply(raw, a, b)
    err_raw = float(np.mean(np.abs(raw - true)))
    err_cal = float(np.mean(np.abs(cal - true)))
    assert err_cal < 0.25 * err_raw, (err_raw, err_cal)
    close(float(cal.mean()), float(won.mean()), abs_=0.02)


@check("isotonic regression is monotone and tracks the truth")
def _():
    rng = np.random.default_rng(32)
    n = 6000
    raw = rng.uniform(0.02, 0.98, n)
    true = np.clip(raw ** 1.8, 0, 1)
    won = (rng.uniform(size=n) < true).astype(float)
    xk, yf = dp.isotonic_fit(raw, won)
    assert np.all(np.diff(yf) >= -1e-12), "isotonic output must be non-decreasing"
    pred = dp.isotonic_apply(xk, yf, np.array([0.1, 0.3, 0.5, 0.7, 0.9]))
    truth = np.array([0.1, 0.3, 0.5, 0.7, 0.9]) ** 1.8
    assert np.max(np.abs(pred - truth)) < 0.06, np.max(np.abs(pred - truth))


@check("empirical-Bayes shrinks a 3-of-4 rep toward the prior")
def _():
    successes = [3, 30, 55, 2, 120]
    trials = [4, 100, 200, 3, 400]
    out = dp.shrink_binomial(successes, trials)
    prior = float(out["prior_mean"])
    raw, shr = out["raw"], out["shrunk"]
    # Small-n reps move a lot; large-n reps barely move.
    assert abs(shr[0] - prior) < abs(raw[0] - prior)
    assert out["shrinkage_weight"][0] > out["shrinkage_weight"][4]
    assert all(min(r, prior) - 1e-9 <= s <= max(r, prior) + 1e-9 for r, s in zip(raw, shr))


@check("normal shrinkage pulls noisy estimates toward the grand mean")
def _():
    out = dp.shrink_normal([0.60, 0.95, 0.90, 1.30], [0.20, 0.03, 0.03, 0.25])
    grand = float(out["prior_mean"])
    assert abs(out["shrunk"][0] - grand) < abs(out["raw"][0] - grand)
    assert out["weight"][1] > out["weight"][0], "precise estimates shrink less"


# ---------------------------------------------------------------------------
# 6. ARR waterfall
# ---------------------------------------------------------------------------


@check("deterministic waterfall reproduces annual GRR and NRR exactly")
def _():
    spec = dp.WaterfallSpec(opening_arr=1000.0, grr=dp.Point(0.90),
                            expansion=dp.Point(0.10), new_logo_arr=dp.Point(0.0),
                            periods_per_year=4)
    res = dp.simulate_arr_waterfall(spec, n_periods=4, n_sims=64, seed=0)
    close(float(res.closing.mean()), 1000.0 * 0.90 * 1.10, rel=1e-9)


@check("waterfall bridge adds up: opening - churn + expansion + new = closing")
def _():
    spec = dp.WaterfallSpec(opening_arr=1121.6, grr=dp.Beta(0.91, 0.015),
                            expansion=dp.Normal(0.28, 0.04),
                            new_logo_arr=dp.LogNormal(30.0, 0.30), periods_per_year=4, rho=0.35)
    res = dp.simulate_arr_waterfall(spec, n_periods=4, n_sims=20000, seed=17)
    b = res.mean_bridge()
    close(b["opening_arr"] + b["churn"] + b["expansion"] + b["new_logo"], b["closing_arr"], rel=1e-9)
    assert b["closing_arr"] > b["opening_arr"]
    assert res.closing.std() > 0


@check("waterfall period correlation widens the annual outcome")
def _():
    kw = dict(opening_arr=1000.0, grr=dp.Beta(0.90, 0.02), expansion=dp.Normal(0.20, 0.05),
              new_logo_arr=dp.LogNormal(25.0, 0.35), periods_per_year=4)
    lo = dp.simulate_arr_waterfall(dp.WaterfallSpec(rho=0.0, **kw), 4, 20000, seed=5).closing
    hi = dp.simulate_arr_waterfall(dp.WaterfallSpec(rho=0.7, **kw), 4, 20000, seed=5).closing
    assert hi.std() > lo.std() * 1.1, (lo.std(), hi.std())


@check("GRR below 1 with zero new logos decays the base at the stated half-life")
def _():
    grr = 0.90
    spec = dp.WaterfallSpec(1000.0, dp.Point(grr), dp.Point(0.0), dp.Point(0.0), periods_per_year=1)
    hl = dp.arr_half_life(grr)
    assert 6.0 < hl < 7.0, hl
    below = dp.simulate_arr_waterfall(spec, n_periods=6, n_sims=8, seed=0).closing.mean() / 1000.0
    above = dp.simulate_arr_waterfall(spec, n_periods=7, n_sims=8, seed=0).closing.mean() / 1000.0
    assert above < 0.5 < below, (below, above)
    close(float(below), grr ** 6, rel=1e-9)
    close(float(above), grr ** 7, rel=1e-9)


# ---------------------------------------------------------------------------
# 7. ASC 606 recognition
# ---------------------------------------------------------------------------


@check("SaaS contract is fully ratable; prepaid billing creates deferred revenue")
def _():
    c = dp.Contract("A", start_month=0, term_months=36, acv=120.0, kind="saas", billing="prepaid")
    s = dp.recognize_contracts([c], n_months=36)
    close(float(s.revenue[0]), 10.0)
    close(float(s.revenue.sum()), 360.0, rel=1e-9)
    close(float(s.billings[0]), 360.0)
    close(float(s.billings.sum()), 360.0)
    close(float(s.deferred_revenue[0]), 350.0)
    close(float(s.deferred_revenue[-1]), 0.0, abs_=1e-9)
    close(float(s.rpo[0]), 350.0)
    close(float(s.crpo[0]), 120.0, rel=1e-9)


@check("term license splits point-in-time license from ratable support")
def _():
    c = dp.Contract("B", start_month=0, term_months=36, acv=120.0, kind="term_license",
                    license_share=0.60, billing="annual")
    s = dp.recognize_contracts([c], n_months=36)
    tcv = 360.0
    close(float(s.revenue[0]), 0.60 * tcv + 0.40 * tcv / 36)
    close(float(s.revenue[1]), 0.40 * tcv / 36)
    close(float(s.revenue.sum()), tcv, rel=1e-9)
    close(float(s.billings[0]), 120.0)
    close(float(s.billings[12]), 120.0)
    close(float(s.billings.sum()), 360.0, rel=1e-9)
    # Upfront license against annual billing creates a contract asset in month 0.
    assert s.contract_assets[0] > 0
    close(float(s.contract_assets[0]), 0.60 * tcv + 0.40 * tcv / 36 - 120.0)


@check("identical ARR, different recognition: SaaS vs term license diverge, ARR does not")
def _():
    saas = dp.Contract("S", 0, 36, 120.0, kind="saas", billing="annual")
    term = dp.Contract("T", 0, 36, 120.0, kind="term_license", license_share=0.60, billing="annual")
    a = dp.recognize_contracts([saas], 12)
    b = dp.recognize_contracts([term], 12)
    close(float(a.revenue.sum()), 120.0, rel=1e-9)
    close(float(b.revenue.sum()), 0.60 * 360 + 0.40 * 360 / 3, rel=1e-9)
    close(float(b.revenue.sum()) / float(a.revenue.sum()), 2.2, rel=1e-9)
    close(saas.acv, term.acv)  # identical ARR contribution


@check("cancellable arrangements are excluded from RPO")
def _():
    firm = dp.Contract("F", 0, 12, 120.0, kind="saas")
    canc = dp.Contract("C", 0, 12, 120.0, kind="saas", cancellable=True)
    s = dp.recognize_contracts([firm, canc], 12)
    close(float(s.rpo[0]), 110.0)          # only the firm contract
    close(float(s.revenue[0]), 20.0)       # but both recognize revenue


@check("perpetual is point-in-time; services amortize over delivery")
def _():
    p = dp.Contract("P", 2, 12, 100.0, kind="perpetual", billing="prepaid")
    sv = dp.Contract("V", 0, 12, 60.0, kind="services", delivery_months=3, billing="prepaid")
    s = dp.recognize_contracts([p, sv], 12)
    close(float(s.revenue_by_kind["perpetual"][2]), 100.0)
    close(float(s.revenue_by_kind["perpetual"].sum()), 100.0)
    close(float(s.revenue_by_kind["services"][0]), 20.0)
    close(float(s.revenue_by_kind["services"][3]), 0.0, abs_=1e-12)


@check("billing schedules move cash, not revenue")
def _():
    rev = []
    cash_m0 = []
    for billing in ("prepaid", "annual", "quarterly", "monthly"):
        c = dp.Contract("X", 0, 36, 120.0, kind="saas", billing=billing)
        s = dp.recognize_contracts([c], 36)
        rev.append(float(s.revenue.sum()))
        cash_m0.append(float(s.billings[0]))
    assert max(rev) - min(rev) < 1e-9, rev
    assert cash_m0 == sorted(cash_m0, reverse=True), cash_m0


@check("quarterly roll-up preserves flows and takes period-end stocks")
def _():
    c = dp.Contract("Q", 0, 24, 120.0, kind="saas", billing="prepaid")
    m = dp.recognize_contracts([c], 24)
    q = m.to_periods(3)
    assert q.n_months == 8
    close(float(q.revenue.sum()), float(m.revenue.sum()), rel=1e-12)
    close(float(q.revenue[0]), float(m.revenue[:3].sum()), rel=1e-12)
    close(float(q.deferred_revenue[0]), float(m.deferred_revenue[2]), rel=1e-12)


# ---------------------------------------------------------------------------
# 8. Reconciliation
# ---------------------------------------------------------------------------


@check("revenue identity closes on a schedule produced by the engine")
def _():
    cs = [
        dp.Contract("1", 0, 36, 500.0, kind="saas", billing="prepaid"),
        dp.Contract("2", 3, 12, 300.0, kind="term_license", license_share=0.5, billing="annual"),
        dp.Contract("3", 6, 24, 200.0, kind="support", billing="quarterly"),
    ]
    s = dp.recognize_contracts(cs, 36)
    q = s.to_periods(3)
    for t in range(1, q.n_months):
        r = dp.revenue_identity_residual(
            billings=float(q.billings[t]),
            delta_deferred_revenue=float(q.deferred_revenue[t] - q.deferred_revenue[t - 1]),
            delta_contract_assets=float(q.contract_assets[t] - q.contract_assets[t - 1]),
            revenue=float(q.revenue[t]),
        )
        assert abs(r["residual"]) < 1e-8, (t, r)


@check("RPO roll-forward closes and flags a 3% break")
def _():
    ok = dp.rpo_rollforward_residual(opening_rpo=2000.0, bookings_tcv=600.0,
                                     revenue=400.0, closing_rpo=2200.0)
    close(ok["residual"], 0.0, abs_=1e-9)
    assert ok["passes_3pct_check"]
    bad = dp.rpo_rollforward_residual(2000.0, 600.0, 400.0, closing_rpo=2400.0)
    assert not bad["passes_3pct_check"]
    close(bad["residual"], 200.0)


@check("the two-term identity is wrong when contract assets move")
def _():
    r = dp.revenue_identity_residual(billings=100.0, delta_deferred_revenue=-10.0,
                                     delta_contract_assets=15.0, revenue=125.0)
    close(r["residual"], 0.0, abs_=1e-9)
    naive = 100.0 - (-10.0)
    assert abs(125.0 - naive) == 15.0


# ---------------------------------------------------------------------------
# 9. P&L and cash
# ---------------------------------------------------------------------------


@check("stream-level P&L differs from a blended margin under a mix shift")
def _():
    gm = {"term": 0.976, "saas": 0.645, "perpetual": 0.988, "support": 0.816, "ps": 0.329}
    opex = {"sm": 519.0, "rd": 162.0, "ga": 162.0}
    base_rev = {"term": 435.0, "saas": 332.0, "perpetual": 44.0, "support": 320.0, "ps": 52.0}
    base = dp.pnl_by_stream(base_rev, gm, opex)
    close(base["revenue"], sum(base_rev.values()), rel=1e-12)
    close(base["gross_profit"], sum(base_rev[k] * gm[k] for k in base_rev), rel=1e-12)
    close(base["operating_income"], base["gross_profit"] - sum(opex.values()), rel=1e-12)
    assert 0.80 < base["gross_margin"] < 0.84, base["gross_margin"]

    # Shift 10 points of revenue mix from term license to SaaS: revenue flat, margin down.
    shift = base["revenue"] * 0.10
    mix_rev = dict(base_rev, term=base_rev["term"] - shift, saas=base_rev["saas"] + shift)
    mixed = dp.pnl_by_stream(mix_rev, gm, opex)
    close(mixed["revenue"], base["revenue"], rel=1e-12)
    drop_pts = (base["gross_margin"] - mixed["gross_margin"]) * 100
    close(drop_pts, 3.31, abs_=0.05)

    try:
        dp.pnl_by_stream({"new_stream": 10.0}, gm, opex)
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError for a stream with no gross margin")


@check("FCF bridge: deferred revenue dominates and SBC is not free")
def _():
    out = dp.fcf_bridge(operating_income=75.0, depreciation_amortization=8.0,
                        stock_based_comp=118.0, delta_deferred_revenue=136.4,
                        delta_receivables=20.0, delta_deferred_commissions=12.0,
                        cash_taxes=25.0, capex=7.0, buyback_to_offset_dilution=118.0)
    close(out["operating_cash_flow"], 75 + 8 + 118 + 136.4 - 20 - 12 - 25)
    close(out["free_cash_flow"], out["operating_cash_flow"] - 7.0)
    close(out["fcf_after_dilution_offset"], out["free_cash_flow"] - 118.0)
    assert out["fcf_after_dilution_offset"] < out["free_cash_flow"]


# ---------------------------------------------------------------------------
# 10. Closed-form levers
# ---------------------------------------------------------------------------


@check("price lever flows ~100% to gross profit absent volume loss")
def _():
    out = dp.price_lever(revenue=1183.0, price_pts=1.0, gross_margin=0.812, operating_margin=0.063)
    close(out["revenue_pct"], 0.01, rel=1e-12)
    close(out["gross_profit_delta"], 11.83, rel=1e-9)
    # +1% price on a 6.3% operating margin is ~15.9% of operating profit.
    close(out["gross_profit_delta"] / (1183.0 * 0.063), 0.1587, rel=0.01)
    close(out["breakeven_volume_loss_pct_per_pt_price"], 1 / 0.812, rel=1e-12)


@check("price lever with elasticity can be value-destroying")
def _():
    good = dp.price_lever(1000.0, 1.0, 0.81, 0.10, volume_elasticity=-0.5)
    bad = dp.price_lever(1000.0, 1.0, 0.81, 0.10, volume_elasticity=-3.0)
    assert good["gross_profit_delta"] > 0
    assert bad["gross_profit_delta"] < 0, bad
    # Breakeven elasticity is -1/gross_margin.
    at_be = dp.price_lever(1000.0, 1.0, 0.81, 0.10, volume_elasticity=-1 / 0.81)
    close(at_be["gross_profit_delta"], 0.0, abs_=0.2)


@check("1 point off a 30% discount is +1.43% net price")
def _():
    out = dp.discount_lever(base_discount=0.30, pts_recovered=1.0)
    close(out["net_price_pct"], 0.0142857, rel=1e-5)
    close(out["new_discount"], 0.29, rel=1e-12)


@check("prepaid is a one-time cash lever with exactly zero revenue effect")
def _():
    out = dp.prepaid_cash_lever(arr_moved=120e6, extra_years_prepaid=2.0)
    close(out["one_time_cash"], 240e6)
    close(out["revenue_effect"], 0.0)
    assert out["recurring"] is False


@check("opex growth gap gives ~0.6 pt of margin per point of gap")
def _():
    out = dp.operating_margin_from_growth_gap(revenue_growth=0.20, opex_growth=0.19,
                                              opex_ratio=0.72, gross_margin=0.81)
    close(out["gap_pts"], 1.0, rel=1e-9)
    close(out["pts_per_gap_pt"], 0.60, abs_=0.01)
    ten = dp.operating_margin_from_growth_gap(0.20, 0.10, 0.72, 0.81)
    close(ten["gap_pts"], 10.0, rel=1e-9)
    assert 5.5 < ten["operating_margin_delta_pts"] < 6.5, ten


@check("magic number, CAC payback, half-life, steady state, coverage")
def _():
    close(dp.magic_number(net_new_arr=100.0, prior_period_sm_expense=200.0), 0.5)
    close(dp.magic_number(100.0, 200.0, gross_margin=0.80), 0.40)
    close(dp.cac_payback_months(sm_expense=200.0, net_new_arr=100.0, gross_margin=0.80), 30.0)
    assert dp.cac_payback_months(200.0, 0.0, 0.8) == float("inf")
    close(dp.arr_half_life(0.90), 6.579, rel=1e-3)
    close(dp.steady_state_arr(100.0, 0.90), 1000.0)
    assert dp.steady_state_arr(100.0, 1.05) == float("inf")
    close(dp.required_pipeline_coverage(0.19), 5.263, rel=1e-3)


# ---------------------------------------------------------------------------
# 11. Scoring and calibration
# ---------------------------------------------------------------------------


@check("ensemble CRPS matches the closed-form normal CRPS")
def _():
    rng = np.random.default_rng(41)
    mu, sigma = 100.0, 12.0
    draws = rng.normal(mu, sigma, 200000)
    for y in (85.0, 100.0, 118.0):
        close(dp.crps_ensemble(draws, y), dp.crps_normal(mu, sigma, y), rel=0.01)


@check("CRPS of a deterministic forecast equals absolute error")
def _():
    close(dp.crps_ensemble(np.full(500, 100.0), 112.0), 12.0, rel=1e-12)


@check("a sharper, correct forecast scores better than a vague one")
def _():
    rng = np.random.default_rng(42)
    sharp = rng.normal(100.0, 5.0, 100000)
    vague = rng.normal(100.0, 30.0, 100000)
    biased = rng.normal(120.0, 5.0, 100000)
    y = 101.0
    assert dp.crps_ensemble(sharp, y) < dp.crps_ensemble(vague, y)
    assert dp.crps_ensemble(sharp, y) < dp.crps_ensemble(biased, y)


@check("pinball loss at the median is half the absolute error")
def _():
    out = dp.pinball_loss({0.5: 100.0}, 110.0)
    close(out["per_tau"][0.5], 5.0)
    hi = dp.pinball_loss({0.9: 100.0}, 110.0)
    close(hi["per_tau"][0.9], 9.0)  # under-forecasting is expensive at tau = 0.9
    lo = dp.pinball_loss({0.9: 120.0}, 110.0)
    close(lo["per_tau"][0.9], 1.0)


@check("Brier decomposition: BS = reliability - resolution + uncertainty")
def _():
    rng = np.random.default_rng(43)
    grid = np.arange(0.05, 1.0, 0.1)
    p = rng.choice(grid, 20000)
    o = (rng.uniform(size=p.size) < p).astype(int)
    out = dp.brier_score(p, o)
    close(out["brier"], out["reliability"] - out["resolution"] + out["uncertainty"], abs_=1e-9)
    assert out["reliability"] < 0.002, out          # well-calibrated by construction
    assert out["skill_vs_base_rate"] > 0.3, out


@check("PIT is uniform for a well-specified forecast and U-shaped when overconfident")
def _():
    rng = np.random.default_rng(44)
    n = 400
    truth = rng.normal(100.0, 10.0, n)
    good = [rng.normal(100.0, 10.0, 3000) for _ in range(n)]
    tight = [rng.normal(100.0, 3.0, 3000) for _ in range(n)]
    pit_good = dp.pit_values(good, truth)
    pit_tight = dp.pit_values(tight, truth)
    chi_good = dp.pit_uniformity_chisq(pit_good)
    chi_tight = dp.pit_uniformity_chisq(pit_tight)
    assert chi_good["ratio_to_dof"] < 3.0, chi_good
    assert chi_tight["ratio_to_dof"] > 10.0, chi_tight
    # U-shape: the extreme bins are overloaded.
    edges = float(np.mean((pit_tight < 0.1) | (pit_tight > 0.9)))
    assert edges > 0.5, edges


@check("interval coverage detects overconfidence")
def _():
    rng = np.random.default_rng(45)
    n = 300
    truth = rng.normal(100.0, 10.0, n)
    good = [rng.normal(100.0, 10.0, 4000) for _ in range(n)]
    tight = [rng.normal(100.0, 4.0, 4000) for _ in range(n)]
    cg = dp.interval_coverage(good, truth, 0.80)
    ct = dp.interval_coverage(tight, truth, 0.80)
    assert cg["verdict"] == "calibrated", cg
    assert ct["verdict"] == "overconfident", ct
    assert ct["mean_width"] < cg["mean_width"]


@check("skill score is positive only when you beat the benchmark")
def _():
    close(dp.skill_score(8.0, 10.0), 0.2)
    assert dp.skill_score(12.0, 10.0) < 0


@check("P90 of a total is not the sum of segment P90s")
def _():
    rng = np.random.default_rng(46)
    segs = [rng.normal(100.0, 20.0, 60000) for _ in range(5)]
    out = dp.quantile_sum_error(segs, 0.9)
    assert out["overstatement"] > 0
    # Naive sum: 5*(mu + z*sd). Correct: 5*mu + z*sd*sqrt(5). Gap = (5 - sqrt(5))*z*sd.
    expected = (5 - math.sqrt(5)) * 1.2816 * 20.0
    close(out["overstatement"], expected, rel=0.05)
    close(out["correct_aggregate_quantile"], 500 + 1.2816 * 20 * math.sqrt(5), rel=0.01)


@check("quantiles helper labels the levels it returns")
def _():
    q = dp.quantiles(np.arange(0, 1001, dtype=float), (0.1, 0.5, 0.9))
    close(q["p10"], 100.0, rel=1e-9)
    close(q["p50"], 500.0, rel=1e-9)
    close(q["p90"], 900.0, rel=1e-9)


# ---------------------------------------------------------------------------
# 12. Sensitivity
# ---------------------------------------------------------------------------


@check("rank_levers orders by swing and reports the base case")
def _():
    def model(p):
        return p["arr"] * p["nrr"] + p["new_logo"] - p["cost"]

    base = {"arr": 1000.0, "nrr": 1.10, "new_logo": 50.0, "cost": 200.0}
    ranked = dp.rank_levers(model, base, {
        "nrr": (1.05, 1.15),
        "new_logo": (30.0, 70.0),
        "cost": (180.0, 220.0),
    })
    assert [e.name for e in ranked] == ["nrr", "new_logo", "cost"], [e.name for e in ranked]
    close(ranked[0].swing, 100.0, rel=1e-9)
    close(ranked[0].base_output, 950.0, rel=1e-9)
    assert ranked[0].swing_pct > ranked[-1].swing_pct
    try:
        dp.rank_levers(model, base, {"nope": (0, 1)})
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError for an unknown lever")


# ---------------------------------------------------------------------------
# End-to-end sanity: the whole chain runs and reconciles
# ---------------------------------------------------------------------------


@check("end to end: waterfall -> contracts -> 606 -> reconciliation -> P&L -> score")
def _():
    spec = dp.WaterfallSpec(opening_arr=1121.6, grr=dp.Beta(0.91, 0.015),
                            expansion=dp.Normal(0.26, 0.05),
                            new_logo_arr=dp.LogNormal(28.0, 0.30), periods_per_year=4, rho=0.35)
    wf = dp.simulate_arr_waterfall(spec, 4, n_sims=5000, seed=99)
    added = float((wf.expansion.sum(axis=1) + wf.new_logo.sum(axis=1)).mean())

    contracts = [dp.Contract(f"n{i}", start_month=i * 3, term_months=36, acv=added / 4,
                             kind="saas", billing="annual") for i in range(4)]
    sch = dp.recognize_contracts(contracts, 12).to_periods(3)
    for t in range(1, sch.n_months):
        r = dp.revenue_identity_residual(
            float(sch.billings[t]),
            float(sch.deferred_revenue[t] - sch.deferred_revenue[t - 1]),
            float(sch.contract_assets[t] - sch.contract_assets[t - 1]),
            float(sch.revenue[t]))
        assert abs(r["residual"]) < 1e-8

    pnl = dp.pnl_by_stream({"saas": float(sch.revenue.sum())}, {"saas": 0.645},
                           {"sm": 100.0, "rd": 30.0, "ga": 30.0})
    assert pnl["revenue"] > 0
    score = dp.crps_ensemble(wf.closing, 1400.0)
    bench = dp.crps_ensemble(np.full(5000, 1121.6), 1400.0)
    assert dp.skill_score(score, bench) > 0, (score, bench)


if __name__ == "__main__":
    print()
    if _FAILURES:
        print(f"\n{len(_FAILURES)} FAILED: {', '.join(_FAILURES)}")
        sys.exit(1)
    print("all self-tests passed")
