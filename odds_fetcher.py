"""
odds_fetcher.py
Fetches live odds from The Odds API for all configured sports and markets.
Handles 2-way markets (NBA, NFL, MLB, Tennis) and 3-way markets (Soccer).
"""

import requests
import logging
from datetime import datetime

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Sports supported by this tool and their Odds API keys
# "h2h" = match winner / moneyline
# Soccer uses 1X2 (3-way: home/draw/away); others use h2h (2-way)
SPORTS_CONFIG = {
    "soccer_epl":           {"name": "Soccer - EPL",        "markets": ["h2h", "btts"]},
    "soccer_uefa_champs_league": {"name": "Soccer - UCL",   "markets": ["h2h", "btts"]},
    "soccer_spain_la_liga": {"name": "Soccer - La Liga",    "markets": ["h2h", "btts"]},
    "americanfootball_nfl": {"name": "NFL",                 "markets": ["h2h", "totals"]},
    "basketball_nba":       {"name": "NBA",                 "markets": ["h2h", "totals"]},
    "tennis_atp_french_open": {"name": "Tennis - ATP",      "markets": ["h2h"]},
    "baseball_mlb":         {"name": "MLB",                 "markets": ["h2h", "totals"]},
}

# All market keys we support
MARKET_KEYS = {
    "h2h":           "Match Winner (H2H / 1X2)",
    "totals":        "Over/Under (Totals)",
    "btts":          "Both Teams to Score",
    "asian_handicap":"Asian Handicap",
}

BASE_URL = "https://api.the-odds-api.com/v4"

# ─── FETCHING ─────────────────────────────────────────────────────────────────

def fetch_odds_for_sport(api_key, sport_key, markets, regions="uk,us,eu,au"):
    """
    Fetch live odds for a single sport from The Odds API.
    
    api_key:    your Odds API key
    sport_key:  e.g. "soccer_epl", "basketball_nba"
    markets:    comma-separated market keys e.g. "h2h,totals"
    regions:    bookmaker regions to include (covers most major bookmakers)
    
    Returns: list of event dicts, or empty list on error
    """
    url = f"{BASE_URL}/sports/{sport_key}/odds"
    params = {
        "apiKey": api_key,
        "regions": regions,
        "markets": ",".join(markets),
        "oddsFormat": "decimal",   # We always use decimal odds for the arb math
        "dateFormat": "iso",
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        # Log remaining API quota from response headers
        quota_used = response.headers.get("x-requests-used", "?")
        quota_remaining = response.headers.get("x-requests-remaining", "?")
        logging.info(f"API quota — Used: {quota_used}, Remaining: {quota_remaining}")
        
        if response.status_code == 200:
            events = response.json()
            logging.info(f"Fetched {len(events)} events for {sport_key}")
            return events
        elif response.status_code == 401:
            logging.error("Invalid API key. Check your ODDS_API_KEY in .env")
        elif response.status_code == 429:
            logging.warning("API rate limit hit. Consider increasing scan interval.")
        else:
            logging.error(f"API error {response.status_code} for {sport_key}: {response.text}")
            
    except requests.exceptions.Timeout:
        logging.error(f"Timeout fetching odds for {sport_key}")
    except requests.exceptions.ConnectionError:
        logging.error(f"Connection error fetching odds for {sport_key}")
    except Exception as e:
        logging.error(f"Unexpected error fetching {sport_key}: {e}")
    
    return []


def fetch_all_sports(api_key):
    """
    Fetch odds for all configured sports and return a unified list of events.
    Each event is tagged with its sport name for display purposes.
    
    Returns: list of all event dicts across all sports
    """
    all_events = []
    
    for sport_key, config in SPORTS_CONFIG.items():
        logging.info(f"Fetching: {config['name']}...")
        events = fetch_odds_for_sport(
            api_key=api_key,
            sport_key=sport_key,
            markets=config["markets"]
        )
        
        # Tag each event with its sport title for display
        for event in events:
            event["sport_title"] = config["name"]
            event["sport_key"] = sport_key
        
        all_events.extend(events)
    
    logging.info(f"Total events fetched: {len(all_events)}")
    return all_events


def fetch_available_sports(api_key):
    """
    Utility function: fetch the full list of sports available on The Odds API.
    Useful for discovering new sport keys to add to SPORTS_CONFIG.
    """
    url = f"{BASE_URL}/sports"
    params = {"apiKey": api_key}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logging.error(f"Error fetching sports list: {e}")
    
    return []
