"""portfolio.py - risk engine for the Meridian Foundation Reserve (Lab 14).

Standard library only. Run:  python portfolio.py

Inputs are course-authored training values, not market estimates.
Every result is computed from the inputs; no answer is typed in.
Each calculation is its own function so app.py (Lab 15) can import them.
"""

import math
import sys

# ---------------------------------------------------------------------------
# Editable inputs (training values)
# ---------------------------------------------------------------------------

SLEEVES = ["Treasury bills", "Treasury 10-year note",
           "Investment-grade bond fund", "Global equity index fund"]

# expected return and volatility, as decimals
EXPECTED_RETURN = {
    "Treasury bills": 0.035,
    "Treasury 10-year note": 0.043,
    "Investment-grade bond fund": 0.050,
    "Global equity index fund": 0.080,
}
VOLATILITY = {
    "Treasury bills": 0.005,
    "Treasury 10-year note": 0.070,
    "Investment-grade bond fund": 0.060,
    "Global equity index fund": 0.160,
}

# correlation matrix, rows and columns in SLEEVES order
CORRELATION = [
    #  Bills  10-yr   IG    Equity
    [1.00,  0.10,  0.05,  0.00],   # Bills
    [0.10,  1.00,  0.80, -0.10],   # 10-year
    [0.05,  0.80,  1.00,  0.25],   # IG bonds
    [0.00, -0.10,  0.25,  1.00],   # Equity
]

# CPI + 4% with CPI = 2.5% (labelled estimate)
OBJECTIVE_RETURN = 0.065

RESERVE_ELIGIBLE = {"Treasury bills", "Treasury 10-year note"}

TOLERANCE = 1e-12


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_correlation(corr, names):
    """Return a list of problems; empty list means the table is usable."""
    problems = []
    n = len(names)
    if len(corr) != n or any(len(row) != n for row in corr):
        return [f"correlation table must be {n} x {n}"]
    for i in range(n):
        if abs(corr[i][i] - 1.0) > TOLERANCE:
            problems.append(f"diagonal {names[i]} is {corr[i][i]}, must be 1")
        for j in range(n):
            c = corr[i][j]
            if c < -1.0 or c > 1.0:
                problems.append(f"{names[i]} / {names[j]} = {c} is outside -1 to 1")
            if j > i and abs(c - corr[j][i]) > TOLERANCE:
                problems.append(f"not symmetric: {names[i]} / {names[j]} = {c} "
                                f"but {names[j]} / {names[i]} = {corr[j][i]}")
    return problems


# ---------------------------------------------------------------------------
# Calculations, one per function
# ---------------------------------------------------------------------------

def covariance_matrix(corr, vols):
    """Covariance = correlation x volatility_i x volatility_j."""
    n = len(vols)
    return [[corr[i][j] * vols[i] * vols[j] for j in range(n)] for i in range(n)]


def portfolio_return(weights, returns):
    """Sum of weight x expected return."""
    return sum(w * r for w, r in zip(weights, returns))


def portfolio_variance(weights, cov):
    """w' Σ w: every pair of sleeves, including the cross (correlation) terms."""
    n = len(weights)
    total = 0.0
    for i in range(n):
        for j in range(n):
            total += weights[i] * weights[j] * cov[i][j]
    return total


def portfolio_volatility(weights, cov):
    return math.sqrt(portfolio_variance(weights, cov))


def reserve_eligible_weight(weights, names, eligible):
    return sum(w for w, name in zip(weights, names) if name in eligible)


def meets_objective(expected_return, objective):
    return expected_return >= objective - TOLERANCE


# ---------------------------------------------------------------------------
# The three baseline portfolios
# ---------------------------------------------------------------------------

def benchmark_weights(names):
    """40% IG bond fund, 60% global equity index fund."""
    target = {"Investment-grade bond fund": 0.40, "Global equity index fund": 0.60}
    return [target.get(name, 0.0) for name in names]


def equal_weights(names):
    return [1.0 / len(names)] * len(names)


def inverse_volatility_weights(vols):
    inv = [1.0 / v for v in vols]
    total = sum(inv)
    return [x / total for x in inv]


def summarize(label, weights, names, returns, cov, eligible, objective):
    er = portfolio_return(weights, returns)
    vol = portfolio_volatility(weights, cov)
    return {
        "label": label,
        "weights": weights,
        "return": er,
        "volatility": vol,
        "reserve": reserve_eligible_weight(weights, names, eligible),
        "meets": meets_objective(er, objective),
    }


def build_baselines(names=SLEEVES, exp_ret=EXPECTED_RETURN, vol=VOLATILITY,
                    corr=CORRELATION, objective=OBJECTIVE_RETURN, eligible=RESERVE_ELIGIBLE):
    problems = validate_correlation(corr, names)
    if problems:
        raise ValueError("Correlation table rejected:\n  - " + "\n  - ".join(problems))
    returns = [exp_ret[n] for n in names]
    vols = [vol[n] for n in names]
    cov = covariance_matrix(corr, vols)
    portfolios = [
        ("Benchmark", benchmark_weights(names)),
        ("Equal weight", equal_weights(names)),
        ("Inverse volatility", inverse_volatility_weights(vols)),
    ]
    return [summarize(lbl, w, names, returns, cov, eligible, objective) for lbl, w in portfolios]


def main():
    try:
        results = build_baselines()
    except ValueError as err:
        print(f"REFUSED: {err}")
        print("Fix the correlation table at the top of portfolio.py and rerun.")
        sys.exit(1)

    print(f"Objective: {OBJECTIVE_RETURN * 100:.2f}% (CPI 2.5% estimate + 4%)")
    print("Weights order: bills / 10-year / IG / equity\n")
    header = f"{'Portfolio':<20}{'Weights (%)':<28}{'Return':>8}{'Vol':>8}{'Reserve':>9}  Meets?"
    print(header)
    print("-" * len(header))
    for r in results:
        w = " / ".join(f"{x * 100:.1f}" for x in r["weights"])
        print(f"{r['label']:<20}{w:<28}{r['return'] * 100:>7.2f}%{r['volatility'] * 100:>7.2f}%"
              f"{r['reserve'] * 100:>8.1f}%  {'yes' if r['meets'] else 'no'}")


if __name__ == "__main__":
    main()
