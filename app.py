from datetime import datetime, timedelta
import random
import sqlite3
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf

# Page Configuration
st.set_page_config(
    page_title="StumpMetrics: Cricket Intelligence", page_icon="🏏", layout="wide"
)

# Auto-refresh live feed every 60 seconds
count = st_autorefresh(interval=60000, limit=None, key="cricket_live_feed")

# ==========================================
# CUSTOM STYLING (BLACK & NEON THEME UX)
# ==========================================
st.markdown(
    """
    <style>
    /* Global Dark Theme Background */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Metric Cards Styling with Neon Glow */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        border: 1px solid #374151;
        padding: 16px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0, 245, 255, 0.05);
    }
    div[data-testid="stMetric"]:hover {
        border-color: #00f5ff;
        box-shadow: 0 0 15px rgba(0, 245, 255, 0.2);
    }
    div[data-testid="stMetric"] label {
        color: #9ca3af !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #00f5ff !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #111827;
        padding: 10px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1f2937;
        color: #d1d5db;
        border-radius: 6px;
        padding: 10px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00f5ff 0%, #3b82f6 100%) !important;
        color: #0b0f19 !important;
    }

    /* Headers */
    h1, h2, h3 {
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# CRICKET ANALYTICS RELATIONAL DATABASE (ALL TEST NATIONS)
# ==========================================
def init_cricket_db():
  conn = sqlite3.connect("stump_metrics.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_match_logs (
            match_id TEXT,
            player_name TEXT,
            team TEXT,
            opposition TEXT,
            format TEXT,
            runs_scored INTEGER,
            balls_faced INTEGER,
            fours INTEGER,
            sixes INTEGER,
            wickets_taken INTEGER,
            economy_rate REAL,
            performance_status TEXT,
            match_date TEXT
        )
    """)

  cursor.execute("SELECT COUNT(*) FROM player_match_logs")
  if cursor.fetchone()[0] == 0:
    # All 12 ICC Test Playing Nations represented
    test_nations = [
        ("Virat Kohli", "India", "ODI"),
        ("Kane Williamson", "New Zealand", "Test"),
        ("Joe Root", "England", "Test"),
        ("Babar Azam", "Pakistan", "ODI"),
        ("Steve Smith", "Australia", "Test"),
        ("Temba Bavuma", "South Africa", "Test"),
        ("Shakib Al Hasan", "Bangladesh", "T20I"),
        ("Angelo Mathews", "Sri Lanka", "Test"),
        ("Nicholas Pooran", "West Indies", "T20I"),
        ("Rashid Khan", "Afghanistan", "T20I"),
        ("Harry Tector", "Ireland", "ODI"),
        ("Craig Ervine", "Zimbabwe", "ODI"),
        ("Jasprit Bumrah", "India", "Test"),
        ("Pat Cummins", "Australia", "Test"),
        ("Shaheen Afridi", "Pakistan", "T20I"),
        ("Trent Boult", "New Zealand", "ODI"),
    ]

    all_teams = [
        "India",
        "Australia",
        "England",
        "Pakistan",
        "South Africa",
        "New Zealand",
        "Sri Lanka",
        "Bangladesh",
        "West Indies",
        "Afghanistan",
        "Ireland",
        "Zimbabwe",
    ]

    base_date = datetime.now() - timedelta(days=45)
    records = []

    for i in range(1, 150):
      m_id = f"MATCH-2026-{i:03d}"
      player, team, fmt = random.choice(test_nations)
      opposition = random.choice([t for t in all_teams if t != team])

      runs = (
          random.randint(0, 140) if fmt != "Test" else random.randint(10, 210)
      )
      balls = max(1, int(runs * random.uniform(0.65, 1.35)))
      fours = max(0, int(runs * random.uniform(0.1, 0.25) / 4))
      sixes = max(0, int(runs * random.uniform(0.02, 0.1) / 6))
      wickets = (
          random.randint(0, 5)
          if "Bumrah" in player
          or "Cummins" in player
          or "Afridi" in player
          or "Boult" in player
          else random.randint(0, 2)
      )
      economy = round(random.uniform(3.8, 8.9), 2)

      # Data Analysis Outlier / Performance Logic
      strike_rate = (runs / balls) * 100
      if strike_rate > 150 or runs > 100:
        status = "🔥 Elite Outlier (Match Winner)"
      elif strike_rate < 50 and runs < 12:
        status = "⚠️ Performance Slump (Review)"
      else:
        status = "✅ Baseline Standard"

      m_date = (base_date + timedelta(days=i * 0.3)).strftime("%Y-%m-%d")
      records.append((
          m_id,
          player,
          team,
          opposition,
          fmt,
          runs,
          balls,
          fours,
          sixes,
          wickets,
          economy,
          status,
          m_date,
      ))

    cursor.executemany(
        """
            INSERT OR IGNORE INTO player_match_logs 
            (match_id, player_name, team, opposition, format, runs_scored, balls_faced, fours, sixes, wickets_taken, economy_rate, performance_status, match_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

  conn.commit()
  conn.close()


init_cricket_db()


def load_cricket_data():
  conn = sqlite3.connect("stump_metrics.db")
  df = pd.read_sql_query("SELECT * FROM player_match_logs", conn)
  conn.close()
  df["match_date"] = pd.to_datetime(df["match_date"])
  return df


df = load_cricket_data()


# ==========================================
# LIVE BROADCAST & STREAMING API (YFINANCE)
# ==========================================
@st.cache_data(ttl=3600)
def fetch_live_market_stream():
  tickers = ["^GSPC", "^IXIC"]
  data = yf.download(tickers, period="5d", progress=False)["Close"]
  return data


market_data = fetch_live_market_stream()

# ==========================================
# DASHBOARD HEADER & SIDEBAR CONTROLS
# ==========================================
st.title("🏏 StumpMetrics: Cricket Analytics & Intelligence Suite")
st.markdown(
    "**End-to-End Data Analyst Portfolio Project** | Relational SQL Database,"
    " Multi-Nation Filtering, Boundary Efficiency Index & Automated Outlier"
    " Detection."
)
st.markdown("---")

st.sidebar.header("🌐 Global Filters")
all_test_nations = [
    "All Test Nations",
    "India",
    "Australia",
    "England",
    "Pakistan",
    "South Africa",
    "New Zealand",
    "Sri Lanka",
    "Bangladesh",
    "West Indies",
    "Afghanistan",
    "Ireland",
    "Zimbabwe",
]
selected_team = st.sidebar.selectbox("Filter by National Team", all_test_nations)

if selected_team != "All Test Nations":
  df = df[df["team"] == selected_team]

# True Cricket Analytics KPI Cards
total_innings = len(df)
total_runs_scored = df["runs_scored"].sum()
overall_strike_rate = round(
    (df["runs_scored"].sum() / max(1, df["balls_faced"].sum())) * 100, 1
)
total_boundaries = (df["fours"] * 4 + df["sixes"] * 6).sum()
boundary_percentage = (
    round((total_boundaries / max(1, total_runs_scored)) * 100, 1)
    if total_runs_scored > 0
    else 0
)

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Match Logs Analyzed",
    f"{total_innings:,}",
    delta="Relational SQL Records",
)
k2.metric(
    "Cumulative Runs Logged",
    f"{total_runs_scored:,}",
    delta="Dataset Volume",
)
k3.metric(
    "Aggregate Strike Rate",
    f"{overall_strike_rate}%",
    delta="Scoring Efficiency",
)
k4.metric(
    "Boundary Contribution",
    f"{boundary_percentage}%",
    delta="Power Hit Index",
)

st.markdown("---")

# Professional Analytical Tabs
tab_sql, tab_outliers, tab_live, tab_ingest = st.tabs([
    "📋 SQL Player Database & Match Logs",
    "🚨 Performance Outlier & Anomaly Detection",
    "📈 Live Global Broadcast Feeds",
    "⚡ Real-Time Match Data Ingestion",
])

with tab_sql:
  st.subheader(
      f"Relational Database Records — {selected_team}"
  )
  st.markdown(
      "Querying live match logs filtered by international formats and"
      " performance classifications."
  )

  col_f1, col_f2 = st.columns(2)
  with col_f1:
    f_format = st.selectbox(
        "Filter Format", ["All Formats", "Test", "ODI", "T20I"]
    )
  with col_f2:
    f_status = st.selectbox(
        "Filter Performance Tier", ["All Tiers", "🔥 Elite Outlier (Match Winner)", "✅ Baseline Standard", "⚠️ Performance Slump (Review)"]
    )

  filtered_df = df.copy()
  if f_format != "All Formats":
    filtered_df = filtered_df[filtered_df["format"] == f_format]
  if f_status != "All Tiers":
    filtered_df = filtered_df[filtered_df["performance_status"] == f_status]

  st.dataframe(
      filtered_df.sort_values(by="match_date", ascending=False),
      use_container_width=True,
  )

with tab_outliers:
  st.subheader("Automated Statistical Outlier & Anomaly Detection Engine")
  st.markdown(
      "Isolating elite batting performances (>100 runs or >150 strike rate) and"
      " performance slumps using automated data rules."
  )

  outliers_df = df[df["performance_status"] != "✅ Baseline Standard"]
  if not outliers_df.empty:
    st.info(
        f"📊 Detected {len(outliers_df)} statistical anomalies requiring"
        " tactical review."
    )
    st.dataframe(
        outliers_df[[
            "match_id",
            "player_name",
            "team",
            "opposition",
            "runs_scored",
            "balls_faced",
            "performance_status",
            "match_date",
        ]],
        use_container_width=True,
    )
  else:
    st.success("All players are performing within normal baseline variance.")

with tab_live:
  st.subheader("Real-Time External Data Feed & Stream Integration")
  st.markdown(
      "Live capital/broadcast benchmark stream simulating low-latency API"
      " synchronization:"
  )
  if not market_data.empty:
    st.line_chart(market_data)
  else:
    st.warning("Establishing secure connection to live API stream...")

with tab_ingest:
  st.subheader("Interactive Match Scorecard Ingestion Portal")
  st.markdown(
      "Simulate real-time data entry to instantly update the local SQLite"
      " database and recalculate KPIs."
  )

  with st.form("cricket_form"):
    col_i1, col_i2 = st.columns(2)
    with col_i1:
      p_name = st.text_input("Player Name", "Virat Kohli")
      p_team = st.selectbox("National Team", all_test_nations[1:])
      p_opp = st.text_input("Opposition Team", "Australia")
      p_fmt = st.selectbox("Match Format", ["ODI", "T20I", "Test"])
    with col_i2:
      p_runs = st.number_input(
          "Runs Scored", min_value=0, max_value=300, value=85
      )
      p_balls = st.number_input(
          "Balls Faced", min_value=1, max_value=350, value=65
      )
      p_wickets = st.number_input(
          "Wickets Taken", min_value=0, max_value=10, value=0
      )

    submit_record = st.form_submit_button("Commit Scorecard to SQL Database")

    if submit_record:
      new_match_id = f"MATCH-2026-{random.randint(500,999)}"
      sr = (p_runs / p_balls) * 100
      status = (
          "🔥 Elite Outlier (Match Winner)"
          if sr > 150 or p_runs > 100
          else "✅ Baseline Standard"
      )

      conn = sqlite3.connect("stump_metrics.db")
      cur = conn.cursor()
      cur.execute(
          """
                INSERT INTO player_match_logs 
                (match_id, player_name, team, opposition, format, runs_scored, balls_faced, fours, sixes, wickets_taken, economy_rate, performance_status, match_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, 8, 3, ?, 6.5, ?, ?)
            """,
          (
              new_match_id,
              p_name,
              p_team,
              p_opp,
              p_fmt,
              p_runs,
              p_balls,
              p_wickets,
              status,
              datetime.now().strftime("%Y-%m-%d"),
          ),
      )
      conn.commit()
      conn.close()
      st.success(
          f"Successfully committed match {new_match_id} to the SQLite database!"
      )
      st.rerun()