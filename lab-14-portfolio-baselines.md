# Lab 14 — Portfolio Baselines

**Course:** FIN 43900, Fall 2026 · **Student:** Shrey · **Partner (from Lab 13):** Ethan Heeres

**Files in this submission**

| File | What it is |
|---|---|
| `portfolio.py` | the risk engine: covariance matrix, three baselines, correlation check |
| `mandate.py` | Lab 13 checker, now with candidate E (the benchmark) |
| `lab-14-portfolio-baselines.md` | this file: verification, explanations, reflection, Project 2 funds |
| `get_prices.py` / `prices.csv` | five years of monthly Adj Close for my Project 2 funds |

Run: `python portfolio.py` · `python mandate.py`

---

## D — the question

> **What does each simple portfolio earn and risk — and does any of them meet the Meridian mandate?**

**Short answer:** Only the benchmark earns the 6.5% objective (6.80%), but it holds 0% in
reserve-eligible assets, so it fails Meridian's reserve rule. Equal weight and inverse volatility
hold plenty of reserve but earn 5.20% and 3.77%, below the objective. **None of the three simple
baselines meets the full mandate.** That's the reason to build an optimizer on Thursday instead of
picking one of these.

### Why two risky assets together can be less risky than either alone (partner explanation)

The benchmark's two parts have volatilities of 6% and 16%. If they moved in lockstep (correlation
+1), a 40/60 mix would have 0.40 × 6 + 0.60 × 16 = **12.0%** volatility, just a weighted
average. Their correlation is only 0.25, so in some years bonds are up when equity is down and the
two partly offset each other. The cross term 2·w₁·w₂·ρ·σ₁·σ₂ shrinks, and the mix comes out at
**10.46%**, about 1.5 points below the weighted average. When correlation is low enough, the mix can even
be less risky than the safer asset alone.

---

## R — inputs (course-authored training values, not market estimates)

| Sleeve | Expected return | Volatility | Reserve-eligible |
|---|---:|---:|---|
| Treasury bills | 3.5% | 0.5% | yes |
| Treasury 10-year note | 4.3% | 7.0% | yes |
| Investment-grade bond fund | 5.0% | 6.0% | no |
| Global equity index fund | 8.0% | 16.0% | no |

Correlation table as given in the lab. Objective = CPI 2.5% (**labelled estimate**) + 4% = **6.5%**.

---

## I — the engine

`portfolio.py`, standard library only. Each calculation is its own function
(`covariance_matrix`, `portfolio_return`, `portfolio_variance`, `portfolio_volatility`,
`reserve_eligible_weight`, `meets_objective`, the three weight builders), so Thursday's `app.py`
can `from portfolio import ...`. `validate_correlation` runs before anything is computed and
refuses a table with values outside −1 to 1, a non-1 diagonal, or asymmetry.

**Line I understood least:** `total += weights[i] * weights[j] * cov[i][j]` inside the
double loop. *Quiz question:* "Why loop over every (i, j) pair instead of only i < j?"
*My answer:* because the full matrix contains both cov[i][j] and cov[j][i], which are equal, and
together they give the "2 × w₁w₂ × covariance" term. The diagonal (i = j) gives w²σ². Looping
over i < j only would need an explicit ×2 and a separate diagonal sum.

---

## V — prove it on the known answer

Output of `python portfolio.py`:

```
Objective: 6.50% (CPI 2.5% estimate + 4%)
Weights order: bills / 10-year / IG / equity

Portfolio           Weights (%)                   Return     Vol  Reserve  Meets?
---------------------------------------------------------------------------------
Benchmark           0.0 / 0.0 / 40.0 / 60.0        6.80%  10.46%     0.0%  yes
Equal weight        25.0 / 25.0 / 25.0 / 25.0      5.20%   5.21%    50.0%  no
Inverse volatility  84.3 / 6.0 / 7.0 / 2.6         3.77%   1.05%    90.3%  no
```

| Portfolio | Weights | Return | Volatility | Reserve | Meets 6.5%? | Matches key? |
|---|---|---:|---:|---:|---|---|
| Benchmark | 0.0 / 0.0 / 40.0 / 60.0 | 6.80 | 10.46 | 0.0 | yes | ✅ |
| Equal weight | 25.0 / 25.0 / 25.0 / 25.0 | 5.20 | 5.21 | 50.0 | no | ✅ |
| Inverse volatility | 84.3 / 6.0 / 7.0 / 2.6 | 3.77 | 1.05 | 90.3 | no | ✅ |

Every value matches. The engine does **not** give 9.90% for the benchmark, so the correlation
term is included.

**Prove it computes.** IG–equity correlation set to `0.50` in both cells:

```
Benchmark           0.0 / 0.0 / 40.0 / 60.0        6.80%  11.00%     0.0%  yes
```

Volatility rose from 10.46% to **11.00%** as expected (return unchanged, since correlation only
affects risk). Set back to 0.25.

### Explain the code (no AI)

The volatility block:

```python
def covariance_matrix(corr, vols):
    n = len(vols)
    return [[corr[i][j] * vols[i] * vols[j] for j in range(n)] for i in range(n)]

def portfolio_variance(weights, cov):
    n = len(weights)
    total = 0.0
    for i in range(n):
        for j in range(n):
            total += weights[i] * weights[j] * cov[i][j]
    return total

def portfolio_volatility(weights, cov):
    return math.sqrt(portfolio_variance(weights, cov))
```

Line by line:

1. `covariance_matrix`: for every pair of sleeves, covariance = ρᵢⱼ × σᵢ × σⱼ. On the diagonal
   ρ = 1, so it is just σᵢ² (the variance of that sleeve).
2. `total = 0.0`: start the running sum of variance.
3. The two `for` loops visit every cell of the 4 × 4 matrix (16 cells).
4. `weights[i] * weights[j] * cov[i][j]`: how much each pair contributes. Diagonal cells give
   w²σ²; off-diagonal cells come in matching pairs, which together give the 2·wᵢwⱼ·covᵢⱼ term.
5. `portfolio_volatility` takes the square root, because variance is in squared units (%²) and
   volatility is back in % per year.

Question I'd expect from my partner: *"What happens if a weight is zero?"* From the code: every
term with that weight multiplies to 0, so the sleeve drops out. That's why the benchmark only
uses the IG and equity cells.

### Swap and break

Correlation IG–equity set to `1.3` in both cells → the engine **refuses**:

```
REFUSED: Correlation table rejected:
  - Investment-grade bond fund / Global equity index fund = 1.3 is outside -1 to 1
  - Global equity index fund / Investment-grade bond fund = 1.3 is outside -1 to 1
Fix the correlation table at the top of portfolio.py and rerun.
```

Also tested asymmetry (0.25 in one cell, 0.30 in the other) → refuses with "not symmetric".
Undone afterward; the file in this repo has the original table.

Ethan's engine: same three rows; refused 1.3.

### Read it — benchmark through the mandate checker

Added candidate E (40 IG bond fund, 60 global equity fund) to `mandate.py`:

```
Candidate E
  Weights sum to 100                  100.0  pass
  Long-only (lowest weight)             0.0  pass
  Reserve-eligible >= 3.0%              0.0  FAIL
  Redeemable in 5 days >= 90%         100.0  pass
  Largest single company <= 8%          0.0  pass
  Calendar-year loss <= 10%          requires CIO clarification
  Verdict: fails 1 rule(s)
```

**The client's own benchmark breaks the client's mandate**: it holds 0.0% in reserve-eligible
assets against a 3.0% minimum (four quarters × $0.75M ÷ $100M). Even moving 3 points from IG
bonds to T-bills would fix that rule. That's a small change that a benchmark-relative CIO should
see before anyone optimizes.

Lab 13 results still reproduce: A passes every checkable rule; B fails 3; C fails 1; D (my
90% equity attack) passes every checkable rule.

---

## Floor checklist

- [x] Engine matches the known answer (all 3 rows)
- [x] Correlation 0.50 → 11.00%
- [x] Refuses a bad correlation (1.3) and an asymmetric table
- [x] Benchmark run through the mandate checker as E → fails reserve at 0.0%

---

## Diversification — learn on my own

**1. What is it?** Spreading money across assets whose returns don't move in perfect step, so the
portfolio's risk is lower than the weighted average of the parts' risks.

**2. How does it work?** Portfolio variance = Σ wᵢ²σᵢ² + Σᵢ≠ⱼ wᵢwⱼρᵢⱼσᵢσⱼ. The second part is
the co-movement term. With ρ = +1, volatility is exactly the weighted average of volatilities,
so there is no benefit. Any ρ below +1 makes the cross term smaller than in that worst case, so
volatility falls below the weighted average; with ρ ≤ 0, some of the movements actively cancel.
It reduces issuer-specific risk but can't remove systematic risk that every asset shares, and the
benefit shrinks with each asset added. Correlations estimated from history are not guaranteed,
and in a crisis they often rise toward +1.

**3. The benchmark by hand** (40% IG: 5.0%, 6.0% · 60% equity: 8.0%, 16.0% · ρ = 0.25)

| Step | Work | Result |
|---|---|---|
| Expected return | 0.40 × 5.0 + 0.60 × 8.0 = 2.0 + 4.8 | **6.80%** |
| Covariance | 0.25 × 0.06 × 0.16 | 0.0024 |
| Bond term | 0.40² × 0.06² = 0.16 × 0.0036 | 0.000576 |
| Equity term | 0.60² × 0.16² = 0.36 × 0.0256 | 0.009216 |
| Cross term | 2 × 0.40 × 0.60 × 0.0024 | 0.001152 |
| Variance | 0.000576 + 0.009216 + 0.001152 | 0.010944 |
| Volatility | √0.010944 | **10.46%** |
| Classic error (no cross term) | √(0.000576 + 0.009216) = √0.009792 | 9.90% |
| If ρ = +1 (no diversification) | 0.40 × 6 + 0.60 × 16 | 12.00% |

Diversification benefit vs. ρ = +1: 12.00 − 10.46 = **1.54 points** of volatility.

---

## Reflect

**1. Why inverse volatility piles into bills.** Each weight is 1 ÷ volatility. Bills' volatility is
0.5%, so 1 ÷ 0.005 = 200, while the other three give 14.3, 16.7 and 6.25. Bills are 200 of the
237.2 total, or **84.3%**. The rule only looks at each sleeve's own risk, not at return or at the
objective, so it chases the lowest-risk asset. The result is very low risk (1.05%), but 3.77%
return is far below the 6.5% objective. It also ignores correlation entirely, so it isn't the true
minimum-variance mix either.

**2. Which baseline I'd show the CIO first, and why.** The **benchmark**, because it is the CIO's
own reference point (S4) and the only one that earns the objective. Showing it first makes the
key issue clear right away: the client's own 60/40 fails the client's own reserve rule. So the
real job is a small, explainable change from the benchmark (carve 3%+ into T-bills/10-year and see
what that costs in return and saves in volatility), not a new portfolio built from scratch. Equal
weight and inverse volatility are useful as contrasts, since both are safer but miss the return
target.

---

## Before Thursday — my Project 2 universe, in funds

My Project 2 client (fictional): a small family charitable fund with a CPI + 3% real-return goal,
a one-year cash reserve for grants, and an explicit concern about inflation eroding its grants.
Roles needed: cash/reserve, government bonds, investment-grade credit, inflation protection,
global equity.

| Role | Ticker | Fund name |
|---|---|---|
| Cash and reserve | BIL | SPDR Bloomberg 1-3 Month T-Bill ETF |
| Government bonds | IEF | iShares 7-10 Year Treasury Bond ETF |
| Fixed income (IG credit) | LQD | iShares iBoxx $ Investment Grade Corporate Bond ETF |
| Inflation protection | TIP | iShares TIPS Bond ETF |
| Equity | VT | Vanguard Total World Stock ETF |

No money market funds (their price sits at $1.00); BIL stands in for cash.

**Price data** — `prices.csv`

| Item | Value |
|---|---|
| Source | Yahoo Finance → Historical Data → Monthly, **Adj Close** column (includes distributions) |
| Tickers | BIL, IEF, LQD, TIP, VT |
| Window | five years of monthly prices, oldest month first |
| Layout | `Date`, then one column per ticker |
| Built with | `python get_prices.py` (yfinance, `auto_adjust=False`, `interval="1mo"`) |
| Download date | _see `prices_source.txt`_ |

These are historical prices: a five-year average is history, not a forecast.
