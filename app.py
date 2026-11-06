from datetime import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="AlphaQuant: Institutional Market Intelligence & Analytics",
    page_icon="⚡",
    layout="wide",
)

# ==========================================
# CUSTOM STYLING (CRYSTAL BLUE THEME)
# ==========================================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #38bdf8;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.1);
        min-height: 95px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #0ea5e9;
        box-shadow: 0 0 20px rgba(14, 165, 233, 0.3);
    }
    div[data-testid="stMetric"] label {
        color: #7dd3fc !important;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-weight: 700;
        font-size: 1.25rem;
    }
    h1, h2, h3 {
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    .terminal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #1e293b;
        padding: 15px 25px;
        border-radius: 10px;
        border: 1px solid #38bdf8;
        margin-bottom: 20px;
    }
    .analytics-card {
        background: #1e293b;
        border: 1px solid #334151;
        padding: 25px;
        border-radius: 10px;
        margin-bottom: 20px;
        line-height: 1.7;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# SIDEBAR CONTROLS & UNIFIED DROPDOWN ROUTING
# ==========================================
st.sidebar.markdown("### ⚡ AlphaQuant Terminal")
st.sidebar.markdown("---")

nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "📈 Price Action & Technicals",
        "📊 Quantitative Risk & Volatility",
        "🔗 Multi-Asset Performance & Spread",
        "📖 Analytics Guide & Overview",
    ],
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Market Screener Input")

comprehensive_tickers = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "AMD",
    "NFLX",
    "INTC",
    "SPY",
    "QQQ",
    "BTC-USD",
    "ETH-USD",
]

active_ticker = st.sidebar.selectbox(
    "Select Focus Asset", comprehensive_tickers, index=0
)

timeframe = st.sidebar.selectbox(
    "Historical Timeframe (Analysis Window)",
    ["1mo", "3mo", "6mo", "1y", "2y"],
    index=2,
)

st.sidebar.markdown("---")
st.sidebar.success(f"🔵 Active Asset: **{active_ticker}**")


# ==========================================
# DATA INGESTION ENGINE
# ==========================================
@st.cache_data(ttl=900, show_spinner=False)
def fetch_raw_stock_data(ticker_symbol, period_str="2y"):
    ticker_symbol = ticker_symbol.strip().upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_symbol}?interval=1d&range={period_str}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code != 200:
            return pd.DataFrame()

        data = response.json()
        if not data.get("chart", {}).get("result"):
            return pd.DataFrame()
            
        result = data["chart"]["result"][0]
        if "timestamp" not in result or not result.get("indicators", {}).get("quote"):
            return pd.DataFrame()
            
        timestamps = result["timestamp"]
        quote = result["indicators"]["quote"][0]

        df = pd.DataFrame(
            {
                "Open": quote.get("open", []),
                "High": quote.get("high", []),
                "Low": quote.get("low", []),
                "Close": quote.get("close", []),
                "Volume": quote.get("volume", []),
            },
            index=pd.to_datetime(timestamps, unit="s"),
        )

        df = df.dropna(subset=["Close"])
        return df
    except Exception:
        return pd.DataFrame()


def fetch_live_stock_data(ticker_symbol, period_str="1y"):
    raw_df = fetch_raw_stock_data(ticker_symbol, period_str="2y")
    if raw_df.empty:
        return raw_df

    raw_df["SMA_20"] = raw_df["Close"].rolling(window=20).mean()
    raw_df["SMA_50"] = raw_df["Close"].rolling(window=50).mean()
    raw_df["BB_Std"] = raw_df["Close"].rolling(window=20).std()
    raw_df["BB_Upper"] = raw_df["SMA_20"] + (raw_df["BB_Std"] * 2)
    raw_df["BB_Lower"] = raw_df["SMA_20"] - (raw_df["BB_Std"] * 2)
    raw_df["Daily_Return"] = raw_df["Close"].pct_change()
    raw_df["Rolling_Vol_30"] = (
        raw_df["Daily_Return"].rolling(window=30).std() * np.sqrt(252) * 100
    )

    max_date = raw_df.index.max()
    if period_str == "1mo":
        cutoff_date = max_date - pd.DateOffset(months=1)
    elif period_str == "3mo":
        cutoff_date = max_date - pd.DateOffset(months=3)
    elif period_str == "6mo":
        cutoff_date = max_date - pd.DateOffset(months=6)
    elif period_str == "1y":
        cutoff_date = max_date - pd.DateOffset(years=1)
    elif period_str == "2y":
        cutoff_date = max_date - pd.DateOffset(years=2)
    else:
        cutoff_date = raw_df.index.min()

    return raw_df[raw_df.index >= cutoff_date]


@st.cache_data(ttl=900, show_spinner=False)
def fetch_multi_asset_data(tuple_tickers, period_str="1y"):
    closes = {}
    for t in tuple_tickers:
        df = fetch_live_stock_data(t, period_str)
        if not df.empty and "Close" in df.columns:
            closes[t] = df["Close"].dropna()

    if closes:
        multi_df = pd.DataFrame(closes).dropna()
        if not multi_df.empty:
            return multi_df
    return pd.DataFrame()


# ==========================================
# VIEW ROUTING
# ==========================================

if nav_choice == "📈 Price Action & Technicals":
    st.markdown(
        f"""
        <div class
