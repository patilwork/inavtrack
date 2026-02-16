"""
Commodity ETF iNAV vs Price Scanner
====================================
Professional scanner with real-time tracking, historical data, and alerts.

Usage:
    pip install -r requirements.txt
    streamlit run app.py
"""

import re
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ---------- Configuration ----------
CSV_PATH = "funds.csv"
REFRESH_INTERVAL_MS = 30000  # 30 seconds
IST = ZoneInfo("Asia/Kolkata")

# ---------- Custom CSS ----------
CUSTOM_CSS = """
<style>
    /* Dark theme base */
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .main-header p {
        color: rgba(255,255,255,0.95);
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    
    /* Timestamp banner */
    .timestamp-banner {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border: 1px solid #3d7ab5;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
    }
    .timestamp-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .timestamp-item {
        text-align: center;
    }
    .timestamp-item .label {
        color: rgba(255,255,255,0.85);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.25rem;
    }
    .timestamp-item .value {
        color: #93c5fd;
        font-size: 1.1rem;
        font-weight: 600;
        font-family: 'SF Mono', 'Monaco', monospace;
    }
    .timestamp-item .value.countdown {
        color: #fcd34d;
        font-size: 1.3rem;
    }
    .timestamp-item .value.large {
        font-size: 1.4rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    .metric-card .value {
        font-size: 2rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .metric-card .label {
        font-size: 0.85rem;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.25rem;
    }
    .metric-card.premium .value { color: #fca5a5; }
    .metric-card.discount .value { color: #86efac; }
    .metric-card.highlight .value { color: #fcd34d; }
    
    /* Alert cards */
    .alert-section {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #334155;
    }
    .alert-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #475569;
    }
    .alert-header h3 {
        margin: 0;
        color: #f1f5f9;
        font-size: 1.1rem;
    }
    
    .alert-item {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 3px solid;
    }
    .alert-item.premium {
        border-color: #ef4444;
        background: rgba(239, 68, 68, 0.15);
    }
    .alert-item.discount {
        border-color: #22c55e;
        background: rgba(34, 197, 94, 0.15);
    }
    .alert-item.consistent {
        border-width: 4px;
        box-shadow: 0 0 20px rgba(251, 191, 36, 0.4);
    }
    .alert-item .fund-name {
        color: #f1f5f9;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .alert-item .symbol {
        color: #cbd5e1;
        font-size: 0.85rem;
        margin-top: 2px;
    }
    .alert-item .streak-badge {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #000;
        padding: 0.2rem 0.5rem;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: 700;
        margin-left: 0.5rem;
    }
    .alert-item .badge {
        padding: 0.4rem 0.85rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.95rem;
    }
    .alert-item.premium .badge {
        background: rgba(239, 68, 68, 0.25);
        color: #fecaca;
    }
    .alert-item.discount .badge {
        background: rgba(34, 197, 94, 0.25);
        color: #bbf7d0;
    }
    
    /* Consistent alert banner */
    .consistent-alert-banner {
        background: linear-gradient(135deg, #92400e 0%, #78350f 100%);
        border: 2px solid #fbbf24;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .consistent-alert-banner .icon {
        font-size: 2rem;
    }
    .consistent-alert-banner .content h4 {
        margin: 0;
        color: #fef3c7;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .consistent-alert-banner .content p {
        margin: 0.25rem 0 0 0;
        color: #fde68a;
        font-size: 0.9rem;
    }
    
    /* Progress tracker */
    .scan-progress {
        background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%);
        border: 1px solid #3b82f6;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
    }
    .scan-progress .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }
    .scan-progress .title {
        color: #f1f5f9;
        font-weight: 600;
        font-size: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .scan-progress .counter {
        color: #93c5fd;
        font-family: 'SF Mono', monospace;
        font-size: 1rem;
        font-weight: 600;
    }
    .scan-progress .current-etf {
        color: #e0f2fe;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .scan-progress .progress-bar {
        height: 8px;
        background: rgba(255,255,255,0.1);
        border-radius: 4px;
        overflow: hidden;
    }
    .scan-progress .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    
    /* Status indicator */
    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    .status-dot.live { background: #22c55e; }
    .status-dot.idle { background: #94a3b8; }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Section headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #fbbf24;
    }
    .section-header h2 {
        margin: 0;
        color: #f1f5f9;
        font-size: 1.25rem;
    }
    
    /* No data message */
    .no-data {
        color: #cbd5e1;
        padding: 1rem;
        font-size: 0.95rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Better buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 10px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Progress bar for countdown */
    .countdown-bar {
        height: 4px;
        background: #475569;
        border-radius: 2px;
        margin-top: 0.5rem;
        overflow: hidden;
    }
    .countdown-bar .fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 2px;
        transition: width 1s linear;
    }
    
    /* Sidebar text improvements */
    .stSidebar .stMarkdown p, .stSidebar .stMarkdown div {
        color: #e2e8f0 !important;
    }
    .stSidebar h3 {
        color: #f1f5f9 !important;
    }
</style>
"""

# ---------- NSE Session Helpers ----------
def make_nse_session() -> requests.Session:
    """Create a requests session with browser-like headers."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive",
    })
    try:
        s.get("https://www.nseindia.com/", timeout=15)
    except Exception:
        pass
    return s


def safe_json(session: requests.Session, url: str, tries: int = 2) -> dict:
    """Fetch JSON with retries."""
    last_err = None
    for attempt in range(tries):
        try:
            r = session.get(url, timeout=12)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            time.sleep(0.5 * (attempt + 1))
            try:
                session.get("https://www.nseindia.com/", timeout=10)
            except Exception:
                pass
    raise RuntimeError(f"Failed: {url} | {last_err}")


def extract_symbol_from_url(url: str) -> str:
    """Extract NSE symbol from get-quote URL."""
    m = re.search(r"/get-quote/equity/([^/]+)", url, re.IGNORECASE)
    if not m:
        raise ValueError(f"Could not extract symbol: {url}")
    return m.group(1).strip().upper()


def fetch_ltp_inav(session: requests.Session, symbol: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """Fetch LTP and iNAV from NSE APIs."""
    ltp = None
    inav = None
    errors = []
    
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        data = safe_json(session, url)
        if isinstance(data, dict):
            price_info = data.get("priceInfo", {})
            if isinstance(price_info, dict):
                ltp_raw = price_info.get("lastPrice")
                if ltp_raw is not None:
                    ltp = float(str(ltp_raw).replace(",", ""))
    except Exception as e:
        errors.append(f"LTP: {e}")
    
    try:
        next_api_url = f"https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi?functionName=getSymbolData&marketType=N&series=EQ&symbol={symbol}"
        next_data = safe_json(session, next_api_url)
        if isinstance(next_data, dict):
            equity_response = next_data.get("equityResponse", [])
            if equity_response and len(equity_response) > 0:
                first_response = equity_response[0]
                if isinstance(first_response, dict):
                    price_info = first_response.get("priceInfo", {})
                    if isinstance(price_info, dict):
                        inav_raw = price_info.get("inav")
                        if inav_raw is not None:
                            inav = float(str(inav_raw).replace(",", ""))
    except Exception as e:
        errors.append(f"iNAV: {e}")
    
    return ltp, inav, "; ".join(errors) if errors else None


def calculate_premium_discount(ltp: Optional[float], inav: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    """Calculate premium/discount percentage and absolute value."""
    if ltp is None or inav is None or inav == 0:
        return None, None
    premium_abs = ltp - inav
    premium_pct = (premium_abs / inav) * 100.0
    return premium_pct, premium_abs


def load_funds_csv(csv_path) -> pd.DataFrame:
    """Load the funds CSV file."""
    df = pd.read_csv(csv_path, header=None)
    if df.iloc[0].isna().all() or str(df.iloc[0, 0]).strip() == "":
        df = df.iloc[1:].reset_index(drop=True)
    df.columns = ["ISIN", "Fund_Name", "NSE_URL"][:len(df.columns)]
    df = df.dropna(subset=["ISIN", "NSE_URL"])
    df["ISIN"] = df["ISIN"].astype(str).str.strip()
    df["Fund_Name"] = df["Fund_Name"].astype(str).str.strip()
    df["NSE_URL"] = df["NSE_URL"].astype(str).str.strip()
    return df


def get_consistent_alerts(scan_history: list, premium_threshold: float, discount_threshold: float, min_streak: int = 3) -> dict:
    """
    Find ETFs with consistent premium/discount above threshold for min_streak cycles.
    Returns dict with symbol -> {"type": "premium"|"discount", "streak": int, "values": [...]}
    """
    if len(scan_history) < min_streak:
        return {}
    
    recent_scans = scan_history[-min_streak:]
    consistent = {}
    latest_results = recent_scans[-1]["results"]
    symbols = latest_results["Symbol"].dropna().unique()
    
    for symbol in symbols:
        premium_streak = 0
        discount_streak = 0
        premium_values = []
        discount_values = []
        
        for scan in recent_scans:
            scan_df = scan["results"]
            row = scan_df[scan_df["Symbol"] == symbol]
            if len(row) == 0:
                break
            
            prem_pct = row.iloc[0]["Premium_Pct"]
            if pd.isna(prem_pct):
                break
            
            if prem_pct >= premium_threshold:
                premium_streak += 1
                premium_values.append(prem_pct)
            elif prem_pct <= discount_threshold:
                discount_streak += 1
                discount_values.append(prem_pct)
        
        if premium_streak >= min_streak:
            consistent[symbol] = {
                "type": "premium",
                "streak": premium_streak,
                "values": premium_values,
                "avg": sum(premium_values) / len(premium_values)
            }
        elif discount_streak >= min_streak:
            consistent[symbol] = {
                "type": "discount",
                "streak": discount_streak,
                "values": discount_values,
                "avg": sum(discount_values) / len(discount_values)
            }
    
    return consistent


# ---------- Streamlit App ----------
st.set_page_config(
    page_title="ETF iNAV Scanner",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize session state
if "scan_history" not in st.session_state:
    st.session_state.scan_history = []
if "last_scan_time" not in st.session_state:
    st.session_state.last_scan_time = None
if "last_fetch_time" not in st.session_state:
    st.session_state.last_fetch_time = None
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

# Header
st.markdown("""
<div class="main-header">
    <h1>🥇 Commodity ETF: iNAV Scanner</h1>
    <p>Real-time premium/discount tracking for Gold & Silver ETFs on NSE</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    csv_file = st.file_uploader("Upload Funds CSV", type=["csv"], help="ISIN, Fund Name, NSE URL")
    
    st.markdown("---")
    st.markdown("### 🎯 Alert Thresholds")
    
    premium_threshold = st.slider("Premium Alert ≥", min_value=0.0, max_value=5.0, value=1.0, step=0.1, format="%.1f%%")
    discount_threshold = st.slider("Discount Alert ≤", min_value=-5.0, max_value=0.0, value=-1.0, step=0.1, format="%.1f%%")
    
    st.markdown("---")
    st.markdown("### ⏱️ Scan Settings")
    
    request_delay = st.slider("Request delay (ms)", min_value=50, max_value=300, value=100, step=25)
    streak_threshold = st.slider("Consistent alert streak", min_value=2, max_value=10, value=3, step=1, help="Highlight ETFs above threshold for this many consecutive scans")
    
    st.markdown("---")
    st.markdown("### 📊 Rate Limit Info")
    st.markdown("""
    <div style="font-size: 0.9rem; color: #e2e8f0;">
    <b>NSE Fair Usage:</b><br>
    • ~2 req/sec is safe<br>
    • 32 ETFs × 2 APIs = 64 calls<br>
    • At 100ms delay: ~25 sec/scan<br>
    • <b>30-sec refresh:</b> Safe ✅<br>
    </div>
    """, unsafe_allow_html=True)

# Load funds
if csv_file is not None:
    funds_df = load_funds_csv(csv_file)
else:
    try:
        funds_df = load_funds_csv(CSV_PATH)
    except FileNotFoundError:
        funds_df = None
        st.error("Please upload a CSV file with fund data.")

if funds_df is not None:
    col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
    
    with col1:
        scan_now = st.button("🔍 Scan Now", type="primary", use_container_width=True)
    
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh
    
    with col3:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.scan_history = []
            st.session_state.last_scan_time = None
            st.session_state.last_fetch_time = None
            st.session_state.last_results = None
            st.rerun()
    
    with col4:
        if st.session_state.last_scan_time:
            status = "live" if auto_refresh else "idle"
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: flex-end; height: 100%; padding-top: 0.5rem;">
                <span class="status-dot {status}"></span>
                <span style="color: #e2e8f0;">Tracking {len(funds_df)} ETFs</span>
            </div>
            """, unsafe_allow_html=True)
    
    if auto_refresh:
        refresh_count = st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="auto_refresh_counter")
        if refresh_count > 0 or st.session_state.last_results is None:
            scan_now = True
    
    if scan_now:
        # Create progress container
        progress_container = st.empty()
        
        # Show scanning progress
        progress_container.markdown(f"""
        <div class="scan-progress">
            <div class="header">
                <div class="title">🔄 Initializing scan...</div>
                <div class="counter">0 / {len(funds_df)}</div>
            </div>
            <div class="current-etf">Warming up NSE session...</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Run scan with progress updates
        start_time = time.time()
        session = make_nse_session()
        results = []
        api_calls = 0
        
        for idx, row in enumerate(funds_df.iterrows()):
            _, row_data = row
            fund_name = row_data["Fund_Name"][:35]
            progress_pct = ((idx + 1) / len(funds_df)) * 100
            
            # Update progress display
            progress_container.markdown(f"""
            <div class="scan-progress">
                <div class="header">
                    <div class="title">🔄 Scanning ETFs...</div>
                    <div class="counter">{idx + 1} / {len(funds_df)}</div>
                </div>
                <div class="current-etf">📍 {fund_name}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {progress_pct}%"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            result = {
                "ISIN": row_data["ISIN"],
                "Fund_Name": row_data["Fund_Name"],
                "Symbol": None,
                "LTP": None,
                "iNAV": None,
                "Premium_Pct": None,
                "Premium_Rs": None,
                "Error": None,
            }
            try:
                symbol = extract_symbol_from_url(row_data["NSE_URL"])
                result["Symbol"] = symbol
                ltp, inav, error = fetch_ltp_inav(session, symbol)
                api_calls += 2
                result["LTP"] = ltp
                result["iNAV"] = inav
                if error:
                    result["Error"] = error
                prem_pct, prem_abs = calculate_premium_discount(ltp, inav)
                result["Premium_Pct"] = prem_pct
                result["Premium_Rs"] = prem_abs
            except Exception as e:
                result["Error"] = str(e)
            results.append(result)
            time.sleep(request_delay / 1000.0)
        
        # Build results dataframe
        results_df = pd.DataFrame(results)
        for col in ["Premium_Pct", "Premium_Rs", "LTP", "iNAV"]:
            results_df[col] = pd.to_numeric(results_df[col], errors='coerce')
        
        elapsed = time.time() - start_time
        fetch_time = datetime.now(IST)
        scan_time = datetime.now(IST)
        
        # Clear progress and show completion
        progress_container.markdown(f"""
        <div class="scan-progress" style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-color: #10b981;">
            <div class="header">
                <div class="title">✅ Scan Complete!</div>
                <div class="counter">{len(funds_df)} / {len(funds_df)}</div>
            </div>
            <div class="current-etf">Completed in {elapsed:.1f}s • {api_calls} API calls • {len(results_df[results_df['iNAV'].notna()])} with iNAV</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 100%; background: linear-gradient(90deg, #10b981, #34d399);"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        progress_container.empty()
        
        # Store results
        st.session_state.last_scan_time = scan_time
        st.session_state.last_fetch_time = fetch_time
        st.session_state.last_results = results_df
        
        st.session_state.scan_history.append({
            "time": scan_time,
            "fetch_time": fetch_time,
            "results": results_df.copy(),
            "elapsed": elapsed,
            "api_calls": api_calls
        })
        if len(st.session_state.scan_history) > 100:
            st.session_state.scan_history = st.session_state.scan_history[-100:]
    
    if st.session_state.last_results is not None:
        results_df = st.session_state.last_results
        scan_time = st.session_state.last_scan_time
        fetch_time = st.session_state.last_fetch_time
        
        # Calculate countdown
        if auto_refresh and scan_time:
            next_refresh = scan_time + timedelta(milliseconds=REFRESH_INTERVAL_MS)
            time_remaining = (next_refresh - datetime.now(IST)).total_seconds()
            time_remaining = max(0, time_remaining)
            countdown_pct = (time_remaining / (REFRESH_INTERVAL_MS / 1000)) * 100
        else:
            time_remaining = 0
            countdown_pct = 0
        
        # Timestamp banner
        st.markdown(f"""
        <div class="timestamp-banner">
            <div class="timestamp-row">
                <div class="timestamp-item">
                    <div class="label">Last Scan</div>
                    <div class="value large">{scan_time.strftime("%d %b %Y, %H:%M:%S")} IST</div>
                </div>
                <div class="timestamp-item">
                    <div class="label">Data Fetched At</div>
                    <div class="value">{fetch_time.strftime("%H:%M:%S")}</div>
                </div>
                <div class="timestamp-item">
                    <div class="label">Scan #</div>
                    <div class="value">{len(st.session_state.scan_history)}</div>
                </div>
                <div class="timestamp-item">
                    <div class="label">Next Refresh</div>
                    <div class="value countdown">{int(time_remaining)}s</div>
                    {f'<div class="countdown-bar"><div class="fill" style="width: {countdown_pct}%"></div></div>' if auto_refresh else '<div style="color: #94a3b8; font-size: 0.85rem;">Auto-refresh OFF</div>'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Consistent alerts
        consistent_alerts = get_consistent_alerts(st.session_state.scan_history, premium_threshold, discount_threshold, streak_threshold)
        
        if consistent_alerts:
            premium_consistent = [s for s, d in consistent_alerts.items() if d["type"] == "premium"]
            discount_consistent = [s for s, d in consistent_alerts.items() if d["type"] == "discount"]
            
            st.markdown(f"""
            <div class="consistent-alert-banner">
                <div class="icon">⚠️</div>
                <div class="content">
                    <h4>Consistent Deviation Alert!</h4>
                    <p>{len(premium_consistent)} ETF(s) at premium and {len(discount_consistent)} ETF(s) at discount for {streak_threshold}+ consecutive scans</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Metrics
        valid = results_df[results_df["Premium_Pct"].notna()]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f'<div class="metric-card"><div class="value">{len(results_df)}</div><div class="label">Total ETFs</div></div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="metric-card highlight"><div class="value">{len(valid)}</div><div class="label">With iNAV</div></div>', unsafe_allow_html=True)
        
        if len(valid) > 0:
            max_prem = valid["Premium_Pct"].max()
            min_disc = valid["Premium_Pct"].min()
            avg_dev = valid["Premium_Pct"].abs().mean()
            
            with col3:
                st.markdown(f'<div class="metric-card premium"><div class="value">{max_prem:+.2f}%</div><div class="label">Max Premium</div></div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown(f'<div class="metric-card discount"><div class="value">{min_disc:+.2f}%</div><div class="label">Max Discount</div></div>', unsafe_allow_html=True)
            
            with col5:
                st.markdown(f'<div class="metric-card"><div class="value">{avg_dev:.2f}%</div><div class="label">Avg |Deviation|</div></div>', unsafe_allow_html=True)
        
        # Alerts
        st.markdown('<div class="section-header"><span>🚨</span><h2>Alerts</h2></div>', unsafe_allow_html=True)
        
        premiums = valid[valid["Premium_Pct"] >= premium_threshold].sort_values("Premium_Pct", ascending=False)
        discounts = valid[valid["Premium_Pct"] <= discount_threshold].sort_values("Premium_Pct")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f'<div class="alert-section"><div class="alert-header"><span style="font-size: 1.2rem;">📈</span><h3>Premium Alerts ({len(premiums)})</h3></div>', unsafe_allow_html=True)
            
            if len(premiums) > 0:
                for _, row in premiums.head(10).iterrows():
                    symbol = row['Symbol']
                    is_consistent = symbol in consistent_alerts and consistent_alerts[symbol]["type"] == "premium"
                    streak_badge = f'<span class="streak-badge">🔥 {consistent_alerts[symbol]["streak"]} scans</span>' if is_consistent else ""
                    consistent_class = "consistent" if is_consistent else ""
                    
                    st.markdown(f"""
                    <div class="alert-item premium {consistent_class}">
                        <div>
                            <div class="fund-name">{row['Fund_Name'][:30]}{streak_badge}</div>
                            <div class="symbol">{symbol} • LTP: ₹{row['LTP']:.2f} • iNAV: ₹{row['iNAV']:.2f}</div>
                        </div>
                        <div class="badge">+{row['Premium_Pct']:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<p class="no-data">No premiums above threshold</p>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="alert-section"><div class="alert-header"><span style="font-size: 1.2rem;">📉</span><h3>Discount Alerts ({len(discounts)})</h3></div>', unsafe_allow_html=True)
            
            if len(discounts) > 0:
                for _, row in discounts.head(10).iterrows():
                    symbol = row['Symbol']
                    is_consistent = symbol in consistent_alerts and consistent_alerts[symbol]["type"] == "discount"
                    streak_badge = f'<span class="streak-badge">🔥 {consistent_alerts[symbol]["streak"]} scans</span>' if is_consistent else ""
                    consistent_class = "consistent" if is_consistent else ""
                    
                    st.markdown(f"""
                    <div class="alert-item discount {consistent_class}">
                        <div>
                            <div class="fund-name">{row['Fund_Name'][:30]}{streak_badge}</div>
                            <div class="symbol">{symbol} • LTP: ₹{row['LTP']:.2f} • iNAV: ₹{row['iNAV']:.2f}</div>
                        </div>
                        <div class="badge">{row['Premium_Pct']:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<p class="no-data">No discounts below threshold</p>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Results table
        st.markdown('<div class="section-header"><span>📊</span><h2>All Results</h2></div>', unsafe_allow_html=True)
        
        display_df = results_df.copy()
        display_df["Streak"] = display_df["Symbol"].apply(lambda s: f"🔥 {consistent_alerts[s]['streak']}" if s in consistent_alerts else "")
        display_df = display_df.sort_values("Premium_Pct", key=abs, ascending=False, na_position="last")
        
        def color_premium(val):
            if pd.isna(val):
                return ""
            if val >= premium_threshold:
                return "background-color: rgba(239, 68, 68, 0.3); color: #fca5a5; font-weight: bold"
            elif val <= discount_threshold:
                return "background-color: rgba(34, 197, 94, 0.3); color: #86efac; font-weight: bold"
            return ""
        
        styled = display_df[["Symbol", "Fund_Name", "LTP", "iNAV", "Premium_Pct", "Premium_Rs", "Streak"]].style.map(
            color_premium, subset=["Premium_Pct"]
        ).format({"LTP": "₹{:.2f}", "iNAV": "₹{:.2f}", "Premium_Pct": "{:+.2f}%", "Premium_Rs": "₹{:+.2f}"}, na_rep="-")
        
        st.dataframe(styled, use_container_width=True, hide_index=True, height=400)
        
        # Historical tracking
        if len(st.session_state.scan_history) > 1:
            st.markdown('<div class="section-header"><span>📈</span><h2>Historical Tracking</h2></div>', unsafe_allow_html=True)
            
            symbols = sorted(results_df["Symbol"].dropna().unique())
            selected_symbol = st.selectbox("Select ETF to track", symbols, index=0)
            
            if selected_symbol:
                history_data = []
                for scan in st.session_state.scan_history:
                    scan_results = scan["results"]
                    row = scan_results[scan_results["Symbol"] == selected_symbol]
                    if len(row) > 0:
                        row = row.iloc[0]
                        history_data.append({"Time": scan["time"], "LTP": row["LTP"], "iNAV": row["iNAV"], "Premium_Pct": row["Premium_Pct"]})
                
                if history_data:
                    hist_df = pd.DataFrame(history_data)
                    
                    if selected_symbol in consistent_alerts:
                        alert_info = consistent_alerts[selected_symbol]
                        st.warning(f"⚠️ **{selected_symbol}** has been at {'premium' if alert_info['type'] == 'premium' else 'discount'} for **{alert_info['streak']} consecutive scans** (avg: {alert_info['avg']:+.2f}%)")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**LTP vs iNAV**")
                        st.line_chart(hist_df[["Time", "LTP", "iNAV"]].set_index("Time"), height=250)
                    
                    with col2:
                        st.markdown("**Premium/Discount %**")
                        st.line_chart(hist_df[["Time", "Premium_Pct"]].set_index("Time"), height=250)
                    
                    st.markdown("**Recent History**")
                    hist_display = hist_df.tail(15).sort_values("Time", ascending=False).copy()
                    hist_display["Time"] = hist_display["Time"].dt.strftime("%H:%M:%S")
                    hist_display["Premium_Pct"] = hist_display["Premium_Pct"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "-")
                    st.dataframe(hist_display, use_container_width=True, hide_index=True)
        
        # Export
        st.markdown('<div class="section-header"><span>💾</span><h2>Export</h2></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button("⬇️ Download Current Scan (CSV)", data=results_df.to_csv(index=False), file_name=f"etf_scan_{scan_time.strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", use_container_width=True)
        
        with col2:
            if st.session_state.scan_history:
                all_history = []
                for scan in st.session_state.scan_history:
                    scan_df = scan["results"].copy()
                    scan_df["Scan_Time"] = scan["time"]
                    scan_df["Fetch_Time"] = scan.get("fetch_time", scan["time"])
                    all_history.append(scan_df)
                
                full_history = pd.concat(all_history, ignore_index=True)
                st.download_button(f"⬇️ Download History ({len(st.session_state.scan_history)} scans)", data=full_history.to_csv(index=False), file_name=f"etf_history_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #cbd5e1; font-size: 0.9rem;">
    <p><b>iNAV</b> = Indicative Net Asset Value | <b>Premium</b> = LTP > iNAV | <b>Discount</b> = LTP < iNAV</p>
    <p>🔥 = Consistent deviation above threshold for multiple scans</p>
</div>
""", unsafe_allow_html=True)
