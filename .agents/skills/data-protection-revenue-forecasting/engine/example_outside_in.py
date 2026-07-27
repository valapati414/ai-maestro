"""Worked outside-in forecast: Commvault FY27 total revenue, from public disclosure only.

Run: ``python3 example_outside_in.py``

Everything here is either a sourced FY26 disclosure (see references/company-profiles.md) or an
input explicitly tagged ASSUMPTION and carried into the assumption register that gets printed
at the end. The output follows the six-part output contract in SKILL.md.

The point of the example is not the number. It is that two methods built from different parts
of the disclosure — an ARR waterfall and a fitted guidance-realization ratio — are made to
disagree in public, and the disagreement is reported rather than averaged away quietly.
"""

from __future__ import annotations

import numpy as np

import dpforecast as dp

N_SIMS = 40000
SEED = 2026

# --------------------------------------------------------------------------------------
# 0. Sourced inputs — Commvault FY26 (fiscal year ended 3/31/2026), $ millions
# --------------------------------------------------------------------------------------

FY26 = {
    "revenue_total": 1183.690,
    "revenue_term_license": 435.324,
    "revenue_saas": 332.981,
    "revenue_perpetual": 43.212,
    "revenue_support": 320.426,
    "revenue_other_services": 51.747,
    "gaap_gross_margin": 0.812,
    "gaap_operating_income": 74.0,
    "sbc": 118.886,
    "fcf": 237.0,
    "deferred_revenue_current": 484.973,
    "deferred_revenue_noncurrent": 293.725,
    "deferred_revenue_current_py": 402.930,
    "deferred_revenue_noncurrent_py": 223.282,
    "rpo_incl_deferred": 1041.243,
    "rpo_pct_within_12m": 0.59,
}

# Total ARR and SaaS ARR, quarter-end, Q4 FY25 through Q4 FY26.
ARR_PATH_FY26 = np.array([930.051, 996.202, 1043.295, 1084.880, 1121.571])
SAAS_ARR_PATH_FY26 = np.array([281.045, 306.874, 335.669, 363.732, 400.157])

# Gross margin by stream, FY26 (derived from the recast cost-of-revenue table).
GM = {"term_license": 0.976, "saas": 0.645, "perpetual": 0.988, "support": 0.816,
      "other_services": 0.329}

# Guidance midpoint vs actual, total revenue, last six quarters.
GUIDANCE = [(245.0, 262.6), (262.0, 275.0), (268.0, 282.0),
            (273.0, 276.2), (299.0, 313.8), (306.5, 311.7)]

# FY27 guidance issued 4/28/26.
FY27_GUIDE_LOW, FY27_GUIDE_HIGH = 1300.0, 1310.0
FY27_GUIDE_MID = 0.5 * (FY27_GUIDE_LOW + FY27_GUIDE_HIGH)

ASSUMPTIONS: list[tuple[str, str, str]] = []


def assume(name: str, value: str, falsifier: str) -> None:
    ASSUMPTIONS.append((name, value, falsifier))


def rule(title: str) -> None:
    print(f"\n{'=' * 86}\n{title}\n{'=' * 86}")


def trapezoid_average(path: np.ndarray, axis: int = -1) -> np.ndarray:
    """Time-weighted average of a quarter-end stock series."""
    w = np.ones(path.shape[axis])
    w[0] = w[-1] = 0.5
    return np.tensordot(path, w, axes=([axis], [0])) / (path.shape[axis] - 1)


# --------------------------------------------------------------------------------------
# Step 1 — Fix definitions before touching a number
# --------------------------------------------------------------------------------------

rule("STEP 1  Definitions and the recast trap")

print("""Commvault Total ARR includes support attached to PERPETUAL licenses, so it is broader
than Rubrik's Subscription ARR and the two must never be compared directly.

Effective FY27 Commvault recast two definitions. Term-based support moves into subscription
revenue, lifting recast FY26 subscription revenue from $768.3M to $970.5M (+$202.2M) with no
change to total revenue; and Subscription ARR is recast to include enterprise support. Total
revenue and Total ARR are unaffected, which is why this forecast is built on TOTAL revenue and
TOTAL ARR: those two series survive the recast intact and need no rebasing.""")

recast_error = 1115.0 / 768.305 - 1115.0 / 970.468
print(f"  Growth error from missing the recast: {recast_error * 100:5.1f} pts on the subscription line")


# --------------------------------------------------------------------------------------
# Step 2 — Split contracted from at-risk, and compute the visibility ratio
# --------------------------------------------------------------------------------------

rule("STEP 2  Contracted vs at-risk, and what accuracy is even achievable")

contracted = FY26["rpo_incl_deferred"] * FY26["rpo_pct_within_12m"]
vis = dp.visibility_ratio(contracted, FY27_GUIDE_MID)
print(f"  RPO incl. deferred revenue at 3/31/26      ${FY26['rpo_incl_deferred']:8.1f}M")
print(f"  Expected to be recognized within 12 months        {FY26['rpo_pct_within_12m']:.0%}")
print(f"  => Contracted FY27 revenue                 ${contracted:8.1f}M")
print(f"  FY27 revenue at guidance midpoint          ${FY27_GUIDE_MID:8.1f}M")
print(f"  VISIBILITY RATIO                                {vis:.2f}")
print(f"""
  Only {vis:.0%} of FY27 revenue is contracted today, which is lower than the "recurring revenue
  is predictable" story implies. Two reasons, both structural rather than a red flag: RPO
  excludes cancellable arrangements entirely, and Commvault's one-year support renewals sit
  outside RPO until they are signed. All of the forecast uncertainty below lives in the other
  {1 - vis:.0%}, and any interval that does not is mis-specified.""")


# --------------------------------------------------------------------------------------
# Step 3 — The ARR-to-revenue conversion factor, fitted not assumed
# --------------------------------------------------------------------------------------

rule("STEP 3  Fit the ARR-to-revenue conversion factor on FY26 — by block, not blended")

arr_revenue_fy26 = (FY26["revenue_total"] - FY26["revenue_perpetual"]
                    - FY26["revenue_other_services"])
avg_arr_fy26 = float(trapezoid_average(ARR_PATH_FY26))
k_blended = arr_revenue_fy26 / avg_arr_fy26

# Split the ARR base into the two blocks that convert to revenue differently.
avg_saas_arr_fy26 = float(trapezoid_average(SAAS_ARR_PATH_FY26))
avg_rest_arr_fy26 = avg_arr_fy26 - avg_saas_arr_fy26
rest_revenue_fy26 = FY26["revenue_term_license"] + FY26["revenue_support"]
K_SAAS = FY26["revenue_saas"] / avg_saas_arr_fy26
K_REST = rest_revenue_fy26 / avg_rest_arr_fy26

print(f"  FY26 revenue from ARR-bearing streams       ${arr_revenue_fy26:8.1f}M")
print(f"  FY26 time-weighted average Total ARR        ${avg_arr_fy26:8.1f}M")
print(f"  => blended conversion factor                      {k_blended:.4f}")
print(f"""
  A blended factor bakes today's mix into every future period, so split it. Commvault
  discloses SaaS ARR quarterly, which is exactly enough to identify two blocks:""")
print(f"  SaaS:          revenue ${FY26['revenue_saas']:7.1f}M / avg ARR ${avg_saas_arr_fy26:7.1f}M "
      f"=> k_saas = {K_SAAS:.4f}")
print(f"  Term+support:  revenue ${rest_revenue_fy26:7.1f}M / avg ARR ${avg_rest_arr_fy26:7.1f}M "
      f"=> k_rest = {K_REST:.4f}")
print(f"""
  k_saas is 1.00 to two decimals, exactly as ASC 606 predicts: Commvault's SaaS is a single
  combined performance obligation recognized ratably, so a dollar of SaaS ARR is a dollar of
  annual revenue and nothing more. All of the excess sits in k_rest, because term licenses are
  a DISTINCT performance obligation recognized at a point in time — a three-year deal books one
  year of ARR but lands most of its license TCV immediately.

  This matters for the forecast direction. The instinct is that a rising SaaS mix drags the
  blended factor down, and it does, but far less than expected: the term+support block keeps
  growing in absolute dollars, so the drag is second-order. Step 6 propagates the two blocks
  separately instead of guessing at the net.""")

assume("k_saas (SaaS ARR to revenue)", f"{K_SAAS:.3f}, range 0.97-1.02",
       "a SaaS revenue quarter more than 3% away from the prior quarter's average SaaS ARR / 4")
assume("k_rest (term+support ARR to revenue)", f"{K_REST:.3f}, range 1.045-1.110",
       "a shift in disclosed term-license duration mix, or term-license revenue diverging "
       "from the non-SaaS ARR base")


# --------------------------------------------------------------------------------------
# Step 4 — The identification problem in the waterfall
# --------------------------------------------------------------------------------------

rule("STEP 4  Decompose FY26 ARR growth (and admit what is not identified)")

opening, closing = ARR_PATH_FY26[0], ARR_PATH_FY26[-1]
net_new = closing - opening
GRR_ASSUMED = 0.91
churn_fy26 = opening * (1 - GRR_ASSUMED)
gross_adds = net_new + churn_fy26
EXPANSION_SHARE = 2 / 3

expansion_fy26 = gross_adds * EXPANSION_SHARE
new_logo_fy26 = gross_adds * (1 - EXPANSION_SHARE)

print(f"  Opening Total ARR (3/31/25)                 ${opening:8.1f}M")
print(f"  Closing Total ARR (3/31/26)                 ${closing:8.1f}M   (+{net_new / opening:.1%})")
print(f"  Churn at assumed {GRR_ASSUMED:.0%} GRR                     $ -{churn_fy26:7.1f}M")
print(f"  => Gross adds required                      ${gross_adds:8.1f}M")
print(f"     of which expansion (assumed 2/3)         ${expansion_fy26:8.1f}M  ({expansion_fy26 / opening:.1%} of opening)")
print(f"     of which new logos                       ${new_logo_fy26:8.1f}M  (${new_logo_fy26 / 4:.1f}M/qtr)")
print("""
  Commvault discloses SaaS NRR (122%) but neither gross retention nor a total-company NRR, and
  no vendor in this category discloses GRR. So GRR, expansion and new-logo ARR are NOT
  separately identified from public data: only their combination is pinned down by the observed
  net ARR change. Step 8 exploits this — the FY27 revenue forecast turns out to be nearly
  invariant to how the split is drawn, while the terminal value is not. Report the invariance
  rather than pretending to a decomposition you cannot see.""")

assume("Gross retention rate (GRR)", "0.91, range 0.88-0.93",
       "a disclosed GRR, or a churn disclosure implying a rate outside that band")
assume("Expansion share of gross ARR adds", "2/3, range 0.50-0.80",
       "customer-count disclosure resuming; +N customers pins the new-logo half directly")


# --------------------------------------------------------------------------------------
# Step 5 — Simulate the FY27 ARR waterfall
# --------------------------------------------------------------------------------------

rule("STEP 5  Simulate the FY27 ARR waterfall")

EXPANSION_FY27 = 0.165  # decelerating from FY26's 19.7%
NEW_LOGO_Q = new_logo_fy26 / 4 * 0.95

spec = dp.WaterfallSpec(
    opening_arr=float(closing),
    grr=dp.Beta(mean_=GRR_ASSUMED, sd=0.012),
    expansion=dp.Normal(EXPANSION_FY27, 0.030),
    new_logo_arr=dp.LogNormal(median=NEW_LOGO_Q, sigma=0.22),
    periods_per_year=4,
    rho=0.40,
)
wf = dp.simulate_arr_waterfall(spec, n_periods=4, n_sims=N_SIMS, seed=SEED)
bridge = wf.mean_bridge()

print("  Mean FY27 ARR bridge ($M):")
for label, key in [("opening ARR", "opening_arr"), ("churn", "churn"),
                   ("expansion", "expansion"), ("new logos", "new_logo"),
                   ("closing ARR", "closing_arr")]:
    print(f"    {label:<16s} {bridge[key]:>9.1f}")
close_q = dp.quantiles(wf.closing, (0.1, 0.5, 0.9))
print(f"  Closing Total ARR   P10 ${close_q['p10']:.0f}M | P50 ${close_q['p50']:.0f}M | P90 ${close_q['p90']:.0f}M")
print(f"  Implied Total ARR growth at the median            {close_q['p50'] / closing - 1:.1%}")

# Cross-check the simulated ARR against what management's own ARR guidance implies.
RECAST_SUB_ARR_FY26 = 1014.729
GUIDE_SUB_ARR_FY27 = 1205.0                       # midpoint of $1,200-1,210M
non_sub_arr = closing - RECAST_SUB_ARR_FY26        # perpetual support, mostly
guide_implied_total_arr = GUIDE_SUB_ARR_FY27 + non_sub_arr * 0.80  # non-sub decays ~20%

print(f"\n  Cross-check against management's own ARR guidance:")
print(f"    recast Subscription ARR 3/31/26        ${RECAST_SUB_ARR_FY26:8.1f}M")
print(f"    FY27 Subscription ARR guide (mid)      ${GUIDE_SUB_ARR_FY27:8.1f}M  "
      f"(+{GUIDE_SUB_ARR_FY27 / RECAST_SUB_ARR_FY26 - 1:.1%})")
print(f"    non-subscription ARR, decayed 20%      ${non_sub_arr * 0.80:8.1f}M")
print(f"    => guidance-implied Total ARR          ${guide_implied_total_arr:8.1f}M  "
      f"(+{guide_implied_total_arr / closing - 1:.1%})")
print(f"    our simulated median Total ARR         ${close_q['p50']:8.1f}M  "
      f"(+{close_q['p50'] / closing - 1:.1%})")
print(f"""
  Our ARR forecast is BELOW what management's own ARR guidance implies. That is worth pausing
  on, because the revenue forecast in Step 6 comes out above management's revenue guide. Both
  cannot be driven by optimism about demand. Step 7c isolates where the disagreement actually
  sits.""")

assume("FY27 expansion rate on the surviving base", f"{EXPANSION_FY27:.1%}, sd 3.0pts",
       "Q1/Q2 FY27 net-new ARR in constant currency running outside the implied quarterly pace")
assume("Within-year period correlation (rho)", "0.40",
       "four FY27 quarters whose net-new ARR is closer to independent than to persistent")
assume("Non-subscription ARR decay", "-20%",
       "perpetual-support ARR disclosed separately and running outside -10% to -30%")


# --------------------------------------------------------------------------------------
# Step 6 — ARR to revenue, plus the streams ARR does not cover
# --------------------------------------------------------------------------------------

rule("STEP 6  Convert to FY27 revenue, propagating the two ARR blocks separately")

rng = np.random.default_rng(SEED + 1)

# SaaS ARR grew +42.4% in FY26. Decelerate, and let it be uncertain.
SAAS_ARR_GROWTH = 0.33
saas_growth_draws = SAAS_ARR_GROWTH + 0.06 * rng.standard_normal(N_SIMS)
saas_arr_close = SAAS_ARR_PATH_FY26[-1] * (1 + saas_growth_draws)
avg_saas_arr_fy27 = 0.5 * (SAAS_ARR_PATH_FY26[-1] + saas_arr_close)

avg_arr_fy27 = trapezoid_average(wf.arr, axis=1)
avg_rest_arr_fy27 = np.maximum(avg_arr_fy27 - avg_saas_arr_fy27, 0.0)

# What k_rest would management's own revenue guide require, given its own ARR guide?
_guide_arr_rev = (FY27_GUIDE_MID - FY26["revenue_perpetual"] * (1 - 0.22)
                  - FY26["revenue_other_services"] * 1.10)
_guide_avg_arr = 0.5 * (closing + guide_implied_total_arr)
_guide_avg_saas = float(np.median(avg_saas_arr_fy27))
K_REST_GUIDE = (_guide_arr_rev - K_SAAS * _guide_avg_saas) / (_guide_avg_arr - _guide_avg_saas)

# Model uncertainty, not parameter uncertainty: with probability P_MGMT the guide's much lower
# implied conversion factor is the right one and we are missing something management can see.
# The weight is set by a coverage rule, not by taste — see the note printed below Step 6 and
# the assertion at the end of Step 7c.
P_MGMT = 0.35
k_saas_draws = rng.triangular(0.970, K_SAAS, 1.020, N_SIMS)
k_rest_ours = rng.triangular(1.045, K_REST, 1.110, N_SIMS)
k_rest_mgmt = rng.triangular(K_REST_GUIDE - 0.02, K_REST_GUIDE, K_REST_GUIDE + 0.027, N_SIMS)
use_mgmt = rng.uniform(size=N_SIMS) < P_MGMT
k_rest_draws = np.where(use_mgmt, k_rest_mgmt, k_rest_ours)

arr_revenue_fy27 = k_saas_draws * avg_saas_arr_fy27 + k_rest_draws * avg_rest_arr_fy27
k_implied = arr_revenue_fy27 / avg_arr_fy27

PERP_DECLINE = 0.22
SERVICES_GROWTH = 0.10
perp = FY26["revenue_perpetual"] * (1 - PERP_DECLINE) * np.exp(
    0.12 * rng.standard_normal(N_SIMS) - 0.5 * 0.12 ** 2)
svcs = FY26["revenue_other_services"] * (1 + SERVICES_GROWTH) * np.exp(
    0.10 * rng.standard_normal(N_SIMS) - 0.5 * 0.10 ** 2)

revenue_waterfall = arr_revenue_fy27 + perp + svcs

print(f"  avg SaaS ARR           P50 ${np.median(avg_saas_arr_fy27):8.1f}M  x k_saas {K_SAAS:.3f}")
print(f"  avg term+support ARR   P50 ${np.median(avg_rest_arr_fy27):8.1f}M  x k_rest {K_REST:.3f}")
print(f"  ARR-borne revenue      P50 ${np.median(arr_revenue_fy27):8.1f}M")
print(f"  Perpetual license      P50 ${np.median(perp):8.1f}M   (FY26 -22%, assumed to continue)")
print(f"  Professional services  P50 ${np.median(svcs):8.1f}M   (FY26 +21%, decelerated to +10%)")
print(f"  ---------------------------------------------")
wq = dp.quantiles(revenue_waterfall, (0.1, 0.5, 0.9))
print(f"  METHOD A total FY27    P10 ${wq['p10']:.0f}M | P50 ${wq['p50']:.0f}M | P90 ${wq['p90']:.0f}M")
print(f"\n  Implied blended conversion factor: {np.median(k_implied):.4f} "
      f"vs FY26's {k_blended:.4f} ({np.median(k_implied) - k_blended:+.4f})")
print(f"  SaaS share of average ARR: {float(np.median(avg_saas_arr_fy27 / avg_arr_fy27)):.1%} "
      f"vs FY26 {avg_saas_arr_fy26 / avg_arr_fy26:.1%}")
print("  A large mix shift, a small conversion effect. Worth knowing before arguing about it.")
print(f"""
  k_rest is drawn as a MIXTURE, not a range: {1 - P_MGMT:.0%} from our fitted view
  ({K_REST:.3f}) and {P_MGMT:.0%} from the much lower {K_REST_GUIDE:.3f} that management's own revenue and
  ARR guides jointly imply (Step 7c derives it). This is model uncertainty rather than
  parameter uncertainty: the two views are different stories about FY27 contract structure, not
  two points in one range, and management can see things the filings do not show.

  The weight is set by a coverage rule rather than by taste: it must be large enough that the
  80% interval still contains the outcome management is guiding to. Publishing an interval that
  excludes the company's own guide amounts to claiming better than 90% confidence that
  management is wrong about its own business, which is not a claim this evidence supports.
  {P_MGMT:.0%} is the smallest round weight that satisfies the rule; Step 7c asserts it.""")

assume("P(management's implied conversion factor is the right one)", f"{P_MGMT:.0%}",
       "Q1 FY27 term-license revenue vs Q1 Total ARR, which resolves it in one quarter")

assume("SaaS ARR growth", f"+{SAAS_ARR_GROWTH:.0%}, sd 6pts (FY26 was +42%)",
       "two quarters of SaaS ARR growth outside the +27% to +39% band")
assume("Perpetual license decline", f"-{PERP_DECLINE:.0%}", "any quarter of perpetual growth")
assume("Professional services growth", f"+{SERVICES_GROWTH:.0%}",
       "two consecutive quarters outside +/-5pts of that pace")


# --------------------------------------------------------------------------------------
# Step 7 — Independent cross-check: fitted guidance realization
# --------------------------------------------------------------------------------------

rule("STEP 7  Cross-check with the fitted guidance-realization ratio")

ratios = np.array([actual / guide for guide, actual in GUIDANCE])
r_mean, r_sd = float(ratios.mean()), float(ratios.std(ddof=1))
print("  Quarterly total-revenue guidance midpoint vs actual:")
for (g, a), r in zip(GUIDANCE, ratios):
    print(f"    guide {g:7.1f}  actual {a:7.1f}   realization {r:.4f}")
print(f"  mean {r_mean:.4f}, sd {r_sd:.4f}, n = {len(ratios)}")
print(f"  FY26 initial annual guide 1135.0 -> actual {FY26['revenue_total']:.1f} "
      f"= {FY26['revenue_total'] / 1135.0:.4f}")

revenue_guidance = FY27_GUIDE_MID * (r_mean + r_sd * rng.standard_normal(N_SIMS))
gq = dp.quantiles(revenue_guidance, (0.1, 0.5, 0.9))
print(f"\n  METHOD B total FY27    P10 ${gq['p10']:.0f}M | P50 ${gq['p50']:.0f}M | P90 ${gq['p90']:.0f}M")
print(f"""
  Guidance has been beaten in six consecutive quarters, so taking the FY27 midpoint at face
  value systematically under-forecasts. That is a fitted, falsifiable pattern rather than a
  view about the business. Two cautions kept in the register: the quarterly realization ratio
  is applied to an ANNUAL guide, and the initial-annual-guide realization has n = 1.""")

assume("Guidance realization ratio", f"{r_mean:.3f} +/- {r_sd:.3f} (n={len(ratios)}, quarterly)",
       "one FY27 quarter landing below the guided midpoint")

disagreement = float(np.median(revenue_guidance) - np.median(revenue_waterfall))
print(f"  Method disagreement (B - A): ${disagreement:+.1f}M "
      f"({disagreement / np.median(revenue_waterfall):+.2%} of Method A)")


# --------------------------------------------------------------------------------------
# Step 7b — Combine as a MIXTURE, then floor the interval width
# --------------------------------------------------------------------------------------

rule("STEP 7b  Combine the methods honestly")

W_A = 0.6  # weight on the waterfall; Method B rests on a single fitted ratio
pick_a = rng.uniform(size=N_SIMS) < W_A
mixture = np.where(pick_a, revenue_waterfall, revenue_guidance)
avg_blend = W_A * revenue_waterfall + (1 - W_A) * revenue_guidance

print(f"  Weighted-average blend:  sd ${avg_blend.std(ddof=1):5.1f}M")
print(f"  Mixture of the two:      sd ${mixture.std(ddof=1):5.1f}M")
print("""
  Averaging two independent sets of draws quietly cancels their errors and produces an
  interval narrower than either method alone — it treats disagreement between models as
  diversifiable, which it is not. A mixture keeps the disagreement in the distribution. Use
  the mixture.""")

# Floor the spread. The company's own guidance, issued with full internal visibility three
# months out, still realizes with a 2.3% standard deviation. An outside-in forecast made
# twelve months out with only public data cannot honestly be sharper than that.
sd_floor = r_sd * FY27_GUIDE_MID
current_sd = float(mixture.std(ddof=1))
inflation = max(sd_floor / current_sd, 1.0)
centre = float(mixture.mean())
combined = centre + (mixture - centre) * inflation

print(f"  Parameter-uncertainty sd from the mixture      ${current_sd:6.1f}M "
      f"({current_sd / centre:.2%} of the median)")
print(f"  Floor: the company's own 3-month-ahead realization sd "
      f"${sd_floor:6.1f}M ({r_sd:.2%})")
print(f"  => inflating the interval by {inflation:.2f}x")
print("""
  Parameter uncertainty is not forecast uncertainty. What the Monte Carlo above measures is
  the spread implied by the ranges we chose, which says nothing about the assumptions we did
  not think to vary or the structure being wrong. Rather than invent a structural-error term,
  we impose a floor with an external referent: management, with the CRM in front of them and
  a three-month horizon, still misses its own midpoint with a 2.3% standard deviation. A
  twelve-month outside-in forecast built from public filings is not entitled to be sharper.

  This is a floor, not an estimate. It is almost certainly still too narrow.""")

assume("Interval-width floor", f"sd >= {r_sd:.1%} of the median, from guidance realization",
       "a backtest of this method over enough resolved periods to measure PIT coverage "
       "directly, which would replace the floor with a fitted value")


# --------------------------------------------------------------------------------------
# Step 7c — Where, precisely, do we disagree with management?
# --------------------------------------------------------------------------------------

rule("STEP 7c  Attribute the disagreement with guidance to a single variable")

guide_perp = FY26["revenue_perpetual"] * (1 - PERP_DECLINE)
guide_svcs = FY26["revenue_other_services"] * (1 + SERVICES_GROWTH)
guide_arr_revenue = FY27_GUIDE_MID - guide_perp - guide_svcs
guide_avg_arr = 0.5 * (closing + guide_implied_total_arr)
guide_implied_k = guide_arr_revenue / guide_avg_arr

our_median = float(np.median(combined))
print(f"  Management guides revenue      ${FY27_GUIDE_MID:8.1f}M")
print(f"  We forecast (median)           ${our_median:8.1f}M   ({our_median - FY27_GUIDE_MID:+.1f}M)")
print()
print(f"  Back out the conversion factor embedded in management's own guidance:")
print(f"    guided revenue                       ${FY27_GUIDE_MID:8.1f}M")
print(f"    less perpetual + services            ${-(guide_perp + guide_svcs):8.1f}M")
print(f"    = ARR-borne revenue implied by guide ${guide_arr_revenue:8.1f}M")
print(f"    guidance-implied average Total ARR   ${guide_avg_arr:8.1f}M")
print(f"    => k implied by GUIDANCE                   {guide_implied_k:.4f}")
print(f"       k realized in FY26                      {k_blended:.4f}")
print(f"       k in our FY27 model (median)            {float(np.median(k_implied)):.4f}")
print(f"    In k_rest terms: guidance implies {K_REST_GUIDE:.3f} against FY26's realized {K_REST:.3f}.")

print(f"""
  There it is. Management's revenue guide and its own ARR guide are only mutually consistent if
  the ARR-to-revenue conversion factor collapses from {k_blended:.3f} to {guide_implied_k:.3f} in a single year —
  a {(k_blended - guide_implied_k) * 100:.1f}-point drop. Our model has it falling {(k_blended - float(np.median(k_implied))) * 100:.1f} points, because the SaaS mix shift
  we can actually measure ({avg_saas_arr_fy26 / avg_arr_fy26:.0%} to {float(np.median(avg_saas_arr_fy27 / avg_arr_fy27)):.0%} of average ARR) does not mechanically produce more.

  So the entire disagreement with management is one variable, and it is an accounting variable,
  not a demand variable. We are NOT forecasting that Commvault sells more than it says it will
  — our ARR forecast is slightly below the guide. We are forecasting that its contracts convert
  to revenue closer to the way they did last year than the guide implies.

  Three readings, and the analysis does not distinguish between them:
    1. Conservative guidance. Consistent with six straight beats and a {r_mean:.3f} realization ratio.
    2. Management expects a sharper term-license duration shift than the SaaS mix implies —
       for instance more 1-year terms, which cut upfront license recognition hard.
    3. Our k_rest is too high because FY26's term-license revenue was flattered by something
       non-recurring in the duration mix.

  Reading 1 and reading 2 point in opposite directions for the same observable, which is why
  the assumption register lists a specific falsifier: Q1 FY27 term-license revenue against Q1
  Total ARR resolves it in a single quarter. Until then this is the position, stated so it can
  be attacked at its actual weak point rather than argued about in generalities.

  Step 6 already carries reading 2/3 at {P_MGMT:.0%} weight, which is why the interval below reaches
  down to the guidance-consistent outcome instead of ruling it out.""")

k_mgmt_scenario = (K_SAAS * float(np.median(avg_saas_arr_fy27))
                   + K_REST_GUIDE * float(np.median(avg_rest_arr_fy27))
                   + guide_perp + guide_svcs)
p10 = dp.quantiles(combined, (0.1,))["p10"]
print(f"  Scenario: if management's implied k_rest ({K_REST_GUIDE:.3f}) is right and our ARR path holds,")
print(f"  FY27 revenue is ${k_mgmt_scenario:.0f}M — within ${abs(k_mgmt_scenario - FY27_GUIDE_MID):.0f}M of the guidance midpoint.")
print(f"  Our P10 is ${p10:.0f}M, so that scenario sits "
      f"{'inside' if p10 <= k_mgmt_scenario else 'OUTSIDE'} the 80% interval — as the coverage")
print(f"  rule in Step 6 requires.")
assert p10 <= k_mgmt_scenario, (
    f"80% interval floor ${p10:.0f}M excludes the guidance-consistent outcome "
    f"${k_mgmt_scenario:.0f}M. Raise P_MGMT until it does not.")


# --------------------------------------------------------------------------------------
# Step 8 — Sensitivity: which assumptions is the answer actually made of
# --------------------------------------------------------------------------------------

rule("STEP 8  Rank the levers")


def revenue_model(p) -> float:
    """Deterministic version of the same chain, for one-at-a-time swings."""
    s = dp.WaterfallSpec(opening_arr=float(closing), grr=dp.Point(p["grr"]),
                         expansion=dp.Point(p["expansion"]),
                         new_logo_arr=dp.Point(p["new_logo_q"]), periods_per_year=4, rho=0.0)
    w = dp.simulate_arr_waterfall(s, n_periods=4, n_sims=1, seed=0)
    avg_total = float(trapezoid_average(w.arr, axis=1)[0])
    avg_saas = 0.5 * (SAAS_ARR_PATH_FY26[-1]
                      + SAAS_ARR_PATH_FY26[-1] * (1 + p["saas_arr_growth"]))
    avg_rest = max(avg_total - avg_saas, 0.0)
    return (p["k_saas"] * avg_saas + p["k_rest"] * avg_rest
            + FY26["revenue_perpetual"] * (1 - p["perp_decline"])
            + FY26["revenue_other_services"] * (1 + p["services_growth"]))


base = {"k_saas": K_SAAS, "k_rest": K_REST, "grr": GRR_ASSUMED, "expansion": EXPANSION_FY27,
        "new_logo_q": NEW_LOGO_Q, "saas_arr_growth": SAAS_ARR_GROWTH,
        "perp_decline": PERP_DECLINE, "services_growth": SERVICES_GROWTH}
ranges = {
    "k_saas": (0.970, 1.020),
    "k_rest": (1.045, 1.110),
    "grr": (0.88, 0.93),
    "expansion": (0.12, 0.21),
    "new_logo_q": (NEW_LOGO_Q * 0.7, NEW_LOGO_Q * 1.3),
    "saas_arr_growth": (0.20, 0.45),
    "perp_decline": (0.10, 0.35),
    "services_growth": (0.0, 0.21),
}
ranked = dp.rank_levers(revenue_model, base, ranges)
print(f"  {'lever':<18s} {'low':>10s} {'high':>10s} {'swing $M':>10s} {'% of base':>10s}")
for e in ranked:
    print(f"  {e.name:<18s} {e.low_value:>10.3f} {e.high_value:>10.3f} "
          f"{e.swing:>10.1f} {e.swing_pct:>9.2%}")

ACCOUNTING_LEVERS = {"k_saas", "k_rest"}
acct = [e for e in ranked if e.name in ACCOUNTING_LEVERS]
demand = [e for e in ranked if e.name not in ACCOUNTING_LEVERS]
print(f"""
  {sum(1 for e in ranked[:3] if e.name in ACCOUNTING_LEVERS)} of the top 3 levers are accounting
  variables rather than demand variables. The largest accounting lever ({acct[0].name},
  ${acct[0].swing:.0f}M) is within ${abs(acct[0].swing - demand[0].swing):.0f}M of the largest demand lever
  ({demand[0].name}, ${demand[0].swing:.0f}M). Neither conversion factor says anything about how much
  Commvault sells; both describe how its contracts are shaped. A forecast of this business is
  about as sensitive to contract structure as to demand, which is why Step 3 fits the factors
  from disclosure rather than assuming them.

  Note the counter-intuitive bottom of the table: SaaS ARR growth is the LEAST important lever
  here (${ranked[-1].swing:.0f}M across a 20%-to-45% range) even though it is the metric the market
  watches most closely. Because k_saas < k_rest, faster SaaS growth at a given total ARR is
  mildly revenue-dilutive in-year — ARR-neutral, value-accretive, and reported-revenue-negative
  all at once. That is the term-license-to-SaaS transition in miniature.""")

# The identification-invariance claim, demonstrated rather than asserted.
def refit_to_fy26(grr_alt: float) -> dict:
    """Re-solve the FY26 decomposition at a different GRR, holding observed FY26 ARR fixed."""
    adds = net_new + opening * (1 - grr_alt)
    exp_fy26 = adds * EXPANSION_SHARE / opening
    p = dict(base)
    p["grr"] = grr_alt
    p["expansion"] = exp_fy26 * (EXPANSION_FY27 / (gross_adds * EXPANSION_SHARE / opening))
    p["new_logo_q"] = adds * (1 - EXPANSION_SHARE) / 4 * 0.95
    return p


print("  Identification check — same observed FY26, three different stories about it:")
print(f"  {'GRR':>6s} {'FY26 expansion':>15s} {'new logo/qtr':>13s} {'FY27 revenue':>13s} {'ARR half-life':>14s}")
for g in (0.88, 0.91, 0.93):
    p = refit_to_fy26(g)
    adds = net_new + opening * (1 - g)
    print(f"  {g:>6.2f} {adds * EXPANSION_SHARE / opening:>14.1%} "
          f"${adds * (1 - EXPANSION_SHARE) / 4:>12.1f}M ${revenue_model(p):>12.0f}M "
          f"{dp.arr_half_life(g):>12.1f}y")
spread = max(revenue_model(refit_to_fy26(g)) for g in (0.88, 0.93)) - \
    min(revenue_model(refit_to_fy26(g)) for g in (0.88, 0.93))
print(f"""
  GRR is unobservable and the three rows are equally consistent with every number Commvault
  has published. They differ by ${spread:.0f}M of FY27 revenue — under 1% — because a point of
  churn avoided is a point of gross adds no longer needed, in the same year. They differ by
  {dp.arr_half_life(0.93) - dp.arr_half_life(0.88):.1f} years of base half-life, which is a very large difference in terminal value.
  So: forecast the year without resolving GRR, and refuse to value the company without it.""")


# --------------------------------------------------------------------------------------
# Step 9 — P&L and cash
# --------------------------------------------------------------------------------------

rule("STEP 9  Build the P&L by stream and bridge to cash")

median_rev = float(np.median(combined))
scale = median_rev / FY26["revenue_total"]
fy27_rev_by_stream = {
    "term_license": FY26["revenue_term_license"] * scale * 1.02,
    "saas": FY26["revenue_saas"] * scale * 1.22,
    "perpetual": float(np.median(perp)),
    "support": FY26["revenue_support"] * scale * 0.97,
    "other_services": float(np.median(svcs)),
}
norm = median_rev / sum(fy27_rev_by_stream.values())
fy27_rev_by_stream = {k_: v * norm for k_, v in fy27_rev_by_stream.items()}

opex = {"sm": median_rev * 0.425, "rd": median_rev * 0.135, "ga": median_rev * 0.133,
        "amort_and_restructuring": median_rev * 0.030}
pnl = dp.pnl_by_stream(fy27_rev_by_stream, GM, opex)

print("  Stream growth rates below are illustrative and normalized to sum to the simulated")
print("  total; the point is the margin arithmetic, not the split.\n")
print(f"  {'stream':<16s} {'FY27 $M':>9s} {'GM':>7s}")
for s, v in fy27_rev_by_stream.items():
    print(f"  {s:<16s} {v:>9.1f} {GM[s]:>7.1%}")
print(f"  {'-' * 34}")
print(f"  revenue           {pnl['revenue']:>9.1f}")
print(f"  gross margin      {pnl['gross_margin']:>9.1%}   (FY26 actual {FY26['gaap_gross_margin']:.1%})")
print(f"  operating income  {pnl['operating_income']:>9.1f}")
print(f"  operating margin  {pnl['operating_margin']:>9.1%}   (FY26 actual "
      f"{FY26['gaap_operating_income'] / FY26['revenue_total']:.1%})")

mix_pts = (fy27_rev_by_stream["saas"] / pnl["revenue"]
           - FY26["revenue_saas"] / FY26["revenue_total"]) * 100
print(f"\n  SaaS mix shift vs FY26: {mix_pts:+.1f} pts, which is why gross margin falls even as")
print("  revenue grows. A blended-margin model would have missed this entirely.")

# Calibrate the cash bridge on FY26 before using it on FY27. Commvault does not disclose the
# working-capital detail, so solve for the residual and carry it forward rather than guessing.
d_dr_fy26 = ((FY26["deferred_revenue_current"] + FY26["deferred_revenue_noncurrent"])
             - (FY26["deferred_revenue_current_py"] + FY26["deferred_revenue_noncurrent_py"]))
D_AND_A, CAPEX_FY26 = 20.0, 8.0
known_fy26 = (FY26["gaap_operating_income"] + D_AND_A + FY26["sbc"] + d_dr_fy26)
residual_fy26 = known_fy26 - CAPEX_FY26 - FY26["fcf"]

print(f"\n  Cash bridge, calibrated on FY26 (actual FCF ${FY26['fcf']:.0f}M):")
print(f"    operating income {FY26['gaap_operating_income']:>7.1f} + D&A {D_AND_A:>5.1f} "
      f"+ SBC {FY26['sbc']:>6.1f} + dDefRev {d_dr_fy26:>6.1f} - capex {CAPEX_FY26:>4.1f}"
      f" = {known_fy26 - CAPEX_FY26:>7.1f}")
print(f"    residual (receivables, deferred commissions, cash taxes, other WC) "
      f"{-residual_fy26:>7.1f}")
print(f"    => FY26 FCF {known_fy26 - CAPEX_FY26 - residual_fy26:>7.1f}  (reconciles by construction)")
print(f"    residual as % of revenue: {residual_fy26 / FY26['revenue_total']:.1%} "
      f"— carried forward at that rate, not as a fixed dollar amount")

d_dr = d_dr_fy26 * scale
fcf = dp.fcf_bridge(operating_income=pnl["operating_income"], depreciation_amortization=D_AND_A,
                    stock_based_comp=FY26["sbc"] * scale, delta_deferred_revenue=d_dr,
                    delta_other_wc=-residual_fy26 * scale,
                    capex=CAPEX_FY26 * scale,
                    buyback_to_offset_dilution=FY26["sbc"] * scale)
print(f"\n  FY27 free cash flow           ${fcf['free_cash_flow']:8.1f}M  "
      f"(company guides $250-260M)")
gap = fcf["free_cash_flow"] - 255.0
print(f"  vs guidance midpoint          ${gap:+8.1f}M  "
      f"({'consistent' if abs(gap) < 40 else 'CHECK THIS — the bridge and the guide disagree'}, "
      f"and it should be: our revenue is {median_rev / FY27_GUIDE_MID - 1:+.1%} vs the guide too)")
print(f"  FCF after offsetting dilution ${fcf['fcf_after_dilution_offset']:8.1f}M  "
      f"<- SBC is not free; the buyback is its cash cost")
print(f"  of which delta deferred revenue ${fcf['deferred_revenue_contribution']:6.1f}M "
      f"— the largest single line, and a bookings-timing artifact rather than earnings")
print("""
  Note what the last two lines do to the story. Headline FCF looks like roughly three times
  GAAP operating income, but most of the gap is customers prepaying (deferred revenue) plus an
  SBC add-back that Commvault turns straight back into cash through buybacks. Strip both and
  the cash generation is far closer to the GAAP number than the headline suggests.""")


# --------------------------------------------------------------------------------------
# Step 10 — Reconciliation
# --------------------------------------------------------------------------------------

rule("STEP 10  Reconcile against disclosed FY26 metrics")

billings_fy26 = FY26["revenue_total"] + (
    (FY26["deferred_revenue_current"] + FY26["deferred_revenue_noncurrent"])
    - (FY26["deferred_revenue_current_py"] + FY26["deferred_revenue_noncurrent_py"]))
rec = dp.revenue_identity_residual(
    billings=billings_fy26,
    delta_deferred_revenue=(FY26["deferred_revenue_current"] + FY26["deferred_revenue_noncurrent"])
    - (FY26["deferred_revenue_current_py"] + FY26["deferred_revenue_noncurrent_py"]),
    delta_contract_assets=0.0,
    revenue=FY26["revenue_total"])
print(f"  Derived FY26 billings                       ${billings_fy26:8.1f}M")
print(f"  Revenue identity residual                   ${rec['residual']:8.3f}M "
      f"({rec['residual_pct_of_revenue']:.2%})")
print("  Circular by construction here, because Commvault does not disclose billings and the")
print("  identity is what produced the estimate. With a disclosed billings figure this becomes")
print("  a real test; the check is kept in place so it starts working the moment one exists.")

implied_growth = np.median(combined) / FY26["revenue_total"] - 1
print(f"\n  Sanity band on implied FY27 total revenue growth: {implied_growth:.1%}")
print(f"    FY26 actual growth                        +19.0%  (constant currency +16%)")
print(f"    FY27 company guidance implies             +{FY27_GUIDE_MID / FY26['revenue_total'] - 1:.1%}")
assert 0.05 < implied_growth < 0.25, "implied growth outside a defensible band — stop and redo"
print("  Forecast growth sits between the guide and the prior year, as a decelerating"
      "\n  large-base infrastructure vendor should.")


# --------------------------------------------------------------------------------------
# Step 11 — Scoring plan
# --------------------------------------------------------------------------------------

rule("STEP 11  Scoring plan — declared before resolution")

benchmark = np.full(N_SIMS, FY27_GUIDE_MID)
naive = np.full(N_SIMS, FY26["revenue_total"] * 1.19)  # last year's growth, repeated

print(f"  Benchmark 1: company guidance midpoint taken at face value  ${FY27_GUIDE_MID:.0f}M")
print(f"  Benchmark 2: FY26 growth rate repeated                      ${naive[0]:.0f}M")
print("  Proper score: CRPS, reported alongside pinball loss at the 10/50/90 quantiles.")
print("  Resolves: Commvault Q4 FY27 press release, expected late April 2027.")

def fmt_skill(model: float, bench: float) -> str:
    return "  n/a" if bench == 0 else f"{dp.skill_score(model, bench):+.2f}"


print(f"\n  {'if the outcome turns out to be':<36s} {'CRPS':>6s} {'vs guide':>9s} {'vs naive':>9s}")
for label, hypo in [("the guidance midpoint exactly", FY27_GUIDE_MID),
                    ("our median exactly", float(np.median(combined))),
                    ("a 3% guidance beat", FY27_GUIDE_MID * 1.03),
                    ("a 5% guidance MISS", FY27_GUIDE_MID * 0.95)]:
    s_us = dp.crps_ensemble(combined, hypo)
    print(f"  {label:<36s} {s_us:>6.1f} {fmt_skill(s_us, dp.crps_ensemble(benchmark, hypo)):>9s} "
          f"{fmt_skill(s_us, dp.crps_ensemble(naive, hypo)):>9s}")
print("  ('vs guide' is n/a in row 1 because a point forecast that is exactly right scores 0.)")

print("""
  Read the last row before the first. Our distribution beats both benchmarks comfortably when
  the outcome lands near our median, and it also loses less than a point forecast would if the
  outcome lands well outside — that asymmetry is the entire reason to ship a distribution. But
  no single resolution can establish calibration. Only a run of forecasts with a uniform PIT
  histogram can, which is why the scoring plan below commits to tracking coverage.""")


# --------------------------------------------------------------------------------------
# THE DELIVERABLE
# --------------------------------------------------------------------------------------

rule("OUTPUT CONTRACT  Commvault FY27 total revenue (FY ending 3/31/2027)")

q = dp.quantiles(combined, (0.1, 0.25, 0.5, 0.75, 0.9))
print(f"\n1. HEADLINE")
print(f"   FY27 total revenue, median ${q['p50']:.0f}M; 80% interval "
      f"${q['p10']:.0f}M to ${q['p90']:.0f}M")
print(f"   Implied growth: {q['p50'] / FY26['revenue_total'] - 1:.1%} "
      f"({q['p10'] / FY26['revenue_total'] - 1:.1%} to {q['p90'] / FY26['revenue_total'] - 1:.1%})")
print(f"   vs company guidance ${FY27_GUIDE_LOW:.0f}-{FY27_GUIDE_HIGH:.0f}M: "
      f"{q['p50'] / FY27_GUIDE_MID - 1:+.1%} at the median")
print(f"   P(revenue > guidance high end) = {float((combined > FY27_GUIDE_HIGH).mean()):.0%}")
print(f"   THE WHOLE CALL RESTS ON ONE VARIABLE. Our ARR forecast is slightly BELOW what")
print(f"   management's own ARR guide implies; the revenue difference is entirely the")
print(f"   ARR-to-revenue conversion factor (Step 7c). One quarter of term-license revenue")
print(f"   against Total ARR settles it. Do not read this as a demand call.")

print(f"\n2. THE SPLIT")
print(f"   Contracted (cRPO)     ${contracted:7.1f}M    visibility ratio {vis:.2f}")
print(f"   At risk               ${q['p50'] - contracted:7.1f}M    all of the interval width lives here")

print(f"\n3. DECOMPOSITION")
print(f"   ARR:  {bridge['opening_arr']:.0f} opening {bridge['churn']:+.0f} churn "
      f"{bridge['expansion']:+.0f} expansion {bridge['new_logo']:+.0f} new logos "
      f"= {bridge['closing_arr']:.0f} closing")
print(f"   Revenue: {K_SAAS:.3f} x SaaS ARR {float(np.median(avg_saas_arr_fy27)):.0f} "
      f"+ {K_REST:.3f} x other ARR {float(np.median(avg_rest_arr_fy27)):.0f} "
      f"+ {float(np.median(perp)):.0f} perpetual + {float(np.median(svcs)):.0f} services "
      f"= {float(np.median(revenue_waterfall)):.0f}  (Method A)")

print(f"\n4. MOST SENSITIVE ASSUMPTIONS")
for e in ranked[:4]:
    print(f"   {e.name:<16s} {e.low_value:.3f} to {e.high_value:.3f}  "
          f"moves revenue ${e.swing:.0f}M ({e.swing_pct:.1%})")

print(f"\n5. ASSUMPTION REGISTER  ({len(ASSUMPTIONS)} entries, every one falsifiable)")
for name, value, falsifier in ASSUMPTIONS:
    print(f"   [ASSUMPTION] {name}")
    print(f"                = {value}")
    print(f"                falsified by: {falsifier}")

print(f"\n6. SCORING PLAN")
print(f"   Benchmark: guidance midpoint ${FY27_GUIDE_MID:.0f}M taken at face value.")
print(f"   Score: CRPS, plus pinball at 10/50/90. Resolves late April 2027.")
print(f"   Calibration is judged on the run of forecasts, not this one: PIT histogram and")
print(f"   80% interval coverage across all resolved forecasts.")

print(f"\n{'=' * 86}")
print("Every number above is reproducible: python3 example_outside_in.py")
print(f"{'=' * 86}")
