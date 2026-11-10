"""
Train and evaluate a Late Arrival Classification model for SkyWays.

Target: arrival_delta_min > 30 minutes (binary classification)
Evaluated on a chronological time-ordered split (Feb-Jun train, Jul test).
Leakage prevention (Brief Page 26):
  - NO actual_gate_in_ts
  - NO yard_wait_min
  - Only features available before truck arrival
"""

import os
import joblib
import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score


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
    "slot_hour",
    "arrival_month",
]


def train_late_arrival_model():
    df = pd.read_csv(DATA_PATH)
    # 1. Clean duplicates
    df = df.drop_duplicates()
    # 2. Exclude NO_SHOW visits as per brief page 26
    df = df[df["visit_outcome"] != "NO_SHOW"].copy()
    df = df.dropna(subset=["arrival_delta_min"])

    # 3. Target: late arrival (> 30 min)
    df["is_late"] = (df["arrival_delta_min"] > 30).astype(int)

    # 4. Chronological time-ordered sorting
    for col in ["planned_departure_ts", "planned_arrival_ts", "slot_start_ts"]:
        df[col] = pd.to_datetime(df[col], utc=True)
    df = df.sort_values("planned_arrival_ts").reset_index(drop=True)

    df["departure_hour"] = df["planned_departure_ts"].dt.hour
    df["arrival_hour"] = df["planned_arrival_ts"].dt.hour
    df["slot_hour"] = df["slot_start_ts"].dt.hour
    df["arrival_month"] = df["planned_arrival_ts"].dt.month

    # Impute missing pallet counts from weight ratio
    kg_per_pallet = (df["load_weight_kg"] / df["pallet_count"].replace(0, np.nan)).median()
    df["pallet_count"] = df["pallet_count"].fillna((df["load_weight_kg"] / kg_per_pallet).round())

    features = CATEGORICAL_FEATURES + NUMERIC_FEATURES
    X = df[features]
    y = df["is_late"]

    # Chronological 80/20 train/test split
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])
    preprocessor = ColumnTransformer([
        ("categorical", cat_pipeline, CATEGORICAL_FEATURES),
        ("numeric", num_pipeline, NUMERIC_FEATURES),
    ])

    clf = Pipeline([
        ("preprocessing", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=200,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        ))
    ])

    clf.fit(X_train, y_train)

    probs = clf.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    baseline_acc = accuracy_score(y_test, np.zeros_like(y_test))
    model_acc = accuracy_score(y_test, preds)
    model_prec = precision_score(y_test, preds)
    model_rec = recall_score(y_test, preds)
    model_auc = roc_auc_score(y_test, probs)

    print("Late Arrival Model Evaluation (Chronological Split):")
    print(f"  Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    print(f"  Baseline Accuracy (Always On-Time): {baseline_acc:.3f}")
    print(f"  Model Accuracy: {model_acc:.3f}")
    print(f"  Model Precision: {model_prec:.3f}")
    print(f"  Model Recall: {model_rec:.3f}")
    print(f"  Model ROC AUC: {model_auc:.3f}")

    model_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(model_dir, "late_arrival_predictor.joblib")
    joblib.dump(clf, model_path)
    print(f"Saved model to {model_path}")
    return clf


if __name__ == "__main__":
    train_late_arrival_model()
