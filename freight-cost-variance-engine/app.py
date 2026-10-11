import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

# Page Configuration
st.set_page_config(page_title="Freight Cost & Variance Analytics", page_icon="🚢", layout="wide")

# Database Connection Parameters
DB_USER = "tejdeepreddygudise"  
DB_PASSWORD = "1234"      
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "freight_db"

@st.cache_resource
def get_engine():
    return create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = get_engine()

# Load Transaction Data from PostgreSQL View
@st.cache_data
def load_data():
    query = "SELECT * FROM vw_freight_cost_variance;"
    return pd.read_sql(query, con=engine)

# Load Carrier Tradeoffs Data
@st.cache_data
def load_carrier_tradeoffs():
    query = "SELECT * FROM vw_carrier_tradeoffs;"
    return pd.read_sql(query, con=engine)

df = load_data().copy()
df_carriers = load_carrier_tradeoffs().copy()

# Dashboard Header
st.title("🚢 Freight Cost & Variance Analytics Engine")
st.markdown("Executive procurement dashboard tracking multi-modal spot-market exposure, contract compliance, and carrier efficiency.")

# Sidebar Filters
st.sidebar.header("🔍 Filter Parameters")

# 1. Trade Lane Filter (New Addition)
if not df.empty and {'lane_id', 'origin_hub', 'destination_hub'}.issubset(df.columns):
    df['lane_display'] = df['lane_id'] + " (" + df['origin_hub'] + " ➔ " + df['destination_hub'] + ")"
    selected_lane = st.sidebar.selectbox("Select Trade Lane", ["All"] + sorted(list(df['lane_display'].unique())))
    if selected_lane != "All":
        df = df[df['lane_display'] == selected_lane]

# 2. Carrier Filter
selected_carrier = st.sidebar.selectbox("Select Carrier", ["All"] + sorted(list(df['carrier_name'].unique())))
if selected_carrier != "All":
    df = df[df['carrier_name'] == selected_carrier]

# 3. Mode of Transport Filter
selected_mode = st.sidebar.selectbox("Transport Mode", ["All"] + sorted(list(df['mode_of_transport'].unique())))
if selected_mode != "All":
    df = df[df['mode_of_transport'] == selected_mode]

# 4. Performance Status Filter
selected_status = st.sidebar.selectbox("Performance Status", ["All"] + sorted(list(df['cost_performance_status'].unique())))
if selected_status != "All":
    df = df[df['cost_performance_status'] == selected_status]

# Create App Tabs for Multi-Page Feel
tab1, tab2 = st.tabs(["📊 Executive Cost & Lane Analytics", "🚚 Carrier Performance & Tiers"])

with tab1:
    # KPI Metrics Row
    st.markdown("### 📊 Executive Overview")
    col1, col2, col3, col4 = st.columns(4)

    total_shipments = len(df)
    total_spend = df['actual_rate_paid_usd'].sum()
    total_leakage = df['variance_vs_contract_usd'].sum()
    avg_transit = df['transit_days'].mean() if total_shipments > 0 else 0

    col1.metric("Total Shipments", f"{total_shipments:,}")
    col2.metric("Total Freight Spend", f"${total_spend:,.2f}")
    col3.metric("Total Cost Leakage", f"${total_leakage:,.2f}", delta_color="inverse")
    col4.metric("Avg Transit Days", f"{avg_transit:.1f} days")

    st.markdown("---")

    # Trade Lane Summary Breakdown
    st.subheader("🌐 Trade Lane Cost Breakdown")
    if not df.empty:
        lane_summary = df.groupby(['lane_id', 'origin_hub', 'destination_hub', 'mode_of_transport']).agg(
            shipments=('transaction_id', 'count'),
            avg_actual=('actual_rate_paid_usd', 'mean'),
            avg_contract=('contracted_base_rate_usd', 'mean'),
            total_leakage=('variance_vs_contract_usd', 'sum')
        ).reset_index()
        
        lane_summary['trade_lane'] = lane_summary['lane_id'] + " - " + lane_summary['origin_hub'] + " ➔ " + lane_summary['destination_hub']
        lane_summary = lane_summary[['trade_lane', 'mode_of_transport', 'shipments', 'avg_actual', 'avg_contract', 'total_leakage']]
        lane_summary = lane_summary.sort_values(by='total_leakage', ascending=False)
        
        st.dataframe(lane_summary.style.format({
            'avg_actual': '${:,.2f}',
            'avg_contract': '${:,.2f}',             'total_leakage': '${:,.2f}'
        }), width="stretch")
    else:
        st.warning("No data matches the selected filters.")

    st.markdown("---")

    # Detailed Transaction View (Drop temporary display column if present)
    st.subheader("📋 Underlying Transactional Audit Log")
    display_df = df.drop(columns=['lane_display'], errors='ignore')
    st.dataframe(display_df, width="stretch")

with tab2:
    st.subheader("🏆 Multi-Modal Carrier Tradeoffs & Operational Tiers")
    st.markdown("Evaluating carriers based on speed, cost variance, and overall operational efficiency tier.")
    
    if not df_carriers.empty:
        st.dataframe(df_carriers.style.format({
            'avg_rate_paid': '${:,.2f}',
            'avg_contract_rate': '${:,.2f}',             'total_leakage_usd': '${:,.2f}',
            'avg_transit_days': '{:.1f} days'
        }), width="stretch")
    else:
        st.warning("No carrier tradeoff data found. Ensure the SQL view `vw_carrier_tradeoffs` is created.")