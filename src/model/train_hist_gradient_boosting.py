"""
Train and evaluate a HistGradientBoosting Classification model for SkyWays.

Target: arrival_delta_min > 30 minutes (binary classification)
Evaluated on a chronological time-ordered split (Feb-Jun train, Jul test).
Leakage prevention (Brief Page 26):
  - NO actual_gate_in_ts
  - NO yard_wait_min
  - Only features available before truck arrival
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, brier_score_loss


DATA_PATH = os.path.join(REPO_ROOT, "data", "dock_visit_history.csv")

# Feature definitions
CATEGORICAL_FEATURES = ["dock_type", "facility_id", "vehicle_type_code", "product_category", "priority_code", "day_of_week"]
NUMERIC_FEATURES = [
    "load_weight_kg", "pallet_count", "origin_distance_km", "rain_flag", "labour_shortage_flag",
    "departure_hour", "slot_hour", "arrival_month", "kg_per_pallet", "is_evening_departure",
    "distance_evening_interaction", "rain_distance_interaction", "is_weekend",
    "carrier_hist_delay_rate", "corridor_hist_delay_rate"
]


class HistGradientBoostingPipeline:
    # Ensure pickle always serializes under the fully-qualified module name
    __module__ = "src.model.train_hist_gradient_boosting"

    def __init__(self, preprocessor, model, carrier_map, corridor_map, default_rate, cat_cols, num_cols):
        self.preprocessor = preprocessor
        self.model = model
        self.carrier_map = carrier_map
        self.corridor_map = corridor_map
        self.default_rate = default_rate
        self.cat_cols = cat_cols
        self.num_cols = num_cols

    def _prepare_df(self, raw_df):
        df = raw_df.copy()
        if "load_weight_kg" in df and "pallet_count" in df:
            df["kg_per_pallet"] = (df["load_weight_kg"] / df["pallet_count"].replace(0, 1)).clip(50, 2000)
        else:
            df["kg_per_pallet"] = 500.0

        if "departure_hour" in df:
            df["is_evening_departure"] = ((df["departure_hour"] >= 16) & (df["departure_hour"] <= 20)).astype(int)
        else:
            df["is_evening_departure"] = 0

        if "origin_distance_km" in df and "is_evening_departure" in df:
            df["distance_evening_interaction"] = df["origin_distance_km"] * df["is_evening_departure"]
        else:
            df["distance_evening_interaction"] = 0

        if "rain_flag" in df and "origin_distance_km" in df:
            df["rain_distance_interaction"] = df["rain_flag"] * df["origin_distance_km"]
        else:
            df["rain_distance_interaction"] = 0

        if "origin_city" in df and "facility_id" in df:
            df["corridor"] = df["origin_city"].astype(str) + "_TO_" + df["facility_id"].astype(str)
        else:
            df["corridor"] = "UNKNOWN"

        if "carrier_id" in df:
            df["carrier_hist_delay_rate"] = df["carrier_id"].map(self.carrier_map).fillna(self.default_rate)
        else:
            df["carrier_hist_delay_rate"] = self.default_rate

        df["corridor_hist_delay_rate"] = df["corridor"].map(self.corridor_map).fillna(self.default_rate)
        if "is_weekend" not in df:
            df["is_weekend"] = 0

        # Ensure all required columns exist
        for c in self.cat_cols:
            if c not in df:
                df[c] = "UNKNOWN"
        for c in self.num_cols:
            if c not in df:
                df[c] = 0.0

        return df[self.cat_cols + self.num_cols]

    def predict_proba(self, X):
        if isinstance(X, pd.DataFrame):
            processed_df = self._prepare_df(X)
            X_matrix = self.preprocessor.transform(processed_df)
        else:
            X_matrix = X
        return self.model.predict_proba(X_matrix)

    def predict(self, X, threshold: float = 0.5):
        probs = self.predict_proba(X)[:, 1]
        return (probs >= threshold).astype(int)


# Backward-compatible alias
LateArrivalPredictorPipeline = HistGradientBoostingPipeline


def build_and_train_hist_gradient_boosting():
    df = pd.read_csv(DATA_PATH).drop_duplicates()
    df = df[df["visit_outcome"] != "NO_SHOW"].copy()
    df = df.dropna(subset=["arrival_delta_min"])
    df["is_late"] = (df["arrival_delta_min"] > 30).astype(int)

    # Chronological time-ordered sorting
    for col in ["planned_departure_ts", "planned_arrival_ts", "slot_start_ts"]:
        df[col] = pd.to_datetime(df[col], utc=True)
    df = df.sort_values("planned_arrival_ts").reset_index(drop=True)

    df["departure_hour"] = df["planned_departure_ts"].dt.hour
    df["arrival_hour"] = df["planned_arrival_ts"].dt.hour
    df["slot_hour"] = df["slot_start_ts"].dt.hour
    df["arrival_month"] = df["planned_arrival_ts"].dt.month
    df["day_of_week_num"] = df["planned_departure_ts"].dt.day_of_week
    df["is_weekend"] = (df["day_of_week_num"] >= 5).astype(int)

    # Impute missing pallet counts from weight ratio
    kg_per_pallet = (df["load_weight_kg"] / df["pallet_count"].replace(0, np.nan)).median()
    df["pallet_count"] = df["pallet_count"].fillna((df["load_weight_kg"] / kg_per_pallet).round())

    # Engineered Features (Strictly known at departure time)
    df["kg_per_pallet"] = (df["load_weight_kg"] / df["pallet_count"].replace(0, 1)).clip(50, 2000)
    df["is_evening_departure"] = ((df["departure_hour"] >= 16) & (df["departure_hour"] <= 20)).astype(int)
    df["distance_evening_interaction"] = df["origin_distance_km"] * df["is_evening_departure"]
    df["rain_distance_interaction"] = df["rain_flag"] * df["origin_distance_km"]
    df["corridor"] = df["origin_city"] + "_TO_" + df["facility_id"]

    # Chronological 80/20 train/test split (no future leakage)
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    # Historical target encoding computed ONLY on train_df
    carrier_delay_rate = train_df.groupby("carrier_id")["is_late"].mean().to_dict()
    global_mean_late = train_df["is_late"].mean()
    train_df["carrier_hist_delay_rate"] = train_df["carrier_id"].map(carrier_delay_rate).fillna(global_mean_late)
    test_df["carrier_hist_delay_rate"] = test_df["carrier_id"].map(carrier_delay_rate).fillna(global_mean_late)

    corridor_delay_rate = train_df.groupby("corridor")["is_late"].mean().to_dict()
    train_df["corridor_hist_delay_rate"] = train_df["corridor"].map(corridor_delay_rate).fillna(global_mean_late)
    test_df["corridor_hist_delay_rate"] = test_df["corridor"].map(corridor_delay_rate).fillna(global_mean_late)

    cat_cols = CATEGORICAL_FEATURES
    num_cols = NUMERIC_FEATURES

    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ("num", "passthrough", num_cols)
    ])

    X_train = preprocessor.fit_transform(train_df[cat_cols + num_cols])
    X_test = preprocessor.transform(test_df[cat_cols + num_cols])
    y_train = train_df["is_late"].values
    y_test = test_df["is_late"].values

    # HistGradientBoostingClassifier with TimeSeriesSplit-optimized hyperparameters
    clf = HistGradientBoostingClassifier(
        learning_rate=0.03,
        max_leaf_nodes=20,
        min_samples_leaf=15,
        l2_regularization=4.0,
        random_state=42
    )
    clf.fit(X_train, y_train)

    probs = clf.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds)
    rec = recall_score(y_test, preds)
    auc = roc_auc_score(y_test, probs)
    brier = brier_score_loss(y_test, probs)
    baseline_acc = accuracy_score(y_test, np.zeros_like(y_test))

    print(f"HistGradientBoosting Evaluation (Chronological Split):")
    print(f"  Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    print(f"  Baseline Accuracy (Always On-Time): {baseline_acc*100:.2f}%")
    print(f"  Model Accuracy:  {acc*100:.2f}%")
    print(f"  Model Precision: {prec*100:.2f}%")
    print(f"  Model Recall:    {rec*100:.2f}%")
    print(f"  Model ROC AUC:   {auc:.4f}")
    print(f"  Brier Score:     {brier:.4f}")

    pipeline = HistGradientBoostingPipeline(
        preprocessor=preprocessor,
        model=clf,
        carrier_map=carrier_delay_rate,
        corridor_map=corridor_delay_rate,
        default_rate=global_mean_late,
        cat_cols=cat_cols,
        num_cols=num_cols
    )

    model_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(model_dir, "hist_gradient_boosting_classifier.joblib")
    joblib.dump(pipeline, model_path)
    print(f"Saved HistGradientBoosting model to {model_path}")

    # Also save to legacy path for backward compatibility
    legacy_path = os.path.join(model_dir, "late_arrival_predictor.joblib")
    joblib.dump(pipeline, legacy_path)

    return pipeline


# Backward-compatible alias
build_and_train_late_model = build_and_train_hist_gradient_boosting


if __name__ == "__main__":
    if "src.model.train_hist_gradient_boosting" not in sys.modules:
        sys.modules["src.model.train_hist_gradient_boosting"] = sys.modules[__name__]
    build_and_train_hist_gradient_boosting()

