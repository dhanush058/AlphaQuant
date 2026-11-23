# 📈 AlphaQuant Financial Intelligence & Quantitative Risk Terminal

An interactive market intelligence and risk analytics app built with Python, Pandas, NumPy, Plotly, and Streamlit. It pulls up-to-date daily market data on demand, computes technical trend, risk, drawdown, and correlation metrics, compares multiple assets side by side, and turns those numbers into clear takeaways with one-click CSV exports and a built-in analytics guide.

Filtering or zooming into a short date range often leaves missing early values (`NaN`) or distorts trend lines. AlphaQuant solves this by loading a 2-year daily price buffer first, computing indicators across the full series, and then cleanly slicing to the selected view window.

🔗 **Live App:** https://alphaquant-analytics.streamlit.app/

---

### 🎯 Overview & Supported Assets
AlphaQuant covers **14 market instruments** across large-cap equities, broad market ETFs, and spot crypto pairs:
- **Equities:** `AAPL`, `MSFT`, `GOOGL`, `AMZN`, `NVDA`, `META`, `TSLA`, `AMD`, `NFLX`, `INTC`
- **Index ETFs:** `SPY`, `QQQ`
- **Crypto Pairs:** `BTC-USD`, `ETH-USD`

**What You Can Do:**
- **Switch Across Four Views:** *Price Action & Technicals*, *Quantitative Risk & Volatility*, *Multi-Asset Performance & Spread*, and *Analytics Guide & Overview*.
- **Choose Time Horizons:** `1mo`, `3mo`, `6mo`, `1y`, and `2y`.
- **Compare Multiple Assets:** Pick **2 to 6 assets** to compare relative growth and see how closely they move together.
- **Export Data:** Download underlying table data as a CSV file for further analysis.

---

### 🚀 Key Features & Analytical Workflow

#### 1. Buffer-First Data Pipeline
- Fetches a 2-year daily (`1d`) OHLCV dataset from Yahoo Finance's chart API using `requests`, with fallback endpoint handling if the primary route runs into trouble.
- Validates response payloads, drops rows with missing closing prices, and handles empty or short datasets safely so charts and metrics never fail silently.
- Computes rolling metrics across the full 2-year buffer before trimming to the chosen lookback window (`1mo`–`2y`) so moving averages, bands, and volatility curves stay smooth and consistent.

#### 2. Price Trend & Volume View (*Price Action & Technicals*)
- **Key Summary Cards:** Highlights the latest close price and change, period high and low with percentage distance from peaks or troughs, and recent volume compared against the 20-day average.
- **Plain-English Takeaways & Analytics Guide:** Translates moving average positions (`SMA_20`, `SMA_50`), 20-day volume participation, and risk/drawdown context into clear, practical summaries that both technical and non-technical readers can follow.
- **Interactive Charts:** Plots closing price, 20-day and 50-day moving averages, 20-day Bollinger Bands (an upper and lower band set two standard deviations above and below the 20-day moving average), and daily volume bars with clean formatting (`K`, `M`, `B`) and date-aligned daily labels.

#### 3. Risk & Return Diagnostics (*Quantitative Risk & Volatility*)
- **Core Risk Metrics:** Tracks annualized volatility (daily return standard deviation scaled across 252 trading days as a percentage), cumulative period return, **Sharpe Ratio** (risk-adjusted return using a `0%` risk-free rate baseline), and **Maximum Drawdown** (the steepest percentage drop from a rolling peak to a subsequent trough).
- **Distribution & Regime Charts:** Combines a 30-day rolling annualized volatility curve with a 50-bin histogram of daily percentage returns to show both shifting volatility regimes and return spread.

#### 4. Multi-Asset Comparison (*Multi-Asset Performance & Spread*)
- **Normalized Growth (`Base = 100`):** Aligns **2 to 6 selected assets** on shared dates and sets every starting point to `100` (`(price / first_price) * 100`) so equities, ETFs, and crypto pairs at very different price levels can be compared fairly on percentage growth.
- **Pairwise Correlation Matrix:** Calculates correlation scores (`-1.00` to `+1.00`) across selected assets so users can see which assets tend to move together and which offer diversification.

---

### 🏗️ Architecture, Caching & Reliability
1. **15-Minute Caching (`ttl=900`):** Uses `@st.cache_data(ttl=900)` on data-fetching functions so switching tabs, tickers, or timeframes stays responsive without making excessive API requests.
2. **Vectorized Calculations:** Uses Pandas rolling and percentage-change operations alongside NumPy math for fast, consistent time-series calculations.
3. **Resilient Fallbacks & Crystal Blue UI:** Styled with custom CSS in a **Crystal Blue** theme with clean layout hierarchy; validates API payloads, falls back across endpoints when needed, cleans missing `Close` rows, handles edge cases gracefully, and shows clear status messages when data is unavailable.

---

### 💡 Tech Stack
- **App & UI:** Streamlit
- **Market Data:** Yahoo Finance Chart API (`requests`)
- **Data & Math:** Pandas, NumPy
- **Visualizations:** Plotly (`plotly.express` and `plotly.graph_objects`)

### 🛠️ Installation & Local Setup:

Want to run this terminal locally on your machine? Follow these simple steps:

1. **Clone the Repository**
   ```bash
   git clone git@github.com:dhanush058/AlphaQuant.git
   cd AlphaQuant
