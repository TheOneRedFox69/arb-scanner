python3 << 'EOF'
code = '''import logging


def calculate_arb_percentage(odds_list):
    return sum(1.0 / odd for odd in odds_list)


def calculate_stakes(odds_list):
    """
    Calculate unit stakes for each outcome.
    Stakes are expressed as units rather than a fixed currency amount.
    Multiply by any unit size to get the actual cash stake.

    Example: returns [2.3, 1.8] meaning stake 2.3 units and 1.8 units.
    Total units staked = 4.1 units.
    Guaranteed return = 4.14 units regardless of result.
    """
    arb_pct = calculate_arb_percentage(odds_list)
    if arb_pct >= 1.0:
        return None

    total_units = 1.0 / arb_pct
    unit_stakes = [round((1.0 / odd) / arb_pct, 4) for odd in odds_list]
    guaranteed_return_units = round(total_units, 4)
    total_staked_units = round(sum(unit_stakes), 4)
    profit_units = round(guaranteed_return_units - total_staked_units, 4)
    profit_percent = round((1 - arb_pct) * 100, 3)

    return {
        "unit_stakes": unit_stakes,
        "total_staked_units": total_staked_units,
        "guaranteed_return_units": guaranteed_return_units,
        "profit_units": profit_units,
        "profit_percent": profit_percent,
        "arb_percent": round(arb_pct * 100, 3)
    }


def get_market_outcomes(bookmaker, market_key):
    for market in bookmaker.get("markets", []):
        if market["key"] == market_key:
            outcomes = market.get("outcomes", [])
            if market_key == "totals":
                return pair_totals_outcomes(outcomes)
            return [(o["name"], o["price"]) for o in outcomes]
    return []


def pair_totals_outcomes(outcomes):
    lines = {}
    for outcome in outcomes:
        point = outcome.get("point")
        name = outcome.get("name")
        price = outcome.get("price")
        if point is not None and name and price:
            if point not in lines:
                lines[point] = {}
            lines[point][name] = price
    valid_pairs = []
    for point, sides in lines.items():
        if "Over" in sides and "Under" in sides:
            valid_pairs.append((point, sides["Over"], sides["Under"]))
    if not valid_pairs:
        return []
    best = min(valid_pairs, key=lambda x: (1/x[1]) + (1/x[2]))
    point, over_price, under_price = best
    return [(f"Over {point}", over_price), (f"Under {point}", under_price)]


def is_plausible_odds_combination(odds_list, market_key, is_soccer):
    if is_soccer and market_key == "h2h":
        for odd in odds_list:
            if not (1.05 <= odd <= 30.0):
                return False
    elif market_key == "totals":
        for odd in odds_list:
            if not (1.30 <= odd <= 4.0):
                return False
    else:
        for odd in odds_list:
            if not (1.05 <= odd <= 20.0):
                return False
        implied_probs = [1.0 / odd for odd in odds_list]
        max_prob = max(implied_probs)
        min_prob = min(implied_probs)
        if max_prob > 0.80 and min_prob < 0.10:
            return False
    return True


def filter_matched_totals(outcome_names):
    over_lines = {}
    under_lines = {}
    for name in outcome_names:
        parts = name.split(" ")
        if len(parts) == 2:
            direction, line = parts[0], parts[1]
            try:
                line = float(line)
                if direction == "Over":
                    over_lines[line] = name
                elif direction == "Under":
                    under_lines[line] = name
            except ValueError:
                continue
    matched = set()
    for line in over_lines:
        if line in under_lines:
            matched.add(over_lines[line])
            matched.add(under_lines[line])
    return matched


def check_event_for_arb(event, market_key, bankroll=None):
    """
    Check a single event and market for arbitrage opportunities.
    bankroll parameter kept for backwards compatibility but no longer used
    for stake calculation — stakes are now unit-based.
    """
    opportunities = []
    bookmakers = event.get("bookmakers", [])

    if len(bookmakers) < 2:
        return opportunities

    outcome_names = set()
    for bookmaker in bookmakers:
        for outcome_name, _ in get_market_outcomes(bookmaker, market_key):
            outcome_names.add(outcome_name)

    if len(outcome_names) < 2:
        return opportunities

    if market_key == "totals":
        outcome_names = filter_matched_totals(outcome_names)
        if not outcome_names:
            return opportunities

    best_odds_per_outcome = {}
    best_book_per_outcome = {}

    for outcome_name in outcome_names:
        best_price = 0
        best_book = None
        for bookmaker in bookmakers:
            for name, price in get_market_outcomes(bookmaker, market_key):
                if name == outcome_name and price > best_price:
                    if 1.01 <= price <= 50.0:
                        best_price = price
                        best_book = bookmaker["title"]
        if best_price > 1.01:
            best_odds_per_outcome[outcome_name] = best_price
            best_book_per_outcome[outcome_name] = best_book

    if len(best_odds_per_outcome) < 2:
        return opportunities

    unique_bookmakers = set(best_book_per_outcome.values())
    if len(unique_bookmakers) < 2:
        return opportunities

    sport_key = event.get("sport_key", "")
    is_soccer = "soccer" in sport_key
    expected_outcomes = 3 if is_soccer and market_key == "h2h" else 2

    if len(best_odds_per_outcome) != expected_outcomes:
        return opportunities

    outcome_list = list(best_odds_per_outcome.keys())
    odds_list = [best_odds_per_outcome[o] for o in outcome_list]

    if not is_plausible_odds_combination(odds_list, market_key, is_soccer):
        return opportunities

    arb_pct = calculate_arb_percentage(odds_list)
    if arb_pct < 0.92:
        return opportunities

    result = calculate_stakes(odds_list)

    if result:
        opportunities.append({
            "event": f"{event.get(\'home_team\', \'?\')} vs {event.get(\'away_team\', \'?\')}",
            "sport": event.get("sport_title", "Unknown"),
            "commence_time": event.get("commence_time", "Unknown"),
            "market": market_key,
            "outcomes": outcome_list,
            "best_odds": odds_list,
            "bookmakers": [best_book_per_outcome[o] for o in outcome_list],
            **result
        })

    return opportunities
'''

with open("arb_calculator.py", "w") as f:
    f.write(code)
print("arb_calculator.py updated successfully")
EOF