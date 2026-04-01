"""
tracker.py
Handles all bet logging, P&L tracking, and financial calculations.
Reads and writes to Google Sheets for persistent storage.
Calculates: MoM return, IRR, ROI, cumulative P&L, bookmaker stats.
"""

import gspread
import json
import logging
import numpy as np
from datetime import datetime, date
from google.oauth2.service_account import Credentials


# ── Google Sheets Setup ───────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SHEET_HEADERS = [
    "Date", "Event", "Sport", "Market",
    "Outcome 1", "Odds 1", "Bookmaker 1", "Stake 1",
    "Outcome 2", "Odds 2", "Bookmaker 2", "Stake 2",
    "Outcome 3", "Odds 3", "Bookmaker 3", "Stake 3",
    "Total Staked", "Guaranteed Return", "Profit", "Profit %",
    "Status", "Actual Return", "Actual Profit", "Notes"
]


def get_sheet(credentials_dict, sheet_id):
    """
    Connect to Google Sheets using service account credentials.
    Returns the first worksheet of the given sheet.
    """
    try:
        creds = Credentials.from_service_account_info(
            credentials_dict, scopes=SCOPES
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)

        # Use first worksheet, create headers if empty
        worksheet = sheet.get_worksheet(0)
        existing = worksheet.get_all_values()

        if not existing:
            worksheet.append_row(SHEET_HEADERS)
            worksheet.format("A1:X1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.1, "green": 0.1, "blue": 0.2}
            })

        return worksheet

    except Exception as e:
        logging.error(f"Google Sheets connection error: {e}")
        return None


def log_bet(worksheet, opportunity, unit_size, notes=""):
    """
    Log a placed bet to Google Sheets.

    opportunity: arb opportunity dict from scanner
    unit_size:   £ per unit
    notes:       optional free text notes
    """
    try:
        outcomes = opportunity["outcomes"]
        odds = opportunity["best_odds"]
        books = opportunity["bookmakers"]
        units = opportunity["unit_stakes"]

        def safe_get(lst, i, default=""):
            return lst[i] if i < len(lst) else default

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            opportunity["event"],
            opportunity["sport"],
            opportunity["market"],
            safe_get(outcomes, 0), safe_get(odds, 0), safe_get(books, 0),
            round(safe_get(units, 0, 0) * unit_size, 2),
            safe_get(outcomes, 1), safe_get(odds, 1), safe_get(books, 1),
            round(safe_get(units, 1, 0) * unit_size, 2),
            safe_get(outcomes, 2), safe_get(odds, 2), safe_get(books, 2),
            round(safe_get(units, 2, 0) * unit_size, 2),
            round(opportunity["total_staked_units"] * unit_size, 2),
            round(opportunity["guaranteed_return_units"] * unit_size, 2),
            round(opportunity["profit_units"] * unit_size, 2),
            opportunity["profit_percent"],
            "Pending",
            "",  # Actual Return (filled in later)
            "",  # Actual Profit (filled in later)
            notes
        ]

        worksheet.append_row(row)
        return True

    except Exception as e:
        logging.error(f"Error logging bet: {e}")
        return False


def get_all_bets(worksheet):
    """
    Fetch all logged bets from Google Sheets.
    Returns list of dicts with column names as keys.
    """
    try:
        records = worksheet.get_all_records()
        return records
    except Exception as e:
        logging.error(f"Error fetching bets: {e}")
        return []


# ── Financial Calculations ─────────────────────────────────────────────────────

def calculate_roi(bets):
    """
    Calculate overall ROI across all completed bets.
    ROI = (Total Profit / Total Staked) * 100
    """
    completed = [b for b in bets if b.get("Status") == "Settled"]
    if not completed:
        return 0.0

    total_staked = sum(float(b.get("Total Staked", 0) or 0) for b in completed)
    total_profit = sum(float(b.get("Actual Profit", 0) or b.get("Profit", 0) or 0) for b in completed)

    if total_staked == 0:
        return 0.0

    return round((total_profit / total_staked) * 100, 3)


def calculate_mom_returns(bets):
    """
    Calculate Month-on-Month returns.
    Returns dict of {YYYY-MM: profit} for each month with settled bets.
    """
    monthly = {}

    for bet in bets:
        if bet.get("Status") != "Settled":
            continue
        try:
            date_str = str(bet.get("Date", ""))[:7]  # YYYY-MM
            profit = float(bet.get("Actual Profit", 0) or bet.get("Profit", 0) or 0)
            staked = float(bet.get("Total Staked", 0) or 0)
            if date_str not in monthly:
                monthly[date_str] = {"profit": 0, "staked": 0}
            monthly[date_str]["profit"] += profit
            monthly[date_str]["staked"] += staked
        except (ValueError, TypeError):
            continue

    result = {}
    for month, data in sorted(monthly.items()):
        if data["staked"] > 0:
            result[month] = {
                "profit": round(data["profit"], 2),
                "staked": round(data["staked"], 2),
                "return_pct": round((data["profit"] / data["staked"]) * 100, 3)
            }

    return result


def calculate_irr(bets, initial_bankroll=400):
    """
    Calculate Internal Rate of Return (IRR) annualised.

    IRR treats each bet as a cash outflow (stake) and each settlement
    as a cash inflow (return). Annualised IRR shows what annual return
    rate your arb betting is equivalent to.

    Uses Newton's method to solve for IRR.
    Returns annualised IRR as a percentage, or None if insufficient data.
    """
    settled = [b for b in bets if b.get("Status") == "Settled"]
    if len(settled) < 2:
        return None

    try:
        # Build cash flow timeline
        # Each bet: outflow at date placed, inflow at settlement
        cash_flows = {}

        for bet in settled:
            date_str = str(bet.get("Date", ""))[:10]
            try:
                bet_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            staked = float(bet.get("Total Staked", 0) or 0)
            actual_return = float(bet.get("Actual Return", 0) or bet.get("Guaranteed Return", 0) or 0)

            if bet_date not in cash_flows:
                cash_flows[bet_date] = 0
            cash_flows[bet_date] -= staked      # outflow
            cash_flows[bet_date] += actual_return  # inflow (same day for arbs)

        if not cash_flows:
            return None

        dates = sorted(cash_flows.keys())
        flows = [cash_flows[d] for d in dates]
        start = dates[0]
        days = [(d - start).days for d in dates]

        # Newton's method to find daily IRR
        rate = 0.001  # starting guess
        for _ in range(1000):
            npv = sum(flows[i] / (1 + rate) ** (days[i] / 365.0) for i in range(len(flows)))
            dnpv = sum(-days[i] / 365.0 * flows[i] / (1 + rate) ** (days[i] / 365.0 + 1) for i in range(len(flows)))
            if dnpv == 0:
                break
            new_rate = rate - npv / dnpv
            if abs(new_rate - rate) < 1e-8:
                rate = new_rate
                break
            rate = new_rate

        annualised_irr = rate * 100
        if -100 < annualised_irr < 10000:
            return round(annualised_irr, 2)

    except Exception as e:
        logging.error(f"IRR calculation error: {e}")

    return None


def calculate_cumulative_pnl(bets):
    """
    Calculate cumulative P&L over time for the profit trend chart.
    Returns list of (date, cumulative_profit) tuples sorted by date.
    """
    settled = [b for b in bets if b.get("Status") == "Settled"]
    if not settled:
        return []

    daily = {}
    for bet in settled:
        date_str = str(bet.get("Date", ""))[:10]
        profit = float(bet.get("Actual Profit", 0) or bet.get("Profit", 0) or 0)
        if date_str not in daily:
            daily[date_str] = 0
        daily[date_str] += profit

    sorted_dates = sorted(daily.keys())
    cumulative = 0
    result = []
    for d in sorted_dates:
        cumulative += daily[d]
        result.append((d, round(cumulative, 2)))

    return result


def calculate_bookmaker_stats(bets):
    """
    Count how many times each bookmaker appears in logged bets.
    Returns dict of {bookmaker: count} sorted by count descending.
    """
    counts = {}
    for bet in bets:
        for field in ["Bookmaker 1", "Bookmaker 2", "Bookmaker 3"]:
            book = bet.get(field, "")
            if book:
                counts[book] = counts.get(book, 0) + 1

    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def calculate_sport_stats(bets):
    """
    Count arb opportunities by sport from logged bets.
    Returns dict of {sport: count}.
    """
    counts = {}
    for bet in bets:
        sport = bet.get("Sport", "Unknown")
        if sport:
            counts[sport] = counts.get(sport, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def get_summary_stats(bets, unit_size=10):
    """
    Get a full summary of all financial stats for the dashboard.
    """
    all_bets = bets
    settled = [b for b in bets if b.get("Status") == "Settled"]
    pending = [b for b in bets if b.get("Status") == "Pending"]

    total_staked = sum(float(b.get("Total Staked", 0) or 0) for b in settled)
    total_profit = sum(float(b.get("Actual Profit", 0) or b.get("Profit", 0) or 0) for b in settled)
    total_return = sum(float(b.get("Actual Return", 0) or b.get("Guaranteed Return", 0) or 0) for b in settled)
    pending_exposure = sum(float(b.get("Total Staked", 0) or 0) for b in pending)

    return {
        "total_bets": len(all_bets),
        "settled_bets": len(settled),
        "pending_bets": len(pending),
        "total_staked": round(total_staked, 2),
        "total_profit": round(total_profit, 2),
        "total_return": round(total_return, 2),
        "pending_exposure": round(pending_exposure, 2),
        "roi": calculate_roi(bets),
        "irr": calculate_irr(bets),
        "mom_returns": calculate_mom_returns(bets),
        "cumulative_pnl": calculate_cumulative_pnl(bets),
        "bookmaker_stats": calculate_bookmaker_stats(bets),
        "sport_stats": calculate_sport_stats(bets),
    }
