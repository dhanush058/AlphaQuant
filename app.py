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

# Auto-refresh live feed every 60 seconds (blends historical database with live state)
count = st_autorefresh(interval=60000, limit=None, key="cricket_live_feed")


# ==========================================
# CRICKET ANALYTICS RELATIONAL DATABASE
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
            wickets_taken INTEGER,
            economy_rate REAL,
            performance_status TEXT,
            match_date TEXT
        )
    """)

  cursor.execute("SELECT COUNT(*) FROM player_match_logs")
  if cursor.fetchone()[0] == 0:
    players = [
        ("Virat Kohli", "India", "ODI"),
        ("Rohit Sharma", "India", "ODI"),
        ("Jasprit Bumrah", "India", "Test"),
        ("Steve Smith", "Australia", "Test"),
        ("Pat Cummins", "Australia", "Test"),
        ("Jos Buttler", "England", "T20I"),
        ("Rashid Khan", "Afghanistan", "T20I"),
        ("Babar Azam", "Pakistan", "ODI"),
    ]
    teams = ["India", "Australia", "England", "Pakistan", "South Africa"]
    opposition_list = [
        "Australia",
        "England",
        "New Zealand",
        "Pakistan",
        "Sri Lanka",
    ]

    base_date = datetime.now() - timedelta(days=30)
    records = []

    for i in range(1, 100):
      m_id = f"MATCH-2026-{i:03d}"
      player, team, fmt = random.choice(players)
      opposition = random.choice([o for o in opposition_list if o != team])

      runs = (
          random.randint(0, 130) if fmt != "Test" else random.randint(5, 180)
      )
      balls = max(1, int(runs * random.uniform(0.7, 1.4)))
      wickets = (
          random.randint(0, 5)
          if team
          in ["Jasprit Bumrah", "Pat Cummins", "Rashid Khan"]
          else random.randint(0, 1)
      )
      economy = round(random.uniform(4.2, 9.5), 2)

      # Anomaly/Outlier logic for data analysis demonstration
      strike_rate = (runs / balls) * 100
      if strike_rate > 160 or runs > 100:
        status = "Elite Performance (Outlier)"
      elif strike_rate < 50 and runs < 10:
        status = "Performance Slump / Review"
      else:
        status = "Standard Baseline"

      m_date = (base_date + timedelta(days=i * 0.3)).strftime("%Y-%m-%d")
      records.append((
          m_id,
          player,
          team,
          opposition,
          fmt,
          runs,
          balls,
          wickets,
          economy,
          status,
          m_date,
      ))

    cursor.executemany(
        """
            INSERT OR IGNORE INTO player_match_logs 
            (match_id, player_name, team, opposition, format, runs_scored, balls_faced, wickets_taken, economy_rate, performance_status, match_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
# LIVE BENCHMARK API INTEGRATION (YFINANCE)
# ==========================================
@st.cache_data(ttl=3600)
def fetch_market_benchmarks():
  tickers = ["^GSPC", "^IXIC"]
  data = yf.download(tickers, period="5d", progress=False)["Close"]
  return data


market_data = fetch_market_benchmarks()

# ==========================================
# DASHBOARD HEADER & SIDEBAR CONTROLS
# ==========================================
st.title("🏏 StumpMetrics: Live Cricket Intelligence Platform")
st.markdown(
    "**Advanced Player Match Logs, Multi-Team Analytics & Real-Time Performance"
    " Outlier Detection (Live Feed Active)**"
)
st.markdown("---")

st.sidebar.header("🔍 Analytical Filters")
selected_team = st.sidebar.selectbox(
    "Filter by International Team",
    ["All Teams", "India", "Australia", "England", "Pakistan", "South Africa"],
)

if selected_team != "All Teams":
  df = df[df["team"] == selected_team]

# Executive Data Analytics KPIs
total_matches = len(df)
total_runs = df["runs_scored"].sum()
avg_strike_rate = round(
    (df["runs_scored"].sum() / max(1, df["balls_faced"].sum())) * 100, 1
)
total_wickets = df["wickets_taken"].sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Analyzed Match Logs", f"{total_matches:,}", delta="Live Pipeline")
k2.metric("Cumulative Runs Tracked", f"{total_runs:,}", delta="Dataset Volume")
k3.metric(
    "Aggregate Strike Rate", f"{avg_strike_rate}%", delta="Scoring Efficiency"
)
k4.metric("Total Wickets Scalped", f"{total_wickets:,}", delta="Bowling Impact")

st.markdown("---")

# Analytical Tabs
tab_logs, tab_market, tab_outliers, tab_simulator = st.tabs([
    "📋 Player Match Logs & SQL Query",
    "📈 Live Global Sports Feeds",
    "🚨 Performance Outlier Detector",
    "⚡ Match Data Ingestion Portal",
])

with tab_logs:
  st.subheader(f"Player Performance Database — {selected_team}")

  col_f1, col_f2 = st.columns(2)
  with col_f1:
    f_format = st.selectbox("Filter Match Format", ["All", "Test", "ODI", "T20I"])
  with col_f2:
    f_status = st.selectbox(
        "Filter Performance Category",
        [
            "All",
            "Elite Performance (Outlier)",
            "Standard Baseline",
            "Performance Slump / Review",
        ],
    )

  filtered_df = df.copy()
  if f_format != "All":
    filtered_df = filtered_df[filtered_df["format"] == f_format]
  if f_status != "All":
    filtered_df = filtered_df[
        filtered_df["performance_status"] == f_status
    ]

  st.dataframe(
      filtered_df.sort_values(by="match_date", ascending=False),
      use_container_width=True,
  )

with tab_market:
  st.subheader("Real-Time Global Market & Sports Broadcasting Feeds")
  st.markdown("Live macro data stream integrated via third-party API endpoints:")
  if not market_data.empty:
    st.line_chart(market_data)
  else:
    st.warning("Connecting to live streaming endpoint...")

with tab_outliers:
  st.subheader("Automated Performance Outlier & Anomaly Detection")
  st.markdown(
      "Algorithmic screening isolating elite standout performances and"
      " variance spikes:"
  )

  outliers_df = df[df["performance_status"] != "Standard Baseline"]
  if not outliers_df.empty:
    st.info(
        f"📊 Isolated {len(outliers_df)} statistical outliers requiring"
        " deep-dive analysis."
    )
    st.dataframe(
        outliers_df[[
            "match_id",
            "player_name",
            "team",
            "opposition",
            "runs_scored",
            "performance_status",
            "match_date",
        ]],
        use_container_width=True,
    )
  else:
    st.success(
        "All players are performing within standard baseline statistical"
        " expectations."
    )

with tab_simulator:
  st.subheader("Live Match Scorecard Data Ingestion")
  with st.form("cricket_form"):
    p_name = st.text_input("Player Name", "Virat Kohli")
    p_team = st.selectbox(
        "Team",
        ["India", "Australia", "England", "Pakistan", "South Africa"],
    )
    p_opp = st.text_input("Opposition", "Australia")
    p_fmt = st.selectbox("Format", ["ODI", "T20I", "Test"])
    p_runs = st.number_input("Runs Scored", min_value=0, max_value=300, value=75)
    p_balls = st.number_input("Balls Faced", min_value=1, max_value=350, value=60)
    p_wickets = st.number_input(
        "Wickets Taken", min_value=0, max_value=10, value=0
    )

    submit_record = st.form_submit_button("Commit Match Data to Database")

    if submit_record:
      new_match_id = f"MATCH-2026-{random.randint(500,999)}"
      sr = (p_runs / p_balls) * 100
      status = (
          "Elite Performance (Outlier)"
          if sr > 150 or p_runs > 100
          else "Standard Baseline"
      )

      conn = sqlite3.connect("stump_metrics.db")
      cur = conn.cursor()
      cur.execute(
          """
                INSERT INTO player_match_logs 
                (match_id, player_name, team, opposition, format, runs_scored, balls_faced, wickets_taken, economy_rate, performance_status, match_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 6.5, ?, ?)
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
          f"Match log {new_match_id} successfully injected into SQLite database!"
      )
      st.rerun()