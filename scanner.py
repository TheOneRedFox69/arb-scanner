"""
scanner.py
Main orchestration loop. Fetches odds, finds arb opportunities,
sends alerts, and logs everything. Run this to start the tool.
"""

import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

from odds_fetcher import fetch_all_sports, SPORTS_CONFIG, MARKET_KEYS
from arb_calculator import check_event_for_arb
from alerts import send_email_alert

# ─── SETUP ────────────────────────────────────────────────────────────────────

load_dotenv()  # Load API keys and settings from .env file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),                          # Print to console
        logging.FileHandler("arb_scanner.log", mode="a") # Also save to log file
    ]
)

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# How often to scan for new opportunities (in seconds)
# Free tier of Odds API: 500 req/month (~17/day). With 7 sports × 1 req each,
# that's ~2 full scans per day on free tier.
# On paid tier, you can safely drop this to 60–120 seconds.
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", 3600))  # default: 1 hour

# Your total bankroll to use per opportunity
BANKROLL = float(os.getenv("BANKROLL", 400))  # default £400 (under £500 budget)

# Minimum profit % to trigger an alert (0.0 = any profitable arb)
MIN_PROFIT_PERCENT = float(os.getenv("MIN_PROFIT_PERCENT", 0.5))

# Set to True to alert on breakeven opportunities too (arb% slightly above 1.0)
INCLUDE_BREAKEVEN = os.getenv("INCLUDE_BREAKEVEN", "false").lower() == "true"

# ─── CORE SCAN FUNCTION ───────────────────────────────────────────────────────

def run_scan(api_key, email_config):
    """
    Run one full scan cycle:
    1. Fetch all odds
    2. Check every event/market combination for arb
    3. Filter by minimum profit threshold
    4. Send email alert if any found
    5. Return found opportunities for dashboard display
    """
    logging.info("=" * 60)
    logging.info(f"Starting scan at {datetime.now().strftime('%d %b %Y %H:%M:%S')}")
    logging.info(f"Bankroll: £{BANKROLL} | Min profit: {MIN_PROFIT_PERCENT}%")
    logging.info("=" * 60)
    
    # Step 1: Fetch all odds
    all_events = fetch_all_sports(api_key)
    
    if not all_events:
        logging.warning("No events fetched. Check API key and internet connection.")
        return []
    
    # Step 2: Check each event × market for arb
    all_opportunities = []
    markets_to_check = list(MARKET_KEYS.keys())
    
    from datetime import timezone
    now = datetime.now(timezone.utc)

    for event in all_events:
        # Skip events that have already started
        commence_time = event.get("commence_time", "")
        try:
            from datetime import datetime as dt
            event_time = dt.fromisoformat(commence_time.replace("Z", "+00:00"))
            if event_time <= now:
                logging.info(f"Skipping in-play event: {event.get('home_team')} vs {event.get('away_team')}")
                continue
        except Exception:
            pass

        for market_key in markets_to_check:
            opps = check_event_for_arb(event, market_key, BANKROLL)
            all_opportunities.extend(opps)
    
    logging.info(f"Raw opportunities found: {len(all_opportunities)}")
    
    # Step 3: Filter by minimum profit threshold
    filtered = [
        opp for opp in all_opportunities
        if opp["profit_percent"] >= MIN_PROFIT_PERCENT
    ]
    
    # Optionally include near-breakeven opportunities
    if INCLUDE_BREAKEVEN:
        near_even = [
            opp for opp in all_opportunities
            if -0.5 <= opp["profit_percent"] < MIN_PROFIT_PERCENT
        ]
        if near_even:
            logging.info(f"Near-breakeven opportunities (not alerted): {len(near_even)}")
    
    # Sort best opportunities first
    filtered.sort(key=lambda x: x["profit_percent"], reverse=True)
    
    if filtered:
        logging.info(f"✅ {len(filtered)} alertable opportunities found!")
        for opp in filtered:
            logging.info(
                f"  → {opp['event']} | {opp['market']} | "
                f"{opp['profit_percent']}% profit | £{opp['guaranteed_profit']} on £{opp['total_staked']}"
            )
        
        # Step 4: Send email alert
        send_email_alert(filtered, email_config)
    else:
        logging.info("No opportunities above threshold this scan.")
    
    return filtered


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Load settings
    api_key = os.getenv("ODDS_API_KEY")
    
    if not api_key:
        logging.error("ODDS_API_KEY not set in .env file. Exiting.")
        exit(1)
    
    email_config = {
        "EMAIL_SENDER":    os.getenv("EMAIL_SENDER"),
        "EMAIL_PASSWORD":  os.getenv("EMAIL_PASSWORD"),
        "EMAIL_RECIPIENT": os.getenv("EMAIL_RECIPIENT"),
        "SMTP_HOST":       os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "SMTP_PORT":       os.getenv("SMTP_PORT", "587"),
    }
    
    logging.info("🚀 Arb Scanner started.")
    logging.info(f"Scanning every {SCAN_INTERVAL_SECONDS}s | Sports: {len(SPORTS_CONFIG)} | Bankroll: £{BANKROLL}")
    
    # Run continuously
    while True:
        try:
            run_scan(api_key, email_config)
        except KeyboardInterrupt:
            logging.info("Scanner stopped by user.")
            break
        except Exception as e:
            logging.error(f"Unexpected error in scan: {e}", exc_info=True)
        
        logging.info(f"Next scan in {SCAN_INTERVAL_SECONDS} seconds...")
        time.sleep(SCAN_INTERVAL_SECONDS)
