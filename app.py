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

# Comprehensive curated asset pool encompassing mega-cap tech, indices, crypto, and growth equities
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

# Fully dropdown-driven asset selection to ensure absolute data consistency and prevent analysis errors
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
    """Fetches a longer max/buffer window to ensure rolling indicators have sufficient history."""
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
    """Fetches raw data with buffer history, computes indicators globally, then filters by timeframe."""
    raw_df = fetch_raw_stock_data(ticker_symbol, period_str="2y")
    if raw_df.empty:
        return raw_df

    # Compute rolling indicators across the full buffer history FIRST
    raw_df["SMA_20"] = raw_df["Close"].rolling(window=20).mean()
    raw_df["SMA_50"] = raw_df["Close"].rolling(window=50).mean()
    raw_df["BB_Std"] = raw_df["Close"].rolling(window=20).std()
    raw_df["BB_Upper"] = raw_df["SMA_20"] + (raw_df["BB_Std"] * 2)
    raw_df["BB_Lower"] = raw_df["SMA_20"] - (raw_df["BB_Std"] * 2)
    raw_df["Daily_Return"] = raw_df["Close"].pct_change()
    raw_df["Rolling_Vol_30"] = (
        raw_df["Daily_Return"].rolling(window=30).std() * np.sqrt(252) * 100
    )

    # Now slice down to the requested timeframe view
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
        <div class="terminal-header">
            <h2 style="margin:0; color:#f8fafc; font-size: 1.5rem;">📈 MARKET INTELLIGENCE: {active_ticker}</h2>
            <div style="font-size: 0.85rem; color: #38bdf8; font-weight: 600;">
                WINDOW: {timeframe.upper()} &nbsp;|&nbsp; THEME: CRYSTAL BLUE
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    with st.spinner(f"Streaming data for {active_ticker}..."):
        stock_df = fetch_live_stock_data(active_ticker, timeframe)

    if not stock_df.empty and "Close" in stock_df.columns:
        latest_close = float(stock_df["Close"].iloc[-1])
        
        # Robust prior close fetching to guarantee true 24h accuracy
        if len(stock_df) >= 2:
            prev_close = float(stock_df["Close"].iloc[-2])
        else:
            prev_close = latest_close
            
        daily_change_pct = ((latest_close - prev_close) / prev_close) * 100
        high_period = float(stock_df["High"].max())
        low_period = float(stock_df["Low"].min())
        total_volume = int(stock_df["Volume"].iloc[-1])

        # Calculate institutional metrics: percentage distance from period peak and trough
        high_pct_from_peak = ((latest_close - high_period) / high_period) * 100
        low_pct_from_trough = ((latest_close - low_period) / low_period) * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Live Close Price",
            f"${latest_close:,.2f}",
            f"{daily_change_pct:+.2f}% 24h",
        )
        c2.metric(
            "Period High",
            f"${high_period:,.2f}",
            f"{high_pct_from_peak:+.2f}% from peak",
        )
        c3.metric(
            "Period Low",
            f"${low_period:,.2f}",
            f"{low_pct_from_trough:+.2f}% from trough",
        )
        c4.metric("Latest Volume", f"{total_volume:,}", "Shares Traded")

        st.markdown("---")

        st.subheader(
            f"Price Action, Moving Averages & Bollinger Bands ({active_ticker})"
        )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df["Close"],
                mode="lines",
                name="Close Price",
                line=dict(color="#38bdf8", width=2),
                hovertemplate=(
                    "<b>Date</b>: %{x|%b %d, %Y}<br><b>Price</b>:"
                    " $%{y:,.2f}<extra></extra>"
                ),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df["SMA_20"],
                mode="lines",
                name="SMA 20",
                line=dict(color="#38bdf8", width=1.5, dash="dash"),
                hovertemplate="<b>SMA 20</b>: $%{y:,.2f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df["SMA_50"],
                mode="lines",
                name="SMA 50",
                line=dict(color="#f43f5e", width=1.5, dash="dash"),
                hovertemplate="<b>SMA 50</b>: $%{y:,.2f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df["BB_Upper"],
                mode="lines",
                name="BB Upper",
                line=dict(color="rgba(56, 189, 248, 0.3)", width=1),
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df["BB_Lower"],
                mode="lines",
                name="BB Lower",
                line=dict(color="rgba(56, 189, 248, 0.3)", width=1),
                fill="tonexty",
                fillcolor="rgba(56, 189, 248, 0.08)",
                hoverinfo="skip",
            )
        )

        fig.update_layout(
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#f8fafc"),
            height=450,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            xaxis=dict(showgrid=True, gridcolor="#334155", title=""),
            yaxis=dict(showgrid=True, gridcolor="#334155", title="Price (USD)"),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Daily Trading Volume Breakdown")

        vol_tail = stock_df.tail(60).copy()

        def format_volume(val):
            if val >= 1e9:
                return f"{val / 1e9:.2f}B"
            elif val >= 1e6:
                return f"{val / 1e6:.2f}M"
            elif val >= 1e3:
                return f"{val / 1e3:.2f}K"
            else:
                return f"{val:.2f}"

        vol_tail["Formatted_Volume"] = vol_tail["Volume"].apply(format_volume)
        vol_tail["Volume_Val"] = vol_tail["Volume"]

        fig_vol = px.bar(
            vol_tail,
            x=vol_tail.index,
            y="Volume_Val",
            custom_data=["Formatted_Volume"],
        )
        fig_vol.update_layout(
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#f8fafc"),
            height=280,
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(showgrid=False, title=""),
            yaxis=dict(showgrid=True, gridcolor="#334155", title="Volume"),
        )
        fig_vol.update_traces(
            marker_color="#38bdf8",
            hovertemplate=(
                "<b>Date</b>: %{x|%b %d, %Y}<br><b>Volume</b>:"
                " %{customdata[0]}<extra></extra>"
            ),
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    else:
        st.error(
            f"⚠️ Unable to retrieve data for '{active_ticker}'. Please verify the symbol format."
        )

elif nav_choice == "📊 Quantitative Risk & Volatility":
    st.subheader(
        f"📊 Quantitative Risk & Volatility Analytics ({active_ticker})"
    )

    with st.spinner(f"Computing risk metrics for {active_ticker}..."):
        stock_df = fetch_live_stock_data(active_ticker, timeframe)

    if not stock_df.empty and "Close" in stock_df.columns:
        annualized_vol = stock_df["Daily_Return"].std() * np.sqrt(252) * 100
        cumulative_return = (
            (stock_df["Close"].iloc[-1] - stock_df["Close"].iloc[0])
            / stock_df["Close"].iloc[0]
        ) * 100
        mean_return_val = stock_df["Daily_Return"].mean() * 100

        q1, q2, q3 = st.columns(3)
        q1.metric(
            "Annualized Volatility (Risk)",
            f"{annualized_vol:.2f}%",
            None,
            help="Annualized Standard Deviation",
        )
        q2.metric(
            "Cumulative Period Return",
            f"{cumulative_return:+.2f}%",
            f"{cumulative_return:+.2f}% ({timeframe})",
        )
        q3.metric(
            "Daily Mean Return",
            f"{mean_return_val:+.3f}%",
            f"{mean_return_val:+.3f}% vs baseline",
        )

        st.markdown("---")
        st.subheader("30-Day Rolling Annualized Volatility Trend (%)")

        vol_clean_df = stock_df.dropna(subset=["Rolling_Vol_30"]).copy()

        fig_vol_trend = go.Figure()
        fig_vol_trend.add_trace(
            go.Scatter(
                x=vol_clean_df.index,
                y=vol_clean_df["Rolling_Vol_30"],
                mode="lines",
                name="30D Volatility",
                line=dict(color="#38bdf8", width=2),
                hovertemplate=(
                    "<b>Date</b>: %{x|%b %d, %Y}<br><b>Volatility</b>:"
                    " %{y:.2f}%<extra></extra>"
                ),
            )
        )
        fig_vol_trend.update_layout(
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#f8fafc"),
            height=320,
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(showgrid=True, gridcolor="#334155", title=""),
            yaxis=dict(showgrid=True, gridcolor="#334155", title="Volatility (%)"),
            showlegend=False,
        )
        st.plotly_chart(fig_vol_trend, use_container_width=True)

        st.markdown("---")
        st.subheader("Daily Return Distribution Frequency")

        returns_clean = (stock_df["Daily_Return"].dropna() * 100).reset_index()
        returns_clean.columns = ["Date", "Return"]

        fig_hist = px.histogram(
            returns_clean,
            x="Return",
            nbins=50,
        )
        fig_hist.update_layout(
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#f8fafc"),
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor="#334155", title="Daily Return (%)"),
            yaxis=dict(
                showgrid=True,
                gridcolor="#334155",
                title="Number of Trading Days",
            ),
        )
        fig_hist.update_traces(
            marker_color="#38bdf8",
            hovertemplate=(
                "<b>Return Range</b>: %{x}<br><b>Number of Trading Days</b>:"
                " %{y}<extra></extra>"
            ),
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.warning(f"⚠️ No quantitative data available for '{active_ticker}'.")

elif nav_choice == "🔗 Multi-Asset Performance & Spread":
    st.subheader("🔗 Multi-Asset Comparative Performance & Spread")
    st.markdown(
        "Comparing normalized cumulative percentage growth across key market leaders (Baseline = 100):"
    )

    with st.spinner("Fetching multi-asset sector stream..."):
        multi_tickers = ("AAPL", "MSFT", "NVDA", "TSLA", "SPY", "QQQ")
        multi_df = fetch_multi_asset_data(multi_tickers, timeframe)

    if not multi_df.empty and len(multi_df) > 0:
        norm_df = (multi_df / multi_df.iloc[0]) * 100

        fig_multi = px.line(norm_df)
        fig_multi.update_layout(
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#f8fafc"),
            height=480,
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(showgrid=True, gridcolor="#334155", title=""),
            yaxis=dict(
                showgrid=True,
                gridcolor="#334155",
                title="Normalized Growth (Base = 100)",
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        fig_multi.update_traces(
            hovertemplate=(
                "<b>Date</b>: %{x|%b %d, %Y}<br><b>Index Value</b>:"
                " %{y:,.2f}<extra></extra>"
            )
        )
        st.plotly_chart(fig_multi, use_container_width=True)
    else:
        st.warning("Multi-asset comparison stream currently unavailable.")

elif nav_choice == "📖 Analytics Guide & Overview":
    st.subheader("📖 Analytics Guide & Overview")
    st.markdown(
        "A comprehensive executive walkthrough explaining how every metric, chart, and feature within AlphaQuant generates business value and analytical insight."
    )

    st.markdown("### 🏢 Product Utility and Business Value")
    st.markdown(
        """
    <div class="analytics-card">
        In modern financial markets and corporate strategy, raw data tables are overwhelmingly dense, while static spreadsheet reports lack real-time interactivity. AlphaQuant addresses this challenge by functioning as an on-demand, institutional-grade Business Intelligence terminal. 
        <br><br>
        It empowers analysts, stakeholders, and strategic decision-makers to instantly evaluate asset performance, quantify risk exposure, and benchmark market leaders without requiring complex infrastructure or expensive proprietary desk software.
    </div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### 📈 Price Action and Technical Analysis")
    st.markdown(
        """
    <div class="analytics-card">
        The top metric cards provide an immediate snapshot of market conditions, showing the latest closing price, period highs and lows, and overall trading liquidity at a glance. This allows stakeholders to gauge 24-hour momentum before diving deeper into historical trends.
        <br><br>
        The main price chart incorporates Simple Moving Averages over 20-day and 50-day windows. By smoothing out daily market noise, these trendlines help analysts spot short-term versus medium-term momentum shifts and potential trend reversals. Framing the price action, the Bollinger Band channel establishes dynamic market boundaries. When the bands contract tightly together, they signal an impending market breakout. When prices touch or exceed the outer boundaries, analysts can quickly identify overextended or overbought and oversold conditions.
        <br><br>
        Because market volume historically precedes price action, the volume bar chart displays daily trading activity. Volume spikes—intelligently formatted in Billions, Millions, or Thousands on hover—confirm the validity behind major price breakouts or sudden institutional sell-offs.
    </div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### 📊 Quantitative Risk and Volatility Intelligence")
    st.markdown(
        """
    <div class="analytics-card">
        Evaluating asset performance without accounting for risk is incomplete. The summary risk metrics translate raw price fluctuations into standardized financial figures, presenting annualized standard deviation to inform portfolio managers of the risk profile associated with holding an asset over time.
        <br><br>
        Because market uncertainty is never constant, the 30-day rolling annualized volatility trend chart tracks how risk shifts dynamically. This visualization highlights specific volatility spikes or periods of relative calm corresponding to macroeconomic news cycles, earnings announcements, or geopolitical shifts.
        <br><br>
        To understand structural market behavior, the daily return distribution histogram maps out the exact shape of historical gains and losses. Analysts rely on this distribution to evaluate skewness and tail risk, observing the precise frequency of extreme daily positive or negative swings.
    </div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### 🔗 Multi-Asset Comparative Performance")
    st.markdown(
        """
    <div class="analytics-card">
        Comparing a lower-priced equity directly against a high-value technology stock or cryptocurrency breaks standard visual scaling due to nominal price discrepancies. 
        <br><br>
        The Multi-Asset Performance module solves this by rescaling every selected asset to start at a standardized baseline index of 100 on day one. This normalization technique enables analysts and portfolio strategists to instantly evaluate relative strength, growth divergence, and sector correlation across market leaders and major benchmarks side-by-side.
    </div>
""",
        unsafe_allow_html=True,
    )
