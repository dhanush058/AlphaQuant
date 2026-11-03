import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="AlphaQuant Terminal", page_icon="📈", layout="wide"
)

st.title("AlphaQuant: Real-Time Financial Intelligence Terminal")


# 1. Data Loading (Replace or adapt with your actual API fetching/CSV loading logic)
@st.cache_data
def load_financial_data():
  # Example: If loading from a file or API, ensure 'Date', 'Ticker', and 'Close' exist
  # Replace "financial_data.csv" with your actual file path or API call
  try:
    data = pd.read_csv("financial_data.csv", parse_dates=["Date"])
  except FileNotFoundError:
    # Fallback dummy data generator for demonstration so the script runs out-of-the-box
    dates = pd.date_range(end=pd.Timestamp.today(), periods=200, freq="B")
    tickers = ["AAPL", "MSFT", "GOOGL"]
    data = pd.DataFrame(
        [
            {
                "Date": d,
                "Ticker": t,
                "Close": np.random.uniform(100, 300)
                + (i * 0.5),  # mock price trend
            }
            for t in tickers
            for i, d in enumerate(dates)
        ]
    )
  return data


df = load_financial_data()

# 2. Defensive check for data loading
if df is None or df.empty:
  st.error(
      "Failed to load dataset or the dataset is empty. Please check your data"
      " source."
  )
elif "Date" not in df.columns or "Close" not in df.columns:
  st.error("The dataset is missing required columns ('Date' or 'Close').")
else:
  # Ensure chronological ordering for accurate rolling calculations across full history
  df = df.sort_values("Date")

  # 3. Calculate daily returns and 30-day rolling annualized volatility ON THE FULL DATASET
  df["Daily_Return"] = df.groupby("Ticker")["Close"].pct_change()
  df["Volatility_30D"] = (
      df.groupby("Ticker")["Daily_Return"]
      .rolling(window=30)
      .std()
      .reset_index(level=0, drop=True)
      * np.sqrt(252)
      * 100
  )  # Annualized %

  # 4. Sidebar Controls for Time Horizon
  st.sidebar.header("Display Settings")
  time_frame = st.sidebar.selectbox(
      "Select Time Horizon", ["1M", "3M", "6M", "1Y", "All"]
  )

  # Determine cutoff date based on the latest date present in the dataset
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

  # 5. Apply date filter AFTER rolling calculation is fully complete
  filtered_df = df[df["Date"] >= cutoff_date]

  # 6. Render Plotly Chart
  st.subheader("30-Day Rolling Annualized Volatility Trend (%)")
  if not filtered_df.empty and filtered_df["Volatility_30D"].notna().any():
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
    st.warning(
        "Insufficient data points available in the selected window to render"
        " the volatility trend."
    )