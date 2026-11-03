import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="AlphaQuant Terminal", page_icon="📈", layout="wide"
)

st.title("AlphaQuant: Real-Time Financial Intelligence Terminal")

# 1. Robust data loading with fallback
@st.cache_data
def load_data():
    try:
        # Replace "financial_data.csv" with your exact CSV filename if different
        return pd.read_csv("financial_data.csv", parse_dates=["Date"])
    except FileNotFoundError:
        # Graceful fallback generator so the app runs instantly out-of-the-box
        dates = pd.date_range(end=pd.Timestamp.today(), periods=200, freq="B")
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
        return pd.DataFrame([
            {
                "Date": d,
                "Ticker": t,
                "Close": np.random.uniform(100, 500) + (i * 0.2)
            }
            for t in tickers
            for i, d in enumerate(dates)
        ])

df = load_data()

if df is not None and not df.empty:
    # 2. Ensure chronological sorting
    df = df.sort_values("Date")

    # 3. Calculate rolling volatility on the FULL dataset first (fixes the 1M blank view)
    df["Daily_Return"] = df.groupby("Ticker")["Close"].pct_change()
    df["Volatility_30D"] = (
        df.groupby("Ticker")["Daily_Return"]
        .rolling(window=30)
        .std()
        .reset_index(level=0, drop=True)
        * np.sqrt(252)
        * 100
    )

    # 4. Sidebar Time Horizon Selector
    st.sidebar.header("Terminal Controls")
    time_frame = st.sidebar.selectbox(
        "Select Time Horizon", ["1M", "3M", "6M", "1Y", "All"], key="vol_time_frame"
    )

    # 5. Apply date filter AFTER the full calculation is complete
    max_date = df["Date"].max()
    if time_frame == "1M":
        cutoff_date = max_date - pd.DateOffset(months=1)
    elif time_frame == "3M":
        cutoff_date = max_date - pd.DateOffset(months=3)
    elif time_frame == "6M":
        cutoff_date = max_date - pd.DateOffset(months=6)
    elif time_frame == "1Y":
        cutoff_date = max_date - pd.DateOffset(years=1)
    else:
        cutoff_date = df["Date"].min()

    filtered_df = df[df["Date"] >= cutoff_date]

    # 6. Render Plotly Chart
    st.subheader("30-Day Rolling Annualized Volatility Trend (%)")
    if not filtered_df.empty:
        fig = px.line(
            filtered_df,
            x="Date",
            y="Volatility_30D",
            color="Ticker",
            labels={
                "Volatility_30D": "30D Annualized Volatility (%)",
                "Date": "Date",
            },
        )
        fig.update_layout(
            hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data points available for the selected timeframe.")
else:
    st.error("Dataset could not be loaded or is empty.")