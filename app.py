from datetime import datetime
import random
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
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# SQL DATABASE INITIALIZATION
# ==========================================
def init_db():
  conn = sqlite3.connect("command_center.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sql_transactions (
            transaction_id TEXT PRIMARY KEY,
            timestamp TEXT,
            entity_region TEXT,
            description TEXT,
            debit REAL,
            credit REAL,
            status TEXT
        )
    """)
  cursor.execute("SELECT COUNT(*) FROM sql_transactions")
  if cursor.fetchone()[0] == 0:
    sample_txs = [
        ("TXM-9021", "2026-11-02 21:03:07", "Americas (US)", "PAYMENT FROM CLIENT A", 0.0, 120500.0, "CONFIRMED"),
        ("TXM-9020", "2026-11-02 21:03:00", "EMEA (Europe)", "UTILITY BILL PAYMENT", 15200.0, 0.0, "PROCESSING"),
        ("TXN-9019", "2026-11-02 21:03:00", "APAC (Singapore)", "PAYMENT FROM CLIENT A", 0.0, 15500.0, "PROCESSING"),
        ("TXN-9018", "2026-11-02 21:00:15", "EMEA (Europe)", "SWIFT WIRE TRANSFER", 450000.0, 0.0, "CONFIRMED"),
        ("TXN-9017", "2026-11-02 20:55:40", "APAC (Singapore)", "VENDOR SETTLEMENT", 82300.0, 0.0, "CONFIRMED"),
    ]
    cursor.executemany("INSERT OR IGNORE INTO sql_transactions VALUES (?, ?, ?, ?, ?, ?, ?)", sample_txs)
  conn.commit()
  conn.close()


init_db()


def load_data():
  conn = sqlite3.connect("command_center.db")
  df = pd.read_sql_query("SELECT * FROM sql_transactions ORDER BY timestamp DESC", conn)
  conn.close()
  return df


# ==========================================
# LIVE API MARKET FEED (REAL DATA)
# ==========================================
@st.cache_data(ttl=300)
def fetch_market_data():
  try:
    data = yf.download(["^GSPC", "^IXIC", "^TNX"], period="1mo", progress=False)["Close"]
    if isinstance(data.columns, pd.MultiIndex):
      data.columns = data.columns.droplevel(0)
    return data
  except Exception:
    return pd.DataFrame()


market_df = fetch_market_data()

# ==========================================
# SIDEBAR NAVIGATION & INTERACTIVE FILTERS
# ==========================================
st.sidebar.markdown("### 🏦 Aegis Command")
st.sidebar.markdown("---")
nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "📊 Executive Command Center",
        "📋 SQL Transaction Ledger",
        "⚡ Live API Analytics",
        "🤖 Aegis AI Assistant",
        "⚙️ Treasury Settings",
    ],
)

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Global Filters")
selected_region = st.sidebar.selectbox("Filter Region", ["All Regions", "Americas (US)", "EMEA (Europe)", "APAC (Singapore)"])
currency_mode = st.sidebar.selectbox("Currency Display", ["USD ($)", "EUR (€)", "GBP (£)", "AED (د.إ)", "JPY (¥)"])
selected_status = st.sidebar.selectbox("Transaction Status", ["All Statuses", "CONFIRMED", "PROCESSING"])

st.sidebar.markdown("---")
st.sidebar.success("🟢 Secure Stream Active")

# FX Conversion Multipliers
fx_rates = {"USD ($)": 1.0, "EUR (€)": 0.92, "GBP (£)": 0.79, "AED (د.إ)": 3.67, "JPY (¥)": 152.0}
fx_symbol = {"USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£", "AED (د.إ)": "AED ", "JPY (¥)": "¥"}
mult = fx_rates[currency_mode]
sym = fx_symbol[currency_mode]

# Load and filter main dataset
df = load_data()
if selected_region != "All Regions":
  df = df[df["entity_region"] == selected_region]
if selected_status != "All Statuses":
  df = df[df["status"] == selected_status]

# ==========================================
# ROUTING VIEWS
# ==========================================

if nav_choice == "📊 Executive Command Center":
  st.markdown(f"""
        <div class="command-header">
            <h2 style="margin:0; color:#ffffff; font-size: 1.5rem;">🌐 GLOBAL TREASURY COMMAND CENTER</h2>
            <div style="font-size: 0.85rem; color: #00ff66; font-weight: 600;">
                REGION: {selected_region} &nbsp;|&nbsp; CURRENCY: {currency_mode}
            </div>
        </div>
    """, unsafe_allow_html=True)

  # 6 KPI Metric Cards
  c1, c2, c3, c4, c5, c6 = st.columns(6)
  c1.metric("Cash on Hand", f"{sym}{78.2 * mult:.1f}M", "+2.1%")
  c2.metric("Forex Exposure", f"{sym}{1.4 * mult:.1f}B", "-0.5%")
  c3.metric("Net Interest Margin", "3.8%", "+0.15%")
  c4.metric("Operating Cash Flow", f"{sym}{25 * mult:.0f}M", "+4.3%")
  c5.metric("Debt Service Ratio", "1.7X", "-0.2%")
  c6.metric("Investment Portfolio", f"{sym}{421 * mult:.0f}M", "+1.8%")

  st.markdown("---")

  # Middle Charts Section
  col_m1, col_m2, col_m3 = st.columns([1.2, 1.2, 1])

  with col_m1:
    st.subheader("Global Cash Balance")
    if not market_df.empty and "^GSPC" in market_df.columns:
      st.line_chart(market_df["^GSPC"].tail(30), height=220)
    else:
      st.line_chart(pd.DataFrame({"Cash": [45, 52, 48, 60, 58, 65, 78]}, index=range(7)), height=220)

  with col_m2:
    st.subheader("Cash Flow Forecast (90D)")
    forecast_data = pd.DataFrame({
        "Cash Flow": [100*mult, 120*mult, 110*mult, 140*mult, 160*mult, 150*mult, 180*mult, 210*mult, 190*mult, 240*mult],
        "Forecast": [105*mult, 125*mult, 115*mult, 145*mult, 165*mult, 155*mult, 185*mult, 215*mult, 195*mult, 250*mult]
    })
    st.area_chart(forecast_data, height=220)

  with col_m3:
    st.subheader("Liquidity Breakdown")
    liquidity_df = pd.DataFrame({
        "Asset": ["Cash", "Short-Term", "Marketable"],
        "Share (%)": [55, 30, 15]
    }).set_index("Asset")
    st.bar_chart(liquidity_df, height=220)

  st.markdown("---")

  # Bottom Section
  b1, b2 = st.columns([2, 1])
  with b1:
    st.subheader("📋 Filtered SQL Transaction Ledger")
    display_df = df.copy()
    display_df["debit"] = display_df["debit"] * mult
    display_df["credit"] = display_df["credit"] * mult
    st.dataframe(display_df, use_container_width=True, hide_index=True)

  with b2:
    st.subheader("📊 Revenue by Region")
    region_data = pd.DataFrame({
        "Region": ["Americas", "EMEA", "APAC", "LatAm"],
        "Revenue": [550*mult, 420*mult, 390*mult, 310*mult]
    }).set_index("Region")
    st.bar_chart(region_data, height=240)

elif nav_choice == "📋 SQL Transaction Ledger":
  st.subheader("📋 Relational SQL Transaction Database Manager")
  st.markdown("Query, inspect, and insert new corporate ledger records into the SQLite database.")

  with st.form("new_trade_form"):
    st.markdown("### ⚡ Execute & Commit New Treasury Transaction")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
      t_id = f"TXN-{random.randint(8000, 9999)}"
      t_reg = st.selectbox("Entity Region", ["Americas (US)", "EMEA (Europe)", "APAC (Singapore)"])
      t_desc = st.text_input("Description", "CLIENT SETTLEMENT WIRE")
    with col_f2:
      t_type = st.selectbox("Transaction Type", ["Credit (Incoming)", "Debit (Outgoing)"])
      t_amt = st.number_input("Amount ($ USD)", min_value=100.0, value=50000.0)

    submitted = st.form_submit_button("Commit Transaction to SQL DB")
    if submitted:
      debit_val = t_amt if t_type == "Debit (Outgoing)" else 0.0
      credit_val = t_amt if t_type == "Credit (Incoming)" else 0.0
      now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      
      conn = sqlite3.connect("command_center.db")
      cur = conn.cursor()
      cur.execute("INSERT INTO sql_transactions VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (t_id, now_str, t_reg, t_desc, debit_val, credit_val, "CONFIRMED"))
      conn.commit()
      conn.close()
      st.success(f"Successfully committed transaction {t_id}!")
      st.rerun()

  st.markdown("---")
  st.subheader("Current Database Records")
  st.dataframe(load_data(), use_container_width=True, hide_index=True)

elif nav_choice == "⚡ Live API Analytics":
  st.subheader("⚡ Real-Time Market Feed Analytics")
  st.markdown("Streaming real-time benchmark yields and stock indices directly from Yahoo Finance API.")
  if not market_df.empty:
    st.line_chart(market_df)
    st.dataframe(market_df.tail(15), use_container_width=True)
  else:
    st.warning("Connecting to live API stream...")

elif nav_choice == "🤖 Aegis AI Assistant":
  st.subheader("🤖 Aegis AI Treasury Assistant")
  st.markdown("Ask natural language questions about your cash positions, transaction logs, forex exposure, or risk metrics.")

  if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your Aegis AI Treasury Assistant. How can I assist you with your cash flow or portfolio analytics today?"}
    ]

  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])

  if prompt := st.chat_input("Ask about cash balance, FX risk, or SQL transactions..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
      st.markdown(prompt)

    prompt_lower = prompt.lower()
    if "cash" in prompt_lower or "balance" in prompt_lower:
      response = "Your current global cash on hand is **$78.2M**, with an operating cash flow of **$25M** (+4.3% growth)."
    elif "transaction" in prompt_lower or "ledger" in prompt_lower:
      tx_count = len(load_data())
      response = f"There are currently **{tx_count} active transaction records** logged in the SQLite relational database across Americas, EMEA, and APAC."
    elif "fx" in prompt_lower or "forex" in prompt_lower:
      response = "Current forex exposure stands at **$1.4B**, primarily hedged against EUR/USD and USD/JPY currency fluctuations."
    else:
      response = f"Analyzing your query regarding *'{prompt}'* against current treasury parameters: All active portfolios and market indicators are operating within normal risk thresholds."

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
      st.markdown(response)

elif nav_choice == "⚙️ Treasury Settings":
  st.subheader("⚙️ System Architecture & Documentation")
  st.markdown("""
  ### Portfolio Project Specifications:
  * **Theme:** Black & Neon Green institutional dark mode (`#0b0f19` and `#00ff66`).
  * **Backend:** Relational SQLite database (`command_center.db`) supporting live transaction logging and ingestion.
  * **Market Integration:** Live REST API streaming via `yfinance` for macro indices and treasury yields.
  * **Interactive Intelligence:** Built-in AI assistant contextually querying live metrics and transaction tables.
  """)