from datetime import datetime, timedelta
import random
import sqlite3
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf

# Page Configuration
st.set_page_config(
    page_title="StumpMetrics: Player Intelligence", page_icon="🏏", layout="wide"
)

# Auto-refresh live feed every 60 seconds
count = st_autorefresh(interval=60000, limit=None, key="cricket_live_feed")

# ==========================================
# CUSTOM STYLING (BLACK & NEON THEME UX)
# ==========================================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
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
    h1, h2, h3 {
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# DATABASE INITIALIZATION & SCHEMA MIGRATION
# ==========================================
def init_cricket_db():
  conn = sqlite3.connect("stump_metrics.db")
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_match_logs (
            match_id TEXT PRIMARY KEY,
            player_name TEXT,
            team TEXT,
            player_role TEXT DEFAULT 'Batter',
            opposition TEXT,
            format TEXT,
            runs_scored INTEGER,
            balls_faced INTEGER,
            fours INTEGER DEFAULT 0,
            sixes INTEGER DEFAULT 0,
            overs_bowled REAL DEFAULT 0.0,
            runs_conceded INTEGER DEFAULT 0,
            wickets_taken INTEGER DEFAULT 0,
            economy_rate REAL DEFAULT 0.0,
            performance_status TEXT,
            match_date TEXT
        )
    """)

  # Ensure all necessary columns exist for role-based analytics
  cursor.execute("PRAGMA table_info(player_match_logs)")
  existing_cols = [col[1] for col in cursor.fetchall()]
  
  migrations = [
      ("player_role", "TEXT DEFAULT 'Batter'"),
      ("fours", "INTEGER DEFAULT 0"),
      ("sixes", "INTEGER DEFAULT 0"),
      ("overs_bowled", "REAL DEFAULT 0.0"),
      ("runs_conceded", "INTEGER DEFAULT 0"),
      ("wickets_taken", "INTEGER DEFAULT 0"),
  ]
  for col_name, col_def in migrations:
    if col_name not in existing_cols:
      cursor.execute(f"ALTER TABLE player_match_logs ADD COLUMN {col_name} {col_def}")

  cursor.execute("SELECT COUNT(*) FROM player_match_logs")
  if cursor.fetchone()[0] == 0:
    # All 12 ICC Test Nations roster with role assignment
    test_nations_roster = [
        ("Virat Kohli", "India", "Batter", "ODI"),
        ("Jasprit Bumrah", "India", "Bowler", "Test"),
        ("Steve Smith", "Australia", "Batter", "Test"),
        ("Pat Cummins", "Australia", "Bowler", "Test"),
        ("Joe Root", "England", "Batter", "Test"),
        ("Ben Stokes", "England", "All-Rounder", "Test"),
        ("Babar Azam", "Pakistan", "Batter", "ODI"),
        ("Shaheen Afridi", "Pakistan", "Bowler", "T20I"),
        ("Kane Williamson", "New Zealand", "Batter", "Test"),
        ("Trent Boult", "New Zealand", "Bowler", "ODI"),
        ("Kagiso Rabada", "South Africa", "Bowler", "Test"),
        ("Shakib Al Hasan", "Bangladesh", "All-Rounder", "ODI"),
        ("Wanindu Hasaranga", "Sri Lanka", "Bowler", "T20I"),
        ("Nicholas Pooran", "West Indies", "Batter", "T20I"),
        ("Rashid Khan", "Afghanistan", "Bowler", "T20I"),
        ("Harry Tector", "Ireland", "Batter", "ODI"),
        ("Sikandar Raza", "Zimbabwe", "All-Rounder", "ODI"),
    ]

    all_teams = [
        "India", "Australia", "England", "Pakistan", "South Africa",
        "New Zealand", "Sri Lanka", "Bangladesh", "West Indies",
        "Afghanistan", "Ireland", "Zimbabwe"
    ]

    base_date = datetime.now() - timedelta(days=90)
    records = []

    for i in range(1, 300):
      m_id = f"MATCH-2026-{i:03d}"
      player, team, role, fmt = random.choice(test_nations_roster)
      opposition = random.choice([t for t in all_teams if t != team])

      if role in ["Batter", "All-Rounder"]:
        runs = random.randint(0, 140) if fmt != "Test" else random.randint(8, 210)
        balls = max(1, int(runs * random.uniform(0.65, 1.35)))
        fours = max(0, int(runs * random.uniform(0.1, 0.25) / 4))
        sixes = max(0, int(runs * random.uniform(0.02, 0.1) / 6))
      else:
        runs, balls, fours, sixes = 0, 0, 0, 0

      if role in ["Bowler", "All-Rounder"]:
        overs = round(random.uniform(2.0, 10.0), 1) if fmt != "Test" else round(random.uniform(8.0, 25.0), 1)
        runs_conc = int(overs * random.uniform(3.2, 8.5))
        wickets = random.randint(0, 5) if random.random() > 0.3 else random.randint(0, 2)
        economy = round(runs_conc / max(0.1, overs), 2)
      else:
        overs, runs_conc, wickets, economy = 0.0, 0, 0, 0.0

      # Outlier Detection Logic
      strike_rate = (runs / balls * 100) if balls > 0 else 0
      if strike_rate > 150 or runs >= 100 or wickets >= 4:
        status = "🔥 Elite Match-Winning Performance"
      elif (strike_rate < 50 and runs < 10 and role != "Bowler") or (economy > 9.5 and role != "Batter"):
        status = "⚠️ Slump / Underperformance"
      else:
        status = "✅ Stable Baseline"

      m_date = (base_date + timedelta(days=i * 0.3)).strftime("%Y-%m-%d")
      records.append((
          m_id, player, team, role, opposition, fmt, runs, balls, fours, sixes,
          overs, runs_conc, wickets, economy, status, m_date
      ))

    cursor.executemany(
        """
            INSERT OR IGNORE INTO player_match_logs 
            (match_id, player_name, team, player_role, opposition, format, runs_scored, balls_faced, fours, sixes, overs_bowled, runs_conceded, wickets_taken, economy_rate, performance_status, match_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
# DASHBOARD HEADER & PLAYER SELECTION SIDEBAR
# ==========================================
st.title("🏏 StumpMetrics: Player Intelligence & Career Analytics")
st.markdown(
    "**Role-Adaptive Data Intelligence Platform** | Deep-Dive SQL Career Logs, Role-Based Analytics (Batting/Bowling), & Performance Outliers."
)
st.markdown("---")

st.sidebar.header("👤 Player Selection")
available_players = sorted(df["player_name"].unique().tolist())
selected_player = st.sidebar.selectbox("Player Selection", available_players)

# Filter dataframe strictly for the selected player
player_df = df[df["player_name"] == selected_player]
player_team = player_df["team"].iloc[0] if not player_df.empty else "Unknown"
player_role = player_df["player_role"].iloc[0] if not player_df.empty else "Batter"

st.sidebar.markdown(f"**National Team:** {player_team}")
st.sidebar.markdown(f"**Primary Role:** `{player_role}`")
st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Global Stream Status")
st.sidebar.success("🟢 Live Broadcast Feed Synced")

# ==========================================
# DYNAMIC ROLE-BASED METRIC CARDS (KPIs)
# ==========================================
total_matches_played = len(player_df)

st.subheader(f"📊 Career Profile KPI Summary: {selected_player} ({player_team} — {player_role})")

if player_role == "Batter":
  player_runs_career = player_df["runs_scored"].sum()
  player_batting_avg = round(player_runs_career / max(1, len(player_df[player_df["runs_scored"] > 0])), 1)
  player_strike_rate = round((player_runs_career / max(1, player_df["balls_faced"].sum())) * 100, 1)
  centuries_count = len(player_df[player_df["runs_scored"] >= 100])

  c1, c2, c3, c4, c5 = st.columns(5)
  c1.metric("Matches Logged", f"{total_matches_played}")
  c2.metric("Total Career Runs", f"{player_runs_career:,}")
  c3.metric("Batting Average", f"{player_batting_avg}")
  c4.metric("Career Strike Rate", f"{player_strike_rate}%")
  c5.metric("Centuries (100s)", f"{centuries_count}")

elif player_role == "Bowler":
  total_wickets = player_df["wickets_taken"].sum()
  total_overs = player_df["overs_bowled"].sum()
  total_runs_conceded = player_df["runs_conceded"].sum()
  bowling_avg = round(total_runs_conceded / max(1, total_wickets), 2)
  career_economy = round(total_runs_conceded / max(0.1, total_overs), 2)
  five_wkt_hauls = len(player_df[player_df["wickets_taken"] >= 5])

  c1, c2, c3, c4, c5 = st.columns(5)
  c1.metric("Matches Logged", f"{total_matches_played}")
  c2.metric("Total Wickets Scalped", f"{total_wickets}")
  c3.metric("Bowling Average", f"{bowling_avg}")
  c4.metric("Economy Rate", f"{career_economy}")
  c5.metric("5-Wicket Hauls", f"{five_wkt_hauls}")

else:  # All-Rounder
  player_runs_career = player_df["runs_scored"].sum()
  total_wickets = player_df["wickets_taken"].sum()
  player_batting_avg = round(player_runs_career / max(1, len(player_df[player_df["runs_scored"] > 0])), 1)
  total_overs = player_df["overs_bowled"].sum()
  total_runs_conceded = player_df["runs_conceded"].sum()
  career_economy = round(total_runs_conceded / max(0.1, total_overs), 2)

  c1, c2, c3, c4, c5 = st.columns(5)
  c1.metric("Matches Logged", f"{total_matches_played}")
  c2.metric("Career Runs", f"{player_runs_career:,}")
  c3.metric("Batting Average", f"{player_batting_avg}")
  c4.metric("Total Wickets", f"{total_wickets}")
  c5.metric("Economy Rate", f"{career_economy}")

st.markdown("---")

# ==========================================
# PLAYER ANALYTICAL TABS
# ==========================================
tab_logs, tab_trends, tab_oppo, tab_ingest = st.tabs([
    "📋 Player Match Log History",
    "📈 Performance & Form Trends",
    "🎯 Opposition Analysis",
    "⚡ Add Match Scorecard",
])

with tab_logs:
  st.subheader(f"SQL Match Database — {selected_player}")
  st.markdown("Filterable record breakdown showing performance indicators adapted to player role.")

  f_format = st.selectbox("Filter Match Format", ["All Formats", "Test", "ODI", "T20I"], key="fmt_filter")
  filtered_logs = player_df.copy()
  if f_format != "All Formats":
    filtered_logs = filtered_logs[filtered_logs["format"] == f_format]

  if player_role == "Batter":
    cols = ["match_date", "format", "opposition", "runs_scored", "balls_faced", "fours", "sixes", "performance_status"]
  elif player_role == "Bowler":
    cols = ["match_date", "format", "opposition", "overs_bowled", "runs_conceded", "wickets_taken", "economy_rate", "performance_status"]
  else:
    cols = ["match_date", "format", "opposition", "runs_scored", "wickets_taken", "economy_rate", "performance_status"]

  st.dataframe(filtered_logs[cols].sort_values(by="match_date", ascending=False), use_container_width=True)

with tab_trends:
  st.subheader(f"Form & Outlier Tracking — {selected_player}")

  if not player_df.empty:
    if player_role == "Batter":
      st.markdown("### Batting Scoring Trend (Runs Scored per Match)")
      chart_data = player_df.set_index("match_date")["runs_scored"]
      st.line_chart(chart_data)
    elif player_role == "Bowler":
      st.markdown("### Bowling Impact Trend (Wickets Taken per Match)")
      chart_data = player_df.set_index("match_date")["wickets_taken"]
      st.bar_chart(chart_data)
    else:
      st.markdown("### Dual Impact Trend (Runs & Wickets)")
      st.line_chart(player_df.set_index("match_date")[["runs_scored", "wickets_taken"]])

    st.markdown("### 🔥 Highlighted Standout Innings")
    outliers = player_df[player_df["performance_status"] == "🔥 Elite Match-Winning Performance"]
    if not outliers.empty:
      st.dataframe(outliers, use_container_width=True)
    else:
      st.info("No standout elite performances flagged in the current window.")

with tab_oppo:
  st.subheader("Opposition Breakdown")

  if not player_df.empty:
    if player_role == "Batter":
      oppo_agg = player_df.groupby("opposition").agg(
          Matches=("match_id", "count"),
          Total_Runs=("runs_scored", "sum"),
          Avg_Runs=("runs_scored", "mean")
      ).reset_index()
      oppo_agg["Avg_Runs"] = oppo_agg["Avg_Runs"].round(1)
    elif player_role == "Bowler":
      oppo_agg = player_df.groupby("opposition").agg(
          Matches=("match_id", "count"),
          Total_Wickets=("wickets_taken", "sum"),
          Avg_Economy=("economy_rate", "mean")
      ).reset_index()
      oppo_agg["Avg_Economy"] = oppo_agg["Avg_Economy"].round(2)
    else:
      oppo_agg = player_df.groupby("opposition").agg(
          Matches=("match_id", "count"),
          Total_Runs=("runs_scored", "sum"),
          Total_Wickets=("wickets_taken", "sum")
      ).reset_index()

    st.dataframe(oppo_agg, use_container_width=True)

with tab_ingest:
  st.subheader(f"Commit New Scorecard for {selected_player}")

  with st.form("player_match_form"):
    col_a, col_b = st.columns(2)
    with col_a:
      opp_team = st.text_input("Opposition Nation", "Australia")
      match_fmt = st.selectbox("Format", ["ODI", "T20I", "Test"])
      p_role = st.selectbox("Player Role Override", ["Batter", "Bowler", "All-Rounder"], index=["Batter", "Bowler", "All-Rounder"].index(player_role))
    with col_b:
      runs = st.number_input("Runs Scored", min_value=0, max_value=300, value=65 if player_role != "Bowler" else 5)
      balls = st.number_input("Balls Faced", min_value=0, max_value=350, value=50 if player_role != "Bowler" else 8)
      overs = st.number_input("Overs Bowled", min_value=0.0, max_value=50.0, value=10.0 if player_role != "Batter" else 0.0)
      wickets = st.number_input("Wickets Taken", min_value=0, max_value=10, value=3 if player_role != "Batter" else 0)

    submit_btn = st.form_submit_button("Commit Inning to SQL Database")

    if submit_btn:
      new_id = f"MATCH-2026-{random.randint(5009,9999)}"
      sr = (runs / balls * 100) if balls > 0 else 0
      status = "🔥 Elite Match-Winning Performance" if sr > 150 or runs >= 100 or wickets >= 4 else "✅ Stable Baseline"
      econ = round(random.uniform(4.0, 7.0), 2) if overs > 0 else 0.0

      conn = sqlite3.connect("stump_metrics.db")
      cur = conn.cursor()
      cur.execute(
          """
            INSERT INTO player_match_logs 
            (match_id, player_name, team, player_role, opposition, format, runs_scored, balls_faced, fours, sixes, overs_bowled, runs_conceded, wickets_taken, economy_rate, performance_status, match_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 4, 1, ?, ?, ?, ?, ?, ?)
          """,
          (new_id, selected_player, player_team, p_role, opp_team, match_fmt, runs, balls, overs, int(overs * econ), wickets, econ, status, datetime.now().strftime("%Y-%m-%d"))
      )
      conn.commit()
      conn.close()
      st.success(f"Successfully recorded match log for {selected_player}!")
      st.rerun()