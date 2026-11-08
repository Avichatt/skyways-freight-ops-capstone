"""Chronological median baseline for unloading-duration prediction."""

import pandas as pd
from sklearn.metrics import mean_absolute_error


DATA_PATH = "data/dock_visit_history.csv"

# Only use features available before the unloading process.
FEATURES = [
    "dock_type",
    "facility_id",
    "carrier_id",
    "vehicle_type_code",
    "product_category",
    "temperature_control_required",
    "load_weight_kg",
    "pallet_count",
    "priority_code",
    "origin_city",
    "origin_distance_km",
    "planned_departure_ts",
    "planned_arrival_ts",
    "slot_start_ts",
    "rain_flag",
    "labour_shortage_flag",
    "day_of_week",
]


def main():
    df = pd.read_csv(DATA_PATH)

    # Keep rows with a known target.
    df = df.dropna(subset=["unload_min"]).copy()

    # Sort by arrival time before splitting.
    df["planned_arrival_ts"] = pd.to_datetime(
        df["planned_arrival_ts"], utc=True
    )
    df = df.sort_values("planned_arrival_ts").reset_index(drop=True)

    split_index = int(len(df) * 0.8)
    train = df.iloc[:split_index]
    test = df.iloc[split_index:]

    # Predict the training-set median for every test row.
    baseline_prediction = train["unload_min"].median()

    mae = mean_absolute_error(
        test["unload_min"],
        [baseline_prediction] * len(test),
    )

    print("Chronological median baseline")
    print("--------------------------------")
    print(f"Training rows: {len(train)}")
    print(f"Test rows: {len(test)}")
    print(f"Training median: {baseline_prediction:.2f} minutes")
    print(f"Test MAE: {mae:.2f} minutes")
    print(
        "Test period:",
        train["planned_arrival_ts"].max(),
        "to",
        test["planned_arrival_ts"].max(),
    )


if __name__ == "__main__":
    main()