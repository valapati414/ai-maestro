"""Commvault Q1 FY2027 (quarter ended June 30, 2026) revenue forecast.

Outside-in, public disclosure only. Built on the FY25/FY26 RECAST quarterly line-item
tables from the Q4 FY26 press release (4/28/26), which restate both years on the
Consolidated Statements of Operations lines effective FY27.

Follows the output contract in SKILL.md. Run from the engine directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# Runnable from the repo root or from this directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

import dpforecast as dp  # noqa: E402

N = 400_000
SEED = 20260728
rng = np.random.default_rng(SEED)
Q = ("Q1", "Q2", "Q3", "Q4")

# ---------------------------------------------------------------------------
# SOURCED: recast quarterly revenue by line, $000s.
# Source: Q4 FY26 press release, "Recast Historical Financial Results".
# https://www.sec.gov/Archives/edgar/data/1169561/000116956126000013/q4fy26pressrelease.htm
# ---------------------------------------------------------------------------
FY25 = {
    "term_license":   np.array([80_405, 84_427, 97_625, 107_954]),
    "term_support":   np.array([39_727, 41_829, 43_047, 44_605]),
    "saas":           np.array([43_675, 49_611, 60_696, 65_274]),
    "perp_license":   np.array([13_736, 10_522, 16_423, 14_962]),
    "perp_support":   np.array([36_561, 35_859, 34_031, 31_904]),
    "other_services": np.array([10_568, 11_030, 10_808, 10_340]),
}
FY26 = {
    "term_license":   np.array([109_282, 92_647, 118_950, 114_445]),
    "term_support":   np.array([47_582, 49_686, 50_962, 53_933]),
    "saas":           np.array([72_445, 80_018, 87_379, 93_139]),
    "perp_license":   np.array([7_335, 12_073, 13_675, 10_129]),
    "perp_support":   np.array([31_439, 30_543, 29_309, 26_972]),
    "other_services": np.array([13_895, 11_221, 13_557, 13_074]),
}
SUB_LINES = ("term_license", "term_support", "saas")
ALL_LINES = SUB_LINES + ("perp_license", "perp_support", "other_services")

for d in (FY25, FY26):
    d["subscription"] = sum(d[k] for k in SUB_LINES)
    d["total"] = sum(d[k] for k in ALL_LINES)

# Integrity check against the reported totals before using any of it.
assert np.allclose(FY26["total"], [281_978, 276_188, 313_832, 311_692])
assert np.allclose(FY25["total"], [224_672, 233_278, 262_630, 275_039])
assert np.allclose(FY26["subscription"], [229_309, 222_351, 257_291, 261_517])
assert FY26["total"].sum() == 1_183_690 and FY25["total"].sum() == 995_619

# Convert to $M for readability
for d in (FY25, FY26):
    for k in list(d):
        d[k] = d[k] / 1000.0

# Guidance issued 4/28/26 on recast definitions
Q1_GUIDE = (263.0, 265.0)
Q1_GUIDE_MID = float(np.mean(Q1_GUIDE))
FY27_TOTAL_GUIDE = (1300.0, 1310.0)

# Subscription guidance midpoint vs actual, six quarters, OLD definition
SUB_GUIDE_MIDS = np.array([145.0, 162.0, 168.0, 175.0, 196.0, 205.0])
SUB_ACTUALS = np.array([158.3, 173.2, 181.7, 172.7, 206.3, 207.6])

# Total ARR balances Q4 FY25 .. Q4 FY26; net-new in constant currency
TOTAL_ARR = np.array([930.051, 996.202, 1043.295, 1084.880, 1121.571])
SAAS_ARR = np.array([281.045, 306.874, 335.669, 363.732, 400.157])
NETNEW_CC = np.array([30.686, 39.642, 47.004, 39.109, 43.733])

rule = "=" * 88


def head(n, title):
    print(f"\n{rule}\nSTEP {n}  {title}\n{rule}")


print(rule)
print("COMMVAULT (CVLT)  Q1 FY2027 — quarter ended June 30, 2026")
print("Outside-in forecast. Recorded 2026-07-28 pre-release; results due 07-28 08:30 EDT.")
print(rule)

# ---------------------------------------------------------------------------
head(1, "The recast: this is the first quarter reported on the new line structure")
# ---------------------------------------------------------------------------
print(f"""
Effective FY27, customer support splits into term-based and perpetual, and term-based
support moves INTO total subscription revenue. Total revenue and Total ARR are untouched.

  FY26 subscription as originally reported   ${FY26['subscription'].sum() - FY26['term_support'].sum():8.1f}M
  FY26 subscription recast                   ${FY26['subscription'].sum():8.1f}M   (+${FY26['term_support'].sum():.1f}M by definition alone)

The year-ago Q1 subscription comparable is ${FY26['subscription'][0]:.1f}M on the recast basis, NOT the
$181.7M originally printed. Anyone using $181.7M computes ~+45% growth against the guide
instead of ~+15%, a {FY26['term_support'].sum() / (FY26['subscription'].sum() - FY26['term_support'].sum()) * 100:.0f}-point artefact.

Commvault guided Q1 FY27 SUBSCRIPTION revenue ${Q1_GUIDE[0]:.0f}-{Q1_GUIDE[1]:.0f}M and a ~19% non-GAAP EBIT
margin. It did NOT guide Q1 total revenue, so total requires forecasting the three
unguided lines as well.""")

# ---------------------------------------------------------------------------
head(2, "Eight quarters of recast history, by line ($M)")
# ---------------------------------------------------------------------------
print(f"\n  {'line':<16}" + "".join(f"{q}'25  " for q in Q) + "".join(f"{q}'26  " for q in Q) + "   FY26 y/y")
for k in ALL_LINES:
    yoy = FY26[k].sum() / FY25[k].sum() - 1
    print(f"  {k:<16}" + "".join(f"{v:6.1f} " for v in FY25[k])
          + "".join(f"{v:6.1f} " for v in FY26[k]) + f"   {yoy*100:+6.1f}%")
print(f"  {'-'*16}" + "-" * 84)
for k in ("subscription", "total"):
    yoy = FY26[k].sum() / FY25[k].sum() - 1
    print(f"  {k:<16}" + "".join(f"{v:6.1f} " for v in FY25[k])
          + "".join(f"{v:6.1f} " for v in FY26[k]) + f"   {yoy*100:+6.1f}%")

print("""
  Read the lines separately, because they behave nothing alike:
    term_support / perp_support / saas   ratable, tight, near-mechanical
    term_license                         point-in-time, swings +/-15% sequentially
    perp_license                         structurally declining and lumpy
    other_services                       small, noisy
  Forecasting a blended growth rate over that mixture is how this quarter gets missed.""")

# ---------------------------------------------------------------------------
head(3, "Baseline BEFORE any driver story (Iron Rule #3)")
# ---------------------------------------------------------------------------
seq_q4_q1 = FY26["total"][0] / FY25["total"][3]
yoy_fy26 = FY26["total"] / FY25["total"] - 1
print(f"""
  FY26 y/y by quarter: {'  '.join(f'{v*100:+.1f}%' for v in yoy_fy26)}   decelerating ~4pt/qtr
  Q4->Q1 sequential:   {(seq_q4_q1-1)*100:+.1f}% (FY25->FY26); FY24->FY25 was +0.6% (n = 2)

  Recorded baseline, timestamped 2026-07-28, before any driver adjustment:
    sequential anchor   ${FY26['total'][3] * 1.0159:.1f}M
    y/y anchor          ${FY26['total'][0] * 1.11:.1f}M""")

# ---------------------------------------------------------------------------
head(4, "METHOD 1 (primary)  Bottom-up by line, each on its own dynamics")
# ---------------------------------------------------------------------------


def seq(line):
    """Q4->Q1 sequential factor, and the within-FY26 sequential factors."""
    return FY26[line][0] / FY25[line][3], FY26[line][1:] / FY26[line][:-1]


draws = {}
print()

# --- SaaS: ratable. Cross-check sequential deceleration against the SaaS ARR balance.
s_q4q1, s_in = seq("saas")
saas_arr_netnew = np.diff(SAAS_ARR)
saas_rev_to_arr = FY26["saas"][0] / (SAAS_ARR[:2].mean() / 4)
saas_arr_q1 = SAAS_ARR[-1] + saas_arr_netnew.mean()
saas_via_arr = saas_rev_to_arr * (SAAS_ARR[-1] + saas_arr_q1) / 2 / 4
saas_via_seq = FY26["saas"][3] * 1.063
SAAS_MU, SAAS_SD = 100.5, 2.0
draws["saas"] = rng.normal(SAAS_MU, SAAS_SD, N)
print(f"  saas          in-year sequentials {'  '.join(f'{v*100-100:+.1f}%' for v in s_in)}, decelerating")
print(f"                sequential view ${saas_via_seq:.1f}M | SaaS-ARR view ${saas_via_arr:.1f}M "
      f"(rev/ARR {saas_rev_to_arr:.3f})")
print(f"                => N({SAAS_MU}, {SAAS_SD})   y/y {SAAS_MU/FY26['saas'][0]*100-100:+.1f}%")

# --- Term support: the most predictable line in the model.
t_q4q1, t_in = seq("term_support")
ts_yoy = FY26["term_support"] / FY25["term_support"] - 1
TS_MU, TS_SD = 56.6, 1.0
draws["term_support"] = rng.normal(TS_MU, TS_SD, N)
print(f"\n  term_support  y/y by quarter {'  '.join(f'{v*100:+.1f}%' for v in ts_yoy)} — remarkably stable")
print(f"                y/y view ${FY26['term_support'][0]*1.19:.1f}M | sequential view "
      f"${FY26['term_support'][3]*1.05:.1f}M  => N({TS_MU}, {TS_SD})")

# --- Term license: the swing factor.
tl_yoy = FY26["term_license"] / FY25["term_license"] - 1
tl_q4q1, tl_in = seq("term_license")
TL_MU, TL_SD = 112.0, 6.5
draws["term_license"] = rng.normal(TL_MU, TL_SD, N)
print(f"\n  term_license  y/y by quarter {'  '.join(f'{v*100:+.1f}%' for v in tl_yoy)} — violently uneven")
print(f"                in-year sequentials {'  '.join(f'{v*100-100:+.1f}%' for v in tl_in)}")
print(f"                Q1 FY26 was a hard comp (+{tl_yoy[0]*100:.0f}%); last two quarters ran "
      f"{tl_yoy[2]*100:+.0f}% and {tl_yoy[3]*100:+.0f}%")
print(f"                => N({TL_MU}, {TL_SD})   y/y {TL_MU/FY26['term_license'][0]*100-100:+.1f}%  "
      f"<-- THE dominant uncertainty")

# --- Perpetual license: structural decline, lumpy, small.
pl_yoy = FY26["perp_license"] / FY25["perp_license"] - 1
PL_MU, PL_SD = 5.8, 1.2
draws["perp_license"] = rng.normal(PL_MU, PL_SD, N)
print(f"\n  perp_license  y/y by quarter {'  '.join(f'{v*100:+.1f}%' for v in pl_yoy)}; FY26 {pl_yoy.mean()*100:+.0f}% avg")
print(f"                Q1 FY26 ${FY26['perp_license'][0]:.1f}M was the year's low "
      f"=> N({PL_MU}, {PL_SD}), wide because the line is erratic")

# --- Perpetual support: steady, predictable decay.
ps_yoy = FY26["perp_support"] / FY25["perp_support"] - 1
PS_MU, PS_SD = 26.7, 0.6
draws["perp_support"] = rng.normal(PS_MU, PS_SD, N)
print(f"\n  perp_support  y/y by quarter {'  '.join(f'{v*100:+.1f}%' for v in ps_yoy)} — a clean -14/-15% decay")
print(f"                every FY26 quarter fell sequentially ({FY26['perp_support'][0]:.1f} -> "
      f"{FY26['perp_support'][3]:.1f})  => N({PS_MU}, {PS_SD})")

# --- Other services.
os_yoy = FY26["other_services"] / FY25["other_services"] - 1
OS_MU, OS_SD = 14.6, 1.0
draws["other_services"] = rng.normal(OS_MU, OS_SD, N)
print(f"\n  other_svcs    y/y by quarter {'  '.join(f'{v*100:+.1f}%' for v in os_yoy)}; Q1 FY26 was the high quarter")
print(f"                => N({OS_MU}, {OS_SD})")

sub_1 = draws["term_license"] + draws["term_support"] + draws["saas"]
resid_1 = draws["perp_license"] + draws["perp_support"] + draws["other_services"]
total_1 = sub_1 + resid_1
print(f"""
  subscription  {TL_MU:.1f} + {TS_MU:.1f} + {SAAS_MU:.1f} = ${sub_1.mean():.1f}M   vs guide ${Q1_GUIDE[0]:.0f}-{Q1_GUIDE[1]:.0f}M
                => an implied beat of ${sub_1.mean()-Q1_GUIDE_MID:+.1f}M, built from the lines rather than assumed
  residual      {PL_MU:.1f} + {PS_MU:.1f} + {OS_MU:.1f} = ${resid_1.mean():.1f}M
  TOTAL         ${total_1.mean():.1f}M, sd ${total_1.std(ddof=1):.1f}M""")

# ---------------------------------------------------------------------------
head(5, "METHOD 2  The guided line plus the fitted realization pattern")
# ---------------------------------------------------------------------------
beats = SUB_ACTUALS - SUB_GUIDE_MIDS
ratios = SUB_ACTUALS / SUB_GUIDE_MIDS
print("\n  Subscription guide midpoint vs actual, OLD definition ($M):")
for g, a, b, r in zip(SUB_GUIDE_MIDS, SUB_ACTUALS, beats, ratios):
    print(f"    guide {g:6.1f}   actual {a:6.1f}   beat {b:+6.1f}   ratio {r:.4f}"
          + ("   <- the only miss" if b < 0 else ""))
print(f"\n  ratio form:  mean {ratios.mean():.4f}  sd {ratios.std(ddof=1):.4f}")
print(f"  dollar form: mean {beats.mean():+.2f}  sd {beats.std(ddof=1):.2f}")
print(f"""
  Use the dollar form. The beats originate in term-license revenue, recognized at a point in
  time, which is also the documented cause of the single miss (term license fell
  ${FY26['term_license'][0]:.1f}M -> ${FY26['term_license'][1]:.1f}M into Q2 FY26). That is a dollar phenomenon driven by deal
  timing, not a percentage of whatever base it happens to sit in. The recast did not touch
  term license; it folded in term SUPPORT, which is ratable and near-mechanical. So applying
  the {ratios.std(ddof=1)*100:.1f}% ratio sd to the bigger recast base would overstate the risk, because the
  volatile component is now a smaller share of the line.

  Centre below the {beats.mean():.1f} full-history mean: the last two quarters beat by only
  {beats[-2]:+.1f} and {beats[-1]:+.1f}, and this is the first quarter guided on new definitions.""")
BEAT_MU, BEAT_SD = 6.0, 7.0
sub_2 = rng.uniform(*Q1_GUIDE, N) + rng.normal(BEAT_MU, BEAT_SD, N)
total_2 = sub_2 + resid_1
print(f"\n  beat ~ N({BEAT_MU}, {BEAT_SD})  =>  subscription ${sub_2.mean():.1f}M   total ${total_2.mean():.1f}M")

# ---------------------------------------------------------------------------
head(6, "METHOD 3  ARR balance x conversion factor — and why it is weak quarterly")
# ---------------------------------------------------------------------------
arr_borne = {}
k_q = []
for i in range(4):
    ab = FY26["total"][i] - FY26["perp_license"][i] - FY26["other_services"][i]
    avg = (TOTAL_ARR[i] + TOTAL_ARR[i + 1]) / 2
    arr_borne[i] = ab
    k_q.append(ab / (avg / 4))
k_q = np.array(k_q)
k_fy26 = (FY26["total"].sum() - FY26["perp_license"].sum() - FY26["other_services"].sum()) / (
    (TOTAL_ARR[0] / 2 + TOTAL_ARR[1:4].sum() + TOTAL_ARR[4] / 2) / 4)
print(f"""
  Total ARR excludes perpetual license and professional services but INCLUDES support on both
  perpetual and term licenses. So ARR-borne revenue = total - perp license - other services.

    quarterly k in FY26:  {'  '.join(f'{v:.4f}' for v in k_q)}
    mean {k_q.mean():.4f}   sd {k_q.std(ddof=1):.4f}   full-year k {k_fy26:.4f}

  That sd is the finding. k swings from {k_q.min():.3f} to {k_q.max():.3f} across four quarters purely on
  term-license timing, so at a QUARTERLY horizon this method carries roughly
  ${k_q.std(ddof=1) * 285:.0f}M of noise from k alone. It is a sanity check, not a forecast. Q1 FY26's
  {k_q[0]:.3f} is the high-water mark and should not be reused as a Q1 seasonal constant.""")
K_MU, K_SD = float(k_q.mean()), float(k_q.std(ddof=1))
NETNEW_MU, NETNEW_SD = 40.0, 7.0
netnew = rng.normal(NETNEW_MU, NETNEW_SD, N)
avg_arr_q1 = (TOTAL_ARR[-1] + (TOTAL_ARR[-1] + netnew)) / 2
total_3 = rng.normal(K_MU, K_SD, N) * avg_arr_q1 / 4 + draws["perp_license"] + draws["other_services"]
print(f"  net-new Total ARR ~ N({NETNEW_MU}, {NETNEW_SD}) (CC history mean ${NETNEW_CC.mean():.1f}M) => "
      f"avg ARR ${avg_arr_q1.mean():.0f}M")
print(f"  k ~ N({K_MU:.4f}, {K_SD:.4f})  =>  total ${total_3.mean():.1f}M, sd ${total_3.std(ddof=1):.1f}M")

# ---------------------------------------------------------------------------
head(7, "METHOD 4  Sequential seasonality, METHOD 5  y/y deceleration")
# ---------------------------------------------------------------------------
total_4 = FY26["total"][3] * rng.normal(1.0159, 0.0190, N)
total_5 = FY26["total"][0] * rng.normal(1.105, 0.020, N)
print(f"""
  4: Q4 FY26 ${FY26['total'][3]:.1f}M x N(1.0159, 0.0190) => ${total_4.mean():.1f}M
     Caveat: Q4 FY26 (${FY26['total'][3]:.1f}M) came in BELOW Q3 (${FY26['total'][2]:.1f}M), so FY26 broke the
     usual Q4-peak shape and this base is softer than the seasonal story assumes. n = 2.
  5: Q1 FY26 ${FY26['total'][0]:.1f}M x N(1.105, 0.020) => ${total_5.mean():.1f}M
     Weakest: FY26 carried a $29.5M FX tailwind, so y/y extrapolation is unreliable.""")

# ---------------------------------------------------------------------------
head(8, "Combine as a mixture")
# ---------------------------------------------------------------------------
methods = {
    "1 bottom-up by line": (total_1, 0.35),
    "2 guide + realization": (total_2, 0.30),
    "3 ARR x k": (total_3, 0.10),
    "4 sequential": (total_4, 0.15),
    "5 y/y deceleration": (total_5, 0.10),
}
print("\n  Mixed, not averaged: these are different stories about the quarter.\n")
for name, (arr, wt) in methods.items():
    print(f"    {wt:>5.0%}  {name:<22} median ${np.median(arr):7.1f}M   sd ${arr.std(ddof=1):5.1f}M")
stack = np.vstack([m[0] for m in methods.values()])
pick = rng.choice(len(methods), N, p=[m[1] for m in methods.values()])
total = stack[pick, np.arange(N)]
sub = np.where(pick == 1, sub_2, sub_1)

q_t = dp.quantiles(total, (0.10, 0.25, 0.50, 0.75, 0.90))
q_s = dp.quantiles(sub, (0.10, 0.50, 0.90))
meds = [np.median(m[0]) for m in methods.values()]
print(f"\n  Method medians span ${min(meds):.1f}M to ${max(meds):.1f}M = ${max(meds)-min(meds):.1f}M of model disagreement.")
print("  The three best-supported methods (1, 2, 4) agree within $2M, which is the real signal here.")

# ---------------------------------------------------------------------------
head(9, "Sensitivity")
# ---------------------------------------------------------------------------


def total_from(p):
    return (p["term_license"] + p["term_support"] + p["saas"]
            + p["perp_license"] + p["perp_support"] + p["other_services"])


base = {"term_license": TL_MU, "term_support": TS_MU, "saas": SAAS_MU,
        "perp_license": PL_MU, "perp_support": PS_MU, "other_services": OS_MU}
ranges = {"term_license": (100.0, 125.0), "term_support": (55.0, 58.0), "saas": (97.0, 104.0),
          "perp_license": (4.0, 8.0), "perp_support": (25.5, 27.5), "other_services": (13.0, 16.2)}
levers = dp.rank_levers(total_from, base, ranges)
print()
for lv in levers:
    print(f"    {lv.name:<16}{lv.low_value:6.1f} to {lv.high_value:6.1f}   moves total "
          f"${lv.swing:5.1f}M  ({lv.swing/np.median(total)*100:4.1f}%)")
print(f"""
  Term license alone is worth more than the other five lines combined. This forecast is, in
  substance, a single-variable bet on point-in-time term-license recognition — which is the
  same variable that produced Commvault's only recent guidance miss. Everything ratable
  (${TS_MU+SAAS_MU+PS_MU:.0f}M of the ${np.median(total):.0f}M, or {(TS_MU+SAAS_MU+PS_MU)/np.median(total)*100:.0f}%) is close to mechanical.""")

# ---------------------------------------------------------------------------
head(10, "THE OUTPUT CONTRACT")
# ---------------------------------------------------------------------------
face_value = Q1_GUIDE_MID + resid_1.mean()
ratable = TS_MU + SAAS_MU + PS_MU
print(f"""
1. HEADLINE
   Q1 FY27 TOTAL revenue         median ${np.median(total):.0f}M    80% interval ${q_t['p10']:.0f}M to ${q_t['p90']:.0f}M
   Q1 FY27 SUBSCRIPTION revenue  median ${np.median(sub):.0f}M    80% interval ${q_s['p10']:.0f}M to ${q_s['p90']:.0f}M
   Implied total y/y        {np.median(total)/FY26['total'][0]*100-100:+.1f}%   (vs ${FY26['total'][0]:.1f}M)
   Implied subscription y/y {np.median(sub)/FY26['subscription'][0]*100-100:+.1f}%   (vs recast ${FY26['subscription'][0]:.1f}M)

   Company guided subscription ${Q1_GUIDE[0]:.0f}-{Q1_GUIDE[1]:.0f}M; no total-revenue guide was given.
   P(subscription above the guide high end) = {float((sub > Q1_GUIDE[1]).mean())*100:.0f}%
   P(subscription below the guide low end)  = {float((sub < Q1_GUIDE[0]).mean())*100:.0f}%
   P(total above ${face_value:.0f}M, guidance at face value) = {float((total > face_value).mean())*100:.0f}%

2. THE SPLIT
   Ratable / near-mechanical   ${ratable:6.1f}M   {ratable/np.median(total)*100:.0f}% of total — term support, SaaS, perpetual support
   Point-in-time / at risk     ${TL_MU+PL_MU+OS_MU:6.1f}M   {(TL_MU+PL_MU+OS_MU)/np.median(total)*100:.0f}% of total — term + perpetual license, services
   Effectively all of the interval width sits in the point-in-time block.

3. DECOMPOSITION
   term license   {TL_MU:6.1f}   +{TL_MU/FY26['term_license'][0]*100-100:.0f}% y/y   point-in-time, the swing factor
   term support   {TS_MU:6.1f}   +{TS_MU/FY26['term_support'][0]*100-100:.0f}% y/y   ratable
   SaaS           {SAAS_MU:6.1f}   +{SAAS_MU/FY26['saas'][0]*100-100:.0f}% y/y   ratable
   = subscription {TL_MU+TS_MU+SAAS_MU:6.1f}   vs guide midpoint {Q1_GUIDE_MID:.0f}, a {TL_MU+TS_MU+SAAS_MU-Q1_GUIDE_MID:+.1f} implied beat
   perp license   {PL_MU:6.1f}   {PL_MU/FY26['perp_license'][0]*100-100:+.0f}% y/y   structural decline
   perp support   {PS_MU:6.1f}   {PS_MU/FY26['perp_support'][0]*100-100:+.0f}% y/y   clean decay
   other services {OS_MU:6.1f}   {OS_MU/FY26['other_services'][0]*100-100:+.0f}% y/y
   = TOTAL        {total_1.mean():6.1f}

4. MOST SENSITIVE ASSUMPTIONS""")
for lv in levers[:3]:
    print(f"   {lv.name:<16}{lv.low_value:6.1f} to {lv.high_value:6.1f}   moves total ${lv.swing:.1f}M "
          f"({lv.swing/np.median(total)*100:.1f}%)")

print(f"""
5. ASSUMPTION REGISTER   (all recast history is SOURCED; these are the judgements)
   [ASSUMPTION] term license = ${TL_MU:.1f}M ({TL_MU/FY26['term_license'][0]*100-100:+.1f}% y/y), sd {TL_SD}
                basis: FY26 y/y ran +36/+10/+22/+6%, decelerating off a hard Q1 comp
                falsified by: a print outside $100-125M
   [ASSUMPTION] SaaS = ${SAAS_MU:.1f}M ({SAAS_MU/FY26['saas'][0]*100-100:+.1f}% y/y), sd {SAAS_SD}
                falsified by: SaaS outside $97-104M, or SaaS ARR outside $425-435M
   [ASSUMPTION] term support = ${TS_MU:.1f}M (+{TS_MU/FY26['term_support'][0]*100-100:.1f}% y/y), sd {TS_SD}
                falsified by: a print outside $55-58M — would mean the term base moved
   [ASSUMPTION] perpetual support = ${PS_MU:.1f}M ({PS_MU/FY26['perp_support'][0]*100-100:+.1f}% y/y), sd {PS_SD}
                falsified by: outside $25.5-27.5M, breaking a clean 8-quarter decay
   [ASSUMPTION] perpetual license = ${PL_MU:.1f}M, sd {PL_SD}; erratic line, deliberately wide
   [ASSUMPTION] other services = ${OS_MU:.1f}M, sd {OS_SD}
   [ASSUMPTION] beat mu = {BEAT_MU} for Method 2 (fitted {beats.mean():.2f}, shaded to recent quarters)
   [ASSUMPTION] net-new Total ARR = ${NETNEW_MU:.0f}M for Method 3
                falsified by: Total ARR at 6/30/26 outside $1,150-1,175M
   [ASSUMPTION] method weights {tuple(m[1] for m in methods.values())} — a judgement about model
                quality, falsifiable by nothing observable
   NOT MODELLED: FX. FY26 carried a $29.5M reported tailwind. A sharp move either way in
                Apr-Jun 2026 sits outside this interval.

6. SCORING PLAN
   Resolves: Q1 FY27 press release, 2026-07-28 08:30 EDT (hours away).
   Benchmark: guidance at face value, ${face_value:.0f}M total = guide midpoint {Q1_GUIDE_MID:.0f} + residual
              {resid_1.mean():.1f}, treated as N({face_value:.0f}, 6.5).
   Score: CRPS on total revenue; pinball loss at p10/p50/p90; and record the realization
          ratio to refit the beat distribution before Q2.
   Quantiles to be scored ($M):
     total        p10 {q_t['p10']:.1f}   p25 {q_t['p25']:.1f}   p50 {q_t['p50']:.1f}   p75 {q_t['p75']:.1f}   p90 {q_t['p90']:.1f}
     subscription p10 {q_s['p10']:.1f}   p50 {q_s['p50']:.1f}   p90 {q_s['p90']:.1f}
   This beats the benchmark only if the beat pattern holds. If Commvault has genuinely
   tightened its guidance process, the naive benchmark wins and the fitted realization
   distribution should be rebuilt with the new observation.

   Consistency with the FY27 guide. Multiplying Q1 by four is the wrong check, because Q1 is
   seasonally the weakest quarter. Use the observed Q1 share of the full year instead:
     Q1 share of FY   FY25 {FY25['total'][0]/FY25['total'].sum()*100:.1f}%   FY26 {FY26['total'][0]/FY26['total'].sum()*100:.1f}%   (drifting up as ratable SaaS
                      flattens the seasonal curve)
     at a {FY26['total'][0]/FY26['total'].sum()*100:.1f}% share, ${np.median(total):.0f}M implies FY27 of ${np.median(total)/(FY26['total'][0]/FY26['total'].sum()):.0f}M
     at a 24.5% share, it implies ${np.median(total)/0.245:.0f}M
     at a 25.0% share, it implies ${np.median(total)/0.250:.0f}M
   Against guidance of ${FY27_TOTAL_GUIDE[0]:.0f}-{FY27_TOTAL_GUIDE[1]:.0f}M, that band straddles the guide rather than
   contradicting it. So this Q1 forecast does NOT require the FY27 guide to be wrong — a
   useful check, because a quarterly call that silently implies a large annual beat is usually
   a quarterly call with an error in it.
""")
