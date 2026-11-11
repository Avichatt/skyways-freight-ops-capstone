"""
Demonstration: Achieving 80%+ Recall using Decision Threshold Tuning.

This script compares:
1. Default Threshold (0.50): Balanced precision/recall
2. High-Recall Threshold (0.30): Logistics safety buffer (catches >80% of delayed shipments)
"""

import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix


def run_demo():
    model_path = os.path.join("src", "model", "hist_gradient_boosting_classifier.joblib")
    print(f"Loading model from: {model_path} ...")
    model = joblib.load(model_path)

    # Load uncorrupted test dataset
    df = pd.read_csv("data/dock_visit_history.csv").drop_duplicates()
    df = df[df["visit_outcome"] != "NO_SHOW"].dropna(subset=["arrival_delta_min"]).copy()
    df["is_late"] = (df["arrival_delta_min"] > 30).astype(int)

    for col in ["planned_departure_ts", "planned_arrival_ts", "slot_start_ts"]:
        df[col] = pd.to_datetime(df[col], utc=True)
    df = df.sort_values("planned_arrival_ts").reset_index(drop=True)

    df["departure_hour"] = df["planned_departure_ts"].dt.hour
    df["arrival_hour"] = df["planned_arrival_ts"].dt.hour
    df["slot_hour"] = df["slot_start_ts"].dt.hour
    df["arrival_month"] = df["planned_arrival_ts"].dt.month

    # Chronological 80/20 test split (July test set)
    split_idx = int(len(df) * 0.8)
    test_df = df.iloc[split_idx:].copy()
    y_true = test_df["is_late"].values
    total_late_trucks = int(y_true.sum())
    total_test_visits = len(y_true)

    # Get continuous risk scores
    probs = model.predict_proba(test_df)[:, 1]

    print("\n==========================================================================")
    print(f" EVALUATING ON JULY TEST SET: {total_test_visits} visits ({total_late_trucks} actually delayed > 30m)")
    print("==========================================================================\n")

    # Threshold 1: Default 0.50
    preds_50 = (probs >= 0.50).astype(int)
    rec_50 = recall_score(y_true, preds_50) * 100
    prec_50 = precision_score(y_true, preds_50) * 100
    acc_50 = accuracy_score(y_true, preds_50) * 100
    caught_50 = int(preds_50[y_true == 1].sum())

    print("[1] DEFAULT DECISION THRESHOLD = 0.50")
    print(f"    - Recall:    {rec_50:.1f}%  -> Caught {caught_50} of {total_late_trucks} delayed trucks")
    print(f"    - Precision: {prec_50:.1f}%")
    print(f"    - Accuracy:  {acc_50:.1f}%")
    print(f"    - Missed:    {total_late_trucks - caught_50} delayed trucks went undetected!\n")

    # Threshold 2: Tuned 0.30 for 80%+ Recall
    preds_30 = (probs >= 0.30).astype(int)
    rec_30 = recall_score(y_true, preds_30) * 100
    prec_30 = precision_score(y_true, preds_30) * 100
    acc_30 = accuracy_score(y_true, preds_30) * 100
    caught_30 = int(preds_30[y_true == 1].sum())

    print("[2] HIGH-RECALL DECISION THRESHOLD = 0.30  <-- TUNED")
    print(f"    - Recall:    {rec_30:.1f}%  -> Caught {caught_30} of {total_late_trucks} delayed trucks")
    print(f"    - Precision: {prec_30:.1f}%")
    print(f"    - Accuracy:  {acc_30:.1f}%")
    print(f"    - Result:    Caught +{caught_30 - caught_50} MORE delayed trucks before arrival!\n")

    print("==========================================================================")
    print(" HOW TO USE THIS IN PRODUCTION CODE (3-Line Example):")
    print("==========================================================================")
    sample_truck = test_df.iloc[[0]]
    sample_prob = float(model.predict_proba(sample_truck)[0][1])

    # Method A: Using predict_proba with threshold 0.30
    is_high_risk = sample_prob >= 0.30

    # Method B: Using pipeline's predict(threshold=0.30)
    decision = int(model.predict(sample_truck, threshold=0.30)[0])

    print(f"Shipment: {sample_truck['carrier_id'].values[0]} to {sample_truck['facility_id'].values[0]}")
    print(f"Predicted Delay Probability: {sample_prob:.1%}")
    print(f"Threshold (0.30) Flagged Risk: {is_high_risk} (Model Prediction: {decision})")
    if is_high_risk:
        print(">> Autonomous Action: Shorten hold reservation from 10m to 5m to protect dock capacity.")
    print("==========================================================================\n")


if __name__ == "__main__":
    run_demo()
