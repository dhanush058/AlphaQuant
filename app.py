import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="AlphaQuant Terminal", layout="wide")

# 1. Load your dataset (replace with your actual data loading function/CSV read)
@st.cache_data
def load_data():
    # Ensure your data loading logic points to your source files or API
    return pd.read_csv("your_data_file.csv", parse_dates=["Date"])

df = load_data()

# 2. Ensure chronological sorting and compute rolling metrics on the FULL dataset first
if df is not None and not df.empty:
    df = df.sort_values("Date")
    
    df["Daily_Return"] = df.groupby("Ticker")["Close"].pct_change()
    df["Volatility_30D"] = (
        df.groupby("Ticker")["Daily_Return"]
        .rolling(window=30)
        .std()
        .reset_index(level=0, drop=True)
        * np.sqrt(252)
        * 100
    )

    # 3. Time horizon selector
    time_frame = st.selectbox(
        "Select Time Horizon", ["1M", "3M", "6M", "1Y", "All"], key="vol_time_frame"
    )

    # 4. Apply date filter AFTER the calculation
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

    # 5. Render Plotly chart
    fig = px.line(
        filtered_df,
        x="Date",
        y="Volatility_30D",
        color="Ticker",
        title="30-Day Rolling Annualized Volatility Trend (%)",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Dataset could not be loaded or is empty.")