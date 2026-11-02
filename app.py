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
# DATABASE INITIALIZATION & AUTO-MIGRATION
# ==========================================
def init_cricket_db():
  conn = sqlite3.connect("stump_metrics.db")
  cursor = conn.cursor()
  
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_match_logs (
            match_id TEXT PRIMARY KEY,
            player_name TEXT,
            team TEXT,
            opposition TEXT,
            format TEXT,
            runs_scored INTEGER,
            balls_faced INTEGER,
            fours INTEGER DEFAULT 0,
            sixes INTEGER DEFAULT 0,
            wickets_taken INTEGER,
            economy_rate REAL,
            performance_status TEXT,
            match_date TEXT
        )
    """)

  cursor.execute("PRAGMA table_info(player_match_logs)")
  existing_cols = [col[1] for col in cursor.fetchall()]
  if "fours" not in existing_cols:
    cursor.execute("ALTER TABLE player_match_logs ADD COLUMN fours INTEGER DEFAULT 0")
  if "sixes" not in existing_cols:
    cursor.execute("ALTER TABLE player_match_logs ADD COLUMN sixes INTEGER DEFAULT 0")

  cursor.execute("SELECT COUNT(*) FROM player_match_logs")
  if cursor.fetchone()[0] == 0:
    test_nations_roster = [
        ("Virat Kohli", "India", "ODI"),
        ("Kane Williamson", "New Zealand", "Test"),
        ("Joe Root", "England", "Test"),
        ("Babar Azam", "Pakistan", "ODI"),
        ("Steve Smith", "Australia", "Test"),
        ("Shakib Al Hasan", "Bangladesh", "T20I"),
        ("Jasprit Bumrah", "India", "Test"),
        ("Rashid Khan", "Afghanistan", "T20I"),
    ]

    all_teams = ["India", "Australia", "England", "Pakistan", "New Zealand", "Bangladesh", "South Africa", "Afghanistan"]
    base_date = datetime.now() - timedelta(days=60)
    records = []

    for i in range(1, 160):
      m_id = f"MATCH-2026-{i:03d}"
      player, team, fmt = random.choice(test_nations_roster)
      opposition = random.choice([t for t in all_teams if t != team])

      runs = random.randint(0, 140) if fmt != "Test" else random.randint(12, 215)
      balls = max(1, int(runs * random.uniform(0.65, 1.35)))
      fours = max(0, int(runs * random.uniform(0.1, 0.25) / 4))
      sixes = max(0, int(runs * random.uniform(0.02, 0.1) / 6))
      wickets = random.randint(0, 5) if "Bumrah" in player or "Rashid" in player else random.randint(0, 2)
      economy = round(random.uniform(3.8, 8.9), 2)

      strike_rate = (runs / balls) * 100
      if strike_rate > 150 or runs > 100:
        status = "🔥 Elite Match-Winning Knock"
      elif strike_rate < 50 and runs < 10:
        status = "⚠️ Slump / Low Conversion"
      else:
        status = "✅ Stable Baseline"

      m_date = (base_date + timedelta(days=i * 0.4)).strftime("%Y-%m-%d")
      records.append((m_id, player, team, opposition, fmt, runs, balls, fours, sixes, wickets, economy, status, m_date))

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
# DASHBOARD HEADER & PLAYER-CENTRIC SIDEBAR
# ==========================================
st.title("🏏 StumpMetrics: Player Intelligence & Career Analytics")
st.markdown(
    "**Player-Centric Data Intelligence Platform** | Deep-Dive SQL Career Logs, Individual Form Tracking, & Performance Outliers."
)
st.markdown("---")

st.sidebar.header("👤 Player Profile Selector")
available_players = sorted(df["player_name"].unique().tolist())
selected_player = st.sidebar.selectbox("Select SuperStar Player", available_players)

# Filter dataframe strictly for the selected player
player_df = df[df["player_name"] == selected_player]
player_team = player_df["team"].iloc[0] if not player_df.empty else "Unknown"

st.sidebar.markdown(f"**National Team:** {player_team}")
st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Global Stream Status")
st.sidebar.success("🟢 Live Broadcast Feed Synced")

# ==========================================
# PLAYER-CENTRIC METRIC CARDS (KPIs)
# ==========================================
total_matches_played = len(player_df)
player_runs_career = player_df["runs_scored"].sum()
player_batting_avg = round(player_runs_career / max(1, len(player_df[player_df["runs_scored"] > 0])), 1)
player_strike_rate = round((player_runs_career / max(1, player_df["balls_faced"].sum())) * 100, 1)
centuries_count = len(player_df[player_df["runs_scored"] >= 100])

st.subheader(f"📊 Career Profile KPI Summary: {selected_player} ({player_team})")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Matches Analyzed", f"{total_matches_played}")
c2.metric("Total Career Runs", f"{player_runs_career:,}")
c3.metric("Est. Batting Avg", f"{player_batting_avg}")
c4.metric("Career Strike Rate", f"{player_strike_rate}%")
c5.metric("Centuries (100s)", f"{centuries_count}")

st.markdown("---")

# ==========================================
# PLAYER ANALYTICAL TABS
# ==========================================
tab_logs, tab_trends, tab_oppo, tab_ingest = st.tabs([
    "📋 Player Match Log History",
    "📈 Performance & Form Trends",
    "🎯 Head-to-Head Opposition Analysis",
    "⚡ Add New Match Scorecard",
])

with tab_logs:
  st.subheader(f"SQL Match History for {selected_player}")
  st.markdown("Complete breakdown of individual innings, balls faced, boundary counts, and status classifications.")

  f_format = st.selectbox("Filter Format", ["All Formats", "Test", "ODI", "T20I"], key="fmt_filter")
  filtered_logs = player_df.copy()
  if f_format != "All Formats":
    filtered_logs = filtered_logs[filtered_logs["format"] == f_format]

  st.dataframe(
      filtered_logs[["match_date", "format", "opposition", "runs_scored", "balls_faced", "fours", "sixes", "performance_status"]].sort_values(by="match_date", ascending=False),
      use_container_width=True,
  )

with tab_trends:
  st.subheader(f"Scoring Trend & Outlier Analysis: {selected_player}")
  st.markdown("Visualizing match-by-match run progression and isolating career peak innings.")

  if not player_df.empty:
    chart_data = player_df.set_index("match_date")["runs_scored"]
    st.line_chart(chart_data)
    
    st.markdown("### 🔥 Highlighted Elite Innings")
    elites = player_df[player_df["runs_scored"] >= 80]
    if not elites.empty:
      st.dataframe(elites[["match_date", "format", "opposition", "runs_scored", "balls_faced", "performance_status"]], use_container_width=True)
    else:
      st.info("No standout elite knocks >80 runs recorded in current window.")
  else:
    st.warning("No data available for this player.")

with tab_oppo:
  st.subheader(f"Opposition Performance Breakdown")
  st.markdown("Aggregating runs scored and average output against different bowling nations.")

  if not player_df.empty:
    oppo_agg = player_df.groupby("opposition").agg(
        Matches=("match_id", "count"),
        Total_Runs=("runs_scored", "sum"),
        Avg_Runs=("runs_scored", "mean")
    ).reset_index()
    oppo_agg["Avg_Runs"] = oppo_agg["Avg_Runs"].round(1)
    st.dataframe(oppo_agg, use_container_width=True)
  else:
    st.info("Insufficient data for aggregation.")

with tab_ingest:
  st.subheader(f"Log a New Match Inning for {selected_player}")
  st.markdown("Instantly push a new match record into the SQLite database to update this player's stats.")

  with st.form("player_match_form"):
    col_a, col_b = st.columns(2)
    with col_a:
      opp_team = st.text_input("Opposition Nation", "Australia")
      match_fmt = st.selectbox("Format", ["ODI", "T20I", "Test"])
    with col_b:
      runs = st.number_input("Runs Scored", min_value=0, max_value=300, value=75)
      balls = st.number_input("Balls Faced", min_value=1, max_value=350, value=60)
      wickets = st.number_input("Wickets Taken (if bowler/all-rounder)", min_value=0, max_value=10, value=0)

    submit_btn = st.form_submit_button("Commit Inning to Database")

    if submit_btn:
      new_id = f"MATCH-2026-{random.randint(5009,9999)}"
      sr = (runs / balls) * 100
      status = "🔥 Elite Match-Winning Knock" if sr > 150 or runs >= 100 else "✅ Stable Baseline"
      
      conn = sqlite3.connect("stump_metrics.db")
      cur = conn.cursor()
      cur.execute(
          """
            INSERT INTO player_match_logs 
            (match_id, player_name, team, opposition, format, runs_scored, balls_faced, fours, sixes, wickets_taken, economy_rate, performance_status, match_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, 6, 2, ?, 6.0, ?, ?)
          """,
          (new_id, selected_player, player_team, opp_team, match_fmt, runs, balls, wickets, status, datetime.now().strftime("%Y-%m-%d"))
      )
      conn.commit()
      conn.close()
      st.success(f"Successfully recorded new innings for {selected_player}!")
      st.rerun()