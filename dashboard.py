import os
import time
import streamlit as st
from datetime import datetime, timezone
from dotenv import load_dotenv
from odds_fetcher import fetch_all_sports, MARKET_KEYS
from arb_calculator import check_event_for_arb

load_dotenv()

st.set_page_config(
    page_title="ArbScanner Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif;
    background-color: #0f1729 !important;
    color: #e2e8f0;
}

.stApp {
    background: linear-gradient(135deg, #0f1729 0%, #111827 50%, #0f1729 100%) !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1e 0%, #0d1428 100%) !important;
    border-right: 1px solid rgba(99, 102, 241, 0.15) !important;
}

section[data-testid="stSidebar"] label {
    color: #64748b !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}

section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input {
    background: rgba(99, 102, 241, 0.08) !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] {
    background: rgba(99, 102, 241, 0.08) !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 32px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    width: 100% !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 24px rgba(99, 102, 241, 0.3) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #818cf8 0%, #6366f1 100%) !important;
    box-shadow: 0 8px 32px rgba(99, 102, 241, 0.5) !important;
    transform: translateY(-1px) !important;
}

.stSpinner > div { border-top-color: #6366f1 !important; }

hr { border-color: rgba(99, 102, 241, 0.15) !important; }

.header-wrap {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0 24px 0;
    border-bottom: 1px solid rgba(99, 102, 241, 0.15);
    margin-bottom: 28px;
}

.header-left { display: flex; align-items: center; gap: 14px; }

.header-logo {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4);
}

.header-title {
    font-size: 20px;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.02em;
}

.header-sub {
    font-size: 11px;
    color: #475569;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 2px;
}

.header-unit {
    text-align: right;
    background: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 12px;
    padding: 10px 18px;
}

.header-unit-label {
    font-size: 10px;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
}

.header-unit-value {
    font-size: 22px;
    font-weight: 700;
    color: #818cf8;
    font-family: 'JetBrains Mono', monospace;
}

.metrics-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 28px;
}

.metric-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(79,70,229,0.05) 100%);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 16px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
}

.metric-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #6366f1, #818cf8);
    opacity: 0.6;
}

.metric-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #475569;
    margin-bottom: 8px;
    font-family: 'JetBrains Mono', monospace;
}

.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: #e2e8f0;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.02em;
}

.metric-value.green { color: #34d399; }
.metric-value.blue { color: #818cf8; }

.section-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #475569;
    margin-bottom: 14px;
    font-family: 'JetBrains Mono', monospace;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(99, 102, 241, 0.15);
}

.opp-card {
    background: linear-gradient(135deg, rgba(15,23,41,0.9) 0%, rgba(13,20,40,0.95) 100%);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
}

.opp-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, #6366f1, #34d399);
    border-radius: 3px 0 0 3px;
}

.opp-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 18px;
}

.opp-event-name {
    font-size: 16px;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 5px;
    letter-spacing: -0.01em;
}

.opp-meta {
    font-size: 11px;
    color: #475569;
    font-family: 'JetBrains Mono', monospace;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.opp-meta span {
    background: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.15);
    padding: 2px 8px;
    border-radius: 4px;
}

.profit-pill {
    background: linear-gradient(135deg, rgba(52,211,153,0.2), rgba(16,185,129,0.1));
    border: 1px solid rgba(52, 211, 153, 0.35);
    color: #34d399;
    padding: 8px 16px;
    border-radius: 50px;
    font-size: 14px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
    letter-spacing: -0.01em;
}

.stats-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 20px;
}

.stat-box {
    background: rgba(99, 102, 241, 0.06);
    border: 1px solid rgba(99, 102, 241, 0.12);
    border-radius: 10px;
    padding: 12px 14px;
    text-align: center;
}

.stat-box-label {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #334155;
    margin-bottom: 5px;
    font-family: 'JetBrains Mono', monospace;
}

.stat-box-value {
    font-size: 14px;
    font-weight: 600;
    color: #94a3b8;
    font-family: 'JetBrains Mono', monospace;
}

.bets-label {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #334155;
    margin-bottom: 10px;
    font-family: 'JetBrains Mono', monospace;
}

.bet-card {
    background: rgba(99, 102, 241, 0.05);
    border: 1px solid rgba(99, 102, 241, 0.12);
    border-radius: 12px;
    padding: 14px 16px;
}

.bet-outcome-name {
    font-size: 13px;
    font-weight: 600;
    color: #cbd5e1;
    margin-bottom: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.bet-line {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
}

.bet-line-label {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #334155;
    font-family: 'JetBrains Mono', monospace;
}

.bet-line-val {
    font-size: 13px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}

.val-odds { color: #818cf8; }
.val-units { color: #94a3b8; }
.val-cash { color: #34d399; }

.book-badge {
    margin-top: 10px;
    display: inline-block;
    font-size: 9px;
    color: #475569;
    background: rgba(15, 23, 41, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.12);
    padding: 3px 8px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.warn-line {
    font-size: 10px;
    color: #334155;
    text-align: center;
    margin-top: 18px;
    font-family: 'JetBrains Mono', monospace;
}

.empty-state {
    text-align: center;
    padding: 64px 20px;
}

.empty-icon { font-size: 36px; margin-bottom: 14px; }

.empty-title {
    font-size: 16px;
    font-weight: 500;
    color: #475569;
    margin-bottom: 6px;
}

.empty-sub {
    font-size: 12px;
    color: #334155;
    font-family: 'JetBrains Mono', monospace;
}

.sidebar-title {
    font-size: 15px;
    font-weight: 700;
    color: #818cf8 !important;
    letter-spacing: -0.01em;
    margin-bottom: 4px;
}

.sidebar-sub {
    font-size: 10px;
    color: #334155 !important;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="sidebar-title">⚡ ArbScanner Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Sports Arbitrage Scanner</div>', unsafe_allow_html=True)
    st.divider()

    api_key = st.text_input("Odds API Key", value=os.getenv("ODDS_API_KEY", ""), type="password")
    unit_size = st.number_input("Unit Size (£)", min_value=1.0, max_value=10000.0, value=10.0, step=1.0,
        help="1 unit = this amount. E.g. unit size £50 means stake of 2.3 units = £115")
    min_profit = st.slider("Min Profit %", min_value=0.0, max_value=5.0, value=0.5, step=0.1)

    st.divider()
    selected_markets = st.multiselect("Markets",
        options=list(MARKET_KEYS.keys()),
        default=list(MARKET_KEYS.keys()),
        format_func=lambda k: MARKET_KEYS[k])

    st.divider()
    auto_refresh = st.toggle("Auto-refresh", value=False)
    refresh_mins = st.number_input("Interval (mins)", min_value=5, max_value=120, value=60, disabled=not auto_refresh)

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="header-wrap">
    <div class="header-left">
        <div class="header-logo">⚡</div>
        <div>
            <div class="header-title">ArbScanner Pro</div>
            <div class="header-sub">{datetime.now().strftime("%d %b %Y · %H:%M:%S UTC")}</div>
        </div>
    </div>
    <div class="header-unit">
        <div class="header-unit-label">Unit Size</div>
        <div class="header-unit-value">£{unit_size:.0f}</div>
    </div>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🔑</div>
        <div class="empty-title">Enter your Odds API key in the sidebar</div>
        <div class="empty-sub">get your key at the-odds-api.com</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

scan_clicked = st.button("⚡  SCAN MARKETS NOW")

# ── Scan ──────────────────────────────────────────────────────────────────────

if scan_clicked or auto_refresh:
    with st.spinner("Connecting to live odds feeds..."):
        all_events = fetch_all_sports(api_key)

    if not all_events:
        st.error("Could not fetch odds. Check your API key and connection.")
        st.stop()

    with st.spinner(f"Scanning {len(all_events)} events across {len(selected_markets)} markets..."):
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

    best_profit = filtered[0]["profit_percent"] if filtered else 0
    best_cash = round(filtered[0]["profit_units"] * unit_size, 2) if filtered else 0

    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-card">
            <div class="metric-label">Events Scanned</div>
            <div class="metric-value blue">{len(all_events)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Arbs Found</div>
            <div class="metric-value {'green' if filtered else ''}">{len(filtered)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Best Profit %</div>
            <div class="metric-value {'green' if filtered else ''}">{best_profit}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Best Profit £</div>
            <div class="metric-value {'green' if filtered else ''}">£{best_cash}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not filtered:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📡</div>
            <div class="empty-title">No opportunities above threshold</div>
            <div class="empty-sub">lower the min profit % or scan again later</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-label">{len(filtered)} opportunit{"y" if len(filtered)==1 else "ies"} found</div>', unsafe_allow_html=True)

        for i, opp in enumerate(filtered, 1):
            total_cash = round(opp["total_staked_units"] * unit_size, 2)
            profit_cash = round(opp["profit_units"] * unit_size, 2)
            return_cash = round(opp["guaranteed_return_units"] * unit_size, 2)
            n = len(opp["outcomes"])
            cols_css = " ".join(["1fr"] * n)

            bets_html = ""
            for j in range(n):
                outcome = opp["outcomes"][j]
                odds = opp["best_odds"][j]
                book = opp["bookmakers"][j]
                units = opp["unit_stakes"][j]
                cash = round(units * unit_size, 2)
                bets_html += f"""
                <div class="bet-card">
                    <div class="bet-outcome-name">{outcome}</div>
                    <div class="bet-line">
                        <span class="bet-line-label">Odds</span>
                        <span class="bet-line-val val-odds">{odds}</span>
                    </div>
                    <div class="bet-line">
                        <span class="bet-line-label">Units</span>
                        <span class="bet-line-val val-units">{units}</span>
                    </div>
                    <div class="bet-line">
                        <span class="bet-line-label">Stake</span>
                        <span class="bet-line-val val-cash">£{cash}</span>
                    </div>
                    <div class="book-badge">{book}</div>
                </div>"""

            st.markdown(f"""
            <div class="opp-card">
                <div class="opp-card-header">
                    <div>
                        <div class="opp-event-name">{opp["event"]}</div>
                        <div class="opp-meta">
                            <span>{opp["sport"]}</span>
                            <span>{MARKET_KEYS.get(opp["market"], opp["market"])}</span>
                            <span>{opp["commence_time"][:10]}</span>
                        </div>
                    </div>
                    <div class="profit-pill">+{opp["profit_percent"]}%</div>
                </div>

                <div class="stats-row">
                    <div class="stat-box">
                        <div class="stat-box-label">Arb %</div>
                        <div class="stat-box-value">{opp["arb_percent"]}%</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-box-label">Total Stake</div>
                        <div class="stat-box-value">£{total_cash}</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-box-label">Return</div>
                        <div class="stat-box-value">£{return_cash}</div>
                    </div>
                </div>

                <div class="bets-label">Bets to place</div>
                <div style="display:grid; grid-template-columns:{cols_css}; gap:10px;">
                    {bets_html}
                </div>
                <div class="warn-line">⚠ Always verify odds on bookmaker site before placing — prices change rapidly</div>
            </div>
            """, unsafe_allow_html=True)

if auto_refresh:
    time.sleep(refresh_mins * 60)
    st.rerun()
