from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

SEED = 42
rng = np.random.default_rng(SEED)

OUTPUT_DIR = Path("FORGEIQ_reconstructed 1/data_generator/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ASSETS
# ============================================================

ASSETS = [
    [
        "CNC-001",
        "CNC",
        "PLANT-A",
        2.0,       # ideal vibration
        65.0,      # ideal temperature
        1200.0,    # ideal RPM
        100.0,     # ideal pressure
        25.0,      # ideal current
    ],
    [
        "CNC-002",
        "CNC",
        "PLANT-A",
        2.0,
        65.0,
        1200.0,
        100.0,
        25.0,
    ],
    [
        "PRESS-001",
        "PRESS",
        "PLANT-B",
        2.5,
        70.0,
        1100.0,
        150.0,
        30.0,
    ],
    [
        "PRESS-002",
        "PRESS",
        "PLANT-B",
        2.5,
        70.0,
        1100.0,
        150.0,
        30.0,
    ],
    [
        "PUMP-001",
        "PUMP",
        "PLANT-C",
        1.8,
        60.0,
        1450.0,
        80.0,
        20.0,
    ],
]


assets_df = pd.DataFrame(
    ASSETS,
    columns=[
        "ASSET_ID",
        "ASSET_TYPE",
        "LOCATION",
        "IDEAL_VIBRATION",
        "IDEAL_TEMPERATURE",
        "IDEAL_RPM",
        "IDEAL_PRESSURE",
        "IDEAL_CURRENT",
    ],
)


# ============================================================
# FAILURE EVENTS
# ============================================================

FAILURE_SPECS = {
    "CNC-001": (
        "2026-11-17 10:00:00",
        "BEARING_DEGRADATION",
    ),
    "CNC-002": (
        "2026-11-17 10:00:00",
        "BEARING_DEGRADATION",
    ),
    "PRESS-001": (
        "2026-11-17 13:00:00",
        "MOTOR_OVERHEATING",
    ),
    "PRESS-002": (
        "2026-11-17 15:00:00",
        "MOTOR_OVERHEATING",
    ),
    "PUMP-001": (
        "2026-11-17 14:00:00",
        "BEARING_DEGRADATION",
    ),
}


# ============================================================
# TIMELINE
# ============================================================

HOURS = pd.date_range(
    "2026-08-24 00:00:00",
    "2026-11-21 17:00:00",
    freq="h",
)


# ============================================================
# SENSOR DATA
# ============================================================

def generate_sensor_data():

    rows = []

    for asset in ASSETS:

        (
            asset_id,
            asset_type,
            location,
            ideal_vibration,
            ideal_temperature,
            ideal_rpm,
            ideal_pressure,
            ideal_current,
        ) = asset

        failure_time = pd.Timestamp(
            FAILURE_SPECS[asset_id][0]
        )

        failure_type = FAILURE_SPECS[asset_id][1]

        for timestamp in HOURS:

            hours_to_failure = (
                failure_time - timestamp
            ).total_seconds() / 3600

            # ------------------------------------------------
            # Normal operating conditions
            # ------------------------------------------------

            vibration = (
                ideal_vibration
                + rng.normal(0, 0.18)
            )

            temperature = (
                ideal_temperature
                + rng.normal(0, 2.0)
            )

            rpm = (
                ideal_rpm
                + rng.normal(0, 12)
            )

            pressure = (
                ideal_pressure
                + rng.normal(0, 1.5)
            )

            current = (
                ideal_current
                + rng.normal(0, 1.2)
            )

            # ------------------------------------------------
            # Progressive degradation
            # ------------------------------------------------

            if 0 <= hours_to_failure <= 24:

                severity = (
                    24 - hours_to_failure
                ) / 24

                # ----------------------------
                # Bearing degradation
                # ----------------------------

                if failure_type == "BEARING_DEGRADATION":

                    vibration += (
                        0.9
                        + 1.8 * severity
                    )

                    temperature += (
                        4
                        + 16 * severity
                    )

                    current += (
                        2 * severity
                    )

                # ----------------------------
                # Motor overheating
                # ----------------------------

                elif failure_type == "MOTOR_OVERHEATING":

                    temperature += (
                        8
                        + 20 * severity
                    )

                    vibration += (
                        0.25
                        + 0.7 * severity
                    )

                    current += (
                        3
                        + 5 * severity
                    )

            rows.append(
                [
                    f"{asset_id}-{timestamp:%Y%m%d%H}",
                    timestamp,
                    asset_id,
                    max(vibration, 0.1),
                    max(temperature, 0),
                    max(rpm, 0),
                    max(pressure, 0),
                    max(current, 0),
                ]
            )

    return pd.DataFrame(
        rows,
        columns=[
            "EVENT_ID",
            "EVENT_TIMESTAMP",
            "ASSET_ID",
            "VIBRATION_MM_S",
            "TEMPERATURE_C",
            "RPM",
            "PRESSURE_BAR",
            "CURRENT_AMPS",
        ],
    )


# ============================================================
# FAILURE HISTORY
# ============================================================

def generate_failures():

    rows = []

    failure_id = 1

    # --------------------------------------------------------
    # Main failure events
    # --------------------------------------------------------

    for asset_id, (
        timestamp,
        failure_type,
    ) in FAILURE_SPECS.items():

        if failure_type == "BEARING_DEGRADATION":

            root_cause = (
                "Bearing wear and shaft misalignment"
            )

            downtime = 14.0
            production_loss = 24500.0

        else:

            root_cause = (
                "Insufficient cooling and thermal load"
            )

            downtime = 8.0
            production_loss = 9200.0

        rows.append(
            [
                f"F-{failure_id:04d}",
                asset_id,
                pd.Timestamp(timestamp),
                failure_type,
                root_cause,
                downtime,
                production_loss,
            ]
        )

        failure_id += 1

    # --------------------------------------------------------
    # Historical failures
    # --------------------------------------------------------

    asset_ids = list(FAILURE_SPECS.keys())

    for i in range(145):

        asset_id = asset_ids[
            i % len(asset_ids)
        ]

        if asset_id.startswith(
            ("CNC-", "PUMP-")
        ):

            failure_type = (
                "BEARING_DEGRADATION"
            )

        else:

            failure_type = (
                "MOTOR_OVERHEATING"
            )

        timestamp = (
            pd.Timestamp("2026-08-25")
            + pd.Timedelta(
                hours=int(
                    rng.integers(
                        0,
                        1800,
                    )
                )
            )
        )

        rows.append(
            [
                f"F-{failure_id:04d}",
                asset_id,
                timestamp,
                failure_type,
                "Historical equipment degradation",
                round(
                    float(
                        rng.uniform(
                            2,
                            14,
                        )
                    ),
                    2,
                ),
                round(
                    float(
                        rng.uniform(
                            1500,
                            25000,
                        )
                    ),
                    2,
                ),
            ]
        )

        failure_id += 1

    return pd.DataFrame(
        rows,
        columns=[
            "FAILURE_ID",
            "ASSET_ID",
            "FAILURE_TIMESTAMP",
            "FAILURE_TYPE",
            "ROOT_CAUSE",
            "DOWNTIME_HOURS",
            "PRODUCTION_LOSS",
        ],
    ).sort_values(
        "FAILURE_TIMESTAMP"
    )


# ============================================================
# MAINTENANCE
# ============================================================

def generate_maintenance():

    rows = []

    for i, asset in enumerate(
        ASSETS,
        start=1,
    ):

        asset_id = asset[0]

        maintenance_date = (
            pd.Timestamp(
                "2026-11-07 22:00:00"
            )
            - pd.Timedelta(
                hours=i * 2
            )
        )

        rows.append(
            [
                f"MW-{i:04d}",
                asset_id,
                maintenance_date,
                "PREVENTIVE",
                None,
                None,
                2.0,
                750.0,
                "TECH-01",
                "Routine preventive maintenance completed",
            ]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "WORK_ORDER_ID",
            "ASSET_ID",
            "MAINTENANCE_DATE",
            "MAINTENANCE_TYPE",
            "FAILURE_TYPE",
            "ROOT_CAUSE",
            "DOWNTIME_HOURS",
            "MAINTENANCE_COST",
            "TECHNICIAN",
            "RESOLUTION",
        ],
    )


# ============================================================
# PRODUCTION DATA
# ============================================================

def generate_production(sensor_df):

    rows = []

    timestamps = (
        sensor_df[
            [
                "ASSET_ID",
                "EVENT_TIMESTAMP",
            ]
        ]
        .drop_duplicates()
    )

    for row in timestamps.itertuples(
        index=False
    ):

        asset_id = row.ASSET_ID
        timestamp = row.EVENT_TIMESTAMP

        planned_time = 60.0

        run_time = float(
            rng.uniform(
                48,
                58,
            )
        )

        units = float(
            rng.integers(
                45,
                70,
            )
        )

        good_units = (
            units
            * float(
                rng.uniform(
                    0.94,
                    0.995,
                )
            )
        )

        # ----------------------------------------------------
        # Production degradation before failure
        # ----------------------------------------------------

        failure_time = pd.Timestamp(
            FAILURE_SPECS[asset_id][0]
        )

        hours_to_failure = (
            failure_time - timestamp
        ).total_seconds() / 3600

        if 0 <= hours_to_failure <= 24:

            severity = (
                24 - hours_to_failure
            ) / 24

            run_time -= (
                15 * severity
            )

            units *= (
                1
                - 0.30 * severity
            )

            good_units *= (
                1
                - 0.35 * severity
            )

        downtime = (
            planned_time
            - run_time
        )

        rows.append(
            [
                f"ORD-{asset_id}-{timestamp:%Y%m%d%H}",
                asset_id,
                timestamp,
                max(units, 0),
                max(
                    min(
                        good_units,
                        units,
                    ),
                    0,
                ),
                1.0,
                planned_time,
                max(run_time, 0),
                max(downtime, 0),
            ]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "ORDER_ID",
            "ASSET_ID",
            "PRODUCTION_TIMESTAMP",
            "UNITS_PRODUCED",
            "GOOD_UNITS",
            "IDEAL_CYCLE_TIME_MIN",
            "PLANNED_PRODUCTION_TIME_MIN",
            "RUN_TIME_MIN",
            "DOWNTIME_MIN",
        ],
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("Generating FORGEIQ data...")

    sensor_df = generate_sensor_data()

    failures_df = generate_failures()

    maintenance_df = generate_maintenance()

    production_df = generate_production(
        sensor_df
    )

    assets_df.to_csv(
        OUTPUT_DIR / "assets.csv",
        index=False,
    )

    sensor_df.to_csv(
        OUTPUT_DIR / "sensor_telemetry.csv",
        index=False,
    )

    failures_df.to_csv(
        OUTPUT_DIR / "failures.csv",
        index=False,
    )

    maintenance_df.to_csv(
        OUTPUT_DIR / "maintenance.csv",
        index=False,
    )

    production_df.to_csv(
        OUTPUT_DIR / "production.csv",
        index=False,
    )

    print()
    print("Generation completed.")
    print("----------------------------")
    print(
        f"Assets:       {len(assets_df):,}"
    )
    print(
        f"Sensors:      {len(sensor_df):,}"
    )
    print(
        f"Failures:     {len(failures_df):,}"
    )
    print(
        f"Maintenance:  {len(maintenance_df):,}"
    )
    print(
        f"Production:   {len(production_df):,}"
    )
    print()
    print(
        f"Output: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()