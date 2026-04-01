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
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0a0e1a;
    color: #e2e8f0;
}

section[data-testid="stSidebar"] {
    background-color: #0d1117;
    border-right: 1px solid #1e2d40;
}

section[data-testid="stSidebar"] * {
    color: #94a3b8 !important;
}

section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stNumberInput label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stMultiSelect label {
    color: #64748b !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

.stButton > button {
    background: linear-gradient(135deg, #0ea5e9, #0284c7);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 12px 32px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    width: 100%;
    transition: all 0.2s;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #38bdf8, #0ea5e9);
    transform: translateY(-1px);
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 24px 0;
}

.metric-card {
    background: #0d1117;
    border: 1px solid #1e2d40;
    border-radius: 8px;
    padding: 16px 20px;
}

.metric-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #475569;
    margin-bottom: 6px;
    font-family: 'IBM Plex Mono', monospace;
}

.metric-value {
    font-size: 24px;
    font-weight: 600;
    color: #e2e8f0;
    font-family: 'IBM Plex Mono', monospace;
}

.metric-value.positive { color: #10b981; }
.metric-value.highlight { color: #0ea5e9; }

.opp-card {
    background: #0d1117;
    border: 1px solid #1e2d40;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}

.opp-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, #10b981, #0ea5e9);
}

.opp-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
}

.opp-event {
    font-size: 16px;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 4px;
}

.opp-meta {
    font-size: 12px;
    color: #475569;
    font-family: 'IBM Plex Mono', monospace;
}

.profit-badge {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #10b981;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    white-space: nowrap;
}

.opp-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 20px;
    padding: 14px;
    background: #070b14;
    border-radius: 6px;
    border: 1px solid #131c2e;
}

.stat-item { text-align: center; }

.stat-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #334155;
    margin-bottom: 4px;
    font-family: 'IBM Plex Mono', monospace;
}

.stat-value {
    font-size: 15px;
    font-weight: 500;
    color: #94a3b8;
    font-family: 'IBM Plex Mono', monospace;
}

.bets-grid {
    display: grid;
    gap: 10px;
}

.bet-row {
    display: grid;
    gap: 10px;
    align-items: center;
}

.bet-cell {
    background: #070b14;
    border: 1px solid #131c2e;
    border-radius: 6px;
    padding: 14px 16px;
}

.bet-outcome {
    font-size: 13px;
    font-weight: 600;
    color: #cbd5e1;
    margin-bottom: 10px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.bet-detail {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
}

.bet-detail-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #334155;
    font-family: 'IBM Plex Mono', monospace;
}

.bet-detail-value {
    font-size: 13px;
    font-weight: 500;
    font-family: 'IBM Plex Mono', monospace;
    color: #94a3b8;
}

.bet-detail-value.odds { color: #0ea5e9; }
.bet-detail-value.stake { color: #10b981; }

.bookmaker-tag {
    display: inline-block;
    margin-top: 8px;
    font-size: 10px;
    color: #475569;
    background: #0d1117;
    border: 1px solid #1e2d40;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace;
}

.warning-text {
    font-size: 11px;
    color: #334155;
    text-align: center;
    margin-top: 16px;
    font-family: 'IBM Plex Mono', monospace;
}

.no-opps {
    text-align: center;
    padding: 60px 20px;
    color: #334155;
}

.no-opps-icon {
    font-size: 40px;
    margin-bottom: 16px;
}

.no-opps-text {
    font-size: 16px;
    color: #475569;
    margin-bottom: 8px;
}

.no-opps-sub {
    font-size: 13px;
    color: #334155;
    font-family: 'IBM Plex Mono', monospace;
}

.header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 20px;
    border-bottom: 1px solid #1e2d40;
    margin-bottom: 24px;
}

.header-title {
    font-size: 22px;
    font-weight: 600;
    color: #e2e8f0;
    letter-spacing: -0.02em;
}

.header-subtitle {
    font-size: 12px;
    color: #334155;
    font-family: 'IBM Plex Mono', monospace;
    margin-top: 2px;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    display: inline-block;
    margin-right: 6px;
    box-shadow: 0 0 6px #10b981;
}

.section-title {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #334155;
    margin-bottom: 12px;
    font-family: 'IBM Plex Mono', monospace;
}

div[data-testid="stExpander"] {
    background: transparent !important;
    border: none !important;
}

.stAlert { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ArbScanner Pro")
    st.markdown("---")

    api_key = st.text_input("Odds API Key", value=os.getenv("ODDS_API_KEY", ""), type="password")
    unit_size = st.number_input("Unit Size (£)", min_value=1.0, max_value=10000.0, value=10.0, step=1.0,
        help="Each unit stake is multiplied by this. E.g. unit size 50 means 1.0 unit = £50")
    min_profit = st.slider("Min Profit %", min_value=0.0, max_value=5.0, value=0.5, step=0.1)

    st.markdown("---")
    selected_markets = st.multiselect("Markets",
        options=list(MARKET_KEYS.keys()),
        default=list(MARKET_KEYS.keys()),
        format_func=lambda k: MARKET_KEYS[k])

    st.markdown("---")
    auto_refresh = st.toggle("Auto-refresh", value=False)
    refresh_mins = st.number_input("Interval (mins)", min_value=5, max_value=120, value=60, disabled=not auto_refresh)

# ── Header ───────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="header-bar">
    <div>
        <div class="header-title">⚡ ArbScanner Pro</div>
        <div class="header-subtitle">Last scan: {datetime.now().strftime("%d %b %Y %H:%M:%S UTC")}</div>
    </div>
    <div style="text-align:right">
        <div style="font-size:12px; color:#334155; font-family:'IBM Plex Mono',monospace;">Unit size</div>
        <div style="font-size:20px; font-weight:600; color:#0ea5e9; font-family:'IBM Plex Mono',monospace;">£{unit_size:.0f}</div>
    </div>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.markdown("""
    <div class="no-opps">
        <div class="no-opps-icon">🔑</div>
        <div class="no-opps-text">Enter your Odds API key in the sidebar to begin</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

scan_clicked = st.button("⚡ SCAN MARKETS", type="primary")

# ── Scan ─────────────────────────────────────────────────────────────────────

if scan_clicked or auto_refresh:
    with st.spinner("Connecting to odds feeds..."):
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

    # ── Metrics ──────────────────────────────────────────────────────────────

    best_profit = filtered[0]["profit_percent"] if filtered else 0
    best_cash = round(filtered[0]["profit_units"] * unit_size, 2) if filtered else 0

    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Events Scanned</div>
            <div class="metric-value highlight">{len(all_events)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Arbs Found</div>
            <div class="metric-value {'positive' if filtered else ''}">{len(filtered)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Best Profit %</div>
            <div class="metric-value {'positive' if filtered else ''}">{best_profit}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Best Profit £</div>
            <div class="metric-value {'positive' if filtered else ''}">£{best_cash}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Opportunities ─────────────────────────────────────────────────────────

    if not filtered:
        st.markdown("""
        <div class="no-opps">
            <div class="no-opps-icon">📡</div>
            <div class="no-opps-text">No opportunities above threshold</div>
            <div class="no-opps-sub">Try lowering the min profit % or scan again later</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-title">{len(filtered)} opportunit{"y" if len(filtered)==1 else "ies"} found</div>', unsafe_allow_html=True)

        for i, opp in enumerate(filtered, 1):
            total_cash = round(opp["total_staked_units"] * unit_size, 2)
            profit_cash = round(opp["profit_units"] * unit_size, 2)
            return_cash = round(opp["guaranteed_return_units"] * unit_size, 2)
            n = len(opp["outcomes"])
            grid_cols = " ".join(["1fr"] * n)

            bets_html = ""
            for j in range(n):
                outcome = opp["outcomes"][j]
                odds = opp["best_odds"][j]
                book = opp["bookmakers"][j]
                units = opp["unit_stakes"][j]
                cash = round(units * unit_size, 2)
                bets_html += f"""
                <div class="bet-cell">
                    <div class="bet-outcome">{outcome}</div>
                    <div class="bet-detail">
                        <span class="bet-detail-label">Odds</span>
                        <span class="bet-detail-value odds">{odds}</span>
                    </div>
                    <div class="bet-detail">
                        <span class="bet-detail-label">Units</span>
                        <span class="bet-detail-value">{units}</span>
                    </div>
                    <div class="bet-detail">
                        <span class="bet-detail-label">Stake</span>
                        <span class="bet-detail-value stake">£{cash}</span>
                    </div>
                    <div class="bookmaker-tag">{book}</div>
                </div>
                """

            st.markdown(f"""
            <div class="opp-card">
                <div class="opp-header">
                    <div>
                        <div class="opp-event">{opp["event"]}</div>
                        <div class="opp-meta">{opp["sport"]} &nbsp;·&nbsp; {MARKET_KEYS.get(opp["market"], opp["market"])} &nbsp;·&nbsp; {opp["commence_time"][:10]}</div>
                    </div>
                    <div class="profit-badge">+{opp["profit_percent"]}%</div>
                </div>

                <div class="opp-stats">
                    <div class="stat-item">
                        <div class="stat-label">Arb %</div>
                        <div class="stat-value">{opp["arb_percent"]}%</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Total Stake</div>
                        <div class="stat-value">£{total_cash}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Guaranteed Return</div>
                        <div class="stat-value">£{return_cash}</div>
                    </div>
                </div>

                <div class="section-title">Bets to place</div>
                <div class="bet-row" style="grid-template-columns: {grid_cols};">
                    {bets_html}
                </div>

                <div class="warning-text">⚠ Verify odds on bookmaker site before placing — prices change rapidly</div>
            </div>
            """, unsafe_allow_html=True)

if auto_refresh:
    time.sleep(refresh_mins * 60)
    st.rerun()
