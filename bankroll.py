"""
bankroll.py
Bankroll management calculations.
Covers Kelly Criterion staking, allocation tracking, and growth projections.
"""

import math


def kelly_criterion(profit_percent, bankroll, fraction=0.25):
    """
    Calculate the optimal stake using the Kelly Criterion.

    For arb betting, Kelly is simplified since the outcome is guaranteed:
    - Edge = profit_percent / 100
    - Kelly stake = edge * bankroll
    - We use fractional Kelly (default 25%) to be conservative

    profit_percent: the arb profit as a percentage (e.g. 1.5)
    bankroll:       total available bankroll in units
    fraction:       Kelly fraction (0.25 = quarter Kelly, recommended for arbs)

    Returns: recommended total stake in units
    """
    edge = profit_percent / 100
    full_kelly = edge * bankroll
    fractional_kelly = full_kelly * fraction
    return round(fractional_kelly, 4)


def calculate_bankroll_stats(bets, current_bankroll):
    """
    Calculate bankroll allocation and exposure stats.

    bets:             list of bet dicts from Google Sheets
    current_bankroll: user's total bankroll in units

    Returns: dict of stats
    """
    pending = [b for b in bets if b.get("Status") == "Pending"]
    settled = [b for b in bets if b.get("Status") == "Settled"]

    pending_exposure = sum(float(b.get("Total Staked", 0) or 0) for b in pending)
    total_profit = sum(float(b.get("Actual Profit", 0) or b.get("Profit", 0) or 0) for b in settled)
    available = max(0, current_bankroll - pending_exposure + total_profit)
    utilisation = (pending_exposure / current_bankroll * 100) if current_bankroll > 0 else 0

    return {
        "total_bankroll": current_bankroll,
        "pending_exposure": round(pending_exposure, 2),
        "realised_profit": round(total_profit, 2),
        "available_capital": round(available, 2),
        "utilisation_pct": round(utilisation, 1),
        "open_bets": len(pending),
    }


def project_growth(bankroll, avg_profit_pct, bets_per_month, months=12):
    """
    Project bankroll growth over time assuming consistent arb returns.

    Uses compound growth: each bet's profit is reinvested.
    Conservative estimate — assumes only half of projected opportunities
    are actually placed.

    Returns: list of (month, projected_bankroll) tuples
    """
    monthly_return = (avg_profit_pct / 100) * bets_per_month * 0.5
    result = [(0, bankroll)]
    current = bankroll
    for m in range(1, months + 1):
        current = current * (1 + monthly_return)
        result.append((m, round(current, 2)))
    return result


def break_even_calculator(api_cost_monthly, avg_profit_pct, unit_size):
    """
    Calculate how many bets needed per month to cover API costs.

    api_cost_monthly: monthly API subscription cost in same currency as unit_size
    avg_profit_pct:   average profit per arb as a percentage
    unit_size:        value of 1 unit in currency

    Returns: dict with bets needed and minimum stake per bet
    """
    if avg_profit_pct <= 0 or unit_size <= 0:
        return None

    profit_per_unit = avg_profit_pct / 100
    units_needed = api_cost_monthly / (profit_per_unit * unit_size)
    bets_needed = math.ceil(units_needed)

    return {
        "api_cost": api_cost_monthly,
        "bets_needed": bets_needed,
        "min_units_per_bet": round(units_needed / max(bets_needed, 1), 2),
        "avg_profit_pct": avg_profit_pct,
    }
