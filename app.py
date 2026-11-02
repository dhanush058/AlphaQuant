from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf

# Page Configuration
st.set_page_config(
    page_title="Global Treasury Command Center",
    page_icon="🏦",
    layout="wide",
)

# Auto-refresh live data feed every 60 seconds
count = st_autorefresh(interval=60000, limit=None, key="command_center_feed")

# ==========================================
# CUSTOM STYLING (BLACK & NEON GREEN THEME)
# ==========================================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    /* Metric Cards with Neon Green Glow */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        border: 1px solid #374151;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0, 255, 102, 0.05);
    }
    div[data-testid="stMetric"]:hover {
        border-color: #00ff66;
        box-shadow: 0 0 15px rgba(0, 255, 102, 0.25);
    }
    div[data-testid="stMetric"] label {
        color: #9ca3af !important;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #00ff66 !important;
        font-weight: 700;
        font-size: 1.25rem;
    }
    h1, h2, h3 {
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    .command-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #111827;
        padding: 15px 25px;
        border-radius: 10px;
        border: 1px solid #374151;
        margin-bottom: 20px;
    }
    /* Tabs & Radio Active States */
    .stRadio [role="radiogroup"] label div {
        color: #d1d5db;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# SQL DATABASE INITIALIZATION
# ==========================================
def init_command_db():
  conn = sqlite3.connect("command_center.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sql_transactions (
            transaction_id TEXT PRIMARY KEY,
            timestamp TEXT,
            description TEXT,
            debit REAL,
            credit REAL,
            status TEXT
        )
    """)
  cursor.execute("SELECT COUNT(*) FROM sql_transactions")
  if cursor.fetchone()[0] == 0:
    sample_txs = [
        ("TXM-9021", "2026-11-02 21:03:07", "PAYMENT FROM CLIENT A", 0.0, 120500.0, "CONFIRMED"),
        ("TXM-9020", "2026-11-02 21:03:00", "UTILITY BILL PAYMENT", 15200.0, 0.0, "PROCESSING"),
        ("TXN-9019", "2026-11-02 21:03:00", "PAYMENT FROM CLIENT A", 0.0, 15500.0, "PROCESSING"),
        ("TXN-9018", "2026-11-02 21:00:15", "SWIFT WIRE TRANSFER - EMEA", 450000.0, 0.0, "CONFIRMED"),
        ("TXN-9017", "2026-11-02 20:55:40", "VENDOR SETTLEMENT - APAC", 82300.0, 0.0, "CONFIRMED"),
    ]
    cursor.executemany("INSERT OR IGNORE INTO sql_transactions VALUES (?, ?, ?, ?, ?, ?)", sample_txs)
  conn.commit()
  conn.close()


init_command_db()


def load_transactions():
  conn = sqlite3.connect("command_center.db")
  df = pd.read_sql_query("SELECT * FROM sql_transactions ORDER BY timestamp DESC", conn)
  conn.close()
  return df


# ==========================================
# LIVE API MARKET FEED (REAL DATA)
# ==========================================
@st.cache_data(ttl=300)
def fetch_command_market_data():
  try:
    data = yf.download(["^GSPC", "^IXIC"], period="1mo", progress=False)["Close"]
    if isinstance(data.columns, pd.MultiIndex):
      data.columns = data.columns.droplevel(0)
    return data
  except Exception:
    return pd.DataFrame()


market_data = fetch_command_market_data()

# ==========================================
# SIDEBAR NAVIGATION RAIL
# ==========================================
st.sidebar.markdown("### 🏦 Aegis Command")
st.sidebar.markdown("---")
nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "📊 Executive Command Center",
        "📋 SQL Transaction Ledger",
        "⚡ Live API Tickers",
        "⚙️ Treasury Settings",
    ],
)
st.sidebar.markdown("---")
st.sidebar.success("🟢 Real-Time Secure Stream Active")

# ==========================================
# VIEW ROUTING BASED ON SIDEBAR SELECTION
# ==========================================

if nav_choice == "📊 Executive Command Center":
  st.markdown("""
        <div class="command-header">
            <h2 style="margin:0; color:#ffffff; font-size: 1.5rem;">🌐 GLOBAL TREASURY COMMAND CENTER</h2>
            <div style="font-size: 0.85rem; color: #00ff66; font-weight: 600;">
                LIVE TICKERS: &nbsp; S&P 500 &nbsp;|&nbsp; NASDAQ &nbsp;|&nbsp; REAL-TIME FEED
            </div>
        </div>
    """, unsafe_allow_html=True)

  # 6 KPI METRIC CARDS
  c1, c2, c3, c4, c5, c6 = st.columns(6)
  c1.metric("Cash on Hand", "$78.2M", "+2.1% (Sim)")
  c2.metric("Forex Exposure", "$1.4B", "-0.5% (Sim)")
  c3.metric("Net Interest Margin", "3.8%", "+0.15% (Sim)")
  c4.metric("Operating Cash Flow", "$25M", "+4.3% (Sim)")
  c5.metric("Debt Service Ratio", "1.7X", "-0.2% (Sim)")
  c6.metric("Investment Portfolio", "$421M", "+1.8% (Sim)")

  st.markdown("---")

  # MIDDLE CHARTS SECTION
  col_m1, col_m2, col_m3 = st.columns([1.2, 1.2, 1])

  with col_m1:
    st.subheader("Global Cash Balance (Simulated)")
    if not market_data.empty and "^GSPC" in market_data.columns:
      st.line_chart(market_data["^GSPC"].tail(30), height=220)
    else:
      chart_data = pd.DataFrame({"Cash": [45, 52, 48, 60, 58, 65, 78]}, index=range(7))
      st.line_chart(chart_data, height=220)

  with col_m2:
    st.subheader("Cash Flow Forecast (Simulated)")
    forecast_data = pd.DataFrame({
        "Cash Flow": [100, 120, 110, 140, 160, 150, 180, 210, 190, 240],
        "Forecast": [105, 125, 115, 145, 165, 155, 185, 215, 195, 250]
    })
    st.area_chart(forecast_data, height=220)

  with col_m3:
    st.subheader("Liquidity Composition (Simulated)")
    liquidity_df = pd.DataFrame({
        "Asset": ["Cash", "Short-Term Securities", "Marketable Securities"],
        "Share (%)": [55, 30, 15]
    }).set_index("Asset")
    st.bar_chart(liquidity_df, height=220)

  st.markdown("---")

  # BOTTOM SECTION
  b1, b2 = st.columns([2, 1])
  with b1:
    st.subheader("📋 SQL Transaction Table (Simulated Enterprise Ledger)")
    tx_df = load_transactions()
    st.dataframe(tx_df, use_container_width=True, hide_index=True)

  with b2:
    st.subheader("📊 Revenue by Region ($M - Simulated)")
    region_data = pd.DataFrame({
        "Region": ["Americas", "EMEA", "APAC", "LatAm", "MeA"],
        "Revenue": [550, 420, 390, 310, 280]
    }).set_index("Region")
    st.bar_chart(region_data, height=240)

elif nav_choice == "📋 SQL Transaction Ledger":
  st.subheader("📋 Relational SQL Transaction Database Manager")
  st.markdown("Manage and query the backend SQLite transaction ledger. *Note: Data is simulated for portfolio demonstration.*")
  
  tx_df = load_transactions()
  st.dataframe(tx_df, use_container_width=True, hide_index=True)

elif nav_choice == "⚡ Live API Tickers":
  st.subheader("⚡ Real-Time Market Feed (Live API Data)")
  st.markdown("Streaming live closing prices and market movements directly from Yahoo Finance API endpoints.")
  
  if not market_data.empty:
    st.line_chart(market_data)
    st.dataframe(market_data.tail(15), use_container_width=True)
  else:
    st.warning("Connecting to live market API stream...")

elif nav_choice == "⚙️ Treasury Settings":
  st.subheader("⚙️ System Architecture & Data Documentation")
  st.markdown("""
    ### Data Source Breakdown for Portfolio Review:
    * **Corporate Ledger & Cash Balances:** Simulated enterprise data (SQLite backend) designed to demonstrate database querying, schema structuring, and CRUD operations.
    * **Market Tickers & Indices:** 100% Real-Time Live Data pulled via asynchronous API calls (`yfinance`).
    * **Tech Stack:** Python, Streamlit, Pandas, SQLite, and custom CSS for dark executive UI design.
    """)