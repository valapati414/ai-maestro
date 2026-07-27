# storage_revenue_prediction

A forecasting skill and runnable engine for predicting revenue, ARR, bookings, and operating
profit at enterprise data-protection, backup, and storage-software vendors — Veeam, Commvault,
Cohesity, Rubrik, Veritas, Druva, Dell PowerProtect, IBM Storage Defender.

It is packaged as an [agent skill](#using-it-as-an-agent-skill), but the engine is a plain
Python library and the references are plain Markdown, so it is equally usable by hand.

## Why this exists

Forecasting a backup vendor is not a growth-rate extrapolation. It is a four-stage identity
chain, plus an explicit statement of what you do not know:

```
demand signal → pipeline → BOOKINGS (ACV/ARR, TCV) → BILLINGS → REVENUE (ASC 606) → CASH
```

Almost every large forecast error in this category comes from one of two things: silently
mixing two links of that chain, or reporting a point estimate for a quantity that is genuinely
a distribution. This repo exists to prevent both.

The core principle is that **the recurring base is highly predictable and the incremental layer
is not**. A vendor with $1.1B of ARR and $300M of at-risk new business does not have "one"
forecast uncertainty — it has almost none on 83% of next year's revenue and a lot on the rest.
Separate them, forecast them differently, and report the split.

## Quick start

```bash
pip install -r requirements.txt

cd engine
python3 dpforecast.py          # API summary
python3 test_dpforecast.py     # self-test suite, all must pass
python3 example_outside_in.py  # full worked Commvault FY27 forecast, end to end
```

Then read [`SKILL.md`](./SKILL.md) — it holds the Iron Rules, the approach decision graph, the
12-step procedure, and the output contract.

**Read the worked example before writing your own forecast.** It is the fastest way to
understand what this repo is for.

## What's here

| Path | Contents |
|---|---|
| [`SKILL.md`](./SKILL.md) | The method: Iron Rules, decision graph, 12-step procedure, output contract, ranked lever table |
| `engine/dpforecast.py` | The forecasting engine — numpy only, scipy optional |
| `engine/example_outside_in.py` | Worked Commvault FY27 forecast from public filings, emitting the full output contract |
| `engine/test_dpforecast.py` | Self-tests; every numeric claim checked against a closed form or a recovery experiment |
| `references/variable-taxonomy.md` | Every forecast variable, its measure type, source, and where it enters |
| `references/with-order-flow.md` | CRM/channel/entitlement schemas, pipeline conversion, judgmental calibration, deal-list Monte Carlo, nowcasting |
| `references/without-order-flow.md` | Outside-in procedure from public disclosure only, with reconciliation checks |
| `references/probability-and-calibration.md` | Measuring predictability, calibrated distributions, proper scoring, backtesting, judgmental debiasing |
| `references/demand-drivers-and-alt-data.md` | Market sizing, named catalysts with proxy series, alt-data with honest predictive value |
| `references/profit-levers.md` | Margin structure, unit economics, ranked sensitivity table, driver-based P&L and FCF bridge |
| `references/company-profiles.md` | Sourced financials, definitions, guidance history, seasonality, comparability traps per vendor |
| `tests/test_skill_integrity.py` | Guards the repo's structure and the engine's dependency constraints |

## The Iron Rules

1. **Never sum across measure types.** ACV, ARR, TCV, billings, revenue, and cash are five
   different quantities. `TCV = ACV × term_years`, so a shift from 1-year to 3-year terms
   triples reported TCV bookings with zero change in ARR.
2. **Never output a point estimate alone.** Every forecast ships with quantiles, the method
   used to produce them, and the score you will grade yourself with. A number without an
   interval is an opinion.
3. **Baseline first, story second.** Write down the autocorrelation-implied growth *before*
   reading any driver research, and timestamp it.
4. **Cite or label.** Every input is either sourced (URL + period) or explicitly tagged
   `[ASSUMPTION]`. There is no third category.
5. **ARR growth is not revenue growth.** The wedge is accounting, and its sign flips depending
   on where the vendor sits in its recognition transition.

## What actually moves the needle

Ranked for a ~$1.2B-revenue vendor at ~81% gross margin and ~72% opex ratio. Full arithmetic in
[`references/profit-levers.md`](./references/profit-levers.md).

| Lever | Realistic 1-yr move | Revenue | Operating margin | Confidence |
|---|---|---|---|---|
| Opex growth vs revenue growth gap | 0–10 pts | none | **+0.60 pt per pt of gap** | High (identity) |
| Price / renewal uplift | +1 to +3 pts | +1.0 to +3.0% | +0.95 to +2.85 pts | High on math |
| Channel discount discipline | 1 pt off a 30% discount | +1.43% | +1.36 pts | Medium |
| Payment terms → multi-year prepaid | 10% of ARR | **zero** | one-time FCF ≈ +$240M | High on math |
| SaaS gross margin | +3 to +10 pts | none | +0.8 to +2.8 pts | Medium-High |
| Cross-sell instead of new logo | shift $50M net-new ARR | none | +2.7 pts (S&M saved) | Medium |
| NRR ±5 pts | 117%↔127% | yr-1 ±0.85% | 3-yr ARR ±$179M | Medium-High |
| Term-license → SaaS mix | +10 pts of mix | reported growth **−8.5 pts** | gross margin −3.3 pts | High |
| GRR ±2 pts | 88%↔92% | yr-1 ∓1% | **terminal value +11%/−9%** | Medium |
| FX | ±3 pts | disclosed, material | partial natural hedge | High |

Two lessons hide in that table. Most "growth" levers are slow-fuse valuation levers with small
first-year P&L effects, while the fastest levers (opex gap, price, discount, payment terms) are
operating decisions with no demand content at all. And the largest single mover of *reported*
revenue growth — the term-license-to-SaaS mix shift — changes no economics whatsoever.

## The worked example, and why it matters

`engine/example_outside_in.py` forecasts Commvault FY27 total revenue from public filings only.
It lands at a median of $1,343M against management's $1,300–1,310M guide — but it is **not** a
demand call. The model's ARR forecast is slightly *below* what management's own ARR guidance
implies.

The entire disagreement reduces to one accounting variable. Management's revenue guide and its
own ARR guide are only mutually consistent if the ARR-to-revenue conversion factor collapses
from 1.049 to 1.007 in a single year — a 4.2-point drop. The model has it falling 1.2 points,
which is what the measurable SaaS mix shift (32% → 39% of average ARR) mechanically produces.

Finding out that your disagreement is about revenue recognition rather than about the business
is the normal outcome in this category. Step 7c of the example shows the arithmetic that
surfaces it.

## Using it as an agent skill

`SKILL.md` carries standard skill frontmatter (`name`, `description`), so the repo can be
dropped into an agent's skills directory:

```bash
git clone https://github.com/<owner>/storage_revenue_prediction.git \
  ~/.claude/skills/data-protection-revenue-forecasting
```

Adjust the destination for your agent runtime — anything that discovers `SKILL.md` frontmatter
will pick it up. The `description` field is what an agent sees when deciding whether to load
the skill, which is why it stays specific and third-person.

## Requirements

Python 3.9+ and numpy. scipy is optional — the engine uses it for the normal CDF when present
and falls back to a built-in approximation when not, so results are the same either way.

This constraint is deliberate and enforced by `tests/test_skill_integrity.py`: pandas, sklearn,
statsmodels, and matplotlib are all rejected, because the engine's value depends on running
anywhere without a data-science stack.

## Scope and disclaimer

This is a forecasting method and a reference implementation. The company figures in
`references/company-profiles.md` and the worked example are sourced from public filings as of
the dates noted in those files, and they go stale. Nothing here is investment advice.

## License

MIT. See [LICENSE](./LICENSE).
