from datetime import datetime, timedelta
import random
import sqlite3
import pandas as pd
import streamlit as st
import yfinance as yf

# Page Configuration
st.set_page_config(
    page_title="Aegis Treasury Intelligence", page_icon="🏛️", layout="wide"
)


# ==========================================
# SECURE MULTI-ENTITY ENTERPRISE DATABASE
# ==========================================
def init_aegis_db():
  conn = sqlite3.connect("aegis_treasury.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS general_ledger (
            transaction_id TEXT PRIMARY KEY,
            entity TEXT,
            counterparty TEXT,
            department TEXT,
            entry_type TEXT,
            amount REAL,
            currency TEXT,
            compliance_status TEXT,
            timestamp TEXT
        )
    """)

  cursor.execute("SELECT COUNT(*) FROM general_ledger")
  if cursor.fetchone()[0] == 0:
    entities = [
        "Aegis Americas Inc",
        "Aegis EMEA Holdings",
        "Aegis APAC Operations",
    ]
    counterparties = [
        "Stripe Global Billing",
        "AWS Cloud Services",
        "Salesforce CRM",
        "Deloitte Advisory",
        "JPMorgan Chase Treasury",
    ]
    departments = [
        "Cloud Infrastructure",
        "Enterprise Sales",
        "R&D Engineering",
        "Legal & Compliance",
        "Global Marketing",
    ]

    base_date = datetime.now() - timedelta(days=45)
    records = []

    for i in range(1, 120):
      t_id = f"AGS-TXN-2026-{i:04d}"
      ent = random.choice(entities)
      cparty = random.choice(counterparties)
      dept = random.choice(departments)
      is_rev = random.random() > 0.4
      entry = "Revenue" if is_rev else "Expense"
      amt = (
          round(random.uniform(12000.00, 85000.00), 2)
          if is_rev
          else round(random.uniform(2500.00, 24000.00), 2)
      )
      status = random.choices(
          ["Verified SOX-Compliant", "Under Review", "Flagged Threshold"],
          weights=[88, 8, 4],
      )[0]
      t_date = (base_date + timedelta(hours=i * 6)).strftime(
          "%Y-%m-%d %H:%M:%S"
      )

      records.append((
          t_id,
          ent,
          cparty,
          dept,
          entry,
          amt,
          "USD",
          status,
          t_date,
      ))

    cursor.executemany(
        """
            INSERT OR IGNORE INTO general_ledger 
            (transaction_id, entity, counterparty, department, entry_type, amount, currency, compliance_status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

  conn.commit()
  conn.close()


init_aegis_db()


def load_ledger():
  conn = sqlite3.connect("aegis_treasury.db")
  df = pd.read_sql_query("SELECT * FROM general_ledger", conn)
  conn.close()
  df["timestamp"] = pd.to_datetime(df["timestamp"])
  return df


df = load_ledger()


# ==========================================
# REAL MARKET DATA INTEGRATION (YFINANCE)
# ==========================================
@st.cache_data(ttl=3600)
def fetch_market_benchmarks():
  tickers = ["^GSPC", "^TNX", "^IXIC"]
  data = yf.download(tickers, period="5d", progress=False)["Close"]
  return data


market_data = fetch_market_benchmarks()

# ==========================================
# DASHBOARD HEADER & ENTITY SELECTOR
# ==========================================
st.title("🏛️ Aegis Treasury Intelligence Platform")
st.markdown(
    "**Global Liquidity Management, Multi-Entity General Ledger & Real-Time"
    " Risk Auditing**"
)
st.markdown("---")

# Sidebar Controls for Enterprise Entities
st.sidebar.header("🌐 Enterprise Controls")
selected_entity = st.sidebar.selectbox(
    "Select Business Entity",
    [
        "All Global Entities",
        "Aegis Americas Inc",
        "Aegis EMEA Holdings",
        "Aegis APAC Operations",
    ],
)

if selected_entity != "All Global Entities":
  df = df[df["entity"] == selected_entity]

# Executive Financial Summary KPIs
total_rev = df[df["entry_type"] == "Revenue"]["amount"].sum()
total_exp = df[df["entry_type"] == "Expense"]["amount"].sum()
net_income = total_rev - total_exp
operating_margin = (net_income / total_rev) * 100 if total_rev > 0 else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Consolidated YTD Revenue", f"${total_rev:,.2f}", delta="+18.4% YoY")
k2.metric(
    "Total Operating Burn", f"${total_exp:,.2f}", delta="-4.2% Optimization"
)
k3.metric(
    "Net Operating Income",
    f"${net_income:,.2f}",
    delta=f"{operating_margin:.1f}% Margin",
)
k4.metric(
    "Treasury Liquidity Runway", "24.6 Months", delta="AAA Investment Grade"
)

st.markdown("---")

# Professional Enterprise Tabs
tab_ledger, tab_market, tab_compliance, tab_simulator = st.tabs([
    "📋 General Ledger Audit",
    "📈 Live Market & Treasury Benchmarks",
    "🚨 SOX Compliance & Risk Monitor",
    "⚡ Real-Time Ingestion Portal",
])

with tab_ledger:
  st.subheader(f"General Ledger Activity — {selected_entity}")

  col_f1, col_f2 = st.columns(2)
  with col_f1:
    f_type = st.selectbox("Filter Ledger Type", ["All", "Revenue", "Expense"])
  with col_f2:
    f_status = st.selectbox(
        "Filter Compliance Status",
        [
            "All",
            "Verified SOX-Compliant",
            "Under Review",
            "Flagged Threshold",
        ],
    )

  filtered_df = df.copy()
  if f_type != "All":
    filtered_df = filtered_df[filtered_df["entry_type"] == f_type]
  if f_status != "All":
    filtered_df = filtered_df[
        filtered_df["compliance_status"] == f_status
    ]

  st.dataframe(
      filtered_df.sort_values(by="timestamp", ascending=False),
      use_container_width=True,
  )

with tab_market:
  st.subheader("Real-Time Macroeconomic & Capital Market Benchmarks")
  st.markdown(
      "Live data pulled via API feeds tracking institutional market rates and"
      " equity indices:"
  )

  if not market_data.empty:
    st.line_chart(market_data)
  else:
    st.warning("Awaiting live market data feed connection...")

with tab_compliance:
  st.subheader("Automated SOX Compliance & Transaction Risk Review")
  flagged_df = df[df["compliance_status"] != "Verified SOX-Compliant"]

  if not flagged_df.empty:
    st.warning(
        f"⚠️ {len(flagged_df)} transactions require mandatory audit review under"
        " Sarbanes-Oxley (SOX) guidelines."
    )
    st.dataframe(
        flagged_df[[
            "transaction_id",
            "entity",
            "counterparty",
            "amount",
            "compliance_status",
            "timestamp",
        ]],
        use_container_width=True,
    )
  else:
    st.success(
        "✅ 100% of ledger transactions comply with institutional governance"
        " thresholds."
    )

with tab_simulator:
  st.subheader("Process Enterprise Wire / Invoice Ingestion")
  with st.form("wire_form"):
    c_party = st.text_input("Counterparty / Vendor Name", "Stripe Global Network")
    c_dept = st.selectbox(
        "Department",
        [
            "Cloud Infrastructure",
            "Enterprise Sales",
            "R&D Engineering",
            "Legal & Compliance",
        ],
    )
    c_type = st.selectbox("Entry Classification", ["Revenue", "Expense"])
    c_amt = st.number_input(
        "Amount (USD)", min_value=100.0, step=1000.0, value=25000.0
    )
    submit_wire = st.form_submit_button("Commit Wire to General Ledger")

    if submit_wire:
      new_id = f"AGS-TXN-2026-{random.randint(5000,9999)}"
      conn = sqlite3.connect("aegis_treasury.db")
      cur = conn.cursor()
      cur.execute(
          """
                INSERT INTO general_ledger 
                (transaction_id, entity, counterparty, department, entry_type, amount, currency, compliance_status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, 'USD', 'Verified SOX-Compliant', ?)
            """,
          (
              new_id,
              selected_entity
              if selected_entity != "All Global Entities"
              else "Aegis Americas Inc",
              c_party,
              c_dept,
              c_type,
              c_amt,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          ),
      )
      conn.commit()
      conn.close()
      st.success(
          f"Wire transaction {new_id} successfully processed and locked into"
          " General Ledger!"
      )
      st.rerun()