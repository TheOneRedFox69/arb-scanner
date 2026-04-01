python3 << 'EOF'
code = '''import os
import time
import streamlit as st
from datetime import datetime, timezone
from dotenv import load_dotenv
from odds_fetcher import fetch_all_sports, MARKET_KEYS
from arb_calculator import check_event_for_arb

load_dotenv()

st.set_page_config(page_title="Arb Scanner", page_icon="Arb", layout="wide")

with st.sidebar:
    st.title("Settings")
    api_key = st.text_input("Odds API Key", value=os.getenv("ODDS_API_KEY", ""), type="password")
    st.divider()
    st.subheader("Stake Multiplier")
    unit_size = st.number_input(
        "Unit size (your currency)",
        min_value=1.0,
        max_value=10000.0,
        value=10.0,
        step=1.0,
        help="Each unit stake is multiplied by this amount. Example: unit size 50 means each 1.0 unit = 50 in your currency."
    )
    st.caption("Example: if a bet shows 2.3 units and your unit size is 50, you stake 115.")
    st.divider()
    min_profit = st.slider("Min Profit Percent", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
    st.divider()
    st.subheader("Markets")
    selected_markets = st.multiselect("Markets to scan", options=list(MARKET_KEYS.keys()), default=list(MARKET_KEYS.keys()), format_func=lambda k: MARKET_KEYS[k])
    st.divider()
    auto_refresh = st.toggle("Auto-refresh", value=False)
    refresh_mins = st.number_input("Refresh every minutes", min_value=5, max_value=120, value=60, disabled=not auto_refresh)

st.title("Sports Arbitrage Scanner")
st.caption("Last updated: " + datetime.now().strftime("%d %b %Y %H:%M:%S"))

if not api_key:
    st.warning("Enter your Odds API key in the sidebar to begin.")
    st.stop()

col1, col2, col3 = st.columns([2, 1, 3])
with col1:
    scan_clicked = st.button("Scan Now", type="primary", use_container_width=True)
with col2:
    st.caption("Unit size: " + str(unit_size))

if scan_clicked or auto_refresh:
    with st.spinner("Fetching live odds from bookmakers..."):
        all_events = fetch_all_sports(api_key)
    if not all_events:
        st.error("Could not fetch odds. Check your API key and connection.")
        st.stop()
    with st.spinner("Scanning events..."):
        all_opps = []
        now = datetime.now(timezone.utc)
        for event in all_events:
            commence_time = event.get("commence_time", "")
            try:
                event_time = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
                if event_time <= now:
                    continue
            except Exception:
                pass
            for market_key in selected_markets:
                opps = check_event_for_arb(event, market_key)
                all_opps.extend(opps)

    filtered = sorted(
        [o for o in all_opps if o["profit_percent"] >= min_profit],
        key=lambda x: x["profit_percent"],
        reverse=True
    )

    st.divider()
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Events Scanned", len(all_events))
    m2.metric("Arbs Found", len(filtered))
    m3.metric("Best Profit", str(filtered[0]["profit_percent"]) + "%" if filtered else "---")
    m4.metric("Total Units", str(filtered[0]["total_staked_units"]) + " units" if filtered else "---")
    m5.metric("Total Cash", str(round(filtered[0]["total_staked_units"] * unit_size, 2)) if filtered else "---")
    st.divider()

    if not filtered:
        st.info("No opportunities found above threshold. Try lowering the minimum profit percent or check back later.")
    else:
        st.subheader(str(len(filtered)) + " Opportunities Found")
        for i, opp in enumerate(filtered, 1):
            total_cash = round(opp["total_staked_units"] * unit_size, 2)
            profit_cash = round(opp["profit_units"] * unit_size, 2)
            return_cash = round(opp["guaranteed_return_units"] * unit_size, 2)
            label = (
                "#" + str(i) + " " + opp["event"] +
                " | " + MARKET_KEYS.get(opp["market"], opp["market"]) +
                " | " + str(opp["profit_percent"]) + "% profit" +
                " | " + str(opp["total_staked_units"]) + " units" +
                " = " + str(total_cash) + " at unit size " + str(unit_size)
            )
            with st.expander(label, expanded=(i == 1)):
                info1, info2 = st.columns(2)
                with info1:
                    st.markdown("**Sport:** " + opp["sport"])
                    st.markdown("**Kick-off:** " + opp["commence_time"])
                    st.markdown("**Market:** " + MARKET_KEYS.get(opp["market"], opp["market"]))
                with info2:
                    st.markdown("**Arb percent:** " + str(opp["arb_percent"]) + "%")
                    st.markdown("**Total units staked:** " + str(opp["total_staked_units"]) + " units")
                    st.markdown("**Total cash staked:** " + str(total_cash) + " at unit size " + str(unit_size))
                    st.markdown("**Guaranteed return:** " + str(opp["guaranteed_return_units"]) + " units = " + str(return_cash))
                    st.markdown("**Guaranteed profit:** " + str(opp["profit_units"]) + " units = " + str(profit_cash))

                st.subheader("Bets to Place")
                bet_cols = st.columns(len(opp["outcomes"]))
                for j, (outcome, odds, book, unit_stake) in enumerate(zip(opp["outcomes"], opp["best_odds"], opp["bookmakers"], opp["unit_stakes"])):
                    cash_stake = round(unit_stake * unit_size, 2)
                    with bet_cols[j]:
                        st.markdown("**" + outcome + "**")
                        st.metric("Odds", odds)
                        st.metric("Units", str(unit_stake) + " units")
                        st.metric("Cash stake", cash_stake)
                        st.caption(book)

                st.caption("Odds change rapidly. Verify on bookmaker site before placing bets.")

if auto_refresh:
    time.sleep(refresh_mins * 60)
    st.rerun()
'''

with open("dashboard.py", "w") as f:
    f.write(code)
print("dashboard.py updated successfully")
EOF