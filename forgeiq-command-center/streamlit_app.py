import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="FORGEIQ Command Center", page_icon="🏭", layout="wide")
conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))


@st.cache_data(ttl=60)
def load_command_center():
    return conn.query("""
        SELECT *
        FROM FORGEIQ.ANALYTICS.COMMAND_CENTER
        ORDER BY CASE RISK_LEVEL
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            ELSE 4 END,
            FAILURE_PROBABILITY DESC
    """)


df = load_command_center()
st.title("🏭 FORGEIQ Command Center")

if df.empty:
    st.info("No active high-risk alerts.")
    st.stop()

assets = df["ASSET_ID"].dropna().unique().tolist()
selected = st.sidebar.selectbox("Select Asset", assets)
asset = df[df["ASSET_ID"] == selected].sort_values("EVENT_TIMESTAMP", ascending=False).iloc[0]


def v(name, default=0):
    x = asset.get(name, default)
    return default if pd.isna(x) else x


st.markdown(f"# 🏭 {asset['ASSET_ID']}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Failure Risk", f"{v('FAILURE_PROBABILITY')*100:.1f}%")
c2.metric("Risk Level", str(v("RISK_LEVEL", "N/A")))
c3.metric("OEE", f"{v('OEE')*100:.1f}%")
c4.metric("Hours Since Maintenance", f"{v('HOURS_SINCE_MAINTENANCE'):.0f}")

st.divider()
st.subheader("📊 Sensor Evidence")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Vibration", f"{v('AVG_VIBRATION'):.2f} mm/s", f"{v('VIBRATION_DEVIATION'):+.2f}")
c2.metric("Temperature", f"{v('AVG_TEMPERATURE'):.1f} °C", f"{v('TEMPERATURE_DEVIATION'):+.1f}")
c3.metric("RPM", f"{v('AVG_RPM'):.0f}", f"{v('RPM_DEVIATION'):+.1f}")
c4.metric("Pressure", f"{v('AVG_PRESSURE'):.1f} bar", f"{v('PRESSURE_DEVIATION'):+.1f}")

st.subheader("📈 Sensor Change — 1 Hour")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Vibration", f"{v('VIBRATION_CHANGE_1H'):+.2f} mm/s")
c2.metric("Temperature", f"{v('TEMPERATURE_CHANGE_1H'):+.2f} °C")
c3.metric("RPM", f"{v('RPM_CHANGE_1H'):+.2f}")
c4.metric("Pressure", f"{v('PRESSURE_CHANGE_1H'):+.2f} bar")

st.divider()
st.subheader("🔧 Failure Diagnosis")
c1, c2 = st.columns(2)
c1.write(f"**Likely Failure Type:** {v('LIKELY_FAILURE_TYPE', 'N/A')}")
c2.write(f"**Operator Action:** {v('OPERATOR_ACTION', 'N/A')}")
st.markdown("**Recommended Action**")
st.info(v("RECOMMENDED_ACTION", "N/A"))

st.divider()
st.subheader("🤖 AI Root Cause Analysis")
rca = v("RCA_EXPLANATION", "")
if str(rca).strip():
    st.markdown(str(rca).replace("\\n", "\n"))
else:
    st.info("AI root cause explanation is not available.")

st.divider()
st.subheader("🛠 Work Order")
if str(v("WORK_ORDER_ID", "")).strip():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Work Order", v("WORK_ORDER_ID"))
    c2.metric("Priority", v("WORK_ORDER_PRIORITY", "N/A"))
    c3.metric("Status", v("WORK_ORDER_STATUS", "N/A"))
    c4.metric("Estimated Downtime", f"{v('ESTIMATED_DOWNTIME_HOURS'):.1f} hrs")
    st.metric("Estimated Production Loss", f"${v('ESTIMATED_PRODUCTION_LOSS'):,.0f}")
else:
    st.info("No active work order for this alert.")

st.divider()
st.subheader("📋 Active Command Center Alerts")
cols = [c for c in [
    "ASSET_ID", "EVENT_TIMESTAMP", "FAILURE_PROBABILITY", "RISK_LEVEL",
    "LIKELY_FAILURE_TYPE", "OEE", "HOURS_SINCE_MAINTENANCE", "WORK_ORDER_STATUS"
] if c in df.columns]
st.dataframe(df[cols], use_container_width=True, hide_index=True)
