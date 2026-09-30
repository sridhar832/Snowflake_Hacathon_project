import pandas as pd
from snowflake.snowpark.context import get_active_session

session = get_active_session()

def load_command_center():
    return session.sql("""
        SELECT *
        FROM FORGEIQ.ANALYTICS.COMMAND_CENTER
        ORDER BY CASE RISK_LEVEL
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            ELSE 4 END,
            FAILURE_PROBABILITY DESC
    """).to_pandas()

df = load_command_center()
print("=== FORGEIQ Command Center ===\n")

if df.empty:
    print("No active high-risk alerts.")
else:
    assets = df["ASSET_ID"].dropna().unique().tolist()
    asset_id = assets[0]
    asset = df[df["ASSET_ID"] == asset_id].sort_values("EVENT_TIMESTAMP", ascending=False).iloc[0]

    def v(name, default=0):
        x = asset.get(name, default)
        return default if pd.isna(x) else x

    print(f"Asset: {asset['ASSET_ID']}")
    print(f"  Failure Risk:          {v('FAILURE_PROBABILITY')*100:.1f}%")
    print(f"  Risk Level:            {v('RISK_LEVEL', 'N/A')}")
    print(f"  OEE:                   {v('OEE')*100:.1f}%")
    print(f"  Hours Since Maint:     {v('HOURS_SINCE_MAINTENANCE'):.0f}")

    print(f"\n--- Sensor Evidence ---")
    print(f"  Vibration:   {v('AVG_VIBRATION'):.2f} mm/s (dev: {v('VIBRATION_DEVIATION'):+.2f})")
    print(f"  Temperature: {v('AVG_TEMPERATURE'):.1f} C (dev: {v('TEMPERATURE_DEVIATION'):+.1f})")
    print(f"  RPM:         {v('AVG_RPM'):.0f} (dev: {v('RPM_DEVIATION'):+.1f})")
    print(f"  Pressure:    {v('AVG_PRESSURE'):.1f} bar (dev: {v('PRESSURE_DEVIATION'):+.1f})")

    print(f"\n--- Sensor Change (1 Hour) ---")
    print(f"  Vibration:   {v('VIBRATION_CHANGE_1H'):+.2f} mm/s")
    print(f"  Temperature: {v('TEMPERATURE_CHANGE_1H'):+.2f} C")
    print(f"  RPM:         {v('RPM_CHANGE_1H'):+.2f}")
    print(f"  Pressure:    {v('PRESSURE_CHANGE_1H'):+.2f} bar")

    print(f"\n--- Failure Diagnosis ---")
    print(f"  Likely Failure Type: {v('LIKELY_FAILURE_TYPE', 'N/A')}")
    print(f"  Operator Action:     {v('OPERATOR_ACTION', 'N/A')}")
    print(f"  Recommended Action:  {v('RECOMMENDED_ACTION', 'N/A')}")

    rca = v("RCA_EXPLANATION", "")
    if str(rca).strip():
        print(f"\n--- AI Root Cause Analysis ---")
        print(str(rca).replace("\\n", "\n"))
    else:
        print("\n--- AI Root Cause Analysis ---")
        print("  AI root cause explanation is not available.")

    if str(v("WORK_ORDER_ID", "")).strip():
        print(f"\n--- Work Order ---")
        print(f"  Work Order ID:       {v('WORK_ORDER_ID')}")
        print(f"  Priority:            {v('WORK_ORDER_PRIORITY', 'N/A')}")
        print(f"  Status:              {v('WORK_ORDER_STATUS', 'N/A')}")
        print(f"  Estimated Downtime:  {v('ESTIMATED_DOWNTIME_HOURS'):.1f} hrs")
        print(f"  Est. Production Loss: ${v('ESTIMATED_PRODUCTION_LOSS'):,.0f}")

    print(f"\n--- Active Command Center Alerts ({len(df)} total) ---")
    cols = [c for c in [
        "ASSET_ID", "EVENT_TIMESTAMP", "FAILURE_PROBABILITY", "RISK_LEVEL",
        "LIKELY_FAILURE_TYPE", "OEE", "HOURS_SINCE_MAINTENANCE", "WORK_ORDER_STATUS"
    ] if c in df.columns]
    print(df[cols].to_string(index=False))
