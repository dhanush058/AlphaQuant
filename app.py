import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Assume 'df' contains historical data spanning well beyond the last 30 days
# Columns required: ['Date', 'Close', 'Ticker']

# Sort chronologically to ensure accurate rolling calculations
df = df.sort_values("Date")

# 2. Calculate daily returns and 30-day rolling annualized volatility ON THE FULL DATASET
df["Daily_Return"] = df.groupby("Ticker")["Close"].pct_change()
df["Volatility_30D"] = (
    df.groupby("Ticker")["Daily_Return"]
    .rolling(window=30)
    .std()
    .reset_index(level=0, drop=True)
    * np.sqrt(252)
    * 100
)  # Annualized %

# 3. Sidebar / User selection for time frame
time_frame = st.selectbox(
    "Select Time Horizon", ["1M", "3M", "6M", "1Y", "All"]
)

# Determine the cutoff date based on the latest date in the dataset
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

# 4. APPLY THE DATE FILTER AFTER THE METRIC IS ALREADY CALCULATED
filtered_df = df[df["Date"] >= cutoff_date]

# 5. Render Plotly Chart
fig = px.line(
    filtered_df,
    x="Date",
    y="Volatility_30D",
    color="Ticker",
    title="30-Day Rolling Annualized Volatility Trend (%)",
)
st.plotly_chart(fig, use_container_width=True)