"""mandate.py - Meridian Foundation Reserve mandate checker (Lab 13, extended in Lab 14).

Standard library only. Run:  python mandate.py

Every number printed is computed from the inputs below; nothing is typed in.
Lab 14 addition: candidate E = the client's own benchmark (40% IG bond fund, 60% equity fund).
"""

# ---------------------------------------------------------------------------
# Editable inputs
# ---------------------------------------------------------------------------

# holding: (issuer, business days to redeem, reserve-eligible)
HOLDINGS = {
    "Cash":                       ("none",             0,  True),
    "Treasury bills":             ("U.S. Treasury",    1,  True),
    "Treasury 10-year note":      ("U.S. Treasury",    1,  True),
    "Global equity index fund":   ("diversified fund", 2,  False),
    "Investment-grade bond fund": ("diversified fund", 3,  False),
    "Private real estate fund":   ("diversified fund", 90, False),
    "Acme Corp bonds":            ("Acme Corp",        4,  False),
    "Acme Corp stock":            ("Acme Corp",        1,  False),
}

# Issuers exempt from the single-issuer limit
EXEMPT_ISSUERS = {"none", "U.S. Treasury", "diversified fund"}

# Candidate portfolios, percent weights
CANDIDATES = {
    "A": {
        "Cash": 2, "Treasury bills": 2, "Treasury 10-year note": 10,
        "Global equity index fund": 60, "Investment-grade bond fund": 26,
        "Private real estate fund": 0, "Acme Corp bonds": 0, "Acme Corp stock": 0,
    },
    "B": {
        "Cash": 1, "Treasury bills": 0, "Treasury 10-year note": 0,
        "Global equity index fund": 55, "Investment-grade bond fund": 20,
        "Private real estate fund": 15, "Acme Corp bonds": 5, "Acme Corp stock": 4,
    },
    "C": {
        "Cash": 1, "Treasury bills": 1, "Treasury 10-year note": 0,
        "Global equity index fund": 70, "Investment-grade bond fund": 20,
        "Private real estate fund": 0, "Acme Corp bonds": 0, "Acme Corp stock": 8,
    },
    # Lab 13 attack: passes every checkable rule, but 90% equity offends S9 (loss tolerance)
    # and S4 (it is a very different risk from the 60/40 benchmark).
    "D": {
        "Cash": 0, "Treasury bills": 3, "Treasury 10-year note": 0,
        "Global equity index fund": 90, "Investment-grade bond fund": 0,
        "Private real estate fund": 0, "Acme Corp bonds": 0, "Acme Corp stock": 7,
    },
    # Lab 14: the client's own benchmark (S4)
    "E": {
        "Cash": 0, "Treasury bills": 0, "Treasury 10-year note": 0,
        "Global equity index fund": 60, "Investment-grade bond fund": 40,
        "Private real estate fund": 0, "Acme Corp bonds": 0, "Acme Corp stock": 0,
    },
}

RESERVE_SIZE = 100.0          # USD millions
QUARTERLY_DISTRIBUTION = 0.75  # USD millions
QUARTERS_TO_COVER = 4
LIQUIDITY_WINDOW_DAYS = 5      # business days
MIN_LIQUID_SHARE = 90.0        # percent
ISSUER_LIMIT = 8.0             # percent
WEIGHT_TOLERANCE = 1e-9


# ---------------------------------------------------------------------------
# Calculations, one per function
# ---------------------------------------------------------------------------

def reserve_minimum(quarters, distribution, reserve_size):
    """Percent of the portfolio needed to cover the payouts."""
    return quarters * distribution / reserve_size * 100.0


def weight_sum(weights):
    return sum(weights.values())


def lowest_weight(weights):
    return min(weights.values())


def reserve_eligible_weight(weights, holdings):
    return sum(w for h, w in weights.items() if holdings[h][2])


def liquid_weight(weights, holdings, window):
    return sum(w for h, w in weights.items() if holdings[h][1] <= window)


def largest_single_company(weights, holdings, exempt):
    by_issuer = {}
    for h, w in weights.items():
        issuer = holdings[h][0]
        if issuer in exempt:
            continue
        by_issuer[issuer] = by_issuer.get(issuer, 0.0) + w
    return max(by_issuer.values()) if by_issuer else 0.0


def check_candidate(weights, reserve_min):
    """Return a list of (rule, measured value, passed)."""
    total = weight_sum(weights)
    low = lowest_weight(weights)
    reserve = reserve_eligible_weight(weights, HOLDINGS)
    liquid = liquid_weight(weights, HOLDINGS, LIQUIDITY_WINDOW_DAYS)
    issuer = largest_single_company(weights, HOLDINGS, EXEMPT_ISSUERS)
    return [
        ("Weights sum to 100", total, abs(total - 100.0) <= WEIGHT_TOLERANCE),
        ("Long-only (lowest weight)", low, low >= 0),
        (f"Reserve-eligible >= {reserve_min:.1f}%", reserve, reserve >= reserve_min - WEIGHT_TOLERANCE),
        (f"Redeemable in {LIQUIDITY_WINDOW_DAYS} days >= {MIN_LIQUID_SHARE:.0f}%", liquid,
         liquid >= MIN_LIQUID_SHARE - WEIGHT_TOLERANCE),
        (f"Largest single company <= {ISSUER_LIMIT:.0f}%", issuer, issuer <= ISSUER_LIMIT + WEIGHT_TOLERANCE),
    ]


def main():
    for name, weights in CANDIDATES.items():
        unknown = set(weights) - set(HOLDINGS)
        if unknown:
            raise SystemExit(f"Candidate {name} uses unknown holdings: {sorted(unknown)}")

    rmin = reserve_minimum(QUARTERS_TO_COVER, QUARTERLY_DISTRIBUTION, RESERVE_SIZE)
    print(f"Reserve minimum: {rmin:.1f}% of the portfolio "
          f"({QUARTERS_TO_COVER} x {QUARTERLY_DISTRIBUTION} / {RESERVE_SIZE:g})\n")

    for name, weights in CANDIDATES.items():
        print(f"Candidate {name}")
        results = check_candidate(weights, rmin)
        fails = 0
        for rule, value, ok in results:
            print(f"  {rule:<34} {value:6.1f}  {'pass' if ok else 'FAIL'}")
            fails += 0 if ok else 1
        print(f"  {'Calendar-year loss <= 10%':<34} requires CIO clarification")
        print("  Verdict: " + ("passes every checkable rule" if fails == 0 else f"fails {fails} rule(s)"))
        print()


if __name__ == "__main__":
    main()
