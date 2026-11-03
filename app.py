import numpy as np
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="AlphaQuant Terminal", layout="wide", initial_sidebar_state="expanded"
)

# Custom CSS for Institutional Styling
st.markdown(
    """
    <style>
        .main { background-color: #0b0f19; color: #f8fafc; }
        .stMetric { background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; }
    </style>
""",
    unsafe_allow_html=True,
)


# Mock Data Generator for Demonstration (Replace with your actual API/Data loader)
@st.cache_data
def load_market_data(ticker):
    np.random.seed(42 if ticker == "INTC" else 24)
    dates = pd.date_range(end=pd.Timestamp.today(), periods=730, freq="B")
    base_price = 100.0 if ticker == "INTC" else 200.0
    walk = np.cumsum(np.random.normal(0.05, 1.5, len(dates)))
    prices = base_price + walk

    df = pd.DataFrame(
        {
            "Open": prices - np.random.uniform(0, 1, len(dates)),
            "High": prices + np.random.uniform(0.5, 3, len(dates)),
            "Low": prices - np.random.uniform(0.5, 3, len(dates)),
            "Close": prices,
            "Volume": np.random.randint(1000000, 50000000, len(dates)),
        },
        index=dates,
    )
    return df


# --- SIDEBAR CONTROLS ---
st.sidebar.title("AlphaQuant Controls")
ticker = st.sidebar.selectbox("Select Asset", ["INTC", "TSLA", "AAPL", "BTC-USD"])
timeframe = st.sidebar.selectbox("Timeframe Window", ["6mo", "1y", "2y"])

# Load Data
df = load_market_data(ticker)

# --- TIMEFRAME SLICING ---
today = df.index[-1]
if timeframe == "6mo":
    start_date = today - pd.DateOffset(months=6)
elif timeframe == "1y":
    start_date = today - pd.DateOffset(years=1)
else:  # '2y'
    start_date = today - pd.DateOffset(years=2)

filtered_df = df.loc[start_date:today]

# --- CALCULATIONS ---
current_price = filtered_df["Close"].iloc[-1]
prev_close = filtered_df["Close"].iloc[-2]

# Period Metrics
period_high = filtered_df["High"].max()
period_low = filtered_df["Low"].min()

# Professional Delta Logic: Distance from Period High/Low (Institutional Standard)
# Instead of confusing daily 'vs Yest', show how far current price is from the structural extreme.
high_delta = current_price - period_high
low_delta = current_price - period_low

high_pct_from_peak = (high_delta / period_high) * 100
low_pct_from_trough = (low_delta / period_low) * 100

# --- TERMINAL UI HEADER ---
st.title(f"AlphaQuant Terminal — {ticker}")
st.markdown(f"**Active Horizon:** `{timeframe.upper()}` | **Data Points:** `{len(filtered_df)} Sessions`")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label=f"{timeframe.upper()} Period High",
        value=f"${period_high:,.2f}",
        delta=f"{high_pct_from_peak:.2f}% from peak",
        delta_color="off",
    )

with col2:
    st.metric(
        label=f"{timeframe.upper()} Period Low",
        value=f"${period_low:,.2f}",
        delta=f"+{abs(low_pct_from_trough):.2f}% from trough",
        delta_color="off",
    )

with col3:
    daily_change = current_price - prev_close
    daily_pct = (daily_change / prev_close) * 100
    st.metric(
        label="Last Close",
        value=f"${current_price:,.2f}",
        delta=f"{daily_pct:+.2f}% vs Yest",
    )

with col4:
    st.metric(
        label="Period Volume (Avg)",
        value=f"{filtered_df['Volume'].mean():,.0f}",
        delta="Stable",
    )

# --- MAIN CHART DISPLAY ---
st.subheader("Price Action & Structural Extremes")
st.line_chart(filtered_df[["Close", "High", "Low"]])
