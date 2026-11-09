"""Train and evaluate a Random Forest unloading-duration model."""

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DATA_PATH = "data/dock_visit_history.csv"

CATEGORICAL_FEATURES = [
    "dock_type",
    "facility_id",
    "carrier_id",
    "vehicle_type_code",
    "product_category",
    "priority_code",
    "origin_city",
    "day_of_week",
]

NUMERIC_FEATURES = [
    "temperature_control_required",
    "load_weight_kg",
    "pallet_count",
    "origin_distance_km",
    "rain_flag",
    "labour_shortage_flag",
    "departure_hour",
    "arrival_hour",
    "slot_hour",
    "arrival_month",
]


def main():
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["unload_min"]).copy()

    # Parse timestamps and sort chronologically.
    for column in [
        "planned_departure_ts",
        "planned_arrival_ts",
        "slot_start_ts",
    ]:
        df[column] = pd.to_datetime(df[column], utc=True)

    df = df.sort_values("planned_arrival_ts").reset_index(drop=True)

    # Extract information available before unloading.
    df["departure_hour"] = df["planned_departure_ts"].dt.hour
    df["arrival_hour"] = df["planned_arrival_ts"].dt.hour
    df["slot_hour"] = df["slot_start_ts"].dt.hour
    df["arrival_month"] = df["planned_arrival_ts"].dt.month

    features = CATEGORICAL_FEATURES + NUMERIC_FEATURES
    X = df[features]
    y = df["unload_min"]

    # Use the same chronological 80/20 split as the baseline.
    split_index = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
    y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])

    preprocessing = ColumnTransformer([
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ("numeric", numeric_pipeline, NUMERIC_FEATURES),
    ])

    model = Pipeline([
        ("preprocessing", preprocessing),
        ("regressor", RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
        )),
    ])

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    model_mae = mean_absolute_error(y_test, predictions)
    baseline_prediction = y_train.median()
    baseline_mae = mean_absolute_error(
        y_test,
        [baseline_prediction] * len(y_test),
    )

    improvement = baseline_mae - model_mae

    print("Random Forest model evaluation")
    print("--------------------------------")
    print(f"Training rows: {len(X_train)}")
    print(f"Test rows: {len(X_test)}")
    print(f"Baseline MAE: {baseline_mae:.2f} minutes")
    print(f"Random Forest MAE: {model_mae:.2f} minutes")
    print(f"MAE improvement: {improvement:.2f} minutes")
    print(
        "Test period:",
        df.iloc[split_index]["planned_arrival_ts"],
        "to",
        df.iloc[-1]["planned_arrival_ts"],
    )

    if model_mae < baseline_mae:
        print("Result: Random Forest beats the baseline.")
    else:
        print("Result: Random Forest does not beat the baseline yet.")

    # Save model artifact and metadata
    import joblib
    import os
    model_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(model_dir, "unload_predictor.joblib")
    joblib.dump(model, model_path)
    print(f"Saved trained model to {model_path}")


if __name__ == "__main__":
    main()