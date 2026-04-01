"""
bookmaker_ratings.py
Bookmaker reliability ratings for arb bettors.
Covers tolerance for arb betting, account limiting risk, and overall reputation.
"""

BOOKMAKER_RATINGS = {
    # ── Arb-Friendly (Sharp books — rarely limit) ─────────────────────────────
    "Pinnacle": {
        "rating": 5,
        "label": "Arb Friendly",
        "color": "#34d399",
        "icon": "✅",
        "note": "The gold standard for arb bettors. Welcomes sharp money, almost never limits accounts. Highest recommended.",
        "limits_arbers": False,
    },
    "Betfair": {
        "rating": 5,
        "label": "Arb Friendly",
        "color": "#34d399",
        "icon": "✅",
        "note": "Exchange model means you bet against other users. No incentive to limit winners. Excellent for arbing.",
        "limits_arbers": False,
    },
    "Matchbook": {
        "rating": 5,
        "label": "Arb Friendly",
        "color": "#34d399",
        "icon": "✅",
        "note": "Betting exchange similar to Betfair. Very arb-friendly, low commission model.",
        "limits_arbers": False,
    },
    "Smarkets": {
        "rating": 5,
        "label": "Arb Friendly",
        "color": "#34d399",
        "icon": "✅",
        "note": "Betting exchange with low commission. No account restrictions for winners.",
        "limits_arbers": False,
    },
    "SBOBet": {
        "rating": 4,
        "label": "Low Risk",
        "color": "#34d399",
        "icon": "✅",
        "note": "Asian bookmaker with high limits and good tolerance for sharp betting.",
        "limits_arbers": False,
    },
    "Unibet": {
        "rating": 3,
        "label": "Moderate Risk",
        "color": "#fbbf24",
        "icon": "⚠️",
        "note": "Generally tolerant but will limit accounts showing consistent arb patterns over time.",
        "limits_arbers": True,
    },
    "Unibet (NL)": {
        "rating": 3,
        "label": "Moderate Risk",
        "color": "#fbbf24",
        "icon": "⚠️",
        "note": "Dutch Unibet. Similar profile to main Unibet — moderate tolerance for arbing.",
        "limits_arbers": True,
    },
    "1xBet": {
        "rating": 3,
        "label": "Moderate Risk",
        "color": "#fbbf24",
        "icon": "⚠️",
        "note": "High odds but be aware of withdrawal issues reported by some users. Use with caution.",
        "limits_arbers": True,
    },
    "Nordic Bet": {
        "rating": 3,
        "label": "Moderate Risk",
        "color": "#fbbf24",
        "icon": "⚠️",
        "note": "Scandinavian bookmaker. Reasonable tolerance but will limit large or frequent winners.",
        "limits_arbers": True,
    },
    "MyBookie.ag": {
        "rating": 3,
        "label": "Moderate Risk",
        "color": "#fbbf24",
        "icon": "⚠️",
        "note": "US-facing offshore book. Decent odds but account reviews for winners are common.",
        "limits_arbers": True,
    },
    "Coolbet": {
        "rating": 3,
        "label": "Moderate Risk",
        "color": "#fbbf24",
        "icon": "⚠️",
        "note": "Estonian operator with decent odds. Moderate arb tolerance.",
        "limits_arbers": True,
    },
    "BetVictor": {
        "rating": 2,
        "label": "High Risk",
        "color": "#f87171",
        "icon": "🚨",
        "note": "Known to limit winning accounts. Keep stakes natural-looking and vary your timing.",
        "limits_arbers": True,
    },
    "Bet365": {
        "rating": 1,
        "label": "Limit Risk",
        "color": "#f87171",
        "icon": "🚨",
        "note": "Aggressively limits arb bettors. Expect stake restrictions after consistent wins. Use sparingly.",
        "limits_arbers": True,
    },
    "William Hill": {
        "rating": 1,
        "label": "Limit Risk",
        "color": "#f87171",
        "icon": "🚨",
        "note": "Frequently restricts accounts. Keep stakes modest and behaviour natural.",
        "limits_arbers": True,
    },
    "Ladbrokes": {
        "rating": 1,
        "label": "Limit Risk",
        "color": "#f87171",
        "icon": "🚨",
        "note": "Part of same group as Coral. Known for limiting sharp accounts quickly.",
        "limits_arbers": True,
    },
    "Coral": {
        "rating": 1,
        "label": "Limit Risk",
        "color": "#f87171",
        "icon": "🚨",
        "note": "Same group as Ladbrokes. Limit-happy with consistent winners.",
        "limits_arbers": True,
    },
    "Paddy Power": {
        "rating": 2,
        "label": "High Risk",
        "color": "#f87171",
        "icon": "🚨",
        "note": "Part of Flutter group. Will limit accounts showing arb patterns.",
        "limits_arbers": True,
    },
    "Betway": {
        "rating": 2,
        "label": "High Risk",
        "color": "#f87171",
        "icon": "🚨",
        "note": "Restricts winning accounts. Arb activity is monitored closely.",
        "limits_arbers": True,
    },
    "DraftKings": {
        "rating": 2,
        "label": "High Risk",
        "color": "#f87171",
        "icon": "🚨",
        "note": "US operator known to limit sharp bettors. Keep activity varied.",
        "limits_arbers": True,
    },
    "FanDuel": {
        "rating": 2,
        "label": "High Risk",
        "color": "#f87171",
        "icon": "🚨",
        "note": "US operator. Similar profile to DraftKings for arb tolerance.",
        "limits_arbers": True,
    },
    "BetMGM": {
        "rating": 2,
        "label": "High Risk",
        "color": "#f87171",
        "icon": "🚨",
        "note": "US operator with known account restriction practices for consistent winners.",
        "limits_arbers": True,
    },
    "PlayUp": {
        "rating": 3,
        "label": "Moderate Risk",
        "color": "#fbbf24",
        "icon": "⚠️",
        "note": "Australian operator. Moderate tolerance, watch for stake restrictions.",
        "limits_arbers": True,
    },
}

DEFAULT_RATING = {
    "rating": 3,
    "label": "Unknown",
    "color": "#64748b",
    "icon": "❓",
    "note": "No data available for this bookmaker. Treat with standard caution.",
    "limits_arbers": None,
}


def get_rating(bookmaker_name):
    """
    Get the reliability rating for a bookmaker.
    Case-insensitive lookup with fallback to default.
    """
    for key, val in BOOKMAKER_RATINGS.items():
        if key.lower() == bookmaker_name.lower():
            return val
    return DEFAULT_RATING


def get_opportunity_risk_score(bookmakers):
    """
    Calculate an overall risk score for an arb opportunity
    based on the bookmakers involved.

    Returns: dict with overall_rating, worst_book, and advice
    """
    ratings = [get_rating(b) for b in bookmakers]
    min_rating = min(r["rating"] for r in ratings)
    worst = bookmakers[ratings.index(min(ratings, key=lambda r: r["rating"]))]

    if min_rating >= 4:
        advice = "Low risk combination — both books are arb-friendly."
        color = "#34d399"
    elif min_rating == 3:
        advice = "Moderate risk — vary your stakes and timing to avoid detection."
        color = "#fbbf24"
    else:
        advice = "High risk — at least one book is known to limit arb bettors. Keep stakes natural."
        color = "#f87171"

    return {
        "overall_rating": min_rating,
        "worst_book": worst,
        "advice": advice,
        "color": color,
    }
