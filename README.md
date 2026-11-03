# 📈 AlphaQuant Financial Intelligence & Quantitative Risk Terminal

An enterprise-grade financial analytics and risk terminal designed to stream live market data, calculate automated risk metrics, and visualize multi-asset intelligence across an executive-grade interface.

This tool solves a common headache in data analysis: when you calculate trends over time (like a 30-day average), traditional apps often leave annoying blank spaces or errors at the start of your chart. AlphaQuant fixes this by pulling a full historical buffer under the hood, running all calculations completely first, and then letting you zoom into any timeframe smoothly without breaking the math.

🔗 **Live Production Deployment URL:** https://github.com/dhanush058/AlphaQuant

### 🚀 Business Impact & Professional Analytics Metrics

- **Data Architecture & Error Elimination:** Solved missing data gaps in charts by engineering a two-stage pipeline—processing historical calculations across a full 2-year buffer *before* letting users filter or zoom into specific timeframes.
  
- **Advanced Risk Tracking:** Built automated volatility tracking that measures how wildly a stock or asset is swinging over a rolling 30-day window, helping spot sudden market risks and calm periods instantly.
  
- **Apples-to-Apples Comparisons:** Created a normalization engine that sets different assets to a shared starting point ($100$), making it easy to compare a high-priced stock against a lower-priced index on the exact same chart.

### 🏗️ How It Works (System Architecture & Pipeline)

**Pipeline Workflow:** 

1. **Live Data Ingestion**: Automatically pulls fresh daily closing prices directly from financial APIs, using smart local caching to keep the app fast and responsive.
   
2. **Behind-the-Scenes Math**: Calculates moving averages, price trends, and risk percentages across the entire history buffer before any user clicks a filter.

3. **Dynamic View Slicing**: Instantly updates the charts when you select different time views (like 1 Month, 6 Months, or 1 Year) without losing any mathematical accuracy.

4. **Multi-Module Layout**: Displays clean, professional dashboards categorized so anyone can scan insights in seconds.

### 📊 Analytical Visualization Framework

The dashboard features clear, interactive charts designed to help you analyze market behavior at a glance:

- **Price Action & Technicals:** Displays price trends alongside helpful guidelines (like moving averages and volatility boundaries) to spot general market direction and key turning points.

- **Quantitative Risk & Volatility:** Tracks continuous market risk over time so you can see when an asset is stabilizing or experiencing high turbulence.

- **Multi-Asset Performance & Spread:** Puts multiple stocks or market indexes side-by-side on a unified percentage scale to see which ones are outperforming.

### 💡 Technology Stack

- **Dashboard Application Interface:** Streamlit (Python Web Framework)

- **Data Sourcing Engine:** Yahoo Finance REST API (`yfinance`)

- **Numerical Calculations:** NumPy (Matrix & Mathematical Operations)

- **Data Processing:** Pandas (Structured Data Tables & Transformation)

- **Visualizations:** Plotly (Interactive Charts & Graphs)

### 🛠️ Installation & Local Setup

Want to run this terminal locally on your machine? Follow these simple steps:

1. **Clone the Repository**
   ```bash
   git clone git@github.com:dhanush058/AlphaQuant.git
   cd AlphaQuant
