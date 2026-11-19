# 📈 AlphaQuant Financial Intelligence & Quantitative Risk Terminal

An interactive market intelligence and quantitative risk terminal built with Python, Pandas, NumPy, Plotly, and Streamlit to stream daily market data, compute technical and volatility indicators, and compare multi-asset performance.

Computing rolling indicators directly inside a zoomed or filtered chart window often leaves leading `NaN` gaps or distorts early trend values. AlphaQuant avoids this by ingesting a 2-year historical buffer first, calculating rolling statistics across the full series, and slicing cleanly to the selected lookback window.

🔗 **Live URL:** https://alphaquant-analytics.streamlit.app/

### 🎯 Overview & Supported Asset Universe: 
AlphaQuant supports **14 market instruments** across large-cap equities, broad market ETFs, and spot crypto pairs:
- **Equities:** `AAPL`, `MSFT`, `GOOGL`, `AMZN`, `NVDA`, `META`, `TSLA`, `AMD`, `NFLX`, `INTC`
- **Index ETFs:** `SPY`, `QQQ`
- **Crypto Pairs:** `BTC-USD`, `ETH-USD`

**Interactive Controls:**
- **Navigation Views:** Switch between *Price Action & Technicals*, *Quantitative Risk & Volatility*, *Multi-Asset Performance & Spread*, and *Analytics Guide & Overview*.
- **Timeframe Windows:** `1mo`, `3mo`, `6mo`, `1y`, and `2y`.
- **Comparison Basket:** Select **2 to 6 assets** for normalized relative performance tracking.

### 🚀 Key Capabilities & Analytical Methodology:

#### 1. Buffer-First Indicator Pipeline:
- Fetches a 2-year daily OHLCV dataset from the Yahoo Finance chart endpoint (`https://query1.finance.yahoo.com/v8/finance/chart/{ticker}`) via `requests`.
- Calculates rolling indicators across the full buffer before filtering to the active timeframe (`1mo`–`2y`) so moving averages and volatility curves stay consistent.

#### 2. Technical & Volume Analytics (*Price Action & Technicals*):
- **KPI Summary Cards:** Displays latest close price with 24-hour change, period high/low with percentage distance from peak/trough, and latest volume compared against the 20-day average volume.
- **Master Key Insights Panel:** Summarizes trend position relative to 20-day and 50-day Simple Moving Averages (`SMA_20`, `SMA_50`), 20-day volume participation, and annualized volatility / drawdown context.
- **Interactive Charts:** Plots closing price, 20D/50D SMAs, 20D Bollinger Bands ($\text{SMA}_{20} \pm 2\sigma_{20}$), and a daily volume bar chart with formatted volume tooltips (`K`, `M`, `B`).

#### 3. Quantitative Risk & Return Diagnostics (*Quantitative Risk & Volatility*):
- **Risk & Return Metrics:** Computes annualized volatility ($\text{Daily Return Std} \times \sqrt{252} \times 100$), cumulative period return, return variance against an annualized target benchmark, and daily mean return.
- **Distribution & Regime Charts:** Tracks 30-day rolling annualized volatility over time alongside a 50-bin histogram of daily percentage returns.

#### 4. Normalized Multi-Asset Comparison (*Multi-Asset Performance & Spread*):
- Aligns selected tickers (`2` to `6` assets) on shared dates and rebases prices to a common baseline (`Base = 100` using `(price / first_price) * 100`) so assets at different price levels can be compared directly.

### 🏗️ Architecture, Caching & Reliability:

1. **Ingestion & 15-Minute Caching:** Uses `@st.cache_data(ttl=900)` on data-fetching functions to reduce repeated API calls and keep tab switching responsive.
2. **Vectorized Transformations:** Uses Pandas rolling/percentage-change operations and NumPy math rather than row-by-row Python loops.
3. **Defensive Fallbacks:** Validates JSON/quote payloads, drops missing `Close` rows, handles empty DataFrames gracefully, and displays clear status/warning messages when data is unavailable.

### 💡 Technology Stack:
- **UI & App Framework:** Streamlit
- **Market Data Ingestion:** Yahoo Finance Chart REST API (`requests`)
- **Data Manipulation:** Pandas
- **Numerical Computing:** NumPy
- **Data Visualization:** Plotly (`plotly.express` and `plotly.graph_objects`)

### 🛠️ Installation & Local Setup:

Want to run this terminal locally on your machine? Follow these simple steps:

1. **Clone the Repository**
   ```bash
   git clone git@github.com:dhanush058/AlphaQuant.git
   cd AlphaQuant
