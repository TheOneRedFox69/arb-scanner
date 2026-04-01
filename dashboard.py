import os
import json
import time
import streamlit as st
from datetime import datetime, timezone, date
from dotenv import load_dotenv
from odds_fetcher import fetch_all_sports, MARKET_KEYS
from arb_calculator import check_event_for_arb
from tracker import get_sheet, log_bet, get_all_bets, get_summary_stats
from bookmaker_ratings import get_rating, get_opportunity_risk_score
from bankroll import kelly_criterion, calculate_bankroll_stats, project_growth, break_even_calculator

load_dotenv()

st.set_page_config(page_title="ArbScanner Pro", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

BACKGROUND_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" style="position:fixed;top:0;left:0;z-index:-1;opacity:0.03;pointer-events:none;">
  <defs>
    <pattern id="bg-pattern" x="0" y="0" width="320" height="320" patternUnits="userSpaceOnUse">
      <!-- Football/Soccer ball -->
      <circle cx="30" cy="30" r="18" fill="none" stroke="white" stroke-width="1.2"/>
      <path d="M30 12 L36 20 L30 28 L24 20 Z" fill="none" stroke="white" stroke-width="1"/>
      <!-- Bar chart (profit) -->
      <rect x="140" y="55" width="6" height="20" fill="none" stroke="white" stroke-width="1.2" rx="1"/>
      <rect x="150" y="45" width="6" height="30" fill="none" stroke="white" stroke-width="1.2" rx="1"/>
      <rect x="160" y="35" width="6" height="40" fill="none" stroke="white" stroke-width="1.2" rx="1"/>
      <!-- Tennis racket -->
      <ellipse cx="260" cy="40" rx="14" ry="18" fill="none" stroke="white" stroke-width="1.2"/>
      <line x1="260" y1="58" x2="260" y2="80" stroke="white" stroke-width="1.5"/>
      <line x1="246" y1="40" x2="274" y2="40" stroke="white" stroke-width="0.8"/>
      <line x1="260" y1="22" x2="260" y2="58" stroke="white" stroke-width="0.8"/>
      <!-- Coin/currency -->
      <circle cx="80" cy="160" r="16" fill="none" stroke="white" stroke-width="1.2"/>
      <text x="80" y="165" font-size="12" text-anchor="middle" fill="white" font-family="serif">£</text>
      <!-- Trophy -->
      <path d="M190 130 L190 110 L210 110 L210 130 Q210 145 200 148 Q190 145 190 130Z" fill="none" stroke="white" stroke-width="1.2"/>
      <line x1="196" y1="148" x2="196" y2="155" stroke="white" stroke-width="1.2"/>
      <line x1="204" y1="148" x2="204" y2="155" stroke="white" stroke-width="1.2"/>
      <line x1="192" y1="155" x2="208" y2="155" stroke="white" stroke-width="1.2"/>
      <path d="M190 115 Q182 115 182 122 Q182 129 190 129" fill="none" stroke="white" stroke-width="1"/>
      <path d="M210 115 Q218 115 218 122 Q218 129 210 129" fill="none" stroke="white" stroke-width="1"/>
      <!-- Line graph (trending up) -->
      <polyline points="240,200 255,185 270,190 285,170 300,155" fill="none" stroke="white" stroke-width="1.5"/>
      <circle cx="300" cy="155" r="2.5" fill="white"/>
      <!-- Basketball -->
      <circle cx="50" cy="240" r="18" fill="none" stroke="white" stroke-width="1.2"/>
      <path d="M32 240 Q50 228 68 240" fill="none" stroke="white" stroke-width="0.8"/>
      <path d="M32 240 Q50 252 68 240" fill="none" stroke="white" stroke-width="0.8"/>
      <line x1="50" y1="222" x2="50" y2="258" stroke="white" stroke-width="0.8"/>
      <!-- Card/ticket -->
      <rect x="130" y="220" width="60" height="38" rx="4" fill="none" stroke="white" stroke-width="1.2"/>
      <line x1="130" y1="232" x2="190" y2="232" stroke="white" stroke-width="0.8"/>
      <line x1="140" y1="242" x2="170" y2="242" stroke="white" stroke-width="0.8"/>
      <!-- American football -->
      <ellipse cx="260" cy="230" rx="20" ry="13" fill="none" stroke="white" stroke-width="1.2"/>
      <line x1="240" y1="230" x2="280" y2="230" stroke="white" stroke-width="0.8"/>
      <line x1="252" y1="220" x2="252" y2="240" stroke="white" stroke-width="0.6"/>
      <line x1="260" y1="218" x2="260" y2="242" stroke="white" stroke-width="0.6"/>
      <line x1="268" y1="220" x2="268" y2="240" stroke="white" stroke-width="0.6"/>
      <!-- Piggy bank -->
      <ellipse cx="160" cy="290" rx="22" ry="18" fill="none" stroke="white" stroke-width="1.2"/>
      <circle cx="176" cy="283" r="4" fill="none" stroke="white" stroke-width="1"/>
      <line x1="148" y1="300" x2="143" y2="312" stroke="white" stroke-width="1.2"/>
      <line x1="155" y1="303" x2="152" y2="315" stroke="white" stroke-width="1.2"/>
      <line x1="165" y1="305" x2="165" y2="317" stroke="white" stroke-width="1.2"/>
      <line x1="172" y1="303" x2="175" y2="315" stroke="white" stroke-width="1.2"/>
      <rect x="153" y="275" width="14" height="3" rx="1" fill="none" stroke="white" stroke-width="0.8"/>
      <!-- Dice -->
      <rect x="10" y="130" width="28" height="28" rx="4" fill="none" stroke="white" stroke-width="1.2"/>
      <circle cx="18" cy="138" r="2" fill="white"/>
      <circle cx="30" cy="138" r="2" fill="white"/>
      <circle cx="24" cy="144" r="2" fill="white"/>
      <circle cx="18" cy="150" r="2" fill="white"/>
      <circle cx="30" cy="150" r="2" fill="white"/>
      <!-- Hockey puck/ice hockey -->
      <ellipse cx="300" cy="280" rx="16" ry="8" fill="none" stroke="white" stroke-width="1.2"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#bg-pattern)"/>
</svg>
"""

TOOLTIPS = {
    "arb_percent": "The combined implied probability of all outcomes. Below 100% means a guaranteed profit exists. E.g. 97.5% = 2.5% guaranteed profit.",
    "profit_percent": "The guaranteed profit you make regardless of the match result, expressed as a percentage of your total stake.",
    "irr": "Internal Rate of Return — your annualised return rate treating each bet as a cash flow. Equivalent to what your betting capital would earn if it were an investment.",
    "roi": "Return on Investment — total profit divided by total amount staked, expressed as a percentage.",
    "kelly": "Kelly Criterion — a mathematical formula that calculates the optimal stake size to maximise long-term bankroll growth without risking ruin.",
    "unit_size": "The monetary value of one unit. E.g. if unit size = 50, then a stake of 2.3 units means you bet 115 in your currency.",
    "confidence": "A score based on how arb-friendly the bookmakers involved are. Higher score = lower risk of account restriction.",
    "mom": "Month-on-Month return — your profit as a percentage of stakes placed within each calendar month.",
    "pending_exposure": "The total amount currently locked in open (unresolved) bets. This capital is at risk until bets settle.",
    "bookmaker_risk": "How likely this bookmaker is to restrict or close your account if you consistently win through arbitrage betting.",
    "break_even": "The minimum number of arb bets you need to place per month to cover your Odds API subscription cost.",
}

def tooltip(key, label=None):
    tip = TOOLTIPS.get(key, "")
    display = label if label else key.replace("_", " ").title()
    return f'{display} <span title="{tip}" style="cursor:help;color:#6366f1;font-size:11px;border:1px solid rgba(99,102,241,0.4);border-radius:50%;padding:0 4px;font-family:monospace;">?</span>'

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[class*="css"],.stApp{{font-family:'Inter',sans-serif;background-color:#0a0e1a!important;color:#e2e8f0}}
.stApp{{background:linear-gradient(135deg,#0a0e1a 0%,#0d1228 50%,#0a0e1a 100%)!important}}
section[data-testid="stSidebar"]{{background:linear-gradient(180deg,#070a14 0%,#0a0f1e 100%)!important;border-right:1px solid rgba(99,102,241,0.12)!important}}
section[data-testid="stSidebar"] label{{color:#64748b!important;font-size:10px!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:0.1em!important}}
.stButton>button{{background:linear-gradient(135deg,#6366f1 0%,#4f46e5 100%)!important;color:white!important;border:none!important;border-radius:12px!important;padding:14px 32px!important;font-family:'Inter',sans-serif!important;font-weight:600!important;font-size:13px!important;letter-spacing:0.08em!important;text-transform:uppercase!important;width:100%!important;box-shadow:0 4px 24px rgba(99,102,241,0.3)!important;transition:all 0.2s!important}}
.stButton>button:hover{{background:linear-gradient(135deg,#818cf8 0%,#6366f1 100%)!important;box-shadow:0 8px 32px rgba(99,102,241,0.5)!important;transform:translateY(-1px)!important}}
.stTabs [data-baseweb="tab-list"]{{background:rgba(99,102,241,0.06)!important;border-radius:10px!important;padding:4px!important;border:1px solid rgba(99,102,241,0.12)!important}}
.stTabs [data-baseweb="tab"]{{color:#475569!important;font-size:12px!important;font-weight:600!important;border-radius:8px!important}}
.stTabs [aria-selected="true"]{{background:linear-gradient(135deg,#6366f1,#4f46e5)!important;color:white!important}}
.stTextInput input,.stNumberInput input,.stSelectbox select,.stTextArea textarea{{background:rgba(99,102,241,0.06)!important;border:1px solid rgba(99,102,241,0.15)!important;border-radius:8px!important;color:#e2e8f0!important;-webkit-text-fill-color:#e2e8f0!important;font-family:'JetBrains Mono',monospace!important}}
input[type="number"]{{color:#e2e8f0!important;-webkit-text-fill-color:#e2e8f0!important}}
input[type="text"]{{color:#e2e8f0!important;-webkit-text-fill-color:#e2e8f0!important}}
[data-baseweb="input"] input{{color:#e2e8f0!important;-webkit-text-fill-color:#e2e8f0!important}}
[data-baseweb="base-input"] input{{color:#e2e8f0!important;-webkit-text-fill-color:#e2e8f0!important}}
.stSlider [data-baseweb="slider"]{{background:rgba(99,102,241,0.15)!important}}
.metric-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}}
.metric-grid-3{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:24px}}
.metric-grid-6{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:24px}}
.metric-card{{background:linear-gradient(135deg,rgba(99,102,241,0.07) 0%,rgba(79,70,229,0.04) 100%);border:1px solid rgba(99,102,241,0.12);border-radius:16px;padding:18px 20px;position:relative;overflow:hidden;backdrop-filter:blur(10px)}}
.metric-card::after{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#6366f1,#818cf8);opacity:0.5}}
.metric-card.green::after{{background:linear-gradient(90deg,#10b981,#34d399)}}
.metric-card.amber::after{{background:linear-gradient(90deg,#f59e0b,#fbbf24)}}
.metric-card.red::after{{background:linear-gradient(90deg,#ef4444,#f87171)}}
.metric-label{{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:#475569;margin-bottom:8px;font-family:'JetBrains Mono',monospace}}
.metric-value{{font-size:24px;font-weight:700;color:#e2e8f0;font-family:'JetBrains Mono',monospace;letter-spacing:-0.02em}}
.metric-value.green{{color:#34d399}}.metric-value.blue{{color:#818cf8}}.metric-value.amber{{color:#fbbf24}}.metric-value.red{{color:#f87171}}
.metric-sub{{font-size:11px;color:#475569;margin-top:4px;font-family:'JetBrains Mono',monospace}}
.section-label{{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.12em;color:#475569;margin-bottom:14px;font-family:'JetBrains Mono',monospace;display:flex;align-items:center;gap:8px}}
.section-label::after{{content:'';flex:1;height:1px;background:rgba(99,102,241,0.12)}}
.opp-card{{background:linear-gradient(135deg,rgba(10,14,26,0.95) 0%,rgba(13,18,40,0.98) 100%);border:1px solid rgba(99,102,241,0.18);border-radius:16px;padding:22px 24px;margin-bottom:14px;position:relative;overflow:hidden;backdrop-filter:blur(20px)}}
.opp-card::before{{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(180deg,#6366f1,#34d399)}}
.opp-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:18px}}
.opp-event{{font-size:17px;font-weight:600;color:#f1f5f9;margin-bottom:5px;letter-spacing:-0.01em}}
.opp-meta{{font-size:11px;color:#475569;font-family:'JetBrains Mono',monospace;display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}}
.opp-meta span{{background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.14);padding:2px 8px;border-radius:4px}}
.profit-pill{{background:linear-gradient(135deg,rgba(52,211,153,0.18),rgba(16,185,129,0.08));border:1px solid rgba(52,211,153,0.3);color:#34d399;padding:8px 16px;border-radius:50px;font-size:14px;font-weight:700;font-family:'JetBrains Mono',monospace;white-space:nowrap;letter-spacing:-0.01em}}
.stats-row{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}}
.stat-box{{background:rgba(99,102,241,0.05);border:1px solid rgba(99,102,241,0.1);border-radius:10px;padding:12px 14px;text-align:center}}
.stat-box-label{{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:#334155;margin-bottom:5px;font-family:'JetBrains Mono',monospace}}
.stat-box-value{{font-size:14px;font-weight:600;color:#94a3b8;font-family:'JetBrains Mono',monospace}}
.bet-card{{background:rgba(99,102,241,0.04);border:1px solid rgba(99,102,241,0.1);border-radius:12px;padding:14px 16px}}
.bet-outcome{{font-size:13px;font-weight:600;color:#cbd5e1;margin-bottom:10px}}
.bet-line{{display:flex;justify-content:space-between;margin-bottom:5px}}
.bet-line-label{{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#334155;font-family:'JetBrains Mono',monospace}}
.bet-line-val{{font-size:13px;font-weight:600;font-family:'JetBrains Mono',monospace}}
.val-odds{{color:#818cf8}}.val-units{{color:#94a3b8}}.val-profit{{color:#34d399}}
.book-badge{{margin-top:8px;display:inline-block;font-size:9px;color:#475569;background:rgba(10,14,26,0.8);border:1px solid rgba(99,102,241,0.1);padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace}}
.risk-bar{{display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:8px;margin:12px 0;font-size:12px;font-family:'JetBrains Mono',monospace}}
.log-section{{background:rgba(99,102,241,0.04);border:1px solid rgba(99,102,241,0.12);border-radius:12px;padding:16px;margin-top:14px}}
.log-section-title{{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:#475569;margin-bottom:12px;font-family:'JetBrains Mono',monospace}}
.log-summary{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0;padding:12px;background:rgba(10,14,26,0.5);border-radius:8px;border:1px solid rgba(99,102,241,0.08)}}
.log-sum-label{{font-size:9px;text-transform:uppercase;letter-spacing:0.08em;color:#334155;font-family:'JetBrains Mono',monospace;margin-bottom:3px}}
.log-sum-value{{font-size:13px;font-weight:600;color:#94a3b8;font-family:'JetBrains Mono',monospace}}
.log-sum-value.green{{color:#34d399}}
.warn-line{{font-size:10px;color:#334155;text-align:center;margin-top:14px;font-family:'JetBrains Mono',monospace}}
.empty-state{{text-align:center;padding:64px 20px}}
.empty-icon{{font-size:36px;margin-bottom:14px}}
.empty-title{{font-size:16px;font-weight:500;color:#475569;margin-bottom:6px}}
.empty-sub{{font-size:12px;color:#334155;font-family:'JetBrains Mono',monospace}}
.header-wrap{{display:flex;align-items:center;justify-content:space-between;padding:8px 0 24px 0;border-bottom:1px solid rgba(99,102,241,0.12);margin-bottom:28px}}
.header-left{{display:flex;align-items:center;gap:14px}}
.header-logo{{width:48px;height:48px;background:linear-gradient(135deg,#6366f1,#4f46e5);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:22px;box-shadow:0 4px 20px rgba(99,102,241,0.35)}}
.header-title{{font-size:22px;font-weight:700;color:#f1f5f9;letter-spacing:-0.02em}}
.header-sub{{font-size:11px;color:#334155;font-family:'JetBrains Mono',monospace;margin-top:3px}}
.header-right{{display:flex;gap:12px;align-items:center}}
.header-unit{{text-align:right;background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.15);border-radius:12px;padding:10px 18px}}
.header-unit-label{{font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.1em;font-weight:600}}
.header-unit-value{{font-size:20px;font-weight:700;color:#818cf8;font-family:'JetBrains Mono',monospace}}
.bankroll-bar{{height:6px;border-radius:3px;background:rgba(99,102,241,0.1);margin:8px 0;overflow:hidden}}
.bankroll-bar-fill{{height:100%;border-radius:3px;background:linear-gradient(90deg,#6366f1,#34d399);transition:width 0.5s}}
.confidence-stars{{color:#fbbf24;font-size:14px;letter-spacing:2px}}
</style>
{BACKGROUND_SVG}
""", unsafe_allow_html=True)

def load_credentials():
    # Try Streamlit secrets first (production), then env var (local dev)
    try:
        raw = st.secrets.get("GOOGLE_CREDENTIALS", "")
    except Exception:
        raw = ""
    if not raw:
        raw = os.getenv("GOOGLE_CREDENTIALS", "")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None

def load_sheet_id():
    try:
        sid = st.secrets.get("GOOGLE_SHEET_ID", "")
    except Exception:
        sid = ""
    if not sid:
        sid = os.getenv("GOOGLE_SHEET_ID", "")
    return sid

SHEET_ID = load_sheet_id()
creds_dict = load_credentials()

@st.cache_resource(ttl=300)
def get_cached_sheet(sheet_id):
    if not creds_dict or not sheet_id:
        return None
    return get_sheet(creds_dict, sheet_id)

@st.cache_data(ttl=300)
def get_cached_bets(sheet_id):
    ws = get_cached_sheet(sheet_id)
    if not ws:
        return []
    return get_all_bets(ws)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚡ ArbScanner Pro")
    st.divider()
    api_key = st.text_input("Odds API Key", value=os.getenv("ODDS_API_KEY", ""), type="password")
    st.markdown(tooltip("unit_size", "Unit Size"), unsafe_allow_html=True)
    unit_size = st.number_input("", min_value=1, max_value=100000, value=10, step=1, key="unit_size_input",
        label_visibility="collapsed")
    st.markdown(tooltip("arb_percent", "Min Profit %"), unsafe_allow_html=True)
    min_profit = st.slider("", min_value=0.0, max_value=5.0, value=0.5, step=0.1, key="min_profit_slider",
        label_visibility="collapsed")
    st.divider()
    st.markdown("**Bankroll Management**")
    st.markdown(tooltip("kelly", "Bankroll (units)"), unsafe_allow_html=True)
    total_bankroll = st.number_input("", min_value=1, max_value=1000000, value=1000, step=10, key="bankroll_input",
        label_visibility="collapsed")
    api_cost = st.number_input("Monthly API cost", min_value=0, max_value=1000, value=20, step=1)
    st.divider()
    selected_markets = st.multiselect("Markets", options=list(MARKET_KEYS.keys()), default=list(MARKET_KEYS.keys()), format_func=lambda k: MARKET_KEYS[k])
    st.divider()
    auto_refresh = st.toggle("Auto-refresh", value=False)
    refresh_mins = st.number_input("Interval mins", min_value=5, max_value=120, value=60, disabled=not auto_refresh)

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
    <div class="header-right">
        <div class="header-unit">
            <div class="header-unit-label">Unit Size</div>
            <div class="header-unit-value">{unit_size}</div>
        </div>
        <div class="header-unit">
            <div class="header-unit-label">Bankroll</div>
            <div class="header-unit-value">{total_bankroll:,}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.markdown('<div class="empty-state"><div class="empty-icon">🔑</div><div class="empty-title">Enter your Odds API key in the sidebar</div><div class="empty-sub">the-odds-api.com</div></div>', unsafe_allow_html=True)
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡  Live Scanner", "✍️  Log Past Bet", "📊  Analytics", "💰  Bankroll", "📋  History"])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — LIVE SCANNER
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    scan_clicked = st.button("⚡  SCAN MARKETS NOW", key="scan_btn")

    if "scan_results" not in st.session_state:
        st.session_state.scan_results = []
        st.session_state.num_events = 0
    if "logged_bets" not in st.session_state:
        st.session_state.logged_bets = set()

    if scan_clicked or auto_refresh:
        with st.spinner("Connecting to live odds feeds..."):
            all_events = fetch_all_sports(api_key)
        if not all_events:
            st.error("Could not fetch odds. Check your API key and credits.")
            st.stop()
        with st.spinner(f"Scanning {len(all_events)} events..."):
            all_opps = []
            now = datetime.now(timezone.utc)
            for event in all_events:
                try:
                    et = datetime.fromisoformat(event.get("commence_time","").replace("Z","+00:00"))
                    if et <= now:
                        continue
                except Exception:
                    pass
                for mk in selected_markets:
                    all_opps.extend(check_event_for_arb(event, mk))
        filtered = sorted([o for o in all_opps if o["profit_percent"] >= min_profit],
            key=lambda x: x["profit_percent"], reverse=True)
        st.session_state.scan_results = filtered
        st.session_state.num_events = len(all_events)
        st.session_state.logged_bets = set()

    filtered = st.session_state.scan_results
    num_events = st.session_state.num_events

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
        worksheet = get_cached_sheet(SHEET_ID) if creds_dict and SHEET_ID else None

        for i, opp in enumerate(filtered, 1):
            n = len(opp["outcomes"])
            cols_css = " ".join(["1fr"] * n)
            risk = get_opportunity_risk_score(opp["bookmakers"])
            kelly_stake = kelly_criterion(opp["profit_percent"], total_bankroll)

            bets_html = ""
            for j in range(n):
                r = get_rating(opp["bookmakers"][j])
                bets_html += f"""
                <div class="bet-card">
                    <div class="bet-outcome">{opp['outcomes'][j]}</div>
                    <div class="bet-line"><span class="bet-line-label">Odds</span><span class="bet-line-val val-odds">{opp['best_odds'][j]}</span></div>
                    <div class="bet-line"><span class="bet-line-label">Suggested units</span><span class="bet-line-val val-units">{opp['unit_stakes'][j]}</span></div>
                    <div class="book-badge">{r['icon']} {opp['bookmakers'][j]}</div>
                    <div style="font-size:9px;color:{r['color']};margin-top:4px;font-family:'JetBrains Mono',monospace;">{r['label']}</div>
                </div>"""

            already_logged = i in st.session_state.logged_bets

            st.markdown(f"""
            <div class="opp-card">
                <div class="opp-header">
                    <div>
                        <div class="opp-event">{opp["event"]}</div>
                        <div class="opp-meta">
                            <span>{opp["sport"]}</span>
                            <span>{MARKET_KEYS.get(opp["market"],opp["market"])}</span>
                            <span>{opp["commence_time"][:10]}</span>
                        </div>
                    </div>
                    <div class="profit-pill">+{opp["profit_percent"]}%</div>
                </div>
                <div class="stats-row">
                    <div class="stat-box"><div class="stat-box-label">{tooltip("arb_percent","Arb %")}</div><div class="stat-box-value">{opp["arb_percent"]}%</div></div>
                    <div class="stat-box"><div class="stat-box-label">{tooltip("kelly","Kelly Stake")}</div><div class="stat-box-value">{kelly_stake} units</div></div>
                    <div class="stat-box"><div class="stat-box-label">Guaranteed return</div><div class="stat-box-value">{round(opp["guaranteed_return_units"],4)} units</div></div>
                </div>
                <div class="risk-bar" style="background:rgba(0,0,0,0.2);border:1px solid {risk['color']}22;">
                    <span style="font-size:14px;">{risk['color'] == '#34d399' and '✅' or risk['color'] == '#fbbf24' and '⚠️' or '🚨'}</span>
                    <span style="color:{risk['color']};font-weight:600;">{risk['advice']}</span>
                </div>
                <div class="section-label" style="margin-bottom:10px;">Bets to place</div>
                <div style="display:grid;grid-template-columns:{cols_css};gap:10px;">{bets_html}</div>
                <div class="warn-line">Always verify odds on bookmaker site before placing · Odds change rapidly</div>
            </div>
            """, unsafe_allow_html=True)

            if already_logged:
                st.success(f"✅ Bet #{i} logged this session")
            elif worksheet:
                with st.container():
                    st.markdown(f'<div class="log-section"><div class="log-section-title">Log bet #{i} to tracker</div></div>', unsafe_allow_html=True)
                    total_input = st.slider(f"Total units to stake — Bet #{i}", min_value=1, max_value=min(total_bankroll, 10000), value=min(int(kelly_stake) or 10, total_bankroll), step=1, key=f"slider_{i}",
                        help="Drag to set your total stake. Pre-set to Kelly Criterion recommendation.")
                    arb_pct = opp["arb_percent"] / 100
                    actual_stakes = [round(total_input * (1.0/odds)/arb_pct, 4) for odds in opp["best_odds"]]
                    split_cols = st.columns(n)
                    for j in range(n):
                        with split_cols[j]:
                            st.markdown(f"""<div class="stat-box" style="margin-top:4px;">
                                <div class="stat-box-label">{opp['outcomes'][j]}</div>
                                <div class="stat-box-value" style="color:#818cf8;">{actual_stakes[j]} units</div>
                                <div class="stat-box-label" style="margin-top:3px;">{opp['bookmakers'][j]}</div>
                            </div>""", unsafe_allow_html=True)
                    est_profit_units = round(total_input*(1-arb_pct), 4)
                    est_profit_value = round(est_profit_units*unit_size, 2)
                    pct_of_bankroll = round(total_input/total_bankroll*100, 1)
                    st.markdown(f"""
                    <div class="log-summary">
                        <div><div class="log-sum-label">Total units</div><div class="log-sum-value">{round(sum(actual_stakes),4)}</div></div>
                        <div><div class="log-sum-label">Total value</div><div class="log-sum-value">{round(sum(actual_stakes)*unit_size,2)}</div></div>
                        <div><div class="log-sum-label">Est. profit</div><div class="log-sum-value green">{est_profit_units} ({est_profit_value})</div></div>
                        <div><div class="log-sum-label">% of bankroll</div><div class="log-sum-value">{pct_of_bankroll}%</div></div>
                    </div>""", unsafe_allow_html=True)
                    notes = st.text_input("Notes (optional)", key=f"notes_{i}", placeholder="e.g. odds moved slightly on placement...")
                    if st.button(f"✅  LOG BET #{i} TO TRACKER", key=f"log_{i}"):
                        opp_to_log = dict(opp)
                        opp_to_log["unit_stakes"] = actual_stakes
                        opp_to_log["total_staked_units"] = sum(actual_stakes)
                        if log_bet(worksheet, opp_to_log, unit_size, notes):
                            st.session_state.logged_bets.add(i)
                            st.cache_data.clear()
                            st.success(f"✅ Bet #{i} logged!")
                            st.rerun()
                        else:
                            st.error("Failed to log. Check Google Sheets connection.")
            else:
                st.info("Add Google Sheets credentials to Streamlit secrets to enable bet logging.")

    if auto_refresh:
        time.sleep(refresh_mins * 60)
        st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — LOG PAST BET
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-label">Log a past arbitrage bet</div>', unsafe_allow_html=True)
    if not creds_dict or not SHEET_ID:
        st.info("Add Google Sheets credentials to Streamlit secrets to enable bet logging.")
    else:
        worksheet = get_cached_sheet(SHEET_ID)
        if not worksheet:
            st.error("Could not connect to Google Sheets.")
        else:
            st.caption("Use this form to log any arbitrage bet placed manually or missed by the scanner.")
            with st.form("retro_bet_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    retro_date = st.date_input("Date bet was placed", value=date.today())
                    retro_event = st.text_input("Event *", placeholder="e.g. Arsenal vs Chelsea")
                    retro_sport = st.selectbox("Sport", options=["Soccer - EPL","Soccer - Champions League","Soccer - La Liga","Soccer - Bundesliga","Soccer - Serie A","Soccer - Ligue 1","Soccer - Championship","Soccer - Other","NBA","NCAA Basketball","EuroLeague Basketball","NBL","NFL","NCAA Football","UFL","MLB","NHL","AHL","Tennis","MMA","Cricket - IPL","Rugby League - NRL","Other"])
                with col2:
                    retro_market = st.selectbox("Market", options=["Match Winner (H2H / 1X2)","Over/Under (Totals)","Both Teams to Score","Asian Handicap","Other"])
                    retro_profit_pct = st.number_input("Profit % at time of placing", min_value=0.0, max_value=20.0, value=1.0, step=0.01, format="%.3f")
                    retro_notes = st.text_input("Notes", placeholder="e.g. placed manually, scanner offline...")
                st.divider()
                num_outcomes = st.radio("Number of outcomes", options=[2, 3], horizontal=True, help="2 for NBA/MLB/Tennis (no draw). 3 for soccer (win/draw/lose).")
                outcome_data = []
                out_cols = st.columns(num_outcomes)
                for j in range(num_outcomes):
                    with out_cols[j]:
                        st.markdown(f"**Outcome {j+1}**")
                        o_name = st.text_input("Outcome", key=f"r_name_{j}", placeholder="e.g. Arsenal" if j==0 else "Draw" if j==1 else "Chelsea")
                        o_odds = st.number_input("Odds", min_value=1.01, max_value=50.0, value=2.0, step=0.01, key=f"r_odds_{j}", format="%.2f")
                        o_book = st.text_input("Bookmaker", key=f"r_book_{j}", placeholder="e.g. Bet365")
                        o_units = st.number_input("Units staked", min_value=0.0, value=1.0, step=0.01, key=f"r_units_{j}", format="%.4f")
                        outcome_data.append({"name":o_name,"odds":o_odds,"book":o_book,"units":o_units})
                st.divider()
                st.caption("Settlement details — fill in once the bet resolves")
                set_col1, set_col2, set_col3 = st.columns(3)
                with set_col1:
                    retro_status = st.selectbox("Status", options=["Pending","Settled","Void"])
                with set_col2:
                    retro_actual_return = st.number_input("Actual return (units)", min_value=0.0, value=0.0, step=0.01, format="%.4f")
                with set_col3:
                    retro_actual_profit = st.number_input("Actual profit (units)", min_value=-10000.0, value=0.0, step=0.01, format="%.4f")
                submitted = st.form_submit_button("✅  LOG PAST BET", use_container_width=True)
                if submitted:
                    if not retro_event.strip():
                        st.error("Please enter the event name.")
                    elif any(not o["name"].strip() or not o["book"].strip() for o in outcome_data):
                        st.error("Please fill in all outcome names and bookmakers.")
                    else:
                        total_staked = sum(o["units"] for o in outcome_data)
                        retro_opp = {
                            "event": retro_event, "sport": retro_sport,
                            "commence_time": retro_date.strftime("%Y-%m-%dT00:00:00Z"),
                            "market": retro_market,
                            "outcomes": [o["name"] for o in outcome_data],
                            "best_odds": [o["odds"] for o in outcome_data],
                            "bookmakers": [o["book"] for o in outcome_data],
                            "unit_stakes": [o["units"] for o in outcome_data],
                            "total_staked_units": total_staked,
                            "guaranteed_return_units": total_staked*(1+retro_profit_pct/100),
                            "profit_units": total_staked*(retro_profit_pct/100),
                            "profit_percent": retro_profit_pct,
                            "arb_percent": round(100-retro_profit_pct, 3),
                        }
                        if log_bet(worksheet, retro_opp, unit_size, retro_notes):
                            if retro_status != "Pending" or retro_actual_profit != 0:
                                try:
                                    last_row = len(worksheet.get_all_values())
                                    worksheet.update(f"U{last_row}", [[retro_status]])
                                    worksheet.update(f"V{last_row}", [[round(retro_actual_return*unit_size,2)]])
                                    worksheet.update(f"W{last_row}", [[round(retro_actual_profit*unit_size,2)]])
                                except Exception:
                                    pass
                            st.cache_data.clear()
                            st.success(f"✅ Past bet logged — {retro_event}")
                        else:
                            st.error("Failed to log. Check Google Sheets connection.")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — ANALYTICS
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-label">Financial Analytics</div>', unsafe_allow_html=True)
    if not creds_dict or not SHEET_ID:
        st.info("Add Google Sheets credentials to unlock analytics.")
    else:
        bets = get_cached_bets(SHEET_ID)
        if not bets:
            st.markdown('<div class="empty-state"><div class="empty-icon">📊</div><div class="empty-title">No bets logged yet</div><div class="empty-sub">log your first bet from the scanner tab</div></div>', unsafe_allow_html=True)
        else:
            stats = get_summary_stats(bets, unit_size)
            irr_display = f"{stats['irr']}%" if stats['irr'] is not None else "Need 2+ settled"
            be = break_even_calculator(api_cost, stats.get("avg_profit_pct", 1.0) or 1.0, unit_size)
            be_display = str(be["bets_needed"]) if be else "—"

            st.markdown(f"""
            <div class="metric-grid-6">
                <div class="metric-card green"><div class="metric-label">{tooltip("roi","Total Profit")}</div><div class="metric-value green">{stats['total_profit']}</div><div class="metric-sub">{stats['settled_bets']} settled bets</div></div>
                <div class="metric-card green"><div class="metric-label">{tooltip("roi","ROI")}</div><div class="metric-value green">{stats['roi']}%</div><div class="metric-sub">return on investment</div></div>
                <div class="metric-card"><div class="metric-label">{tooltip("irr","IRR Annualised")}</div><div class="metric-value blue">{irr_display}</div><div class="metric-sub">equiv. annual return</div></div>
                <div class="metric-card"><div class="metric-label">Total Staked</div><div class="metric-value">{stats['total_staked']}</div><div class="metric-sub">capital deployed</div></div>
                <div class="metric-card amber"><div class="metric-label">{tooltip("pending_exposure","Pending Exposure")}</div><div class="metric-value amber">{stats['pending_exposure']}</div><div class="metric-sub">{stats['pending_bets']} open bets</div></div>
                <div class="metric-card"><div class="metric-label">{tooltip("break_even","Break-even bets/mo")}</div><div class="metric-value blue">{be_display}</div><div class="metric-sub">to cover API cost</div></div>
            </div>""", unsafe_allow_html=True)

            import plotly.graph_objects as go
            cb = "rgba(0,0,0,0)"
            fc = "#64748b"
            gc = "rgba(99,102,241,0.08)"

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f'<div class="section-label">{tooltip("roi","Cumulative P&L")}</div>', unsafe_allow_html=True)
                pnl = stats["cumulative_pnl"]
                if pnl:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=[d[0] for d in pnl], y=[d[1] for d in pnl], mode="lines+markers", line=dict(color="#6366f1",width=2), marker=dict(color="#818cf8",size=5), fill="tozeroy", fillcolor="rgba(99,102,241,0.06)"))
                    fig.update_layout(paper_bgcolor=cb, plot_bgcolor=cb, font=dict(color=fc,family="JetBrains Mono"), xaxis=dict(gridcolor=gc), yaxis=dict(gridcolor=gc), margin=dict(l=0,r=0,t=10,b=0), showlegend=False, height=260)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("No settled bets yet.")
            with c2:
                st.markdown(f'<div class="section-label">{tooltip("mom","Month-on-Month Return %")}</div>', unsafe_allow_html=True)
                mom = stats["mom_returns"]
                if mom:
                    months = list(mom.keys())
                    returns = [mom[m]["return_pct"] for m in months]
                    fig2 = go.Figure()
                    fig2.add_trace(go.Bar(x=months, y=returns, marker_color=["#34d399" if r>=0 else "#f87171" for r in returns]))
                    fig2.update_layout(paper_bgcolor=cb, plot_bgcolor=cb, font=dict(color=fc,family="JetBrains Mono"), xaxis=dict(gridcolor=gc), yaxis=dict(gridcolor=gc,ticksuffix="%"), margin=dict(l=0,r=0,t=10,b=0), showlegend=False, height=260)
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.caption("No settled bets yet.")

            c3, c4 = st.columns(2)
            with c3:
                st.markdown(f'<div class="section-label">{tooltip("bookmaker_risk","Bookmaker Leaderboard")}</div>', unsafe_allow_html=True)
                book_stats = stats["bookmaker_stats"]
                if book_stats:
                    colors = [get_rating(b)["color"] for b in book_stats.keys()]
                    fig3 = go.Figure()
                    fig3.add_trace(go.Bar(x=list(book_stats.values()), y=list(book_stats.keys()), orientation="h", marker_color=colors))
                    fig3.update_layout(paper_bgcolor=cb, plot_bgcolor=cb, font=dict(color=fc,family="JetBrains Mono"), xaxis=dict(gridcolor=gc), yaxis=dict(gridcolor=gc), margin=dict(l=0,r=0,t=10,b=0), showlegend=False, height=260)
                    st.plotly_chart(fig3, use_container_width=True)
                    st.caption("🟢 Arb-friendly  🟡 Moderate risk  🔴 Limit risk")
                else:
                    st.caption("No bookmaker data yet.")
            with c4:
                st.markdown('<div class="section-label">Sport Breakdown</div>', unsafe_allow_html=True)
                sport_stats = stats["sport_stats"]
                if sport_stats:
                    fig4 = go.Figure()
                    fig4.add_trace(go.Pie(labels=list(sport_stats.keys()), values=list(sport_stats.values()), hole=0.6, marker_colors=["#6366f1","#34d399","#818cf8","#fbbf24","#f87171","#06b6d4","#a78bfa"]))
                    fig4.update_layout(paper_bgcolor=cb, font=dict(color=fc,family="JetBrains Mono"), margin=dict(l=0,r=0,t=10,b=0), legend=dict(font=dict(color="#64748b",size=10)), height=260)
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.caption("No sport data yet.")

            if st.button("🔄 Refresh Analytics"):
                st.cache_data.clear()
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — BANKROLL MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-label">Bankroll Management</div>', unsafe_allow_html=True)

    bets = get_cached_bets(SHEET_ID) if creds_dict and SHEET_ID else []
    bk_stats = calculate_bankroll_stats(bets, total_bankroll)
    utilisation = bk_stats["utilisation_pct"]
    util_color = "#34d399" if utilisation < 30 else "#fbbf24" if utilisation < 70 else "#f87171"

    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card green">
            <div class="metric-label">{tooltip("pending_exposure","Available Capital")}</div>
            <div class="metric-value green">{bk_stats['available_capital']:,}</div>
            <div class="metric-sub">units free to deploy</div>
        </div>
        <div class="metric-card amber">
            <div class="metric-label">{tooltip("pending_exposure","Locked in Open Bets")}</div>
            <div class="metric-value amber">{bk_stats['pending_exposure']:,}</div>
            <div class="metric-sub">{bk_stats['open_bets']} pending bets</div>
        </div>
        <div class="metric-card green">
            <div class="metric-label">Realised Profit</div>
            <div class="metric-value green">{bk_stats['realised_profit']:,}</div>
            <div class="metric-sub">from settled bets</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Bankroll Utilisation</div>
            <div class="metric-value" style="color:{util_color};">{utilisation}%</div>
            <div class="metric-sub">of total bankroll deployed</div>
        </div>
    </div>
    <div class="bankroll-bar"><div class="bankroll-bar-fill" style="width:{min(utilisation,100)}%;"></div></div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f'<div class="section-label">{tooltip("kelly","Kelly Criterion Calculator")}</div>', unsafe_allow_html=True)

    kc1, kc2, kc3 = st.columns(3)
    with kc1:
        k_profit = st.number_input("Arb profit %", min_value=0.1, max_value=20.0, value=1.0, step=0.1, format="%.2f")
    with kc2:
        k_fraction = st.select_slider("Kelly fraction", options=[0.1, 0.25, 0.5, 1.0], value=0.25,
            help="Full Kelly (1.0) is aggressive. Quarter Kelly (0.25) is recommended for arb betting.")
    with kc3:
        k_stake = kelly_criterion(k_profit, total_bankroll, k_fraction)
        st.markdown(f"""
        <div class="metric-card green" style="margin-top:8px;">
            <div class="metric-label">Recommended Stake</div>
            <div class="metric-value green">{k_stake}</div>
            <div class="metric-sub">units ({round(k_stake*unit_size,2)} value)</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-label">Bankroll Growth Projection</div>', unsafe_allow_html=True)

    pr1, pr2, pr3 = st.columns(3)
    with pr1:
        proj_profit = st.number_input("Avg profit per arb %", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
    with pr2:
        proj_bets = st.number_input("Arbs placed per month", min_value=1, max_value=500, value=20, step=1)
    with pr3:
        proj_months = st.slider("Projection months", min_value=1, max_value=36, value=12)

    projection = project_growth(total_bankroll, proj_profit, proj_bets, proj_months)
    final = projection[-1][1]
    growth_pct = round((final - total_bankroll) / total_bankroll * 100, 1)

    import plotly.graph_objects as go
    cb = "rgba(0,0,0,0)"
    fc = "#64748b"
    gc = "rgba(99,102,241,0.08)"

    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(
        x=[p[0] for p in projection],
        y=[p[1] for p in projection],
        mode="lines+markers",
        line=dict(color="#34d399", width=2),
        marker=dict(color="#34d399", size=5),
        fill="tozeroy",
        fillcolor="rgba(52,211,153,0.06)",
        name="Projected Bankroll"
    ))
    fig_proj.add_hline(y=total_bankroll, line_dash="dash", line_color="rgba(99,102,241,0.4)", annotation_text="Starting bankroll")
    fig_proj.update_layout(
        paper_bgcolor=cb, plot_bgcolor=cb,
        font=dict(color=fc, family="JetBrains Mono"),
        xaxis=dict(gridcolor=gc, title="Month"),
        yaxis=dict(gridcolor=gc, title="Units"),
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False, height=300
    )
    st.plotly_chart(fig_proj, use_container_width=True)
    st.markdown(f"""
    <div class="metric-grid-3">
        <div class="metric-card green"><div class="metric-label">Projected Bankroll</div><div class="metric-value green">{final:,.0f}</div><div class="metric-sub">after {proj_months} months</div></div>
        <div class="metric-card green"><div class="metric-label">Projected Growth</div><div class="metric-value green">+{growth_pct}%</div><div class="metric-sub">total return</div></div>
        <div class="metric-card"><div class="metric-label">{tooltip("break_even","Break-even Bets/mo")}</div><div class="metric-value blue">{break_even_calculator(api_cost, proj_profit, unit_size)['bets_needed'] if break_even_calculator(api_cost, proj_profit, unit_size) else '—'}</div><div class="metric-sub">to cover API cost of {api_cost}/mo</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("⚠️ Projection assumes consistent opportunity volume and successful execution. Actual results will vary.")

    st.divider()
    st.markdown(f'<div class="section-label">{tooltip("bookmaker_risk","Bookmaker Risk Guide")}</div>', unsafe_allow_html=True)
    from bookmaker_ratings import BOOKMAKER_RATINGS
    for name, r in BOOKMAKER_RATINGS.items():
        stars = "★" * r["rating"] + "☆" * (5 - r["rating"])
        st.markdown(f"""
        <div style="display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-bottom:1px solid rgba(99,102,241,0.08);">
            <span style="font-size:18px;width:24px;">{r['icon']}</span>
            <div style="flex:1;">
                <div style="font-size:13px;font-weight:600;color:#cbd5e1;">{name} <span style="color:{r['color']};font-size:11px;font-family:'JetBrains Mono',monospace;">· {r['label']}</span></div>
                <div style="font-size:11px;color:#475569;margin-top:2px;">{r['note']}</div>
            </div>
            <div style="color:{r['color']};font-size:12px;font-family:'JetBrains Mono',monospace;white-space:nowrap;">{stars}</div>
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 5 — BET HISTORY
# ════════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-label">Bet History</div>', unsafe_allow_html=True)
    if not creds_dict or not SHEET_ID:
        st.info("Add Google Sheets credentials to see bet history.")
    else:
        bets = get_cached_bets(SHEET_ID)
        if not bets:
            st.markdown('<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-title">No bets logged yet</div></div>', unsafe_allow_html=True)
        else:
            import pandas as pd
            df = pd.DataFrame(bets)
            display_cols = ["Date","Event","Sport","Market","Total Staked","Guaranteed Return","Profit","Profit %","Status","Actual Profit","Notes"]
            display_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 Refresh History"):
                    st.cache_data.clear()
                    st.rerun()
            with col_b:
                st.link_button("📊 Open Google Sheet", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}")
