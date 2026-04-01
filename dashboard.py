import os
import json
import time
import streamlit as st
from datetime import datetime, timezone
from dotenv import load_dotenv
from odds_fetcher import fetch_all_sports, MARKET_KEYS
from arb_calculator import check_event_for_arb
from tracker import get_sheet, log_bet, get_all_bets, get_summary_stats

load_dotenv()

st.set_page_config(page_title="ArbScanner Pro", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif;background-color:#0f1729!important;color:#e2e8f0}
.stApp{background:linear-gradient(135deg,#0f1729 0%,#111827 50%,#0f1729 100%)!important}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a0f1e 0%,#0d1428 100%)!important;border-right:1px solid rgba(99,102,241,0.15)!important}
section[data-testid="stSidebar"] label{color:#64748b!important;font-size:10px!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:0.1em!important}
.stButton>button{background:linear-gradient(135deg,#6366f1 0%,#4f46e5 100%)!important;color:white!important;border:none!important;border-radius:12px!important;padding:14px 32px!important;font-family:'Inter',sans-serif!important;font-weight:600!important;font-size:13px!important;letter-spacing:0.08em!important;text-transform:uppercase!important;width:100%!important;box-shadow:0 4px 24px rgba(99,102,241,0.3)!important}
.stButton>button:hover{background:linear-gradient(135deg,#818cf8 0%,#6366f1 100%)!important;box-shadow:0 8px 32px rgba(99,102,241,0.5)!important;transform:translateY(-1px)!important}
.stTabs [data-baseweb="tab-list"]{background:rgba(99,102,241,0.08)!important;border-radius:10px!important;padding:4px!important;border:1px solid rgba(99,102,241,0.15)!important}
.stTabs [data-baseweb="tab"]{color:#475569!important;font-size:12px!important;font-weight:600!important;border-radius:8px!important}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#6366f1,#4f46e5)!important;color:white!important}
.stNumberInput input{background:rgba(99,102,241,0.08)!important;border:1px solid rgba(99,102,241,0.2)!important;border-radius:8px!important;color:#e2e8f0!important;font-family:'JetBrains Mono',monospace!important}
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:28px}
.metric-grid-6{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:28px}
.metric-card{background:linear-gradient(135deg,rgba(99,102,241,0.08) 0%,rgba(79,70,229,0.05) 100%);border:1px solid rgba(99,102,241,0.15);border-radius:16px;padding:18px 20px;position:relative;overflow:hidden}
.metric-card::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#6366f1,#818cf8);opacity:0.6}
.metric-card.green::after{background:linear-gradient(90deg,#10b981,#34d399)}
.metric-card.amber::after{background:linear-gradient(90deg,#f59e0b,#fbbf24)}
.metric-label{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:#475569;margin-bottom:8px;font-family:'JetBrains Mono',monospace}
.metric-value{font-size:26px;font-weight:700;color:#e2e8f0;font-family:'JetBrains Mono',monospace;letter-spacing:-0.02em}
.metric-value.green{color:#34d399}.metric-value.blue{color:#818cf8}.metric-value.amber{color:#fbbf24}
.metric-sub{font-size:11px;color:#475569;margin-top:4px;font-family:'JetBrains Mono',monospace}
.section-label{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.12em;color:#475569;margin-bottom:14px;font-family:'JetBrains Mono',monospace;display:flex;align-items:center;gap:8px}
.section-label::after{content:'';flex:1;height:1px;background:rgba(99,102,241,0.15)}
.opp-card{background:linear-gradient(135deg,rgba(15,23,41,0.9) 0%,rgba(13,20,40,0.95) 100%);border:1px solid rgba(99,102,241,0.2);border-radius:16px;padding:22px 24px;margin-bottom:14px;position:relative;overflow:hidden}
.opp-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(180deg,#6366f1,#34d399)}
.opp-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:18px}
.opp-event{font-size:16px;font-weight:600;color:#f1f5f9;margin-bottom:5px}
.opp-meta{font-size:11px;color:#475569;font-family:'JetBrains Mono',monospace;display:flex;gap:8px;flex-wrap:wrap}
.opp-meta span{background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.15);padding:2px 8px;border-radius:4px}
.profit-pill{background:linear-gradient(135deg,rgba(52,211,153,0.2),rgba(16,185,129,0.1));border:1px solid rgba(52,211,153,0.35);color:#34d399;padding:8px 16px;border-radius:50px;font-size:14px;font-weight:700;font-family:'JetBrains Mono',monospace;white-space:nowrap}
.stats-row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:20px}
.stat-box{background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.12);border-radius:10px;padding:12px 14px;text-align:center}
.stat-box-label{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:#334155;margin-bottom:5px;font-family:'JetBrains Mono',monospace}
.stat-box-value{font-size:14px;font-weight:600;color:#94a3b8;font-family:'JetBrains Mono',monospace}
.bet-card{background:rgba(99,102,241,0.05);border:1px solid rgba(99,102,241,0.12);border-radius:12px;padding:14px 16px}
.bet-outcome{font-size:13px;font-weight:600;color:#cbd5e1;margin-bottom:12px}
.bet-line{display:flex;justify-content:space-between;margin-bottom:5px}
.bet-line-label{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#334155;font-family:'JetBrains Mono',monospace}
.bet-line-val{font-size:13px;font-weight:600;font-family:'JetBrains Mono',monospace}
.val-odds{color:#818cf8}.val-units{color:#94a3b8}.val-profit{color:#34d399}
.book-badge{margin-top:10px;display:inline-block;font-size:9px;color:#475569;background:rgba(15,23,41,0.8);border:1px solid rgba(99,102,241,0.12);padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace}
.log-section{background:rgba(99,102,241,0.05);border:1px solid rgba(99,102,241,0.15);border-radius:12px;padding:16px;margin-top:16px}
.log-section-title{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:#475569;margin-bottom:12px;font-family:'JetBrains Mono',monospace}
.log-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px;margin-bottom:14px;padding:12px;background:rgba(15,23,41,0.5);border-radius:8px;border:1px solid rgba(99,102,241,0.1)}
.log-sum-label{font-size:9px;text-transform:uppercase;letter-spacing:0.08em;color:#334155;font-family:'JetBrains Mono',monospace;margin-bottom:3px}
.log-sum-value{font-size:13px;font-weight:600;color:#94a3b8;font-family:'JetBrains Mono',monospace}
.log-sum-value.green{color:#34d399}
.warn-line{font-size:10px;color:#334155;text-align:center;margin-top:18px;font-family:'JetBrains Mono',monospace}
.empty-state{text-align:center;padding:64px 20px}
.empty-icon{font-size:36px;margin-bottom:14px}
.empty-title{font-size:16px;font-weight:500;color:#475569;margin-bottom:6px}
.empty-sub{font-size:12px;color:#334155;font-family:'JetBrains Mono',monospace}
.header-wrap{display:flex;align-items:center;justify-content:space-between;padding:8px 0 24px 0;border-bottom:1px solid rgba(99,102,241,0.15);margin-bottom:28px}
.header-left{display:flex;align-items:center;gap:14px}
.header-logo{width:44px;height:44px;background:linear-gradient(135deg,#6366f1,#4f46e5);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px;box-shadow:0 4px 16px rgba(99,102,241,0.4)}
.header-title{font-size:20px;font-weight:700;color:#f1f5f9;letter-spacing:-0.02em}
.header-sub{font-size:11px;color:#475569;font-family:'JetBrains Mono',monospace;margin-top:2px}
.header-unit{text-align:right;background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);border-radius:12px;padding:10px 18px}
.header-unit-label{font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.1em;font-weight:600}
.header-unit-value{font-size:22px;font-weight:700;color:#818cf8;font-family:'JetBrains Mono',monospace}
</style>
""", unsafe_allow_html=True)

def load_credentials():
    raw = os.getenv("GOOGLE_CREDENTIALS", "")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
creds_dict = load_credentials()

with st.sidebar:
    st.markdown("### ⚡ ArbScanner Pro")
    st.divider()
    api_key = st.text_input("Odds API Key", value=os.getenv("ODDS_API_KEY", ""), type="password")
    unit_size = st.number_input("Unit Size", min_value=1.0, max_value=10000.0, value=10.0, step=1.0,
        help="The value of 1 unit in your currency. E.g. 1 unit = 50 means a 2.3 unit stake = 150")
    min_profit = st.slider("Min Profit %", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
    st.divider()
    selected_markets = st.multiselect("Markets", options=list(MARKET_KEYS.keys()), default=list(MARKET_KEYS.keys()), format_func=lambda k: MARKET_KEYS[k])
    st.divider()
    auto_refresh = st.toggle("Auto-refresh", value=False)
    refresh_mins = st.number_input("Interval mins", min_value=5, max_value=120, value=60, disabled=not auto_refresh)

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
        <div class="header-unit-value">{unit_size:.0f}</div>
    </div>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.markdown('<div class="empty-state"><div class="empty-icon">🔑</div><div class="empty-title">Enter your Odds API key in the sidebar</div></div>', unsafe_allow_html=True)
    st.stop()

tab1, tab2, tab3 = st.tabs(["⚡  Live Scanner", "📊  Analytics", "📋  Bet History"])

with tab1:
    scan_clicked = st.button("⚡  SCAN MARKETS NOW", key="scan_btn")

    if "scan_results" not in st.session_state:
        st.session_state.scan_results = []
    if "logged_bets" not in st.session_state:
        st.session_state.logged_bets = set()

    if scan_clicked or auto_refresh:
        with st.spinner("Connecting to live odds feeds..."):
            all_events = fetch_all_sports(api_key)
        if not all_events:
            st.error("Could not fetch odds. Check your API key.")
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
            key=lambda x: x["profit_percent"], reverse=True
        )
        st.session_state.scan_results = filtered
        st.session_state.num_events = len(all_events)
        st.session_state.logged_bets = set()

    filtered = st.session_state.get("scan_results", [])
    num_events = st.session_state.get("num_events", 0)

    if num_events > 0:
        best_profit = filtered[0]["profit_percent"] if filtered else 0
        best_units = round(filtered[0]["profit_units"], 4) if filtered else 0

        st.markdown(f"""
        <div class="metric-grid">
            <div class="metric-card"><div class="metric-label">Events Scanned</div><div class="metric-value blue">{num_events}</div></div>
            <div class="metric-card"><div class="metric-label">Arbs Found</div><div class="metric-value {'green' if filtered else ''}">{len(filtered)}</div></div>
            <div class="metric-card {'green' if filtered else ''}"><div class="metric-label">Best Profit %</div><div class="metric-value {'green' if filtered else ''}">{best_profit}%</div></div>
            <div class="metric-card {'green' if filtered else ''}"><div class="metric-label">Best Profit (units)</div><div class="metric-value {'green' if filtered else ''}">{best_units}</div></div>
        </div>""", unsafe_allow_html=True)

    if not filtered and num_events == 0:
        st.markdown('<div class="empty-state"><div class="empty-icon">📡</div><div class="empty-title">Hit Scan to find arbitrage opportunities</div><div class="empty-sub">covers 30+ sports and leagues worldwide</div></div>', unsafe_allow_html=True)
    elif not filtered:
        st.markdown('<div class="empty-state"><div class="empty-icon">📡</div><div class="empty-title">No opportunities above threshold</div><div class="empty-sub">lower the min profit % or scan again later</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-label">{len(filtered)} opportunit{"y" if len(filtered)==1 else "ies"} found</div>', unsafe_allow_html=True)
        worksheet = get_sheet(creds_dict, SHEET_ID) if creds_dict and SHEET_ID else None

        for i, opp in enumerate(filtered, 1):
            total_units = opp["total_staked_units"]
            profit_units = opp["profit_units"]
            return_units = opp["guaranteed_return_units"]
            n = len(opp["outcomes"])
            cols_css = " ".join(["1fr"] * n)

            bets_html = ""
            for j in range(n):
                outcome = opp["outcomes"][j]
                odds = opp["best_odds"][j]
                book = opp["bookmakers"][j]
                units = opp["unit_stakes"][j]
                bets_html += f"""
                <div class="bet-card">
                    <div class="bet-outcome">{outcome}</div>
                    <div class="bet-line"><span class="bet-line-label">Odds</span><span class="bet-line-val val-odds">{odds}</span></div>
                    <div class="bet-line"><span class="bet-line-label">Suggested units</span><span class="bet-line-val val-units">{units}</span></div>
                    <div class="book-badge">{book}</div>
                </div>"""

            already_logged = i in st.session_state.logged_bets

            st.markdown(f"""
            <div class="opp-card">
                <div class="opp-header">
                    <div>
                        <div class="opp-event">{opp["event"]}</div>
                        <div class="opp-meta"><span>{opp["sport"]}</span><span>{MARKET_KEYS.get(opp["market"],opp["market"])}</span><span>{opp["commence_time"][:10]}</span></div>
                    </div>
                    <div class="profit-pill">+{opp["profit_percent"]}%</div>
                </div>
                <div class="stats-row">
                    <div class="stat-box"><div class="stat-box-label">Arb %</div><div class="stat-box-value">{opp["arb_percent"]}%</div></div>
                    <div class="stat-box"><div class="stat-box-label">Total units staked</div><div class="stat-box-value">{round(total_units,4)}</div></div>
                    <div class="stat-box"><div class="stat-box-label">Guaranteed return</div><div class="stat-box-value">{round(return_units,4)} units</div></div>
                </div>
                <div class="section-label" style="margin-bottom:10px;">Bets to place</div>
                <div style="display:grid;grid-template-columns:{cols_css};gap:10px;">{bets_html}</div>
                <div class="warn-line">Always verify odds on bookmaker site before placing</div>
            </div>
            """, unsafe_allow_html=True)

            if already_logged:
                st.success(f"✅ Bet #{i} already logged this session")
            elif worksheet:
                st.markdown('<div class="log-section"><div class="log-section-title">Log this bet to tracker</div>', unsafe_allow_html=True)

                input_cols = st.columns(n)
                actual_stakes = []
                for j in range(n):
                    with input_cols[j]:
                        suggested = opp["unit_stakes"][j]
                        stake = st.number_input(
                            f"{opp['outcomes'][j]} — units staked",
                            min_value=0.0,
                            value=float(suggested),
                            step=0.01,
                            format="%.4f",
                            key=f"stake_{i}_{j}"
                        )
                        actual_stakes.append(stake)

                total_actual = sum(actual_stakes)
                total_actual_value = round(total_actual * unit_size, 2)
                profit_estimate = round(profit_units * unit_size, 2)

                st.markdown(f"""
                <div class="log-summary">
                    <div>
                        <div class="log-sum-label">Total units</div>
                        <div class="log-sum-value">{round(total_actual, 4)}</div>
                    </div>
                    <div>
                        <div class="log-sum-label">Total value</div>
                        <div class="log-sum-value">{total_actual_value}</div>
                    </div>
                    <div>
                        <div class="log-sum-label">Est. profit</div>
                        <div class="log-sum-value green">{profit_estimate}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                notes = st.text_input("Notes (optional)", key=f"notes_{i}", placeholder="e.g. placed on mobile, odds moved slightly...")

                st.markdown('</div>', unsafe_allow_html=True)

                if st.button(f"✅  LOG BET #{i} TO TRACKER", key=f"log_{i}"):
                    opp_to_log = dict(opp)
                    opp_to_log["unit_stakes"] = actual_stakes
                    opp_to_log["total_staked_units"] = total_actual
                    if log_bet(worksheet, opp_to_log, unit_size, notes):
                        st.session_state.logged_bets.add(i)
                        st.success(f"✅ Bet #{i} logged to Google Sheets!")
                        st.rerun()
                    else:
                        st.error("Failed to log. Check Google Sheets connection.")
            else:
                st.info("Add Google Sheets credentials to Streamlit secrets to enable bet logging.")

    if auto_refresh:
        time.sleep(refresh_mins * 60)
        st.rerun()

with tab2:
    st.markdown('<div class="section-label">Financial Analytics</div>', unsafe_allow_html=True)
    if not creds_dict or not SHEET_ID:
        st.info("Add GOOGLE_CREDENTIALS and GOOGLE_SHEET_ID to Streamlit secrets to unlock analytics.")
    else:
        worksheet = get_sheet(creds_dict, SHEET_ID)
        if not worksheet:
            st.error("Could not connect to Google Sheets.")
        else:
            bets = get_all_bets(worksheet)
            if not bets:
                st.markdown('<div class="empty-state"><div class="empty-icon">📊</div><div class="empty-title">No bets logged yet</div><div class="empty-sub">log your first bet from the scanner tab</div></div>', unsafe_allow_html=True)
            else:
                stats = get_summary_stats(bets, unit_size)
                irr_display = f"{stats['irr']}%" if stats['irr'] is not None else "Need 2+ settled"
                st.markdown(f"""
                <div class="metric-grid-6">
                    <div class="metric-card green"><div class="metric-label">Total Profit</div><div class="metric-value green">{stats['total_profit']}</div><div class="metric-sub">{stats['settled_bets']} settled bets</div></div>
                    <div class="metric-card green"><div class="metric-label">ROI</div><div class="metric-value green">{stats['roi']}%</div><div class="metric-sub">return on investment</div></div>
                    <div class="metric-card"><div class="metric-label">IRR Annualised</div><div class="metric-value blue">{irr_display}</div><div class="metric-sub">equiv. annual return</div></div>
                    <div class="metric-card"><div class="metric-label">Total Staked</div><div class="metric-value">{stats['total_staked']}</div><div class="metric-sub">capital deployed</div></div>
                    <div class="metric-card amber"><div class="metric-label">Pending Exposure</div><div class="metric-value amber">{stats['pending_exposure']}</div><div class="metric-sub">{stats['pending_bets']} open bets</div></div>
                    <div class="metric-card"><div class="metric-label">Total Bets</div><div class="metric-value blue">{stats['total_bets']}</div><div class="metric-sub">all time</div></div>
                </div>""", unsafe_allow_html=True)

                import plotly.graph_objects as go
                chart_bg = "rgba(0,0,0,0)"
                font_color = "#64748b"
                grid_color = "rgba(99,102,241,0.1)"

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="section-label">Cumulative P&L</div>', unsafe_allow_html=True)
                    pnl_data = stats["cumulative_pnl"]
                    if pnl_data:
                        dates = [d[0] for d in pnl_data]
                        values = [d[1] for d in pnl_data]
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=dates, y=values, mode="lines+markers", line=dict(color="#6366f1", width=2), marker=dict(color="#818cf8", size=6), fill="tozeroy", fillcolor="rgba(99,102,241,0.08)"))
                        fig.update_layout(paper_bgcolor=chart_bg, plot_bgcolor=chart_bg, font=dict(color=font_color, family="JetBrains Mono"), xaxis=dict(gridcolor=grid_color), yaxis=dict(gridcolor=grid_color), margin=dict(l=0,r=0,t=10,b=0), showlegend=False, height=280)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.caption("No settled bets yet.")

                with col2:
                    st.markdown('<div class="section-label">Month-on-Month Return %</div>', unsafe_allow_html=True)
                    mom = stats["mom_returns"]
                    if mom:
                        months = list(mom.keys())
                        returns = [mom[m]["return_pct"] for m in months]
                        colors = ["#34d399" if r >= 0 else "#f87171" for r in returns]
                        fig2 = go.Figure()
                        fig2.add_trace(go.Bar(x=months, y=returns, marker_color=colors))
                        fig2.update_layout(paper_bgcolor=chart_bg, plot_bgcolor=chart_bg, font=dict(color=font_color, family="JetBrains Mono"), xaxis=dict(gridcolor=grid_color), yaxis=dict(gridcolor=grid_color, ticksuffix="%"), margin=dict(l=0,r=0,t=10,b=0), showlegend=False, height=280)
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.caption("No settled bets yet.")

                col3, col4 = st.columns(2)
                with col3:
                    st.markdown('<div class="section-label">Bookmaker Leaderboard</div>', unsafe_allow_html=True)
                    book_stats = stats["bookmaker_stats"]
                    if book_stats:
                        fig3 = go.Figure()
                        fig3.add_trace(go.Bar(x=list(book_stats.values()), y=list(book_stats.keys()), orientation="h", marker_color="#6366f1"))
                        fig3.update_layout(paper_bgcolor=chart_bg, plot_bgcolor=chart_bg, font=dict(color=font_color, family="JetBrains Mono"), xaxis=dict(gridcolor=grid_color), yaxis=dict(gridcolor=grid_color), margin=dict(l=0,r=0,t=10,b=0), showlegend=False, height=280)
                        st.plotly_chart(fig3, use_container_width=True)
                    else:
                        st.caption("No bookmaker data yet.")

                with col4:
                    st.markdown('<div class="section-label">Sport Breakdown</div>', unsafe_allow_html=True)
                    sport_stats = stats["sport_stats"]
                    if sport_stats:
                        fig4 = go.Figure()
                        fig4.add_trace(go.Pie(labels=list(sport_stats.keys()), values=list(sport_stats.values()), hole=0.6, marker_colors=["#6366f1","#34d399","#818cf8","#fbbf24","#f87171"]))
                        fig4.update_layout(paper_bgcolor=chart_bg, font=dict(color=font_color, family="JetBrains Mono"), margin=dict(l=0,r=0,t=10,b=0), legend=dict(font=dict(color="#64748b", size=11)), height=280)
                        st.plotly_chart(fig4, use_container_width=True)
                    else:
                        st.caption("No sport data yet.")

with tab3:
    st.markdown('<div class="section-label">Bet History</div>', unsafe_allow_html=True)
    if not creds_dict or not SHEET_ID:
        st.info("Add GOOGLE_CREDENTIALS and GOOGLE_SHEET_ID to Streamlit secrets to see bet history.")
    else:
        worksheet = get_sheet(creds_dict, SHEET_ID)
        if not worksheet:
            st.error("Could not connect to Google Sheets.")
        else:
            bets = get_all_bets(worksheet)
            if not bets:
                st.markdown('<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-title">No bets logged yet</div><div class="empty-sub">your logged bets will appear here</div></div>', unsafe_allow_html=True)
            else:
                import pandas as pd
                df = pd.DataFrame(bets)
                display_cols = ["Date","Event","Sport","Market","Total Staked","Guaranteed Return","Profit","Profit %","Status","Actual Profit","Notes"]
                display_cols = [c for c in display_cols if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
                st.caption(f"Showing {len(bets)} bets. Edit Status and Actual Profit directly in your Google Sheet to update analytics.")
                st.link_button("Open Google Sheet", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}")
